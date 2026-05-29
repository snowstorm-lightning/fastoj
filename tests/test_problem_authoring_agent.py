import json
import uuid
from datetime import datetime
from typing import Any

import pytest
from fastapi import HTTPException

from backend.ai.providers import BaseAIProvider
from backend.api.admin import (
    AdminTestCaseCreate,
    AdminTestCaseUpdate,
    create_testcase,
    delete_problem,
    delete_testcase,
    list_testcases,
    require_admin,
    update_testcase,
)
from backend.api.admin_agent import create_problem_draft
from backend.core.config import settings
from backend.models import (
    AgentRun,
    AgentStep,
    Difficulty,
    Problem,
    ProblemDraft,
    Solution,
    Submission,
    SubmissionResult,
    TestCaseResult,
    User,
)
from backend.models import (
    TestCase as OJTestCase,
)
from backend.schemas.problem_authoring import ProblemAuthoringRequest, ProblemDraftUpdate
from backend.services.problem_authoring_agent import (
    ProblemAuthoringAgentService,
    ProblemDraftValidationAdapter,
    load_json,
    normalize_function_call_args,
)


class FakeQuery:
    def __init__(self, items: list[Any]):
        self.items = list(items)

    def filter(self, *criteria):
        for criterion in criteria:
            left = getattr(criterion, "left", None)
            right = getattr(criterion, "right", None)
            field_name = getattr(left, "name", None)
            value = getattr(right, "value", None)
            operator_name = getattr(getattr(criterion, "operator", None), "__name__", "")
            if field_name is None:
                continue
            if operator_name == "eq":
                self.items = [item for item in self.items if str(getattr(item, field_name)) == str(value)]
            elif operator_name == "ne":
                self.items = [item for item in self.items if str(getattr(item, field_name)) != str(value)]
        return self

    def order_by(self, *args):
        if args and "DESC" in str(args[0]).upper():
            self.items = list(reversed(self.items))
        return self

    def first(self):
        return self.items[0] if self.items else None

    def all(self):
        return self.items


class FakeSession:
    def __init__(self):
        self.data: dict[type, list[Any]] = {
            AgentRun: [],
            AgentStep: [],
            ProblemDraft: [],
            Problem: [],
            OJTestCase: [],
            Solution: [],
        }

    def add(self, item):
        if getattr(item, "created_at", None) is None:
            item.created_at = datetime.utcnow()
        if hasattr(item, "updated_at") and getattr(item, "updated_at", None) is None:
            item.updated_at = datetime.utcnow()
        self.data.setdefault(type(item), []).append(item)

    def flush(self):
        pass

    def commit(self):
        for items in self.data.values():
            for item in items:
                if hasattr(item, "updated_at"):
                    item.updated_at = datetime.utcnow()

    def refresh(self, item):
        if hasattr(item, "updated_at"):
            item.updated_at = datetime.utcnow()

    def query(self, model):
        return FakeQuery(self.data.setdefault(model, []))

    def delete(self, item):
        items = self.data.setdefault(type(item), [])
        if item in items:
            items.remove(item)


class FakeProvider(BaseAIProvider):
    def __init__(self, raw: str):
        self.raw = raw

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        return self.raw


class SequenceProvider(BaseAIProvider):
    def __init__(self, raw_values: list[str]):
        self.raw_values = raw_values
        self.calls: list[tuple[str, str]] = []

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        index = min(len(self.calls) - 1, len(self.raw_values) - 1)
        return self.raw_values[index]


class EchoExecutor:
    def execute(self, code: str, language: str, input_data: str, time_limit: int = 1000, memory_limit: int = 256):
        return {
            "status": "ac",
            "output": input_data,
            "error_message": None,
            "execute_time": 1,
            "memory_used": 16,
        }


class FailingExecutor:
    def execute(self, code: str, language: str, input_data: str, time_limit: int = 1000, memory_limit: int = 256):
        return {
            "status": "ac",
            "output": "wrong",
            "error_message": None,
            "execute_time": 1,
            "memory_used": 16,
        }


class SecretFailingExecutor:
    def execute(self, code: str, language: str, input_data: str, time_limit: int = 1000, memory_limit: int = 256):
        return {
            "status": "re",
            "output": "SECRET_ACTUAL_OUTPUT",
            "error_message": "SECRET_HIDDEN_INPUT SECRET_EXPECTED_OUTPUT",
            "execute_time": 1,
            "memory_used": 16,
        }


