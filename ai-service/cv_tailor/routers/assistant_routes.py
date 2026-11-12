"""Workspace conversations, application drafts, and career agent runs."""
from datetime import datetime, timezone
import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from cv_tailor.database import get_db
from cv_tailor.dependencies import get_workspace_id
from cv_tailor.limiter import limiter
from cv_tailor.models import database_models as models
from cv_tailor.models.schemas import JobApplicationCreate, JobApplicationUpdate
from cv_tailor.services.career_agent import CareerToolContext, run_career_agent, serialize_draft
from cv_tailor.services.agent_activity import activity_sink
from cv_tailor.services.pdf_service import PDFCompilationError, compile_latex_to_pdf, pdf_page_count

router = APIRouter(prefix="/assistant", tags=["assistant"])


class ConversationCreate(BaseModel):
    job_id: int | None = None


class LinkJob(BaseModel):
    job_id: int


class SendMessage(BaseModel):
    content: str = Field(min_length=1, max_length=12000)
    request_id: str | None = Field(default=None, min_length=1, max_length=80)


class ReviseDraft(BaseModel):
    content: str = Field(min_length=1, max_length=100000)


def _write_lock(db):
    db.rollback()
    if db.bind.dialect.name == "sqlite":
        db.connection().exec_driver_sql("BEGIN IMMEDIATE")


def _conversation(db, workspace_id, conversation_id, *, lock=False):
    if lock:
        _write_lock(db)
    query = db.query(models.AssistantConversation).filter(
        models.AssistantConversation.id == conversation_id,
        models.AssistantConversation.workspace_id == workspace_id,
    )
    conversation = query.first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


def _job(db, workspace_id, job_id):
    if job_id is None:
        return None
    job = db.query(models.JobApplication).filter(
        models.JobApplication.id == job_id, models.JobApplication.workspace_id == workspace_id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


def _draft(db, conversation_id, draft_id):
    draft = db.query(models.AssistantDraft).filter(
        models.AssistantDraft.id == draft_id,
        models.AssistantDraft.conversation_id == conversation_id,
    ).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found.")
    return draft


def _summary(conversation):
    return {"id": conversation.id, "job_id": conversation.job_id, "title": conversation.title,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None}


def _detail(conversation, db):
    messages = db.query(models.AssistantMessage).filter(
        models.AssistantMessage.conversation_id == conversation.id).order_by(models.AssistantMessage.id).all()
    drafts = db.query(models.AssistantDraft).filter(
        models.AssistantDraft.conversation_id == conversation.id).order_by(models.AssistantDraft.id).all()
    return {**_summary(conversation), "messages": [{"id": m.id, "role": m.role, "content": m.content,
             "created_at": m.created_at.isoformat() if m.created_at else None} for m in messages],
            "drafts": [serialize_draft(d) for d in drafts]}


@router.get("/conversations")
def list_conversations(request: Request, db: Session = Depends(get_db)):
    workspace_id = get_workspace_id(request)
    conversations = db.query(models.AssistantConversation).filter(
        models.AssistantConversation.workspace_id == workspace_id).order_by(models.AssistantConversation.updated_at.desc()).all()
    return [_summary(item) for item in conversations]


@router.post("/conversations")
def create_conversation(data: ConversationCreate, request: Request, db: Session = Depends(get_db)):
    workspace_id = get_workspace_id(request)
    _write_lock(db)
    job = _job(db, workspace_id, data.job_id)
    if job:
        existing = db.query(models.AssistantConversation).filter_by(workspace_id=workspace_id, job_id=job.id).first()
        if existing:
            return _summary(existing)
    conversation = models.AssistantConversation(workspace_id=workspace_id, job_id=job.id if job else None,
        title=f"{job.job_title} · {job.company_name}"[:200] if job else "General conversation")
    db.add(conversation)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(models.AssistantConversation).filter_by(workspace_id=workspace_id, job_id=data.job_id).first()
        if existing:
            return _summary(existing)
        raise
    db.refresh(conversation)
    return _summary(conversation)


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: int, request: Request, db: Session = Depends(get_db)):
    conversation = _conversation(db, get_workspace_id(request), conversation_id)
    return _detail(conversation, db)


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, request: Request, db: Session = Depends(get_db)):
    conversation = _conversation(db, get_workspace_id(request), conversation_id, lock=True)
    db.delete(conversation)
    db.commit()
    return {"status": "deleted"}


