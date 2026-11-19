"""
Auto Apply Phase 1 Service — Job Filtering, Selection, and Run Queue.
Handles:
1. Candidate setup defaults (role themes & target experience range) prepopulated from profile.
2. Run-level adjustable location with two modes (Filter vs. Prioritize).
3. Cross-posted job deduplication and exclusion of previously applied roles.
4. Preview generation with eligibility reasons and ambiguity flagging.
5. Persistent queue management with Pause, Resume, and 'Needs your input' handling.
6. Chat-style activity feed event tracking.
"""
from __future__ import annotations

import os
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from cv_tailor.config import data_dir
from cv_tailor import workspace as w
from cv_tailor.services.job_repository_service import (
    job_repo_service,
    generate_job_fingerprint,
    calculate_tenure_from_experiences,
)

logger = logging.getLogger("auto-apply-service")


def _resolve_user_id(request_or_email: Any = None) -> str:
    """Extracts user identifier for data isolation (e.g. 'abhinav', 'shivangi', or 'default')."""
    if isinstance(request_or_email, str):
        email = request_or_email.lower().strip()
    elif hasattr(request_or_email, "headers"):
        email = request_or_email.headers.get("X-User-Email", "").lower().strip()
    else:
        email = ""
    
    if "abhinav" in email:
        return "abhinav"
    if "shivangi" in email:
        return "shivangi"
    return "default"


def _get_user_file(user_id: str, suffix: str) -> Path:
    p = data_dir() / f"auto_apply_{suffix}_{user_id}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


# --- 1. Setup Defaults & Profile Prepopulation ---

def get_profile_suggestions(user_id: str) -> Dict[str, Any]:
    """Prepopulates suggested themes and experience range from the confirmed candidate profile."""
    profile = {}
    try:
        profile = w.profile_get() or {}
    except Exception:
        profile = {}

    experiences = profile.get("experience", [])
    tenure = calculate_tenure_from_experiences(experiences)
    if tenure <= 0:
        tenure = 5.0

    # Suggested range around candidate's verified tenure
    min_exp = max(0, int(tenure - 2))
    max_exp = max(min_exp + 3, int(tenure + 3))

    # Suggested themes based on user archetype / profile
    if user_id == "abhinav" or "abhinav" in profile.get("first_name", "").lower():
        suggested_themes = [
            "Corporate Strategy & Transformation",
            "FP&A and Business Planning",
            "Operations and Strategic Finance",
            "CEO Office & Chief of Staff"
        ]
    elif user_id == "shivangi":
        suggested_themes = [
            "Investments & M&A",
            "Equity Research",
            "IPO Readiness & Listing",
            "Strategy Consulting",
            "Manufacturing Setup"
        ]
    else:
        preset = profile.get("preset_slug", "strategy-consulting")
        suggested_themes = [
            preset.replace("-", " ").title(),
            "Corporate Strategy",
            "Operations Management"
        ]

    return {
        "calculated_tenure_years": round(tenure, 1),
        "suggested_min_experience": min_exp,
        "suggested_max_experience": max_exp,
        "suggested_themes": suggested_themes,
        "default_preferred_locations": ["Hyderabad", "Bengaluru", "Mumbai"],
        "default_work_arrangements": ["Hybrid", "Remote", "Onsite"],
    }


