from hashlib import sha256
import io
import json
import os
import subprocess
import sys

import pytest
from pydantic import ValidationError
from reportlab.pdfgen.canvas import Canvas

from cv_tailor.models.application_form import ApplicationFormContent
from cv_tailor.services.application_forms import assess_form, prepare_form, check_saved_form, confirm_submission


def field(**changes):
    return {"key": "step/name", "label": "Name", "kind": "text", "required": True,
            "original_value": "Alex", "proposed_value": "Alex", "observed_value": "Alex",
            "observation": "observed", "observed_at": "2026-11-02T10:00:00+08:00",
            "source": "confirmed_profile", "evidence": "profile.first_name", **changes}


def snapshot(**changes):
    return {"session_id": "a" * 32, "application_id": 1, "application_revision": 1,
            "profile_revision": 1, "company_name": "Acme", "job_title": "Engineer",
            "form_url": "https://example.com/jobs/engineer/apply", "posting_status": "active",
            "identity_confirmed": True, "inventory_complete": True, "all_steps_complete": True,
            "fields": [field()], **changes}


def assess(**changes):
    return assess_form(ApplicationFormContent.model_validate(snapshot(**changes)))


def codes(result):
    return {issue["code"] for issue in result["issues"]}


def test_readback_must_match_even_when_wrong_value_is_nonempty():
    assert assess()["ready_for_review"]
    result = assess(fields=[field(observed_value="Another applicant")])
    assert not result["ready_for_review"]
    assert "value_mismatch" in codes(result)
    assert "unverified" in codes(assess(fields=[field(observation="unreadable")]))
    assert "unverified" in codes(assess(fields=[field(observation="missing")]))
    assert not assess(fields=[field(kind="select", options=["Alex"], observed_value="Wrong")])["ready_for_review"]


def test_utf16_word_limits_unknown_limits_and_truncation():
    result = assess(fields=[field(original_value=None, proposed_value="A😀", observed_value="A😀",
        limit={"maximum": 2, "unit": "utf16", "source": "maxlength"})])
    assert "over_limit" in codes(result)
    assert result["fields"][0]["used"] == 3
    result = assess(fields=[field(limit={"maximum": 0, "unit": "utf16", "source": "maxlength"})])
    assert "over_limit" in codes(result)
    assert "over_limit" in codes(assess(fields=[field(original_value=None, proposed_value="two words",
        limit={"maximum": 1, "unit": "words", "source": "Visible help"})]))
    assert "limit_unknown" in codes(assess())
    assert not assess(fields=[field(proposed_value="Alex Example", change_confirmed=True)])["ready_for_review"]


def test_exact_options_required_consent_and_sensitive_confirmation():
    assert "invalid_option" in codes(assess(fields=[field(kind="select", options=["Different"])]))
    result = assess(fields=[field(label="Salary expectation", sensitive=False)])
    assert "confirmation_needed" in codes(result)
    result = assess(fields=[field(kind="checkbox", label="I consent", original_value=None,
        proposed_value=False, observed_value=False, user_confirmed=True)])
    assert "required_empty" in codes(result)
    assert assess(fields=[field(kind="checkbox", label="I consent", original_value=None,
        proposed_value=True, observed_value=True, user_confirmed=True)])["ready_for_review"]
    assert "existing_value_changed" in codes(assess(fields=[field(proposed_value="New name")]))


def test_conditional_and_repeated_controls_and_incomplete_inventory():
    missing = field(key="step/experience2/description", label="Role description", original_value=None,
                    proposed_value=None, observed_value="")
    result = assess(fields=[field(key="step/experience1/description"), missing])
    assert "required_empty" in codes(result)
    assert not assess(inventory_complete=False)["ready_for_review"]
    assert not assess(all_steps_complete=False)["ready_for_review"]
    assert not assess(posting_status="closed")["ready_for_review"]
    with pytest.raises(ValidationError, match="unique"):
        ApplicationFormContent.model_validate(snapshot(fields=[field(), field()]))
    with pytest.raises(ValidationError):
        ApplicationFormContent.model_validate(snapshot(state="submission_confirmed"))
    with pytest.raises(ValidationError, match="credentials"):
        ApplicationFormContent.model_validate(snapshot(form_url="https://user:secret@example.com/"))


