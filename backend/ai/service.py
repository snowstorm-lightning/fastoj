import json
import re
from typing import Any

from sqlalchemy.orm import Session

from backend.ai.config import AIConfig
from backend.ai.prompts import chat, explain_submission, hint, review_code
from backend.ai.providers import AIProviderUnavailableError, BaseAIProvider, build_provider
from backend.ai.schemas import AIChatResponse, AIExplainResponse, AIHintResponse, AIReviewResponse
from backend.models import Problem, Submission, SubmissionResult, TestCaseResult, User

RESULT_TO_VERDICT = {
    SubmissionResult.AC: "accepted",
    SubmissionResult.WA: "wrong_answer",
    SubmissionResult.TLE: "time_limit",
    SubmissionResult.MLE: "memory_limit",
    SubmissionResult.CE: "compile_error",
    SubmissionResult.RE: "runtime_error",
    SubmissionResult.SE: "system_error",
}


class AIService:
    def __init__(self, db: Session, provider: BaseAIProvider | None = None, model_profile: str | None = None):
        self.db = db
        self.config = AIConfig.from_settings(model_profile)
        self.provider = provider or build_provider(self.config)

    def explain_submission(self, submission_id: str, current_user: User, locale: str = "en") -> AIExplainResponse:
        submission = self._get_allowed_submission(submission_id, current_user)
        context = self._submission_context(submission)
        context["response_language"] = self._response_language(locale)
        raw = self.provider.complete_json(
            self._localized_system_prompt(explain_submission.SYSTEM_PROMPT, locale),
            explain_submission.build_prompt(context),
        )
        return self._parse_explain(raw, context)

    def review_submission(self, submission_id: str, current_user: User, locale: str = "en") -> AIReviewResponse:
        submission = self._get_allowed_submission(submission_id, current_user)
        context = self._submission_context(submission, include_results=False)
        context["response_language"] = self._response_language(locale)
        raw = self.provider.complete_json(
            self._localized_system_prompt(review_code.SYSTEM_PROMPT, locale),
            review_code.build_prompt(context),
        )
        return self._parse_review(raw)

    def chat_submission(
        self,
        submission_id: str,
        message: str,
        current_user: User,
        locale: str = "en",
    ) -> AIChatResponse:
        submission = self._get_allowed_submission(submission_id, current_user)
        context = self._submission_context(submission)
        context["response_language"] = self._response_language(locale)
        context["user_question"] = self._redact_secrets(message)
        context["rules"] = [
            "Use only supplied public testcase details.",
            "Do not reveal hidden testcase details.",
            "Do not return a complete accepted solution.",
        ]
        raw = self.provider.complete_json(
            self._localized_system_prompt(chat.SYSTEM_PROMPT, locale),
            chat.build_prompt(context),
        )
        return self._parse_chat(raw)

    def hint_problem(
        self,
        problem_id: str,
        level: int,
        language: str | None,
        current_code: str | None,
        locale: str = "en",
    ) -> AIHintResponse:
        problem = self.db.query(Problem).filter(Problem.id == problem_id, Problem.is_public.is_(True)).first()
        if not problem:
            raise ValueError("Problem not found")
        context = {
            "problem": self._problem_context(problem),
            "level": level,
            "language": language,
            "response_language": self._response_language(locale),
            "current_code": self._redact_secrets(current_code or ""),
            "rules": [
                "Do not use hidden testcases.",
                "Do not return complete accepted code.",
            ],
        }
        raw = self.provider.complete_json(self._localized_system_prompt(hint.SYSTEM_PROMPT, locale), hint.build_prompt(context))
        data = self._extract_json(raw)
        data.setdefault("level", level)
        data.setdefault("hint", self._fallback_hint(level, problem))
        data["focus"] = self._coerce_string_list(data.get("focus"))
        data["full_solution_revealed"] = False
        return AIHintResponse.model_validate(data)

    def _get_allowed_submission(self, submission_id: str, current_user: User) -> Submission:
        query = self.db.query(Submission).filter(Submission.id == submission_id)
        if current_user.role != "admin":
            query = query.filter(Submission.user_id == current_user.id)
        submission = query.first()
        if not submission:
            raise ValueError("Submission not found")
        return submission

    def _submission_context(self, submission: Submission, include_results: bool = True) -> dict[str, Any]:
        problem = submission.problem
        public_results: list[dict[str, Any]] = []
        hidden_failed = False
        if include_results:
            for index, result in enumerate(submission.testcase_results, start=1):
                if result.is_hidden:
                    hidden_failed = hidden_failed or result.status != SubmissionResult.AC
                    continue
                public_results.append(self._public_result_context(index, result))

        return {
            "problem": self._problem_context(problem),
            "language": submission.language,
            "code": self._redact_secrets(submission.code),
            "submission_status": submission.status.value,
            "submission_result": submission.result.value if submission.result else None,
            "verdict": RESULT_TO_VERDICT.get(submission.result, "unknown") if submission.result else "unknown",
            "compile_or_runtime_error": submission.error_message,
            "public_testcase_results": public_results,
            "hidden_failure_notice": (
                "Hidden testcase failed. Hidden input, expected output, and actual output are not available."
                if hidden_failed
                else None
            ),
        }

    def _problem_context(self, problem: Problem) -> dict[str, Any]:
        return {
            "title": problem.title,
            "description": problem.description,
            "difficulty": problem.difficulty.value,
            "tags": problem.tags or [],
            "time_limit": problem.time_limit,
            "memory_limit": problem.memory_limit,
        }

    def _public_result_context(self, index: int, result: TestCaseResult) -> dict[str, Any]:
        return {
            "case_index": index,
            "status": result.status.value,
            "input": result.input,
            "expected_output": result.expected_output,
            "actual_output": result.actual_output,
            "execute_time": result.execute_time,
            "memory_used": result.memory_used,
        }

    def _parse_explain(self, raw: str, context: dict[str, Any]) -> AIExplainResponse:
        data = self._extract_json(raw)
        data["summary"] = self._coerce_text(data.get("summary"), raw.strip()[:500] or "AI returned an empty explanation.")
        data["verdict"] = self._coerce_text(data.get("verdict"), context.get("verdict") or "unknown")
        data["verdict"] = self._coerce_verdict(data.get("verdict"), context.get("verdict") or "unknown")
        data["likely_causes"] = self._coerce_string_list(data.get("likely_causes"))
        data["suspicious_code_regions"] = self._coerce_regions(data.get("suspicious_code_regions"))
        data["public_case_analysis"] = self._coerce_public_case_analysis(data.get("public_case_analysis"))
        data["minimal_fix_hint"] = self._coerce_text(
            data.get("minimal_fix_hint"),
            "Focus on the first failing public case or likely boundary categories.",
        )
        data["edge_cases_to_check"] = self._coerce_string_list(data.get("edge_cases_to_check"))
        data["complexity_comment"] = self._coerce_text(
            data.get("complexity_comment"),
            "No reliable complexity comment was returned.",
        )
        data["next_action"] = self._coerce_text(data.get("next_action"), "Revise the code and run public cases again.")
        data["full_solution_revealed"] = False
        return AIExplainResponse.model_validate(data)

    def _parse_review(self, raw: str) -> AIReviewResponse:
        data = self._extract_json(raw)
        data["summary"] = self._coerce_text(data.get("summary"), raw.strip()[:500] or "AI returned an empty review.")
        data["risks"] = self._coerce_string_list(data.get("risks"))
        data["io_format_notes"] = self._coerce_string_list(data.get("io_format_notes"))
        data["edge_cases_to_check"] = self._coerce_string_list(data.get("edge_cases_to_check"))
        data["complexity_comment"] = self._coerce_text(
            data.get("complexity_comment"),
            "No reliable complexity comment was returned.",
        )
        data["suggested_next_action"] = self._coerce_text(
            data.get("suggested_next_action"),
            "Run public cases, then submit when the behavior matches.",
        )
        return AIReviewResponse.model_validate(data)

    def _parse_chat(self, raw: str) -> AIChatResponse:
        data = self._extract_json(raw)
        data["message"] = self._coerce_text(data.get("message"), raw.strip()[:800] or "AI returned an empty response.")
        data["suggested_actions"] = self._coerce_string_list(data.get("suggested_actions"))
        data["full_solution_revealed"] = False
        return AIChatResponse.model_validate(data)

    def _extract_json(self, raw: str) -> dict[str, Any]:
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                    return data if isinstance(data, dict) else {}
                except json.JSONDecodeError:
                    return {}
        return {}

    def _coerce_string_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(item) for item in value if item is not None]
        return [str(value)]

    def _coerce_regions(self, value: Any) -> list[dict[str, Any]]:
        if value is None:
            return []
        raw_items = value if isinstance(value, list) else [value]
        regions: list[dict[str, Any]] = []
        for item in raw_items:
            if isinstance(item, str):
                regions.append({"reason": item})
            elif isinstance(item, dict):
                regions.append(
                    {
                        "line_start": item.get("line_start"),
                        "line_end": item.get("line_end"),
                        "reason": str(item.get("reason") or item.get("description") or item),
                    }
                )
            elif item is not None:
                regions.append({"reason": str(item)})
        return regions

    def _coerce_public_case_analysis(self, value: Any) -> list[dict[str, Any]]:
        if value is None:
            return []
        raw_items = value if isinstance(value, list) else [value]
        cases: list[dict[str, Any]] = []
        for index, item in enumerate(raw_items, start=1):
            if isinstance(item, str):
                cases.append(
                    {
                        "case_index": index,
                        "observation": item,
                        "expected_summary": "See the public expected output.",
                        "actual_summary": "See the public actual output.",
                    }
                )
            elif isinstance(item, dict):
                cases.append(
                    {
                        "case_index": int(item.get("case_index") or index),
                        "observation": str(item.get("observation") or item.get("summary") or item),
                        "expected_summary": str(item.get("expected_summary") or item.get("expected") or ""),
                        "actual_summary": str(item.get("actual_summary") or item.get("actual") or ""),
                    }
                )
        return cases

    def _coerce_verdict(self, value: Any, fallback: str) -> str:
        allowed = {
            "accepted",
            "wrong_answer",
            "time_limit",
            "memory_limit",
            "compile_error",
            "runtime_error",
            "system_error",
            "unknown",
        }
        verdict = str(value or fallback)
        return verdict if verdict in allowed else fallback

    def _redact_secrets(self, text: str) -> str:
        patterns = [
            r"sk-[A-Za-z0-9_\-]+",
            r"postgresql://[^\s]+",
            r"redis://[^\s]+",
            r"SECRET_KEY\s*=\s*[^\s]+",
            r"Authorization:\s*Bearer\s+[A-Za-z0-9_\-.]+",
        ]
        redacted = text
        for pattern in patterns:
            redacted = re.sub(pattern, "[REDACTED]", redacted, flags=re.IGNORECASE)
        return redacted

    def _fallback_hint(self, level: int, problem: Problem) -> str:
        if level == 1:
            return f"Start from the main pattern suggested by the tags: {', '.join(problem.tags or [])}."
        if level == 2:
            return "Identify the invariant that lets you avoid checking every possible answer."
            return "Write pseudocode first: parse input, maintain the needed state, update the answer, then print exactly the required output."

    def _coerce_text(self, value: Any, fallback: str) -> str:
        if value is None:
            return fallback
        text = str(value).strip()
        return text or fallback

    def _response_language(self, locale: str) -> str:
        return "Simplified Chinese" if locale == "zh" else "English"

    def _localized_system_prompt(self, prompt: str, locale: str) -> str:
        if locale == "zh":
            return f"{prompt}\nRespond in Simplified Chinese for every user-facing string inside the JSON values."
        return f"{prompt}\nRespond in English for every user-facing string inside the JSON values."


__all__ = ["AIProviderUnavailableError", "AIService"]
