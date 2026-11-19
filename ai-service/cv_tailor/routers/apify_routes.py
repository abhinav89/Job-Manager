"""
Private Apify Jobs Router for Job-Manager.
Restricted strictly to allowlisted executive accounts (Abhinav and Shivangi)
with server-verified HMAC session tokens, isolated storage, and theme-level matching.
"""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, Header, Request

from cv_tailor.services.apify_service import (
    ALLOWED_APIFY_ACCOUNTS,
    create_apify_token,
    verify_apify_token,
    get_user_profile,
    save_user_profile,
    get_user_jobs,
    get_user_alerts,
    save_user_alerts,
    run_apify_scheduled_scrape,
    get_budget_ledger,
)

logger = logging.getLogger("apify-routes")

router = APIRouter(prefix="/apify", tags=["apify-private"])


# --- Server-Side Verification Dependency ---

def get_current_apify_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Enforces server-verified authentication for all private Apify endpoints.
    A browser-supplied email header alone is explicitly rejected.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide a valid server-verified Apify session token."
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    payload = verify_apify_token(token)
    if not payload:
        raise HTTPException(
            status_code=403,
            detail="Invalid or expired Apify session token. Access is restricted to authorized accounts."
        )

    return payload


# --- Models ---

class AuthVerifyRequest(BaseModel):
    email: str
    passcode: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    location_mode: Optional[str] = None
    selected_cities: Optional[List[str]] = None
    include_remote_india: Optional[bool] = None
    remote_only: Optional[bool] = None
    compensation_target: Optional[str] = None
    compensation_benchmark: Optional[str] = None
    themes: Optional[List[Dict[str, Any]]] = None


class AssignThemeResumeRequest(BaseModel):
    theme_id: str
    active_resume_filename: str
    active_resume_version: str = "v1"


# --- Endpoints ---

@router.post("/auth/verify")
def verify_and_login(req: AuthVerifyRequest):
    """
    Server-verified authentication for Apify.
    Validates user identity against allowlist and issues an HMAC-signed session token.
    """
    normalized_email = req.email.strip().lower()
    
    # Check allowlist
    user_id = ALLOWED_APIFY_ACCOUNTS.get(normalized_email)
    if not user_id:
        # Check username match
        uname = normalized_email.split("@")[0]
        user_id = ALLOWED_APIFY_ACCOUNTS.get(uname)

    if not user_id:
        raise HTTPException(
            status_code=403,
            detail="Access restricted. Apify Job Matches is a private executive feature enabled only for Abhinav and Shivangi."
        )

    # Issue server-signed token
    token = create_apify_token(normalized_email, user_id)
    profile = get_user_profile(user_id)

    return {
        "status": "success",
        "token": token,
        "user_id": user_id,
        "display_name": profile.get("display_name", user_id.title()),
        "email": normalized_email,
        "message": f"Welcome {profile.get('display_name')}. Private Apify session verified."
    }


@router.get("/profile")
def get_apify_profile(user: Dict[str, Any] = Depends(get_current_apify_user)):
    """Returns the authenticated user's private Apify profile and theme configuration."""
    profile = get_user_profile(user["user_id"])
    return {
        "status": "success",
        "profile": profile
    }


@router.put("/profile")
def update_apify_profile(req: UpdateProfileRequest, user: Dict[str, Any] = Depends(get_current_apify_user)):
    """Updates themes, location preferences, and compensation benchmarks."""
    profile = get_user_profile(user["user_id"])
    
    if req.location_mode is not None:
        profile["location_mode"] = req.location_mode
    if req.selected_cities is not None:
        profile["selected_cities"] = req.selected_cities
    if req.include_remote_india is not None:
        profile["include_remote_india"] = req.include_remote_india
    if req.remote_only is not None:
        profile["remote_only"] = req.remote_only
    if req.compensation_target is not None:
        profile["compensation_target"] = req.compensation_target
    if req.compensation_benchmark is not None:
        profile["compensation_benchmark"] = req.compensation_benchmark
    if req.themes is not None:
        profile["themes"] = req.themes

    save_user_profile(user["user_id"], profile)
    return {
        "status": "success",
        "profile": profile,
        "message": "Preferences saved successfully."
    }