def authored_payload(public_count: int = 2, hidden_count: int = 6) -> str:
    return json.dumps(
        {
            "title": "Echo Number",
            "slug_candidate": "echo-number",
            "description": "Read one value and print it.",
            "input_format": "One value.",
            "output_format": "The same value.",
            "function_signature": None,
            "difficulty": "easy",
            "tags": ["io"],
            "mode": "acm",
            "time_limit": 1000,
            "memory_limit": 256,
            "hint": "Print what you read.",
            "official_solution_language": "python",
            "official_solution_code": "import sys\nprint(sys.stdin.read().strip())\n",
            "official_solution_explanation": "The solution echoes stdin.",
            "time_complexity": "O(n)",
            "space_complexity": "O(n)",
            "public_sample_testcases": [
                {"input": str(index), "output": str(index), "explanation": "Echo."}
                for index in range(1, public_count + 1)
            ],
            "hidden_testcases": [
                {"input": str(index), "output": str(index), "explanation": "Hidden echo."}
                for index in range(10, 10 + hidden_count)
            ],
            "validation_notes": "Validated by executing the official solution.",
        }
    )


def authored_both_payload() -> str:
    return json.dumps(
        {
            "title": "Echo Value",
            "slug_candidate": "echo-value",
            "description": "Return the given value in both function and ACM practice modes.",
            "input_format": "One JSON value.",
            "output_format": "The returned value.",
            "function_signature": "def echo_value(value: int) -> int:",
            "difficulty": "easy",
            "tags": ["io"],
            "mode": "both",
            "time_limit": 1000,
            "memory_limit": 256,
            "hint": "Return the input value.",
            "official_solution_language": "python",
            "official_solution_code": "def echo_value(value: int) -> int:\n    return value\n",
            "official_solution_explanation": "The solution returns the argument unchanged.",
            "time_complexity": "O(1)",
            "space_complexity": "O(1)",
            "public_sample_testcases": [
                {"input": "7", "output": "7", "explanation": "Echo the value."},
            ],
            "hidden_testcases": [],
            "validation_notes": "Both modes share the same expected answer.",
        }
    )


def authored_multilanguage_payload() -> str:
    payload = json.loads(authored_payload(public_count=1, hidden_count=0))
    payload["official_solutions"] = [
        {
            "language": "python",
            "code": "import sys\nprint(sys.stdin.read().strip())\n",
            "explanation": "Echo stdin in Python.",
        },
        {
            "language": "cpp",
            "code": "#include <bits/stdc++.h>\nusing namespace std;\nint main(){string s; getline(cin,s); cout<<s<<'\\n';}\n",
            "explanation": "Echo stdin in C++.",
        },
        {
            "language": "java",
            "code": "import java.util.*; class Solution { public static void main(String[] args){ Scanner sc = new Scanner(System.in); if(sc.hasNextLine()) System.out.println(sc.nextLine()); }}",
            "explanation": "Echo stdin in Java.",
        },
    ]
    return json.dumps(payload)


def request_payload() -> ProblemAuthoringRequest:
    return ProblemAuthoringRequest(
        topic="echo number",
        difficulty="easy",
        tags=["io"],
        mode="acm",
        target_language="python",
        locale="en",
        model_profile="default",
    )


def multilanguage_request_payload() -> ProblemAuthoringRequest:
    return ProblemAuthoringRequest(
        topic="echo number",
        difficulty="easy",
        tags=["io"],
        mode="acm",
        target_language="python",
        target_languages=["python", "cpp", "java"],
        locale="en",
        model_profile="default",
    )


def admin_user() -> User:
    return User(id=uuid.uuid4(), username="admin", email="admin@example.com", password_hash="x", role="admin")


def test_require_admin_rejects_non_admin_user():
    user = User(id=uuid.uuid4(), username="user", email="user@example.com", password_hash="x", role="user")

    with pytest.raises(HTTPException) as exc_info:
        require_admin(user)

    assert exc_info.value.status_code == 403


def test_ai_disabled_endpoint_returns_503_and_does_not_create_problem(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "disabled")
    db = FakeSession()

    with pytest.raises(HTTPException) as exc_info:
        create_problem_draft(request_payload(), db, admin_user())

    assert exc_info.value.status_code == 503
    assert db.data[Problem] == []
    assert db.data[AgentRun][0].status == "failed"