@router.post("/conversations/{conversation_id}/link-job")
def link_job(conversation_id: int, data: LinkJob, request: Request, db: Session = Depends(get_db)):
    workspace_id = get_workspace_id(request)
    conversation = _conversation(db, workspace_id, conversation_id, lock=True)
    job = _job(db, workspace_id, data.job_id)
    if conversation.job_id is not None and conversation.job_id != job.id:
        raise HTTPException(status_code=409, detail="This conversation already belongs to an application.")
    other = db.query(models.AssistantConversation).filter(
        models.AssistantConversation.workspace_id == workspace_id, models.AssistantConversation.job_id == job.id,
        models.AssistantConversation.id != conversation.id).first()
    if other:
        raise HTTPException(status_code=409, detail="That application already has a conversation.")
    conversation.job_id = job.id
    conversation.title = f"{job.job_title} · {job.company_name}"[:200]
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="That application already has a conversation.") from exc
    return _detail(conversation, db)


@router.post("/conversations/{conversation_id}/messages")
@limiter.limit("10/minute")
async def send_message(conversation_id: int, data: SendMessage, request: Request, db: Session = Depends(get_db)):
    from uuid import uuid4
    from cv_tailor.services.snapshots import snapshot, profile_snapshot
    from cv_tailor.services.conversation_evidence import select_user_evidence
    from cv_tailor.routers.database_routes import PROFILE_LOAD_OPTIONS
    from cv_tailor.services.preset_service import resolve_preset
    from cv_tailor.services.llm_service import retrieve_successful_evidence

    workspace_id = get_workspace_id(request)
    conversation = _conversation(db, workspace_id, conversation_id, lock=True)
    content = data.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="Enter a message.")
    request_key = data.request_id or uuid4().hex
    if conversation.active_request_key:
        active = db.query(models.AssistantTurn).filter_by(conversation_id=conversation_id, request_key=conversation.active_request_key).first()
        if active and active.status == "in_progress":
            created = active.created_at.replace(tzinfo=timezone.utc) if active.created_at.tzinfo is None else active.created_at
            if (datetime.now(timezone.utc) - created).total_seconds() > 900:
                active.status, active.error = "failed", "Worker completion is unknown. Review before retrying this work."
                conversation.active_request_key = None
                db.commit()
    previous = db.query(models.AssistantTurn).filter_by(conversation_id=conversation_id, request_key=request_key).first()
    if previous:
        if previous.content != content:
            raise HTTPException(status_code=409, detail="This request ID was already used for a different message.")
        if previous.status == "completed":
            return _detail(conversation, db)
        # Recover the conversation lock, but never automatically repeat work whose
        # external outcome is unknown after a process crash.
        created = previous.created_at.replace(tzinfo=timezone.utc) if previous.created_at.tzinfo is None else previous.created_at
        if previous.status == "in_progress" and (datetime.now(timezone.utc) - created).total_seconds() > 900:
            previous.status, previous.error = "failed", "The worker stopped before completion; review before starting another request."
            db.query(models.AssistantConversation).filter_by(id=conversation_id, active_request_key=request_key).update({"active_request_key": None})
            db.commit()
        raise HTTPException(status_code=409, detail=f"This request is {previous.status}. Refresh the conversation before starting another request.")
    # Support retrying messages written before the turn lifecycle was introduced.
    legacy = db.query(models.AssistantMessage).filter_by(conversation_id=conversation_id, request_key=request_key).first()
    if legacy:
        if legacy.content != content:
            raise HTTPException(status_code=409, detail="This request ID was already used for a different message.")
        return _detail(conversation, db)
    claimed = db.query(models.AssistantConversation).filter_by(id=conversation_id, workspace_id=workspace_id, active_request_key=None).update({"active_request_key": request_key})
    if not claimed:
        db.rollback()
        raise HTTPException(status_code=409, detail="Another turn is active in this conversation. Wait or cancel it first.")
    turn = models.AssistantTurn(conversation_id=conversation_id, request_key=request_key, content=content, status="in_progress")
    db.add(turn)
    db.add(models.AssistantMessage(conversation_id=conversation_id, role="user", content=content, request_key=request_key))
    try:
        db.flush()
        profile = db.query(models.Profile).options(*PROFILE_LOAD_OPTIONS).filter_by(workspace_id=workspace_id).first()
        job = _job(db, workspace_id, conversation.job_id)
        transcript = [{"role": m.role, "content": m.content} for m in db.query(models.AssistantMessage).filter_by(conversation_id=conversation_id).order_by(models.AssistantMessage.id).all()]
        drafts = [snapshot(d) for d in db.query(models.AssistantDraft).filter_by(conversation_id=conversation_id).order_by(models.AssistantDraft.id).all()]
        applications = [snapshot(j) for j in db.query(models.JobApplication).filter_by(workspace_id=workspace_id).order_by(models.JobApplication.id.desc()).limit(101).all()]
        preset = resolve_preset(db, profile.preset_slug) if profile else None
        preset_data = {key: getattr(preset, key) for key in ("slug", "display_name", "target_summary_prompt", "core_skills_bank", "metric_prompts", "section_order", "recommended_template", "lever_guidance")} if preset else None
        historical = retrieve_successful_evidence(profile, job.job_description if job else "", db) if profile else []
        ctx = CareerToolContext(None, workspace_id, snapshot(conversation), snapshot(job), profile_snapshot(profile), select_user_evidence(transcript),
            staged=True, drafts=drafts, applications=applications, preset=preset_data, historical_evidence=historical)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This request is already active.") from exc
    except Exception:
        db.rollback()
        raise

    activity = []
    sink = activity_sink.get()
    def record_activity(item):
        activity.append(item)
        if sink:
            sink(item)
    ctx.activity_callback = record_activity

    def finish_failure(status, message):
        _write_lock(db)
        # Claim, completion, cancellation and recovery lock the conversation first.
        conversation = db.query(models.AssistantConversation).filter_by(id=conversation_id, workspace_id=workspace_id).first()
        row = db.query(models.AssistantTurn).filter_by(conversation_id=conversation_id, request_key=request_key).first()
        if row and row.status == "in_progress":
            row.status, row.error = status, message
        if conversation and conversation.active_request_key == request_key:
            conversation.active_request_key = None
        db.commit()

    try:
        from cv_tailor.services.external_work import run_agent
        reply = await run_agent(run_career_agent, ctx, transcript)
        if activity:
            ctx.save_draft("agent_activity", json.dumps(activity, ensure_ascii=False))
        _write_lock(db)
        conversation = db.query(models.AssistantConversation).filter_by(id=conversation_id, workspace_id=workspace_id).first()
        turn = db.query(models.AssistantTurn).filter_by(conversation_id=conversation_id, request_key=request_key).first()
        if not conversation or not turn or turn.status != "in_progress" or conversation.active_request_key != request_key:
            raise HTTPException(status_code=409, detail="This turn was cancelled or its conversation is no longer available.")
        assistant_message = models.AssistantMessage(conversation_id=conversation_id, role="assistant", content=reply)
        db.add(assistant_message)
        db.flush()
        identifiers = {}
        saved = []
        for staged in ctx.created_drafts:
            draft = models.AssistantDraft(conversation_id=conversation_id, type=staged.type, content=staged.content,
                details={**staged.details, "assistant_message_id": assistant_message.id})
            db.add(draft)
            db.flush()
            identifiers[staged.id] = draft.id
            saved.append(draft)
        for draft in saved:
            details = dict(draft.details)
            key = details.get("context_key", "")
            if key.startswith("draft:"):
                old = int(key.split(":", 1)[1])
                details["context_key"] = f"draft:{identifiers.get(old, old)}"
            draft.details = details
        conversation.active_request_key = None
        conversation.updated_at = datetime.now(timezone.utc)
        turn.status = "completed"
        db.commit()
    except asyncio.CancelledError:
        finish_failure("cancelled", "The connection closed before completion.")
        raise
    except Exception as exc:
        finish_failure("failed", "The turn could not finish. Review its status before starting another request.")
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=502, detail="The career agent couldn't respond. Please start a new request after reviewing the conversation.") from exc
    return _detail(conversation, db)


