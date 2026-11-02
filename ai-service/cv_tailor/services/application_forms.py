"""Validation and persistence support; browser actions belong to the local agent.

Observations are agent reports, not independently collected browser evidence.
Never interpret missing/unreadable observations as successful verification.
"""
from datetime import date
from hashlib import sha256
import re
from uuid import uuid4

from sqlalchemy import select

from cv_tailor.models.application_form import ApplicationFormContent, FormDocument
from cv_tailor.models import database_models as m


def _empty(value):
    return value is None or value == "" or value == [] or (isinstance(value, str) and not value.strip())


def assess_form(snapshot: ApplicationFormContent):
    issues = []
    def issue(code, message, key=None, severity="blocking"):
        issues.append({"code": code, "message": message, "field_key": key, "severity": severity})

    if not snapshot.form_url:
        issue("form_url_missing", "Confirm the live application URL.")
    if snapshot.posting_status != "active":
        issue("posting_unverified", "The posting has not been verified as active.")
    if not snapshot.identity_confirmed:
        issue("identity_unverified", "Confirm the form matches the intended company and role.")
    if not snapshot.inventory_complete or not snapshot.fields:
        issue("inventory_incomplete", "Inspect the whole current step, including conditional fields.")
    if not snapshot.all_steps_complete:
        issue("steps_incomplete", "More application steps may remain.")

    documents = {d.draft_id: d for d in snapshot.documents}
    results = []
    for f in snapshot.fields:
        expected = f.proposed_value if f.proposed_value is not None else f.original_value
        planned = not _empty(expected) or f.document_id is not None
        if f.kind == "checkbox" and expected is False and f.proposed_value is None and f.source == "none":
            planned = False  # untouched unchecked checkbox, not an asserted answer
        used = None
        if f.required is None:
            issue("required_unknown", "Confirm whether this field is required.", f.key)
        if f.kind == "unknown":
            issue("control_unknown", "This control needs inspection by the user.", f.key)
        sensitive = f.sensitive or bool(re.search(r"\b(visa|sponsorship|salary|compensation|disability|veteran|ethnicity|race|gender|relocat\w*|background check|work authori[sz]ation|legally authori[sz]ed|consent|i agree|i accept)\b", f.label, re.I))
        if sensitive and planned and not f.user_confirmed:
            issue("confirmation_needed", "Confirm this personal answer before filling it.", f.key)
        if planned and f.kind != "file" and (f.source == "none" or not f.evidence.strip()):
            issue("evidence_missing", "Record the confirmed source of this answer.", f.key)
        if planned and f.source in {"selected_resume", "selected_cover_letter"}:
            kind = "resume" if f.source == "selected_resume" else "cover_letter"
            if not any(d.kind == kind for d in snapshot.documents):
                issue("document_missing", "Select the document that supplies this answer.", f.key)
        if not _empty(f.original_value) and f.proposed_value is not None and f.original_value != f.proposed_value and not f.change_confirmed:
            issue("existing_value_changed", "Preserve the existing value until the user approves a change.", f.key)
        if f.kind == "file" and f.original_files and f.document_id in documents and not f.change_confirmed:
            doc = documents[f.document_id]
            original_matches = len(f.original_files) == 1 and (
                f.original_files[0].filename, f.original_files[0].size, f.original_files[0].sha256
            ) == (doc.filename, doc.size, doc.sha256)
            if not original_matches:
                issue("existing_attachment_changed", "Confirm before replacing the existing uploaded file.", f.key)
        if f.required and (not planned or (f.kind == "checkbox" and expected is not True)):
            issue("required_empty", "A required answer is missing.", f.key)
        if f.kind in {"select", "radio"} and planned:
            values = expected if isinstance(expected, list) else [expected]
            if not f.options or any(value not in f.options for value in values):
                issue("invalid_option", "Use the exact option labels confirmed on the live form.", f.key)
        if isinstance(expected, str) and f.kind != "file":
            if f.limit:
                used = len(expected.encode("utf-16-le", errors="surrogatepass")) // 2 if f.limit.unit == "utf16" else len(expected.split())
                if used > f.limit.maximum:
                    issue("over_limit", f"Answer uses {used}/{f.limit.maximum} {f.limit.unit}.", f.key)
            elif f.kind in {"text", "textarea"}:
                issue("limit_unknown", "No field limit was confirmed; check the live field.", f.key, "warning")
        if f.validation_errors:
            issue("portal_validation", "; ".join(f.validation_errors), f.key)
        if not planned and f.observation in {"unreadable", "missing"}:
            issue("unverified", "This control could not be inspected reliably.", f.key)
        verified = False
        if planned:
            if f.observation != "observed":
                issue("unverified", "Read the value back from a fresh live observation.", f.key)
            elif f.kind == "file":
                doc = documents.get(f.document_id)
                verified = doc is not None and len(f.observed_files) == 1 and any(
                    (item.filename, item.size, item.sha256) == (doc.filename, doc.size, doc.sha256)
                    for item in f.observed_files)
                if not verified:
                    issue("attachment_unverified", "The selected file's name, size and SHA-256 were not all verified.", f.key)
            else:
                verified = f.observed_value == expected
                if not verified:
                    issue("value_mismatch", "The observed value does not exactly match the intended answer.", f.key)
        results.append({"key": f.key, "verified": verified, "used": used,
                        "maximum": f.limit.maximum if f.limit else None,
                        "unit": f.limit.unit if f.limit else None})
    ready = not any(i["severity"] == "blocking" for i in issues)
    state = "verified_for_review" if ready else "partially_filled" if any(f.observation == "observed" for f in snapshot.fields) else "drafted"
    return {"state": state, "ready_for_review": ready, "issues": issues, "fields": results,
            "verification_source": "agent_reported_live_observations"}


