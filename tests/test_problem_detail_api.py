import json
import uuid

from backend.core.time import utc_now
from backend.models import Difficulty, Problem
from backend.models import TestCase as ProblemTestCase
from backend.services.problem_service import ProblemService


class FakeQuery:
    def __init__(self, items):
        self.items = list(items)

    def filter(self, *criteria):
        for criterion in criteria:
            left = getattr(criterion, "left", None)
            right = getattr(criterion, "right", None)
            field_name = getattr(left, "name", None)
            value = getattr(right, "value", None)
            if field_name is None:
                continue
            if field_name == "is_hidden" and value is None:
                value = False
            self.items = [item for item in self.items if str(getattr(item, field_name)) == str(value)]
        return self

    def order_by(self, *_args):
        self.items.sort(key=lambda item: getattr(item, "order", 0))
        return self

    def first(self):
        return self.items[0] if self.items else None

    def all(self):
        return self.items


class FakeSession:
    def __init__(self, problem, testcases):
        self.data = {
            Problem: [problem],
            ProblemTestCase: list(testcases),
        }
        for testcase in self.data[ProblemTestCase]:
            testcase.problem = problem

    def query(self, model):
        return FakeQuery(self.data.setdefault(model, []))


def _problem(slug: str = "two-sum") -> Problem:
    return Problem(
        id=uuid.uuid4(),
        title="Two Sum",
        slug=slug,
        description="Find two indices.",
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


def _testcase(problem_id: uuid.UUID, order: int, hidden: bool = False) -> ProblemTestCase:
    return ProblemTestCase(
        id=uuid.uuid4(),
        problem_id=problem_id,
        input="[2,7,11,15]\n9",
        output="[0,1]",
        is_hidden=hidden,
        is_sample=not hidden,
        score=10,
        order=order,
        created_at=utc_now(),
    )


def _metadata_case(
    problem_id: uuid.UUID,
    order: int,
    input_data: str,
    output_data: str,
    acm_input: str,
    function_only: bool = False,
) -> ProblemTestCase:
    io_metadata = {
        "function": {
            "input": input_data,
            "output": output_data,
        },
        "acm": {
            "input": acm_input,
            "output": output_data,
        },
    }
    return ProblemTestCase(
        id=uuid.uuid4(),
        problem_id=problem_id,
        input=input_data,
        output=output_data,
        io_metadata_json=None if function_only else json.dumps(io_metadata, separators=(",", ":")),
        is_hidden=False,
        is_sample=True,
        score=10,
        order=order,
        created_at=utc_now(),
    )


def test_problem_detail_returns_localized_sample_explanations():
    problem = _problem()
    db = FakeSession(problem, [_testcase(problem.id, 0), _testcase(problem.id, 1, hidden=True)])
    service = ProblemService(db)

    zh_problem = service.get_problem_by_id(str(problem.id), "zh")
    en_problem = service.get_problem_by_id(str(problem.id), "en")

    assert zh_problem is not None
    assert en_problem is not None
    assert zh_problem.sample_testcases[0].explanation
    assert en_problem.sample_testcases[0].explanation
    assert "哈希表" in zh_problem.sample_testcases[0].explanation
    assert "hash table" in en_problem.sample_testcases[0].explanation.lower()


def test_problem_detail_returns_null_explanation_for_non_seed_problem():
    problem = _problem("custom-problem")
    db = FakeSession(problem, [_testcase(problem.id, 0)])
    service = ProblemService(db)

    detail = service.get_problem_by_id(str(problem.id), "zh")

    assert detail is not None
    assert detail.sample_testcases[0].explanation is None


def test_problem_detail_supports_function_acm_view_in_same_case():
    problem = _problem()
    testcases = [_metadata_case(problem.id, 0, "[1,2,3]\n3", "[0, 1]", "[1,2,3]\n3")]
    db = FakeSession(problem, testcases)
    service = ProblemService(db)

    detail_acm = service.get_problem_by_id(str(problem.id), "en", "acm")
    if detail_acm is None:
        raise AssertionError("problem should exist")
    case_acm = detail_acm.sample_testcases[0]
    assert case_acm.display_mode == "acm"
    assert case_acm.input == "[1,2,3]\n3"
    assert case_acm.function_input is None

    detail_function = service.get_problem_by_id(str(problem.id), "en", "function")
    if detail_function is None:
        raise AssertionError("problem should exist")
    case_function = detail_function.sample_testcases[0]
    assert case_function is not None
    assert case_function.display_mode == "function"
    assert case_function.function_input == "[1,2,3]\n3"


def test_problem_detail_fallback_to_function_when_acm_view_is_missing():
    problem = Problem(
        id=uuid.uuid4(),
        title="Two Sum",
        slug="two-sum",
        description="Find two indices.",
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
    testcases = [_metadata_case(problem.id, 0, "[2,7,11,15]\n9", "[0,1]", "", function_only=True)]
    db = FakeSession(problem, testcases)
    service = ProblemService(db)

    detail = service.get_problem_by_id(str(problem.id), "en", "acm")
    assert detail is not None
    assert detail.sample_testcases[0].display_mode == "function"
    assert detail.sample_testcases[0].function_input == "[2,7,11,15]\n9"
