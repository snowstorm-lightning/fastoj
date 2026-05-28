from types import SimpleNamespace

from backend.models import SubmissionResult, SubmissionStatus
from backend.worker.tasks import consumer as consumer_module
from backend.worker.tasks.consumer import JudgeTaskConsumer


def test_consumer_prefers_task_code_for_function_mode(monkeypatch):
    fake_db = SimpleNamespace(close=lambda: None)
    fake_submission = SimpleNamespace(
        id="s1",
        problem_id="p1",
        code="def two_sum(nums, target): return []",
        language="python",
        status=SubmissionStatus.PENDING,
        testcase_results=[],
    )
    captured = {}

    class FakeSubmissionService:
        def __init__(self, db):
            self.db = db

        def get_submission_for_judge(self, submission_id):
            return fake_submission

        def update_submission_status(self, *args, **kwargs):
            return fake_submission

    class FakeJudgeTask:
        def execute(self, *, submission_id, problem_id, code, language, use_hidden, db, run_testcases=None):
            captured["code"] = code
            captured["use_hidden"] = use_hidden
            captured["run_testcases"] = run_testcases
            return {
                "result": SubmissionResult.AC,
                "error_message": None,
                "execute_time": 1,
                "memory_used": 1,
                "score": 10,
            }

    monkeypatch.setattr(consumer_module, "SessionLocal", lambda: fake_db)
    monkeypatch.setattr(consumer_module, "SubmissionService", FakeSubmissionService)
    monkeypatch.setattr(consumer_module.queue_service, "publish_status", lambda *args, **kwargs: None)
    monkeypatch.setattr(consumer_module.queue_service, "ack_task", lambda *args, **kwargs: None)

    consumer = JudgeTaskConsumer()
    consumer.judge_task = FakeJudgeTask()
    consumer.process_task(
        {
            "submission_id": "s1",
            "code": "wrapped judge harness",
            "use_hidden": False,
        },
        message_id="m1",
    )

    assert captured == {"code": "wrapped judge harness", "use_hidden": False, "run_testcases": None}
