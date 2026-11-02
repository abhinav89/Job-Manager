from concurrent.futures import ThreadPoolExecutor
import io
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from reportlab.pdfgen.canvas import Canvas


def test_profile_revision_and_confirmed_context(local_workspace, profile_payload):
    w = local_workspace
    saved = w.profile_save(profile_payload)
    assert saved["revision"] == 1
    context = w.context_export()
    assert [item["skill_name"] for item in context["profile"]["skills"]] == ["Python"]
    with pytest.raises(w.WorkspaceError, match="Refresh"):
        w.profile_save(profile_payload)
    saved = w.profile_save({**profile_payload, "revision": 1, "first_name": "Updated"})
    assert saved["revision"] == 2


def test_mutations_are_atomic_and_idempotent(local_workspace):
    w = local_workspace
    payload = {"company_name": "Acme", "job_title": "Developer"}
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: w.application_add(payload, "same-request"), range(8)))
    assert len({item["id"] for item in results}) == 1
    assert len(w.applications_list()) == 1
    with pytest.raises(w.WorkspaceError, match="different input"):
        w.application_add({**payload, "job_title": "Other"}, "same-request")
    app = results[0]
    updated = w.application_update(app["id"], {"status": "Interview"}, app["revision"])
    with pytest.raises(w.WorkspaceError):
        w.application_update(app["id"], {"status": "Rejected"}, app["revision"])
    assert w.application_get(app["id"])["status"] == "Interview"
    archived = w.application_update(app["id"], {"is_archived": True}, updated["revision"])
    assert w.applications_list(archived=False) == []
    assert archived["status"] == "Interview"


def test_application_uses_profile_template_unless_explicit(local_workspace, profile_payload):
    w = local_workspace
    w.profile_save({**profile_payload, "preferred_template": "modern"})
    job = w.application_add({"company_name": "Acme", "job_title": "Developer"})
    assert job["template_id"] == "modern"
    classic = w.application_add({"company_name": "Acme", "job_title": "Other", "template_id": "classic"})
    assert classic["template_id"] == "classic"


def test_general_context_resumes_only_general_drafts(local_workspace):
    w = local_workspace
    general = w.import_draft("interview_plan", {"content": "Practice Python questions."})
    app = w.application_add({"company_name": "Acme", "job_title": "Developer"})
    w.import_draft("interview_plan", {"content": "Prepare for Acme."}, app["id"])
    context = w.context_export("interview_plan")
    assert [draft["id"] for draft in context["drafts"]] == [general["id"]]


def test_conversation_facts_do_not_change_profile_or_other_applications(local_workspace, profile_payload):
    w = local_workspace
    w.profile_save(profile_payload)
    first = w.application_add({"company_name": "Acme", "job_title": "Developer"})
    second = w.application_add({"company_name": "Other", "job_title": "Developer"})
    letter = {"content": "I managed a team of 5 people."}
    with pytest.raises(w.WorkspaceError, match="Unsupported"):
        w.import_draft("cover_letter", letter, first["id"])
    w.import_draft("cover_letter", letter, first["id"], evidence=[letter["content"]])
    assert w.context_export("cover_letter", first["id"])["conversation_evidence"] == [letter["content"]]
    assert w.context_export("cover_letter", second["id"])["conversation_evidence"] == []
    assert "5" not in json.dumps(w.profile_get())


def test_drafts_apply_and_cascade_without_accounts(local_workspace, profile_payload):
    w = local_workspace
    w.profile_save(profile_payload)
    app = w.application_add({"company_name": "Acme", "job_title": "Developer"})
    draft = w.import_draft("cover_letter", {"content": "I use Python."}, app["id"], "letter")
    assert w.application_get(app["id"])["cover_letter"] is None
    applied = w.apply_draft(draft["id"], 1)
    assert applied["cover_letter"] == "I use Python."
    assert len(w.drafts_list(app["id"])) == 1
    with pytest.raises(Exception):
        w.import_draft("cover_letter", {"content": ""}, app["id"])
    assert len(w.drafts_list(app["id"])) == 1
    w.application_delete(app["id"], applied["revision"])
    assert w.drafts_list() == []