def test_create_draft_saves_draft_run_and_steps():
    db = FakeSession()
    service = ProblemAuthoringAgentService(
        db,
        provider=FakeProvider(authored_payload()),
        validator=ProblemDraftValidationAdapter(EchoExecutor()),
    )

    draft, run = service.create_draft(request_payload(), admin_user())

    assert draft.status == "validated"
    assert run.status == "succeeded"
    assert len(db.data[ProblemDraft]) == 1
    assert len(db.data[AgentRun]) == 1
    assert {step.step_type for step in db.data[AgentStep]} >= {"plan", "model_call", "validation", "persistence"}


def test_create_and_approve_draft_with_multiple_official_solution_languages():
    db = FakeSession()
    service = ProblemAuthoringAgentService(
        db,
        provider=FakeProvider(authored_multilanguage_payload()),
        validator=ProblemDraftValidationAdapter(EchoExecutor()),
    )
    user = admin_user()

    draft, _run = service.create_draft(multilanguage_request_payload(), user)
    approved = service.approve_draft(str(draft.id), user)

    assert draft.status == "approved"
    assert approved.approved_problem_id is not None
    assert {solution.language for solution in db.data[Solution]} == {"python", "cpp", "java"}
    report = json.loads(draft.validation_report_json)
    assert {result["solution_language"] for result in report["case_results"]} == {"python", "cpp", "java"}


def test_create_draft_requires_requested_official_solution_languages():
    db = FakeSession()
    service = ProblemAuthoringAgentService(
        db,
        provider=SequenceProvider([authored_payload(public_count=1, hidden_count=0)] * 3),
        validator=ProblemDraftValidationAdapter(EchoExecutor()),
    )

    draft, _run = service.create_draft(multilanguage_request_payload(), admin_user())

    assert draft.status == "validation_failed"
    report = json.loads(draft.validation_report_json)
    assert "official_solution_languages" in {
        check["name"] for check in report["checks"] if not check["passed"]
    }


def test_update_draft_revalidates_and_records_manual_step():
    db = FakeSession()
    user = admin_user()
    service = ProblemAuthoringAgentService(
        db,
        provider=FakeProvider(authored_payload()),
        validator=ProblemDraftValidationAdapter(EchoExecutor()),
    )
    draft, _ = service.create_draft(request_payload(), user)

    updated = service.update_draft(
        str(draft.id),
        ProblemDraftUpdate(
            title="Echo Value",
            slug="echo-value",
            testcases=[
                {"input": "7", "output": "7", "is_hidden": False, "is_sample": True, "order": 1},
            ],
        ),
        user,
    )

    assert updated.title == "Echo Value"
    assert updated.slug == "echo-value"
    assert updated.status == "validated"
    assert len(db.data[AgentRun]) == 2
    assert db.data[AgentStep][-1].step_type == "manual_edit"


def test_update_draft_rejects_duplicate_manual_slug():
    db = FakeSession()
    user = admin_user()
    db.add(
        Problem(
            id=uuid.uuid4(),
            title="Taken",
            slug="taken-slug",
            description="Existing problem.",
            difficulty=Difficulty.EASY,
            mode="acm",
        )
    )
    service = ProblemAuthoringAgentService(
        db,
        provider=FakeProvider(authored_payload()),
        validator=ProblemDraftValidationAdapter(EchoExecutor()),
    )
    draft, _ = service.create_draft(request_payload(), user)

    with pytest.raises(ValueError, match="Slug already exists: taken-slug"):
        service.update_draft(str(draft.id), ProblemDraftUpdate(slug="taken-slug"), user)

    assert draft.slug == "echo-number"


def test_update_draft_ignores_failed_or_rejected_drafts_when_checking_slug():
    db = FakeSession()
    user = admin_user()
    for status in ["validation_failed", "rejected", "approved"]:
        db.add(
            ProblemDraft(
                id=uuid.uuid4(),
                title=f"Historical {status}",
                slug=f"historical-{status}",
                description="Historical draft.",
                difficulty="easy",
                tags="[]",
                mode="acm",
                official_solution_language="python",
                official_solution_code="print(1)",
                official_solution_explanation="Return one.",
                testcases_json="[]",
                validation_report_json="{}",
                status=status,
                created_by=user.id,
            )
        )
    service = ProblemAuthoringAgentService(
        db,
        provider=FakeProvider(authored_payload()),
        validator=ProblemDraftValidationAdapter(EchoExecutor()),
    )
    draft, _ = service.create_draft(request_payload(), user)

    updated = service.update_draft(
        str(draft.id),
        ProblemDraftUpdate(slug="historical-validation-failed"),
        user,
    )

    assert updated.slug == "historical-validation-failed"


