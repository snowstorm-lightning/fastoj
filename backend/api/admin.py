from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
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
def overview(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    problems = db.query(Problem).order_by(Problem.created_at.desc()).all()
    users = db.query(User).order_by(User.created_at.desc()).all()
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
                }
                for user in users
            ],
            "problems": [
                {
                    "id": str(problem.id),
                    "title": problem.title,
                    "slug": problem.slug,
                    "difficulty": problem.difficulty.value,
                    "tags": problem.tags or [],
                    "is_public": problem.is_public,
                    "testcase_count": len(problem.testcases),
                    "hidden_testcase_count": sum(1 for testcase in problem.testcases if testcase.is_hidden),
                    "solution_count": len(problem.solutions),
                    "total_submissions": problem.total_submissions,
                }
                for problem in problems
            ],
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
