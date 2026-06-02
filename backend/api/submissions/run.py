from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.models import User
from backend.schemas.submission import SubmissionCreate, SubmissionResponse
from backend.services.submission_service import JudgeServiceUnavailableError, SubmissionService

router = APIRouter(prefix="/submissions/run", tags=["run"])


@router.post("", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def run_code(
    submission_data: SubmissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run code with public testcases only (no hidden testcases)."""
    service = SubmissionService(db)
    try:
        ip_address = request.client.host if request.client else None
        submission = service.create_run(
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
    except JudgeServiceUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except ValueError as e:
        if "Unsupported language" in str(e) or "Function mode" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
