
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from backend.models import Problem, TestCase
from backend.schemas.problem import ProblemDetail, ProblemFilter, ProblemListItem, SampleTestCase


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
                    created_at=problem.created_at.isoformat(),
                )
            )

        return result, total

    def get_problem_by_id(self, problem_id: str) -> ProblemDetail | None:
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
            total_submissions=problem.total_submissions,  # type: ignore[arg-type]
            accepted_submissions=self._accepted_submissions(problem),
            ac_rate=ac_rate,
            sample_testcases=[
                SampleTestCase(input=tc.input, output=tc.output) for tc in sample_testcases  # type: ignore[arg-type]
            ],
            created_at=problem.created_at.isoformat(),
        )

    def get_problem_by_slug(self, slug: str) -> ProblemDetail | None:
        """Get problem detail by slug."""
        problem = self.db.query(Problem).filter(Problem.slug == slug).first()
        if not problem or not problem.is_public:
            return None
        return self.get_problem_by_id(str(problem.id))

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