def test_resume_build_edit_and_overflow(local_workspace, profile_payload, monkeypatch):
    w = local_workspace
    from cv_tailor.services import pdf_service
    w.profile_save(profile_payload)
    app = w.application_add({"company_name": "Acme", "job_title": "Developer"})
    def pdf(pages):
        stream = io.BytesIO()
        canvas = Canvas(stream)
        for _ in range(pages):
            canvas.drawString(50, 750, "Alex Example Summary Python Experience Education Skills")
            canvas.showPage()
        canvas.save()
        return stream.getvalue()
    monkeypatch.setattr(pdf_service, "compile_latex_to_pdf", lambda text: pdf(1))
    content = {"summary": "I use Python.", "experience": [], "projects": [], "skills": [{"category": "Languages", "items": "Python"}], "certifications": ""}
    draft = w.import_draft("resume", content, app["id"])
    assert draft["metadata"]["one_page"]
    blocks = w.resume_blocks(draft["id"])
    assert blocks[0]["id"] == "summary"
    revised = w.resume_patch(draft["id"], {"blocks": [{"id": "summary", "text": "Python developer."}]})
    before, after = draft["content"], revised["content"]
    assert before.replace("I use Python.", "Python developer.") == after
    assert len(w.export_draft(revised["id"], "pdf")) > 100
    monkeypatch.setattr(pdf_service, "compile_latex_to_pdf", lambda text: pdf(2))
    overflow = w.import_draft("resume", content, app["id"])
    with pytest.raises(w.WorkspaceError, match="one page"):
        w.apply_draft(overflow["id"], 1)
    assert not w.application_get(app["id"])["has_pdf"]


def test_cli_needs_no_web_or_provider_modules(tmp_path):
    script = '''
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"fastapi", "uvicorn", "google", "openai", "psycopg", "psycopg2"}:
            raise ImportError("forbidden dependency: " + fullname)
sys.meta_path.insert(0, Block())
from cv_tailor.cli import main
raise SystemExit(main(sys.argv[1:]))
'''
    env = {**os.environ, "AI_MODE": "external", "DATABASE_URL": "postgresql://must-not-connect/unused", "PYTHONIOENCODING": "utf-8"}
    for args, payload in [(["init"], None), (["applications", "add", "--input", "-"], {"company_name": "Acme", "job_title": "Developer"}), (["applications", "list"], None)]:
        result = subprocess.run([sys.executable, "-c", script, "--data-dir", str(tmp_path), "--json", *args], input=json.dumps(payload) if payload else None, text=True, capture_output=True, env=env)
        assert result.returncode == 0, result.stdout + result.stderr
        json.loads(result.stdout)


def test_cli_uses_utf8_even_with_legacy_windows_encoding(tmp_path, profile_payload):
    payload = {**profile_payload, "first_name": "\u96f7\u5a1c"}
    result = subprocess.run([sys.executable, "-m", "cv_tailor", "--data-dir", str(tmp_path), "--json", "profile", "import", "--input", "-"],
        input=json.dumps(payload, ensure_ascii=False).encode("utf-8"), capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "cp1252", "AI_MODE": "external"})
    assert result.returncode == 0, result.stderr.decode("utf-8")
    assert json.loads(result.stdout.decode("utf-8"))["first_name"] == payload["first_name"]


def test_two_cli_processes_reuse_request_id(tmp_path):
    command = [sys.executable, "-m", "cv_tailor", "--data-dir", str(tmp_path), "--json"]
    payload = json.dumps({"company_name": "Acme", "job_title": "Developer"}).encode()
    children = [subprocess.Popen(command + ["applications", "add", "--input", "-", "--request-id", "process-retry"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
    results = [child.communicate(payload, timeout=30) for child in children]
    assert all(child.returncode == 0 for child in children), results
    assert json.loads(results[0][0])["id"] == json.loads(results[1][0])["id"]


def test_adding_dashboard_keeps_workspace(local_workspace, monkeypatch):
    from cv_tailor import dashboard
    w = local_workspace
    saved = w.application_add({"company_name": "Acme", "job_title": "Developer"})
    commands = []
    monkeypatch.setattr(dashboard.subprocess, "run", lambda command, **kwargs: commands.append(command))
    monkeypatch.setattr(dashboard.shutil, "which", lambda name: "npm")
    monkeypatch.setattr(dashboard, "package_assets", lambda: {"installed": True})
    assert dashboard.install()["installed"]
    assert w.application_get(saved["id"])["job_title"] == "Developer"
    assert commands[0][-1].endswith("[dashboard]")
    assert commands[1][-1] == "ci"
    assert commands[2][-2:] == ["run", "build"]
