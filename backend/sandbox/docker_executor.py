import logging
import os
import tempfile
from typing import Any

import docker

from backend.core.config import settings

logger = logging.getLogger(__name__)


def get_docker_client() -> docker.DockerClient:
    """Get Docker client with platform-aware connection."""
    # Windows Docker Desktop uses TCP
    if os.name == "nt":
        return docker.DockerClient(base_url="tcp://localhost:2375")
    # Unix systems use socket
    return docker.DockerClient(base_url="unix://var/run/docker.sock")


class DockerExecutor:
    """Executes code in isolated Docker containers."""

    def __init__(self):
        self._client = None
        self.container_name_prefix = "fastoj_judge_"

    @property
    def client(self) -> docker.DockerClient:
        """Lazy initialization of Docker client."""
        if self._client is None:
            self._client = get_docker_client()
        return self._client

    def execute(
        self,
        code: str,
        language: str,
        input_data: str,
        time_limit: int = 1000,
        memory_limit: int = 256,
    ) -> dict[str, Any]:
        """
        Execute code in Docker container and return result.

        Args:
            code: Source code to execute
            language: Programming language
            input_data: Input to pass to the code
            time_limit: Time limit in milliseconds
            memory_limit: Memory limit in MB

        Returns:
            Dict with keys: status, output, error_message, execute_time, memory_used
        """
        container = None
        try:
            # Write code to temp file
            with tempfile.TemporaryDirectory() as temp_dir:
                code_file = self._write_code_file(temp_dir, code, language)

                # Create and run container
                container = self._create_container(temp_dir, code_file, language, input_data, time_limit, memory_limit)
                result = self._run_container(container, time_limit)

                return result

        except docker.errors.DockerException as e:
            logger.error(f"Docker execution error: {e}")
            return {
                "status": "se",
                "output": None,
                "error_message": f"Docker error: {str(e)}",
                "execute_time": 0,
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
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

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

    def _get_image(self, language: str) -> str:
        """Get the Docker image for the given language."""
        # Default judge image from settings
        image = settings.JUDGE_CONTAINER_IMAGE
        # Could be extended to use language-specific images
        return image

    def _get_run_command(self, code_file: str, language: str) -> str:
        """Get the command to run the code."""
        commands = {
            "python": f"python {code_file}",
            "c": f"./solution {code_file}",
            "cpp": f"./solution {code_file}",
            "java": "java Solution",
            "javascript": f"node {code_file}",
            "typescript": f"ts-node {code_file}",
            "golang": f"go run {code_file}",
        }
        return commands.get(language, f"python {code_file}")

    def _create_container(
        self,
        work_dir: str,
        code_file: str,
        language: str,
        input_data: str,
        time_limit: int,
        memory_limit: int,
    ):
        """Create a Docker container for code execution."""
        image = self._get_image(language)
        run_cmd = self._get_run_command(code_file, language)

        # Write input to file
        input_file = os.path.join(work_dir, "input.txt")
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(input_data)

        container = self.client.containers.run(
            image,
            f"sh -c 'cat /input.txt | {run_cmd}'",
            detach=True,
            mem_limit=f"{memory_limit}m",
            memswap_limit=f"{memory_limit}m",
            cpu_period=100000,
            cpu_quota=int(time_limit * 1000),  # Convert ms to microseconds
            network_disabled=False,
            volumes={
                work_dir: {"bind": "/code", "mode": "ro"},
                input_file: {"bind": "/input.txt", "mode": "ro"},
            },
            working_dir="/code",
            user="root",
            stdout=True,
            stderr=True,
            remove=False,
        )
        return container

    def _run_container(self, container, time_limit: int) -> dict[str, Any]:
        """Run container and return result."""
        import time

        start_time = time.time()

        try:
            # Wait for container to finish with timeout
            result = container.wait(timeout=time_limit / 1000 + 5)  # Add buffer to timeout
            exit_code = result.get("StatusCode", 1)

            # Get output
            logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
            execute_time = int((time.time() - start_time) * 1000)

            if exit_code == 0:
                return {
                    "status": "ac",
                    "output": logs,
                    "error_message": None,
                    "execute_time": execute_time,
                    "memory_used": 0,
                }
            else:
                return {
                    "status": "re",
                    "output": logs if logs else None,
                    "error_message": f"Runtime error (exit code {exit_code})",
                    "execute_time": execute_time,
                    "memory_used": 0,
                }

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

    def cleanup(self, submission_id: str):
        """Clean up any containers for a submission."""
        try:
            container_name = f"{self.container_name_prefix}{submission_id}"
            container = self.client.containers.get(container_name)
            container.remove(force=True)
        except docker.errors.NotFound:
            pass
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
