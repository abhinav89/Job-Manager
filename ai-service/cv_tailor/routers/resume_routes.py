"""
Resume and Profile Theme Management Routes for Job-Manager.
Enables candidates to manage multiple resumes categorized by career themes/archetypes
(Sales, BD, Product, Tech Engineer, Marketing, Finance, Operations, Supply Chain, HR, Strategy & Transformation).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from cv_tailor.config import data_dir
from cv_tailor import workspace as w

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["resumes"])

DEFAULT_THEMES = [
    {
        "id": "strategy-transformation",
        "name": "Strategy & Transformation",
        "category": "Corporate & Consulting",
        "icon": "Briefcase",
        "description": "Chief of Staff, Corporate Strategy, Management Consulting, Business Transformation",
        "target_roles": ["Strategy Manager", "Chief of Staff", "Transformation Lead", "Management Consultant"],
        "recommended_template": "classic",
        "is_custom": False,
    },
    {
        "id": "finance",
        "name": "Finance & FP&A",
        "category": "Corporate Finance",
        "icon": "DollarSign",
        "description": "Corporate Finance, FP&A, Financial Modeling, Valuation, Controllership",
        "target_roles": ["Finance Manager", "FP&A Lead", "Corporate Finance Specialist", "Investment Associate"],
        "recommended_template": "modern",
        "is_custom": False,
    },
    {
        "id": "product",
        "name": "Product Management",
        "category": "Product & Innovation",
        "icon": "Sparkles",
        "description": "Product Strategy, Technical PM, Product Roadmaps, GTM, Agile & Scrum",
        "target_roles": ["Product Manager", "Senior PM", "Head of Product", "Technical Product Manager"],
        "recommended_template": "minimal",
        "is_custom": False,
    },
    {
        "id": "tech-engineer",
        "name": "Tech & Software Engineering",
        "category": "Engineering & Technology",
        "icon": "Code",
        "description": "Full Stack, Backend, Cloud Architecture, DevOps, Data Systems",
        "target_roles": ["Full Stack Engineer", "Backend Developer", "Tech Lead", "Software Architect"],
        "recommended_template": "technical",
        "is_custom": False,
    },
    {
        "id": "sales",
        "name": "Enterprise Sales",
        "category": "Commercial & Revenue",
        "icon": "TrendingUp",
        "description": "Enterprise Sales, Account Executive, Sales Leadership, Revenue Growth",
        "target_roles": ["Account Executive", "Sales Manager", "VP of Sales", "Enterprise Sales Lead"],
        "recommended_template": "classic",
        "is_custom": False,
    },
    {
        "id": "bd",
        "name": "Business Development & Partnerships",
        "category": "Commercial & Partnerships",
        "icon": "Handshake",
        "description": "Strategic Alliances, Channel Growth, Commercial Partnerships, Market Entry",
        "target_roles": ["Director of BD", "Partnerships Lead", "Business Development Manager"],
        "recommended_template": "classic",
        "is_custom": False,
    },
    {
        "id": "operations",
        "name": "Operations & BizOps",
        "category": "Operations & Process",
        "icon": "Cpu",
        "description": "BizOps, Operational Excellence, Process Improvement, Automation",
        "target_roles": ["Operations Manager", "BizOps Lead", "Director of Operations"],
        "recommended_template": "modern",
        "is_custom": False,
    },
    {
        "id": "supply-chain",
        "name": "Supply Chain & Logistics",
        "category": "Operations & Logistics",
        "icon": "Truck",
        "description": "Global Procurement, Logistics, Vendor Management, SCM",
        "target_roles": ["Supply Chain Manager", "Procurement Lead", "Logistics Director"],
        "recommended_template": "classic",
        "is_custom": False,
    },
    {
        "id": "marketing",
        "name": "Marketing & Growth",
        "category": "Growth & Marketing",
        "icon": "Megaphone",
        "description": "Growth Marketing, Brand Strategy, Performance Marketing, Demand Gen",
        "target_roles": ["Marketing Manager", "Growth Lead", "Head of Marketing"],
        "recommended_template": "minimal",
        "is_custom": False,
    },
    {
        "id": "hr",
        "name": "Human Resources & People",
        "category": "People & Culture",
        "icon": "Users",
        "description": "People Operations, Talent Acquisition, HRBP, Organizational Culture",
        "target_roles": ["HRBP", "Head of People", "Talent Acquisition Lead"],
        "recommended_template": "classic",
        "is_custom": False,
    },
]

def _get_storage_path(filename: str) -> Path:
    p = data_dir() / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def _load_custom_themes() -> List[Dict[str, Any]]:
    path = _get_storage_path("custom_themes.json")
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

def _save_custom_themes(themes: List[Dict[str, Any]]):
    path = _get_storage_path("custom_themes.json")
    path.write_text(json.dumps(themes, indent=2), encoding="utf-8")

def _load_user_resumes() -> List[Dict[str, Any]]:
    path = _get_storage_path("user_resumes.json")
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

def _save_user_resumes(resumes: List[Dict[str, Any]]):
    path = _get_storage_path("user_resumes.json")
    path.write_text(json.dumps(resumes, indent=2), encoding="utf-8")


class CreateResumePayload(BaseModel):
    name: str
    theme_id: str
    template_id: Optional[str] = "classic"
    target_roles: Optional[List[str]] = Field(default_factory=list)
    summary: Optional[str] = ""
    notes: Optional[str] = ""


class CreateThemePayload(BaseModel):
    name: str
    description: Optional[str] = ""
    target_roles: Optional[List[str]] = Field(default_factory=list)
    recommended_template: Optional[str] = "classic"


@router.get("/themes")
def list_themes():
    """Returns all pre-configured and user-added career themes."""
    custom = _load_custom_themes()
    return {
        "status": "success",
        "themes": DEFAULT_THEMES + custom
    }


@router.post("/themes")
def create_custom_theme(payload: CreateThemePayload):
    """Allows user to create a new career theme/archetype relevant to their profile."""
    name_clean = payload.name.strip()
    if not name_clean:
        raise HTTPException(status_code=400, detail="Theme name is required.")
    
    slug = name_clean.lower().replace("&", "and").replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")

    custom = _load_custom_themes()
    for t in DEFAULT_THEMES + custom:
        if t["id"] == slug or t["name"].lower() == name_clean.lower():
            raise HTTPException(status_code=400, detail="A theme with this name already exists.")

    new_theme = {
        "id": slug,
        "name": name_clean,
        "category": "Custom Career Profile",
        "icon": "Sparkles",
        "description": payload.description.strip() or f"Specialized profile for {name_clean}",
        "target_roles": payload.target_roles or [name_clean],
        "recommended_template": payload.recommended_template or "classic",
        "is_custom": True,
    }
    custom.append(new_theme)
    _save_custom_themes(custom)
    return {"status": "success", "theme": new_theme}


@router.delete("/themes/{theme_id}")
def delete_custom_theme(theme_id: str):
    """Deletes a custom career theme."""
    custom = _load_custom_themes()
    filtered = [t for t in custom if t["id"] != theme_id]
    if len(filtered) == len(custom):
        raise HTTPException(status_code=404, detail="Custom theme not found or cannot delete default theme.")
    _save_custom_themes(filtered)
    return {"status": "success", "message": "Theme deleted."}


@router.get("")
def list_all_resumes():
    """
    Returns all resumes:
    1. Primary Master Resume (sourced directly from verified career facts)
    2. Any theme-specific resumes created by the user.
    """
    profile = None
    try:
        profile = w.profile_get()
    except Exception:
        profile = {}

    first_name = (profile.get("first_name") or "Candidate").strip()
    last_name = (profile.get("last_name") or "").strip()
    full_name = f"{first_name} {last_name}".strip()
    exp_count = len(profile.get("experience", []))
    skills_count = len(profile.get("skills", []))
    edu_count = len(profile.get("education", []))

    # Master CV
    master_resume = {
        "id": "master-cv",
        "name": f"{first_name}_Master_Resume_CV",
        "display_title": "Primary Master CV (All Verified Facts)",
        "theme_id": "master",
        "theme_name": "Primary Master CV",
        "template_id": profile.get("preferred_template") or "classic",
        "target_roles": profile.get("target_roles", ["Business Analyst - Strategy Office", "Corporate Strategy"]),
        "experience_count": exp_count,
        "skills_count": skills_count,
        "education_count": edu_count,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "is_master": True,
        "description": "Your comprehensive source of truth with 100% confirmed facts."
    }

    user_resumes = _load_user_resumes()
    all_resumes = [master_resume] + user_resumes

    return {
        "status": "success",
        "total": len(all_resumes),
        "resumes": all_resumes
    }


@router.post("")
def create_resume(payload: CreateResumePayload):
    """Creates a new theme-specific resume."""
    clean_name = payload.name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Resume name is required.")

    all_themes = DEFAULT_THEMES + _load_custom_themes()
    theme_info = next((t for t in all_themes if t["id"] == payload.theme_id), None)
    theme_name = theme_info["name"] if theme_info else "Specialized Theme"

    profile = None
    try:
        profile = w.profile_get()
    except Exception:
        profile = {}

    new_id = f"cv-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    new_resume = {
        "id": new_id,
        "name": clean_name,
        "display_title": clean_name,
        "theme_id": payload.theme_id,
        "theme_name": theme_name,
        "template_id": payload.template_id or (theme_info.get("recommended_template") if theme_info else "classic"),
        "target_roles": payload.target_roles or (theme_info.get("target_roles") if theme_info else [clean_name]),
        "experience_count": len(profile.get("experience", [])),
        "skills_count": len(profile.get("skills", [])),
        "education_count": len(profile.get("education", [])),
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "is_master": False,
        "summary": payload.summary,
        "notes": payload.notes,
        "description": f"Targeted resume for {theme_name} opportunities."
    }

    user_resumes = _load_user_resumes()
    user_resumes.append(new_resume)
    _save_user_resumes(user_resumes)

    return {"status": "success", "resume": new_resume}


@router.delete("/{resume_id}")
def delete_resume(resume_id: str):
    """Deletes a custom theme resume."""
    if resume_id == "master-cv":
        raise HTTPException(status_code=400, detail="Cannot delete the Primary Master CV.")

    user_resumes = _load_user_resumes()
    filtered = [r for r in user_resumes if r["id"] != resume_id]
    if len(filtered) == len(user_resumes):
        raise HTTPException(status_code=404, detail="Resume not found.")
    _save_user_resumes(filtered)
    return {"status": "success", "message": "Resume deleted."}