def test_attachment_verifies_exact_selected_file_and_never_guesses():
    doc = {"draft_id": 7, "kind": "resume", "filename": "resume-7.pdf", "size": 5,
           "sha256": "a" * 64, "source_sha256": "b" * 64}
    upload = field(kind="file", original_value=None, proposed_value=None, observed_value=None,
                   document_id=7, observed_files=[{"filename": "resume-7.pdf", "size": 5, "sha256": "a" * 64}])
    assert assess(documents=[doc], fields=[upload])["ready_for_review"]
    original = [{"filename": "previous-resume.pdf", "size": 5, "sha256": "c" * 64}]
    replacement = {**upload, "original_files": original, "observation": "unobserved"}
    assert "existing_attachment_changed" in codes(assess(documents=[doc], fields=[replacement]))
    assert "existing_attachment_changed" not in codes(assess(documents=[doc], fields=[{**replacement, "change_confirmed": True}]))
    for change in ({"sha256": None}, {"size": 6}, {"filename": "other.pdf"}):
        invalid = {**upload, "observed_files": [{**upload["observed_files"][0], **change}]}
        assert "attachment_unverified" in codes(assess(documents=[doc], fields=[invalid]))


def setup_application(w, profile_payload):
    w.profile_save(profile_payload)
    return w.application_add({"company_name": "Acme", "job_title": "Engineer"})


def test_checkpoints_persist_and_resume_without_touching_application(local_workspace, profile_payload):
    w = local_workspace
    job = setup_application(w, profile_payload)
    prepared = prepare_form(job["id"])
    data = {**prepared["snapshot"], **snapshot()}
    draft = w.import_draft("application_form", data, job["id"], "first")
    assert w.import_draft("application_form", data, job["id"], "first")["id"] == draft["id"]
    assert check_saved_form(draft["id"])["state"] == "verified_for_review"
    assert w.application_get(job["id"])["status"] == "Saved"
    with pytest.raises(w.WorkspaceError, match="--parent"):
        w.import_draft("application_form", data, job["id"])
    data["fields"][0]["observed_value"] = "Changed by user"
    revised = w.import_draft("application_form", data, job["id"], "second", draft["id"])
    assert revised["metadata"]["validation"]["state"] == "partially_filled"
    assert w.draft_get(draft["id"])["metadata"]["validation"]["state"] == "verified_for_review"
    with pytest.raises(w.WorkspaceError, match="newer"):
        w.import_draft("application_form", data, job["id"], parent=draft["id"])
    with pytest.raises(w.WorkspaceError, match="explicit application"):
        w.import_draft("application_form", data)
    assert w.context_export("application_form", job["id"])["drafts"][0]["id"] == revised["id"]


