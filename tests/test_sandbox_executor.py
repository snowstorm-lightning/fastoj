import io
import tarfile

from backend.core.config import settings
from backend.sandbox import executor as executor_module
from backend.sandbox.executor import SandboxExecutor, cleanup_judge_containers


def test_docker_execution_takes_precedence_with_json_line_input(monkeypatch):
    executor = SandboxExecutor()
    monkeypatch.setattr(settings, "FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION", False)
    monkeypatch.setattr(SandboxExecutor, "docker_client", property(lambda self: object()))

    def fake_execute_in_docker(*, code, language, input_data, time_limit, memory_limit):
        assert input_data == "[2,7,11,15]\n9"
        return {
            "status": "ac",
            "output": "[0,1]",
            "error_message": None,
            "execute_time": 1,
            "memory_used": 1,
        }

    monkeypatch.setattr(executor, "_execute_in_docker", fake_execute_in_docker)

    result = executor.execute(
        code="print('wrapped harness')",
        language="python",
        input_data="[2,7,11,15]\n9",
    )

    assert result["status"] == "ac"


def test_docker_execution_copies_code_and_input_by_archive(monkeypatch):
    executor = SandboxExecutor()

    class FakeContainer:
        def put_archive(self, path, data):
            assert path == "/tmp/work"
            with tarfile.open(fileobj=io.BytesIO(data), mode="r") as archive:
                names = set(archive.getnames())
                assert "solution.py" in names
                assert "input.txt" in names
                assert archive.extractfile("input.txt").read().decode("utf-8") == "hello"
            return True

        def exec_run(self, command, stdout, stderr, workdir, user):
            if command == "mkdir -p /tmp/work":
                assert workdir == "/tmp"
                assert user == "root"
                return 0, b""
            if command.startswith("sh -lc 'chmod"):
                assert workdir == "/tmp"
                assert user == "root"
                return 0, b""
            assert "cd /tmp/work" in command
            assert "cat input.txt |" not in command
            assert "< input.txt" in command
            assert workdir == "/tmp/work"
            assert user == "nobody"
            return 0, b"ok\n"

        def logs(self, stdout, stderr):
            return b"ok\n"

        def remove(self, force):
            return None

    class FakeContainers:
        def run(self, image, command, **kwargs):
            assert "volumes" not in kwargs
            assert "tmpfs" not in kwargs
            assert kwargs["read_only"] is False
            assert kwargs["network_disabled"] is True
            assert kwargs["name"].startswith("fastoj_judge_")
            assert kwargs["labels"]["fastoj.judge"] == "true"
            return FakeContainer()

    class FakeDockerClient:
        containers = FakeContainers()

    monkeypatch.setattr(SandboxExecutor, "docker_client", property(lambda self: FakeDockerClient()))

    result = executor.execute(
        code="print(input())",
        language="python",
        input_data="hello",
    )

    assert result["status"] == "ac"
    assert result["output"] == "ok\n"


def test_docker_execution_labels_task_container(monkeypatch):
    executor = SandboxExecutor()
    captured = {}

    class FakeContainer:
        def put_archive(self, path, data):
            return True

        def exec_run(self, command, stdout, stderr, workdir, user):
            return 0, b"ok\n"

        def remove(self, force):
            return None

    class FakeContainers:
        def run(self, image, command, **kwargs):
            captured.update(kwargs)
            return FakeContainer()

    class FakeDockerClient:
        containers = FakeContainers()

    monkeypatch.setattr(SandboxExecutor, "docker_client", property(lambda self: FakeDockerClient()))
    monkeypatch.setenv("FASTOJ_JUDGE_SUBMISSION_ID", "s1")
    monkeypatch.setenv("FASTOJ_JUDGE_MESSAGE_ID", "1-0")

    executor.execute(code="print(input())", language="python", input_data="hello")

    assert captured["labels"] == {
        "fastoj.judge": "true",
        "fastoj.submission_id": "s1",
        "fastoj.message_id": "1-0",
    }


def test_cleanup_judge_containers_removes_only_matching_task(monkeypatch):
    removed = []

    class FakeContainer:
        id = "container-1"

        def remove(self, force):
            removed.append(force)

    class FakeContainers:
        def list(self, all, filters):
            assert all is True
            assert filters == {
                "label": [
                    "fastoj.judge=true",
                    "fastoj.submission_id=s1",
                    "fastoj.message_id=1-0",
                ]
            }
            return [FakeContainer()]

    class FakeDockerClient:
        containers = FakeContainers()

        def close(self):
            return None

    monkeypatch.setattr(executor_module, "get_docker_client", lambda: FakeDockerClient())

    count = cleanup_judge_containers("s1", "1-0")

    assert count == 1
    assert removed == [True]
