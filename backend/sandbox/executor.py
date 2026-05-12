import logging
import os
import subprocess
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
    """Executes code using subprocess or Docker based on configuration."""

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
                logger.warning(f"Docker not available, falling back to subprocess: {e}")
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
        function_name: str = None,
    ) -> dict[str, Any]:
        """
        Execute code and return result.

        Args:
            code: Source code to execute
            language: Programming language
            input_data: Input to pass to the code (function call format for LeetCode style)
            time_limit: Time limit in milliseconds
            memory_limit: Memory limit in MB
            function_name: Function name to call (for LeetCode style)

        Returns:
            Dict with keys: status, output, error_message, execute_time, memory_used
        """
        # For LeetCode style (function call input), use function execution
        if function_name or self._is_function_call(input_data):
            return self._execute_function_test(
                code=code,
                language=language,
                input_data=input_data,
                time_limit=time_limit,
                memory_limit=memory_limit,
                function_name=function_name,
            )

        # Try Docker first if enabled
        if self._use_docker and self.docker_client:
            return self._execute_in_docker(
                code=code,
                language=language,
                input_data=input_data,
                time_limit=time_limit,
                memory_limit=memory_limit,
            )

        # Fall back to subprocess
        return self._execute_in_subprocess_fallback(
            code=code,
            language=language,
            input_data=input_data,
            time_limit=time_limit,
            memory_limit=memory_limit,
        )

    def _is_function_call(self, input_data: str) -> bool:
        """Check if input looks like a function call."""
        if not input_data:
            return False
        return '(' in input_data and ')' in input_data

    def _execute_function_test(
        self,
        code: str,
        language: str,
        input_data: str,
        time_limit: int,
        memory_limit: int,
        function_name: str = None,
    ) -> dict[str, Any]:
        """Execute a function call (LeetCode style)."""
        if language != "python":
            return self._execute_in_subprocess_fallback(
                code=code,
                language=language,
                input_data=input_data,
                time_limit=time_limit,
                memory_limit=memory_limit,
            )

        # For Python, wrap the code with a test harness
        return self._execute_python_function(code, input_data, time_limit, memory_limit)

    def _execute_python_function(
        self,
        code: str,
        input_data: str,
        time_limit: int,
        memory_limit: int,
    ) -> dict[str, Any]:
        """Execute Python function call."""
        import re
        import time as time_module

        # Parse function call: "function_name(arg1, arg2, ...)"
        match = re.match(r'(\w+)\((.*)\)\s*$', input_data.strip(), re.DOTALL)
        if not match:
            return {
                "status": "re",
                "output": None,
                "error_message": f"Invalid function call format: {input_data}",
                "execute_time": 0,
                "memory_used": 0,
            }

        func_name = match.group(1)
        args_str = match.group(2)

        # Create wrapper code that executes the function call
        wrapper_code = f'''
{code}

# Test execution
import sys
try:
    result = {func_name}({args_str})
    # Convert result to string representation
    if isinstance(result, (list, tuple)):
        print(repr(result), file=sys.stdout)
    else:
        print(result, file=sys.stdout)
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    sys.exit(1)
'''

        start_time = time_module.time()

        try:
            result = subprocess.run(
                ["python", "-c", wrapper_code],
                capture_output=True,
                timeout=time_limit / 1000,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "tle",
                "output": None,
                "error_message": f"Time limit exceeded ({time_limit}ms)",
                "execute_time": time_limit,
                "memory_used": 0,
            }

        execute_time = int((time_module.time() - start_time) * 1000)

        stderr = result.stderr.decode("utf-8", errors="replace")
        stdout = result.stdout.decode("utf-8", errors="replace")

        if result.returncode != 0:
            return {
                "status": "re",
                "output": None,
                "error_message": f"Runtime error:\n{stderr}",
                "execute_time": execute_time,
                "memory_used": 0,
            }

        return {
            "status": "ac",
            "output": stdout.strip(),
            "error_message": None,
            "execute_time": execute_time,
            "memory_used": memory_limit,
        }

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
                # Write code to file
                code_file = self._write_code_file(temp_dir, code, language)

                # Write input to file
                input_file = os.path.join(temp_dir, "input.txt")
                with open(input_file, "w", encoding="utf-8") as f:
                    f.write(input_data)

                # Get image and run command
                image = settings.JUDGE_CONTAINER_IMAGE
                run_cmd = self._get_run_command_docker(code_file, language)

                # Create and run container
                container = self.docker_client.containers.run(
                    image,
                    f"sh -c 'cat /input.txt | {run_cmd}'",
                    detach=True,
                    mem_limit=f"{memory_limit}m",
                    memswap_limit=f"{memory_limit}m",
                    cpu_period=100000,
                    cpu_quota=int(time_limit * 1000),
                    network_disabled=True,
                    volumes={
                        temp_dir: {"bind": "/code", "mode": "ro"},
                        input_file: {"bind": "/input.txt", "mode": "ro"},
                    },
                    working_dir="/code",
                    user="nobody",
                    stdout=True,
                    stderr=True,
                    remove=False,
                )

                import time
                start_time = time.time()

                try:
                    result = container.wait(timeout=time_limit / 1000 + 5)
                    exit_code = result.get("StatusCode", 1)
                except docker.errors.Timeout:
                    try:
                        container.kill()
                    except Exception:
                        pass
                    return {
                        "status": "tle",
                        "output": None,
                        "error_message": f"Time limit exceeded ({time_limit}ms)",
                        "execute_time": time_limit,
                        "memory_used": 0,
                    }

                logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
                execute_time = int((time.time() - start_time) * 1000)

                if exit_code == 0:
                    return {
                        "status": "ac",
                        "output": logs,
                        "error_message": None,
                        "execute_time": execute_time,
                        "memory_used": memory_limit,
                    }
                else:
                    return {
                        "status": "re",
                        "output": logs if logs else None,
                        "error_message": f"Runtime error (exit code {exit_code})",
                        "execute_time": execute_time,
                        "memory_used": 0,
                    }

        except docker.errors.DockerException as e:
            logger.warning(f"Docker execution failed, falling back to subprocess: {e}")
            return self._execute_in_subprocess_fallback(
                code=code,
                language=language,
                input_data=input_data,
                time_limit=time_limit,
                memory_limit=memory_limit,
            )
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

    def _get_run_command_docker(self, code_file: str, language: str) -> str:
        """Get the command to run the code in Docker."""
        commands = {
            "python": f"python {code_file}",
            "c": f"gcc {code_file} -o solution && ./solution",
            "cpp": f"g++ {code_file} -o solution && ./solution",
            "java": f"javac {code_file} && java Solution",
            "javascript": f"node {code_file}",
            "typescript": f"ts-node {code_file}",
            "golang": f"go run {code_file}",
        }
        return commands.get(language, f"python {code_file}")

    def _execute_in_subprocess_fallback(
        self,
        code: str,
        language: str,
        input_data: str,
        time_limit: int,
        memory_limit: int,
    ) -> dict[str, Any]:
        """Execute code using subprocess (fallback when Docker unavailable)."""
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
        filename = f"solution{extension}"
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
        stdout = result.stdout.decode("utf-8", errors="replace")
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
