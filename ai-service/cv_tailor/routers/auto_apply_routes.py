"""
Auto Apply Phase 1 Router — Job Filtering, Selection, and Run Queue.
Provides endpoints for setup defaults, run-level location filtering/prioritization,
job preview with cross-post deduplication and tracker exclusion,
persistent queue management (pause/resume/needs input), and chat-style activity feed.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session

from cv_tailor.database import get_db
from cv_tailor.services.auto_apply_service import (
    _resolve_user_id,
    get_profile_suggestions,
    get_auto_apply_defaults,
    save_auto_apply_defaults,
    generate_auto_apply_preview,
    get_queue_data,
    add_jobs_to_queue,
    set_queue_paused_state,
    resolve_needs_input_item,
    get_answer_bank,
    save_answer_bank,
    process_queue_form_filling,
    answer_pending_question,
    get_application_form_review,
    tailor_cv_for_job,
    process_queue_with_approvals,
    approve_tailored_cv,
    approve_portal_submission,
    get_tailored_cv_preview,
    submit_to_company_portal,
    verify_unclear_submission,
    execute_workday_flow,
    resume_human_checkpoint,
    prepare_portal_handoff,
    report_manual_submission,
    connect_gmail_account,
    disconnect_gmail_account,
    get_gmail_status,
    parse_and_ingest_message,
    draft_email_application,
    approve_and_send_email,
)

logger = logging.getLogger("auto-apply-routes")

router = APIRouter(prefix="/auto-apply", tags=["auto-apply"])


# --- Pydantic Schemas ---

class AutoApplySetupUpdate(BaseModel):
    role_themes: List[str]
    min_experience_years: int = Field(ge=0, le=40)
    max_experience_years: int = Field(ge=0, le=40)
    preferred_locations: Optional[List[str]] = None
    work_arrangements: Optional[List[str]] = None
    location_mode: Optional[str] = "prioritize"
    unattended_include_lower_ranked: Optional[bool] = False
    auto_queue_future_matches: Optional[bool] = False
    review_tailored_cv: Optional[bool] = True
    review_before_portal_submission: Optional[bool] = True
    allow_unattended_submission: Optional[bool] = False
    daily_submission_limit: Optional[int] = 10
    allow_workday_account_creation: Optional[bool] = False
    review_before_email_send: Optional[bool] = True
    gmail_connected: Optional[bool] = False
    gmail_account_email: Optional[str] = None
    gmail_scopes_granted: Optional[List[str]] = None


class GmailConnectRequest(BaseModel):
    code_or_token: Optional[str] = None
    enable_inbox_access: bool = False
    test_email: Optional[str] = None


class IntakeMessageRequest(BaseModel):
    raw_text: str = Field(description="Pasted or forwarded message text from WhatsApp, LinkedIn, or Gmail alerts")
    source: str = Field(default="whatsapp", description="'whatsapp', 'linkedin_post', 'gmail_alert', 'social_post'")
    sender_info: Optional[str] = None


class ApproveEmailRequest(BaseModel):
    recipient_email: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None


class PreviewRequest(BaseModel):
    locations: Optional[List[str]] = None
    location_mode: Optional[str] = "prioritize"  # "filter" or "prioritize"
    work_arrangements: Optional[List[str]] = None
    unattended_include_lower_ranked: Optional[bool] = False


class QueueJobsRequest(BaseModel):
    selected_jobs: List[Dict[str, Any]]
    save_rule: Optional[bool] = False


class ResolveNeedsInputRequest(BaseModel):
    action: str = Field(description="'approve' or 'dismiss'")


class AnswerBankUpdateRequest(BaseModel):
    answers: List[Dict[str, Any]]
    rule_answers: Optional[Dict[str, List[Dict[str, Any]]]] = None


class AnswerQuestionRequest(BaseModel):
    answer_text: str = Field(description="Answer text or option label")
    scope: Optional[str] = Field(default="save_as_default", description="'use_once', 'save_for_rule', 'save_as_default', 'ask_every_time'")
    selected_option: Optional[str] = None


class ProcessQueueRequest(BaseModel):
    mock_form_catalog: Optional[Dict[str, List[Dict[str, Any]]]] = None
    rule_overrides: Optional[Dict[str, bool]] = None


class VerifySubmissionRequest(BaseModel):
    action: str = Field(default="confirm_received", description="'confirm_received' or 'confirm_not_received'")


class ReportAppliedRequest(BaseModel):
    confirmation_ref: Optional[str] = None
    notes: Optional[str] = ""


class SubmitPortalRequest(BaseModel):
    mock_simulated_outcome: Optional[str] = None


# --- Endpoints ---

@router.get("/setup")
def get_setup(request: Request):
    """
    Returns saved editable defaults (themes, target experience)
    along with profile-derived suggestions.
    """
    user_id = _resolve_user_id(request)
    defaults = get_auto_apply_defaults(user_id)
    suggestions = get_profile_suggestions(user_id)

    return {
        "status": "success",
        "defaults": defaults,
        "profile_suggestions": suggestions,
    }


@router.put("/setup")
def update_setup(payload: AutoApplySetupUpdate, request: Request):
    """Saves editable defaults (themes, experience range) for future runs."""
    user_id = _resolve_user_id(request)
    current = get_auto_apply_defaults(user_id)

    current["role_themes"] = payload.role_themes
    current["min_experience_years"] = payload.min_experience_years
    current["max_experience_years"] = payload.max_experience_years
    if payload.preferred_locations is not None:
        current["preferred_locations"] = payload.preferred_locations
    if payload.work_arrangements is not None:
        current["work_arrangements"] = payload.work_arrangements
    if payload.location_mode is not None:
        current["location_mode"] = payload.location_mode
    if payload.unattended_include_lower_ranked is not None:
        current["unattended_include_lower_ranked"] = payload.unattended_include_lower_ranked
    if payload.auto_queue_future_matches is not None:
        current["auto_queue_future_matches"] = payload.auto_queue_future_matches
    if payload.review_tailored_cv is not None:
        current["review_tailored_cv"] = payload.review_tailored_cv
    if payload.review_before_portal_submission is not None:
        current["review_before_portal_submission"] = payload.review_before_portal_submission
    if payload.allow_unattended_submission is not None:
        current["allow_unattended_submission"] = payload.allow_unattended_submission
    if payload.daily_submission_limit is not None:
        current["daily_submission_limit"] = payload.daily_submission_limit
    if payload.allow_workday_account_creation is not None:
        current["allow_workday_account_creation"] = payload.allow_workday_account_creation

    save_auto_apply_defaults(user_id, current)
    return {
        "status": "success",
        "message": "Auto Apply defaults updated successfully.",
        "defaults": current,
    }


@router.post("/preview")
def preview_matching_jobs(payload: PreviewRequest, request: Request, db: Session = Depends(get_db)):
    """
    Computes preview of matching jobs before starting queue:
    - Filters/prioritizes by location for this specific run.
    - Leaves saved themes and experience defaults intact!
    - Deduplicates cross-posted listings.
    - Excludes previously applied tracker roles.
    - Flags missing or ambiguous details.
    """
    user_id = _resolve_user_id(request)
    preview = generate_auto_apply_preview(
        user_id=user_id,
        run_locations=payload.locations,
        location_mode=payload.location_mode,
        run_work_arrangements=payload.work_arrangements,
        unattended_include_lower_ranked=payload.unattended_include_lower_ranked,
        db=db,
    )
    return preview


@router.get("/queue")
def get_queue(request: Request):
    """Returns persistent queue state, items, and chat-style activity feed."""
    user_id = _resolve_user_id(request)
    queue = get_queue_data(user_id)
    return {
        "status": "success",
        "queue": queue,
    }


@router.post("/queue")
def queue_jobs(payload: QueueJobsRequest, request: Request):
    """Adds preview-selected jobs into the persistent application queue."""
    if not payload.selected_jobs:
        raise HTTPException(status_code=400, detail="No jobs selected for queuing.")

    user_id = _resolve_user_id(request)
    res = add_jobs_to_queue(user_id, payload.selected_jobs)

    # If save_rule requested, persist auto_queue_future_matches
    if payload.save_rule:
        defaults = get_auto_apply_defaults(user_id)
        defaults["auto_queue_future_matches"] = True
        save_auto_apply_defaults(user_id, defaults)

    return res


@router.post("/queue/pause")
def pause_queue(request: Request):
    """Pauses the application queue."""
    user_id = _resolve_user_id(request)
    return set_queue_paused_state(user_id, paused=True)


@router.post("/queue/resume")
def resume_queue(request: Request):
    """Resumes the application queue."""
    user_id = _resolve_user_id(request)
    return set_queue_paused_state(user_id, paused=False)


@router.post("/queue/{item_id}/resolve")
def resolve_needs_input(item_id: str, payload: ResolveNeedsInputRequest, request: Request):
    """Resolves a job flagged under 'Needs your input' by approving or dismissing it."""
    user_id = _resolve_user_id(request)
    try:
        return resolve_needs_input_item(user_id, item_id, payload.action)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Phase 2 Endpoints: Answer Bank & Assisted Form Filling ---

@router.get("/answer-bank")
def get_user_answer_bank(request: Request):
    """Returns candidate Answer Bank seeded with core application question categories."""
    user_id = _resolve_user_id(request)
    bank = get_answer_bank(user_id)
    return {
        "status": "success",
        "answer_bank": bank
    }


@router.put("/answer-bank")
def update_user_answer_bank(payload: AnswerBankUpdateRequest, request: Request):
    """Updates candidate Answer Bank with customized questions, categories, and answers."""
    user_id = _resolve_user_id(request)
    bank = get_answer_bank(user_id)
    bank["answers"] = payload.answers
    if payload.rule_answers is not None:
        bank["rule_answers"] = payload.rule_answers
    saved = save_answer_bank(user_id, bank)
    return {
        "status": "success",
        "message": "Answer Bank updated successfully.",
        "answer_bank": saved
    }


@router.post("/queue/process")
def process_queue_fill(payload: Optional[ProcessQueueRequest] = None, request: Request = None):
    """
    Executes an application cycle across active queued jobs (Phase 2 & Phase 3):
    1. Tailors separate CV for LinkedIn/Portals/Email (skips for iimjobs/Naukri).
    2. Checkpoint 1 (Review Tailored CV): pauses at 'waiting_cv_review' if ON; auto-advances if OFF.
    3. Form Filling with Answer Bank: pauses at 'needs_answer' if unfamiliar required questions.
    4. Checkpoint 2 (Review Before Submission): pauses at 'waiting_submission_review' if ON; auto-advances if OFF.
    """
    user_id = _resolve_user_id(request)
    mock_catalog = payload.mock_form_catalog if payload else None
    rule_overrides = payload.rule_overrides if payload else None
    return process_queue_with_approvals(user_id, mock_catalog, rule_overrides)


@router.post("/queue/{item_id}/approve-cv")
def approve_cv(item_id: str, request: Request):
    """Candidate approves tailored CV at Checkpoint 1 and advances job."""
    user_id = _resolve_user_id(request)
    try:
        return approve_tailored_cv(user_id, item_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/queue/{item_id}/approve-submission")
def approve_submission(item_id: str, request: Request):
    """Candidate approves final application package at Checkpoint 2."""
    user_id = _resolve_user_id(request)
    try:
        return approve_portal_submission(user_id, item_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/queue/{item_id}/cv-preview")
def get_cv_preview(item_id: str, request: Request):
    """Returns tailored CV wording diff, page count, overflow status, and version."""
    user_id = _resolve_user_id(request)
    try:
        return get_tailored_cv_preview(user_id, item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/queue/{item_id}/answer")
def submit_question_answer(item_id: str, payload: AnswerQuestionRequest, request: Request):
    """
    Answers an unfamiliar required question for a paused job.
    Supports 4 scopes: 'use_once', 'save_for_rule', 'save_as_default', 'ask_every_time'.
    Resumes the job and advances it to 'ready_for_review'.
    """
    user_id = _resolve_user_id(request)
    try:
        return answer_pending_question(
            user_id=user_id,
            queue_item_id=item_id,
            answer_text=payload.answer_text,
            scope=payload.scope or "save_as_default",
            selected_option=payload.selected_option
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/queue/{item_id}/review")
def review_job_application(item_id: str, request: Request):
    """
    Fetches full form answers snapshot for manual inspection prior to submission.
    Submission remains strictly manual in Phase 2.
    """
    user_id = _resolve_user_id(request)
    try:
        return get_application_form_review(user_id, item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Phase 4 Endpoints: Portal Automation, Workday Accounts & Adapter Hand-offs ---

@router.post("/queue/{item_id}/submit-portal")
def portal_submit(item_id: str, payload: Optional[SubmitPortalRequest] = None, request: Request = None):
    """
    Executes automated company portal or Workday submission.
    Enforces 'Applied' status policy: marks Applied only after confirmation capture.
    If result is unclear, holds at 'submission_unclear' before retrying.
    """
    user_id = _resolve_user_id(request)
    queue = get_queue_data(user_id)
    target = next((item for item in queue["queue_items"] if item["queue_item_id"] == item_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Queue item '{item_id}' not found.")

    source = target.get("source", "")
    url = target.get("job_url", "")
    simulated_outcome = payload.mock_simulated_outcome if payload else None

    try:
        if "workday" in source.lower() or "myworkdayjobs" in url.lower():
            return execute_workday_flow(user_id, item_id, mock_checkpoint=simulated_outcome)
        elif "naukri" in source.lower() or "iimjobs" in source.lower() or "linkedin" in source.lower():
            return prepare_portal_handoff(user_id, item_id)
        else:
            return submit_to_company_portal(user_id, item_id, mock_simulated_outcome=simulated_outcome)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/queue/{item_id}/verify-unclear")
def verify_unclear_result(item_id: str, payload: VerifySubmissionRequest, request: Request):
    """
    Verifies an unclear/timed out submission with employer portal before permitting any retry.
    """
    user_id = _resolve_user_id(request)
    try:
        return verify_unclear_submission(user_id, item_id, payload.action)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/queue/{item_id}/resume-checkpoint")
def resume_checkpoint(item_id: str, request: Request):
    """
    Resumes a Workday or portal job paused for human interaction (CAPTCHA, MFA, declaration).
    """
    user_id = _resolve_user_id(request)
    try:
        return resume_human_checkpoint(user_id, item_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/queue/{item_id}/handoff")
def get_handoff(item_id: str, request: Request):
    """
    Prepares a clean handoff package for portals where automated actions are unsupported (Naukri, iimjobs, LinkedIn).
    """
    user_id = _resolve_user_id(request)
    try:
        return prepare_portal_handoff(user_id, item_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/queue/{item_id}/report-applied")
def report_applied(item_id: str, payload: ReportAppliedRequest, request: Request):
    """
    Candidate reports manual submission (via portal handoff or external application).
    Marks the application as 'Applied' in the tracker and records confirmation details.
    """
    user_id = _resolve_user_id(request)
    try:
        return report_manual_submission(user_id, item_id, payload.confirmation_ref, payload.notes or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Phase 5 Routes ─────────────────────────────────────────────────────────

@router.post("/gmail/connect")
def connect_gmail_route(payload: GmailConnectRequest, request: Request):
    """
    Connects Gmail account using Google OAuth.
    Requests drafting/sending scope and optional inbox access for alert intake & Workday verification.
    """
    user_id = _resolve_user_id(request)
    try:
        return connect_gmail_account(
            user_id=user_id,
            code_or_token=payload.code_or_token,
            enable_inbox_access=payload.enable_inbox_access,
            test_email=payload.test_email
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/gmail/disconnect")
def disconnect_gmail_route(request: Request):
    """Disconnects Gmail account."""
    user_id = _resolve_user_id(request)
    try:
        return disconnect_gmail_account(user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/gmail/status")
def get_gmail_status_route(request: Request):
    """Retrieves Gmail connection status, email address, and granted scopes."""
    user_id = _resolve_user_id(request)
    return get_gmail_status(user_id)


@router.post("/intake/message")
def ingest_message_route(payload: IntakeMessageRequest, request: Request):
    """
    Ingests forwarded WhatsApp messages, shared LinkedIn posts, or Gmail alerts.
    Extracts role, company, recipient email, and instructions.
    Evaluates against Phase 1 theme/location rules, routing incomplete items to 'Needs Input'.
    """
    user_id = _resolve_user_id(request)
    try:
        return parse_and_ingest_message(
            user_id=user_id,
            raw_text=payload.raw_text,
            source=payload.source,
            sender_info=payload.sender_info
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/queue/{item_id}/draft-email")
def draft_email_route(item_id: str, request: Request):
    """
    Drafts tailored email application with job-specific PDF CV attached.
    Pauses for review when review_before_email_send is ON or when hiring-manager outreach is detected.
    """
    user_id = _resolve_user_id(request)
    try:
        return draft_email_application(user_id, item_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/queue/{item_id}/approve-email")
def approve_email_route(item_id: str, payload: ApproveEmailRequest, request: Request):
    """
    Candidate approves sending email application.
    Checks duplicates, delivers email via Gmail integration, and records in tracker as 'Applied by email'.
    """
    user_id = _resolve_user_id(request)
    try:
        overrides = {}
        if payload.recipient_email:
            overrides["recipient_email"] = payload.recipient_email
        if payload.subject:
            overrides["subject"] = payload.subject
        if payload.body:
            overrides["body"] = payload.body
        return approve_and_send_email(user_id, item_id, overrides or None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
