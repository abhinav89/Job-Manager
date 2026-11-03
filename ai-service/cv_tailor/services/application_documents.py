"""Read and revise saved application preparation without replacing earlier drafts."""
from datetime import datetime, timezone

from sqlalchemy import select

from cv_tailor import workspace as w
from cv_tailor.models import database_models as m
from cv_tailor.models.agent_content import TextContent


DOCUMENT_KINDS = {"interview_plan", "cheat_sheet", "research"}


def list_documents(application_id):
    w.application_get(application_id)
    return [draft for draft in w.drafts_list(application_id) if draft["type"] in DOCUMENT_KINDS]


def revise_document(application_id, draft_id, content, request_id=None):
    content = TextContent(content=content).content
    if not content.strip():
        raise w.WorkspaceError("Document content cannot be blank.")

    def save(db):
        w.require(db.get(m.JobApplication, application_id), "Application")
        original = w.require(db.scalar(select(m.AssistantDraft).join(m.AssistantConversation).where(
            m.AssistantDraft.id == draft_id,
            m.AssistantConversation.job_id == application_id,
        )), "Document")
        if original.type not in DOCUMENT_KINDS:
            raise w.WorkspaceError("Only interview plans, cheat sheets, and research can be edited here.")
        versions = db.scalars(select(m.AssistantDraft).where(
            m.AssistantDraft.conversation_id == original.conversation_id,
            m.AssistantDraft.type == original.type,
            m.AssistantDraft.id > original.id,
        ))
        if any((version.details or {}).get("parent_id") == original.id for version in versions):
            raise w.WorkspaceError(
                "A newer version exists. Copy your edits, then open the latest version before saving.",
                "conflict", 409,
            )
        details = {key: value for key, value in (original.details or {}).items()
                   if key not in {"assistant_message_id", "semantic_review"}}
        details.update(source="user_edit", parent_id=original.id)
        details["structured_content"] = {**details.get("structured_content", {}), "content": content}
        draft = m.AssistantDraft(conversation_id=original.conversation_id, type=original.type,
                                 content=content, details=details)
        db.add(draft)
        db.get(m.AssistantConversation, original.conversation_id).updated_at = datetime.now(timezone.utc)
        db.flush()
        return w.draft_dict(draft)

    return w.mutation("application-document.revise", [application_id, draft_id, content], save, request_id)
