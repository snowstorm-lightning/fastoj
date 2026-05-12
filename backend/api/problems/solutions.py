
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.services.problem_service import ProblemService
from backend.services.solution_service import SolutionService

router = APIRouter(prefix="/problems/{problem_id}/solutions", tags=["solutions"])


@router.get("")
async def get_problem_solutions(
    problem_id: str,
    language: str | None = None,
    db: Session = Depends(get_db),
):
    """Get solutions for a problem."""
    # Verify problem exists
    problem_service = ProblemService(db)
    problem = problem_service.get_problem_by_id(problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )

    solution_service = SolutionService(db)
    solutions = solution_service.get_solutions(problem_id, language)

    return {
        "success": True,
        "data": [
            {
                "id": str(s.id),
                "language": s.language,
                "code": s.code,
                "explanation": s.explanation,
                "time_complexity": s.time_complexity,
                "space_complexity": s.space_complexity,
            }
            for s in solutions
        ],
    }