@router.post("/theme-resume")
def assign_theme_resume(req: AssignThemeResumeRequest, user: Dict[str, Any] = Depends(get_current_apify_user)):
    """Assigns or updates an active resume version for a specific theme."""
    profile = get_user_profile(user["user_id"])
    updated = False

    for t in profile.get("themes", []):
        if t["id"] == req.theme_id:
            t["active_resume_filename"] = req.active_resume_filename
            t["active_resume_version"] = req.active_resume_version
            t["status"] = "Active"
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Theme not found.")

    save_user_profile(user["user_id"], profile)
    return {
        "status": "success",
        "message": f"Resume assigned to theme {req.theme_id}.",
        "profile": profile
    }


@router.get("/jobs")
def get_apify_jobs(
    theme_id: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_apify_user)
):
    """
    Returns private Apify matches with ranked shortlists:
    - Hyderabad (up to 5 now, configurable to 20)
    - Other India & Remote (up to 1 now, configurable to 5)
    """
    all_jobs = get_user_jobs(user["user_id"])
    profile = get_user_profile(user["user_id"])

    # If theme_id is specified, filter by that theme
    if theme_id and theme_id != "all":
        filtered_jobs = [
            j for j in all_jobs
            if any(m.get("theme_id") == theme_id for m in j.get("theme_matches", []))
        ]
    else:
        filtered_jobs = all_jobs

    # Shortlists
    hyderabad_matches = [j for j in filtered_jobs if j.get("is_hyderabad")]
    other_india_matches = [j for j in filtered_jobs if not j.get("is_hyderabad")]

    return {
        "status": "success",
        "total_matches": len(filtered_jobs),
        "hyderabad_matches": hyderabad_matches[:5],
        "other_india_matches": other_india_matches[:1],
        "all_matches": filtered_jobs,
        "themes": profile.get("themes", []),
        "compensation_benchmark": profile.get("compensation_target") or profile.get("compensation_benchmark", "Undisclosed")
    }


@router.get("/alerts")
def get_apify_alerts(user: Dict[str, Any] = Depends(get_current_apify_user)):
    """Returns private notification alerts for newly qualified openings."""
    alerts = get_user_alerts(user["user_id"])
    return {
        "status": "success",
        "total": len(alerts),
        "unread_count": sum(1 for a in alerts if not a.get("read")),
        "alerts": alerts[:30]
    }


@router.post("/alerts/mark-read")
def mark_alerts_read(user: Dict[str, Any] = Depends(get_current_apify_user)):
    """Marks all user alerts as read."""
    alerts = get_user_alerts(user["user_id"])
    for a in alerts:
        a["read"] = True
    save_user_alerts(user["user_id"], alerts)
    return {"status": "success", "message": "All alerts marked as read."}


@router.post("/run-now")
def trigger_live_test(user: Dict[str, Any] = Depends(get_current_apify_user)):
    """
    Triggers a manual, capped single-run test (max 5 postings)
    for the verified user to validate Actor fetching, rotation, and theme matching.
    """
    result = run_apify_scheduled_scrape(user["user_id"], is_test=True)
    return {
        "status": "success",
        "telemetry": result
    }


@router.post("/cron-trigger")
def trigger_scheduled_cron(
    request: Request,
    x_cron_secret: Optional[str] = Header(None)
):
    """
    Called by GitHub Actions scheduled workflow twice daily (00:30 UTC & 12:30 UTC / 6 AM & 6 PM IST).
    Iterates over Abhinav and Shivangi profiles, enforces 5 postings/run limit,
    checks budget ceiling, and sends private alerts.
    """
    expected_secret = os.getenv("CRON_SECRET", "dealos-cron-secret-2026")
    if x_cron_secret != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid cron authorization secret.")

    results = {}
    for user_id in ["abhinav", "shivangi"]:
        try:
            res = run_apify_scheduled_scrape(user_id, is_test=False)
            results[user_id] = res
        except Exception as e:
            logger.exception(f"Scheduled Apify run failed for {user_id}: {e}")
            results[user_id] = {"status": "error", "message": str(e)}

    return {
        "status": "completed",
        "timestamp": os.getenv("GITHUB_RUN_ID", "scheduled_run"),
        "results": results,
        "budget_ledger": get_budget_ledger()
    }
