import json
import re
import uuid
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.ai.profiles import resolve_ai_config
from backend.ai.prompts import problem_authoring
from backend.ai.providers import AIProviderUnavailableError, BaseAIProvider, build_provider
from backend.core.code_normalization import normalize_source_code
from backend.core.languages import Language
from backend.core.locales import ai_response_language, normalize_locale
from backend.core.time import utc_now
from backend.models import (
    AgentRun,
    AgentStep,
    Difficulty,
    Problem,
    ProblemDraft,
    Solution,
    TestCase,
    User,
)
from backend.sandbox.executor import SandboxExecutor
from backend.schemas.problem_authoring import (
    AuthoredOfficialSolution,
    AuthoredProblemDraft,
    AuthoredTestCase,
    ProblemAuthoringRequest,
    ProblemDraftUpdate,
    ProblemImportRequest,
)
from backend.services.function_mode import wrap_function_submission

MAX_AUTHORING_REPAIR_ATTEMPTS = 2
SLUG_RESERVED_DRAFT_STATUSES = {"draft", "validating", "validated"}


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def load_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return slug.strip("-") or "generated-problem"


def normalize_function_call_args(raw: str, parameter_names: list[str]) -> list[Any]:
    """Accept common AI-authored function testcase shapes without exposing values."""

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return []
    try:
        if len(lines) > 1:
            args = [json.loads(line) for line in lines]
            names = [name for name in parameter_names if name not in {"self", "cls"}]
            if names and len(args) != len(names):
                raise ValueError("Function-mode testcase input argument count does not match function_signature.")
            return args
        value = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise ValueError("Function-mode testcase input must be valid JSON.") from exc

    names = [name for name in parameter_names if name not in {"self", "cls"}]
    if isinstance(value, dict) and names:
        if all(name in value for name in names):
            args = [value[name] for name in names]
            return args
        args_value = value.get("args")
        if isinstance(args_value, list):
            args = args_value
            if len(args) != len(names):
                raise ValueError("Function-mode testcase input argument count does not match function_signature.")
            return args
        return [value]
    if isinstance(value, list) and len(names) > 1 and len(value) == len(names):
        return value
    args = value if isinstance(value, list) and not names else [value]
    if names and len(args) != len(names):
        raise ValueError("Function-mode testcase input argument count does not match function_signature.")
    return args


