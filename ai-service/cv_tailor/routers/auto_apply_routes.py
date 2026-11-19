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
    Executes a form-filling cycle across active queued jobs.
    Pauses any job encountering unfamiliar required questions ('needs_answer')
    while allowing other eligible jobs in the queue to continue to 'ready_for_review'.
    """
    user_id = _resolve_user_id(request)
    mock_catalog = payload.mock_form_catalog if payload else None
    return process_queue_form_filling(user_id, mock_catalog)


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
