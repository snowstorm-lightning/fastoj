import json
import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.ai.config import AIConfig
from backend.ai.prompts import problem_authoring
from backend.ai.providers import AIProviderUnavailableError, BaseAIProvider, build_provider
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
from backend.schemas.problem_authoring import AuthoredProblemDraft, ProblemAuthoringRequest


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

    def validate(self, draft: AuthoredProblemDraft, testcases: list[dict[str, Any]]) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []

        def check(name: str, passed: bool, message: str) -> None:
            checks.append({"name": name, "passed": passed, "message": message})

        required_fields = {
            "title": draft.title,
            "description": draft.description,
            "official_solution_code": draft.official_solution_code,
            "official_solution_explanation": draft.official_solution_explanation,
            "time_complexity": draft.time_complexity,
            "space_complexity": draft.space_complexity,
        }
        for field, value in required_fields.items():
            check(field, bool(str(value or "").strip()), f"{field} is required")

        if draft.mode == "acm":
            check("input_format", bool(str(draft.input_format or "").strip()), "ACM mode requires input_format")
            check("output_format", bool(str(draft.output_format or "").strip()), "ACM mode requires output_format")
        else:
            check(
                "function_signature",
                bool(str(draft.function_signature or "").strip()),
                "Function mode requires function_signature",
            )

        public_count = sum(1 for testcase in testcases if not testcase["is_hidden"])
        hidden_count = sum(1 for testcase in testcases if testcase["is_hidden"])
        check("public_sample_count", public_count >= 2, "At least 2 public sample testcases are required")
        check("hidden_testcase_count", hidden_count >= 6, "At least 6 hidden testcases are required")
        check(
            "non_empty_outputs",
            all(str(testcase.get("output") or "").strip() for testcase in testcases),
            "Every expected output must be non-empty",
        )

        if draft.mode == "function" and str(draft.function_signature or "").strip():
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
        language = draft.official_solution_language
        if draft.mode == "function":
            if language != "python":
                return [
                    {
                        "case_index": None,
                        "hidden": None,
                        "passed": False,
                        "status": "se",
                        "error_message": "Function-mode draft validation currently supports Python only.",
                    }
                ]
            code = self._build_python_function_harness(draft)
        else:
            code = draft.official_solution_code

        results: list[dict[str, Any]] = []
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
                    "passed": passed,
                    "status": "ac" if passed else status_value if status_value != "ac" else "wa",
                    "execute_time": execution.get("execute_time", 0),
                    "memory_used": execution.get("memory_used", 0),
                    "error_message": self._safe_case_error(status_value, passed),
                }
            )
        return results

    def _build_python_function_harness(self, draft: AuthoredProblemDraft) -> str:
        function_name = self._function_name(draft)
        parameter_names = self._function_parameters(draft)
        parameter_names_json = json.dumps(parameter_names, ensure_ascii=False)
        return f"""{draft.official_solution_code.rstrip()}

if __name__ == "__main__":
    import json
    import sys

    def _fastoj_load_args(raw, parameter_names):
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            return []
        if len(lines) > 1:
            return [json.loads(line) for line in lines]
        value = json.loads(lines[0])
        names = [name for name in parameter_names if name not in ("self", "cls")]
        if isinstance(value, dict) and names:
            if all(name in value for name in names):
                return [value[name] for name in names]
            args_value = value.get("args")
            if isinstance(args_value, list):
                return args_value
            return [value]
        if isinstance(value, list) and len(names) > 1 and len(value) == len(names):
            return value
        return [value]

    raw = sys.stdin.read().strip()
    args = _fastoj_load_args(raw, {parameter_names_json})
    fn = globals().get("{function_name}")
    if not callable(fn) and "Solution" in globals():
        candidate = getattr(Solution(), "{function_name}", None)
        if callable(candidate):
            fn = candidate
    if not callable(fn):
        raise NameError("Expected function {function_name}")
    result = fn(*args)
    if isinstance(result, bool):
        print(str(result).lower())
    elif isinstance(result, (list, dict)):
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(result)
"""

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
        try:
            return json.loads(actual_output) == json.loads(expected_output)
        except json.JSONDecodeError:
            return False

    def _safe_case_error(self, status_value: Any, passed: bool) -> str | None:
        if passed:
            return None
        status = str(status_value or "se").upper()
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
        run = AgentRun(
            id=uuid.uuid4(),
            run_type="problem_authoring",
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
            {"topic": payload.topic, "mode": payload.mode, "target_language": payload.target_language},
            {"plan": ["generate structured draft", "validate fields and testcase counts", "run official solution", "persist draft"]},
            "succeeded",
        )

        try:
            raw = self._call_model(payload)
            self._add_step(
                run,
                "model_call",
                "ai_provider.complete_json",
                {"model_profile": payload.model_profile, "locale": payload.locale},
                {"raw_length": len(raw)},
                "succeeded",
            )
            authored = self._parse_model_response(raw)
            authored = authored.model_copy(
                update={
                    "difficulty": payload.difficulty,
                    "mode": payload.mode,
                    "tags": payload.tags or authored.tags,
                    "official_solution_language": payload.target_language or authored.official_solution_language,
                }
            )
            slug = self._unique_slug(authored.slug_candidate or authored.title)
            testcases = self._testcases(authored)
            validation_report = self.validator.validate(authored, testcases)
            self._add_step(
                run,
                "validation",
                self.validator.__class__.__name__,
                {"slug": slug, "case_count": len(testcases)},
                self._validation_step_output(validation_report),
                "succeeded" if validation_report["passed"] else "failed",
                None if validation_report["passed"] else "Draft validation failed",
            )

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
                time_complexity=authored.time_complexity,
                space_complexity=authored.space_complexity,
                testcases_json=dump_json(testcases),
                validation_report_json=dump_json(validation_report),
                status="validated" if validation_report["passed"] else "validation_failed",
                created_by=current_user.id,
            )
            self.db.add(draft)
            self.db.flush()
            run.draft_id = draft.id
            run.status = "succeeded"
            run.output_json = dump_json({"draft_id": str(draft.id), "validation": validation_report})
            run.finished_at = datetime.utcnow()
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

        self.db.add(
            Solution(
                id=uuid.uuid4(),
                problem_id=problem.id,
                language=draft.official_solution_language,
                code=draft.official_solution_code,
                explanation=draft.official_solution_explanation,
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

    def _call_model(self, payload: ProblemAuthoringRequest) -> str:
        config = AIConfig.from_settings(payload.model_profile)
        provider = self.provider or build_provider(config)
        context = payload.model_dump()
        context["response_language"] = "Simplified Chinese" if payload.locale == "zh" else "English"
        return provider.complete_json(problem_authoring.SYSTEM_PROMPT, problem_authoring.build_prompt(context))

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

        required_signal = {"title", "description", "official_solution_code"}
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
        if exclude_draft_id:
            query = query.filter(ProblemDraft.id != exclude_draft_id)
        return query.first() is not None

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
        run.finished_at = datetime.utcnow()
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
                locale="en",
                created_by=current_user.id,
                draft_id=draft.id,
                finished_at=datetime.utcnow(),
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