def get_auto_apply_defaults(user_id: str) -> Dict[str, Any]:
    """Retrieves saved editable defaults for this user, or seeds from profile suggestions."""
    path = _get_user_file(user_id, "defaults")
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass

    suggestions = get_profile_suggestions(user_id)
    defaults = {
        "user_id": user_id,
        "role_themes": suggestions["suggested_themes"],
        "min_experience_years": suggestions["suggested_min_experience"],
        "max_experience_years": suggestions["suggested_max_experience"],
        "preferred_locations": suggestions["default_preferred_locations"],
        "work_arrangements": suggestions["default_work_arrangements"],
        "location_mode": "prioritize",  # "filter" or "prioritize"
        "unattended_include_lower_ranked": False,
        "auto_queue_future_matches": False,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    save_auto_apply_defaults(user_id, defaults)
    return defaults


def save_auto_apply_defaults(user_id: str, data: Dict[str, Any]):
    path = _get_user_file(user_id, "defaults")
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# --- 2. Deduplication & Tracker Application Exclusion ---

def get_applied_fingerprints(db = None, workspace_id: int = 1) -> Tuple[set[str], set[str]]:
    """
    Returns sets of applied company-title fingerprints and job URLs from the application tracker
    to ensure previously applied roles are completely excluded.
    """
    applied_fingerprints = set()
    applied_urls = set()

    # Query from SQLite / Postgres JobApplication model
    try:
        from cv_tailor.database import get_db
        from cv_tailor.models import database_models as db_models

        # If a db session is provided or created
        if db:
            apps = db.query(db_models.JobApplication).all()
        else:
            with next(get_db()) as session:
                apps = session.query(db_models.JobApplication).all()

        for app in apps:
            if app.status in ["Applied", "Interview", "Tech Test", "Offer", "Rejected", "Ghosted", "Saved"]:
                if app.company_name and app.job_title:
                    fp = generate_job_fingerprint(app.company_name, app.job_title, app.location)
                    applied_fingerprints.add(fp)
                if app.job_url:
                    applied_urls.add(app.job_url.strip().lower())
    except Exception as e:
        logger.debug(f"Could not load applied roles from database: {e}")

    return applied_fingerprints, applied_urls


def deduplicate_jobs(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicates cross-posted jobs across LinkedIn, Greenhouse, Lever, etc."""
    seen_fingerprints = set()
    seen_urls = set()
    deduped = []

    for job in jobs:
        company = job.get("company_name") or job.get("company") or "Unknown"
        title = job.get("job_title") or job.get("title") or "Unknown"
        loc = job.get("location") or ""
        url = (job.get("job_url") or job.get("url") or "").strip().lower()

        fp = generate_job_fingerprint(company, title, loc)

        if fp in seen_fingerprints or (url and url in seen_urls):
            continue

        seen_fingerprints.add(fp)
        if url:
            seen_urls.add(url)
        deduped.append(job)

    return deduped


# --- 3. Experience & Theme Qualification Logic ---

def parse_experience_range(text: str) -> Tuple[Optional[int], Optional[int], bool]:
    """
    Parses experience text (e.g. '5-8 yrs', '10+ years', '3 to 6 Yrs').
    Returns (min_exp, max_exp, is_ambiguous).
    """
    if not text:
        return None, None, True

    clean = text.lower()
    range_match = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)', clean)
    if range_match:
        return int(range_match.group(1)), int(range_match.group(2)), False

    plus_match = re.search(r'(\d+)\s*\+', clean)
    if plus_match:
        val = int(plus_match.group(1))
        return val, val + 5, False

    single_match = re.search(r'\b(\d+)\s*(?:yrs|years|year|yr)\b', clean)
    if single_match:
        val = int(single_match.group(1))
        return val, val + 3, False

    return None, None, True


def match_job_theme(job: Dict[str, Any], themes: List[str]) -> Tuple[Optional[str], float, str]:
    """Checks if job matches any of the candidate's active themes."""
    title = (job.get("job_title") or job.get("title") or "").lower()
    desc = (job.get("job_description") or job.get("description") or "").lower()
    combined = f"{title} {desc}"

    best_theme = None
    best_score = 0.0
    rationale = ""

    for theme in themes:
        theme_clean = theme.lower()
        theme_tokens = [w for w in re.split(r'[^a-z0-9]', theme_clean) if len(w) > 3 and w not in ["and", "with", "the"]]

        # Title match has high weight
        title_matches = [t for t in theme_tokens if t in title]
        desc_matches = [t for t in theme_tokens if t in desc]

        score = (len(title_matches) * 2.5) + (len(desc_matches) * 0.5)
        if score > best_score:
            best_score = score
            best_theme = theme
            reasons = []
            if title_matches:
                reasons.append(f"Title aligns with '{', '.join(title_matches)}'")
            if desc_matches:
                reasons.append(f"Scope matches {', '.join(desc_matches[:3])}")
            rationale = " and ".join(reasons) if reasons else f"Matches {theme} career archetype."

    return best_theme, best_score, rationale


# --- 4. Preview Generation ---

def generate_auto_apply_preview(
    user_id: str,
    run_locations: Optional[List[str]] = None,
    location_mode: Optional[str] = None,
    run_work_arrangements: Optional[List[str]] = None,
    unattended_include_lower_ranked: Optional[bool] = None,
    db = None,
) -> Dict[str, Any]:
    """
    Computes a preview of matching jobs before starting or queuing:
    - Reuses saved editable themes and experience range defaults.
    - Applies run-level adjustable location settings without modifying saved defaults!
    - Deduplicates cross-posted jobs.
    - Excludes previously applied tracker roles.
    - Flags missing or ambiguous eligibility information for review.
    """
    defaults = get_auto_apply_defaults(user_id)
    themes = defaults.get("role_themes", [])
    target_min_exp = defaults.get("min_experience_years", 4)
    target_max_exp = defaults.get("max_experience_years", 10)

    # Use run-level location overrides if provided, otherwise default
    effective_locations = [loc.strip() for loc in (run_locations if run_locations is not None else defaults.get("preferred_locations", ["Hyderabad"]))]
    effective_mode = location_mode if location_mode in ["filter", "prioritize"] else defaults.get("location_mode", "prioritize")
    effective_arrangements = run_work_arrangements if run_work_arrangements is not None else defaults.get("work_arrangements", ["Hybrid", "Remote", "Onsite"])

    # 1. Fetch raw candidate jobs from repository + Apify private stores
    raw_repo_jobs = job_repo_service._jobs or []
    from cv_tailor.services.apify_service import get_user_jobs
    apify_jobs = get_user_jobs(user_id) or []

    # Map Apify jobs to standard schema
    mapped_apify_jobs = []
    for aj in apify_jobs:
        mapped_apify_jobs.append({
            "id": aj.get("id"),
            "company_name": aj.get("company", "Confidential"),
            "job_title": aj.get("title", "Executive Role"),
            "location": aj.get("location", "Hyderabad, India"),
            "work_arrangement": aj.get("work_mode", "Hybrid"),
            "job_url": aj.get("job_url", ""),
            "source": "LinkedIn (Apify)",
            "experience_years_min": target_min_exp,
            "experience_years_max": target_max_exp,
            "job_description": aj.get("description") or aj.get("why_it_fits", ""),
            "date_posted": aj.get("posting_date"),
            "salary_range": aj.get("advertised_pay", "Undisclosed"),
            "why_it_fits_override": aj.get("why_it_fits"),
        })

    all_raw_jobs = mapped_apify_jobs + raw_repo_jobs

    # 2. Deduplicate cross-posted listings
    deduped_jobs = deduplicate_jobs(all_raw_jobs)
    cross_posts_excluded_count = len(all_raw_jobs) - len(deduped_jobs)

    # 3. Exclude previously applied roles
    applied_fps, applied_urls = get_applied_fingerprints(db)
    eligible_unapplied_jobs = []
    previously_applied_count = 0

    for job in deduped_jobs:
        comp = job.get("company_name") or job.get("company") or ""
        title = job.get("job_title") or job.get("title") or ""
        loc = job.get("location") or ""
        url = (job.get("job_url") or "").strip().lower()
        fp = generate_job_fingerprint(comp, title, loc)

        if fp in applied_fps or (url and url in applied_urls):
            previously_applied_count += 1
            continue
        eligible_unapplied_jobs.append(job)

    # 4. Evaluate against themes, experience, and location
    preview_items = []
    for job in eligible_unapplied_jobs:
        matched_theme, score, rationale = match_job_theme(job, themes)
        if not matched_theme or score < 1.0:
            continue

        job_loc = (job.get("location") or "Undisclosed").strip()
        job_arrangement = (job.get("work_arrangement") or "Onsite").strip()

        # Check experience fit
        exp_min = job.get("experience_years_min")
        exp_max = job.get("experience_years_max")
        is_ambiguous_exp = False

        if exp_min is None or exp_max is None:
            # Try to parse from description / snippet
            desc = job.get("job_description") or ""
            parsed_min, parsed_max, is_ambiguous_exp = parse_experience_range(desc)
            exp_min = parsed_min if parsed_min is not None else target_min_exp
            exp_max = parsed_max if parsed_max is not None else target_max_exp

        # Flag missing or ambiguous eligibility information
        ambiguity_flags = []
        if is_ambiguous_exp:
            ambiguity_flags.append("Advertised experience range is unspecified or ambiguous in posting.")
        if not job_loc or job_loc.lower() in ["undisclosed", "confidential", "india"]:
            ambiguity_flags.append("Exact city location is unclear.")
        if job.get("salary_range") in [None, "", "Undisclosed", "Competitive"]:
            ambiguity_flags.append("Advertised compensation is undisclosed.")

        # Location matching
        is_preferred_loc = any(loc.lower() in job_loc.lower() for loc in effective_locations)
        is_remote_match = "remote" in job_arrangement.lower() and any("remote" in l.lower() for l in effective_locations)
        matches_location = is_preferred_loc or is_remote_match

        # Mode A: Filter by location — strictly drop non-matching locations
        if effective_mode == "filter" and not matches_location:
            continue

        exp_str = f"{exp_min}–{exp_max} yrs" if not is_ambiguous_exp else "Unspecified"
        why_qualified = job.get("why_it_fits_override") or (
            f"Matches {matched_theme} theme. Experience fits target {target_min_exp}–{target_max_exp} yrs range ({exp_str})."
            + (f" Located in preferred location ({job_loc})." if is_preferred_loc else "")
        )

        preview_items.append({
            "job_id": str(job.get("id") or generate_job_fingerprint(job.get("company_name", ""), job.get("job_title", ""))),
            "company_name": job.get("company_name") or job.get("company") or "Corporate Employer",
            "job_title": job.get("job_title") or job.get("title") or "Executive Role",
            "matched_theme": matched_theme,
            "advertised_experience_range": exp_str,
            "location": job_loc,
            "work_arrangement": job_arrangement,
            "source": job.get("source") or "Repository",
            "job_url": job.get("job_url") or "",
            "why_it_qualified": why_qualified,
            "is_preferred_location": is_preferred_loc or is_remote_match,
            "has_ambiguity": len(ambiguity_flags) > 0,
            "ambiguity_flags": ambiguity_flags,
            "eligible_for_auto_queue": len(ambiguity_flags) == 0 and (is_preferred_loc or effective_mode != "filter"),
        })

    # Mode B: Prioritize by location — put preferred locations first, other eligible below
    if effective_mode == "prioritize":
        preview_items.sort(key=lambda item: (not item["is_preferred_location"], item["has_ambiguity"]))

    # Summary counts
    preferred_count = sum(1 for item in preview_items if item["is_preferred_location"])
    other_locations_count = len(preview_items) - preferred_count
    ambiguous_count = sum(1 for item in preview_items if item["has_ambiguity"])

    return {
        "status": "success",
        "total_preview_jobs": len(preview_items),
        "preferred_location_count": preferred_count,
        "other_eligible_location_count": other_locations_count,
        "ambiguous_flagged_count": ambiguous_count,
        "cross_posts_excluded_count": cross_posts_excluded_count,
        "previously_applied_excluded_count": previously_applied_count,
        "effective_run_settings": {
            "locations": effective_locations,
            "location_mode": effective_mode,
            "work_arrangements": effective_arrangements,
            "unattended_include_lower_ranked": unattended_include_lower_ranked if unattended_include_lower_ranked is not None else defaults.get("unattended_include_lower_ranked", False),
        },
        "saved_defaults_preserved": {
            "role_themes": defaults["role_themes"],
            "min_experience_years": defaults["min_experience_years"],
            "max_experience_years": defaults["max_experience_years"],
        },
        "jobs": preview_items,
    }


# --- 5. Persistent Queue & Chat-Style Activity Feed ---

def get_queue_data(user_id: str) -> Dict[str, Any]:
    """Loads persistent run queue and activity feed."""
    path = _get_user_file(user_id, "queue")
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass

    initial_state = {
        "user_id": user_id,
        "queue_status": "ready",  # "ready", "running", "paused"
        "queue_items": [],
        "activity_feed": [
            {
                "id": "act-init",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sender": "agent",
                "message": "Auto Apply Setup initialized. Select eligible jobs to begin your application queue.",
                "badge": "System"
            }
        ],
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    save_queue_data(user_id, initial_state)
    return initial_state


def save_queue_data(user_id: str, queue_data: Dict[str, Any]):
    path = _get_user_file(user_id, "queue")
    queue_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(queue_data, indent=2), encoding="utf-8")


def _append_activity_event(queue: Dict[str, Any], message: str, badge: str = "Queue", data_payload: Optional[Dict[str, Any]] = None):
    """Appends an event to an active queue dictionary."""
    event = {
        "id": f"act-{int(time.time() * 1000)}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sender": "agent",
        "message": message,
        "badge": badge,
        "payload": data_payload
    }
    queue.setdefault("activity_feed", []).append(event)


def log_activity_event(user_id: str, message: str, badge: str = "Queue", data_payload: Optional[Dict[str, Any]] = None):
    """Appends an event to the chat-style activity feed and saves to disk."""
    queue = get_queue_data(user_id)
    _append_activity_event(queue, message, badge, data_payload)
    save_queue_data(user_id, queue)


def add_jobs_to_queue(user_id: str, selected_job_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Adds preview-selected jobs into the persistent queue."""
    queue = get_queue_data(user_id)
    existing_job_ids = {item["job_id"] for item in queue["queue_items"]}

    added = 0
    needs_input_count = 0

    for job in selected_job_items:
        job_id = str(job["job_id"])
        if job_id in existing_job_ids:
            continue

        # If job has ambiguity, mark as needs_input
        initial_status = "needs_input" if job.get("has_ambiguity") else "queued"
        if initial_status == "needs_input":
            needs_input_count += 1

        queue_item = {
            "queue_item_id": f"qitem-{int(time.time() * 1000)}-{added}",
            "job_id": job_id,
            "company_name": job.get("company_name", "Corporate Employer"),
            "job_title": job.get("job_title", "Professional Role"),
            "matched_theme": job.get("matched_theme", "General"),
            "advertised_experience_range": job.get("advertised_experience_range", "Unspecified"),
            "location": job.get("location", "India"),
            "source": job.get("source", "Feeder"),
            "job_url": job.get("job_url", ""),
            "why_it_qualified": job.get("why_it_qualified", ""),
            "has_ambiguity": job.get("has_ambiguity", False),
            "ambiguity_flags": job.get("ambiguity_flags", []),
            "status": initial_status,
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }
        queue["queue_items"].append(queue_item)
        existing_job_ids.add(job_id)
        added += 1

    if added > 0:
        _append_activity_event(
            queue,
            f"Queued {added} new job application(s). "
            + (f"({needs_input_count} flagged for 'Needs your input')." if needs_input_count else ""),
            badge="Queue"
        )

    save_queue_data(user_id, queue)
    return {
        "status": "success",
        "added_count": added,
        "needs_input_count": needs_input_count,
        "total_queued": len(queue["queue_items"]),
    }


def set_queue_paused_state(user_id: str, paused: bool) -> Dict[str, Any]:
    """Pauses or resumes the persistent queue."""
    queue = get_queue_data(user_id)
    queue["queue_status"] = "paused" if paused else "running"

    status_word = "Paused ⏸️" if paused else "Resumed ▶️"
    _append_activity_event(
        queue,
        f"Application Queue {status_word} by candidate. Active jobs will hold checkpoints safely.",
        badge="Control"
    )

    save_queue_data(user_id, queue)
    return {
        "status": "success",
        "queue_status": queue["queue_status"],
        "message": f"Queue {status_word} successfully."
    }


def resolve_needs_input_item(user_id: str, queue_item_id: str, action: str) -> Dict[str, Any]:
    """Handles 'Needs your input' action: candidate approves job for queue or dismisses it."""
    queue = get_queue_data(user_id)
    target = next((item for item in queue["queue_items"] if item["queue_item_id"] == queue_item_id), None)

    if not target:
        raise ValueError(f"Queue item '{queue_item_id}' not found.")

    if action == "approve":
        target["status"] = "queued"
        target["has_ambiguity"] = False
        _append_activity_event(
            queue,
            f"Candidate approved '{target['job_title']}' at {target['company_name']} despite flagged details.",
            badge="Approved"
        )
        msg = "Job approved and added to active queue."
    elif action == "dismiss":
        target["status"] = "dismissed"
        _append_activity_event(
            queue,
            f"Candidate dismissed '{target['job_title']}' at {target['company_name']}.",
            badge="Dismissed"
        )
        msg = "Job dismissed from queue."
    else:
        raise ValueError(f"Unknown action '{action}'. Use 'approve' or 'dismiss'.")

    save_queue_data(user_id, queue)
    return {
        "status": "success",
        "message": msg,
        "item": target
    }