def test_document_selection_is_bound_to_application_and_exact_bytes(local_workspace, profile_payload, monkeypatch):
    w = local_workspace
    job = setup_application(w, profile_payload)
    letter = w.import_draft("cover_letter", {"content": "I use Python."}, job["id"])
    from cv_tailor.services import pdf_service
    pdf_stream = io.BytesIO()
    canvas = Canvas(pdf_stream, invariant=1)
    canvas.drawString(50, 750, "Alex Example Summary Python Skills")
    canvas.save()
    monkeypatch.setattr(pdf_service, "compile_latex_to_pdf", lambda text: pdf_stream.getvalue())
    resume = w.import_draft("resume", {"summary": "I use Python.", "experience": [], "projects": [],
        "skills": [{"category": "Languages", "items": "Python"}], "certifications": ""}, job["id"])
    manifest = prepare_form(job["id"], resume=resume["id"])["snapshot"]["documents"][0]
    assert sha256(w.export_draft(resume["id"], "pdf")).hexdigest() == manifest["sha256"]
    prepared = prepare_form(job["id"], cover_letter=letter["id"])
    doc = prepared["snapshot"]["documents"][0]
    assert sha256(w.export_draft(letter["id"], "pdf")).hexdigest() == doc["sha256"]
    assert w.export_draft(letter["id"], "pdf") == w.export_draft(letter["id"], "pdf")
    other = w.application_add({"company_name": "Acme", "job_title": "Other role"})
    with pytest.raises(w.WorkspaceError, match="correct kind"):
        prepare_form(other["id"], cover_letter=letter["id"])
    with pytest.raises(w.WorkspaceError, match="correct kind"):
        prepare_form(job["id"], resume=letter["id"])
    data = {**snapshot(), "session_id": prepared["snapshot"]["session_id"], "documents": [doc]}
    data["documents"][0]["sha256"] = "0" * 64
    saved = w.import_draft("application_form", data, job["id"])
    assert "document_changed" in codes(saved["metadata"]["validation"])


def test_stale_context_is_not_silently_verified(local_workspace, profile_payload):
    w = local_workspace
    job = setup_application(w, profile_payload)
    draft = w.import_draft("application_form", snapshot(), job["id"])
    w.profile_save({**profile_payload, "first_name": "Updated"}, revision=1)
    assert "profile_changed" in codes(check_saved_form(draft["id"]))
    w.application_update(job["id"], {"job_title": "Other role"}, 1)
    result = check_saved_form(draft["id"])
    assert "application_changed" in codes(result)
    assert not result["ready_for_review"]


def test_submission_confirmation_is_explicit_atomic_and_retryable(local_workspace, profile_payload):
    w = local_workspace
    job = setup_application(w, profile_payload)
    draft = w.import_draft("application_form", snapshot(), job["id"])
    with pytest.raises(w.WorkspaceError, match="explicitly"):
        confirm_submission(draft["id"], 1, "2026-11-02")
    with pytest.raises(w.WorkspaceError, match="Refresh"):
        confirm_submission(draft["id"], 99, "2026-11-02", True, "bad")
    assert len(w.drafts_list(job["id"])) == 1
    result = confirm_submission(draft["id"], 1, "2026-11-02", True, "confirmed")
    assert result["application"]["status"] == "Applied"
    assert result["application"]["date_applied"] == "2026-11-02"
    assert result["draft"]["metadata"]["submission"]["confirmed_by"] == "user"
    assert confirm_submission(draft["id"], 1, "2026-11-02", True, "confirmed") == result
    assert len(w.drafts_list(job["id"])) == 2
    assert check_saved_form(result["draft"]["id"])["state"] == "submission_confirmed"
    with pytest.raises(w.WorkspaceError, match="newer"):
        confirm_submission(draft["id"], 2, "2026-11-02", True, "other")


def test_cli_check_works_after_restart_without_browser_or_ai(tmp_path, profile_payload):
    command = [sys.executable, "-m", "cv_tailor", "--data-dir", str(tmp_path), "--json"]
    def run(args, payload=None):
        result = subprocess.run(command + args, input=json.dumps(payload) if payload else None,
            text=True, capture_output=True, env={**os.environ, "AI_MODE": "external"}, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)
    run(["profile", "import", "--input", "-"], profile_payload)
    job = run(["applications", "add", "--input", "-"], {"company_name": "Acme", "job_title": "Engineer"})
    prepared = run(["forms", "prepare", "--application", str(job["id"])])
    assert prepared["snapshot"]["fields"] == []
    draft = run(["drafts", "import", "--kind", "application_form", "--application", str(job["id"]),
                 "--input", "-", "--request-id", "restart"], snapshot())
    assert run(["forms", "check", str(draft["id"])])["state"] == "verified_for_review"
