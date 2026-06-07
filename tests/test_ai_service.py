from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

from backend.ai.config import AIConfig
from backend.ai.profiles import list_ai_profiles, refresh_ai_profiles, resolve_ai_config
from backend.ai.providers.base import AIProviderEmptyResponseError, AIProviderUnavailableError
from backend.ai.providers.disabled import DisabledAIProvider
from backend.ai.providers.openai_compatible import OpenAICompatibleProvider
from backend.ai.schemas import AIHintResponse
from backend.ai.service import AIService
from backend.api.ai import hint_problem
from backend.api.ai import profiles as ai_profiles_endpoint
from backend.core.config import settings
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


def _user(role: str = "user", permissions: list[str] | None = None):
    return SimpleNamespace(role=role, content_admin_permissions=permissions or [])


def _configure_openai(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "openai_compatible")
    monkeypatch.setattr(settings, "AI_BASE_URL", "http://default.local/v1")
    monkeypatch.setattr(settings, "AI_API_KEY", "sk-default")
    monkeypatch.setattr(settings, "AI_MODEL", "default-model")
    monkeypatch.setattr(settings, "AI_DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setattr(settings, "AI_DEEPSEEK_API_KEY", "sk-deepseek")
    monkeypatch.setattr(settings, "AI_DEEPSEEK_MODEL", "deepseek-model")
    monkeypatch.setattr(settings, "AI_DEEPSEEK_PRO_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setattr(settings, "AI_DEEPSEEK_PRO_API_KEY", "sk-deepseek")
    monkeypatch.setattr(settings, "AI_DEEPSEEK_PRO_MODEL", "deepseek-pro-model")
    monkeypatch.setattr(settings, "AI_DEEPSEEK_PRO_TIMEOUT_SECONDS", 120)
    monkeypatch.setattr(settings, "AI_DEEPSEEK_PRO_MAX_OUTPUT_TOKENS", 4000)
    monkeypatch.setattr(settings, "AI_QWEN_BASE_URL", "http://qwen.local/v1")
    monkeypatch.setattr(settings, "AI_QWEN_API_KEY", "sk-no-key-required")
    monkeypatch.setattr(settings, "AI_QWEN_MODEL", "qwen-model")


def _models_response(url: str, model_ids: list[str]) -> httpx.Response:
    return httpx.Response(
        200,
        json={"data": [{"id": model_id} for model_id in model_ids]},
        request=httpx.Request("GET", url),
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


def test_openai_provider_rejects_unconfigured_deepseek_key():
    provider = OpenAICompatibleProvider(
        AIConfig(
            provider="openai_compatible",
            base_url="https://api.deepseek.com",
            api_key="",
            model="deepseek-v4-flash",
            timeout_seconds=1,
            max_output_tokens=128,
        )
    )

    with pytest.raises(AIProviderUnavailableError, match="DeepSeek profile is not configured"):
        provider.complete_json("system", "user")


def test_openai_provider_rejects_empty_length_response_with_metadata(monkeypatch):
    def fake_post(url: str, *args, **kwargs):
        return httpx.Response(
            200,
            json={
                "model": "deepseek-v4-pro",
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "reasoning_content": "thinking",
                        },
                    }
                ],
                "usage": {
                    "completion_tokens": 4000,
                    "completion_tokens_details": {"reasoning_tokens": 4000},
                },
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = OpenAICompatibleProvider(
        AIConfig(
            provider="openai_compatible",
            base_url="http://provider.local/v1",
            api_key="sk-test",
            model="deepseek-v4-pro",
            timeout_seconds=1,
            max_output_tokens=4000,
        )
    )

    with pytest.raises(AIProviderEmptyResponseError, match="exhausted the output budget") as exc_info:
        provider.complete_json("system", "user")

    assert exc_info.value.metadata["finish_reason"] == "length"
    assert exc_info.value.metadata["content_len"] == 0
    assert exc_info.value.metadata["reasoning_tokens"] == 4000


def test_ai_profiles_disabled_provider_returns_no_user_options(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "disabled")

    user_profiles = list_ai_profiles(include_unavailable=False)
    admin_profiles = list_ai_profiles(include_unavailable=True, include_admin_only=True)

    assert user_profiles == []
    assert len(admin_profiles) == 4
    assert all(not profile.available for profile in admin_profiles)
    with pytest.raises(AIProviderUnavailableError, match="AI provider is unavailable"):
        resolve_ai_config("default")


def test_deepseek_missing_key_is_configuration_failure_without_network(monkeypatch):
    _configure_openai(monkeypatch)
    monkeypatch.setattr(settings, "AI_DEEPSEEK_API_KEY", "")
    monkeypatch.setattr(settings, "AI_DEEPSEEK_PRO_API_KEY", "")
    monkeypatch.setattr(settings, "AI_API_KEY", "sk-no-key-required")

    def fake_get(url: str, *args, **kwargs):
        assert "api.deepseek.com" not in url
        if "default.local" in url:
            return _models_response(url, ["default-model"])
        return _models_response(url, ["qwen-model"])

    monkeypatch.setattr(httpx, "get", fake_get)
    statuses = refresh_ai_profiles(force=True)

    assert statuses["deepseek"].configured is False
    assert statuses["deepseek"].available is False
    assert statuses["deepseek"].reason == "DeepSeek API key is not configured."
    assert statuses["deepseek-pro"].configured is False
    assert statuses["deepseek-pro"].available is False


def test_ai_profile_models_endpoint_controls_availability(monkeypatch):
    _configure_openai(monkeypatch)

    def fake_get(url: str, *args, **kwargs):
        if "default.local" in url:
            return _models_response(url, ["default-model"])
        if "deepseek" in url:
            return _models_response(url, ["deepseek-model", "deepseek-pro-model"])
        return _models_response(url, ["other-qwen-model"])

    monkeypatch.setattr(httpx, "get", fake_get)
    statuses = refresh_ai_profiles(force=True)

    assert statuses["default"].available is True
    assert statuses["deepseek-pro"].available is True
    assert statuses["deepseek"].available is True
    assert statuses["qwen-local"].available is False
    assert statuses["qwen-local"].reason == "Configured model is not available."


def test_ai_profiles_endpoint_filters_by_role(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "disabled")
    refresh_ai_profiles(force=True)

    assert ai_profiles_endpoint(_user("user")) == []
    admin_profiles = ai_profiles_endpoint(_user("admin"))

    assert len(admin_profiles) == 4
    assert all(profile.reason for profile in admin_profiles)


def test_regular_users_do_not_receive_admin_only_profiles(monkeypatch):
    _configure_openai(monkeypatch)

    def fake_get(url: str, *args, **kwargs):
        if "default.local" in url:
            return _models_response(url, ["default-model"])
        if "deepseek" in url:
            return _models_response(url, ["deepseek-model", "deepseek-pro-model"])
        return _models_response(url, ["qwen-model"])

    monkeypatch.setattr(httpx, "get", fake_get)
    refresh_ai_profiles(force=True)

    user_values = {profile.value for profile in ai_profiles_endpoint(_user("user"))}
    admin_values = {profile.value for profile in ai_profiles_endpoint(_user("admin"))}
    content_admin_values = {
        profile.value
        for profile in ai_profiles_endpoint(_user("content_admin", ["problem:create_own"]))
    }

    assert "deepseek-pro" not in user_values
    assert "deepseek-pro" in admin_values
    assert "deepseek-pro" in content_admin_values


def test_admin_only_model_profile_is_rejected_for_regular_users():
    with pytest.raises(HTTPException) as exc_info:
        hint_problem(
            "problem-1",
            SimpleNamespace(level=1, language=None, current_code=None, model_profile="deepseek-pro", locale="zh"),
            db=None,
            current_user=_user("user"),
        )

    assert getattr(exc_info.value, "status_code", None) == 403


def test_default_profile_routes_to_first_available_candidate(monkeypatch):
    _configure_openai(monkeypatch)

    def fake_get(url: str, *args, **kwargs):
        if "default.local" in url:
            return _models_response(url, ["different-model"])
        if "deepseek" in url:
            return _models_response(url, ["deepseek-model", "deepseek-pro-model"])
        raise httpx.ConnectError("refused", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    refresh_ai_profiles(force=True)

    config = resolve_ai_config("default")

    assert config.profile == "deepseek"
    assert config.model == "deepseek-model"


def test_deepseek_pro_profile_resolves_explicitly(monkeypatch):
    _configure_openai(monkeypatch)

    config = resolve_ai_config("deepseek-pro")

    assert config.profile == "deepseek-pro"
    assert config.model == "deepseek-pro-model"
    assert config.max_output_tokens == 4000


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
