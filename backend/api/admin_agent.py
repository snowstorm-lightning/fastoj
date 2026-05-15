from fastapi import APIRouter, Depends, HTTPException, status
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
        steps=[_step_response(step) for step in run.steps],
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
    return _run_response(run)


@router.get("/problem-drafts", response_model=list[ProblemDraftListItem])
def list_problem_drafts(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    drafts = db.query(ProblemDraft).order_by(ProblemDraft.created_at.desc()).all()
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
    return _draft_response(draft)


@router.post("/problem-drafts/{draft_id}/approve", response_model=ProblemDraftResponse)
def approve_problem_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        draft = ProblemAuthoringAgentService(db).approve_draft(draft_id, current_user)
        return _draft_response(draft)
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
        return _draft_response(draft)
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


def _run_response(run: AgentRun) -> AgentRunResponse:
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
        steps=[_step_response(step) for step in sorted(run.steps, key=lambda item: item.step_index)],
    )


def _draft_response(draft: ProblemDraft) -> ProblemDraftResponse:
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
        time_complexity=draft.time_complexity,
        space_complexity=draft.space_complexity,
        testcases=load_json(draft.testcases_json, []),
        validation_report=load_json(draft.validation_report_json, {}),
        status=draft.status,
        created_by=str(draft.created_by),
        approved_problem_id=str(draft.approved_problem_id) if draft.approved_problem_id else None,
        created_at=draft.created_at.isoformat(),
        updated_at=draft.updated_at.isoformat(),
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


def _validation_summary(report: dict) -> dict:
    return {
        "passed": bool(report.get("passed")),
        "summary": report.get("summary", "not_validated"),
        "public_sample_count": report.get("public_sample_count", 0),
        "hidden_testcase_count": report.get("hidden_testcase_count", 0),
        "failed_checks": [
            check.get("name")
            for check in report.get("checks", [])
            if isinstance(check, dict) and not check.get("passed")
        ],
    }