def document_manifest(identifier, application, kind):
    from cv_tailor import workspace as w
    from cv_tailor.database import SessionLocal
    with SessionLocal() as db:
        draft = w.require(db.get(m.AssistantDraft, identifier), "Selected document")
        conversation = w.require(db.get(m.AssistantConversation, draft.conversation_id), "Conversation")
        if conversation.job_id != application or draft.type != kind:
            raise w.WorkspaceError("Select a document of the correct kind from this application")
        source = sha256(draft.content.encode()).hexdigest()
    # Compilation runs outside the write transaction. Cache the exact bytes so
    # export, subsequent checks, and the uploaded file all share one fingerprint.
    pdf = w.export_draft(identifier, "pdf")
    with w.write_session() as db:
        draft = w.require(db.get(m.AssistantDraft, identifier), "Selected document")
        if sha256(draft.content.encode()).hexdigest() != source:
            raise w.WorkspaceError("Selected document changed; prepare again", "conflict", 409)
        if draft.pdf_data:
            pdf = draft.pdf_data
        else:
            draft.pdf_data = pdf
    return FormDocument(draft_id=identifier, kind=kind, filename=f"{kind}-{identifier}.pdf",
                        source_sha256=source, sha256=sha256(pdf).hexdigest(), size=len(pdf))


def prepare_form(application, resume=None, cover_letter=None):
    from cv_tailor import workspace as w
    context = w.context_export("application_form", application)
    if not context["profile"]:
        raise w.WorkspaceError("Save a confirmed profile before preparing an application form")
    job = context["application"]
    documents = []
    if resume:
        documents.append(document_manifest(resume, application, "resume"))
    if cover_letter:
        documents.append(document_manifest(cover_letter, application, "cover_letter"))
    snapshot = ApplicationFormContent(session_id=uuid4().hex, application_id=application,
        application_revision=job["revision"], profile_revision=context["profile"]["revision"],
        company_name=job["company_name"], job_title=job["job_title"], documents=documents)
    return {"context": context, "snapshot": snapshot.model_dump(mode="json"),
            "instructions": "Use cv-apply. Inspect the live form, save a checkpoint before filling, and stop for human review before submission."}


