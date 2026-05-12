
from sqlalchemy.orm import Session

from backend.models import Solution


class SolutionService:
    def __init__(self, db: Session):
        self.db = db

    def get_solutions(
        self, problem_id: str, language: str | None = None
    ) -> list[Solution]:
        """Get solutions for a problem, optionally filtered by language."""
        query = self.db.query(Solution).filter(Solution.problem_id == problem_id)

        if language:
            query = query.filter(Solution.language == language)

        return query.all()

    def get_solution_by_language(
        self, problem_id: str, language: str
    ) -> Solution | None:
        """Get a specific solution by problem and language."""
        return (
            self.db.query(Solution)
            .filter(Solution.problem_id == problem_id, Solution.language == language)
            .first()
        )
