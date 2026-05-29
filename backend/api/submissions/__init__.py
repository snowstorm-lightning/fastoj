import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.models import User
from backend.schemas.submission import (
    SubmissionCreate,
    SubmissionDetail,
    SubmissionListItem,
    SubmissionResponse,
)
from backend.services.submission_service import SubmissionService

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission(
    submission_data: SubmissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new submission (full judging with all testcases)."""
    service = SubmissionService(db)
    try:
        ip_address = request.client.host if request.client else None
        submission = service.create_submission(
            submission_data,
            str(current_user.id),
            ip_address,
            is_admin=current_user.role == "admin",
        )

        return SubmissionResponse(
            id=str(submission.id),
            problem_id=str(submission.problem_id),
            user_id=str(submission.user_id),
            code=submission.code,  # type: ignore[arg-type]
            language=submission.language,  # type: ignore[arg-type]
            status=submission.status.value,
            result=submission.result.value if submission.result else None,
            error_message=submission.error_message,  # type: ignore[arg-type]
            execute_time=submission.execute_time,  # type: ignore[arg-type]
            memory_used=submission.memory_used,  # type: ignore[arg-type]
            score=submission.score,  # type: ignore[arg-type]
            created_at=submission.created_at.isoformat(),
            finished_at=submission.finished_at.isoformat() if submission.finished_at else None,
        )
    except ValueError as e:
        if "Unsupported language" in str(e) or "Function mode" in str(e) or "Custom run" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{submission_id}", response_model=SubmissionDetail)
async def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get submission detail."""
    service = SubmissionService(db)
    submission = service.get_submission(
        submission_id,
        str(current_user.id),
        is_admin=current_user.role == "admin",
    )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    # Filter hidden testcase results for non-owner
    filtered_results = [
        r for r in submission.testcase_results if not r.is_hidden
    ]
    submission.testcase_results = filtered_results

    return submission


@router.get("")
async def get_user_submissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    problem_id: str | None = None,
    language: str | None = None,
    result: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's submissions."""
    service = SubmissionService(db)
    submissions, total = service.get_user_submissions(
        str(current_user.id),
        page,
        page_size,
        problem_id,
        language,
        result,
        status,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return {
        "success": True,
        "data": [s.model_dump() for s in submissions],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }
