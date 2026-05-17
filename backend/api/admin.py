from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.core.database import get_db
from backend.models import Difficulty, Problem, Solution, TestCase, User

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminUserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class AdminProblemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    hint: str | None = None
    difficulty: str | None = None
    tags: list[str] | None = None
    is_public: bool | None = None


class AdminSolutionUpsert(BaseModel):
    language: str
    code: str
    explanation: str
    time_complexity: str | None = None
    space_complexity: str | None = None


class AdminTestCaseUpdate(BaseModel):
    input: str | None = None
    output: str | None = None
    is_hidden: bool | None = None
    is_sample: bool | None = None
    score: int | None = None


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user


@router.get("/overview")
def overview(
    user_query: str | None = Query(None, max_length=100),
    user_role: str | None = Query(None, pattern="^(user|admin)$"),
    user_status: str | None = Query(None, pattern="^(active|disabled)$"),
    user_page: int = Query(1, ge=1),
    user_page_size: int = Query(10, ge=1, le=50),
    problem_query: str | None = Query(None, max_length=100),
    problem_difficulty: str | None = Query(None, pattern="^(easy|medium|hard)$"),
    problem_visibility: str | None = Query(None, pattern="^(public|private)$"),
    problem_page: int = Query(1, ge=1),
    problem_page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user_base_query = db.query(User)
    if user_query and user_query.strip():
        pattern = f"%{user_query.strip()}%"
        user_base_query = user_base_query.filter(or_(User.username.ilike(pattern), User.email.ilike(pattern)))
    if user_role:
        user_base_query = user_base_query.filter(User.role == user_role)
    if user_status:
        user_base_query = user_base_query.filter(User.is_active.is_(user_status == "active"))

    problem_base_query = db.query(Problem)
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
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.role is not None:
        if payload.role not in {"user", "admin"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    return {"success": True}


@router.patch("/problems/{problem_id}")
def update_problem(
    problem_id: str,
    payload: AdminProblemUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    if payload.difficulty is not None:
        try:
            problem.difficulty = Difficulty(payload.difficulty)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid difficulty") from exc

    for field in ["title", "description", "hint", "tags", "is_public"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(problem, field, value)
    db.commit()
    return {"success": True}


@router.put("/problems/{problem_id}/solutions")
def upsert_solution(
    problem_id: str,
    payload: AdminSolutionUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    solution = db.query(Solution).filter(Solution.problem_id == problem.id, Solution.language == payload.language).first()
    if not solution:
        solution = Solution(problem_id=problem.id, language=payload.language, created_by=current_user.id)
        db.add(solution)
    solution.code = payload.code
    solution.explanation = payload.explanation
    solution.time_complexity = payload.time_complexity
    solution.space_complexity = payload.space_complexity
    solution.is_official = True
    db.commit()
    return {"success": True}


@router.patch("/testcases/{testcase_id}")
def update_testcase(
    testcase_id: str,
    payload: AdminTestCaseUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    testcase = db.query(TestCase).filter(TestCase.id == testcase_id).first()
    if not testcase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Testcase not found")
    for field in ["input", "output", "is_hidden", "is_sample", "score"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(testcase, field, value)
    db.commit()
    return {"success": True}
