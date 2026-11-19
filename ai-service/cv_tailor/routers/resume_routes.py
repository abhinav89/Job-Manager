"""
Resume and Profile Theme Management Routes for Job-Manager.
Enables candidates to manage multiple resumes categorized by career themes/archetypes
(Sales, BD, Product, Tech Engineer, Marketing, Finance, Operations, Supply Chain, HR, Strategy & Transformation).
Includes custom theme resume duplication, versioning (v1, v2), and Apify theme assignment.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Request, Header

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

def _resolve_user_id(request: Request) -> str:
    """Identifies the user namespace from request headers."""
    email = request.headers.get("X-User-Email", "").strip().lower()
    if "abhinav" in email:
        return "abhinav"
    if "shivangi" in email:
        return "shivangi"
    return "default"

def _get_storage_path(filename: str, user_id: str = "default") -> Path:
    prefix = f"{user_id}_" if user_id != "default" else ""
    p = data_dir() / f"{prefix}{filename}"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def _load_custom_themes(user_id: str = "default") -> List[Dict[str, Any]]:
    path = _get_storage_path("custom_themes.json", user_id)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

def _save_custom_themes(themes: List[Dict[str, Any]], user_id: str = "default"):
    path = _get_storage_path("custom_themes.json", user_id)
    path.write_text(json.dumps(themes, indent=2), encoding="utf-8")

def _load_user_resumes(user_id: str = "default") -> List[Dict[str, Any]]:
    path = _get_storage_path("user_resumes.json", user_id)
    if not path.exists():
        # Seed user-specific defaults if empty
        seeded = _seed_default_resumes(user_id)
        if seeded:
            _save_user_resumes(seeded, user_id)
            return seeded
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

def _seed_default_resumes(user_id: str) -> List[Dict[str, Any]]:
    if user_id == "abhinav":
        return [
            {
                "id": "cv-abhinav-bms",
                "name": "BMS_Operations_Finance_v1.pdf",
                "display_title": "BMS Operations Finance (v1)",
                "theme_id": "finance",
                "theme_name": "Finance & FP&A",
                "template_id": "modern",
                "target_roles": ["Senior Manager Operations Finance", "Senior Manager FP&A"],
                "experience_count": 6,
                "skills_count": 24,
                "education_count": 2,
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "is_master": False,
                "version": "v1",
                "versions": [{"version": "v1", "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "notes": "Initial starting file"}],
                "assigned_themes": ["fpa-business-planning", "operations-strategic-finance"],
                "description": "Validated source file for FP&A and Operations Finance themes."
            },
            {
                "id": "cv-abhinav-dubai",
                "name": "Dubai_Strategy_CEO_Office_v1.pdf",
                "display_title": "Dubai Strategy & CEO Office (v1)",
                "theme_id": "strategy-transformation",
                "theme_name": "Strategy & Transformation",
                "template_id": "classic",
                "target_roles": ["Enterprise Strategy Lead", "Chief of Staff to the CEO"],
                "experience_count": 6,
                "skills_count": 22,
                "education_count": 2,
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "is_master": False,
                "version": "v1",
                "versions": [{"version": "v1", "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "notes": "Initial starting file"}],
                "assigned_themes": ["corporate-strategy-transformation", "ceo-office-chief-of-staff"],
                "description": "Informs Strategy and CEO Office themes. Targets India opportunities."
            }
        ]
    elif user_id == "shivangi":
        return [
            {
                "id": "cv-shivangi-gbs",
                "name": "GBS_Consulting_v2.pdf",
                "display_title": "GBS Consulting (v2)",
                "theme_id": "strategy-and-consulting",
                "theme_name": "Strategy & Consulting",
                "template_id": "modern",
                "target_roles": ["Investment Manager", "Equity Research Lead", "Strategy Consulting Manager"],
                "experience_count": 4,
                "skills_count": 18,
                "education_count": 2,
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "is_master": False,
                "version": "v2",
                "versions": [
                    {"version": "v1", "created_at": "2026-09-01", "notes": "Original draft"},
                    {"version": "v2", "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "notes": "Active GBS consulting revision"}
                ],
                "assigned_themes": ["investments", "equity-research"],
                "description": "Specialized for private investments and equity research coverage."
            },
            {
                "id": "cv-shivangi-pmo",
                "name": "11_Sep_Strategy_PMO.pdf",
                "display_title": "11 Sep Strategy & PMO (v1)",
                "theme_id": "strategy-transformation",
                "theme_name": "Strategy & Transformation",
                "template_id": "classic",
                "target_roles": ["IPO Readiness Lead", "Senior Manager Corporate Strategy", "Greenfield Setup Lead"],
                "experience_count": 4,
                "skills_count": 20,
                "education_count": 2,
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "is_master": False,
                "version": "v1",
                "versions": [{"version": "v1", "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "notes": "Initial verified PMO file"}],
                "assigned_themes": ["ipo-readiness-sme-listing", "manufacturing-setup"],
                "description": "Documented IPO analysis, plant setup readiness, and enterprise PMO."
            }
        ]
    return []

def _save_user_resumes(resumes: List[Dict[str, Any]], user_id: str = "default"):
    path = _get_storage_path("user_resumes.json", user_id)
    path.write_text(json.dumps(resumes, indent=2), encoding="utf-8")


class CreateResumePayload(BaseModel):
    name: str
    theme_id: str
    template_id: Optional[str] = "classic"
    target_roles: Optional[List[str]] = Field(default_factory=list)
    summary: Optional[str] = ""
    notes: Optional[str] = ""


class DuplicateResumePayload(BaseModel):
    source_resume_id: str
    new_name: str
    target_theme_id: str


class AddVersionPayload(BaseModel):
    version_label: str
    notes: Optional[str] = ""


class AssignThemeResumePayload(BaseModel):
    theme_id: str
    resume_id: str
    version: str = "v1"


class CreateThemePayload(BaseModel):
    name: str
    description: Optional[str] = ""
    target_roles: Optional[List[str]] = Field(default_factory=list)
    recommended_template: Optional[str] = "classic"


@router.get("/themes")
def list_themes(request: Request):
    """Returns all pre-configured and user-added career themes."""
    user_id = _resolve_user_id(request)
    custom = _load_custom_themes(user_id)
    return {
        "status": "success",
        "themes": DEFAULT_THEMES + custom
    }


@router.post("/themes")
def create_custom_theme(payload: CreateThemePayload, request: Request):
    """Allows user to create a new career theme/archetype relevant to their profile."""
    user_id = _resolve_user_id(request)
    name_clean = payload.name.strip()
    if not name_clean:
        raise HTTPException(status_code=400, detail="Theme name is required.")
    
    slug = name_clean.lower().replace("&", "and").replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")

    custom = _load_custom_themes(user_id)
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
    _save_custom_themes(custom, user_id)
    return {"status": "success", "theme": new_theme}


@router.get("")
def list_all_resumes(request: Request):
    """
    Returns all resumes for current user:
    1. Primary Master Resume (sourced directly from verified career facts)
    2. Any theme-specific resumes with their active versions.
    """
    user_id = _resolve_user_id(request)
    profile = None
    try:
        profile = w.profile_get()
    except Exception:
        profile = {}

    first_name = (profile.get("first_name") or ("Abhinav" if user_id == "abhinav" else ("Shivangi" if user_id == "shivangi" else "Candidate"))).strip()
    exp_count = len(profile.get("experience", []))
    skills_count = len(profile.get("skills", []))
    edu_count = len(profile.get("education", []))

    master_resume = {
        "id": "master-cv",
        "name": f"{first_name}_Master_Resume_CV",
        "display_title": f"{first_name} Master CV (All Verified Facts)",
        "theme_id": "master",
        "theme_name": "Primary Master CV",
        "template_id": profile.get("preferred_template") or "classic",
        "target_roles": profile.get("target_roles", ["Executive Strategy", "Operations"]),
        "experience_count": exp_count or 6,
        "skills_count": skills_count or 22,
        "education_count": edu_count or 2,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "is_master": True,
        "version": "Master",
        "versions": [{"version": "Master", "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "notes": "Master verified profile"}],
        "description": "Your comprehensive source of truth with 100% confirmed facts."
    }

    user_resumes = _load_user_resumes(user_id)
    all_resumes = [master_resume] + user_resumes

    return {
        "status": "success",
        "total": len(all_resumes),
        "resumes": all_resumes
    }


@router.post("")
def create_resume(payload: CreateResumePayload, request: Request):
    """Creates a new theme-specific resume."""
    user_id = _resolve_user_id(request)
    clean_name = payload.name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Resume name is required.")

    all_themes = DEFAULT_THEMES + _load_custom_themes(user_id)
    theme_info = next((t for t in all_themes if t["id"] == payload.theme_id), None)
    theme_name = theme_info["name"] if theme_info else "Specialized Theme"

    new_id = f"cv-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    new_resume = {
        "id": new_id,
        "name": clean_name,
        "display_title": clean_name,
        "theme_id": payload.theme_id,
        "theme_name": theme_name,
        "template_id": payload.template_id or "classic",
        "target_roles": payload.target_roles or (theme_info.get("target_roles") if theme_info else [clean_name]),
        "experience_count": 6,
        "skills_count": 20,
        "education_count": 2,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "is_master": False,
        "version": "v1",
        "versions": [{"version": "v1", "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "notes": "Initial draft"}],
        "assigned_themes": [payload.theme_id],
        "summary": payload.summary,
        "notes": payload.notes,
        "description": f"Targeted resume for {theme_name} opportunities."
    }

    user_resumes = _load_user_resumes(user_id)
    user_resumes.append(new_resume)
    _save_user_resumes(user_resumes, user_id)

    return {"status": "success", "resume": new_resume}


@router.post("/duplicate")
def duplicate_resume(payload: DuplicateResumePayload, request: Request):
    """
    Duplicates an existing resume as a new custom theme resume.
    Editing the duplicate does not affect the source resume.
    """
    user_id = _resolve_user_id(request)
    user_resumes = _load_user_resumes(user_id)
    source = next((r for r in user_resumes if r["id"] == payload.source_resume_id), None)
    
    if not source and payload.source_resume_id != "master-cv":
        raise HTTPException(status_code=404, detail="Source resume not found.")

    all_themes = DEFAULT_THEMES + _load_custom_themes(user_id)
    target_theme = next((t for t in all_themes if t["id"] == payload.target_theme_id), None)
    target_theme_name = target_theme["name"] if target_theme else "Specialized Theme"

    new_id = f"cv-copy-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    duplicated_resume = {
        "id": new_id,
        "name": payload.new_name.strip(),
        "display_title": payload.new_name.strip(),
        "theme_id": payload.target_theme_id,
        "theme_name": target_theme_name,
        "template_id": source.get("template_id", "classic") if source else "classic",
        "target_roles": source.get("target_roles", [payload.new_name]) if source else [payload.new_name],
        "experience_count": source.get("experience_count", 6) if source else 6,
        "skills_count": source.get("skills_count", 20) if source else 20,
        "education_count": source.get("education_count", 2) if source else 2,
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "is_master": False,
        "version": "v1",
        "versions": [{"version": "v1", "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "notes": f"Duplicated from {source.get('name', 'Master CV') if source else 'Master CV'}"}],
        "assigned_themes": [payload.target_theme_id],
        "summary": source.get("summary", "") if source else "",
        "notes": f"Duplicated copy for {target_theme_name}.",
        "description": f"Tailored resume for {target_theme_name} (independent copy)."
    }

    user_resumes.append(duplicated_resume)
    _save_user_resumes(user_resumes, user_id)

    return {
        "status": "success",
        "message": f"Successfully created independent copy '{payload.new_name}' under {target_theme_name}.",
        "resume": duplicated_resume
    }


@router.post("/{resume_id}/version")
def add_resume_version(resume_id: str, payload: AddVersionPayload, request: Request):
    """Adds a new revision version (e.g. v2, v3) to a resume."""
    user_id = _resolve_user_id(request)
    user_resumes = _load_user_resumes(user_id)
    target = next((r for r in user_resumes if r["id"] == resume_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Resume not found.")

    new_v = payload.version_label.strip()
    target["version"] = new_v
    target.setdefault("versions", []).append({
        "version": new_v,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "notes": payload.notes or "Updated revision"
    })
    target["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    _save_user_resumes(user_resumes, user_id)

    return {"status": "success", "resume": target}


@router.post("/assign-theme")
def assign_resume_to_theme(payload: AssignThemeResumePayload, request: Request):
    """Associates a theme with a specific resume version."""
    user_id = _resolve_user_id(request)
    user_resumes = _load_user_resumes(user_id)
    target = next((r for r in user_resumes if r["id"] == payload.resume_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Resume not found.")

    assigned = set(target.get("assigned_themes", []))
    assigned.add(payload.theme_id)
    target["assigned_themes"] = list(assigned)
    _save_user_resumes(user_resumes, user_id)

    return {
        "status": "success",
        "message": f"Assigned '{target['name']}' ({payload.version}) to theme '{payload.theme_id}'."
    }


@router.delete("/{resume_id}")
def delete_resume(resume_id: str, request: Request):
    """Deletes a custom theme resume."""
    if resume_id == "master-cv":
        raise HTTPException(status_code=400, detail="Cannot delete the Primary Master CV.")

    user_id = _resolve_user_id(request)
    user_resumes = _load_user_resumes(user_id)
    filtered = [r for r in user_resumes if r["id"] != resume_id]
    if len(filtered) == len(user_resumes):
        raise HTTPException(status_code=404, detail="Resume not found.")
    _save_user_resumes(filtered, user_id)
    return {"status": "success", "message": "Resume deleted."}
