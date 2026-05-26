import io
import logging
import os
import subprocess
import tarfile
import tempfile
from typing import Any

import docker

from backend.core.config import settings
from backend.sandbox.languages.base import LanguageRunner
from backend.sandbox.languages.cpp import CppRunner, CRunner
from backend.sandbox.languages.golang import GolangRunner
from backend.sandbox.languages.java import JavaRunner
from backend.sandbox.languages.javascript import JavaScriptRunner, TypeScriptRunner
from backend.sandbox.languages.python import PythonRunner

logger = logging.getLogger(__name__)


def get_docker_client() -> docker.DockerClient:
    """Get Docker client with platform-aware connection."""
    if os.name == "nt":
        return docker.DockerClient(base_url="tcp://localhost:2375")
    return docker.DockerClient(base_url="unix://var/run/docker.sock")


class SandboxExecutor:
    """Executes code in Docker, with an explicit local-only subprocess escape hatch."""

    def __init__(self):
        self.container_name_prefix = "fastoj_judge_"
        self._runners = {
            "python": PythonRunner(),
            "c": CRunner(),
            "cpp": CppRunner(),
            "java": JavaRunner(),
            "javascript": JavaScriptRunner(),
            "typescript": TypeScriptRunner(),
            "golang": GolangRunner(),
        }
        self._use_docker = settings.JUDGE_USE_DOCKER
        self._docker_client = None

    @property
    def docker_client(self) -> docker.DockerClient | None:
        """Lazy initialization of Docker client."""
        if not self._use_docker:
            return None
        if self._docker_client is None:
            try:
                self._docker_client = get_docker_client()
                self._docker_client.ping()
            except docker.errors.DockerException as e:
                logger.warning("Docker not available for judge execution: %s", e)
                self._use_docker = False
                return None
        return self._docker_client

    def execute(
        self,
        code: str,
        language: str,
        input_data: str,
        time_limit: int = 1000,
        memory_limit: int = 256,
    ) -> dict[str, Any]:
        """
        Execute code and return result.

        Args:
            code: Source code to execute
            language: Programming language
            input_data: Input to pass to the code
            time_limit: Time limit in milliseconds
            memory_limit: Memory limit in MB

        Returns:
            Dict with keys: status, output, error_message, execute_time, memory_used
        """
        if language not in self._runners:
            return {
                "status": "se",
                "output": None,
                "error_message": f"Unsupported language: {language}",
                "execute_time": 0,
                "memory_used": 0,
            }

        # Try Docker first if enabled.
        if self._use_docker and self.docker_client:
            return self._execute_in_docker(
                code=code,
                language=language,
                input_data=input_data,
                time_limit=time_limit,
                memory_limit=memory_limit,
            )

        if not settings.FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION:
            return {
                "status": "se",
                "output": None,
                "error_message": "Docker judge is unavailable. Unsafe local execution is disabled.",
                "execute_time": 0,
                "memory_used": 0,
            }

        return self._execute_in_subprocess_fallback(
            code=code,
            language=language,
            input_data=input_data,
            time_limit=time_limit,
            memory_limit=memory_limit,
        )

    def _execute_in_docker(
        self,
        code: str,
        language: str,
        input_data: str,
        time_limit: int,
        memory_limit: int,
    ) -> dict[str, Any]:
        """Execute code in Docker container."""
        container = None
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                code_file = self._write_code_file(temp_dir, code, language)
                with open(os.path.join(temp_dir, code_file), encoding="utf-8") as f:
                    code_content = f.read()

            image = settings.JUDGE_CONTAINER_IMAGE
            run_cmd = self._get_run_command_docker(code_file, language)
            timeout_seconds = max(1, int(time_limit / 1000) + 2)

            container = self.docker_client.containers.run(
                image,
                "sh -lc 'sleep 600'",
                detach=True,
                mem_limit=f"{memory_limit}m",
                memswap_limit=f"{memory_limit}m",
                cpu_period=100000,
                cpu_quota=int(time_limit * 1000),
                network_disabled=True,
                pids_limit=128,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges"],
                read_only=False,
                working_dir="/tmp",
                user="nobody",
                stdout=True,
                stderr=True,
                remove=False,
            )

            setup_exit_code, setup_logs = container.exec_run(
                "mkdir -p /tmp/work",
                stdout=True,
                stderr=True,
                workdir="/tmp",
                user="root",
            )
            if setup_exit_code != 0:
                setup_output = setup_logs.decode("utf-8", errors="replace")
                return {
                    "status": "se",
                    "output": None,
                    "error_message": f"Failed to prepare judge workspace: {setup_output}",
                    "execute_time": 0,
                    "memory_used": 0,
                }

            archive_ok = container.put_archive(
                "/tmp/work",
                self._build_judge_archive(
                    {
                        code_file: code_content,
                        "input.txt": input_data,
                    }
                ),
            )
            if not archive_ok:
                return {
                    "status": "se",
                    "output": None,
                    "error_message": "Failed to copy source into judge workspace.",
                    "execute_time": 0,
                    "memory_used": 0,
                }

            permission_exit_code, permission_logs = container.exec_run(
                "sh -lc 'chmod -R a+rwX /tmp/work'",
                stdout=True,
                stderr=True,
                workdir="/tmp",
                user="root",
            )
            if permission_exit_code != 0:
                permission_output = permission_logs.decode("utf-8", errors="replace")
                return {
                    "status": "se",
                    "output": None,
                    "error_message": f"Failed to prepare judge workspace permissions: {permission_output}",
                    "execute_time": 0,
                    "memory_used": 0,
                }

            import time

            start_time = time.time()
            exit_code, raw_logs = container.exec_run(
                f"timeout {timeout_seconds}s sh -lc 'cd /tmp/work && {run_cmd} < input.txt'",
                stdout=True,
                stderr=True,
                workdir="/tmp/work",
                user="nobody",
            )

            output_truncated = len(raw_logs) > settings.JUDGE_MAX_OUTPUT_BYTES
            logs = raw_logs[: settings.JUDGE_MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
            execute_time = int((time.time() - start_time) * 1000)
            error_suffix = "\nOutput truncated." if output_truncated else None

            if exit_code == 0:
                return {
                    "status": "ac",
                    "output": logs,
                    "error_message": error_suffix,
                    "execute_time": execute_time,
                    "memory_used": memory_limit,
                }
            if exit_code == 124:
                return {
                    "status": "tle",
                    "output": logs if logs else None,
                    "error_message": f"Time limit exceeded ({time_limit}ms)",
                    "execute_time": time_limit,
                    "memory_used": 0,
                }
            if exit_code == 42:
                return {
                    "status": "ce",
                    "output": None,
                    "error_message": f"Compilation error:\n{logs}",
                    "execute_time": execute_time,
                    "memory_used": 0,
                }
            if exit_code in {137, 139}:
                return {
                    "status": "mle" if exit_code == 137 else "re",
                    "output": logs if logs else None,
                    "error_message": "Memory limit exceeded" if exit_code == 137 else "Runtime error",
                    "execute_time": execute_time,
                    "memory_used": memory_limit,
                }
            return {
                "status": "re",
                "output": logs if logs else None,
                "error_message": f"Runtime error (exit code {exit_code}){error_suffix or ''}",
                "execute_time": execute_time,
                "memory_used": 0,
            }

        except docker.errors.DockerException as e:
            logger.warning("Docker execution failed: %s", e)
            if settings.FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION:
                return self._execute_in_subprocess_fallback(
                    code=code,
                    language=language,
                    input_data=input_data,
                    time_limit=time_limit,
                    memory_limit=memory_limit,
                )
            return {
                "status": "se",
                "output": None,
                "error_message": f"Docker judge failed and unsafe local execution is disabled: {e}",
                "execute_time": 0,
                "memory_used": 0,
            }
        except Exception as e:
            logger.error(f"Docker execution error: {e}")
            return {
                "status": "se",
                "output": None,
                "error_message": str(e),
                "execute_time": 0,
                "memory_used": 0,
            }
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    def _build_judge_archive(self, files: dict[str, str]) -> bytes:
        """Build a small tar archive for copying source/input into a judge container."""
        stream = io.BytesIO()
        added_dirs: set[str] = set()
        with tarfile.open(fileobj=stream, mode="w") as archive:
            for path, content in files.items():
                directory = os.path.dirname(path)
                if directory and directory not in added_dirs:
                    dir_info = tarfile.TarInfo(directory)
                    dir_info.type = tarfile.DIRTYPE
                    dir_info.mode = 0o755
                    archive.addfile(dir_info)
                    added_dirs.add(directory)

                data = content.encode("utf-8")
                file_info = tarfile.TarInfo(path)
                file_info.size = len(data)
                file_info.mode = 0o644
                archive.addfile(file_info, io.BytesIO(data))
        stream.seek(0)
        return stream.getvalue()

    def _get_run_command_docker(self, code_file: str, language: str) -> str:
        """Get the command to run the code in Docker."""
        commands = {
            "python": "python3 solution.py",
            "c": "gcc solution.c -o solution || exit 42; ./solution",
            "cpp": "g++ solution.cpp -o solution || exit 42; ./solution",
            "java": "javac Solution.java || exit 42; java Solution",
            "javascript": "node solution.js",
            "typescript": "ts-node solution.ts",
            "golang": "go run solution.go",
        }
        return commands.get(language, f"python3 {code_file}")

    def _execute_in_subprocess_fallback(
        self,
        code: str,
        language: str,
        input_data: str,
        time_limit: int,
        memory_limit: int,
    ) -> dict[str, Any]:
        """Execute code using subprocess only when the local unsafe fallback is enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Write code to file
                code_file = self._write_code_file(temp_dir, code, language)

                # Execute in subprocess
                result = self._execute_in_subprocess(
                    code_file=code_file,
                    language=language,
                    input_data=input_data,
                    time_limit=time_limit,
                    memory_limit=memory_limit,
                    work_dir=temp_dir,
                )

                return result

            except subprocess.TimeoutExpired:
                return {
                    "status": "tle",
                    "output": None,
                    "error_message": f"Time limit exceeded ({time_limit}ms)",
                    "execute_time": time_limit,
                    "memory_used": 0,
                }
            except Exception as e:
                logger.error(f"Sandbox execution error: {e}")
                return {
                    "status": "se",
                    "output": None,
                    "error_message": str(e),
                    "execute_time": 0,
                    "memory_used": 0,
                }

    def _get_runner(self, language: str) -> LanguageRunner | None:
        """Get the language runner for the given language."""
        return self._runners.get(language)

    def _write_code_file(self, temp_dir: str, code: str, language: str) -> str:
        """Write code to a file and return the filename."""
        extension_map = {
            "python": ".py",
            "c": ".c",
            "cpp": ".cpp",
            "java": ".java",
            "javascript": ".js",
            "typescript": ".ts",
            "golang": ".go",
        }

        extension = extension_map.get(language, ".txt")
        filename = "Solution.java" if language == "java" else f"solution{extension}"
        filepath = os.path.join(temp_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        return filename

    def _execute_in_subprocess(
        self,
        code_file: str,
        language: str,
        input_data: str,
        time_limit: int,
        memory_limit: int,
        work_dir: str,
    ) -> dict[str, Any]:
        """Execute code using subprocess."""
        runner = self._get_runner(language)
        if not runner:
            return {
                "status": "se",
                "output": None,
                "error_message": f"Unsupported language: {language}",
                "execute_time": 0,
                "memory_used": 0,
            }

        # Handle compilation for languages that need it
        compile_output = None
        if runner.needs_compilation():
            compile_cmd = runner.get_compile_command(code_file)
            if compile_cmd:
                compile_result = subprocess.run(
                    compile_cmd,
                    shell=True,
                    cwd=work_dir,
                    capture_output=True,
                    timeout=30,
                )
                if compile_result.returncode != 0:
                    return {
                        "status": "ce",
                        "output": None,
                        "error_message": f"Compilation error:\n{compile_result.stderr.decode('utf-8', errors='replace')}",
                        "execute_time": 0,
                        "memory_used": 0,
                    }

        # Execute the code
        run_cmd = runner.get_run_command(code_file)
        if not run_cmd:
            return {
                "status": "se",
                "output": None,
                "error_message": "No run command available",
                "execute_time": 0,
                "memory_used": 0,
            }

        import time
        start_time = time.time()

        try:
            result = subprocess.run(
                run_cmd,
                shell=True,
                input=input_data.encode("utf-8"),
                capture_output=True,
                timeout=time_limit / 1000,  # Convert ms to seconds
                cwd=work_dir,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "tle",
                "output": None,
                "error_message": f"Time limit exceeded ({time_limit}ms)",
                "execute_time": time_limit,
                "memory_used": 0,
            }

        execute_time = int((time.time() - start_time) * 1000)  # Convert to ms

        # Check for runtime errors
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")
            return {
                "status": "re",
                "output": None,
                "error_message": f"Runtime error:\n{stderr}",
                "execute_time": execute_time,
                "memory_used": 0,
            }

        # Success - return output
        stdout_bytes = result.stdout[: settings.JUDGE_MAX_OUTPUT_BYTES]
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        if len(result.stdout) > settings.JUDGE_MAX_OUTPUT_BYTES:
            stdout += "\nOutput truncated."
        return {
            "status": "ac",
            "output": stdout,
            "error_message": None,
            "execute_time": execute_time,
            "memory_used": memory_limit,  # Approximate
        }

    def cleanup(self, submission_id: str):
        """Clean up any resources for a submission."""
        # No cleanup needed for subprocess execution
        pass
