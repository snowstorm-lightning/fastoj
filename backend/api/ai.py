from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.ai.providers import AIProviderUnavailableError
from backend.ai.schemas import AIExplainResponse, AIHintRequest, AIHintResponse, AIReviewResponse
from backend.ai.service import AIService
from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.models import User

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/submissions/{submission_id}/explain", response_model=AIExplainResponse)
def explain_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return AIService(db).explain_submission(submission_id, current_user)
    except AIProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/submissions/{submission_id}/review", response_model=AIReviewResponse)
def review_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return AIService(db).review_submission(submission_id, current_user)
    except AIProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/problems/{problem_id}/hint", response_model=AIHintResponse)
def hint_problem(
    problem_id: str,
    payload: AIHintRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return AIService(db).hint_problem(
            problem_id,
            payload.level,
            payload.language,
            payload.current_code,
        )
    except AIProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
