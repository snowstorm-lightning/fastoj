from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.ai.profiles import ADMIN_ONLY_PROFILE_IDS, list_ai_profiles
from backend.ai.providers import AIProviderUnavailableError
from backend.ai.schemas import (
    AIActionRequest,
    AIChatRequest,
    AIChatResponse,
    AIExplainResponse,
    AIHintRequest,
    AIHintResponse,
    AIProfileResponse,
    AIReviewResponse,
)
from backend.ai.service import AIService
from backend.api.admin import (
    CONTENT_PERMISSION_CREATE_OWN_PROBLEMS,
    ROLE_ADMIN,
    has_content_permission,
)
from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.core.locales import DEFAULT_LOCALE
from backend.models import User

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/profiles", response_model=list[AIProfileResponse])
def profiles(current_user: User = Depends(get_current_user)):
    can_use_admin_profiles = _can_use_admin_model_profile(current_user)
    return list_ai_profiles(include_unavailable=can_use_admin_profiles, include_admin_only=can_use_admin_profiles)


def _requested_model_profile(model_profile: str | None, current_user: User) -> str:
    profile = (model_profile or "default").strip().lower()
    if profile in ADMIN_ONLY_PROFILE_IDS and not _can_use_admin_model_profile(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This AI model profile is admin-only.")
    return profile


def _can_use_admin_model_profile(current_user: User) -> bool:
    return current_user.role == ROLE_ADMIN or has_content_permission(current_user, CONTENT_PERMISSION_CREATE_OWN_PROBLEMS)


@router.post("/submissions/{submission_id}/explain", response_model=AIExplainResponse)
def explain_submission(
    submission_id: str,
    payload: AIActionRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        model_profile = _requested_model_profile(payload.model_profile if payload else "default", current_user)
        locale = payload.locale if payload else DEFAULT_LOCALE
        return AIService(db, model_profile=model_profile).explain_submission(submission_id, current_user, locale)
    except AIProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/submissions/{submission_id}/review", response_model=AIReviewResponse)
def review_submission(
    submission_id: str,
    payload: AIActionRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        model_profile = _requested_model_profile(payload.model_profile if payload else "default", current_user)
        locale = payload.locale if payload else DEFAULT_LOCALE
        return AIService(db, model_profile=model_profile).review_submission(submission_id, current_user, locale)
    except AIProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/submissions/{submission_id}/chat", response_model=AIChatResponse)
def chat_submission(
    submission_id: str,
    payload: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        model_profile = _requested_model_profile(payload.model_profile, current_user)
        return AIService(db, model_profile=model_profile).chat_submission(
            submission_id,
            payload.message,
            current_user,
            payload.locale,
        )
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
        model_profile = _requested_model_profile(payload.model_profile, current_user)
        return AIService(db, model_profile=model_profile).hint_problem(
            problem_id,
            payload.level,
            payload.language,
            payload.current_code,
            payload.locale,
        )
    except AIProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
