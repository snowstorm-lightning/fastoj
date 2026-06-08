import uuid
from collections.abc import Iterable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.ai.providers import AIProviderUnavailableError
from backend.ai.schemas import AILocale, AIModelProfile
from backend.api.auth import get_current_user
from backend.core.code_normalization import normalize_source_code
from backend.core.database import get_db
from backend.core.languages import Language
from backend.core.locales import DEFAULT_LOCALE, ai_response_language
from backend.core.security import get_password_hash
from backend.models import (
    Difficulty,
    Problem,
    ProblemDiscussion,
    ProblemDiscussionLike,
    ProblemDraft,
    Solution,
    Submission,
    TestCase,
    TestCaseResult,
    User,
)
from backend.schemas.problem_authoring import (
    AuthoredOfficialSolution,
    AuthoredProblemDraft,
    AuthoredTestCase,
)
from backend.services.problem_authoring_agent import (
    ProblemAuthoringAgentService,
    ProblemDraftValidationAdapter,
    dump_json,
    load_json,
    normalize_slug,
)

router = APIRouter(prefix="/admin", tags=["admin"])

ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_CONTENT_ADMIN = "content_admin"
VALID_USER_ROLES = {ROLE_USER, ROLE_ADMIN, ROLE_CONTENT_ADMIN}

CONTENT_PERMISSION_CREATE_OWN_PROBLEMS = "problem:create_own"
CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS = "problem:update_own"
CONTENT_PERMISSION_PUBLISH_OWN_PROBLEMS = "problem:publish_own"
CONTENT_PERMISSION_MANAGE_USERS = "user:manage"
CONTENT_PERMISSION_MODERATE_DISCUSSIONS = "discussion:moderate"
VALID_CONTENT_ADMIN_PERMISSIONS = {
    CONTENT_PERMISSION_CREATE_OWN_PROBLEMS,
    CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS,
    CONTENT_PERMISSION_PUBLISH_OWN_PROBLEMS,
    CONTENT_PERMISSION_MANAGE_USERS,
    CONTENT_PERMISSION_MODERATE_DISCUSSIONS,
}


