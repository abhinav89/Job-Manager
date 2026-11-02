import os
import pytest
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def local_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("CV_TAILOR_HOME", str(tmp_path))
    monkeypatch.setenv("AI_MODE", "external")
    for key in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY", "JEV_API_KEY", "TYPESAFE_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    from cv_tailor import database, workspace
    from cv_tailor.schema_changes import apply_schema_changes
    engine = database.make_engine("sqlite:///" + (tmp_path / "cv-tailor.sqlite3").as_posix())
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", sessions)
    monkeypatch.setattr(workspace, "SessionLocal", sessions)
    apply_schema_changes(engine)
    yield workspace
    engine.dispose()


@pytest.fixture
def profile_payload():
    return {"first_name": "Alex", "last_name": "Example", "mobile_no": "", "email": "alex@example.com",
            "education": [], "experience": [], "projects": [],
            "skills": [{"skill_name": "Python", "is_confirmed": True}, {"skill_name": "Rust", "is_confirmed": False}],
            "certifications": [], "preset_slug": "blank", "preferred_template": "classic"}
