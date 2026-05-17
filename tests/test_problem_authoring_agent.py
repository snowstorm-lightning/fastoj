import json
import uuid
from datetime import datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.ai.providers import BaseAIProvider
from backend.api.admin_agent import router as admin_agent_router
from backend.api.auth import get_current_user
from backend.core.config import settings
from backend.core.database import get_db
from backend.models import AgentRun, AgentStep, Problem, ProblemDraft, Solution, User
from backend.models import TestCase as OJTestCase
from backend.schemas.problem_authoring import ProblemAuthoringRequest
from backend.services.problem_authoring_agent import (
    ProblemAuthoringAgentService,
    ProblemDraftValidationAdapter,
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


class FakeProvider(BaseAIProvider):
    def __init__(self, raw: str):
        self.raw = raw

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        return self.raw


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


def admin_user() -> User:
    return User(id=uuid.uuid4(), username="admin", email="admin@example.com", password_hash="x", role="admin")


def make_test_app(db: FakeSession, user: User | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(admin_agent_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db
    if user is not None:
        app.dependency_overrides[get_current_user] = lambda: user
    return app


def test_non_admin_agent_endpoints_return_403():
    db = FakeSession()
    user = User(id=uuid.uuid4(), username="user", email="user@example.com", password_hash="x", role="user")
    client = TestClient(make_test_app(db, user))

    endpoints = [
        ("post", "/api/v1/admin/agent/problem-drafts", request_payload().model_dump()),
        ("get", "/api/v1/admin/agent/runs/00000000-0000-0000-0000-000000000000", None),
        ("get", "/api/v1/admin/problem-drafts", None),
        ("get", "/api/v1/admin/problem-drafts/00000000-0000-0000-0000-000000000000", None),
        ("post", "/api/v1/admin/problem-drafts/00000000-0000-0000-0000-000000000000/approve", None),
        ("post", "/api/v1/admin/problem-drafts/00000000-0000-0000-0000-000000000000/reject", None),
    ]
    for method, path, body in endpoints:
        response = getattr(client, method)(path, json=body) if body is not None else getattr(client, method)(path)
        assert response.status_code == 403


def test_ai_disabled_endpoint_returns_503_and_does_not_create_problem(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "disabled")
    db = FakeSession()
    client = TestClient(make_test_app(db, admin_user()))

    response = client.post("/api/v1/admin/agent/problem-drafts", json=request_payload().model_dump())

    assert response.status_code == 503
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