class AdminUserUpdate(BaseModel):
    role: str | None = None
    content_admin_permissions: list[str] | None = Field(default=None, max_length=len(VALID_CONTENT_ADMIN_PERMISSIONS))
    is_active: bool | None = None

    @field_validator("content_admin_permissions")
    @classmethod
    def validate_content_admin_permissions(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        permissions = _normalize_content_admin_permissions(value)
        invalid = sorted(set(permissions) - VALID_CONTENT_ADMIN_PERMISSIONS)
        if invalid:
            raise ValueError(f"Invalid content admin permissions: {', '.join(invalid)}")
        return permissions


class AdminPasswordReset(BaseModel):
    new_password: str = Field(min_length=8)


class AdminProblemUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    hint: str | None = None
    difficulty: str | None = None
    tags: list[str] | None = None
    is_public: bool | None = None
    mode: str | None = None
    input_format: str | None = None
    output_format: str | None = None
    function_signature: str | None = None
    time_limit: int | None = Field(default=None, ge=100, le=10000)
    memory_limit: int | None = Field(default=None, ge=16, le=2048)


class AdminSolutionUpsert(BaseModel):
    language: str
    code: str
    explanation: str
    time_complexity: str | None = None
    space_complexity: str | None = None

    @field_validator("code")
    @classmethod
    def clean_code(cls, value: str) -> str:
        return normalize_source_code(value)


class AdminSolutionGenerateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    language: str
    locale: AILocale = DEFAULT_LOCALE
    model_profile: AIModelProfile = "default"
    problem: AdminProblemUpdate | None = None
    solutions: list[AdminSolutionUpsert] | None = Field(default=None, max_length=7)


class AdminTestCaseUpdate(BaseModel):
    input: str | None = None
    output: str | None = None
    io_metadata: dict[str, Any] | None = None
    is_hidden: bool | None = None
    is_sample: bool | None = None
    score: int | None = Field(default=None, ge=0)
    order: int | None = Field(default=None, ge=0)


class AdminTestCaseCreate(BaseModel):
    input: str
    output: str
    io_metadata: dict[str, Any] | None = None
    is_hidden: bool = False
    is_sample: bool = False
    score: int = Field(default=10, ge=0)
    order: int | None = Field(default=None, ge=0)


def _normalize_content_admin_permissions(permissions: Iterable[str] | None) -> list[str]:
    if not permissions:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for permission in permissions:
        value = str(permission).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized


def content_admin_permissions(user: User | None) -> list[str]:
    return _normalize_content_admin_permissions(getattr(user, "content_admin_permissions", None))


def has_content_permission(user: User | None, permission: str) -> bool:
    if user is None:
        return False
    if user.role == ROLE_ADMIN:
        return True
    if user.role != ROLE_CONTENT_ADMIN:
        return False
    return permission in content_admin_permissions(user)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user


def require_content_permission(permission: str):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not has_content_permission(current_user, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient content permission")
        return current_user

    return dependency


def require_admin_dashboard_access(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role == ROLE_ADMIN:
        return current_user
    if current_user.role == ROLE_CONTENT_ADMIN and content_admin_permissions(current_user):
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")


def _ensure_own_problem_or_admin(problem: Problem, current_user: User) -> None:
    if current_user.role == ROLE_ADMIN:
        return
    if str(problem.created_by) == str(current_user.id):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only manage your own problems")


def _ensure_own_draft_or_admin(draft: ProblemDraft, current_user: User) -> None:
    if current_user.role == ROLE_ADMIN:
        return
    if str(draft.created_by) == str(current_user.id):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only manage your own drafts")


def _nullable_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _ensure_problem_slug_available(db: Session, slug: str, problem_id: str) -> None:
    existing = db.query(Problem).filter(Problem.slug == slug, Problem.id != problem_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Slug already exists: {slug}")


def _normalize_case_flags(is_hidden: bool, is_sample: bool) -> tuple[bool, bool]:
    if is_hidden:
        return True, False
    if is_sample:
        return False, True
    return False, False


def _user_token_version(user: User) -> int:
    return int(getattr(user, "token_version", 0) or 0)


def _active_admin_count(db: Session) -> int:
    return (
        db.query(User)
        .filter(User.role == ROLE_ADMIN, User.is_active.is_(True))
        .count()
    )


def _ensure_safe_user_update(db: Session, user: User, payload: AdminUserUpdate, current_user: User) -> None:
    next_role = str(payload.role if payload.role is not None else (user.role or ROLE_USER))
    next_active = bool(payload.is_active if payload.is_active is not None else user.is_active)
    current_role = str(user.role or ROLE_USER)
    currently_active = bool(user.is_active)

    if current_user.role != ROLE_ADMIN:
        if current_role != ROLE_USER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can manage elevated accounts")
        if payload.role is not None or payload.content_admin_permissions is not None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can change roles or permissions")

    if str(user.id) == str(current_user.id):
        if payload.is_active is False or (payload.role is not None and next_role != ROLE_ADMIN):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot disable or downgrade your own admin account")

    removes_active_admin = currently_active and current_role == ROLE_ADMIN and (next_role != ROLE_ADMIN or not next_active)
    if removes_active_admin and _active_admin_count(db) <= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the last active admin")


@router.get("/overview")
def overview(
    user_query: str | None = Query(None, max_length=100),
    user_role: str | None = Query(None, pattern="^(user|admin|content_admin)$"),
    user_status: str | None = Query(None, pattern="^(active|disabled)$"),
    user_page: int = Query(1, ge=1),
    user_page_size: int = Query(10, ge=1, le=50),
    problem_query: str | None = Query(None, max_length=100),
    problem_difficulty: str | None = Query(None, pattern="^(easy|medium|hard)$"),
    problem_visibility: str | None = Query(None, pattern="^(public|private)$"),
    problem_page: int = Query(1, ge=1),
    problem_page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_dashboard_access),
):
    user_base_query = db.query(User)
    if current_user.role != ROLE_ADMIN and not has_content_permission(current_user, CONTENT_PERMISSION_MANAGE_USERS):
        user_base_query = user_base_query.filter(User.id == current_user.id)
    if user_query and user_query.strip():
        pattern = f"%{user_query.strip()}%"
        user_base_query = user_base_query.filter(or_(User.username.ilike(pattern), User.email.ilike(pattern)))
    if user_role:
        user_base_query = user_base_query.filter(User.role == user_role)
    if user_status:
        user_base_query = user_base_query.filter(User.is_active.is_(user_status == "active"))

    problem_base_query = db.query(Problem)
    if current_user.role != ROLE_ADMIN:
        problem_base_query = problem_base_query.filter(Problem.created_by == current_user.id)
    if problem_query and problem_query.strip():
        pattern = f"%{problem_query.strip()}%"
        problem_base_query = problem_base_query.filter(or_(Problem.title.ilike(pattern), Problem.slug.ilike(pattern)))
    if problem_difficulty:
        problem_base_query = problem_base_query.filter(Problem.difficulty == Difficulty(problem_difficulty))
    if problem_visibility:
        problem_base_query = problem_base_query.filter(Problem.is_public.is_(problem_visibility == "public"))

    users_total = user_base_query.count()
    problems_total = problem_base_query.count()
    users = (
        user_base_query.order_by(User.created_at.desc())
        .offset((user_page - 1) * user_page_size)
        .limit(user_page_size)
        .all()
    )
    problems = (
        problem_base_query.order_by(Problem.created_at.desc())
        .offset((problem_page - 1) * problem_page_size)
        .limit(problem_page_size)
        .all()
    )
    return {
        "success": True,
        "data": {
            "users": [
                {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "content_admin_permissions": content_admin_permissions(user),
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                }
                for user in users
            ],
            "problems": [
                {
                    "id": str(problem.id),
                    "title": problem.title,
                    "slug": problem.slug,
                    "description": problem.description,
                    "difficulty": problem.difficulty.value,
                    "tags": problem.tags or [],
                    "is_public": problem.is_public,
                    "mode": problem.mode,
                    "input_format": problem.input_format,
                    "output_format": problem.output_format,
                    "function_signature": problem.function_signature,
                    "hint": problem.hint,
                    "time_limit": problem.time_limit,
                    "memory_limit": problem.memory_limit,
                    "testcase_count": len(problem.testcases),
                    "hidden_testcase_count": sum(1 for testcase in problem.testcases if testcase.is_hidden),
                    "solution_count": len(problem.solutions),
                    "total_submissions": problem.total_submissions,
                    "created_at": problem.created_at.isoformat(),
                    "updated_at": problem.updated_at.isoformat() if problem.updated_at else None,
                }
                for problem in problems
            ],
            "pagination": {
                "users": {
                    "page": user_page,
                    "page_size": user_page_size,
                    "total": users_total,
                    "total_pages": (users_total + user_page_size - 1) // user_page_size,
                },
                "problems": {
                    "page": problem_page,
                    "page_size": problem_page_size,
                    "total": problems_total,
                    "total_pages": (problems_total + problem_page_size - 1) // problem_page_size,
                },
            },
        },
    }


@router.patch("/users/{user_id}")
def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_MANAGE_USERS)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if current_user.role != ROLE_ADMIN and (payload.role is not None or payload.content_admin_permissions is not None):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can change roles and permissions")
    next_role = str(payload.role if payload.role is not None else (user.role or ROLE_USER))
    if next_role not in VALID_USER_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    if payload.content_admin_permissions is not None and next_role != ROLE_CONTENT_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content admin permissions require content_admin role",
        )
    _ensure_safe_user_update(db, user, payload, current_user)
    if payload.role is not None:
        user.role = payload.role
        if payload.role != ROLE_CONTENT_ADMIN:
            user.content_admin_permissions = []
    if payload.content_admin_permissions is not None:
        user.content_admin_permissions = payload.content_admin_permissions
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    return {"success": True}


@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: str,
    payload: AdminPasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    require_admin(current_user)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if str(user.id) == str(current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use account settings to change your own password")
    user.password_hash = get_password_hash(payload.new_password)
    user.token_version = _user_token_version(user) + 1
    db.commit()
    return {"success": True}


@router.patch("/problems/{problem_id}")
def update_problem(
    problem_id: str,
    payload: AdminProblemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    _ensure_own_problem_or_admin(problem, current_user)
    if payload.difficulty is not None:
        try:
            problem.difficulty = Difficulty(payload.difficulty)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid difficulty") from exc
    if payload.slug is not None:
        requested_slug = str(payload.slug or "").strip()
        slug = normalize_slug(requested_slug or str(payload.title or problem.title))
        _ensure_problem_slug_available(db, slug, problem_id)
        problem.slug = slug
    if payload.mode is not None:
        if payload.mode not in {"function", "acm", "both"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mode")
        problem.mode = payload.mode

    for field in ["title", "description", "hint", "tags", "is_public"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(problem, field, value)
    for field in ["input_format", "output_format", "function_signature"]:
        if field in payload.model_fields_set:
            setattr(problem, field, _nullable_text(getattr(payload, field)))
    if payload.time_limit is not None:
        problem.time_limit = payload.time_limit
    if payload.memory_limit is not None:
        problem.memory_limit = payload.memory_limit
    db.commit()
    return {"success": True}


@router.delete("/problems/{problem_id}")
def delete_problem(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    _ensure_own_problem_or_admin(problem, current_user)

    testcases = db.query(TestCase).filter(TestCase.problem_id == problem.id).all()
    submissions = db.query(Submission).filter(Submission.problem_id == problem.id).all()
    solutions = db.query(Solution).filter(Solution.problem_id == problem.id).all()
    discussions = db.query(ProblemDiscussion).filter(ProblemDiscussion.problem_id == problem.id).all()
    discussion_ids = [discussion.id for discussion in discussions]
    discussion_likes = (
        db.query(ProblemDiscussionLike)
        .filter(ProblemDiscussionLike.discussion_id.in_(discussion_ids))
        .all()
        if discussion_ids
        else []
    )
    linked_drafts = db.query(ProblemDraft).filter(ProblemDraft.approved_problem_id == problem.id).all()

    testcase_results: list[TestCaseResult] = []
    seen_result_ids: set[str] = set()

    def collect_results(results: list[TestCaseResult]) -> None:
        for result in results:
            result_id = str(result.id)
            if result_id in seen_result_ids:
                continue
            seen_result_ids.add(result_id)
            testcase_results.append(result)

    for submission in submissions:
        collect_results(db.query(TestCaseResult).filter(TestCaseResult.submission_id == submission.id).all())
    for testcase in testcases:
        collect_results(db.query(TestCaseResult).filter(TestCaseResult.testcase_id == testcase.id).all())

    for draft in linked_drafts:
        draft.approved_problem_id = None
    for result in testcase_results:
        db.delete(result)
    for submission in submissions:
        db.delete(submission)
    for solution in solutions:
        db.delete(solution)
    for like in discussion_likes:
        db.delete(like)

    discussions_by_id = {str(discussion.id): discussion for discussion in discussions}

    def discussion_depth(discussion: ProblemDiscussion) -> int:
        depth = 0
        parent_id = getattr(discussion, "parent_id", None)
        seen: set[str] = set()
        while parent_id is not None and str(parent_id) in discussions_by_id and str(parent_id) not in seen:
            seen.add(str(parent_id))
            depth += 1
            parent_id = getattr(discussions_by_id[str(parent_id)], "parent_id", None)
        return depth

    for discussion in sorted(discussions, key=discussion_depth, reverse=True):
        db.delete(discussion)
    for testcase in testcases:
        db.delete(testcase)
    db.delete(problem)
    db.commit()
    return {
        "success": True,
        "deleted": {
            "problems": 1,
            "testcases": len(testcases),
            "submissions": len(submissions),
            "testcase_results": len(testcase_results),
            "solutions": len(solutions),
            "discussions": len(discussions),
            "discussion_likes": len(discussion_likes),
            "draft_links_cleared": len(linked_drafts),
        },
    }


@router.get("/problems/{problem_id}/solutions")
def list_solutions(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    _ensure_own_problem_or_admin(problem, current_user)
    solutions = (
        db.query(Solution)
        .filter(Solution.problem_id == problem.id)
        .order_by(Solution.language.asc())
        .all()
    )
    return {"success": True, "data": [_solution_response(solution) for solution in solutions]}


@router.put("/problems/{problem_id}/solutions")
def upsert_solution(
    problem_id: str,
    payload: AdminSolutionUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    _ensure_own_problem_or_admin(problem, current_user)
    language = payload.language.strip().lower()
    if not Language.is_supported(language):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported language: {language}")
    solution = db.query(Solution).filter(Solution.problem_id == problem.id, Solution.language == language).first()
    if not solution:
        solution = Solution(problem_id=problem.id, language=language, created_by=current_user.id)
        db.add(solution)
    solution.code = payload.code
    solution.explanation = payload.explanation
    solution.time_complexity = payload.time_complexity
    solution.space_complexity = payload.space_complexity
    solution.is_official = True
    db.commit()
    db.refresh(solution)
    return {"success": True, "data": _solution_response(solution)}


@router.post("/problems/{problem_id}/solutions/generate", response_model=AuthoredOfficialSolution)
def generate_solution(
    problem_id: str,
    payload: AdminSolutionGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    _ensure_own_problem_or_admin(problem, current_user)
    language = payload.language.strip().lower()
    if not Language.is_supported(language):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported language: {language}")
    context = _solution_generation_context(problem, payload)
    try:
        return ProblemAuthoringAgentService(db).generate_solution_from_context(
            context,
            language,
            payload.model_profile,
        )
    except AIProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/problems/{problem_id}/solutions/{language}")
def delete_solution(
    problem_id: str,
    language: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    _ensure_own_problem_or_admin(problem, current_user)
    normalized_language = language.strip().lower()
    solution = (
        db.query(Solution)
        .filter(Solution.problem_id == problem.id, Solution.language == normalized_language)
        .first()
    )
    if not solution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solution not found")
    db.delete(solution)
    db.commit()
    return {"success": True}


@router.post("/problems/{problem_id}/revalidate")
def revalidate_problem(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    _ensure_own_problem_or_admin(problem, current_user)
    report = _validate_problem(problem)
    return {"success": True, "data": report}


@router.get("/problems/{problem_id}/testcases")
def list_testcases(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    _ensure_own_problem_or_admin(problem, current_user)
    testcases = (
        db.query(TestCase)
        .filter(TestCase.problem_id == problem.id)
        .order_by(TestCase.order.asc(), TestCase.created_at.asc())
        .all()
    )
    return {"success": True, "data": [_testcase_response(testcase) for testcase in testcases]}


@router.post("/problems/{problem_id}/testcases", status_code=status.HTTP_201_CREATED)
def create_testcase(
    problem_id: str,
    payload: AdminTestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    _ensure_own_problem_or_admin(problem, current_user)
    order = payload.order
    if order is None:
        latest = (
            db.query(TestCase)
            .filter(TestCase.problem_id == problem.id)
            .order_by(TestCase.order.desc())
            .first()
        )
        order = int(latest.order) + 1 if latest else 1
    is_hidden, is_sample = _normalize_case_flags(payload.is_hidden, payload.is_sample)
    testcase = TestCase(
        id=uuid.uuid4(),
        problem_id=problem.id,
        input=payload.input,
        output=payload.output,
        io_metadata_json=dump_json(payload.io_metadata) if payload.io_metadata else None,
        is_hidden=is_hidden,
        is_sample=is_sample,
        score=payload.score,
        order=order,
    )
    db.add(testcase)
    db.commit()
    db.refresh(testcase)
    return {"success": True, "data": _testcase_response(testcase)}


@router.patch("/testcases/{testcase_id}")
def update_testcase(
    testcase_id: str,
    payload: AdminTestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    testcase = db.query(TestCase).filter(TestCase.id == testcase_id).first()
    if not testcase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Testcase not found")
    if testcase.problem:
        _ensure_own_problem_or_admin(testcase.problem, current_user)
    for field in ["input", "output", "is_hidden", "is_sample", "score", "order"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(testcase, field, value)
    if payload.io_metadata is not None:
        testcase.io_metadata_json = dump_json(payload.io_metadata) if payload.io_metadata else None
    if payload.is_hidden is True:
        testcase.is_hidden, testcase.is_sample = True, False
    elif payload.is_sample is True:
        testcase.is_hidden, testcase.is_sample = False, True
    else:
        testcase.is_hidden, testcase.is_sample = _normalize_case_flags(bool(testcase.is_hidden), bool(testcase.is_sample))
    db.commit()
    db.refresh(testcase)
    return {"success": True, "data": _testcase_response(testcase)}


@router.delete("/testcases/{testcase_id}")
def delete_testcase(
    testcase_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    testcase = db.query(TestCase).filter(TestCase.id == testcase_id).first()
    if not testcase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Testcase not found")
    if testcase.problem:
        _ensure_own_problem_or_admin(testcase.problem, current_user)
    db.delete(testcase)
    db.commit()
    return {"success": True}


def _testcase_response(testcase: TestCase) -> dict:
    return {
        "id": str(testcase.id),
        "problem_id": str(testcase.problem_id),
        "input": testcase.input,
        "output": testcase.output,
        "io_metadata": load_json(getattr(testcase, "io_metadata_json", None), None),
        "is_hidden": testcase.is_hidden,
        "is_sample": testcase.is_sample,
        "score": testcase.score,
        "order": testcase.order,
        "created_at": testcase.created_at.isoformat() if testcase.created_at else None,
    }


def _solution_response(solution: Solution) -> dict:
    return {
        "id": str(solution.id),
        "problem_id": str(solution.problem_id),
        "language": solution.language,
        "code": solution.code,
        "explanation": solution.explanation,
        "time_complexity": solution.time_complexity,
        "space_complexity": solution.space_complexity,
        "is_official": solution.is_official,
        "created_at": solution.created_at.isoformat() if solution.created_at else None,
        "updated_at": solution.updated_at.isoformat() if solution.updated_at else None,
    }


def _solution_generation_context(problem: Problem, payload: AdminSolutionGenerateRequest) -> dict[str, Any]:
    problem_patch = payload.problem or AdminProblemUpdate()

    def patched(field: str, current: Any) -> Any:
        if field in problem_patch.model_fields_set:
            return getattr(problem_patch, field)
        return current

    ordered_testcases = sorted(
        problem.testcases or [],
        key=lambda item: (
            int(item.order or 0),
            item.created_at.isoformat() if item.created_at else "",
        ),
    )
    hidden_values = [
        str(value)
        for testcase in ordered_testcases
        if testcase.is_hidden
        for value in (testcase.input, testcase.output)
        if value is not None and len(str(value).strip()) >= 8
    ]

    def redact(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value)
        for secret in hidden_values:
            text = text.replace(secret, "[hidden]")
        return _truncate_prompt_value(text)

    if payload.solutions is not None:
        solutions = payload.solutions
    else:
        solutions = [
            AdminSolutionUpsert(
                language=str(solution.language),
                code=str(solution.code),
                explanation=str(solution.explanation),
                time_complexity=solution.time_complexity,
                space_complexity=solution.space_complexity,
            )
            for solution in (problem.solutions or [])
            if solution.is_official
        ]

    return {
        "target_language": payload.language.strip().lower(),
        "response_language": ai_response_language(payload.locale),
        "title": redact(patched("title", problem.title)),
        "slug": redact(patched("slug", problem.slug)),
        "description": redact(patched("description", problem.description)),
        "difficulty": patched("difficulty", problem.difficulty.value),
        "tags": patched("tags", list(problem.tags or [])),
        "mode": patched("mode", problem.mode),
        "input_format": redact(patched("input_format", problem.input_format)),
        "output_format": redact(patched("output_format", problem.output_format)),
        "function_signature": redact(patched("function_signature", problem.function_signature)),
        "time_limit": patched("time_limit", problem.time_limit),
        "memory_limit": patched("memory_limit", problem.memory_limit),
        "hint": redact(patched("hint", problem.hint)),
        "public_sample_testcases": [
            {
                "case_index": index,
                "input": testcase.input,
                "expected_output": testcase.output,
                "explanation": None,
            }
            for index, testcase in enumerate(ordered_testcases, start=1)
            if not testcase.is_hidden
        ],
        "hidden_testcase_count": sum(1 for testcase in ordered_testcases if testcase.is_hidden),
        "existing_official_solutions": [
            {
                "language": solution.language.strip().lower(),
                "code": redact(solution.code) or "",
                "explanation": redact(solution.explanation) or "",
                "time_complexity": redact(solution.time_complexity),
                "space_complexity": redact(solution.space_complexity),
            }
            for solution in solutions
            if solution.language.strip().lower() != payload.language.strip().lower()
        ],
    }


def _truncate_prompt_value(value: str, limit: int = 6000) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit]}...[truncated]"


def _problem_validation_failure(problem: Problem, checks: list[dict], case_results: list[dict] | None = None) -> dict:
    public_count = sum(1 for testcase in problem.testcases if not testcase.is_hidden)
    hidden_count = sum(1 for testcase in problem.testcases if testcase.is_hidden)
    results = case_results or []
    failed = sum(1 for result in results if isinstance(result, dict) and not result.get("passed"))
    return {
        "passed": False,
        "summary": "validation_failed",
        "checks": checks,
        "case_results": results,
        "case_summary": {"total": len(results), "failed": failed},
        "public_sample_count": public_count,
        "hidden_testcase_count": hidden_count,
    }


def _validate_problem(problem: Problem) -> dict:
    solution_records = [solution for solution in problem.solutions if solution.is_official]
    try:
        solutions = [
            AuthoredOfficialSolution(
                language=str(solution.language),
                code=str(solution.code),
                explanation=str(solution.explanation),
            )
            for solution in solution_records
        ]
    except ValidationError as exc:
        return _problem_validation_failure(
            problem,
            [
                {
                    "name": ".".join(str(part) for part in error.get("loc", ())) or "official_solution",
                    "passed": False,
                    "message": str(error.get("type") or "invalid"),
                }
                for error in exc.errors()
            ],
        )
    if not solutions:
        return _problem_validation_failure(
            problem,
            [{"name": "official_solutions", "passed": False, "message": "At least one official solution is required"}],
        )
    testcases = [
        {
            "input": str(testcase.input),
            "output": str(testcase.output),
            "is_hidden": bool(testcase.is_hidden),
            "is_sample": bool(testcase.is_sample),
            "explanation": None,
            "order": int(testcase.order or index),
        }
        for index, testcase in enumerate(
            sorted(
                problem.testcases,
                key=lambda item: (
                    int(item.order or 0),
                    item.created_at.isoformat() if item.created_at else "",
                ),
            ),
            start=1,
        )
    ]
    primary = solutions[0]
    primary_record = solution_records[0]
    try:
        authored = AuthoredProblemDraft(
            title=str(problem.title),
            slug_candidate=str(problem.slug),
            description=str(problem.description),
            input_format=problem.input_format,
            output_format=problem.output_format,
            function_signature=problem.function_signature,
            difficulty=problem.difficulty.value,
            tags=list(problem.tags or []),
            mode=str(problem.mode or "acm"),
            time_limit=int(problem.time_limit or 1000),
            memory_limit=int(problem.memory_limit or 256),
            hint=problem.hint,
            official_solution_language=primary.language,
            official_solution_code=primary.code,
            official_solution_explanation=primary.explanation,
            official_solutions=solutions,
            time_complexity=str(primary_record.time_complexity or ""),
            space_complexity=str(primary_record.space_complexity or ""),
            public_sample_testcases=[
                AuthoredTestCase(
                    input=str(testcase["input"]),
                    output=str(testcase["output"]),
                    explanation=None,
                )
                for testcase in testcases
                if not testcase["is_hidden"]
            ],
            hidden_testcases=[
                AuthoredTestCase(
                    input=str(testcase["input"]),
                    output=str(testcase["output"]),
                    explanation=None,
                )
                for testcase in testcases
                if testcase["is_hidden"]
            ],
        )
    except ValidationError as exc:
        return _problem_validation_failure(
            problem,
            [
                {
                    "name": ".".join(str(part) for part in error.get("loc", ())) or "problem",
                    "passed": False,
                    "message": str(error.get("type") or "invalid"),
                }
                for error in exc.errors()
            ],
        )
    return ProblemDraftValidationAdapter().validate(authored, testcases, [solution.language for solution in solutions])