def check_bindings(db, snapshot):
    from cv_tailor import workspace as w
    job = w.require(db.get(m.JobApplication, snapshot.application_id), "Application")
    result = assess_form(snapshot)
    def issue(code, message):
        result["issues"].append({"code": code, "message": message, "field_key": None, "severity": "blocking"})
    if (job.revision, job.company_name, job.job_title) != (snapshot.application_revision, snapshot.company_name, snapshot.job_title):
        issue("application_changed", "Refresh the application context and confirm the target again.")
    profile = db.scalar(select(m.Profile).where(m.Profile.workspace_id == 1))
    if not profile or profile.revision != snapshot.profile_revision:
        issue("profile_changed", "Review the answers against the current confirmed profile.")
    for doc in snapshot.documents:
        draft = w.require(db.get(m.AssistantDraft, doc.draft_id), "Selected document")
        conversation = db.get(m.AssistantConversation, draft.conversation_id)
        if not conversation or conversation.job_id != snapshot.application_id or draft.type != doc.kind:
            raise w.WorkspaceError("Selected document belongs to a different application or document kind")
        if (sha256(draft.content.encode()).hexdigest() != doc.source_sha256 or not draft.pdf_data or
            sha256(draft.pdf_data).hexdigest() != doc.sha256 or len(draft.pdf_data) != doc.size or
            doc.filename != f"{doc.kind}-{doc.draft_id}.pdf"):
            issue("document_changed", "Prepare and verify the selected document again; its fingerprint differs.")
    if any(i["severity"] == "blocking" for i in result["issues"]):
        result["ready_for_review"] = False
        if result["state"] == "verified_for_review":
            result["state"] = "partially_filled"
    return result


def check_saved_form(identifier):
    from cv_tailor import workspace as w
    from cv_tailor.database import SessionLocal
    with SessionLocal() as db:
        draft = w.require(db.get(m.AssistantDraft, identifier), "Form checkpoint")
        if draft.type != "application_form":
            raise w.WorkspaceError("Select an application-form checkpoint")
        snapshot = ApplicationFormContent.model_validate(draft.details["structured_content"])
        result = check_bindings(db, snapshot)
        if draft.details.get("submission"):
            result["state"] = "submission_confirmed"
            result["submission"] = draft.details["submission"]
        return result


def confirm_submission(identifier, revision, submitted_on, user_confirmed=False, request_id=None):
    from cv_tailor import workspace as w
    if not user_confirmed:
        raise w.WorkspaceError("Confirm submission only after the user explicitly says they submitted the application")
    submitted_on = date.fromisoformat(submitted_on)
    def save(db):
        original = w.require(db.get(m.AssistantDraft, identifier), "Form checkpoint")
        if original.type != "application_form":
            raise w.WorkspaceError("Select an application-form checkpoint")
        if original.details.get("submission"):
            raise w.WorkspaceError("Submission is already confirmed; reuse the original request ID for a retry", "conflict", 409)
        snapshot = ApplicationFormContent.model_validate(original.details["structured_content"])
        siblings = db.scalars(select(m.AssistantDraft).where(m.AssistantDraft.conversation_id == original.conversation_id,
            m.AssistantDraft.type == "application_form", m.AssistantDraft.id > identifier))
        if any((row.details or {}).get("structured_content", {}).get("session_id") == snapshot.session_id for row in siblings):
            raise w.WorkspaceError("A newer checkpoint exists; confirm the latest one", "conflict", 409)
        job = w.require(db.get(m.JobApplication, snapshot.application_id), "Application")
        w.check_revision(job, revision)
        if (job.company_name, job.job_title) != (snapshot.company_name, snapshot.job_title):
            raise w.WorkspaceError("The target changed; review the form against the current company and role", "conflict", 409)
        submission = {"submitted_on": submitted_on.isoformat(), "confirmed_by": "user",
                      "values": "last_observed_snapshot; later manual edits may differ"}
        details = {**original.details, "parent_id": original.id, "submission": submission,
                   "validation": {**original.details["validation"], "state": "submission_confirmed"}}
        job.status, job.date_applied = "Applied", submitted_on
        job.revision += 1
        snapshot.application_revision = job.revision
        details["structured_content"] = snapshot.model_dump(mode="json")
        row = m.AssistantDraft(conversation_id=original.conversation_id, type="application_form", content=snapshot.model_dump_json(indent=2), details=details)
        db.add(row)
        db.flush()
        return {"application": w.application_dict(job), "draft": w.draft_dict(row)}
    return w.mutation(f"form.confirm:{identifier}", [revision, submitted_on, user_confirmed], save, request_id)
