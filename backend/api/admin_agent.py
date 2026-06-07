import asyncio
import hashlib
import json

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.ai.providers import AIProviderUnavailableError
from backend.api.admin import (
    CONTENT_PERMISSION_CREATE_OWN_PROBLEMS,
    CONTENT_PERMISSION_PUBLISH_OWN_PROBLEMS,
    CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS,
    ROLE_ADMIN,
    require_content_permission,
)
from backend.core.database import SessionLocal, get_db
from backend.core.time import utc_now
from backend.models import AgentRun, AgentStep, ProblemDraft, User
from backend.schemas.problem_authoring import (
    AgentRunMessageRequest,
    AgentRunMessageResponse,
    AgentRunResponse,
    AgentRunRetryRequest,
    AgentSessionMessageResponse,
    AgentSessionResponse,
    AgentStepResponse,
    AuthoredOfficialSolution,
    ProblemAuthoringCreateResponse,
    ProblemAuthoringRequest,
    ProblemDraftListItem,
    ProblemDraftResponse,
    ProblemDraftSolutionGenerateRequest,
    ProblemDraftUpdate,
    ProblemImportRequest,
)
from backend.services.problem_authoring_agent import (
    AgentRunFailedError,
    AgentRunProviderUnavailableError,
    ProblemAuthoringAgentService,
    load_json,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/agent/problem-drafts", response_model=ProblemAuthoringCreateResponse)
def create_problem_draft(
    payload: ProblemAuthoringRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_CREATE_OWN_PROBLEMS)),
    background_tasks: BackgroundTasks = None,
):
    if background_tasks is not None:
        run = ProblemAuthoringAgentService(db).enqueue_draft_run(
            payload,
            current_user,
            "problem_authoring",
        )
        background_tasks.add_task(_execute_agent_run_background, str(run.id), str(current_user.id))
        return _queued_response(db, run)

    try:
        draft, run = ProblemAuthoringAgentService(db).create_draft(payload, current_user)
    except AgentRunProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_agent_failure_detail(exc),
        ) from exc
    except AIProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except AgentRunFailedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_agent_failure_detail(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    validation_report = load_json(draft.validation_report_json, {})
    return ProblemAuthoringCreateResponse(
        draft_id=str(draft.id),
        run_id=str(run.id),
        session_id=_run_session_id(db, run),
        status=draft.status,
        validation_summary=_validation_summary(validation_report),
        steps=[_step_response(step) for step in _run_steps(db, run)],
    )


@router.post("/agent/problem-imports", response_model=ProblemAuthoringCreateResponse)
def create_problem_import(
    payload: ProblemImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_CREATE_OWN_PROBLEMS)),
    background_tasks: BackgroundTasks = None,
):
    if background_tasks is not None:
        run = ProblemAuthoringAgentService(db).enqueue_draft_run(
            payload,
            current_user,
            "problem_import",
        )
        background_tasks.add_task(_execute_agent_run_background, str(run.id), str(current_user.id))
        return _queued_response(db, run)

    try:
        draft, run = ProblemAuthoringAgentService(db).create_import_draft(payload, current_user)
    except AgentRunProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_agent_failure_detail(exc),
        ) from exc
    except AIProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except AgentRunFailedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_agent_failure_detail(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    validation_report = load_json(draft.validation_report_json, {})
    return ProblemAuthoringCreateResponse(
        draft_id=str(draft.id),
        run_id=str(run.id),
        session_id=_run_session_id(db, run),
        status=draft.status,
        validation_summary=_validation_summary(validation_report),
        steps=[_step_response(step) for step in _run_steps(db, run)],
    )


@router.get("/agent/runs", response_model=list[AgentRunResponse])
def list_agent_runs(
    run_type: str | None = Query(None, max_length=50),
    status_filter: str | None = Query(None, alias="status", max_length=30),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_CREATE_OWN_PROBLEMS)),
):
    runs_query = db.query(AgentRun)
    if current_user.role != ROLE_ADMIN:
        runs_query = runs_query.filter(AgentRun.created_by == current_user.id)
    if run_type:
        runs_query = runs_query.filter(AgentRun.run_type == run_type)
    if status_filter:
        runs_query = runs_query.filter(AgentRun.status == status_filter)
    runs = (
        runs_query.order_by(AgentRun.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [_run_response(db, run) for run in runs]


@router.get("/agent/sessions", response_model=list[AgentSessionResponse])
def list_agent_sessions(
    run_type: str | None = Query(None, max_length=50),
    status_filter: str | None = Query(None, alias="status", max_length=30),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_CREATE_OWN_PROBLEMS)),
):
    sessions = _agent_sessions(db, current_user, run_type=run_type, status_filter=status_filter)
    ordered = sorted(sessions.values(), key=lambda session: session["updated_at"], reverse=True)
    selected = ordered[(page - 1) * page_size : page * page_size]
    return [_session_response(db, session) for session in selected]


