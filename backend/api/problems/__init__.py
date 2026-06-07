import math
import uuid
from collections import Counter, defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.api.admin import CONTENT_PERMISSION_MODERATE_DISCUSSIONS, has_content_permission
from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.core.locales import DEFAULT_LOCALE
from backend.core.security import decode_token
from backend.core.time import utc_now
from backend.models import Problem, ProblemDiscussion, ProblemDiscussionLike, User
from backend.schemas.discussion import ProblemDiscussionCreate, ProblemDiscussionResponse
from backend.schemas.problem import ProblemFilter
from backend.services.problem_service import ProblemService

router = APIRouter(prefix="/problems", tags=["problems"])
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _parse_uuid(value: str, detail: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail) from exc


def _get_optional_current_user(
    token: str | None = Depends(optional_oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if not token:
        return None
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def _can_delete_discussion(current_user: User | None, discussion: ProblemDiscussion) -> bool:
    if current_user is None:
        return False
    if str(discussion.user_id) == str(current_user.id):
        return True
    return has_content_permission(current_user, CONTENT_PERMISSION_MODERATE_DISCUSSIONS)


def _discussion_response(
    discussion: ProblemDiscussion,
    *,
    replies_by_parent: dict[str, list[ProblemDiscussion]] | None = None,
    like_counts: Counter[str] | None = None,
    liked_discussion_ids: set[str] | None = None,
    current_user: User | None = None,
) -> ProblemDiscussionResponse:
    discussion_id = str(discussion.id)
    is_deleted = getattr(discussion, "deleted_at", None) is not None
    replies = replies_by_parent.get(discussion_id, []) if replies_by_parent else []
    return ProblemDiscussionResponse(
        id=discussion_id,
        problem_id=str(discussion.problem_id),
        parent_id=str(discussion.parent_id) if getattr(discussion, "parent_id", None) else None,
        user_id=str(discussion.user_id),
        author=str(discussion.user.username if discussion.user else "FastOJ User"),
        body="" if is_deleted else str(discussion.body),
        deleted=is_deleted,
        is_deleted=is_deleted,
        is_template=False,
        deleted_at=discussion.deleted_at.isoformat() if getattr(discussion, "deleted_at", None) else None,
        deleted_by=str(discussion.deleted_by) if getattr(discussion, "deleted_by", None) else None,
        like_count=(like_counts or Counter()).get(discussion_id, 0),
        liked_by_me=discussion_id in (liked_discussion_ids or set()),
        can_delete=(not is_deleted and _can_delete_discussion(current_user, discussion)),
        reply_count=len(replies),
        created_at=discussion.created_at.isoformat(),
        updated_at=discussion.updated_at.isoformat() if discussion.updated_at else None,
        replies=[
            _discussion_response(
                reply,
                replies_by_parent=replies_by_parent,
                like_counts=like_counts,
                liked_discussion_ids=liked_discussion_ids,
                current_user=current_user,
            )
            for reply in sorted(replies, key=lambda item: item.created_at or utc_now())
        ],
    )


def _problem_for_discussions(problem_id: str, db: Session, current_user: User | None = None) -> Problem:
    problem_uuid = _parse_uuid(problem_id, "Invalid problem id")
    problem = db.query(Problem).filter(Problem.id == problem_uuid).first()
    if not problem or (not problem.is_public and not has_content_permission(current_user, CONTENT_PERMISSION_MODERATE_DISCUSSIONS)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    return problem


def _discussion_for_problem(problem: Problem, discussion_id: str, db: Session) -> ProblemDiscussion:
    discussion_uuid = _parse_uuid(discussion_id, "Invalid discussion id")
    discussion = (
        db.query(ProblemDiscussion)
        .filter(ProblemDiscussion.id == discussion_uuid, ProblemDiscussion.problem_id == problem.id)
        .first()
    )
    if not discussion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discussion not found")
    return discussion


def _load_discussion_likes(
    db: Session,
    discussion_ids: list[uuid.UUID],
) -> tuple[Counter[str], dict[tuple[str, str], ProblemDiscussionLike]]:
    if not discussion_ids:
        return Counter(), {}
    likes = db.query(ProblemDiscussionLike).filter(ProblemDiscussionLike.discussion_id.in_(discussion_ids)).all()
    like_counts: Counter[str] = Counter(str(like.discussion_id) for like in likes)
    likes_by_user_discussion = {(str(like.user_id), str(like.discussion_id)): like for like in likes}
    return like_counts, likes_by_user_discussion


def _discussion_like_count(db: Session, discussion_id: uuid.UUID) -> int:
    return len(db.query(ProblemDiscussionLike).filter(ProblemDiscussionLike.discussion_id == discussion_id).all())


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
async def get_problem(
    problem_id: str,
    locale: str = DEFAULT_LOCALE,
    judge_mode: str | None = Query(None, pattern="^(acm|function)$"),
    db: Session = Depends(get_db),
):
    """Get problem detail by ID."""
    service = ProblemService(db)
    problem = service.get_problem_by_id(problem_id, locale, judge_mode)

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
    current_user: User | None = Depends(_get_optional_current_user),
):
    """Get discussion posts for a public problem as a nested tree."""
    problem = _problem_for_discussions(problem_id, db, current_user)

    discussions = (
        db.query(ProblemDiscussion)
        .filter(ProblemDiscussion.problem_id == problem.id)
        .order_by(ProblemDiscussion.created_at.desc())
        .all()
    )
    discussion_ids = [discussion.id for discussion in discussions]
    like_counts, likes_by_user_discussion = _load_discussion_likes(db, discussion_ids)
    current_user_id = str(current_user.id) if current_user else None
    liked_discussion_ids = {
        discussion_id
        for (user_id, discussion_id), _like in likes_by_user_discussion.items()
        if current_user_id is not None and user_id == current_user_id
    }
    replies_by_parent: dict[str, list[ProblemDiscussion]] = defaultdict(list)
    roots: list[ProblemDiscussion] = []
    discussion_id_set = {str(discussion.id) for discussion in discussions}
    for discussion in discussions:
        parent_id = str(discussion.parent_id) if getattr(discussion, "parent_id", None) else None
        if parent_id and parent_id in discussion_id_set:
            replies_by_parent[parent_id].append(discussion)
        else:
            roots.append(discussion)
    roots = sorted(roots, key=lambda item: item.created_at or utc_now(), reverse=True)[:limit]
    return {
        "success": True,
        "data": [
            _discussion_response(
                discussion,
                replies_by_parent=replies_by_parent,
                like_counts=like_counts,
                liked_discussion_ids=liked_discussion_ids,
                current_user=current_user,
            ).model_dump()
            for discussion in roots
        ],
    }


@router.post("/{problem_id}/discussions", status_code=status.HTTP_201_CREATED)
def create_problem_discussion(
    problem_id: str,
    payload: ProblemDiscussionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a discussion post for a public problem."""
    problem = _problem_for_discussions(problem_id, db, current_user)

    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Discussion body is required")

    parent_id = None
    if payload.parent_id:
        parent = _discussion_for_problem(problem, payload.parent_id, db)
        if getattr(parent, "deleted_at", None) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot reply to a deleted discussion")
        parent_id = parent.id

    now = utc_now()
    discussion = ProblemDiscussion(
        id=uuid.uuid4(),
        problem_id=problem.id,
        parent_id=parent_id,
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
        "data": _discussion_response(discussion, current_user=current_user).model_dump(),
    }


@router.delete("/{problem_id}/discussions/{discussion_id}")
def delete_problem_discussion(
    problem_id: str,
    discussion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a discussion post owned by the user or a moderator."""
    problem = _problem_for_discussions(problem_id, db, current_user)
    discussion = _discussion_for_problem(problem, discussion_id, db)
    if not _can_delete_discussion(current_user, discussion):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete this discussion")
    if getattr(discussion, "deleted_at", None) is None:
        now = utc_now()
        discussion.deleted_at = now
        discussion.deleted_by = current_user.id
        discussion.updated_at = now
        db.commit()
        db.refresh(discussion)
    return {"success": True, "data": _discussion_response(discussion, current_user=current_user).model_dump()}


@router.post("/{problem_id}/discussions/{discussion_id}/like")
def like_problem_discussion(
    problem_id: str,
    discussion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Like a discussion post. Repeating the request is idempotent."""
    problem = _problem_for_discussions(problem_id, db, current_user)
    discussion = _discussion_for_problem(problem, discussion_id, db)
    if getattr(discussion, "deleted_at", None) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot like a deleted discussion")
    existing = (
        db.query(ProblemDiscussionLike)
        .filter(ProblemDiscussionLike.discussion_id == discussion.id, ProblemDiscussionLike.user_id == current_user.id)
        .first()
    )
    if not existing:
        db.add(
            ProblemDiscussionLike(
                id=uuid.uuid4(),
                discussion_id=discussion.id,
                user_id=current_user.id,
                created_at=utc_now(),
            )
        )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    return {
        "success": True,
        "data": {"liked": True, "like_count": _discussion_like_count(db, discussion.id)},
    }


@router.delete("/{problem_id}/discussions/{discussion_id}/like")
def unlike_problem_discussion(
    problem_id: str,
    discussion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a discussion like. Repeating the request is idempotent."""
    problem = _problem_for_discussions(problem_id, db, current_user)
    discussion = _discussion_for_problem(problem, discussion_id, db)
    existing = (
        db.query(ProblemDiscussionLike)
        .filter(ProblemDiscussionLike.discussion_id == discussion.id, ProblemDiscussionLike.user_id == current_user.id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
    return {
        "success": True,
        "data": {"liked": False, "like_count": _discussion_like_count(db, discussion.id)},
    }
