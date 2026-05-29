from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.ai.providers import AIProviderUnavailableError
from backend.api.admin import require_admin
from backend.core.database import get_db
from backend.models import AgentRun, AgentStep, ProblemDraft, User
from backend.schemas.problem_authoring import (
    AgentRunResponse,
    AgentStepResponse,
    ProblemAuthoringCreateResponse,
    ProblemAuthoringRequest,
    ProblemDraftListItem,
    ProblemDraftResponse,
    ProblemDraftUpdate,
)
from backend.services.problem_authoring_agent import ProblemAuthoringAgentService, load_json

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/agent/problem-drafts", response_model=ProblemAuthoringCreateResponse)
def create_problem_draft(
    payload: ProblemAuthoringRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        draft, run = ProblemAuthoringAgentService(db).create_draft(payload, current_user)
    except AIProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    validation_report = load_json(draft.validation_report_json, {})
    return ProblemAuthoringCreateResponse(
        draft_id=str(draft.id),
        run_id=str(run.id),
        status=draft.status,
        validation_summary=_validation_summary(validation_report),
        steps=[_step_response(step) for step in _run_steps(db, run)],
    )


@router.get("/agent/runs/{run_id}", response_model=AgentRunResponse)
def get_agent_run(
    run_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")
    return _run_response(db, run)


@router.get("/problem-drafts", response_model=list[ProblemDraftListItem])
def list_problem_drafts(
    query: str | None = Query(None, max_length=100),
    status_filter: str | None = Query(None, alias="status", max_length=30),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    drafts_query = db.query(ProblemDraft)
    if query and query.strip():
        pattern = f"%{query.strip()}%"
        drafts_query = drafts_query.filter(or_(ProblemDraft.title.ilike(pattern), ProblemDraft.slug.ilike(pattern)))
    if status_filter:
        drafts_query = drafts_query.filter(ProblemDraft.status == status_filter)
    drafts = (
        drafts_query.order_by(ProblemDraft.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [_draft_list_item(draft) for draft in drafts]


@router.get("/problem-drafts/{draft_id}", response_model=ProblemDraftResponse)
def get_problem_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    draft = db.query(ProblemDraft).filter(ProblemDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem draft not found")
    return _draft_response(db, draft)


@router.patch("/problem-drafts/{draft_id}", response_model=ProblemDraftResponse)
def update_problem_draft(
    draft_id: str,
    payload: ProblemDraftUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        draft = ProblemAuthoringAgentService(db).update_draft(draft_id, payload, current_user)
        return _draft_response(db, draft)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/problem-drafts/{draft_id}/approve", response_model=ProblemDraftResponse)
def approve_problem_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        draft = ProblemAuthoringAgentService(db).approve_draft(draft_id, current_user)
        return _draft_response(db, draft)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/problem-drafts/{draft_id}/reject", response_model=ProblemDraftResponse)
def reject_problem_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        draft = ProblemAuthoringAgentService(db).reject_draft(draft_id, current_user)
        return _draft_response(db, draft)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def _step_response(step: AgentStep) -> AgentStepResponse:
    return AgentStepResponse(
        id=str(step.id),
        run_id=str(step.run_id),
        step_index=step.step_index,
        step_type=step.step_type,
        tool_name=step.tool_name,
        input=load_json(step.input_json, {}),
        output=load_json(step.output_json, {}),
        status=step.status,
        error_message=step.error_message,
        created_at=step.created_at.isoformat(),
    )


def _latest_run(db: Session, draft: ProblemDraft) -> AgentRun | None:
    return db.query(AgentRun).filter(AgentRun.draft_id == draft.id).order_by(AgentRun.created_at.desc()).first()


def _run_steps(db: Session, run: AgentRun) -> list[AgentStep]:
    return db.query(AgentStep).filter(AgentStep.run_id == run.id).order_by(AgentStep.step_index).all()


def _run_response(db: Session, run: AgentRun) -> AgentRunResponse:
    return AgentRunResponse(
        id=str(run.id),
        run_type=run.run_type,
        status=run.status,
        input=load_json(run.input_json, {}),
        output=load_json(run.output_json, {}),
        error_message=run.error_message,
        model_profile=run.model_profile,
        locale=run.locale,
        created_by=str(run.created_by),
        draft_id=str(run.draft_id) if run.draft_id else None,
        created_at=run.created_at.isoformat(),
        finished_at=run.finished_at.isoformat() if run.finished_at else None,
        steps=[_step_response(step) for step in _run_steps(db, run)],
    )


def _draft_response(db: Session, draft: ProblemDraft) -> ProblemDraftResponse:
    latest_run = _latest_run(db, draft)
    return ProblemDraftResponse(
        id=str(draft.id),
        title=draft.title,
        slug=draft.slug,
        description=draft.description,
        difficulty=draft.difficulty,
        tags=load_json(draft.tags, []),
        mode=draft.mode,
        input_format=draft.input_format,
        output_format=draft.output_format,
        function_signature=draft.function_signature,
        time_limit=draft.time_limit,
        memory_limit=draft.memory_limit,
        hint=draft.hint,
        official_solution_language=draft.official_solution_language,
        official_solution_code=draft.official_solution_code,
        official_solution_explanation=draft.official_solution_explanation,
        official_solutions=_draft_solutions(draft),
        time_complexity=draft.time_complexity,
        space_complexity=draft.space_complexity,
        testcases=load_json(draft.testcases_json, []),
        validation_report=load_json(draft.validation_report_json, {}),
        status=draft.status,
        created_by=str(draft.created_by),
        approved_problem_id=str(draft.approved_problem_id) if draft.approved_problem_id else None,
        created_at=draft.created_at.isoformat(),
        updated_at=draft.updated_at.isoformat(),
        steps=[_step_response(step) for step in _run_steps(db, latest_run)] if latest_run else [],
    )


def _draft_list_item(draft: ProblemDraft) -> ProblemDraftListItem:
    report = load_json(draft.validation_report_json, {})
    return ProblemDraftListItem(
        id=str(draft.id),
        title=draft.title,
        slug=draft.slug,
        difficulty=draft.difficulty,
        tags=load_json(draft.tags, []),
        mode=draft.mode,
        status=draft.status,
        validation_summary=_validation_summary(report),
        approved_problem_id=str(draft.approved_problem_id) if draft.approved_problem_id else None,
        created_at=draft.created_at.isoformat(),
        updated_at=draft.updated_at.isoformat(),
    )


def _draft_solutions(draft: ProblemDraft) -> list[dict]:
    raw = load_json(getattr(draft, "official_solutions_json", None), [])
    if isinstance(raw, list) and raw:
        return [
            {
                "language": str(solution.get("language") or "python"),
                "code": str(solution.get("code") or ""),
                "explanation": str(solution.get("explanation") or ""),
            }
            for solution in raw
            if isinstance(solution, dict)
        ]
    return [
        {
            "language": str(draft.official_solution_language or "python"),
            "code": str(draft.official_solution_code or ""),
            "explanation": str(draft.official_solution_explanation or ""),
        }
    ]


def _validation_summary(report: dict) -> dict:
    return {
        "passed": bool(report.get("passed")),
        "summary": report.get("summary", "not_validated"),
        "public_sample_count": report.get("public_sample_count", 0),
        "hidden_testcase_count": report.get("hidden_testcase_count", 0),
        "case_summary": report.get("case_summary", {}),
        "failed_checks": [
            check.get("name")
            for check in report.get("checks", [])
            if isinstance(check, dict) and not check.get("passed")
        ],
    }
