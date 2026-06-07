import hashlib
import json
import re
import uuid
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.ai.profiles import resolve_ai_config
from backend.ai.prompts import problem_authoring
from backend.ai.providers import (
    AICompletion,
    AIProviderEmptyResponseError,
    AIProviderUnavailableError,
    BaseAIProvider,
    build_provider,
)
from backend.core.code_normalization import normalize_source_code
from backend.core.config import settings
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

DEFAULT_AUTHORING_REPAIR_ATTEMPTS = 6
MAX_AUTHORING_REPAIR_ATTEMPTS_LIMIT = 8
SLUG_RESERVED_DRAFT_STATUSES = {"draft", "validating", "validated"}


class AgentRunFailedError(ValueError):
    def __init__(self, message: str, run_id: str):
        super().__init__(message)
        self.run_id = run_id


class AgentRunProviderUnavailableError(AIProviderUnavailableError):
    def __init__(self, message: str, run_id: str):
        super().__init__(message)
        self.run_id = run_id


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def load_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def authoring_repair_attempts() -> int:
    configured = getattr(settings, "AI_AUTHORING_REPAIR_ATTEMPTS", DEFAULT_AUTHORING_REPAIR_ATTEMPTS)
    try:
        value = int(configured)
    except (TypeError, ValueError):
        value = DEFAULT_AUTHORING_REPAIR_ATTEMPTS
    return max(0, min(value, MAX_AUTHORING_REPAIR_ATTEMPTS_LIMIT))


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
                    input_value, _output_value = self._testcase_io_for_mode(testcase, "function")
                    normalize_function_call_args(input_value, parameter_names)
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
        execution_modes = self._execution_modes_for_draft(draft)
        for solution in draft.official_solutions:
            language = solution.language
            for execution_mode in execution_modes:
                source_code = self._solution_code_for_mode(solution, execution_mode)
                try:
                    code = (
                        wrap_function_submission(
                            source_code,
                            language,
                            draft.slug_candidate or "generated-problem",
                            draft.function_signature,
                        )
                        if execution_mode == "function"
                        else source_code
                    )
                except ValueError as exc:
                    results.append(
                        {
                            "case_index": None,
                            "hidden": None,
                            "solution_language": language,
                            "execution_mode": execution_mode,
                            "problem_mode": draft.mode,
                            "validation_mode": self._validation_mode_label(draft, execution_mode),
                            "passed": False,
                            "status": "se",
                            "error_message": str(exc),
                        }
                    )
                    continue
                for index, testcase in enumerate(testcases, start=1):
                    input_data, expected_output = self._testcase_io_for_mode(testcase, execution_mode)
                    execution = self.executor.execute(
                        code=code,
                        language=language,
                        input_data=input_data,
                        time_limit=draft.time_limit,
                        memory_limit=draft.memory_limit,
                    )
                    actual = str(execution.get("output") or "").strip()
                    expected = expected_output.strip()
                    status_value = execution.get("status") or "se"
                    passed = status_value == "ac" and self._outputs_match(actual, expected)
                    results.append(
                        {
                            "case_index": index,
                            "hidden": bool(testcase["is_hidden"]),
                            "solution_language": language,
                            "execution_mode": execution_mode,
                            "problem_mode": draft.mode,
                            "validation_mode": self._validation_mode_label(draft, execution_mode),
                            "passed": passed,
                            "status": "ac" if passed else status_value if status_value != "ac" else "wa",
                            "execute_time": execution.get("execute_time", 0),
                            "memory_used": execution.get("memory_used", 0),
                            "error_message": self._safe_case_error(status_value, passed),
                        }
                    )
        return results

    def _execution_modes_for_draft(self, draft: AuthoredProblemDraft) -> list[str]:
        if draft.mode == "function":
            return ["function"]
        if draft.mode == "acm":
            return ["acm"]
        has_dual_solution_code = any(
            solution.acm_code and solution.function_code
            for solution in draft.official_solutions
        )
        return ["acm", "function"] if has_dual_solution_code else ["function"]

    def _solution_code_for_mode(self, solution: AuthoredOfficialSolution, execution_mode: str) -> str:
        if execution_mode == "acm" and solution.acm_code:
            return solution.acm_code
        if execution_mode == "function" and solution.function_code:
            return solution.function_code
        return solution.code

    def _validation_mode_label(self, draft: AuthoredProblemDraft, execution_mode: str) -> str:
        if draft.mode == "both" and execution_mode == "function" and self._execution_modes_for_draft(draft) == ["function"]:
            return "canonical_function"
        return execution_mode

    def _testcase_io_for_mode(self, testcase: dict[str, Any], execution_mode: str) -> tuple[str, str]:
        metadata = testcase.get("io_metadata")
        if isinstance(metadata, dict):
            view = metadata.get(execution_mode)
            if isinstance(view, dict):
                input_value = view.get("input")
                output_value = view.get("output")
                if input_value is not None and output_value is not None:
                    return str(input_value), str(output_value)
        return str(testcase["input"]), str(testcase["output"])

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

    def create_draft(
        self,
        payload: ProblemAuthoringRequest,
        current_user: User,
        *,
        agent_session_id: str | None = None,
        existing_run: AgentRun | None = None,
    ) -> tuple[ProblemDraft, AgentRun]:
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
            agent_session_id=agent_session_id,
            existing_run=existing_run,
        )

    def create_import_draft(
        self,
        payload: ProblemImportRequest,
        current_user: User,
        *,
        agent_session_id: str | None = None,
        existing_run: AgentRun | None = None,
    ) -> tuple[ProblemDraft, AgentRun]:
        source_metadata = {
            "kind": "imported",
            "source_url": payload.source_url,
            "raw_material": payload.raw_material,
            "raw_material_length": len(payload.raw_material),
            "import_notes": payload.import_notes,
            "rewrite_policy": "rewrite",
        }
        structured_draft = self._structured_import_candidate(payload)
        if structured_draft is not None:
            return self._create_draft_from_structured_import(
                payload,
                current_user,
                source_metadata,
                structured_draft,
                agent_session_id=agent_session_id,
                existing_run=existing_run,
            )
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
            agent_session_id=agent_session_id,
            existing_run=existing_run,
        )

    def enqueue_draft_run(
        self,
        payload: ProblemAuthoringRequest | ProblemImportRequest,
        current_user: User,
        run_type: str,
        *,
        agent_session_id: str | None = None,
        parent_run_id: str | None = None,
        retry_guidance: str | None = None,
    ) -> AgentRun:
        run_id = uuid.uuid4()
        session_id = agent_session_id or str(run_id)
        run_input = payload.model_dump()
        run_input["agent_session_id"] = session_id
        if parent_run_id:
            run_input["parent_run_id"] = parent_run_id
        if retry_guidance:
            run_input["retry_guidance"] = retry_guidance[:500]
        run = AgentRun(
            id=run_id,
            run_type=run_type,
            status="running",
            input_json=dump_json(run_input),
            output_json=dump_json({"agent_session_id": session_id}),
            model_profile=payload.model_profile,
            locale=payload.locale,
            created_by=current_user.id,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def _create_draft_from_structured_import(
        self,
        payload: ProblemImportRequest,
        current_user: User,
        source_metadata: dict[str, Any],
        authored: AuthoredProblemDraft,
        *,
        agent_session_id: str | None = None,
        existing_run: AgentRun | None = None,
    ) -> tuple[ProblemDraft, AgentRun]:
        run = existing_run
        if run is None:
            run_id = uuid.uuid4()
            session_id = agent_session_id or str(run_id)
            run_input = payload.model_dump()
            run_input["agent_session_id"] = session_id
            run = AgentRun(
                id=run_id,
                run_type="problem_import",
                status="running",
                input_json=dump_json(run_input),
                output_json="{}",
                model_profile=payload.model_profile,
                locale=payload.locale,
                created_by=current_user.id,
            )
            self.db.add(run)
        else:
            run_input = {**payload.model_dump(), **load_json(run.input_json, {})}
            session_id = str(run_input.get("agent_session_id") or agent_session_id or run.id)
            run_input["agent_session_id"] = session_id
            run.input_json = dump_json(run_input)
            run.output_json = dump_json({**load_json(run.output_json, {}), "agent_session_id": session_id})
            run.status = "running"
            run.error_message = None
            run.finished_at = None
        self.db.flush()
        self._add_step(
            run,
            "plan",
            "problem_authoring_agent",
            {
                "topic": payload.topic,
                "mode": payload.mode,
                "target_languages": payload.requested_languages(),
                "source_kind": source_metadata.get("kind"),
                "raw_material_length": source_metadata.get("raw_material_length"),
            },
            {
                "plan": [
                    "parse structured imported statement",
                    "extract public samples and provided official solution",
                    "generate deterministic hidden tests when the problem pattern is recognized",
                    "validate official solution",
                    "persist final draft",
                ],
                "strategy": "structured_import",
            },
            "succeeded",
        )
        self._commit_trace(run)

        try:
            authored = self._prepare_authored_draft(authored, payload)
            authored, effective_languages, language_warnings = self._effective_structured_import_languages(
                authored,
                payload.requested_languages(),
            )
            slug = self._unique_slug(authored.slug_candidate or authored.title)
            testcases = self._testcases(authored)
            self._add_step(
                run,
                "extract_rewrite",
                "structured_import_parser",
                {
                    "raw_material_length": len(payload.raw_material),
                    "requested_mode": payload.mode,
                    "requested_languages": payload.requested_languages(),
                },
                {
                    "title": authored.title,
                    "slug_candidate": authored.slug_candidate,
                    "public_sample_count": len(authored.public_sample_testcases),
                    "hidden_testcase_count": len(authored.hidden_testcases),
                    "official_solution_languages": [solution.language for solution in authored.official_solutions],
                    "effective_languages": effective_languages,
                    "language_warnings": language_warnings,
                },
                "succeeded",
            )
            self._commit_trace(run)

            validation_report = self.validator.validate(authored, testcases, effective_languages)
            self._add_step(
                run,
                "validation",
                self.validator.__class__.__name__,
                {
                    "slug": slug,
                    "case_count": len(testcases),
                    "attempt": 1,
                    "strategy": "structured_import",
                    "requested_languages": payload.requested_languages(),
                    "effective_languages": effective_languages,
                },
                {
                    **self._validation_step_output(validation_report),
                    "attempt": 1,
                    "language_warnings": language_warnings,
                },
                "succeeded" if validation_report["passed"] else "failed",
                None if validation_report["passed"] else "Draft validation failed",
            )
            self._commit_trace(run)

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
                target_languages_json=dump_json(effective_languages),
                time_complexity=authored.time_complexity,
                space_complexity=authored.space_complexity,
                testcases_json=dump_json(testcases),
                validation_report_json=dump_json(validation_report),
                source_metadata_json=dump_json(
                    {
                        **source_metadata,
                        "structured_import": True,
                        "agent_session_id": session_id,
                        "requested_languages": payload.requested_languages(),
                        "effective_languages": effective_languages,
                        "language_warnings": language_warnings,
                    }
                ),
                status="validated" if validation_report["passed"] else "validation_failed",
                created_by=current_user.id,
            )
            self.db.add(draft)
            self.db.flush()
            run.draft_id = draft.id
            run.status = "succeeded"
            run.output_json = dump_json(
                {
                    "draft_id": str(draft.id),
                    "validation": validation_report,
                    "agent_session_id": session_id,
                    "language_warnings": language_warnings,
                }
            )
            run.finished_at = utc_now()
            self._add_step(
                run,
                "persistence",
                "sqlalchemy",
                {"draft_status": draft.status, "strategy": "structured_import"},
                {"draft_id": str(draft.id), "status": draft.status},
                "succeeded",
            )
            self.db.commit()
            self.db.refresh(draft)
            self.db.refresh(run)
            return draft, run
        except (ValidationError, ValueError) as exc:
            self._fail_run(run, str(exc), "validation")
            raise AgentRunFailedError(str(exc), str(run.id)) from exc

    def _structured_import_candidate(self, payload: ProblemImportRequest) -> AuthoredProblemDraft | None:
        raw = payload.raw_material
        if "在线最小二乘回归" in raw and "ADD x y" in raw and "QUERY x0" in raw:
            return self._online_least_squares_import_candidate(payload)
        if payload.mode != "acm":
            return None
        samples = self._extract_chinese_samples(raw)
        code = self._extract_python_code(raw)
        if not samples or not code:
            return None
        title = payload.topic or self._first_nonempty_line(raw) or "Imported ACM Problem"
        description = self._import_statement_body(raw)
        return AuthoredProblemDraft(
            title=title,
            slug_candidate=normalize_slug(title),
            description=description,
            input_format=self._extract_chinese_section(raw, "输入描述", ["输出描述", "样例"]) or "Read input from stdin as described in the statement.",
            output_format=self._extract_chinese_section(raw, "输出描述", ["样例", "题解"]) or "Print the required answer.",
            function_signature=None,
            difficulty=payload.difficulty,
            tags=payload.tags or ["Implementation"],
            mode=payload.mode,
            time_limit=2000,
            memory_limit=256,
            hint="维护题目所需的增量状态，按操作顺序回答查询。",
            official_solution_language="python",
            official_solution_code=code,
            official_solution_explanation=self._extract_solution_explanation(raw) or "The official solution follows the algorithm described in the imported explanation.",
            official_solutions=[
                AuthoredOfficialSolution(
                    language="python",
                    code=code,
                    explanation=self._extract_solution_explanation(raw) or "The official solution follows the algorithm described in the imported explanation.",
                )
            ],
            time_complexity="O(Q)",
            space_complexity="O(1)",
            public_sample_testcases=[
                AuthoredTestCase(input=sample["input"], output=sample["output"], explanation=sample.get("explanation"))
                for sample in samples
            ],
            hidden_testcases=[],
            validation_notes="Structured import parsed public samples and the provided Python official solution without a model call.",
        )

    def _online_least_squares_import_candidate(self, payload: ProblemImportRequest) -> AuthoredProblemDraft | None:
        raw = payload.raw_material
        samples = self._extract_chinese_samples(raw)
        if not samples:
            return None
        use_function_mode = payload.mode in {"function", "both"}
        acm_code = self._extract_python_code(raw)
        if not acm_code and payload.mode == "acm":
            return None
        title = "智能物流定价引擎（在线学习）"
        description = self._online_least_squares_description(raw, payload.mode)
        if payload.mode == "function":
            input_format = "函数接收一个字符串操作列表 operations。每个操作是 `ADD x y` 或 `QUERY x0`。"
            output_format = "函数返回每次 `QUERY` 的预测值字符串列表，每个字符串固定保留 6 位小数。"
        elif payload.mode == "both":
            input_format = "ACM 模式第一行是操作数 Q，之后每行是 `ADD x y` 或 `QUERY x0`。函数模式接收 `operations: list[str]`。"
            output_format = "ACM 模式对每个 `QUERY` 输出一行固定 6 位小数；函数模式返回这些结果组成的字符串列表。"
        else:
            input_format = self._extract_chinese_section(raw, "输入描述", ["输出描述", "样例"]) or "第一行是操作数 Q，之后每行是 ADD x y 或 QUERY x0。"
            output_format = self._extract_chinese_section(raw, "输出描述", ["样例", "题解"]) or "对每个 QUERY 输出一行固定 6 位小数的预测值。"
        public_cases = [
            self._format_online_least_squares_case(sample["input"], sample.get("explanation"), use_function_mode)
            for sample in samples
        ]
        hidden_cases = [
            self._format_online_least_squares_case(case_input, explanation, use_function_mode)
            for case_input, explanation in self._online_least_squares_hidden_inputs()
        ]
        solution_code = self._online_least_squares_function_solution() if payload.mode in {"function", "both"} else acm_code
        solution_explanation = self._online_least_squares_solution_explanation()
        official_solutions = self._online_least_squares_official_solutions(
            payload.requested_languages(),
            payload.mode,
            solution_explanation,
            acm_code,
        )
        primary_solution = official_solutions[0]
        return AuthoredProblemDraft(
            title=title,
            slug_candidate="smart-logistics-pricing-engine-online-least-squares-regression",
            description=description,
            input_format=input_format,
            output_format=output_format,
            function_signature=(
                "def online_least_squares(operations: list[str]) -> list[str]:"
                if payload.mode in {"function", "both"}
                else None
            ),
            difficulty=payload.difficulty,
            tags=self._online_least_squares_tags(payload.tags),
            mode=payload.mode,
            time_limit=2000,
            memory_limit=256,
            hint="不要保存所有样本；只维护回归公式需要的五个累加量，并单独处理所有 x 相同的退化情况。",
            official_solution_language=primary_solution.language,
            official_solution_code=primary_solution.code,
            official_solution_explanation=primary_solution.explanation,
            official_solutions=official_solutions,
            time_complexity="O(Q)",
            space_complexity="O(1)",
            public_sample_testcases=public_cases,
            hidden_testcases=hidden_cases,
            validation_notes="Structured import recognized the online least-squares regression pattern and generated deterministic tests.",
        )

    def _format_online_least_squares_case(
        self,
        acm_input: str,
        explanation: str | None,
        use_function_mode: bool,
    ) -> AuthoredTestCase:
        operations = self._online_least_squares_operations(acm_input)
        outputs = self._online_least_squares_outputs(operations)
        acm_input_value = self._online_least_squares_acm_input(operations)
        acm_output_value = "\n".join(outputs)
        function_input_value = json.dumps(
            self._online_least_squares_operation_lines(operations),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        function_output_value = json.dumps(outputs, ensure_ascii=False, separators=(",", ":"))
        io_metadata = {
            "acm": {"input": acm_input_value, "output": acm_output_value},
            "function": {"input": function_input_value, "output": function_output_value},
        }
        if use_function_mode:
            return AuthoredTestCase(
                input=function_input_value,
                output=function_output_value,
                explanation=explanation,
                io_metadata=io_metadata,
            )
        return AuthoredTestCase(
            input=acm_input_value,
            output=acm_output_value,
            explanation=explanation,
            io_metadata=io_metadata,
        )

    def _online_least_squares_operations(self, acm_input: str) -> list[list[Any]]:
        lines = [line.strip() for line in acm_input.strip().splitlines() if line.strip()]
        if not lines:
            return []
        operations: list[list[Any]] = []
        for line in lines[1:]:
            parts = line.split()
            if not parts:
                continue
            if parts[0] == "ADD" and len(parts) >= 3:
                operations.append(["ADD", int(parts[1]), int(parts[2])])
            elif parts[0] == "QUERY" and len(parts) >= 2:
                operations.append(["QUERY", int(parts[1])])
        return operations

    def _online_least_squares_acm_input(self, operations: list[list[Any]]) -> str:
        lines = [str(len(operations))]
        lines.extend(self._online_least_squares_operation_lines(operations))
        return "\n".join(lines)

    def _online_least_squares_operation_lines(self, operations: list[list[Any]]) -> list[str]:
        lines: list[str] = []
        for operation in operations:
            if operation[0] == "ADD":
                lines.append(f"ADD {operation[1]} {operation[2]}")
            else:
                lines.append(f"QUERY {operation[1]}")
        return lines

    def _online_least_squares_outputs(self, operations: list[list[Any]]) -> list[str]:
        n = 0
        sx = sy = sxx = sxy = 0
        first_x: int | None = None
        same_x = True
        outputs: list[str] = []
        for operation in operations:
            if operation[0] == "ADD":
                x = int(operation[1])
                y = int(operation[2])
                if n == 0:
                    first_x = x
                elif x != first_x:
                    same_x = False
                n += 1
                sx += x
                sy += y
                sxx += x * x
                sxy += x * y
                continue
            x0 = int(operation[1])
            if n == 0:
                outputs.append("0.000000")
            elif same_x:
                outputs.append(f"{float(sy) / n:.6f}")
            else:
                numerator = float(n) * sxy - float(sx) * sy
                denominator = float(n) * sxx - float(sx) * sx
                a = numerator / denominator
                b = (float(sy) - a * float(sx)) / n
                outputs.append(f"{a * x0 + b:.6f}")
        return outputs

    def _online_least_squares_hidden_inputs(self) -> list[tuple[str, str]]:
        cases = [
            (
                "1\nQUERY 0",
                "没有样本时按题意返回 0.000000。",
            ),
            (
                "4\nADD 5 10\nQUERY 5\nQUERY 100\nQUERY -100",
                "只有一个 x 值时使用常数模型，所有查询都返回 y 的平均值。",
            ),
            (
                "5\nADD 0 1\nADD 1 3\nADD 2 5\nQUERY 3\nQUERY -1",
                "样本完全落在 y=2x+1 上，查询可直接由拟合直线得到。",
            ),
            (
                "7\nADD -10 -20\nADD 0 5\nQUERY 10\nADD 10 40\nQUERY -5\nQUERY 0\nQUERY 20",
                "覆盖负数距离、负数价格和新增样本后参数变化。",
            ),
            (
                "6\nADD 2 8\nADD 2 10\nADD 2 12\nQUERY 2\nQUERY 9\nQUERY -4",
                "所有 x 相同时，预测值恒为当前 y 的平均值。",
            ),
            (
                "8\nADD 1 1\nADD 1 3\nQUERY 1\nADD 3 9\nQUERY 2\nADD 5 11\nQUERY 4\nQUERY -2",
                "先经历退化状态，再加入不同 x 变成唯一最小二乘解。",
            ),
            (
                "6\nADD 1000000 1000000\nADD -1000000 -999999\nQUERY 0\nQUERY 1000000\nADD 0 1\nQUERY -1000000",
                "覆盖较大正负值，检验统计量和浮点格式化。",
            ),
            (
                "10\nQUERY 7\nADD 0 0\nQUERY 3\nADD 10 30\nQUERY 5\nADD 20 80\nQUERY 15\nADD 30 90\nQUERY 25",
                "查询可能出现在任何位置，模型必须随 ADD 在线更新。",
            ),
        ]
        return [(self._online_least_squares_acm_input(self._online_least_squares_operations(case)), explanation) for case, explanation in cases]

    def _online_least_squares_official_solutions(
        self,
        requested_languages: list[str],
        mode: str,
        explanation: str,
        provided_python_acm_code: str | None,
    ) -> list[AuthoredOfficialSolution]:
        use_function_mode = mode == "function"
        available = {
            "python": self._online_least_squares_function_solution()
            if use_function_mode
            else provided_python_acm_code or self._online_least_squares_python_acm_solution(),
            "cpp": self._online_least_squares_cpp_solution(use_function_mode),
            "java": self._online_least_squares_java_solution(use_function_mode),
        }
        ordered_languages = [language for language in requested_languages if language in available]
        if "python" not in ordered_languages:
            ordered_languages.insert(0, "python")
        solutions: list[AuthoredOfficialSolution] = []
        for language in ordered_languages:
            code = available.get(language)
            if code:
                if mode == "both":
                    function_code = self._online_least_squares_function_solution() if language == "python" else (
                        self._online_least_squares_cpp_solution(True)
                        if language == "cpp"
                        else self._online_least_squares_java_solution(True)
                    )
                    acm_code = (provided_python_acm_code or self._online_least_squares_python_acm_solution()) if language == "python" else (
                        self._online_least_squares_cpp_solution(False)
                        if language == "cpp"
                        else self._online_least_squares_java_solution(False)
                    )
                    solutions.append(
                        AuthoredOfficialSolution(
                            language=language,
                            code=function_code,
                            explanation=explanation,
                            acm_code=acm_code,
                            function_code=function_code,
                        )
                    )
                else:
                    solutions.append(AuthoredOfficialSolution(language=language, code=code, explanation=explanation))
        return solutions

    def _online_least_squares_python_acm_solution(self) -> str:
        return normalize_source_code(
            """
import sys


def main():
    data = sys.stdin.buffer.read().split()
    idx = 0
    q = int(data[idx])
    idx += 1
    n = 0
    sx = sy = sxx = sxy = 0
    first_x = None
    same_x = True
    out = []

    for _ in range(q):
        op = data[idx]
        idx += 1
        if op == b"ADD":
            x = int(data[idx])
            y = int(data[idx + 1])
            idx += 2
            if n == 0:
                first_x = x
            elif x != first_x:
                same_x = False
            n += 1
            sx += x
            sy += y
            sxx += x * x
            sxy += x * y
        else:
            x0 = int(data[idx])
            idx += 1
            if n == 0:
                out.append("0.000000")
            elif same_x:
                out.append(f"{float(sy) / n:.6f}")
            else:
                numerator = float(n) * sxy - float(sx) * sy
                denominator = float(n) * sxx - float(sx) * sx
                a = numerator / denominator
                b = (float(sy) - a * float(sx)) / n
                out.append(f"{a * x0 + b:.6f}")
    sys.stdout.write("\\n".join(out))


main()
"""
        )

    def _online_least_squares_function_solution(self) -> str:
        return normalize_source_code(
            """
def online_least_squares(operations: list[str]) -> list[str]:
    n = 0
    sx = sy = sxx = sxy = 0
    first_x = None
    same_x = True
    result: list[str] = []

    for operation in operations:
        parts = operation.split()
        op = parts[0]
        if op == "ADD":
            x = int(parts[1])
            y = int(parts[2])
            if n == 0:
                first_x = x
            elif x != first_x:
                same_x = False
            n += 1
            sx += x
            sy += y
            sxx += x * x
            sxy += x * y
        else:
            x0 = int(parts[1])
            if n == 0:
                result.append("0.000000")
            elif same_x:
                result.append(f"{float(sy) / n:.6f}")
            else:
                numerator = float(n) * sxy - float(sx) * sy
                denominator = float(n) * sxx - float(sx) * sx
                a = numerator / denominator
                b = (float(sy) - a * float(sx)) / n
                result.append(f"{a * x0 + b:.6f}")
    return result
"""
        )

    def _online_least_squares_cpp_solution(self, use_function_mode: bool) -> str:
        core = """
vector<string> solveOperations(const vector<string>& operations) {
    long long n = 0;
    long double sx = 0, sy = 0, sxx = 0, sxy = 0;
    long double firstX = 0;
    bool sameX = true;
    vector<string> result;

    for (const string& operation : operations) {
        stringstream ss(operation);
        string op;
        ss >> op;
        if (op == "ADD") {
            long double x, y;
            ss >> x >> y;
            if (n == 0) firstX = x;
            else if (x != firstX) sameX = false;
            n++;
            sx += x;
            sy += y;
            sxx += x * x;
            sxy += x * y;
        } else {
            long double x0;
            ss >> x0;
            long double ans = 0;
            if (n == 0) {
                ans = 0;
            } else if (sameX) {
                ans = sy / n;
            } else {
                long double numerator = n * sxy - sx * sy;
                long double denominator = n * sxx - sx * sx;
                long double a = numerator / denominator;
                long double b = (sy - a * sx) / n;
                ans = a * x0 + b;
            }
            ostringstream out;
            out << fixed << setprecision(6) << (double)ans;
            result.push_back(out.str());
        }
    }
    return result;
}
"""
        if use_function_mode:
            return normalize_source_code(
                f"""
#include <bits/stdc++.h>
using namespace std;

{core}

vector<string> online_least_squares(vector<string> operations) {{
    return solveOperations(operations);
}}
"""
            )
        return normalize_source_code(
            f"""
#include <bits/stdc++.h>
using namespace std;

{core}

int main() {{
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int q;
    cin >> q;
    string op;
    vector<string> operations;
    operations.reserve(q);
    for (int i = 0; i < q; i++) {{
        cin >> op;
        if (op == "ADD") {{
            long long x, y;
            cin >> x >> y;
            operations.push_back("ADD " + to_string(x) + " " + to_string(y));
        }} else {{
            long long x0;
            cin >> x0;
            operations.push_back("QUERY " + to_string(x0));
        }}
    }}
    vector<string> answers = solveOperations(operations);
    for (const string& answer : answers) {{
        cout << answer << '\\n';
    }}
    return 0;
}}
"""
        )

    def _online_least_squares_java_solution(self, use_function_mode: bool) -> str:
        core = """
    private String[] solveOperations(String[] operations) {
        long n = 0L;
        double sx = 0.0, sy = 0.0, sxx = 0.0, sxy = 0.0;
        double firstX = 0.0;
        boolean sameX = true;
        ArrayList<String> result = new ArrayList<>();

        for (String operation : operations) {
            String[] parts = operation.trim().split("\\\\s+");
            String op = parts[0];
            if (op.equals("ADD")) {
                double x = Double.parseDouble(parts[1]);
                double y = Double.parseDouble(parts[2]);
                if (n == 0L) firstX = x;
                else if (x != firstX) sameX = false;
                n++;
                sx += x;
                sy += y;
                sxx += x * x;
                sxy += x * y;
            } else {
                double x0 = Double.parseDouble(parts[1]);
                double ans;
                if (n == 0L) {
                    ans = 0.0;
                } else if (sameX) {
                    ans = sy / n;
                } else {
                    double numerator = n * sxy - sx * sy;
                    double denominator = n * sxx - sx * sx;
                    double a = numerator / denominator;
                    double b = (sy - a * sx) / n;
                    ans = a * x0 + b;
                }
                result.add(String.format(Locale.US, "%.6f", ans));
            }
        }
        return result.toArray(new String[0]);
    }
"""
        if use_function_mode:
            return normalize_source_code(
                f"""
import java.util.*;

class Solution {{
{core}

    public String[] online_least_squares(String[] operations) {{
        return solveOperations(operations);
    }}
}}
"""
            )
        return normalize_source_code(
            f"""
import java.io.*;
import java.util.*;

class Solution {{
{core}

    public static void main(String[] args) throws Exception {{
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        int q = Integer.parseInt(br.readLine().trim());
        String[] operations = new String[q];
        for (int i = 0; i < q; i++) {{
            operations[i] = br.readLine().trim();
        }}
        String[] answers = new Solution().solveOperations(operations);
        StringBuilder out = new StringBuilder();
        for (String answer : answers) {{
            out.append(answer).append('\\n');
        }}
        System.out.print(out.toString());
    }}
}}
"""
        )

    def _online_least_squares_tags(self, requested_tags: list[str]) -> list[str]:
        tags: list[str] = []
        for tag in [*requested_tags, "在线学习", "最小二乘回归", "Data Stream", "Math", "Simulation"]:
            cleaned = tag.strip()
            if cleaned and cleaned not in tags:
                tags.append(cleaned)
        return tags[:10]

    def _online_least_squares_solution_explanation(self) -> str:
        return """
## 题解：在线最小二乘回归

每次 `QUERY` 都重新扫描所有样本会达到 `O(Q^2)`，无法通过 `2 * 10^5` 级别的数据。因此要维护最小二乘闭式公式需要的增量统计量。

## 状态维护

维护五个量：

```text
n   = 样本数
Sx  = sum(x)
Sy  = sum(y)
Sxx = sum(x * x)
Sxy = sum(x * y)
```

执行 `ADD x y` 时只做常数次更新：

```text
n   += 1
Sx  += x
Sy  += y
Sxx += x * x
Sxy += x * y
```

## 查询

如果 `n = 0`，按题意返回 `0.000000`。

如果所有样本的 `x` 都相同，分母 `n * Sxx - Sx * Sx` 为 0，斜率不唯一。题目规定退化为常数模型，答案是 `Sy / n`。

其他情况下代入闭式公式：

```text
a = (n * Sxy - Sx * Sy) / (n * Sxx - Sx * Sx)
b = (Sy - a * Sx) / n
answer = a * x0 + b
```

实现时用 `same_x` 记录当前所有 `x` 是否都相同，避免用浮点数判断分母是否为 0。Python 整数不会溢出；C++/Java 版本在最终公式计算时使用浮点类型并固定输出 6 位小数。

## 复杂度

- 每次 `ADD`：`O(1)`
- 每次 `QUERY`：`O(1)`
- 总时间复杂度：`O(Q)`
- 空间复杂度：`O(1)`
""".strip()

    def _extract_chinese_samples(self, raw: str) -> list[dict[str, str | None]]:
        normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
        matches = list(re.finditer(r"(?m)^样例\s*\d+\s*$", normalized))
        samples: list[dict[str, str | None]] = []
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
            block = normalized[match.end() : end]
            if "题解" in block:
                block = block.split("题解", 1)[0]
            input_match = re.search(r"输入[:：]?\s*\n(?P<input>.*?)(?=\n输出[:：]?\s*\n)", block, re.DOTALL)
            output_match = re.search(r"输出[:：]?\s*\n(?P<output>.*?)(?=\n样例解释|\Z)", block, re.DOTALL)
            if not input_match or not output_match:
                continue
            explanation = None
            explanation_match = re.search(r"样例解释\s*\n(?P<explanation>.*)\Z", block, re.DOTALL)
            if explanation_match:
                explanation = explanation_match.group("explanation").strip() or None
            samples.append(
                {
                    "input": input_match.group("input").strip(),
                    "output": output_match.group("output").strip(),
                    "explanation": explanation,
                }
            )
        return samples

    def _extract_python_code(self, raw: str) -> str | None:
        normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
        marker = re.search(r"Python\s*代码", normalized, re.IGNORECASE)
        if not marker:
            return None
        tail = normalized[marker.end() :]
        fenced = re.search(r"```(?:python)?\s*\n(?P<code>.*?)(?:\n```|\Z)", tail, re.DOTALL | re.IGNORECASE)
        if fenced:
            return normalize_source_code(fenced.group("code"))
        lines = tail.splitlines()
        start = 0
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(("import ", "from ", "def ", "class ", "#")):
                start = index
                break
        code_lines: list[str] = []
        for line in lines[start:]:
            if re.match(r"^\s*-{5,}\s*$", line):
                break
            code_lines.append(line)
        code = "\n".join(code_lines).strip()
        return normalize_source_code(code) if code else None

    def _extract_solution_explanation(self, raw: str) -> str | None:
        normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
        match = re.search(r"题解[:：]?.*?(?P<body>问题拆解.*?)(?=\nPython\s*代码|\Z)", normalized, re.DOTALL)
        if match:
            return match.group("body").strip()
        return None

    def _extract_chinese_section(self, raw: str, start_title: str, end_titles: list[str]) -> str | None:
        normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
        start_match = re.search(rf"(?m)^{re.escape(start_title)}\s*$", normalized)
        if not start_match:
            return None
        end_pattern = "|".join(re.escape(title) for title in end_titles)
        end_match = re.search(rf"(?m)^({end_pattern})\b", normalized[start_match.end() :])
        end = start_match.end() + end_match.start() if end_match else len(normalized)
        return normalized[start_match.end() : end].strip() or None

    def _first_nonempty_line(self, raw: str) -> str | None:
        for line in raw.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
        return None

    def _import_statement_body(self, raw: str) -> str:
        normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
        body = normalized.split("题解", 1)[0].strip()
        return body or normalized[:6000].strip()

    def _online_least_squares_description(self, _raw: str, mode: str) -> str:
        mode_note = {
            "acm": "本题使用 **ACM 模式**：从标准输入读取操作并向标准输出打印每个查询结果。",
            "function": "本题使用 **函数模式**：实现 `online_least_squares(operations)`，返回每个查询结果组成的字符串列表。",
            "both": "本题同时支持 **ACM 模式** 和 **函数模式**。两种模式使用同一组逻辑用例，但输入输出展示形式不同。",
        }.get(mode, "本题支持在线处理操作序列。")
        return f"""
## 题目描述

你在一家同城物流平台负责“运费估计引擎”。平台会不断新增历史订单样本，每条样本包含运输距离 `x` 和成交运费 `y`。系统用一元线性回归模型估计新订单价格：

```text
y = a * x + b
```

你需要维护一个在线学习模块，按顺序处理两类操作：

- `ADD x y`：新增一条历史样本 `(x, y)`。
- `QUERY x0`：基于当前全部样本拟合最小二乘直线，并输出该直线在 `x0` 处的预测值。

{mode_note}

## 最小二乘公式

设当前样本数为 `n`，并维护：

```text
Sx  = sum(xi)
Sy  = sum(yi)
Sxx = sum(xi * xi)
Sxy = sum(xi * yi)
```

当最优解唯一时：

```text
a = (n * Sxy - Sx * Sy) / (n * Sxx - Sx * Sx)
b = (Sy - a * Sx) / n
answer = a * x0 + b
```

## 退化规则

- 如果当前样本数 `n = 0`，`QUERY` 输出 `0.000000`。
- 如果所有样本的 `x` 都相同，最小二乘直线不唯一。此时规定使用常数模型，预测值为当前所有 `y` 的平均值 `Sy / n`。

## 输入与输出

### ACM 模式

第一行包含整数 `Q`，表示操作总数。接下来 `Q` 行，每行是：

```text
ADD x y
QUERY x0
```

对每个 `QUERY` 输出一行预测值，固定保留 6 位小数。

### 函数模式

函数签名：

```python
def online_least_squares(operations: list[str]) -> list[str]:
```

`operations[i]` 是一条 `ADD x y` 或 `QUERY x0` 操作。函数返回每个查询的预测值字符串，固定保留 6 位小数。

## 约束

- `1 <= Q <= 2 * 10^5`
- `-10^6 <= x, y, x0 <= 10^6`
- 保证中间统计量在 64 位有符号整数范围内。
""".strip()

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
        agent_session_id: str | None = None,
        existing_run: AgentRun | None = None,
    ) -> tuple[ProblemDraft, AgentRun]:
        run = existing_run
        if run is None:
            run_id = uuid.uuid4()
            session_id = agent_session_id or str(run_id)
            run_input = payload.model_dump()
            run_input["agent_session_id"] = session_id
            run = AgentRun(
                id=run_id,
                run_type=run_type,
                status="running",
                input_json=dump_json(run_input),
                output_json="{}",
                model_profile=payload.model_profile,
                locale=payload.locale,
                created_by=current_user.id,
            )
            self.db.add(run)
        else:
            run_input = {**payload.model_dump(), **load_json(run.input_json, {})}
            session_id = str(run_input.get("agent_session_id") or agent_session_id or run.id)
            run_input["agent_session_id"] = session_id
            run.input_json = dump_json(run_input)
            run.output_json = dump_json({**load_json(run.output_json, {}), "agent_session_id": session_id})
            run.status = "running"
            run.error_message = None
            run.finished_at = None
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
                        "max_repair_attempts": authoring_repair_attempts(),
            },
            "succeeded",
        )
        self._commit_trace(run)

        try:
            authored: AuthoredProblemDraft | None = None
            testcases: list[dict[str, Any]] = []
            validation_report: dict[str, Any] | None = None
            repair_context: dict[str, Any] | None = None
            last_parse_error: ValueError | None = None
            total_attempts = authoring_repair_attempts() + 1

            for attempt in range(1, total_attempts + 1):
                model_input = {
                    "model_profile": payload.model_profile,
                    "locale": payload.locale,
                    "attempt": attempt,
                    "repair_attempt": max(attempt - 1, 0),
                }
                try:
                    completion = self._call_model_completion(payload, repair_context, system_prompt, prompt_builder)
                    raw = completion.content
                    self._add_step(
                        run,
                        model_step_type,
                        "ai_provider.complete_json",
                        model_input,
                        {**completion.metadata, "raw_length": len(raw), "attempt": attempt},
                        "succeeded",
                    )
                    self._commit_trace(run)
                except AIProviderEmptyResponseError as exc:
                    last_parse_error = ValueError(str(exc))
                    self._add_step(
                        run,
                        model_step_type,
                        "ai_provider.complete_json",
                        model_input,
                        {**exc.metadata, "raw_length": 0, "attempt": attempt},
                        "failed",
                        str(exc),
                    )
                    self._commit_trace(run)
                    if attempt >= total_attempts:
                        raise last_parse_error from exc
                    repair_context = self._provider_repair_context(payload, str(exc), exc.metadata, attempt)
                    continue
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
                    self._commit_trace(run)
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
                self._commit_trace(run)
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
                source_metadata_json=dump_json({**source_metadata, "agent_session_id": session_id}),
                status="validated" if validation_report["passed"] else "validation_failed",
                created_by=current_user.id,
            )
            self.db.add(draft)
            self.db.flush()
            run.draft_id = draft.id
            run.status = "succeeded"
            run.output_json = dump_json(
                {"draft_id": str(draft.id), "validation": validation_report, "agent_session_id": session_id}
            )
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
            raise AgentRunProviderUnavailableError(str(exc), str(run.id)) from exc
        except (ValidationError, ValueError) as exc:
            self._fail_run(run, str(exc), "validation")
            raise AgentRunFailedError(str(exc), str(run.id)) from exc

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
                    io_metadata_json=dump_json(testcase.get("io_metadata")) if testcase.get("io_metadata") else None,
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

    def chat_about_run(
        self,
        run_id: str,
        message: str,
        model_profile: str,
        locale: str,
        current_user: User,
    ) -> tuple[str, list[str], AgentStep]:
        run = self.db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if not run:
            raise LookupError("Agent run not found")
        provider = self.provider
        if provider is None:
            config = resolve_ai_config(model_profile)
            provider = build_provider(config)
        prompt = json.dumps(
            {
                "task": "Explain this FastOJ admin agent run and suggest concrete next actions.",
                "response_language": ai_response_language(locale),
                "admin_message": message.strip(),
                "run": self._safe_run_context(run),
                "required_json_schema": {
                    "message": "short answer for the admin",
                    "suggested_actions": ["short actionable suggestions"],
                },
                "rules": [
                    "Do not reveal hidden testcase content.",
                    "Do not reproduce full raw source material or full code blocks.",
                    "Keep the answer focused on diagnosis, retry guidance, or manual edits.",
                ],
            },
            ensure_ascii=False,
        )
        try:
            completion = provider.complete_json_with_metadata(
                "You are FastOJ's admin-only Agent Run assistant. Return only JSON.",
                prompt,
            )
        except AIProviderEmptyResponseError as exc:
            self._add_step(
                run,
                "agent_chat",
                "ai_provider.complete_json",
                {
                    "model_profile": model_profile,
                    "locale": locale,
                    "message_length": len(message.strip()),
                    "message": message.strip()[:2000],
                    "asked_by": str(current_user.id),
                },
                exc.metadata,
                "failed",
                str(exc),
            )
            self.db.commit()
            raise ValueError(str(exc)) from exc
        data = self._extract_json(completion.content)
        answer = str(data.get("message") or completion.content.strip()[:1200] or "No answer was returned.")
        suggested = data.get("suggested_actions")
        if isinstance(suggested, str):
            suggested_actions = [suggested]
        elif isinstance(suggested, list):
            suggested_actions = [str(item) for item in suggested if item is not None][:6]
        else:
            suggested_actions = []
        step = self._add_step(
            run,
            "agent_chat",
            "ai_provider.complete_json",
            {
                "model_profile": model_profile,
                "locale": locale,
                "message_length": len(message.strip()),
                "message": message.strip()[:2000],
                "asked_by": str(current_user.id),
            },
            {
                **completion.metadata,
                "message": answer,
                "suggested_actions": suggested_actions,
            },
            "succeeded",
        )
        self.db.commit()
        return answer, suggested_actions, step

    def retry_run(
        self,
        run_id: str,
        guidance: str | None,
        locale: str | None,
        model_profile: str | None,
        current_user: User,
    ) -> tuple[ProblemDraft, AgentRun]:
        parent = self.db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if not parent:
            raise LookupError("Agent run not found")
        parent_input = load_json(parent.input_json, {})
        session_id = self._agent_session_id(parent)
        retry_guidance = (guidance or "").strip()
        if parent.run_type == "problem_import":
            payload = ProblemImportRequest.model_validate(parent_input)
            updates: dict[str, Any] = {}
            if locale:
                updates["locale"] = locale
            if model_profile:
                updates["model_profile"] = model_profile
            if retry_guidance:
                notes = "\n\n".join(part for part in [payload.import_notes, f"Retry guidance: {retry_guidance}"] if part)
                updates["import_notes"] = notes[:2000]
            payload = payload.model_copy(update=updates)
            draft, retry = self.create_import_draft(payload, current_user, agent_session_id=session_id)
        elif parent.run_type == "problem_authoring":
            payload = ProblemAuthoringRequest.model_validate(parent_input)
            updates = {}
            if locale:
                updates["locale"] = locale
            if model_profile:
                updates["model_profile"] = model_profile
            if retry_guidance:
                constraints = "\n\n".join(part for part in [payload.constraints, f"Retry guidance: {retry_guidance}"] if part)
                updates["constraints"] = constraints[:2000]
            payload = payload.model_copy(update=updates)
            draft, retry = self.create_draft(payload, current_user, agent_session_id=session_id)
        else:
            raise ValueError("Only problem authoring and import runs can be retried")

        retry_input = load_json(retry.input_json, {})
        retry_input["agent_session_id"] = session_id
        retry_input["parent_run_id"] = str(parent.id)
        if retry_guidance:
            retry_input["retry_guidance"] = retry_guidance[:500]
        retry.input_json = dump_json(retry_input)
        retry_output = load_json(retry.output_json, {})
        retry_output["agent_session_id"] = session_id
        retry_output["parent_run_id"] = str(parent.id)
        retry.output_json = dump_json(retry_output)
        draft_metadata = load_json(draft.source_metadata_json, {})
        draft_metadata["agent_session_id"] = session_id
        draft_metadata["parent_run_id"] = str(parent.id)
        if retry_guidance:
            draft_metadata["retry_guidance"] = retry_guidance[:500]
        draft.source_metadata_json = dump_json(draft_metadata)
        self.db.commit()
        self.db.refresh(draft)
        self.db.refresh(retry)
        return draft, retry

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
            completion = provider.complete_json_with_metadata(
                problem_authoring.SOLUTION_SYSTEM_PROMPT,
                problem_authoring.build_solution_prompt(context),
            )
            raw = completion.content
            self._add_step(
                run,
                "solution_generation",
                "ai_provider.complete_json",
                {"draft_id": str(draft.id), "language": language, "model_profile": model_profile},
                {**completion.metadata, "raw_length": len(raw)},
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
            raise AgentRunProviderUnavailableError(str(exc), str(run.id)) from exc
        except AIProviderEmptyResponseError as exc:
            self._fail_run(run, str(exc), "solution_generation")
            raise AgentRunFailedError(str(exc), str(run.id)) from exc
        except (ValidationError, ValueError) as exc:
            self._fail_run(run, str(exc), "solution_generation")
            raise AgentRunFailedError(str(exc), str(run.id)) from exc

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
        try:
            raw = provider.complete_json(
                problem_authoring.SOLUTION_SYSTEM_PROMPT,
                problem_authoring.build_solution_prompt(context),
            )
        except AIProviderEmptyResponseError as exc:
            raise ValueError(str(exc)) from exc
        return self._parse_solution_response(raw, language)

    def _call_model(
        self,
        payload: ProblemAuthoringRequest | ProblemImportRequest,
        repair_context: dict[str, Any] | None,
        system_prompt: str,
        prompt_builder: Callable[[dict[str, Any]], str],
    ) -> str:
        return self._call_model_completion(payload, repair_context, system_prompt, prompt_builder).content

    def _call_model_completion(
        self,
        payload: ProblemAuthoringRequest | ProblemImportRequest,
        repair_context: dict[str, Any] | None,
        system_prompt: str,
        prompt_builder: Callable[[dict[str, Any]], str],
    ) -> AICompletion:
        provider = self.provider
        if provider is None:
            config = resolve_ai_config(payload.model_profile)
            provider = build_provider(config)
        context = payload.model_dump()
        context["response_language"] = ai_response_language(payload.locale)
        if repair_context:
            context["repair_request"] = repair_context
        return provider.complete_json_with_metadata(system_prompt, prompt_builder(context))

    def _agent_session_id(self, run: AgentRun, seen: set[str] | None = None) -> str:
        seen = seen or set()
        run_id = str(run.id)
        if run_id in seen:
            return run_id
        seen.add(run_id)

        run_input = load_json(run.input_json, {})
        run_output = load_json(run.output_json, {})
        for source in (run_input, run_output):
            session_id = str(source.get("agent_session_id") or "").strip()
            if session_id:
                return session_id

        parent_run_id = str(run_input.get("parent_run_id") or run_output.get("parent_run_id") or "").strip()
        if parent_run_id:
            parent = self.db.query(AgentRun).filter(AgentRun.id == parent_run_id).first()
            if parent is not None:
                return self._agent_session_id(parent, seen)

        raw_material = str(run_input.get("raw_material") or "").strip()
        if raw_material:
            digest = hashlib.sha256(raw_material.encode("utf-8")).hexdigest()[:16]
            return f"legacy-import:{run.created_by}:{run_input.get('mode') or 'unknown'}:{digest}"
        topic = str(run_input.get("topic") or "").strip()
        if topic:
            digest = hashlib.sha256(topic.encode("utf-8")).hexdigest()[:16]
            return f"legacy-topic:{run.created_by}:{run.run_type}:{run_input.get('mode') or 'unknown'}:{digest}"
        return run_id

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
                "tags": self._import_tags(payload.tags, authored.tags) if isinstance(payload, ProblemImportRequest) else payload.tags or authored.tags,
                "official_solution_language": primary.language,
                "official_solution_code": primary.code,
                "official_solution_explanation": primary.explanation,
                "official_solutions": solutions,
            }
        )

    def _import_tags(self, requested_tags: list[str], authored_tags: list[str]) -> list[str]:
        merged: list[str] = []
        for tag in [*requested_tags, *authored_tags]:
            cleaned = str(tag or "").strip()
            if cleaned and cleaned not in merged:
                merged.append(cleaned)
        return merged[:10]

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
            candidate = self._first_balanced_json(raw)
            if candidate:
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    return {}
        return {}

    def _first_balanced_json(self, raw: str) -> str | None:
        max_depth = 256
        start = -1
        expected_stack: list[str] = []
        in_string = False
        escaped = False
        previous_nonspace = ""
        for index, char in enumerate(raw):
            if start == -1:
                if char == "{":
                    start = index
                    expected_stack = ["}"]
                    previous_nonspace = char
                elif char == "[":
                    start = index
                    expected_stack = ["]"]
                    previous_nonspace = char
                continue

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                    previous_nonspace = char
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                expected_stack.append("}")
            elif char == "[":
                expected_stack.append("]")
            if len(expected_stack) > max_depth:
                start = -1
                expected_stack = []
                in_string = False
                escaped = False
                previous_nonspace = ""
                continue
            if char.isalpha() and previous_nonspace not in (":", "[", ","):
                start = -1
                expected_stack = []
                in_string = False
                escaped = False
                previous_nonspace = ""
                continue
            if start == -1:
                continue
            if char in ("{", "["):
                previous_nonspace = char
                continue
            if char in ("}", "]"):
                if not expected_stack or char != expected_stack[-1]:
                    start = -1
                    expected_stack = []
                    in_string = False
                    escaped = False
                    previous_nonspace = ""
                    continue
                expected_stack.pop()
                if not expected_stack:
                    return raw[start : index + 1]
            if not char.isspace():
                previous_nonspace = char
        return None

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
        solutions: list[dict[str, str]] = []
        for solution in authored.official_solutions:
            item = {
                "language": solution.language,
                "code": solution.code,
                "explanation": solution.explanation,
            }
            if solution.acm_code:
                item["acm_code"] = solution.acm_code
            if solution.function_code:
                item["function_code"] = solution.function_code
            solutions.append(item)
        return solutions

    def _effective_structured_import_languages(
        self,
        authored: AuthoredProblemDraft,
        requested_languages: list[str],
    ) -> tuple[AuthoredProblemDraft, list[str], list[str]]:
        available_languages: list[str] = []
        for solution in authored.official_solutions:
            language = solution.language.strip().lower()
            if language and language not in available_languages:
                available_languages.append(language)

        requested = [language for language in requested_languages if Language.is_supported(language)]
        effective = [language for language in requested if language in available_languages]
        if not effective and available_languages:
            effective = [available_languages[0]]

        missing = [language for language in requested if language not in available_languages]
        warnings: list[str] = []
        if missing and effective:
            warnings.append(
                "已选择 "
                + ", ".join(missing)
                + "，但本次结构化导入未能可靠补齐这些语言；已保留 "
                + ", ".join(effective)
                + " 以保证草稿通过验证。"
            )

        return self._with_primary_solution(authored, effective or requested), effective or requested, warnings

    def _with_primary_solution(
        self,
        authored: AuthoredProblemDraft,
        preferred_languages: list[str],
    ) -> AuthoredProblemDraft:
        solutions = self._ordered_solutions_for_languages(authored.official_solutions, preferred_languages)
        if not solutions:
            return authored
        primary = solutions[0]
        return authored.model_copy(
            update={
                "official_solution_language": primary.language,
                "official_solution_code": primary.code,
                "official_solution_explanation": primary.explanation,
                "official_solutions": solutions,
            }
        )

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
                    "io_metadata": testcase.io_metadata,
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
                    "io_metadata": testcase.io_metadata,
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
                io_metadata=testcase.get("io_metadata") if isinstance(testcase.get("io_metadata"), dict) else None,
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
                    acm_code=solution.get("acm_code"),
                    function_code=solution.get("function_code"),
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
                acm_code = item.acm_code
                function_code = item.function_code
            elif isinstance(item, dict):
                language = str(item.get("language") or "").strip().lower()
                code = normalize_source_code(str(item.get("code") or ""))
                explanation = str(item.get("explanation") or "").strip()
                raw_acm_code = item.get("acm_code")
                raw_function_code = item.get("function_code")
                acm_code = normalize_source_code(str(raw_acm_code)) if raw_acm_code is not None else None
                function_code = normalize_source_code(str(raw_function_code)) if raw_function_code is not None else None
            else:
                continue
            if not language or language in seen or not Language.is_supported(language):
                continue
            if not code.strip() or not explanation:
                continue
            solution = {"language": language, "code": code, "explanation": explanation}
            if acm_code and acm_code.strip():
                solution["acm_code"] = acm_code
            if function_code and function_code.strip():
                solution["function_code"] = function_code
            normalized.append(solution)
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
                    "io_metadata": testcase.get("io_metadata") if isinstance(testcase.get("io_metadata"), dict) else None,
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
            "max_attempts": authoring_repair_attempts() + 1,
            "instruction": "Return a complete replacement JSON object matching the required schema.",
            "safe_error": message,
            "requested_mode": payload.mode,
            "requested_difficulty": payload.difficulty,
            "requested_tags": payload.tags,
            "requested_languages": payload.requested_languages(),
        }

    def _provider_repair_context(
        self,
        payload: ProblemAuthoringRequest | ProblemImportRequest,
        message: str,
        metadata: dict[str, Any],
        attempt: int,
    ) -> dict[str, Any]:
        return {
            "kind": "provider_empty_response_repair",
            "attempt": attempt + 1,
            "max_attempts": authoring_repair_attempts() + 1,
            "instruction": (
                "The previous model response used its output budget before returning JSON content. "
                "Return the complete JSON object immediately, keep reasoning brief, and avoid prose outside JSON."
            ),
            "safe_error": message,
            "finish_reason": metadata.get("finish_reason"),
            "completion_tokens": metadata.get("completion_tokens"),
            "reasoning_tokens": metadata.get("reasoning_tokens"),
            "max_tokens": metadata.get("max_tokens"),
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
            "max_attempts": authoring_repair_attempts() + 1,
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

    def _safe_run_context(self, run: AgentRun) -> dict[str, Any]:
        run_input = load_json(run.input_json, {})
        safe_input = {
            key: value
            for key, value in run_input.items()
            if key not in {"raw_material", "code", "official_solution_code", "official_solutions"}
        }
        if "raw_material" in run_input:
            safe_input["raw_material_length"] = len(str(run_input.get("raw_material") or ""))
        steps = (
            self.db.query(AgentStep)
            .filter(AgentStep.run_id == run.id)
            .order_by(AgentStep.step_index.asc())
            .all()
        )
        safe_steps = []
        for step in steps:
            output = load_json(step.output_json, {})
            safe_steps.append(
                {
                    "step_index": step.step_index,
                    "step_type": step.step_type,
                    "tool_name": step.tool_name,
                    "status": step.status,
                    "error_message": self._truncate(step.error_message, 300),
                    "finish_reason": output.get("finish_reason"),
                    "raw_length": output.get("raw_length") or output.get("content_len"),
                    "reasoning_tokens": output.get("reasoning_tokens"),
                    "case_count": output.get("case_count"),
                    "summary": output.get("summary"),
                    "passed": output.get("passed"),
                }
            )
        return {
            "id": str(run.id),
            "run_type": run.run_type,
            "status": run.status,
            "model_profile": run.model_profile,
            "locale": run.locale,
            "draft_id": str(run.draft_id) if run.draft_id else None,
            "error_message": self._truncate(run.error_message, 500),
            "input": safe_input,
            "steps": safe_steps,
        }

    def _truncate(self, value: Any, limit: int) -> str | None:
        if value is None:
            return None
        text = str(value)
        return text if len(text) <= limit else f"{text[:limit]}..."

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

    def _commit_trace(self, run: AgentRun) -> None:
        self.db.commit()
        self.db.refresh(run)

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
