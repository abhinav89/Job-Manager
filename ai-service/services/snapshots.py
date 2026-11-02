"""Plain turn inputs: no live ORM state or lazy loading in external workers."""
from types import SimpleNamespace


def snapshot(row, relationships=()):
    if row is None:
        return None
    values = {column.key: getattr(row, column.key) for column in row.__mapper__.column_attrs
              if column.key != "pdf_data"}
    for name in relationships:
        values[name] = [snapshot(item) for item in getattr(row, name)]
    return SimpleNamespace(**values)


def profile_snapshot(profile):
    return snapshot(profile, ("education", "experience", "projects", "skills", "certifications"))


def resume_snapshot(db, profile, jd, preset_slug):
    from services.preset_service import resolve_preset
    from services.llm_service import retrieve_successful_evidence
    preset = resolve_preset(db, preset_slug)
    config = {column.key: getattr(preset, column.key) for column in preset.__mapper__.column_attrs} if preset else None
    history = retrieve_successful_evidence(profile, jd, db)
    plain = profile_snapshot(profile)
    db.rollback()
    return plain, config, history