@router.get("/agent/sessions/{session_id}", response_model=AgentSessionResponse)
def get_agent_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_CREATE_OWN_PROBLEMS)),
):
    sessions = _agent_sessions(db, current_user)
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent session not found")
    return _session_response(db, session)


@router.get("/agent/runs/{run_id}", response_model=AgentRunResponse)
def get_agent_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_CREATE_OWN_PROBLEMS)),
):
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")
    _ensure_own_run_or_admin(run, current_user)
    return _run_response(db, run)


@router.get("/agent/runs/{run_id}/events")
async def stream_agent_run_events(
    run_id: str,
    request: Request,
    last_event_id: str | None = Header(None, alias="Last-Event-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_CREATE_OWN_PROBLEMS)),
):
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")
    _ensure_own_run_or_admin(run, current_user)
    user_id = str(current_user.id)
    user_role = str(current_user.role)
    try:
        last_step_index = int(last_event_id or "0")
    except ValueError:
        last_step_index = 0

    async def event_generator():
        sent_step_index = last_step_index
        sent_terminal = False
        sent_draft_ready = False
        heartbeat = 0
        stream_db = SessionLocal()
        try:
            stream_run = stream_db.query(AgentRun).filter(AgentRun.id == run_id).first()
            if not stream_run:
                yield _sse_event("error", "error", {"message": "Agent run not found"})
                return
            if user_role != ROLE_ADMIN and str(stream_run.created_by) != user_id:
                yield _sse_event("error", "error", {"message": "Can only access your own agent runs"})
                return
            yield _sse_event("snapshot", "0", {"run": _run_response(stream_db, stream_run).model_dump()})

            while True:
                if await request.is_disconnected():
                    return
                stream_db.expire_all()
                stream_run = stream_db.query(AgentRun).filter(AgentRun.id == run_id).first()
                if not stream_run:
                    yield _sse_event("error", "error", {"message": "Agent run not found"})
                    return
                steps = (
                    stream_db.query(AgentStep)
                    .filter(AgentStep.run_id == stream_run.id, AgentStep.step_index > sent_step_index)
                    .order_by(AgentStep.step_index.asc())
                    .all()
                )
                for step in steps:
                    sent_step_index = int(step.step_index)
                    yield _sse_event("step", str(sent_step_index), {"step": _step_response(step).model_dump()})

                if stream_run.draft_id and not sent_draft_ready:
                    sent_draft_ready = True
                    yield _sse_event(
                        "draft_ready",
                        str(sent_step_index),
                        {"draft_id": str(stream_run.draft_id), "run_id": str(stream_run.id)},
                    )

                if stream_run.status != "running" and not sent_terminal:
                    sent_terminal = True
                    yield _sse_event(
                        "run_status",
                        str(sent_step_index),
                        {"run": _run_response(stream_db, stream_run).model_dump()},
                    )
                    return

                heartbeat += 1
                if heartbeat % 10 == 0:
                    yield _sse_event("heartbeat", str(sent_step_index), {"status": stream_run.status})
                await asyncio.sleep(0.75)
        finally:
            stream_db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/agent/runs/{run_id}/messages", response_model=AgentRunMessageResponse)
@router.post("/agent/runs/{run_id}/follow-ups", response_model=AgentRunMessageResponse)
def create_agent_run_message(
    run_id: str,
    payload: AgentRunMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_CREATE_OWN_PROBLEMS)),
):
    try:
        message, suggested_actions, step = ProblemAuthoringAgentService(db).chat_about_run(
            run_id,
            payload.message,
            payload.model_profile,
            payload.locale,
            current_user,
        )
        return AgentRunMessageResponse(
            run_id=run_id,
            message=message,
            suggested_actions=suggested_actions,
            step=_step_response(step),
        )
    except AgentRunProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=_agent_failure_detail(exc)) from exc
    except AIProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/agent/runs/{run_id}/retry", response_model=ProblemAuthoringCreateResponse)
