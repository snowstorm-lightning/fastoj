from types import SimpleNamespace

from backend.models import SubmissionResult, SubmissionStatus
from backend.services import submission_service as submission_module
from backend.services.submission_service import SubmissionService


def test_async_submission_falls_back_inline_when_no_worker_heartbeat(monkeypatch):
    updates = []
    pushed = []

    class FakeService(SubmissionService):
        def update_submission_status(self, submission_id, status, **kwargs):
            updates.append((submission_id, status, kwargs))

    class FakeJudgeTask:
        def execute(self, **kwargs):
            return {
                "result": SubmissionResult.AC,
                "error_message": None,
                "execute_time": 7,
                "memory_used": 16,
                "score": 10,
            }

    monkeypatch.setattr(submission_module.settings, "JUDGE_ASYNC", True)
    monkeypatch.setattr(submission_module.queue_service, "has_live_worker", lambda: False)
    monkeypatch.setattr(submission_module.queue_service, "push_task", lambda task: pushed.append(task))
    monkeypatch.setattr("backend.worker.tasks.judge_task.JudgeTask", FakeJudgeTask)

    service = FakeService(db=SimpleNamespace())
    submission = SimpleNamespace(id="s1", problem_id="p1", code="print(1)", language="python")

    service._queue_or_judge_now(submission, use_hidden=False, judge_code="print(1)")

    assert pushed == []
    assert updates[0][1] == SubmissionStatus.JUDGING
    assert updates[1][1] == SubmissionStatus.FINISHED
    assert updates[1][2]["result"] == SubmissionResult.AC