def test_update_draft_rejects_slug_used_by_validated_draft():
    db = FakeSession()
    user = admin_user()
    db.add(
        ProblemDraft(
            id=uuid.uuid4(),
            title="Active Draft",
            slug="active-draft",
            description="Validated draft.",
            difficulty="easy",
            tags="[]",
            mode="acm",
            official_solution_language="python",
            official_solution_code="print(1)",
            official_solution_explanation="Return one.",
            testcases_json="[]",
            validation_report_json="{}",
            status="validated",
            created_by=user.id,
        )
    )
    service = ProblemAuthoringAgentService(
        db,
        provider=FakeProvider(authored_payload()),
        validator=ProblemDraftValidationAdapter(EchoExecutor()),
    )
    draft, _ = service.create_draft(request_payload(), user)

    with pytest.raises(ValueError, match="Slug already exists: active-draft"):
        service.update_draft(str(draft.id), ProblemDraftUpdate(slug="active-draft"), user)


def test_create_draft_repairs_validation_failure_and_saves_validated_draft():
    db = FakeSession()
    provider = SequenceProvider(
        [
            authored_payload(public_count=0, hidden_count=0),
            authored_payload(public_count=1, hidden_count=0),
        ]
    )
    service = ProblemAuthoringAgentService(
        db,
        provider=provider,
        validator=ProblemDraftValidationAdapter(EchoExecutor()),
    )

    draft, _run = service.create_draft(request_payload(), admin_user())

    assert draft.status == "validated"
    assert len(provider.calls) == 2
    validation_steps = [step for step in db.data[AgentStep] if step.step_type == "validation"]
    assert len(validation_steps) == 2
    assert load_json(validation_steps[0].input_json, {})["attempt"] == 1
    assert load_json(validation_steps[1].input_json, {})["attempt"] == 2


def test_create_draft_persists_last_failed_draft_after_two_repairs():
    db = FakeSession()
    provider = SequenceProvider([authored_payload(public_count=0, hidden_count=0)] * 3)
    service = ProblemAuthoringAgentService(
        db,
        provider=provider,
        validator=ProblemDraftValidationAdapter(EchoExecutor()),
    )

    draft, _run = service.create_draft(request_payload(), admin_user())

    assert draft.status == "validation_failed"
    assert len(provider.calls) == 3
    report = json.loads(draft.validation_report_json)
    assert report["public_sample_count"] == 0
    failed_checks = {check["name"] for check in report["checks"] if not check["passed"]}
    assert {"testcase_count", "public_sample_count"} <= failed_checks


def test_validation_accepts_simple_problem_without_hidden_cases():
    db = FakeSession()
    service = ProblemAuthoringAgentService(
        db,
        provider=FakeProvider(authored_payload(public_count=1, hidden_count=0)),
        validator=ProblemDraftValidationAdapter(EchoExecutor()),
    )

    draft, _run = service.create_draft(request_payload(), admin_user())

    assert draft.status == "validated"
    report = json.loads(draft.validation_report_json)
    assert report["public_sample_count"] == 1
    assert report["hidden_testcase_count"] == 0


def test_validation_accepts_both_mode_with_acm_and_function_contracts():
    db = FakeSession()
    service = ProblemAuthoringAgentService(
        db,
        provider=FakeProvider(authored_both_payload()),
        validator=ProblemDraftValidationAdapter(EchoExecutor()),
    )
    request = ProblemAuthoringRequest(
        topic="echo value",
        difficulty="easy",
        tags=["io"],
        mode="both",
        target_language="python",
        locale="en",
        model_profile="default",
    )

    draft, _run = service.create_draft(request, admin_user())

    assert draft.status == "validated"
    assert draft.mode == "both"
    report = json.loads(draft.validation_report_json)
    passed_checks = {check["name"] for check in report["checks"] if check["passed"]}
    assert {"input_format", "output_format", "function_signature", "function_testcase_inputs"} <= passed_checks


def test_authoring_output_match_accepts_json_string_expected_value():
    validator = ProblemDraftValidationAdapter(EchoExecutor())

    assert validator._outputs_match("qiu qiu", '"qiu qiu"')


def test_model_validation_error_sanitizes_raw_payload_values():
    payload = json.loads(authored_payload())
    payload["time_limit"] = "SECRET_TIME_LIMIT"
    payload["hidden_testcases"][0]["input"] = "SECRET_HIDDEN_INPUT"
    service = ProblemAuthoringAgentService(FakeSession(), provider=FakeProvider(json.dumps(payload)))

    with pytest.raises(ValueError) as exc_info:
        service._parse_model_response(json.dumps(payload))

    message = str(exc_info.value)
    assert "time_limit" in message
    assert "int_parsing" in message
    assert "SECRET" not in message
    assert "hidden_testcases" not in message


