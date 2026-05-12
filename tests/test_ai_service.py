from types import SimpleNamespace

import pytest

from backend.ai.providers.base import AIProviderUnavailableError
from backend.ai.providers.disabled import DisabledAIProvider
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
