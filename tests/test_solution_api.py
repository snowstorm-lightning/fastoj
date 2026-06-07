import asyncio
import uuid
from types import SimpleNamespace
from typing import Any

from backend.api.problems.solutions import get_problem_solutions
from backend.core.time import utc_now
from backend.models import Difficulty, Problem, Solution
from backend.models import TestCase as ProblemTestCase


class FakeQuery:
    def __init__(self, items: list[Any]):
        self.items = list(items)

    def filter(self, *criteria):
        for criterion in criteria:
            left = getattr(criterion, "left", None)
            right = getattr(criterion, "right", None)
            field_name = getattr(left, "name", None)
            value = getattr(right, "value", None)
            if field_name is None:
                continue
            self.items = [item for item in self.items if str(getattr(item, field_name)) == str(value)]
        return self

    def order_by(self, *_args):
        return self

    def first(self):
        return self.items[0] if self.items else None

    def all(self):
        return self.items


class FakeSession:
    def __init__(self, problem: Problem, solutions: list[Solution]):
        self.data: dict[type, list[Any]] = {
            Problem: [problem],
            Solution: solutions,
            ProblemTestCase: [],
        }

    def query(self, model):
        return FakeQuery(self.data.setdefault(model, []))


def _problem() -> Problem:
    return Problem(
        id=uuid.uuid4(),
        title="Fallback Problem",
        slug="two-sum",
        description="Temporary problem.",
        difficulty=Difficulty.EASY,
        tags=["Array"],
        mode="function",
        function_signature="def two_sum(nums: list[int], target: int) -> list[int]",
        time_limit=1000,
        memory_limit=256,
        is_public=True,
        total_submissions=0,
        accepted_submissions=0,
        created_at=utc_now(),
    )


def _solution(problem_id: uuid.UUID, language: str, code: str) -> Solution:
    return SimpleNamespace(
        id=uuid.uuid4(),
        problem_id=problem_id,
        language=language,
        code=code,
        explanation=f"{language} explanation",
        time_complexity="O(n)",
        space_complexity="O(n)",
    )


def test_public_solution_api_falls_back_to_python_when_requested_language_missing():
    problem = _problem()
    db = FakeSession(problem, [_solution(problem.id, "python", "def two_sum(nums, target): return []")])

    response = asyncio.run(get_problem_solutions(str(problem.id), language="cpp", locale="zh", db=db))

    assert response["data"][0]["language"] == "python"
    assert response["data"][0]["code"].startswith("def two_sum")
    assert "哈希表" in response["data"][0]["explanation"]


def test_public_solution_api_returns_english_seed_explanation():
    problem = _problem()
    db = FakeSession(problem, [_solution(problem.id, "python", "def two_sum(nums, target): return []")])

    response = asyncio.run(get_problem_solutions(str(problem.id), language="python", locale="en", db=db))

    assert response["data"][0]["language"] == "python"
    assert "hash table" in response["data"][0]["explanation"].lower()


def test_public_solution_api_keeps_requested_language_when_available():
    problem = _problem()
    db = FakeSession(
        problem,
        [
            _solution(problem.id, "python", "def two_sum(nums, target): return []"),
            _solution(problem.id, "cpp", "vector<int> two_sum(vector<int> nums, int target) { return {}; }"),
        ],
    )

    response = asyncio.run(get_problem_solutions(str(problem.id), language="cpp", locale="en", db=db))

    assert response["data"][0]["language"] == "cpp"