def test_function_call_arg_normalizer_accepts_deepseek_shapes():
    assert normalize_function_call_args('{"nums":[-1,0,1]}', ["nums"]) == [[-1, 0, 1]]
    assert normalize_function_call_args("[[2,7,11,15],9]", ["nums", "target"]) == [[2, 7, 11, 15], 9]
    assert normalize_function_call_args('{"args":[[2,7,11,15],9]}', ["nums", "target"]) == [[2, 7, 11, 15], 9]


def test_function_call_arg_normalizer_rejects_count_mismatch_safely():
    with pytest.raises(ValueError, match="argument count"):
        normalize_function_call_args("[[2,7,11,15]]", ["nums", "target"])


def test_approve_draft_creates_problem_testcases_and_solution_with_hidden_cases():
    db = FakeSession()
    service = ProblemAuthoringAgentService(
        db,
        provider=FakeProvider(authored_payload()),
        validator=ProblemDraftValidationAdapter(EchoExecutor()),
    )
    user = admin_user()
    draft, _run = service.create_draft(request_payload(), user)

    approved = service.approve_draft(str(draft.id), user)

    assert approved.status == "approved"
    assert len(db.data[Problem]) == 1
    assert db.data[Problem][0].mode == "acm"
    assert db.data[Problem][0].input_format == "One value."
    assert len(db.data[OJTestCase]) == 8
    assert len(db.data[Solution]) == 1
    hidden_cases = [testcase for testcase in db.data[OJTestCase] if testcase.is_hidden]
    assert len(hidden_cases) == 6
    assert all(testcase.is_sample is False for testcase in hidden_cases)


def test_approving_approved_draft_is_idempotent():
    db = FakeSession()
    service = ProblemAuthoringAgentService(
        db,
        provider=FakeProvider(authored_payload()),
        validator=ProblemDraftValidationAdapter(EchoExecutor()),
    )
    user = admin_user()
    draft, _run = service.create_draft(request_payload(), user)

    service.approve_draft(str(draft.id), user)
    service.approve_draft(str(draft.id), user)

    assert len(db.data[Problem]) == 1


def test_validation_failure_keeps_draft_validation_failed():
    db = FakeSession()
    service = ProblemAuthoringAgentService(
        db,
        provider=FakeProvider(authored_payload()),
        validator=ProblemDraftValidationAdapter(FailingExecutor()),
    )

    draft, _run = service.create_draft(request_payload(), admin_user())

    assert draft.status == "validation_failed"
    report = json.loads(draft.validation_report_json)
    assert report["passed"] is False
    assert any(check["name"] == "official_solution" for check in report["checks"] if not check["passed"])


def test_validation_failure_sanitizes_executor_error_detail():
    payload = json.loads(authored_payload())
    payload["hidden_testcases"][0]["input"] = "SECRET_HIDDEN_INPUT"
    payload["hidden_testcases"][0]["output"] = "SECRET_EXPECTED_OUTPUT"
    db = FakeSession()
    service = ProblemAuthoringAgentService(
        db,
        provider=FakeProvider(json.dumps(payload)),
        validator=ProblemDraftValidationAdapter(SecretFailingExecutor()),
    )

    draft, run = service.create_draft(request_payload(), admin_user())

    assert draft.status == "validation_failed"
    report = draft.validation_report_json
    run_output = run.output_json
    assert "SECRET_HIDDEN_INPUT" not in report
    assert "SECRET_EXPECTED_OUTPUT" not in report
    assert "SECRET_ACTUAL_OUTPUT" not in report
    assert "SECRET_HIDDEN_INPUT" not in run_output
    assert "SECRET_EXPECTED_OUTPUT" not in run_output
    assert "SECRET_ACTUAL_OUTPUT" not in run_output


