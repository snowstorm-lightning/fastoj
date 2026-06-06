import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.core.time import utc_now
from backend.models import Problem, ProblemDiscussion, User
from backend.schemas.discussion import ProblemDiscussionCreate, ProblemDiscussionResponse
from backend.schemas.problem import ProblemFilter
from backend.services.problem_service import ProblemService

router = APIRouter(prefix="/problems", tags=["problems"])


def _discussion_response(discussion: ProblemDiscussion) -> ProblemDiscussionResponse:
    return ProblemDiscussionResponse(
        id=str(discussion.id),
        problem_id=str(discussion.problem_id),
        user_id=str(discussion.user_id),
        author=str(discussion.user.username if discussion.user else "FastOJ User"),
        body=str(discussion.body),
        created_at=discussion.created_at.isoformat(),
        updated_at=discussion.updated_at.isoformat() if discussion.updated_at else None,
    )


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


@router.get("/{problem_id}/discussions")
def get_problem_discussions(
    problem_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get recent discussion posts for a public problem."""
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem or not problem.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    discussions = (
        db.query(ProblemDiscussion)
        .filter(ProblemDiscussion.problem_id == problem_id)
        .order_by(ProblemDiscussion.created_at.desc())
        .all()
    )[:limit]
    return {
        "success": True,
        "data": [_discussion_response(discussion).model_dump() for discussion in discussions],
    }


@router.post("/{problem_id}/discussions", status_code=status.HTTP_201_CREATED)
def create_problem_discussion(
    problem_id: str,
    payload: ProblemDiscussionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a discussion post for a public problem."""
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem or (not problem.is_public and current_user.role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Discussion body is required")

    now = utc_now()
    discussion = ProblemDiscussion(
        id=uuid.uuid4(),
        problem_id=problem.id,
        user_id=current_user.id,
        user=current_user,
        body=body,
        created_at=now,
        updated_at=now,
    )
    db.add(discussion)
    db.commit()
    db.refresh(discussion)
    return {
        "success": True,
        "data": _discussion_response(discussion).model_dump(),
    }
