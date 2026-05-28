from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.models import Difficulty, SubmissionResult
from backend.worker.tasks.judge_task import JudgeTask, _outputs_match


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


def test_hidden_progress_event_does_not_expose_case_metadata(monkeypatch):
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
    published = []
    monkeypatch.setattr(
        "backend.services.queue_service.queue_service.publish_status",
        lambda *args: published.append(args),
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

    task.execute("s1", "p1", "print(1)", "python", True, db)

    progress_payload = published[0][2]
    assert "current_testcase" not in progress_payload
    assert "total_testcases" not in progress_payload
    assert "last_status" not in progress_payload


def test_outputs_match_json_equivalent_lists():
    assert _outputs_match("[0,1]", "[0, 1]")


def test_outputs_match_rejects_different_values():
    assert not _outputs_match("[1,0]", "[0, 1]")


def test_custom_run_testcases_store_visible_user_outputs(monkeypatch):
    problem = SimpleNamespace(
        id="p1",
        time_limit=1000,
        memory_limit=256,
        difficulty=Difficulty.EASY,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = problem
    db.query.return_value.filter.return_value.count.return_value = 0
    monkeypatch.setattr(
        "backend.services.queue_service.queue_service.publish_status",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        JudgeTask,
        "_expected_output_for_input",
        lambda self, problem, db, input_data, public_outputs: "expected-output",
    )
    task = JudgeTask()
    task.executor = SimpleNamespace(
        execute=lambda **kwargs: {
            "status": "ac",
            "output": "user-output",
            "error_message": None,
            "execute_time": 1,
            "memory_used": 1,
        }
    )

    result = task.execute(
        "s1",
        "p1",
        "print(1)",
        "python",
        False,
        db,
        run_testcases=[{"input": "user-input", "expected_output": "client-provided-output"}],
    )

    stored_result = db.add.call_args.args[0]
    assert result["result"] == SubmissionResult.WA
    assert stored_result.testcase_id is None
    assert stored_result.input == "user-input"
    assert stored_result.expected_output == "expected-output"
    assert stored_result.actual_output == "user-output"
    assert stored_result.is_hidden is False


def test_custom_run_generates_expected_output_with_official_solution(monkeypatch):
    problem = SimpleNamespace(
        id="p1",
        slug="two-sum",
        time_limit=1000,
        memory_limit=256,
        difficulty=Difficulty.EASY,
        function_signature=None,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = problem
    db.query.return_value.filter.return_value.count.return_value = 0
    monkeypatch.setattr(
        "backend.worker.tasks.judge_task.ProblemService.get_public_testcases",
        lambda self, problem_id: [],
    )
    monkeypatch.setattr(
        "backend.services.queue_service.queue_service.publish_status",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        JudgeTask,
        "_official_solution",
        lambda self, problem, db: ("python", "official code"),
    )

    def fake_execute(**kwargs):
        if kwargs["code"] == "official code":
            return {
                "status": "ac",
                "output": "expected-output",
                "error_message": None,
                "execute_time": 1,
                "memory_used": 1,
            }
        return {
            "status": "ac",
            "output": "user-output",
            "error_message": None,
            "execute_time": 1,
            "memory_used": 1,
        }

    task = JudgeTask()
    task.executor = SimpleNamespace(execute=fake_execute)

    result = task.execute(
        "s1",
        "p1",
        "print(1)",
        "python",
        False,
        db,
        run_testcases=[{"input": "user-input", "expected_output": "client-provided-output"}],
    )

    stored_result = db.add.call_args.args[0]
    assert result["result"] == SubmissionResult.WA
    assert stored_result.input == "user-input"
    assert stored_result.expected_output == "expected-output"
    assert stored_result.actual_output == "user-output"


def test_builtin_reference_solution_available_for_next_permutation():
    problem = SimpleNamespace(id="p1", slug="next-permutation")
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    task = JudgeTask()

    official = task._official_solution(problem, db)

    assert official is not None
    language, code = official
    assert language == "python"
    assert "nums[i + 1 :]" in code


def test_builtin_reference_solution_available_for_majority_element():
    problem = SimpleNamespace(id="p1", slug="majority-element")
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    task = JudgeTask()

    official = task._official_solution(problem, db)

    assert official is not None
    language, code = official
    assert language == "python"
    assert "candidate" in code


def test_official_function_solution_uses_signature_fallback():
    problem = SimpleNamespace(id="p1", slug="majority-element", function_signature=None)
    solution = SimpleNamespace(
        language="python",
        code="def majority_element(nums):\n    return nums[0]\n",
    )
    task = JudgeTask()

    prepared = task._prepare_official_code(problem, solution)

    assert "def majority_element" in prepared
    assert "sys.stdin" in prepared