class ProblemDraftValidationAdapter:
    """Validates generated drafts through the same sandbox executor used by judging."""

    def __init__(self, executor: SandboxExecutor | None = None):
        self.executor = executor or SandboxExecutor()

    def validate(
        self,
        draft: AuthoredProblemDraft,
        testcases: list[dict[str, Any]],
        required_languages: list[str] | None = None,
    ) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []

        def check(name: str, passed: bool, message: str) -> None:
            checks.append({"name": name, "passed": passed, "message": message})

        required_fields = {
            "title": draft.title,
            "description": draft.description,
            "official_solutions": draft.official_solutions,
            "time_complexity": draft.time_complexity,
            "space_complexity": draft.space_complexity,
        }
        for field, value in required_fields.items():
            if isinstance(value, list):
                check(field, bool(value), f"{field} is required")
            else:
                check(field, bool(str(value or "").strip()), f"{field} is required")

        requires_acm = draft.mode in {"acm", "both"}
        requires_function = draft.mode in {"function", "both"}
        if requires_acm:
            check("input_format", bool(str(draft.input_format or "").strip()), "ACM mode requires input_format")
            check("output_format", bool(str(draft.output_format or "").strip()), "ACM mode requires output_format")
        if requires_function:
            check(
                "function_signature",
                bool(str(draft.function_signature or "").strip()),
                "Function mode requires function_signature",
            )

        public_count = sum(1 for testcase in testcases if not testcase["is_hidden"])
        hidden_count = sum(1 for testcase in testcases if testcase["is_hidden"])
        total_count = len(testcases)
        solution_languages = [solution.language for solution in draft.official_solutions]
        missing_languages = sorted(set(required_languages or []) - set(solution_languages))
        check("testcase_count", total_count >= 1, "At least 1 testcase is required")
        check("public_sample_count", public_count >= 1, "At least 1 public sample testcase is required")
        check(
            "official_solution_languages",
            not missing_languages,
            f"Missing official solutions for: {', '.join(missing_languages)}",
        )
        check(
            "non_empty_outputs",
            all(str(testcase.get("output") or "").strip() for testcase in testcases),
            "Every expected output must be non-empty",
        )

        if requires_function and str(draft.function_signature or "").strip():
            try:
                parameter_names = self._function_parameters(draft)
                for testcase in testcases:
                    normalize_function_call_args(str(testcase.get("input") or ""), parameter_names)
                check(
                    "function_testcase_inputs",
                    True,
                    "Function testcase inputs are valid JSON argument values",
                )
            except ValueError as exc:
                check("function_testcase_inputs", False, str(exc))

        case_results = []
        if all(item["passed"] for item in checks):
            try:
                case_results = self._run_solution(draft, testcases)
            except ValueError as exc:
                case_results = [
                    {
                        "case_index": None,
                        "hidden": None,
                        "passed": False,
                        "status": "se",
                        "error_message": str(exc),
                    }
                ]
        if case_results:
            check(
                "official_solution",
                all(result["passed"] for result in case_results),
                "Official solution must pass every generated testcase",
            )

        passed = all(item["passed"] for item in checks)
        return {
            "passed": passed,
            "summary": "validated" if passed else "validation_failed",
            "checks": checks,
            "case_results": case_results,
            "case_summary": self._case_summary(case_results),
            "public_sample_count": public_count,
            "hidden_testcase_count": hidden_count,
        }

    def _run_solution(self, draft: AuthoredProblemDraft, testcases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        execution_modes = ["function"] if draft.mode in {"function", "both"} else ["acm"]
        for solution in draft.official_solutions:
            language = solution.language
            for execution_mode in execution_modes:
                try:
                    code = (
                        wrap_function_submission(
                            solution.code,
                            language,
                            draft.slug_candidate or "generated-problem",
                            draft.function_signature,
                        )
                        if execution_mode == "function"
                        else solution.code
                    )
                except ValueError as exc:
                    results.append(
                        {
                            "case_index": None,
                            "hidden": None,
                            "solution_language": language,
                            "execution_mode": execution_mode,
                            "problem_mode": draft.mode,
                            "validation_mode": "canonical_function" if draft.mode == "both" else execution_mode,
                            "passed": False,
                            "status": "se",
                            "error_message": str(exc),
                        }
                    )
                    continue
                for index, testcase in enumerate(testcases, start=1):
                    execution = self.executor.execute(
                        code=code,
                        language=language,
                        input_data=str(testcase["input"]),
                        time_limit=draft.time_limit,
                        memory_limit=draft.memory_limit,
                    )
                    actual = str(execution.get("output") or "").strip()
                    expected = str(testcase["output"]).strip()
                    status_value = execution.get("status") or "se"
                    passed = status_value == "ac" and self._outputs_match(actual, expected)
                    results.append(
                        {
                            "case_index": index,
                            "hidden": bool(testcase["is_hidden"]),
                            "solution_language": language,
                            "execution_mode": execution_mode,
                            "problem_mode": draft.mode,
                            "validation_mode": "canonical_function" if draft.mode == "both" else execution_mode,
                            "passed": passed,
                            "status": "ac" if passed else status_value if status_value != "ac" else "wa",
                            "execute_time": execution.get("execute_time", 0),
                            "memory_used": execution.get("memory_used", 0),
                            "error_message": self._safe_case_error(status_value, passed),
                        }
                    )
        return results

    def _function_name(self, draft: AuthoredProblemDraft) -> str:
        signature = draft.function_signature or ""
        match = re.search(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", signature)
        if match:
            return match.group(1)
        match = re.search(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", draft.official_solution_code)
        if match:
            return match.group(1)
        raise ValueError("Function mode requires a Python def function signature")

    def _function_parameters(self, draft: AuthoredProblemDraft) -> list[str]:
        signature = draft.function_signature or ""
        function_name = self._function_name(draft)
        match = re.search(rf"def\s+{re.escape(function_name)}\s*\((?P<params>.*?)\)", signature, re.DOTALL)
        if not match:
            match = re.search(rf"def\s+{re.escape(function_name)}\s*\((?P<params>.*?)\)", draft.official_solution_code, re.DOTALL)
        if not match:
            raise ValueError("Function mode requires a parseable Python function signature")
        names: list[str] = []
        for item in self._split_signature_parameters(match.group("params")):
            cleaned = item.strip()
            if not cleaned or cleaned.startswith("*"):
                continue
            name = cleaned.split(":", 1)[0].split("=", 1)[0].strip()
            if name and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
                names.append(name)
        return names

    def _split_signature_parameters(self, params: str) -> list[str]:
        parts: list[str] = []
        start = 0
        depth = 0
        for index, char in enumerate(params):
            if char in "([{":
                depth += 1
            elif char in ")]}" and depth:
                depth -= 1
            elif char == "," and depth == 0:
                parts.append(params[start:index])
                start = index + 1
        parts.append(params[start:])
        return parts

    def _outputs_match(self, actual_output: str, expected_output: str) -> bool:
        if actual_output == expected_output:
            return True
        actual_is_json, actual_json = self._json_value(actual_output)
        expected_is_json, expected_json = self._json_value(expected_output)
        if expected_is_json and isinstance(expected_json, str) and actual_output == expected_json:
            return True
        if actual_is_json and isinstance(actual_json, str) and expected_output == actual_json:
            return True
        if actual_is_json and expected_is_json:
            return actual_json == expected_json
        return False

    def _json_value(self, value: str) -> tuple[bool, Any]:
        try:
            return True, json.loads(value)
        except json.JSONDecodeError:
            return False, None

    def _safe_case_error(self, status_value: Any, passed: bool) -> str | None:
        if passed:
            return None
        status = str(status_value or "se").upper()
        if status == "AC":
            return "Official solution output did not match expected output during validation."
        return f"Official solution returned {status} during validation."

    def _case_summary(self, case_results: list[dict[str, Any]]) -> dict[str, Any]:
        failed = [result for result in case_results if not result.get("passed")]
        return {
            "total": len(case_results),
            "failed": len(failed),
            "failed_public": sum(1 for result in failed if result.get("hidden") is False),
            "failed_hidden": sum(1 for result in failed if result.get("hidden") is True),
            "failed_statuses": sorted({str(result.get("status") or "unknown") for result in failed}),
        }


class ProblemAuthoringAgentService:
    def __init__(
        self,
        db: Session,
        provider: BaseAIProvider | None = None,
        validator: ProblemDraftValidationAdapter | None = None,
    ):
        self.db = db
        self.provider = provider
        self.validator = validator or ProblemDraftValidationAdapter()

    def create_draft(self, payload: ProblemAuthoringRequest, current_user: User) -> tuple[ProblemDraft, AgentRun]:
        return self._create_draft_from_model(
            payload,
            current_user,
            run_type="problem_authoring",
            system_prompt=problem_authoring.SYSTEM_PROMPT,
            prompt_builder=problem_authoring.build_prompt,
            model_step_type="model_call",
            source_metadata={"kind": "generated"},
            plan_items=[
                "generate structured draft",
                "validate fields and testcase counts",
                "repair draft at most twice if validation fails",
                "run official solution",
                "persist final draft",
            ],
        )

    def create_import_draft(self, payload: ProblemImportRequest, current_user: User) -> tuple[ProblemDraft, AgentRun]:
        source_metadata = {
            "kind": "imported",
            "source_url": payload.source_url,
            "raw_material": payload.raw_material,
            "raw_material_length": len(payload.raw_material),
            "import_notes": payload.import_notes,
            "rewrite_policy": "rewrite",
        }
        return self._create_draft_from_model(
            payload,
            current_user,
            run_type="problem_import",
            system_prompt=problem_authoring.IMPORT_SYSTEM_PROMPT,
            prompt_builder=problem_authoring.build_import_prompt,
            model_step_type="extract_rewrite",
            source_metadata=source_metadata,
            plan_items=[
                "extract problem intent, examples, constraints, and solution clues",
                "rewrite statement, explanations, and official solutions",
                "adapt inputs and outputs to FastOJ mode",
                "repair draft at most twice if validation fails",
                "persist final draft",
            ],
        )

    def _create_draft_from_model(
        self,
        payload: ProblemAuthoringRequest | ProblemImportRequest,
        current_user: User,
        *,
        run_type: str,
        system_prompt: str,
        prompt_builder: Callable[[dict[str, Any]], str],
        model_step_type: str,
        source_metadata: dict[str, Any],
        plan_items: list[str],
    ) -> tuple[ProblemDraft, AgentRun]:
        run = AgentRun(
            id=uuid.uuid4(),
            run_type=run_type,
            status="running",
            input_json=dump_json(payload.model_dump()),
            output_json="{}",
            model_profile=payload.model_profile,
            locale=payload.locale,
            created_by=current_user.id,
        )
        self.db.add(run)
        self.db.flush()

        self._add_step(
            run,
            "plan",
            "problem_authoring_agent",
            {
                "topic": getattr(payload, "topic", None),
                "mode": payload.mode,
                "target_languages": payload.requested_languages(),
                "source_kind": source_metadata.get("kind"),
                "raw_material_length": source_metadata.get("raw_material_length"),
            },
            {
                "plan": plan_items,
                "max_repair_attempts": MAX_AUTHORING_REPAIR_ATTEMPTS,
            },
            "succeeded",
        )

        try:
            authored: AuthoredProblemDraft | None = None
            testcases: list[dict[str, Any]] = []
            validation_report: dict[str, Any] | None = None
            repair_context: dict[str, Any] | None = None
            last_parse_error: ValueError | None = None
            total_attempts = MAX_AUTHORING_REPAIR_ATTEMPTS + 1

            for attempt in range(1, total_attempts + 1):
                raw = self._call_model(payload, repair_context, system_prompt, prompt_builder)
                self._add_step(
                    run,
                    model_step_type,
                    "ai_provider.complete_json",
                    {
                        "model_profile": payload.model_profile,
                        "locale": payload.locale,
                        "attempt": attempt,
                        "repair_attempt": max(attempt - 1, 0),
                    },
                    {"raw_length": len(raw), "attempt": attempt},
                    "succeeded",
                )
                try:
                    authored = self._prepare_authored_draft(self._parse_model_response(raw), payload)
                except ValueError as exc:
                    last_parse_error = exc
                    self._add_step(
                        run,
                        "validation",
                        "pydantic",
                        {"attempt": attempt, "case_count": 0},
                        {"passed": False, "summary": "schema_validation_failed", "attempt": attempt},
                        "failed",
                        str(exc),
                    )
                    if attempt >= total_attempts:
                        raise exc
                    repair_context = self._schema_repair_context(payload, str(exc), attempt)
                    continue

                slug = self._unique_slug(authored.slug_candidate or authored.title)
                testcases = self._testcases(authored)
                validation_report = self.validator.validate(authored, testcases, payload.requested_languages())
                self._add_step(
                    run,
                    "validation",
                    self.validator.__class__.__name__,
                    {"slug": slug, "case_count": len(testcases), "attempt": attempt},
                    {**self._validation_step_output(validation_report), "attempt": attempt},
                    "succeeded" if validation_report["passed"] else "failed",
                    None if validation_report["passed"] else "Draft validation failed",
                )
                if validation_report["passed"] or attempt >= total_attempts:
                    break
                repair_context = self._validation_repair_context(authored, testcases, validation_report, attempt)

            if authored is None or validation_report is None:
                raise last_parse_error or ValueError("AI problem draft JSON does not match the required schema")

            draft = ProblemDraft(
                id=uuid.uuid4(),
                title=authored.title,
                slug=slug,
                description=authored.description,
                difficulty=authored.difficulty,
                tags=dump_json(authored.tags),
                mode=authored.mode,
                input_format=authored.input_format,
                output_format=authored.output_format,
                function_signature=authored.function_signature,
                time_limit=authored.time_limit,
                memory_limit=authored.memory_limit,
                hint=authored.hint,
                official_solution_language=authored.official_solution_language,
                official_solution_code=authored.official_solution_code,
                official_solution_explanation=authored.official_solution_explanation,
                official_solutions_json=dump_json(self._solutions(authored)),
                target_languages_json=dump_json(payload.requested_languages()),
                time_complexity=authored.time_complexity,
                space_complexity=authored.space_complexity,
                testcases_json=dump_json(testcases),
                validation_report_json=dump_json(validation_report),
                source_metadata_json=dump_json(source_metadata),
                status="validated" if validation_report["passed"] else "validation_failed",
                created_by=current_user.id,
            )
            self.db.add(draft)
            self.db.flush()
            run.draft_id = draft.id
            run.status = "succeeded"
            run.output_json = dump_json({"draft_id": str(draft.id), "validation": validation_report})
            run.finished_at = utc_now()
            self._add_step(
                run,
                "persistence",
                "sqlalchemy",
                {"draft_status": draft.status},
                {"draft_id": str(draft.id), "status": draft.status},
                "succeeded",
            )
            self.db.commit()
            self.db.refresh(draft)
            self.db.refresh(run)
            return draft, run
        except AIProviderUnavailableError as exc:
            self._fail_run(run, str(exc), "model_call")
            raise
        except (ValidationError, ValueError) as exc:
            self._fail_run(run, str(exc), "validation")
            raise

    def approve_draft(self, draft_id: str, current_user: User) -> ProblemDraft:
        draft = self._get_draft(draft_id)
        if draft.status == "approved":
            return draft
        if draft.status != "validated":
            raise ValueError("Only validated drafts can be approved")

        draft.slug = self._unique_slug(str(draft.slug), exclude_draft_id=str(draft.id))
        problem = Problem(
            id=uuid.uuid4(),
            title=draft.title,
            slug=draft.slug,
            description=draft.description,
            difficulty=Difficulty(draft.difficulty),
            time_limit=draft.time_limit,
            memory_limit=draft.memory_limit,
            tags=load_json(draft.tags, []),
            hint=draft.hint,
            mode=draft.mode,
            input_format=draft.input_format,
            output_format=draft.output_format,
            function_signature=draft.function_signature,
            source="agent",
            is_public=True,
            created_by=current_user.id,
        )
        self.db.add(problem)
        self.db.flush()

        testcases = load_json(draft.testcases_json, [])
        for index, testcase in enumerate(testcases, start=1):
            self.db.add(
                TestCase(
                    id=uuid.uuid4(),
                    problem_id=problem.id,
                    input=testcase["input"],
                    output=testcase["output"],
                    is_hidden=bool(testcase["is_hidden"]),
                    is_sample=bool(testcase["is_sample"]),
                    score=10,
                    order=index,
                )
            )

        for solution in self._solutions_from_record(draft):
            self.db.add(
                Solution(
                    id=uuid.uuid4(),
                    problem_id=problem.id,
                    language=solution["language"],
                    code=solution["code"],
                    explanation=solution["explanation"],
                    time_complexity=draft.time_complexity,
                    space_complexity=draft.space_complexity,
                    is_official=True,
                    created_by=current_user.id,
                )
            )
        draft.status = "approved"
        draft.approved_problem_id = problem.id
        self._add_approval_step(draft, current_user, "approved", {"problem_id": str(problem.id)})
        self.db.commit()
        self.db.refresh(draft)
        return draft

    def reject_draft(self, draft_id: str, current_user: User) -> ProblemDraft:
        draft = self._get_draft(draft_id)
        if draft.status == "approved":
            raise ValueError("Approved drafts cannot be rejected")
        if draft.status != "rejected":
            draft.status = "rejected"
            self._add_approval_step(draft, current_user, "rejected", {})
            self.db.commit()
            self.db.refresh(draft)
        return draft

    def update_draft(self, draft_id: str, payload: ProblemDraftUpdate, current_user: User) -> ProblemDraft:
        draft = self._get_draft(draft_id)
        if draft.status == "approved":
            raise ValueError("Approved drafts cannot be edited")
        if draft.status == "rejected":
            raise ValueError("Rejected drafts cannot be edited")

        values = payload.model_dump(exclude_unset=True)
        changed_fields = sorted(values.keys())
        if "title" in values and values["title"] is not None:
            draft.title = str(values["title"]).strip()
        if "slug" in values:
            requested_slug = str(values["slug"] or "").strip()
            if requested_slug:
                normalized_slug = normalize_slug(requested_slug)
                if self._slug_exists(normalized_slug, exclude_draft_id=str(draft.id)):
                    raise ValueError(f"Slug already exists: {normalized_slug}")
                draft.slug = normalized_slug
            else:
                draft.slug = self._unique_slug(str(draft.title), exclude_draft_id=str(draft.id))
        if "description" in values and values["description"] is not None:
            draft.description = str(values["description"]).strip()
        if "difficulty" in values and values["difficulty"] is not None:
            draft.difficulty = values["difficulty"]
        if "tags" in values and values["tags"] is not None:
            draft.tags = dump_json(values["tags"])
        if "mode" in values and values["mode"] is not None:
            draft.mode = values["mode"]
        if "target_languages" in values and values["target_languages"] is not None:
            draft.target_languages_json = dump_json(values["target_languages"])
        if "input_format" in values:
            draft.input_format = self._nullable_text(values["input_format"])
        if "output_format" in values:
            draft.output_format = self._nullable_text(values["output_format"])
        if "function_signature" in values:
            draft.function_signature = self._nullable_text(values["function_signature"])
        if "time_limit" in values and values["time_limit"] is not None:
            draft.time_limit = int(values["time_limit"])
        if "memory_limit" in values and values["memory_limit"] is not None:
            draft.memory_limit = int(values["memory_limit"])
        if "hint" in values:
            draft.hint = self._nullable_text(values["hint"])
        if "official_solution_language" in values and values["official_solution_language"] is not None:
            draft.official_solution_language = str(values["official_solution_language"]).strip() or "python"
        if "official_solution_code" in values and values["official_solution_code"] is not None:
            draft.official_solution_code = str(values["official_solution_code"])
        if "official_solution_explanation" in values and values["official_solution_explanation"] is not None:
            draft.official_solution_explanation = str(values["official_solution_explanation"]).strip()
        if "official_solutions" in values and values["official_solutions"] is not None:
            updated_solutions = self._normalize_updated_solutions(values["official_solutions"])
            if not updated_solutions:
                raise ValueError("At least one official solution is required")
            draft.official_solutions_json = dump_json(updated_solutions)
            primary = self._solutions_from_record(draft)[0]
            draft.official_solution_language = primary["language"]
            draft.official_solution_code = primary["code"]
            draft.official_solution_explanation = primary["explanation"]
        elif any(
            key in values
            for key in (
                "official_solution_language",
                "official_solution_code",
                "official_solution_explanation",
            )
        ):
            draft.official_solutions_json = dump_json(
                self._merge_primary_solution_into_solutions(draft)
            )
        if "time_complexity" in values:
            draft.time_complexity = self._nullable_text(values["time_complexity"])
        if "space_complexity" in values:
            draft.space_complexity = self._nullable_text(values["space_complexity"])

        testcases = load_json(draft.testcases_json, [])
        if "testcases" in values and values["testcases"] is not None:
            testcases = self._normalize_updated_testcases(values["testcases"])
            draft.testcases_json = dump_json(testcases)

        authored = self._draft_model_from_record(draft, testcases)
        required_languages = self._target_languages_from_record(draft, authored)
        validation_report = self.validator.validate(authored, testcases, required_languages)
        draft.validation_report_json = dump_json(validation_report)
        draft.status = "validated" if validation_report["passed"] else "validation_failed"

        run = AgentRun(
            id=uuid.uuid4(),
            run_type="problem_authoring",
            status="succeeded",
            input_json=dump_json(
                {
                    "draft_id": str(draft.id),
                    "changed_fields": changed_fields,
                    "testcase_count": len(testcases),
                }
            ),
            output_json=dump_json({"draft_id": str(draft.id), "validation": validation_report}),
            model_profile="manual",
            locale=normalize_locale(current_user.locale),
            created_by=current_user.id,
            draft_id=draft.id,
            finished_at=utc_now(),
        )
        self.db.add(run)
        self.db.flush()
        self._add_step(
            run,
            "manual_edit",
            "admin",
            {"draft_id": str(draft.id), "changed_fields": changed_fields, "testcase_count": len(testcases)},
            {**self._validation_step_output(validation_report), "draft_status": draft.status},
            "succeeded" if validation_report["passed"] else "failed",
            None if validation_report["passed"] else "Draft validation failed",
        )
        self.db.commit()
        self.db.refresh(draft)
        return draft

    def revalidate_draft(self, draft_id: str, current_user: User) -> ProblemDraft:
        return self.update_draft(draft_id, ProblemDraftUpdate(), current_user)

    def generate_solution_for_draft(
        self,
        draft_id: str,
        language: str,
        model_profile: str,
        locale: str,
        current_user: User,
        draft_update: ProblemDraftUpdate | None = None,
    ) -> AuthoredOfficialSolution:
        draft = self._get_draft(draft_id)
        if draft.status in {"approved", "rejected"}:
            raise ValueError("Approved or rejected drafts are read-only")
        language = language.strip().lower()
        if not Language.is_supported(language):
            raise ValueError(f"Unsupported language: {language}")

        run = AgentRun(
            id=uuid.uuid4(),
            run_type="problem_authoring_solution",
            status="running",
            input_json=dump_json({"draft_id": str(draft.id), "language": language}),
            output_json="{}",
            model_profile=model_profile,
            locale=locale,
            created_by=current_user.id,
            draft_id=draft.id,
        )
        self.db.add(run)
        self.db.flush()

        try:
            context = self._solution_generation_context(draft, language, locale, draft_update)
            provider = self.provider
            if provider is None:
                config = resolve_ai_config(model_profile)
                provider = build_provider(config)
            raw = provider.complete_json(
                problem_authoring.SOLUTION_SYSTEM_PROMPT,
                problem_authoring.build_solution_prompt(context),
            )
            self._add_step(
                run,
                "solution_generation",
                "ai_provider.complete_json",
                {"draft_id": str(draft.id), "language": language, "model_profile": model_profile},
                {"raw_length": len(raw)},
                "succeeded",
            )
            solution = self._parse_solution_response(raw, language)
            run.status = "succeeded"
            run.output_json = dump_json({"language": solution.language, "code_length": len(solution.code)})
            run.finished_at = utc_now()
            self.db.commit()
            return solution
        except AIProviderUnavailableError as exc:
            self._fail_run(run, str(exc), "solution_generation")
            raise
        except (ValidationError, ValueError) as exc:
            self._fail_run(run, str(exc), "solution_generation")
            raise

    def generate_solution_from_context(
        self,
        context: dict[str, Any],
        language: str,
        model_profile: str,
    ) -> AuthoredOfficialSolution:
        """Generate one official solution from a sanitized admin context."""
        language = language.strip().lower()
        if not Language.is_supported(language):
            raise ValueError(f"Unsupported language: {language}")
        provider = self.provider
        if provider is None:
            config = resolve_ai_config(model_profile)
            provider = build_provider(config)
        raw = provider.complete_json(
            problem_authoring.SOLUTION_SYSTEM_PROMPT,
            problem_authoring.build_solution_prompt(context),
        )
        return self._parse_solution_response(raw, language)

    def _call_model(
        self,
        payload: ProblemAuthoringRequest | ProblemImportRequest,
        repair_context: dict[str, Any] | None,
        system_prompt: str,
        prompt_builder: Callable[[dict[str, Any]], str],
    ) -> str:
        provider = self.provider
        if provider is None:
            config = resolve_ai_config(payload.model_profile)
            provider = build_provider(config)
        context = payload.model_dump()
        context["response_language"] = ai_response_language(payload.locale)
        if repair_context:
            context["repair_request"] = repair_context
        return provider.complete_json(system_prompt, prompt_builder(context))

    def _prepare_authored_draft(
        self,
        authored: AuthoredProblemDraft,
        payload: ProblemAuthoringRequest | ProblemImportRequest,
    ) -> AuthoredProblemDraft:
        requested = payload.requested_languages()
        solutions = self._ordered_solutions_for_languages(authored.official_solutions, requested)
        primary = solutions[0] if solutions else AuthoredOfficialSolution(
            language=payload.target_language,
            code=authored.official_solution_code,
            explanation=authored.official_solution_explanation,
        )
        return authored.model_copy(
            update={
                "difficulty": payload.difficulty,
                "mode": payload.mode,
                "tags": payload.tags or authored.tags,
                "official_solution_language": primary.language,
                "official_solution_code": primary.code,
                "official_solution_explanation": primary.explanation,
                "official_solutions": solutions,
            }
        )

    def _parse_model_response(self, raw: str) -> AuthoredProblemDraft:
        data = self._extract_json(raw)
        candidate = self._find_draft_payload(data)
        try:
            return AuthoredProblemDraft.model_validate(candidate)
        except ValidationError as exc:
            missing = [
                ".".join(str(part) for part in error["loc"])
                for error in exc.errors()
                if error.get("type") == "missing"
            ]
            if missing:
                preview = ", ".join(missing[:8])
                suffix = "..." if len(missing) > 8 else ""
                raise ValueError(f"AI problem draft JSON is missing required fields: {preview}{suffix}") from exc
            raise ValueError(
                "AI problem draft JSON does not match the required schema: "
                f"{self._validation_error_summary(exc)}"
            ) from exc

    def _parse_solution_response(self, raw: str, language: str) -> AuthoredOfficialSolution:
        data = self._extract_json(raw)
        candidate = self._find_solution_payload(data)
        if str(candidate.get("language") or "").strip().lower() != language:
            candidate = {**candidate, "language": language}
        try:
            return AuthoredOfficialSolution.model_validate(candidate)
        except ValidationError as exc:
            raise ValueError(
                "AI official solution JSON does not match the required schema: "
                f"{self._validation_error_summary(exc)}"
            ) from exc

    def _find_solution_payload(self, data: Any) -> dict[str, Any]:
        if isinstance(data, str):
            return self._find_solution_payload(self._extract_json(data))
        if not isinstance(data, dict):
            raise ValueError("AI provider did not return a JSON object for the official solution")
        if {"language", "code", "explanation"} & set(data):
            return data
        for key in ("solution", "official_solution", "data", "result", "output", "content", "json"):
            nested = data.get(key)
            if isinstance(nested, dict | str):
                try:
                    return self._find_solution_payload(nested)
                except ValueError:
                    continue
        keys = ", ".join(sorted(str(key) for key in data.keys())[:8]) or "none"
        raise ValueError(f"AI provider returned JSON without an official solution object. Top-level keys: {keys}")

    def _validation_error_summary(self, exc: ValidationError) -> str:
        summaries = []
        for error in exc.errors():
            loc = ".".join(str(part) for part in error.get("loc", ())) or "root"
            error_type = str(error.get("type") or "invalid")
            summaries.append(f"{loc} ({error_type})")
        if not summaries:
            return "unknown validation error"
        preview = ", ".join(summaries[:8])
        return f"{preview}{'...' if len(summaries) > 8 else ''}"

    def _extract_json(self, raw: str) -> Any:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            decoder = json.JSONDecoder()
            for match in re.finditer(r"[\{\[]", raw):
                try:
                    data, _index = decoder.raw_decode(raw[match.start() :])
                    return data
                except json.JSONDecodeError:
                    continue
        return {}

    def _find_draft_payload(self, data: Any) -> dict[str, Any]:
        if isinstance(data, str):
            return self._find_draft_payload(self._extract_json(data))
        if not isinstance(data, dict):
            raise ValueError("AI provider did not return a JSON object for the problem draft")

        required_signal = {"title", "description", "official_solution_code", "official_solutions"}
        if required_signal & set(data):
            return data

        for key in ("problem", "problem_draft", "draft", "data", "result", "output", "content", "json"):
            nested = data.get(key)
            if isinstance(nested, dict | str):
                try:
                    return self._find_draft_payload(nested)
                except ValueError:
                    continue

        keys = ", ".join(sorted(str(key) for key in data.keys())[:8]) or "none"
        raise ValueError(f"AI provider returned JSON without a problem draft object. Top-level keys: {keys}")

    def _solutions(self, authored: AuthoredProblemDraft) -> list[dict[str, str]]:
        return [
            {
                "language": solution.language,
                "code": solution.code,
                "explanation": solution.explanation,
            }
            for solution in authored.official_solutions
        ]

    def _ordered_solutions_for_languages(
        self,
        solutions: list[AuthoredOfficialSolution],
        requested_languages: list[str],
    ) -> list[AuthoredOfficialSolution]:
        by_language = {solution.language: solution for solution in solutions}
        ordered: list[AuthoredOfficialSolution] = []
        for language in requested_languages:
            solution = by_language.get(language)
            if solution:
                ordered.append(solution)
        for solution in solutions:
            if solution.language not in {item.language for item in ordered}:
                ordered.append(solution)
        return ordered

    def _testcases(self, authored: AuthoredProblemDraft) -> list[dict[str, Any]]:
        testcases: list[dict[str, Any]] = []
        for index, testcase in enumerate(authored.public_sample_testcases, start=1):
            testcases.append(
                {
                    "input": testcase.input,
                    "output": testcase.output,
                    "is_hidden": False,
                    "is_sample": True,
                    "explanation": testcase.explanation,
                    "order": index,
                }
            )
        offset = len(testcases)
        for index, testcase in enumerate(authored.hidden_testcases, start=1):
            testcases.append(
                {
                    "input": testcase.input,
                    "output": testcase.output,
                    "is_hidden": True,
                    "is_sample": False,
                    "explanation": testcase.explanation,
                    "order": offset + index,
                }
            )
        return testcases

    def _solution_generation_context(
        self,
        draft: ProblemDraft,
        language: str,
        locale: str,
        draft_update: ProblemDraftUpdate | None,
    ) -> dict[str, Any]:
        values = draft_update.model_dump(exclude_unset=True) if draft_update else {}
        testcases = load_json(draft.testcases_json, [])
        if "testcases" in values and values["testcases"] is not None:
            testcases = self._normalize_updated_testcases(values["testcases"])

        solutions = self._solutions_from_record(draft)
        if "official_solutions" in values and values["official_solutions"] is not None:
            updated_solutions = self._normalize_updated_solutions(values["official_solutions"])
            if updated_solutions:
                solutions = updated_solutions

        hidden_values = [
            str(value)
            for testcase in testcases
            if testcase.get("is_hidden")
            for value in (testcase.get("input"), testcase.get("output"))
            if value is not None and len(str(value).strip()) >= 8
        ]

        def redact(value: Any) -> str | None:
            if value is None:
                return None
            text = str(value)
            for secret in hidden_values:
                text = text.replace(secret, "[hidden]")
            return self._truncate_for_prompt(text)

        public_samples = [
            {
                "case_index": index,
                "input": testcase.get("input"),
                "expected_output": testcase.get("output"),
                "explanation": testcase.get("explanation"),
            }
            for index, testcase in enumerate(testcases, start=1)
            if not testcase.get("is_hidden")
        ]

        return {
            "target_language": language,
            "response_language": ai_response_language(locale),
            "title": redact(values.get("title", draft.title)),
            "slug": redact(values.get("slug", draft.slug)),
            "description": redact(values.get("description", draft.description)),
            "difficulty": values.get("difficulty", draft.difficulty),
            "tags": values.get("tags", load_json(draft.tags, [])),
            "mode": values.get("mode", draft.mode),
            "input_format": redact(values.get("input_format", draft.input_format)),
            "output_format": redact(values.get("output_format", draft.output_format)),
            "function_signature": redact(values.get("function_signature", draft.function_signature)),
            "time_limit": values.get("time_limit", draft.time_limit),
            "memory_limit": values.get("memory_limit", draft.memory_limit),
            "hint": redact(values.get("hint", draft.hint)),
            "time_complexity": redact(values.get("time_complexity", draft.time_complexity)),
            "space_complexity": redact(values.get("space_complexity", draft.space_complexity)),
            "public_sample_testcases": public_samples,
            "hidden_testcase_count": sum(1 for testcase in testcases if testcase.get("is_hidden")),
            "existing_official_solutions": [
                {
                    "language": solution["language"],
                    "code": redact(solution.get("code")) or "",
                    "explanation": redact(solution.get("explanation")) or "",
                }
                for solution in solutions
                if solution.get("language") != language
            ],
        }

    def _truncate_for_prompt(self, value: str, limit: int = 6000) -> str:
        if len(value) <= limit:
            return value
        return f"{value[:limit]}...[truncated]"

    def _draft_model_from_record(self, draft: ProblemDraft, testcases: list[dict[str, Any]]) -> AuthoredProblemDraft:
        public_cases: list[AuthoredTestCase] = []
        hidden_cases: list[AuthoredTestCase] = []
        for testcase in testcases:
            case = AuthoredTestCase(
                input=str(testcase.get("input") or ""),
                output=str(testcase.get("output") or ""),
                explanation=self._nullable_text(testcase.get("explanation")),
            )
            if testcase.get("is_hidden"):
                hidden_cases.append(case)
            else:
                public_cases.append(case)
        solutions = self._solutions_from_record(draft)
        if not solutions:
            raise ValueError("At least one official solution is required")
        primary = solutions[0]
        return AuthoredProblemDraft(
            title=str(draft.title),
            slug_candidate=str(draft.slug),
            description=str(draft.description),
            input_format=draft.input_format,
            output_format=draft.output_format,
            function_signature=draft.function_signature,
            difficulty=str(draft.difficulty),
            tags=load_json(draft.tags, []),
            mode=str(draft.mode),
            time_limit=int(draft.time_limit or 1000),
            memory_limit=int(draft.memory_limit or 256),
            hint=draft.hint,
            official_solution_language=primary["language"],
            official_solution_code=primary["code"],
            official_solution_explanation=primary["explanation"],
            official_solutions=[
                AuthoredOfficialSolution(
                    language=solution["language"],
                    code=solution["code"],
                    explanation=solution["explanation"],
                )
                for solution in solutions
            ],
            time_complexity=str(draft.time_complexity or ""),
            space_complexity=str(draft.space_complexity or ""),
            public_sample_testcases=public_cases,
            hidden_testcases=hidden_cases,
        )

    def _solutions_from_record(self, draft: ProblemDraft) -> list[dict[str, str]]:
        raw_solutions = load_json(getattr(draft, "official_solutions_json", None), [])
        normalized = self._normalize_updated_solutions(raw_solutions)
        if normalized:
            return normalized
        code = normalize_source_code(str(draft.official_solution_code or ""))
        explanation = str(draft.official_solution_explanation or "")
        if code.strip() and explanation.strip():
            return [
                {
                    "language": str(draft.official_solution_language or "python"),
                    "code": code,
                    "explanation": explanation,
                }
            ]
        return []

    def _target_languages_from_record(
        self,
        draft: ProblemDraft,
        authored: AuthoredProblemDraft | None = None,
    ) -> list[str]:
        raw_languages = load_json(getattr(draft, "target_languages_json", None), [])
        languages: list[str] = []
        if isinstance(raw_languages, list):
            for item in raw_languages:
                language = str(item or "").strip().lower()
                if language and Language.is_supported(language) and language not in languages:
                    languages.append(language)
        if languages:
            return languages
        source = authored.official_solutions if authored else []
        for solution in source:
            language = solution.language
            if language not in languages:
                languages.append(language)
        if not languages:
            for solution in self._solutions_from_record(draft):
                language = solution["language"]
                if language not in languages:
                    languages.append(language)
        return languages

    def _normalize_updated_solutions(self, raw_solutions: list[Any]) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in raw_solutions:
            if isinstance(item, AuthoredOfficialSolution):
                language = item.language
                code = normalize_source_code(item.code)
                explanation = item.explanation
            elif isinstance(item, dict):
                language = str(item.get("language") or "").strip().lower()
                code = normalize_source_code(str(item.get("code") or ""))
                explanation = str(item.get("explanation") or "").strip()
            else:
                continue
            if not language or language in seen or not Language.is_supported(language):
                continue
            if not code.strip() or not explanation:
                continue
            normalized.append({"language": language, "code": code, "explanation": explanation})
            seen.add(language)
        return normalized

    def _merge_primary_solution_into_solutions(self, draft: ProblemDraft) -> list[dict[str, str]]:
        primary = {
            "language": str(draft.official_solution_language or "python").strip().lower() or "python",
            "code": str(draft.official_solution_code or ""),
            "explanation": str(draft.official_solution_explanation or "").strip(),
        }
        solutions = [primary]
        for solution in self._solutions_from_record(draft):
            if solution["language"] != primary["language"]:
                solutions.append(solution)
        return self._normalize_updated_solutions(solutions)

    def _normalize_updated_testcases(self, raw_testcases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for index, testcase in enumerate(raw_testcases, start=1):
            order = testcase.get("order") if isinstance(testcase, dict) else None
            is_hidden = bool(testcase.get("is_hidden"))
            is_sample = False if is_hidden else bool(testcase.get("is_sample"))
            normalized.append(
                {
                    "input": str(testcase.get("input") or ""),
                    "output": str(testcase.get("output") or ""),
                    "is_hidden": is_hidden,
                    "is_sample": is_sample,
                    "explanation": self._nullable_text(testcase.get("explanation")),
                    "order": int(order) if order else index,
                }
            )
        return sorted(normalized, key=lambda item: int(item.get("order") or 0))

    def _nullable_text(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _schema_repair_context(
        self,
        payload: ProblemAuthoringRequest | ProblemImportRequest,
        message: str,
        attempt: int,
    ) -> dict[str, Any]:
        return {
            "kind": "schema_repair",
            "attempt": attempt + 1,
            "max_attempts": MAX_AUTHORING_REPAIR_ATTEMPTS + 1,
            "instruction": "Return a complete replacement JSON object matching the required schema.",
            "safe_error": message,
            "requested_mode": payload.mode,
            "requested_difficulty": payload.difficulty,
            "requested_tags": payload.tags,
            "requested_languages": payload.requested_languages(),
        }

    def _validation_repair_context(
        self,
        authored: AuthoredProblemDraft,
        testcases: list[dict[str, Any]],
        report: dict[str, Any],
        attempt: int,
    ) -> dict[str, Any]:
        hidden_values = [
            str(value)
            for testcase in testcases
            if testcase.get("is_hidden")
            for value in (testcase.get("input"), testcase.get("output"))
            if value is not None and len(str(value).strip()) >= 8
        ]

        def redact(value: str | None) -> str | None:
            if value is None:
                return None
            text = str(value)
            for secret in hidden_values:
                text = text.replace(secret, "[hidden]")
            return text

        sanitized_solutions = [
            {
                **solution,
                "code": redact(str(solution.get("code") or "")) or "",
                "explanation": redact(str(solution.get("explanation") or "")) or "",
            }
            for solution in self._solutions(authored)
        ]
        failed_checks = [
            {"name": check.get("name"), "message": check.get("message")}
            for check in report.get("checks", [])
            if not check.get("passed")
        ]
        case_results = [record for record in report.get("case_results", []) if isinstance(record, dict)]
        public_results = [
            {
                "case_index": result.get("case_index"),
                "passed": result.get("passed"),
                "status": result.get("status"),
                "error_message": result.get("error_message"),
            }
            for result in case_results
            if result.get("hidden") is False
        ]
        public_samples = [
            {
                "case_index": index,
                "input": testcase.get("input"),
                "expected_output": testcase.get("output"),
                "explanation": testcase.get("explanation"),
            }
            for index, testcase in enumerate(testcases, start=1)
            if not testcase.get("is_hidden")
        ]
        return {
            "kind": "validation_repair",
            "attempt": attempt + 1,
            "max_attempts": MAX_AUTHORING_REPAIR_ATTEMPTS + 1,
            "instruction": (
                "Return a complete replacement JSON object. Hidden testcase content from the previous draft is omitted; "
                "regenerate any needed public or hidden testcases so the official solution passes all generated tests."
            ),
            "failed_checks": failed_checks,
            "case_summary": report.get("case_summary", {}),
            "public_case_results": public_results,
            "previous_draft_without_hidden_testcases": {
                "title": redact(authored.title),
                "slug_candidate": redact(authored.slug_candidate),
                "description": redact(authored.description),
                "input_format": redact(authored.input_format),
                "output_format": redact(authored.output_format),
                "function_signature": redact(authored.function_signature),
                "difficulty": authored.difficulty,
                "tags": authored.tags,
                "mode": authored.mode,
                "time_limit": authored.time_limit,
                "memory_limit": authored.memory_limit,
                "hint": redact(authored.hint),
                "official_solution_language": authored.official_solution_language,
                "official_solution_code": redact(authored.official_solution_code),
                "official_solution_explanation": redact(authored.official_solution_explanation),
                "official_solutions": sanitized_solutions,
                "time_complexity": redact(authored.time_complexity),
                "space_complexity": redact(authored.space_complexity),
                "public_sample_testcases": public_samples,
                "hidden_testcase_count": sum(1 for testcase in testcases if testcase.get("is_hidden")),
                "validation_notes": redact(authored.validation_notes),
            },
        }

    def _unique_slug(self, value: str, exclude_draft_id: str | None = None) -> str:
        base = normalize_slug(value)
        candidate = base
        suffix = 2
        while self._slug_exists(candidate, exclude_draft_id):
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate

    def _slug_exists(self, slug: str, exclude_draft_id: str | None) -> bool:
        if self.db.query(Problem).filter(Problem.slug == slug).first():
            return True
        query = self.db.query(ProblemDraft).filter(ProblemDraft.slug == slug)
        return any(
            str(draft.id) != str(exclude_draft_id)
            and str(getattr(draft, "status", "")) in SLUG_RESERVED_DRAFT_STATUSES
            for draft in query.all()
        )

    def _get_draft(self, draft_id: str) -> ProblemDraft:
        draft = self.db.query(ProblemDraft).filter(ProblemDraft.id == draft_id).first()
        if not draft:
            raise LookupError("Problem draft not found")
        return draft

    def _add_step(
        self,
        run: AgentRun,
        step_type: str,
        tool_name: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        status: str,
        error_message: str | None = None,
    ) -> AgentStep:
        latest_step = (
            self.db.query(AgentStep)
            .filter(AgentStep.run_id == run.id)
            .order_by(AgentStep.step_index.desc())
            .first()
        )
        current_max = latest_step.step_index if latest_step else 0
        step = AgentStep(
            id=uuid.uuid4(),
            run_id=run.id,
            step_index=current_max + 1,
            step_type=step_type,
            tool_name=tool_name,
            input_json=dump_json(input_data),
            output_json=dump_json(output_data),
            status=status,
            error_message=error_message,
        )
        self.db.add(step)
        self.db.flush()
        return step

    def _fail_run(self, run: AgentRun, message: str, step_type: str) -> None:
        self._add_step(run, step_type, "problem_authoring_agent", {}, {}, "failed", message)
        run.status = "failed"
        run.error_message = message
        run.finished_at = utc_now()
        self.db.commit()

    def _add_approval_step(
        self,
        draft: ProblemDraft,
        current_user: User,
        status: str,
        output_data: dict[str, Any],
    ) -> None:
        run = self.db.query(AgentRun).filter(AgentRun.draft_id == draft.id).order_by(AgentRun.created_at.desc()).first()
        if not run:
            run = AgentRun(
                id=uuid.uuid4(),
                run_type="problem_authoring",
                status="succeeded",
                input_json="{}",
                output_json="{}",
                model_profile="manual",
                locale=normalize_locale(current_user.locale),
                created_by=current_user.id,
                draft_id=draft.id,
                finished_at=utc_now(),
            )
            self.db.add(run)
            self.db.flush()
        self._add_step(
            run,
            "approval",
            "admin",
            {"draft_id": str(draft.id), "admin_id": str(current_user.id)},
            output_data,
            status,
        )

    def _validation_step_output(self, report: dict[str, Any]) -> dict[str, Any]:
        return {
            "passed": report["passed"],
            "summary": report["summary"],
            "public_sample_count": report["public_sample_count"],
            "hidden_testcase_count": report["hidden_testcase_count"],
            "case_summary": report.get("case_summary", {}),
            "failed_checks": [check["name"] for check in report["checks"] if not check["passed"]],
        }