def test_validation_repair_prompt_omits_hidden_testcase_content():
    payload = json.loads(authored_payload())
    payload["hidden_testcases"][0]["input"] = "SECRET_HIDDEN_INPUT"
    payload["hidden_testcases"][0]["output"] = "SECRET_EXPECTED_OUTPUT"
    provider = SequenceProvider([json.dumps(payload)] * 3)
    db = FakeSession()
    service = ProblemAuthoringAgentService(
        db,
        provider=provider,
        validator=ProblemDraftValidationAdapter(SecretFailingExecutor()),
    )

    draft, run = service.create_draft(request_payload(), admin_user())

    assert draft.status == "validation_failed"
    prompts = "\n".join(user_prompt for _system_prompt, user_prompt in provider.calls)
    assert "SECRET_HIDDEN_INPUT" not in prompts
    assert "SECRET_EXPECTED_OUTPUT" not in prompts
    assert "SECRET_ACTUAL_OUTPUT" not in prompts
    assert "SECRET_HIDDEN_INPUT" not in run.output_json
    assert "SECRET_EXPECTED_OUTPUT" not in run.output_json


def test_admin_can_manage_problem_testcases_with_hidden_content():
    db = FakeSession()
    problem = Problem(
        id=uuid.uuid4(),
        title="Admin Case",
        slug="admin-case",
        description="Admin testcase management.",
        difficulty=Difficulty.EASY,
        mode="acm",
    )
    hidden_case = OJTestCase(
        id=uuid.uuid4(),
        problem_id=problem.id,
        input="SECRET_ADMIN_INPUT",
        output="SECRET_ADMIN_OUTPUT",
        is_hidden=True,
        is_sample=False,
        score=10,
        order=1,
    )
    db.add(problem)
    db.add(hidden_case)
    user = admin_user()

    list_response = list_testcases(str(problem.id), db, user)
    assert list_response["data"][0]["input"] == "SECRET_ADMIN_INPUT"

    create_response = create_testcase(
        str(problem.id),
        AdminTestCaseCreate(input="2", output="2", is_hidden=False, is_sample=True, score=5),
        db,
        user,
    )
    created = create_response["data"]
    assert created["order"] == 2
    assert created["is_sample"] is True

    patch_response = update_testcase(
        str(hidden_case.id),
        AdminTestCaseUpdate(input="updated", output="ok", is_hidden=False, order=3),
        db,
        user,
    )
    patched = patch_response["data"]
    assert patched["input"] == "updated"
    assert patched["is_hidden"] is False
    assert patched["order"] == 3

    delete_response = delete_testcase(created["id"], db, user)
    assert delete_response["success"] is True
    assert len(db.data[OJTestCase]) == 1


def test_admin_can_delete_problem_and_related_rows():
    db = FakeSession()
    user = admin_user()
    problem = Problem(
        id=uuid.uuid4(),
        title="Delete Me",
        slug="delete-me",
        description="Temporary problem.",
        difficulty=Difficulty.EASY,
        mode="acm",
    )
    testcase = OJTestCase(
        id=uuid.uuid4(),
        problem_id=problem.id,
        input="1",
        output="1",
        is_hidden=False,
        is_sample=True,
        score=10,
        order=1,
    )
    submission = Submission(
        id=uuid.uuid4(),
        user_id=user.id,
        problem_id=problem.id,
        code="print(1)",
        language="python",
    )
    testcase_result = TestCaseResult(
        id=uuid.uuid4(),
        submission_id=submission.id,
        testcase_id=testcase.id,
        status=SubmissionResult.AC,
        input="1",
        expected_output="1",
        actual_output="1",
    )
    solution = Solution(
        id=uuid.uuid4(),
        problem_id=problem.id,
        language="python",
        code="print(1)",
        explanation="Return one.",
        is_official=True,
    )
    draft = ProblemDraft(
        id=uuid.uuid4(),
        title="Delete Me",
        slug="delete-me",
        description="Temporary problem.",
        difficulty="easy",
        tags="[]",
        mode="acm",
        official_solution_language="python",
        official_solution_code="print(1)",
        official_solution_explanation="Return one.",
        testcases_json="[]",
        validation_report_json="{}",
        status="approved",
        created_by=user.id,
        approved_problem_id=problem.id,
    )
    for item in [problem, testcase, submission, testcase_result, solution, draft]:
        db.add(item)

    response = delete_problem(str(problem.id), db, user)

    assert response["success"] is True
    assert response["deleted"]["testcases"] == 1
    assert response["deleted"]["submissions"] == 1
    assert response["deleted"]["testcase_results"] == 1
    assert response["deleted"]["solutions"] == 1
    assert response["deleted"]["draft_links_cleared"] == 1
    assert db.data[Problem] == []
    assert db.data[OJTestCase] == []
    assert db.data[Submission] == []
    assert db.data[TestCaseResult] == []
    assert db.data[Solution] == []
    assert draft.approved_problem_id is None
