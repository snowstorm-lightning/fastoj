from types import SimpleNamespace

from backend.models import SubmissionResult, SubmissionStatus
from backend.services.queue_service import TaskAlreadyHandledError
from backend.worker.tasks import consumer as consumer_module
from backend.worker.tasks.consumer import JudgeTaskConsumer, handle_task_failure


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


def test_handle_task_failure_resets_pending_for_retry(monkeypatch):
    fake_db = SimpleNamespace(close=lambda: None)
    updates = []
    published = []

    class FakeSubmissionService:
        def __init__(self, db):
            self.db = db

        def get_submission_for_judge(self, submission_id):
            return None

        def update_submission_status(self, *args, **kwargs):
            updates.append((args, kwargs))

    monkeypatch.setattr(consumer_module.queue_service, "retry_or_dead_letter", lambda *args: False)
    monkeypatch.setattr(consumer_module.queue_service, "publish_status", lambda *args: published.append(args))
    monkeypatch.setattr(consumer_module, "SubmissionService", FakeSubmissionService)

    terminal = handle_task_failure({"submission_id": "s1"}, "1-0", "boom", db=fake_db)

    assert terminal is False
    assert updates == [(("s1", SubmissionStatus.PENDING), {})]
    assert published[0][0] == "s1"
    assert published[0][1] == "pending"


def test_handle_task_failure_noops_when_message_already_handled(monkeypatch):
    fake_db = SimpleNamespace(close=lambda: None)
    updates = []
    published = []

    class FakeSubmissionService:
        def __init__(self, db):
            self.db = db

        def get_submission_for_judge(self, submission_id):
            return None

        def update_submission_status(self, *args, **kwargs):
            updates.append((args, kwargs))

    def already_handled(*args):
        raise TaskAlreadyHandledError("already acked")

    monkeypatch.setattr(consumer_module.queue_service, "retry_or_dead_letter", already_handled)
    monkeypatch.setattr(consumer_module.queue_service, "publish_status", lambda *args: published.append(args))
    monkeypatch.setattr(consumer_module, "SubmissionService", FakeSubmissionService)

    terminal = handle_task_failure({"submission_id": "s1"}, "1-0", "late parent failure", db=fake_db)

    assert terminal is True
    assert updates == []
    assert published == []


def test_handle_task_failure_completes_existing_results_without_retry(monkeypatch):
    fake_db = SimpleNamespace(close=lambda: None)
    existing_result = SimpleNamespace(status=SubmissionResult.AC)
    fake_submission = SimpleNamespace(
        status=SubmissionStatus.JUDGING,
        testcase_results=[existing_result],
    )
    updates = []
    published = []
    acked = []

    class FakeSubmissionService:
        def __init__(self, db):
            self.db = db

        def get_submission_for_judge(self, submission_id):
            return fake_submission

        def update_submission_status(self, *args, **kwargs):
            updates.append((args, kwargs))

    class FakeJudgeTask:
        def summarize_existing_results(self, db, testcase_results):
            assert testcase_results == [existing_result]
            return {
                "result": SubmissionResult.AC,
                "error_message": None,
                "execute_time": 5,
                "memory_used": 9,
                "score": 10,
            }

    monkeypatch.setattr(consumer_module, "SubmissionService", FakeSubmissionService)
    monkeypatch.setattr(consumer_module, "JudgeTask", FakeJudgeTask)
    monkeypatch.setattr(
        consumer_module.queue_service,
        "retry_or_dead_letter",
        lambda *args: (_ for _ in ()).throw(AssertionError("existing results should not retry")),
    )
    monkeypatch.setattr(consumer_module.queue_service, "publish_status", lambda *args: published.append(args))
    monkeypatch.setattr(consumer_module.queue_service, "ack_task", lambda *args: acked.append(args))

    terminal = handle_task_failure({"submission_id": "s1"}, "1-0", "child crashed", db=fake_db)

    assert terminal is True
    assert updates == [
        (
            ("s1", SubmissionStatus.FINISHED),
            {
                "result": SubmissionResult.AC,
                "error_message": None,
                "execute_time": 5,
                "memory_used": 9,
                "score": 10,
            },
        )
    ]
    assert published[0][0] == "s1"
    assert published[0][1] == "result"
    assert published[0][2]["result"] == "ac"
    assert acked == [("1-0",)]
