from sqlalchemy.orm import Session, selectinload
from cv_tailor.models import database_models as db_models
from cv_tailor.models.schemas import UserProfile
from cv_tailor.services.preset_service import resolve_preset

PROFILE_LOAD_OPTIONS = (
    selectinload(db_models.Profile.education),
    selectinload(db_models.Profile.experience),
    selectinload(db_models.Profile.projects),
    selectinload(db_models.Profile.skills),
    selectinload(db_models.Profile.certifications),
)


def serialize_profile(profile: db_models.Profile) -> dict:
    return {
        "id": profile.id,
        "revision": profile.revision,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "mobile_no": profile.mobile_no,
        "email": profile.email,
        "linkedin": profile.linkedin,
        "github": profile.github,
        "portfolio": profile.portfolio,
        "preset_slug": profile.preset_slug,
        "preferred_template": profile.preferred_template,
        "education": [
            {
                "school_name": item.school_name,
                "course": item.course,
                "location": item.location,
                "description": item.description,
                "date_range": item.date_range,
            }
            for item in profile.education
        ],
        "experience": [
            {
                "job_title": item.job_title,
                "company": item.company,
                "location": item.location,
                "description": item.description,
                "date_range": item.date_range,
            }
            for item in profile.experience
        ],
        "projects": [
            {
                "name": item.name,
                "description": item.description,
                "date_range": item.date_range,
                "link": item.link,
            }
            for item in profile.projects
        ],
        "skills": [{"skill_name": item.skill_name, "is_confirmed": bool(item.is_confirmed)} for item in profile.skills],
        "certifications": [
            {
                "name": item.name,
                "issuer": item.issuer,
                "date_issued": item.date_issued,
            }
            for item in profile.certifications
        ],
    }

def save_profile_data(db: Session, workspace_id: int, profile_data: UserProfile) -> None:
    """Update the profile in place and replace its nested rows, then commit."""
    existing = db.query(db_models.Profile).filter(
        db_models.Profile.workspace_id == workspace_id
    ).first()
    # Saving another profile field must never silently confirm old suggestions.
    previous_confirmations = {
        skill.skill_name.strip().casefold(): bool(skill.is_confirmed)
        for skill in existing.skills
    } if existing else {}
    previous_project_links = {project.name.strip().casefold(): project.link for project in existing.projects if project.name} if existing else {}
    previous_education_dates = {(item.school_name, item.course): item.date_range for item in existing.education} if existing else {}
    if existing:
        db.query(db_models.Education).filter(db_models.Education.profile_id == existing.id).delete()
        db.query(db_models.Experience).filter(db_models.Experience.profile_id == existing.id).delete()
        db.query(db_models.Project).filter(db_models.Project.profile_id == existing.id).delete()
        db.query(db_models.Skill).filter(db_models.Skill.profile_id == existing.id).delete()
        db.query(db_models.Certification).filter(db_models.Certification.profile_id == existing.id).delete()
        db.flush()
        db.expire(existing, ["education", "experience", "projects", "skills", "certifications"])

    new_profile = existing or db_models.Profile(workspace_id=workspace_id)
    for field in ("first_name", "last_name", "mobile_no", "email", "linkedin", "github", "portfolio", "preset_slug"):
        setattr(new_profile, field, getattr(profile_data, field))
    if profile_data.preferred_template is not None:
        new_profile.preferred_template = profile_data.preferred_template
    db.add(new_profile)
    db.flush()

    for edu in profile_data.education:
        db.add(db_models.Education(
            profile_id=new_profile.id,
            school_name=edu.school_name,
            course=edu.course,
            location=edu.location,
            description=edu.description,
            date_range=edu.date_range if edu.date_range is not None else previous_education_dates.get((edu.school_name, edu.course)),
        ))

    for exp in profile_data.experience:
        db.add(db_models.Experience(
            profile_id=new_profile.id,
            job_title=exp.job_title,
            company=exp.company,
            location=exp.location,
            description=exp.description,
            date_range=exp.date_range
        ))

    for proj in profile_data.projects:
        db.add(db_models.Project(
            profile_id=new_profile.id,
            name=proj.name,
            description=proj.description,
            date_range=proj.date_range,
            link=proj.link if proj.link is not None else previous_project_links.get(proj.name.strip().casefold()),
        ))

    for skill in profile_data.skills:
        key = skill.skill_name.strip().casefold()
        confirmed = skill.is_confirmed
        if confirmed is None:
            confirmed = previous_confirmations.get(key, False)
        db.add(db_models.Skill(
            profile_id=new_profile.id,
            skill_name=skill.skill_name,
            is_confirmed=confirmed,
        ))

    existing_skills = {s.skill_name.lower() for s in profile_data.skills}
    preset = resolve_preset(db, profile_data.preset_slug)
    if preset and preset.core_skills_bank:
        for p_skill in preset.core_skills_bank:
            if p_skill.lower() not in existing_skills:
                db.add(db_models.Skill(
                    profile_id=new_profile.id,
                    skill_name=p_skill,
                    is_confirmed=False,
                ))

    for cert in profile_data.certifications:
        db.add(db_models.Certification(
            profile_id=new_profile.id,
            name=cert.name,
            issuer=cert.issuer,
            date_issued=cert.date_issued
        ))

    db.flush()
