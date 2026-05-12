import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.problem import (
    PaginationInfo,
    ProblemDetail,
    ProblemFilter,
    ProblemListItem,
)
from backend.services.problem_service import ProblemService

router = APIRouter(prefix="/problems", tags=["problems"])


@router.get("")
async def get_problems(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    difficulty: str | None = None,
    tags: str | None = None,
    keyword: str | None = None,
    sort: str = Query("created_at", regex="^(created_at|ac_rate|difficulty)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """Get paginated problem list with filters."""
    filters = ProblemFilter(
        page=page,
        page_size=page_size,
        difficulty=difficulty,
        tags=tags,
        keyword=keyword,
        sort=sort,
        order=order,
    )

    service = ProblemService(db)
    problems, total = service.get_problems(filters)

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return {
        "success": True,
        "data": [p.model_dump() for p in problems],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }


@router.get("/{problem_id}")
async def get_problem(problem_id: str, db: Session = Depends(get_db)):
    """Get problem detail by ID."""
    service = ProblemService(db)
    problem = service.get_problem_by_id(problem_id)

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )

    return {
        "success": True,
        "data": problem.model_dump(),
    }
