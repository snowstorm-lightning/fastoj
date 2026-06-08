
import json
from typing import Any

from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from backend.core.locales import DEFAULT_LOCALE
from backend.models import Problem, TestCase
from backend.schemas.problem import ProblemDetail, ProblemFilter, ProblemListItem, SampleTestCase
from backend.scripts.seed_explanations import sample_explanation_for_slug
from backend.services.problem_modes import FUNCTION_SIGNATURES


class ProblemService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _ac_rate(problem: Problem) -> float:
        total = int(problem.total_submissions or 0)
        accepted = int(problem.accepted_submissions or 0)
        if total <= 0:
            return 0.0
        return round(min(max(accepted / total, 0.0), 1.0), 2)

    @staticmethod
    def _accepted_submissions(problem: Problem) -> int:
        total = max(int(problem.total_submissions or 0), 0)
        accepted = max(int(problem.accepted_submissions or 0), 0)
        return min(accepted, total)

    @staticmethod
    def _function_signature(problem: Problem) -> str | None:
        return problem.function_signature or FUNCTION_SIGNATURES.get(str(problem.slug))

    @staticmethod
    def _has_io_view(metadata: dict[str, Any], mode: str) -> bool:
        view = metadata.get(mode) if isinstance(metadata, dict) else None
        if not isinstance(view, dict):
            return False
        return "input" in view and "output" in view and view["input"] is not None and view["output"] is not None

    @classmethod
    def _normalize_judge_mode(cls, mode: str | None) -> str | None:
        return mode if mode in {"acm", "function"} else None

    @classmethod
    def _supported_modes(cls, problem: Problem | None, testcase: TestCase | None = None) -> set[str]:
        metadata = cls._io_metadata(testcase) if testcase is not None else {}
        supports_function = bool(cls._function_signature(problem)) if problem else False
        supports_acm = False
        if problem is not None:
            normalized_mode = str(problem.mode or "").lower()
            if normalized_mode in {"acm", "both"}:
                supports_acm = cls._has_io_view(metadata, "acm") or normalized_mode == "acm"
            elif supports_function:
                supports_acm = cls._has_io_view(metadata, "acm")
        return {
            mode
            for mode in {"acm", "function"}
            if (
                mode == "acm" and supports_acm
            ) or (
                mode == "function" and supports_function and (
                    testcase is None or cls._has_io_view(metadata, "function") or not bool(metadata)
                )
            )
        }

    @classmethod
    def _resolve_judge_mode(
        cls,
        problem: Problem | None,
        testcase: TestCase,
        requested_mode: str | None,
    ) -> str | None:
        normalized = cls._normalize_judge_mode(requested_mode)
        supported = cls._supported_modes(problem, testcase)
        normalized_problem_mode = str(problem.mode or "").lower() if problem is not None else ""
        if normalized in supported:
            return normalized

        if normalized is None:
            if normalized_problem_mode in {"acm", "both"} and "acm" in supported:
                return "acm"
            if normalized_problem_mode == "function" and "function" in supported:
                return "function"
            if "function" in supported:
                return "function"
            if "acm" in supported:
                return "acm"
            return None

        if normalized == "acm":
            if "acm" in supported:
                return "acm"
            if "function" in supported:
                return "function"
            return None
        if normalized == "function" and "acm" in supported:
            return "acm"
        if normalized == "function" and "function" in supported:
            return "function"
        return None

    @classmethod
    def _mode(cls, problem: Problem) -> str:
        if str(problem.mode or "") == "both":
            return "both"
        if str(problem.mode or "") == "function":
            return "function"
        if cls._function_signature(problem):
            return "function"
        return problem.mode or "acm"

    def get_problems(self, filters: ProblemFilter) -> tuple[list[ProblemListItem], int]:
        """Get paginated and filtered problem list."""
        query = self.db.query(Problem).filter(Problem.is_public.is_(True))

        # Apply filters
        if filters.difficulty:
            query = query.filter(Problem.difficulty == filters.difficulty)  # type: ignore[arg-type]

        if filters.keyword:
            keyword = f"%{filters.keyword}%"
            query = query.filter(
                or_(
                    Problem.title.ilike(keyword),
                    Problem.description.ilike(keyword),
                )
            )

        if filters.tags:
            tags = [tag.strip() for tag in filters.tags.split(",") if tag.strip()]
            if tags:
                query = query.filter(Problem.tags.contains(tags))

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        sort_column = getattr(Problem, filters.sort, Problem.created_at)
        if filters.order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        query = query.offset(offset).limit(filters.page_size)

        problems = query.all()

        # Convert to response models
        result = []
        for problem in problems:
            ac_rate = self._ac_rate(problem)
            result.append(
                ProblemListItem(
                    id=str(problem.id),
                    title=problem.title,  # type: ignore[arg-type]
                    slug=problem.slug,  # type: ignore[arg-type]
                    difficulty=problem.difficulty.value,
                    tags=problem.tags or [],  # type: ignore[arg-type]
                    total_submissions=problem.total_submissions,  # type: ignore[arg-type]
                    accepted_submissions=self._accepted_submissions(problem),
                    ac_rate=ac_rate,
                    is_public=problem.is_public,  # type: ignore[arg-type]
                    mode=self._mode(problem),
                    function_signature=self._function_signature(problem),
                    created_at=problem.created_at.isoformat(),
                )
            )

        return result, total

    def get_problem_by_id(
        self,
        problem_id: str,
        locale: str = DEFAULT_LOCALE,
        judge_mode: str | None = None,
    ) -> ProblemDetail | None:
        """Get problem detail by ID."""
        problem = self.db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem or not problem.is_public:
            return None

        # Expose public testcases in the problem detail. Hidden testcases remain
        # available only to the judge worker during full submissions.
        sample_testcases = (
            self.db.query(TestCase)
            .filter(
                TestCase.problem_id == problem_id,
                TestCase.is_hidden == False,
            )
            .order_by(TestCase.order)
            .all()
        )

        ac_rate = self._ac_rate(problem)

        return ProblemDetail(
            id=str(problem.id),
            title=problem.title,  # type: ignore[arg-type]
            slug=problem.slug,  # type: ignore[arg-type]
            description=problem.description,  # type: ignore[arg-type]
            difficulty=problem.difficulty.value,
            tags=problem.tags or [],  # type: ignore[arg-type]
            time_limit=problem.time_limit,  # type: ignore[arg-type]
            memory_limit=problem.memory_limit,  # type: ignore[arg-type]
            hint=problem.hint,  # type: ignore[arg-type]
            mode=self._mode(problem),
            input_format=problem.input_format,  # type: ignore[arg-type]
            output_format=problem.output_format,  # type: ignore[arg-type]
            function_signature=self._function_signature(problem),
            total_submissions=problem.total_submissions,  # type: ignore[arg-type]
            accepted_submissions=self._accepted_submissions(problem),
            ac_rate=ac_rate,
            sample_testcases=[
                self._sample_testcase_response(problem, tc, index, locale, judge_mode)
                for index, tc in enumerate(sample_testcases)
            ],
            created_at=problem.created_at.isoformat(),
        )

    def get_problem_by_slug(
        self,
        slug: str,
        locale: str = DEFAULT_LOCALE,
        judge_mode: str | None = None,
    ) -> ProblemDetail | None:
        """Get problem detail by slug."""
        problem = self.db.query(Problem).filter(Problem.slug == slug).first()
        if not problem or not problem.is_public:
            return None
        return self.get_problem_by_id(str(problem.id), locale, judge_mode)

    @staticmethod
    def _io_metadata(testcase: TestCase) -> dict[str, Any]:
        raw = getattr(testcase, "io_metadata_json", None)
        if not raw:
            return {}
        try:
            value = json.loads(str(raw))
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    @classmethod
    def testcase_io_view(cls, testcase: TestCase, judge_mode: str | None) -> tuple[str, str, str | None]:
        metadata = cls._io_metadata(testcase)
        problem = getattr(testcase, "problem", None)
        selected_mode = cls._resolve_judge_mode(problem, testcase, judge_mode)
        normalized_mode = selected_mode
        input_value = None
        output_value = None
        if normalized_mode:
            view = metadata.get(normalized_mode)
            if isinstance(view, dict):
                input_value = view.get("input")
                output_value = view.get("output")
            if input_value is not None and output_value is not None:
                return str(input_value), str(output_value), normalized_mode
        return str(testcase.input), str(testcase.output), selected_mode

    def _sample_testcase_response(
        self,
        problem: Problem,
        testcase: TestCase,
        index: int,
        locale: str,
        judge_mode: str | None,
    ) -> SampleTestCase:
        input_value, output_value, display_mode = self.testcase_io_view(testcase, judge_mode)
        metadata = self._io_metadata(testcase)
        acm_view = metadata.get("acm") if isinstance(metadata.get("acm"), dict) else {}
        function_view = metadata.get("function") if isinstance(metadata.get("function"), dict) else {}
        supports_function = bool(self._function_signature(problem))
        selected_function_view = function_view
        if not selected_function_view and supports_function:
            selected_function_view = {"input": str(testcase.input), "output": str(testcase.output)}
        return SampleTestCase(
            input=input_value,
            output=output_value,
            explanation=sample_explanation_for_slug(
                str(problem.slug),
                index,
                input_value,
                output_value,
                locale,
            ),
            acm_input=str(acm_view.get("input")) if acm_view.get("input") is not None else None,
            acm_output=str(acm_view.get("output")) if acm_view.get("output") is not None else None,
            function_input=str(selected_function_view.get("input"))
            if selected_function_view.get("input") is not None
            else None,
            function_output=str(selected_function_view.get("output"))
            if selected_function_view.get("output") is not None
            else None,
            display_mode=display_mode,
        )

    def get_public_testcases(self, problem_id: str) -> list[TestCase]:
        """Get public (non-hidden) testcases for a problem."""
        return (
            self.db.query(TestCase)
            .filter(TestCase.problem_id == problem_id, TestCase.is_hidden == False)
            .order_by(TestCase.order)
            .all()
        )

    def get_all_testcases(self, problem_id: str) -> list[TestCase]:
        """Get all testcases (public + hidden) for a problem."""
        return (
            self.db.query(TestCase)
            .filter(TestCase.problem_id == problem_id)
            .order_by(TestCase.order)
            .all()
        )