def retry_agent_run(
    run_id: str,
    payload: AgentRunRetryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_CREATE_OWN_PROBLEMS)),
    background_tasks: BackgroundTasks = None,
):
    if background_tasks is not None:
        parent = db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")
        _ensure_own_run_or_admin(parent, current_user)
        retry_payload, session_id, retry_guidance = _retry_payload_from_parent(db, parent, payload)
        retry = ProblemAuthoringAgentService(db).enqueue_draft_run(
            retry_payload,
            current_user,
            str(parent.run_type),
            agent_session_id=session_id,
            parent_run_id=str(parent.id),
            retry_guidance=retry_guidance,
        )
        background_tasks.add_task(_execute_agent_run_background, str(retry.id), str(current_user.id))
        return _queued_response(db, retry)

    try:
        draft, retry = ProblemAuthoringAgentService(db).retry_run(
            run_id,
            payload.guidance or payload.message,
            payload.locale,
            payload.model_profile,
            current_user,
        )
    except AgentRunProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=_agent_failure_detail(exc)) from exc
    except AIProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except AgentRunFailedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_agent_failure_detail(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    validation_report = load_json(draft.validation_report_json, {})
    return ProblemAuthoringCreateResponse(
        draft_id=str(draft.id),
        run_id=str(retry.id),
        session_id=_run_session_id(db, retry),
        status=draft.status,
        validation_summary=_validation_summary(validation_report),
        steps=[_step_response(step) for step in _run_steps(db, retry)],
    )


@router.get("/problem-drafts", response_model=list[ProblemDraftListItem])
def list_problem_drafts(
    query: str | None = Query(None, max_length=100),
    status_filter: str | None = Query(None, alias="status", max_length=30),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_CREATE_OWN_PROBLEMS)),
):
    drafts_query = db.query(ProblemDraft)
    if current_user.role != ROLE_ADMIN:
        drafts_query = drafts_query.filter(ProblemDraft.created_by == current_user.id)
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
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    draft = db.query(ProblemDraft).filter(ProblemDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem draft not found")
    _ensure_own_draft_or_admin(draft, current_user)
    return _draft_response(db, draft)


@router.patch("/problem-drafts/{draft_id}", response_model=ProblemDraftResponse)
def update_problem_draft(
    draft_id: str,
    payload: ProblemDraftUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    draft = db.query(ProblemDraft).filter(ProblemDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem draft not found")
    _ensure_own_draft_or_admin(draft, current_user)
    try:
        draft = ProblemAuthoringAgentService(db).update_draft(draft_id, payload, current_user)
        return _draft_response(db, draft)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/problem-drafts/{draft_id}/revalidate", response_model=ProblemDraftResponse)
def revalidate_problem_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    draft = db.query(ProblemDraft).filter(ProblemDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem draft not found")
    _ensure_own_draft_or_admin(draft, current_user)
    try:
        draft = ProblemAuthoringAgentService(db).revalidate_draft(draft_id, current_user)
        return _draft_response(db, draft)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/problem-drafts/{draft_id}/solutions/generate", response_model=AuthoredOfficialSolution)
def generate_problem_draft_solution(
    draft_id: str,
    payload: ProblemDraftSolutionGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    draft = db.query(ProblemDraft).filter(ProblemDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem draft not found")
    _ensure_own_draft_or_admin(draft, current_user)
    try:
        return ProblemAuthoringAgentService(db).generate_solution_for_draft(
            draft_id,
            payload.language,
            payload.model_profile,
            payload.locale,
            current_user,
            payload.draft,
        )
    except AgentRunProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_agent_failure_detail(exc),
        ) from exc
    except AIProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except AgentRunFailedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=_agent_failure_detail(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/problem-drafts/{draft_id}/approve", response_model=ProblemDraftResponse)
def approve_problem_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_PUBLISH_OWN_PROBLEMS)),
):
    draft = db.query(ProblemDraft).filter(ProblemDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem draft not found")
    _ensure_own_draft_or_admin(draft, current_user)
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
    current_user: User = Depends(require_content_permission(CONTENT_PERMISSION_UPDATE_OWN_PROBLEMS)),
):
    draft = db.query(ProblemDraft).filter(ProblemDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem draft not found")
    _ensure_own_draft_or_admin(draft, current_user)
    try:
        draft = ProblemAuthoringAgentService(db).reject_draft(draft_id, current_user)
        return _draft_response(db, draft)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def _queued_response(db: Session, run: AgentRun) -> ProblemAuthoringCreateResponse:
    return ProblemAuthoringCreateResponse(
        draft_id=str(run.draft_id) if run.draft_id else None,
        run_id=str(run.id),
        session_id=_run_session_id(db, run),
        status=str(run.status),
        validation_summary={},
        steps=[_step_response(step) for step in _run_steps(db, run)],
    )


def _sse_event(event: str, event_id: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, default=str)
    return f"id: {event_id}\nevent: {event}\ndata: {payload}\n\n"


def _retry_payload_from_parent(
    db: Session,
    parent: AgentRun,
    payload: AgentRunRetryRequest,
) -> tuple[ProblemImportRequest | ProblemAuthoringRequest, str, str]:
    parent_input = load_json(parent.input_json, {})
    session_id = _run_session_id(db, parent)
    retry_guidance = (payload.guidance or payload.message or "").strip()
    if parent.run_type == "problem_import":
        request_payload = ProblemImportRequest.model_validate(parent_input)
        updates: dict[str, str] = {}
        if payload.locale:
            updates["locale"] = payload.locale
        if payload.model_profile:
            updates["model_profile"] = payload.model_profile
        if retry_guidance:
            notes = "\n\n".join(
                part for part in [request_payload.import_notes, f"Retry guidance: {retry_guidance}"] if part
            )
            updates["import_notes"] = notes[:2000]
        return request_payload.model_copy(update=updates), session_id, retry_guidance
    if parent.run_type == "problem_authoring":
        request_payload = ProblemAuthoringRequest.model_validate(parent_input)
        updates = {}
        if payload.locale:
            updates["locale"] = payload.locale
        if payload.model_profile:
            updates["model_profile"] = payload.model_profile
        if retry_guidance:
            constraints = "\n\n".join(
                part for part in [request_payload.constraints, f"Retry guidance: {retry_guidance}"] if part
            )
            updates["constraints"] = constraints[:2000]
        return request_payload.model_copy(update=updates), session_id, retry_guidance
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only problem authoring and import runs can be retried")


def _execute_agent_run_background(run_id: str, user_id: str) -> None:
    db = SessionLocal()
    try:
        run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        if not run or not user:
            return
        run_input = load_json(run.input_json, {})
        session_id = str(run_input.get("agent_session_id") or run.id)
        service = ProblemAuthoringAgentService(db)
        if run.run_type == "problem_import":
            payload = ProblemImportRequest.model_validate(run_input)
            service.create_import_draft(payload, user, agent_session_id=session_id, existing_run=run)
        elif run.run_type == "problem_authoring":
            payload = ProblemAuthoringRequest.model_validate(run_input)
            service.create_draft(payload, user, agent_session_id=session_id, existing_run=run)
        else:
            run.status = "failed"
            run.error_message = f"Unsupported agent run type: {run.run_type}"
            run.finished_at = utc_now()
            db.commit()
    except (AgentRunProviderUnavailableError, AgentRunFailedError, AIProviderUnavailableError, ValueError) as exc:
        db.rollback()
        run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if run and run.status == "running":
            run.status = "failed"
            run.error_message = str(exc)
            run.finished_at = utc_now()
            db.commit()
    finally:
        db.close()


def _ensure_own_run_or_admin(run: AgentRun, current_user: User) -> None:
    if current_user.role == ROLE_ADMIN:
        return
    if str(run.created_by) == str(current_user.id):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only access your own agent runs")


def _ensure_own_draft_or_admin(draft: ProblemDraft, current_user: User) -> None:
    if current_user.role == ROLE_ADMIN:
        return
    if str(draft.created_by) == str(current_user.id):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only access your own drafts")


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


def _draft_runs(db: Session, draft: ProblemDraft) -> list[AgentRun]:
    return db.query(AgentRun).filter(AgentRun.draft_id == draft.id).order_by(AgentRun.created_at.asc()).all()


def _run_steps(db: Session, run: AgentRun) -> list[AgentStep]:
    return db.query(AgentStep).filter(AgentStep.run_id == run.id).order_by(AgentStep.step_index).all()


def _agent_sessions(
    db: Session,
    current_user: User,
    *,
    run_type: str | None = None,
    status_filter: str | None = None,
) -> dict[str, dict]:
    runs_query = db.query(AgentRun)
    drafts_query = db.query(ProblemDraft)
    if current_user.role != ROLE_ADMIN:
        runs_query = runs_query.filter(AgentRun.created_by == current_user.id)
        drafts_query = drafts_query.filter(ProblemDraft.created_by == current_user.id)
    if run_type:
        runs_query = runs_query.filter(AgentRun.run_type == run_type)

    runs = runs_query.order_by(AgentRun.created_at.asc()).all()
    drafts = drafts_query.order_by(ProblemDraft.created_at.asc()).all()
    sessions: dict[str, dict] = {}

    def ensure_session(session_id: str) -> dict:
        session = sessions.get(session_id)
        if session is None:
            session = {"id": session_id, "runs": [], "drafts": [], "created_at": None, "updated_at": None}
            sessions[session_id] = session
        return session

    for run in runs:
        session_id = _run_session_id(db, run)
        session = ensure_session(session_id)
        session["runs"].append(run)
        _touch_session(session, run.created_at, run.finished_at or run.created_at)

    draft_run_session: dict[str, str] = {}
    for session_id, session in sessions.items():
        for run in session["runs"]:
            if run.draft_id:
                draft_run_session[str(run.draft_id)] = session_id

    for draft in drafts:
        session_id = _draft_session_id(draft, draft_run_session)
        session = ensure_session(session_id)
        session["drafts"].append(draft)
        _touch_session(session, draft.created_at, draft.updated_at)

    if status_filter:
        sessions = {
            session_id: session
            for session_id, session in sessions.items()
            if _session_status(session) == status_filter
        }
    return sessions


def _touch_session(session: dict, created_at, updated_at) -> None:
    if session["created_at"] is None or created_at < session["created_at"]:
        session["created_at"] = created_at
    if session["updated_at"] is None or updated_at > session["updated_at"]:
        session["updated_at"] = updated_at


def _run_session_id(db: Session, run: AgentRun, seen: set[str] | None = None) -> str:
    seen = seen or set()
    run_id = str(run.id)
    if run_id in seen:
        return run_id
    seen.add(run_id)

    run_input = load_json(run.input_json, {})
    run_output = load_json(run.output_json, {})
    for source in (run_input, run_output):
        session_id = str(source.get("agent_session_id") or "").strip()
        if session_id:
            return session_id

    parent_run_id = str(run_input.get("parent_run_id") or run_output.get("parent_run_id") or "").strip()
    if parent_run_id:
        parent = db.query(AgentRun).filter(AgentRun.id == parent_run_id).first()
        if parent is not None:
            return _run_session_id(db, parent, seen)

    raw_material = str(run_input.get("raw_material") or "").strip()
    if raw_material:
        digest = hashlib.sha256(raw_material.encode("utf-8")).hexdigest()[:16]
        return f"legacy-import:{run.created_by}:{run_input.get('mode') or 'unknown'}:{digest}"
    topic = str(run_input.get("topic") or "").strip()
    if topic:
        digest = hashlib.sha256(topic.encode("utf-8")).hexdigest()[:16]
        return f"legacy-topic:{run.created_by}:{run.run_type}:{run_input.get('mode') or 'unknown'}:{digest}"
    return run_id


def _draft_session_id(draft: ProblemDraft, draft_run_session: dict[str, str]) -> str:
    metadata = _draft_source_metadata(draft)
    session_id = str(metadata.get("agent_session_id") or "").strip()
    if session_id:
        return session_id
    linked_session = draft_run_session.get(str(draft.id))
    if linked_session:
        return linked_session
    raw_material = str(metadata.get("raw_material") or "").strip()
    if raw_material:
        digest = hashlib.sha256(raw_material.encode("utf-8")).hexdigest()[:16]
        return f"legacy-import:{draft.created_by}:{draft.mode or 'unknown'}:{digest}"
    return str(draft.id)


def _session_status(session: dict) -> str:
    latest_draft = _latest_draft(session)
    if latest_draft is not None:
        return latest_draft.status
    latest_run = _latest_run(session)
    return latest_run.status if latest_run is not None else "unknown"


def _latest_run(session: dict) -> AgentRun | None:
    runs = session.get("runs") or []
    if not runs:
        return None
    return max(runs, key=lambda run: run.finished_at or run.created_at)


def _latest_draft(session: dict) -> ProblemDraft | None:
    drafts = session.get("drafts") or []
    if not drafts:
        return None
    return max(drafts, key=lambda draft: draft.updated_at)


def _session_response(db: Session, session: dict) -> AgentSessionResponse:
    runs = sorted(session.get("runs") or [], key=lambda run: run.created_at)
    drafts = sorted(session.get("drafts") or [], key=lambda draft: draft.created_at)
    latest_run = _latest_run(session)
    latest_draft = _latest_draft(session)
    first_run = runs[0] if runs else None
    first_input = load_json(first_run.input_json, {}) if first_run else {}
    latest_metadata = _draft_source_metadata(latest_draft) if latest_draft is not None else {}
    title = (
        latest_draft.title
        if latest_draft is not None
        else str(first_input.get("topic") or _raw_material_title(first_input) or "出题会话")
    )
    run_type = latest_run.run_type if latest_run is not None else str(first_input.get("run_type") or "problem_authoring")
    mode = latest_draft.mode if latest_draft is not None else str(first_input.get("mode") or "") or None
    source_kind = str(latest_metadata.get("kind") or ("imported" if first_input.get("raw_material") else "generated"))
    created_at = session["created_at"] or (latest_run.created_at if latest_run else latest_draft.created_at)
    updated_at = session["updated_at"] or created_at
    return AgentSessionResponse(
        id=session["id"],
        title=title,
        run_type=run_type,
        status=_session_status(session),
        mode=mode,
        source_kind=source_kind,
        draft_count=len(drafts),
        run_count=len(runs),
        latest_draft=_draft_list_item(latest_draft) if latest_draft is not None else None,
        latest_run=_run_response(db, latest_run) if latest_run is not None else None,
        drafts=[_draft_list_item(draft) for draft in drafts],
        runs=[_run_response(db, run) for run in runs],
        messages=_session_messages(db, runs),
        created_at=created_at.isoformat(),
        updated_at=updated_at.isoformat(),
    )


def _raw_material_title(run_input: dict) -> str | None:
    raw_material = str(run_input.get("raw_material") or "").strip()
    if not raw_material:
        return None
    for line in raw_material.splitlines():
        cleaned = line.strip("# \t")
        if cleaned:
            return cleaned[:80]
    return None


def _session_messages(db: Session, runs: list[AgentRun]) -> list[AgentSessionMessageResponse]:
    messages: list[AgentSessionMessageResponse] = []
    for run in runs:
        run_input = load_json(run.input_json, {})
        created_at = run.created_at.isoformat()
        raw_material = str(run_input.get("raw_material") or "").strip()
        if raw_material:
            messages.append(
                AgentSessionMessageResponse(
                    id=f"{run.id}:raw",
                    role="user",
                    message=f"导入原始材料（{len(raw_material)} 字）：{_raw_material_title(run_input) or '未命名题面'}",
                    run_id=str(run.id),
                    created_at=created_at,
                )
            )
        elif run_input.get("topic"):
            messages.append(
                AgentSessionMessageResponse(
                    id=f"{run.id}:topic",
                    role="user",
                    message=f"生成题目：{run_input.get('topic')}",
                    run_id=str(run.id),
                    created_at=created_at,
                )
            )
        retry_guidance = str(run_input.get("retry_guidance") or "").strip() or _retry_guidance_from_notes(run_input)
        if retry_guidance:
            messages.append(
                AgentSessionMessageResponse(
                    id=f"{run.id}:retry",
                    role="user",
                    message=f"重试指导：{retry_guidance}",
                    run_id=str(run.id),
                    created_at=created_at,
                )
            )
        for step in _run_steps(db, run):
            if step.step_type != "agent_chat":
                continue
            step_input = load_json(step.input_json, {})
            step_output = load_json(step.output_json, {})
            user_message = str(step_input.get("message") or "").strip()
            if not user_message and step_input.get("message_length"):
                user_message = f"管理员发送了一条追问（{step_input.get('message_length')} 字）"
            if user_message:
                messages.append(
                    AgentSessionMessageResponse(
                        id=f"{step.id}:user",
                        role="user",
                        message=user_message,
                        run_id=str(run.id),
                        created_at=step.created_at.isoformat(),
                    )
                )
            answer = str(step_output.get("message") or "").strip()
            if answer:
                messages.append(
                    AgentSessionMessageResponse(
                        id=f"{step.id}:assistant",
                        role="assistant",
                        message=answer,
                        run_id=str(run.id),
                        created_at=step.created_at.isoformat(),
                    )
                )
    return sorted(messages, key=lambda message: message.created_at)


def _retry_guidance_from_notes(run_input: dict) -> str:
    notes = str(run_input.get("import_notes") or run_input.get("constraints") or "")
    marker = "Retry guidance:"
    if marker not in notes:
        return ""
    return notes.rsplit(marker, 1)[-1].strip()[:500]


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


def _agent_failure_detail(exc: AgentRunFailedError | AgentRunProviderUnavailableError) -> dict[str, str]:
    return {"message": str(exc), "run_id": exc.run_id}


def _draft_response(db: Session, draft: ProblemDraft) -> ProblemDraftResponse:
    runs = _draft_runs(db, draft)
    latest_run = runs[-1] if runs else None
    all_steps = [step for run in runs for step in _run_steps(db, run)]
    return ProblemDraftResponse(
        id=str(draft.id),
        title=draft.title,
        slug=draft.slug,
        description=draft.description,
        difficulty=draft.difficulty,
        tags=load_json(draft.tags, []),
        mode=draft.mode,
        target_languages=_draft_target_languages(draft),
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
        source_metadata=_draft_source_metadata(draft),
        status=draft.status,
        created_by=str(draft.created_by),
        approved_problem_id=str(draft.approved_problem_id) if draft.approved_problem_id else None,
        created_at=draft.created_at.isoformat(),
        updated_at=draft.updated_at.isoformat(),
        steps=[_step_response(step) for step in (all_steps or (_run_steps(db, latest_run) if latest_run else []))],
        runs=[_run_response(db, run) for run in runs],
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
        target_languages=_draft_target_languages(draft),
        status=draft.status,
        validation_summary=_validation_summary(report),
        source_metadata=_draft_source_metadata(draft),
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


def _draft_target_languages(draft: ProblemDraft) -> list[str]:
    raw = load_json(getattr(draft, "target_languages_json", None), [])
    if isinstance(raw, list):
        languages = [str(item).strip().lower() for item in raw if str(item).strip()]
        if languages:
            return list(dict.fromkeys(languages))
    return list(dict.fromkeys(solution["language"] for solution in _draft_solutions(draft)))


def _draft_source_metadata(draft: ProblemDraft) -> dict:
    metadata = load_json(getattr(draft, "source_metadata_json", None), {})
    return metadata if isinstance(metadata, dict) else {}


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