@router.post("/conversations/{conversation_id}/messages/stream")
@limiter.limit("10/minute")
async def stream_message(conversation_id: int, data: SendMessage, request: Request, db: Session = Depends(get_db)):
    # Validate access before beginning the streaming response.
    _conversation(db, get_workspace_id(request), conversation_id)
    db.rollback()
    if not data.content.strip():
        raise HTTPException(status_code=422, detail="Enter a message.")

    async def stream():
        queue = asyncio.Queue()
        token = activity_sink.set(lambda item: queue.put_nowait({"type": "activity", "activity": item}))

        async def run():
            try:
                result = await send_message.__wrapped__(conversation_id, data, request, db)
                await queue.put({"type": "complete", "conversation": result})
            except HTTPException as exc:
                turn = db.query(models.AssistantTurn).filter_by(conversation_id=conversation_id, request_key=data.request_id).first() if data.request_id else None
                status = turn.status if turn else None
                db.rollback()
                await queue.put({"type": "error", "message": str(exc.detail), "request_status": status})
            except Exception:
                await queue.put({"type": "error", "message": "The agent could not respond. Please try again."})

        task = asyncio.create_task(run())
        activity_sink.reset(token)
        try:
            while True:
                event = await queue.get()
                yield json.dumps(event, ensure_ascii=False) + "\n"
                if event["type"] in {"complete", "error"}:
                    break
        finally:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    db.rollback()

    return StreamingResponse(stream(), media_type="application/x-ndjson",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/conversations/{conversation_id}/messages/{request_key}/cancel")
def cancel_message(conversation_id: int, request_key: str, request: Request, db: Session = Depends(get_db)):
    workspace_id = get_workspace_id(request)
    conversation = db.query(models.AssistantConversation).filter_by(id=conversation_id, workspace_id=workspace_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    turn = db.query(models.AssistantTurn).filter_by(conversation_id=conversation_id, request_key=request_key).first()
    if not turn:
        raise HTTPException(status_code=404, detail="Request not found.")
    if turn.status == "in_progress":
        turn.status, turn.error = "cancelled", "Cancelled by the user. External work may still be winding down."
        db.query(models.AssistantConversation).filter_by(id=conversation_id, active_request_key=request_key).update({"active_request_key": None})
    db.commit()
    return {"status": turn.status}


@router.post("/conversations/{conversation_id}/drafts/{draft_id}/revise")
def revise_draft(conversation_id: int, draft_id: int, data: ReviseDraft, request: Request, db: Session = Depends(get_db)):
    conversation = _conversation(db, get_workspace_id(request), conversation_id)
    original = _draft(db, conversation.id, draft_id)
    draft_type = original.type
    if draft_type in {"tracker_action", "job_search", "agent_activity", "application_form"}:
        raise HTTPException(status_code=422, detail="This item cannot be edited as a draft.")
    details = {key: value for key, value in (original.details or {}).items() if key != "assistant_message_id"}
    if draft_type == "resume":
        db.rollback()
        try:
            pages = pdf_page_count(compile_latex_to_pdf(data.content))
        except PDFCompilationError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
        details = {**details, "pages": pages, "one_page": pages == 1}
        conversation = _conversation(db, get_workspace_id(request), conversation_id)
    draft = models.AssistantDraft(conversation_id=conversation.id, type=draft_type,
                                  content=data.content, details=details)
    db.add(draft)
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(draft)
    return serialize_draft(draft)


@router.post("/conversations/{conversation_id}/drafts/{draft_id}/confirm-tracker-action")
def confirm_tracker_action(conversation_id: int, draft_id: int, request: Request, db: Session = Depends(get_db)):
    workspace_id = get_workspace_id(request)
    conversation = _conversation(db, workspace_id, conversation_id)
    draft = db.query(models.AssistantDraft).filter_by(id=draft_id, conversation_id=conversation.id).first()
    if not draft or draft.type != "tracker_action":
        raise HTTPException(status_code=404, detail="Tracker proposal not found.")
    details = draft.details or {}
    if details.get("applied"):
        raise HTTPException(status_code=409, detail="This proposal has already been applied.")
    action = details.get("action")
    if action == "add":
        if conversation.job_id is not None:
            raise HTTPException(status_code=409, detail="This conversation is already linked to an application.")
        payload = details.get("payload") or {}
        if not all(str(payload.get(k) or "").strip() for k in ("company_name", "job_title", "job_description", "job_source")):
            raise HTTPException(status_code=422, detail="The job details are incomplete.")
        try:
            data = JobApplicationCreate.model_validate(payload)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid job details.") from exc
        job = models.JobApplication(workspace_id=workspace_id, **data.model_dump())
        db.add(job)
        db.flush()
        conversation.job_id = job.id
        conversation.title = f"{job.job_title} · {job.company_name}"[:200]
    elif action in {"update", "archive", "restore", "delete"}:
        job = _job(db, workspace_id, details.get("job_id"))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        from cv_tailor.workspace import check_revision
        check_revision(job, details.get("revision"))
        if action == "update":
            changes = details.get("changes") or {}
            allowed = {"company_name", "job_title", "job_url", "job_source", "job_description", "short_description", "status", "date_applied", "follow_up_date", "job_type", "location", "salary_range", "priority", "notes"}
            if not isinstance(changes, dict) or not changes or set(changes) - allowed:
                raise HTTPException(status_code=422, detail="Invalid tracker changes.")
            if "status" in changes and changes["status"] not in {"Saved", "Applied", "Interview", "Tech Test", "Offer", "Rejected", "Ghosted"}:
                raise HTTPException(status_code=422, detail="Invalid application status.")
            if any(field in changes and (not isinstance(changes[field], str) or not changes[field].strip()) for field in ("company_name", "job_title")):
                raise HTTPException(status_code=422, detail="Company and job title cannot be blank.")
            try:
                data = JobApplicationUpdate.model_validate(changes)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail="Invalid tracker changes.") from exc
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(job, field, value)
        elif action in {"archive", "restore"}:
            job.is_archived = action == "archive"
        else:
            current_deleted = conversation.job_id == job.id
            db.delete(job)
            if current_deleted:
                db.commit()
                return {"conversation_deleted": True}
    else:
        raise HTTPException(status_code=422, detail="Invalid tracker action.")
    if action != "add" and action != "delete":
        job.revision += 1
    draft.details = {**details, "applied": True}
    db.commit()
    return {"conversation_deleted": False, "conversation": _detail(conversation, db)}


@router.post("/conversations/{conversation_id}/drafts/{draft_id}/apply")
def apply_draft(conversation_id: int, draft_id: int, request: Request, revision: int, db: Session = Depends(get_db)):
    from cv_tailor import workspace as w
    _draft(db, conversation_id, draft_id)
    db.rollback()
    job = w.apply_draft(draft_id, revision)
    return {"status": "applied", "job_id": job["id"], "draft_id": draft_id}


def _snapshot_current(db, conversation, draft_type, content):
    if not content:
        return
    existing = db.query(models.AssistantDraft.id).filter_by(
        conversation_id=conversation.id, type=draft_type, content=content).first()
    if not existing:
        db.add(models.AssistantDraft(conversation_id=conversation.id, type=draft_type,
                                     content=content, details={"origin": "previous_application_document"}))


@router.get("/conversations/{conversation_id}/drafts/{draft_id}/pdf")
def download_draft_pdf(conversation_id: int, draft_id: int, request: Request, db: Session = Depends(get_db)):
    conversation = _conversation(db, get_workspace_id(request), conversation_id)
    draft = _draft(db, conversation.id, draft_id)
    draft_type, content = draft.type, draft.content
    db.rollback()
    if draft_type == "resume":
        try:
            pdf = compile_latex_to_pdf(content)
        except PDFCompilationError as exc:
            raise HTTPException(status_code=exc.status_code, detail=f"Could not compile this CV: {exc}") from exc
        return Response(content=pdf, media_type="application/pdf",
                        headers={"Content-Disposition": "inline; filename=cv-draft.pdf", "Cache-Control": "no-store"})
    if draft_type != "cheat_sheet":
        raise HTTPException(status_code=422, detail="PDF export is available for CVs and cheat sheets.")
    from cv_tailor.services.career_documents import cheat_sheet_pdf
    try:
        pdf = cheat_sheet_pdf(content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not create the cheat sheet PDF.") from exc
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=interview-cheat-sheet.pdf"})
