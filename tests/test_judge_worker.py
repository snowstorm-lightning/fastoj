import os

from backend.worker import judge_worker as worker_module
from backend.worker.judge_worker import JudgeWorker, _judge_child_entrypoint


def test_parent_clears_active_task_after_child_success(monkeypatch):
    events = []

    class SuccessfulProcess:
        exitcode = 0

        def __init__(self, *, target, args):
            self.target = target
            self.args = args
            events.append(("child", target, args))

        def start(self):
            events.append("start")

        def join(self, timeout=None):
            events.append(("join", timeout))

        def is_alive(self):
            return False

    worker = JudgeWorker()
    worker.process_factory = SuccessfulProcess
    monkeypatch.setattr(worker_module.settings, "JUDGE_TASK_HARD_TIMEOUT_SECONDS", 12)
    monkeypatch.setattr(
        worker_module.queue_service,
        "mark_task_active",
        lambda message_id, submission_id, deadline_at: events.append(
            ("active", message_id, submission_id, deadline_at)
        ),
    )
    monkeypatch.setattr(worker_module.queue_service, "clear_task_active", lambda: events.append("clear"))
    monkeypatch.setattr(
        worker_module,
        "handle_task_failure",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("success path must not fail task")),
    )

    worker.process_task_in_child({"submission_id": "s1"}, "1-0")

    active_events = [event for event in events if isinstance(event, tuple) and event[0] == "active"]
    assert active_events
    assert active_events[0][:3] == ("active", "1-0", "s1")
    assert ("child", worker_module._judge_child_entrypoint, ({"submission_id": "s1"}, "1-0")) in events
    assert "start" in events
    assert ("join", 12) in events
    assert events[-1] == "clear"


def test_parent_retries_and_kills_child_after_hard_timeout(monkeypatch):
    events = []
    failures = []

    class HangingProcess:
        exitcode = None

        def __init__(self, *, target, args):
            self.alive = True

        def start(self):
            events.append("start")

        def join(self, timeout=None):
            events.append(("join", timeout))

        def is_alive(self):
            return self.alive

        def terminate(self):
            events.append("terminate")

        def kill(self):
            events.append("kill")
            self.alive = False

    worker = JudgeWorker()
    worker.process_factory = HangingProcess
    monkeypatch.setattr(worker_module.settings, "JUDGE_TASK_HARD_TIMEOUT_SECONDS", 2)
    monkeypatch.setattr(worker_module.settings, "JUDGE_CHILD_TERMINATE_GRACE_SECONDS", 1)
    monkeypatch.setattr(worker_module.queue_service, "mark_task_active", lambda *args: events.append("active"))
    monkeypatch.setattr(worker_module.queue_service, "clear_task_active", lambda: events.append("clear"))
    monkeypatch.setattr(
        worker_module,
        "cleanup_judge_containers",
        lambda submission_id, message_id: events.append(("cleanup", submission_id, message_id)) or 1,
    )
    monkeypatch.setattr(
        worker_module,
        "handle_task_failure",
        lambda task, message_id, error_message: failures.append((task, message_id, error_message)),
    )

    task = {"submission_id": "s1"}
    worker.process_task_in_child(task, "1-0")

    assert "terminate" in events
    assert "kill" in events
    assert ("cleanup", "s1", "1-0") in events
    assert events[-1] == "clear"
    assert failures == [(task, "1-0", "Judge child process exceeded hard timeout")]


def test_parent_retries_after_child_crash(monkeypatch):
    events = []
    failures = []

    class CrashedProcess:
        exitcode = 7

        def __init__(self, *, target, args):
            pass

        def start(self):
            events.append("start")

        def join(self, timeout=None):
            events.append(("join", timeout))

        def is_alive(self):
            return False

        def terminate(self):
            events.append("terminate")

        def kill(self):
            events.append("kill")

    worker = JudgeWorker()
    worker.process_factory = CrashedProcess
    monkeypatch.setattr(worker_module.settings, "JUDGE_TASK_HARD_TIMEOUT_SECONDS", 3)
    monkeypatch.setattr(worker_module.queue_service, "mark_task_active", lambda *args: events.append("active"))
    monkeypatch.setattr(worker_module.queue_service, "clear_task_active", lambda: events.append("clear"))
    monkeypatch.setattr(
        worker_module,
        "handle_task_failure",
        lambda task, message_id, error_message: failures.append((task, message_id, error_message)),
    )

    task = {"submission_id": "s1"}
    worker.process_task_in_child(task, "1-0")

    assert "terminate" not in events
    assert "kill" not in events
    assert events[-1] == "clear"
    assert failures == [(task, "1-0", "Judge child process exited with code 7")]


def test_parent_retries_when_child_start_fails(monkeypatch):
    events = []
    failures = []

    class StartFailedProcess:
        exitcode = None

        def __init__(self, *, target, args):
            pass

        def start(self):
            raise RuntimeError("spawn unavailable")

        def is_alive(self):
            return False

    worker = JudgeWorker()
    worker.process_factory = StartFailedProcess
    monkeypatch.setattr(worker_module.queue_service, "mark_task_active", lambda *args: events.append("active"))
    monkeypatch.setattr(worker_module.queue_service, "clear_task_active", lambda: events.append("clear"))
    monkeypatch.setattr(
        worker_module,
        "handle_task_failure",
        lambda task, message_id, error_message: failures.append((task, message_id, error_message)),
    )

    task = {"submission_id": "s1"}
    worker.process_task_in_child(task, "1-0")

    assert events == ["active", "clear"]
    assert len(failures) == 1
    assert failures[0][0] == task
    assert failures[0][1] == "1-0"
    assert "spawn unavailable" in failures[0][2]


def test_shutdown_does_not_fail_already_successful_child(monkeypatch):
    failures = []

    class FinishedProcess:
        exitcode = 0

        def is_alive(self):
            return False

    worker = JudgeWorker()
    worker.active_child_process = FinishedProcess()
    worker.active_child_task = {"submission_id": "s1"}
    worker.active_child_message_id = "1-0"
    monkeypatch.setattr(
        worker_module,
        "handle_task_failure",
        lambda *args: failures.append(args),
    )

    worker._stop_active_child("shutdown")

    assert failures == []


def test_child_entrypoint_sets_task_env_and_runs_consumer(monkeypatch):
    calls = []

    class FakeConsumer:
        def process_task(self, task, message_id):
            calls.append((task, message_id, os.environ["FASTOJ_JUDGE_SUBMISSION_ID"], os.environ["FASTOJ_JUDGE_MESSAGE_ID"]))

    monkeypatch.setattr(worker_module.queue_service, "disconnect", lambda: calls.append("disconnect"))
    monkeypatch.setattr(worker_module, "JudgeTaskConsumer", FakeConsumer)

    task = {"submission_id": "s1"}
    _judge_child_entrypoint(task, "1-0")

    assert calls == ["disconnect", (task, "1-0", "s1", "1-0")]
