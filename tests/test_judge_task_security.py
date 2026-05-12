from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.models import Difficulty, SubmissionResult
from backend.worker.tasks.judge_task import JudgeTask


def test_judge_task_does_not_store_hidden_actual_output(monkeypatch):
    problem = SimpleNamespace(
        id="p1",
        time_limit=1000,
        memory_limit=256,
        difficulty=Difficulty.EASY,
    )
    hidden_case = SimpleNamespace(
        id="tc-hidden",
        input="hidden-input",
        output="hidden-output",
        is_hidden=True,
        score=10,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = problem
    db.query.return_value.filter.return_value.count.return_value = 0
    monkeypatch.setattr(
        "backend.worker.tasks.judge_task.ProblemService.get_all_testcases",
        lambda self, problem_id: [hidden_case],
    )
    monkeypatch.setattr(
        "backend.services.queue_service.queue_service.publish_status",
        lambda *args, **kwargs: None,
    )
    task = JudgeTask()
    task.executor = SimpleNamespace(
        execute=lambda **kwargs: {
            "status": "wa",
            "output": "hidden-actual",
            "error_message": None,
            "execute_time": 1,
            "memory_used": 1,
        }
    )

    result = task.execute("s1", "p1", "print(1)", "python", True, db)

    stored_result = db.add.call_args.args[0]
    assert result["result"] == SubmissionResult.WA
    assert stored_result.input is None
    assert stored_result.expected_output is None
    assert stored_result.actual_output is None
