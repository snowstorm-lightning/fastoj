from types import SimpleNamespace

import httpx
import pytest

from backend.ai.config import AIConfig
from backend.ai.providers.base import AIProviderUnavailableError
from backend.ai.providers.disabled import DisabledAIProvider
from backend.ai.providers.openai_compatible import OpenAICompatibleProvider
from backend.ai.schemas import AIHintResponse
from backend.ai.service import AIService
from backend.models import Difficulty, SubmissionResult, SubmissionStatus


def _problem():
    return SimpleNamespace(
        title="Two Sum",
        description="Find two numbers.",
        difficulty=Difficulty.EASY,
        tags=["Array", "Hash Table"],
        time_limit=1000,
        memory_limit=256,
    )


def test_disabled_provider_raises_clear_error():
    with pytest.raises(AIProviderUnavailableError):
        DisabledAIProvider().complete_json("", "")


def test_openai_provider_wraps_connection_errors(monkeypatch):
    def raise_connect_error(*args, **kwargs):
        request = httpx.Request("POST", "http://host.docker.internal:8080/v1/chat/completions")
        raise httpx.ConnectError("[Errno 111] Connection refused", request=request)

    monkeypatch.setattr(httpx, "post", raise_connect_error)
    provider = OpenAICompatibleProvider(
        AIConfig(
            provider="openai_compatible",
            base_url="http://host.docker.internal:8080/v1",
            api_key="sk-no-key-required",
            model="qwen2.5-coder-3b-instruct",
            timeout_seconds=1,
            max_output_tokens=128,
        )
    )

    with pytest.raises(AIProviderUnavailableError, match="AI provider is unreachable"):
        provider.complete_json("system", "user")


def test_explain_context_does_not_include_hidden_case_details():
    hidden = SimpleNamespace(
        is_hidden=True,
        status=SubmissionResult.WA,
        input="SECRET_INPUT",
        expected_output="SECRET_EXPECTED",
        actual_output="SECRET_ACTUAL",
        execute_time=1,
        memory_used=1,
    )
    public = SimpleNamespace(
        is_hidden=False,
        status=SubmissionResult.WA,
        input="1 2",
        expected_output="3",
        actual_output="4",
        execute_time=1,
        memory_used=1,
    )
    submission = SimpleNamespace(
        problem=_problem(),
        language="python",
        code="print('x')",
        status=SubmissionStatus.FINISHED,
        result=SubmissionResult.WA,
        error_message=None,
        testcase_results=[public, hidden],
    )

    context = AIService(SimpleNamespace())._submission_context(submission)
    serialized = str(context)
    assert "SECRET_INPUT" not in serialized
    assert "SECRET_EXPECTED" not in serialized
    assert "SECRET_ACTUAL" not in serialized
    assert "Hidden testcase failed" in serialized
    assert "1 2" in serialized


def test_explain_wraps_non_json_provider_response():
    service = AIService(SimpleNamespace())
    response = service._parse_explain("plain text response", {"verdict": "wrong_answer"})
    assert response.verdict == "wrong_answer"
    assert response.full_solution_revealed is False


def test_ai_response_parser_accepts_scalar_fields_from_provider():
    service = AIService(SimpleNamespace())

    hint = service._parse_review(
        '{"summary":"ok","risks":"Hash Table","io_format_notes":"stdin","edge_cases_to_check":"empty","complexity_comment":"O(n)","suggested_next_action":"retry"}'
    )
    assert hint.risks == ["Hash Table"]
    assert hint.io_format_notes == ["stdin"]
    assert hint.edge_cases_to_check == ["empty"]

    explain = service._parse_explain(
        '{"summary":"bad","verdict":"wrong_answer","likely_causes":"off by one","suspicious_code_regions":"line 2","public_case_analysis":"output mismatch","minimal_fix_hint":"check index","edge_cases_to_check":"duplicates","complexity_comment":"O(n)","next_action":"rerun"}',
        {"verdict": "wrong_answer"},
    )
    assert explain.likely_causes == ["off by one"]
    assert explain.suspicious_code_regions[0].reason == "line 2"
    assert explain.public_case_analysis[0].observation == "output mismatch"
    assert explain.edge_cases_to_check == ["duplicates"]


def test_ai_response_parser_accepts_null_text_fields_from_provider():
    service = AIService(SimpleNamespace())

    explain = service._parse_explain(
        '{"summary":null,"verdict":null,"minimal_fix_hint":null,"complexity_comment":null,"next_action":null}',
        {"verdict": "accepted"},
    )
    assert explain.verdict == "accepted"
    assert explain.summary
    assert explain.minimal_fix_hint
    assert explain.complexity_comment
    assert explain.next_action

    review = service._parse_review(
        '{"summary":null,"risks":null,"io_format_notes":null,"edge_cases_to_check":null,"complexity_comment":null,"suggested_next_action":null}'
    )
    assert review.summary
    assert review.complexity_comment
    assert review.suggested_next_action


def test_chat_parser_never_marks_full_solution_revealed():
    service = AIService(SimpleNamespace())
    response = service._parse_chat(
        '{"message":null,"suggested_actions":"run public cases","full_solution_revealed":true}'
    )
    assert response.message
    assert response.suggested_actions == ["run public cases"]
    assert response.full_solution_revealed is False


def test_hint_parser_accepts_scalar_focus():
    service = AIService(SimpleNamespace())
    data = {"level": 1, "hint": "Use a dictionary.", "focus": "Hash Table", "full_solution_revealed": True}
    data["focus"] = service._coerce_string_list(data.get("focus"))
    data["full_solution_revealed"] = False
    response = AIHintResponse.model_validate(data)
    assert response.full_solution_revealed is False
    assert data["focus"] == ["Hash Table"]
