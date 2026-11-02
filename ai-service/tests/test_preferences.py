import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from contextlib import closing

import pytest


def test_preferences_work_before_profile_and_new_applications_inherit(local_workspace):
    w = local_workspace
    initial = w.preferences_get()
    assert initial["resume_template"] == "classic"
    assert initial["tracking_connection"] is None
    saved = w.preferences_update({"resume_template": "sidebar", "tracking_connection": {"provider": "notion"}}, initial["revision"])
    assert saved["workspace_uuid"] == initial["workspace_uuid"]
    assert saved["tracking_connection"] == {"provider": "notion", "config_path": None}
    assert w.application_add({"company_name": "Example", "job_title": "Engineer"})["template_id"] == "sidebar"
    assert w.application_add({"company_name": "Example", "job_title": "Other", "template_id": "modern"})["template_id"] == "modern"
    assert w.context_export()["preferences"] == saved


def test_partial_changes_preserve_other_choices_and_detect_conflicts(local_workspace, tmp_path):
    w = local_workspace
    config_path = str(tmp_path / "connection.json")
    saved = w.preferences_update({"tracking_connection": {"provider": "obsidian", "config_path": config_path}}, 1)
    updated = w.preferences_update({"resume_template": "technical"}, saved["revision"])
    assert updated["tracking_connection"] == saved["tracking_connection"]
    with pytest.raises(w.WorkspaceError, match="Refresh"):
        w.preferences_update({"resume_template": "compact"}, saved["revision"])
    disconnected = w.preferences_update({"tracking_connection": None}, updated["revision"])
    assert disconnected["resume_template"] == "technical"
    assert disconnected["tracking_connection"] is None


def test_profile_and_default_template_stay_compatible_without_overwriting_applications(local_workspace, profile_payload):
    w = local_workspace
    w.preferences_update({"resume_template": "executive"}, 1)
    profile_without_choice = {key: value for key, value in profile_payload.items() if key != "preferred_template"}
    profile = w.profile_save(profile_without_choice)
    assert profile["preferred_template"] == "executive"
    application = w.application_add({"company_name": "Example", "job_title": "Engineer"})
    preferences = w.preferences_get()
    w.preferences_update({"resume_template": "minimal"}, preferences["revision"])
    assert w.profile_get()["preferred_template"] == "minimal"
    with pytest.raises(w.WorkspaceError, match="Refresh"):
        w.profile_save({**profile, "first_name": "Changed"})
    assert w.application_get(application["id"])["template_id"] == "executive"
    profile = w.profile_get()
    w.profile_save({**profile, "preferred_template": "serif"})
    assert w.preferences_get()["resume_template"] == "serif"
    with pytest.raises(w.WorkspaceError, match="Refresh"):
        w.preferences_update({"resume_template": "classic"}, preferences["revision"] + 1)


@pytest.mark.parametrize("payload", [
    {"resume_template": "unknown"}, {"resume_template": None},
    {"token": "fictional-private-value"},
    {"tracking_connection": {"provider": "notion", "token": "fictional-private-value"}},
    {"tracking_connection": {"provider": "unknown"}},
    {"tracking_connection": {"provider": "notion", "config_path": ".env.integrations"}},
    {"tracking_connection": {"provider": "notion", "config_path": "https://example.com/config.json"}},
])
def test_preference_schema_rejects_credentials_and_invalid_values(local_workspace, payload):
    w = local_workspace
    before = w.preferences_get()
    with pytest.raises(w.WorkspaceError) as error:
        w.preferences_update(payload, before["revision"])
    assert "fictional-private-value" not in str(error.value)
    assert w.preferences_get() == before


def test_version_one_upgrade_preserves_choices_and_creates_a_backup(local_workspace, profile_payload):
    from cv_tailor import database
    from cv_tailor.schema_changes import apply_schema_changes
    w = local_workspace
    w.profile_save({**profile_payload, "preferred_template": "modern"})
    application = w.application_add({"company_name": "Example", "job_title": "Engineer", "template_id": "compact"})
    with database.engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE workspace_preferences")
        connection.exec_driver_sql("PRAGMA user_version=1")
    apply_schema_changes(database.engine)
    assert w.preferences_get()["resume_template"] == "modern"
    assert w.application_get(application["id"])["template_id"] == "compact"
    database_path = Path(database.engine.url.database)
    backups = list(database_path.parent.glob(database_path.name + ".backup-*"))
    assert len(backups) == 1
    with closing(sqlite3.connect(backups[0])) as backup:
        assert backup.execute("PRAGMA user_version").fetchone()[0] == 1
    uuid = w.preferences_get()["workspace_uuid"]
    apply_schema_changes(database.engine)
    assert w.preferences_get()["workspace_uuid"] == uuid
    assert len(list(database_path.parent.glob(database_path.name + ".backup-*"))) == 1


def test_new_cli_processes_reload_preferences_and_isolate_workspaces(tmp_path):
    def run(directory, *args, payload=None, success=True):
        result = subprocess.run([sys.executable, "-m", "cv_tailor", "--data-dir", str(directory), "--json", *args],
            input=json.dumps(payload) if payload is not None else None, capture_output=True, text=True,
            env={**os.environ, "AI_MODE": "external"})
        assert result.returncode == (0 if success else 1), result.stdout + result.stderr
        return json.loads(result.stdout)
    first = tmp_path / "first"
    second = tmp_path / "second"
    assert run(first, "status")["preferences"] is None
    initial = run(first, "preferences", "get")
    saved = run(first, "preferences", "set", "--revision", str(initial["revision"]), "--input", "-",
        payload={"resume_template": "minimal", "tracking_connection": {"provider": "airtable"}})
    assert run(first, "status")["preferences"] == saved
    assert run(first, "preferences", "get") == saved
    other = run(second, "preferences", "get")
    assert other["resume_template"] == "classic"
    assert other["workspace_uuid"] != saved["workspace_uuid"]
    invalid = run(first, "preferences", "set", "--revision", str(saved["revision"]), "--input", "-",
        payload={"tracking_connection": {"provider": "notion", "token": "fictional-private-value"}}, success=False)
    assert "fictional-private-value" not in json.dumps(invalid)


def test_http_and_cli_share_revisioned_preferences(local_workspace):
    from fastapi.testclient import TestClient
    from cv_tailor.main import app
    w = local_workspace
    with TestClient(app) as client:
        initial = client.get("/api/preferences").json()
        response = client.patch("/api/preferences", json={"revision": initial["revision"], "resume_template": "compact"})
        assert response.status_code == 200, response.text
        assert w.preferences_get() == response.json()
        assert client.get("/api/workspace").json()["preferences"] == response.json()
        assert client.patch("/api/preferences", json={"revision": initial["revision"], "resume_template": "modern"}).status_code == 409
        rejected = client.patch("/api/preferences", json={"revision": response.json()["revision"], "token": "fictional-private-value"})
        assert rejected.status_code == 422
        assert "fictional-private-value" not in rejected.text
