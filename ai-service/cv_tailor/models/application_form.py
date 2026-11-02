"""Portable form checkpoints reported by the user's browser-capable agent."""
from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, field_validator, model_validator


class FormModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FormDocument(FormModel):
    draft_id: int = Field(gt=0)
    kind: Literal["resume", "cover_letter"]
    filename: str = Field(min_length=1, max_length=255)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size: int = Field(gt=0)


class ObservedFile(FormModel):
    filename: str
    size: int = Field(ge=0)
    sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class FormLimit(FormModel):
    maximum: int = Field(ge=0)
    unit: Literal["utf16", "words"]
    source: str = Field(min_length=1, max_length=1000)


FormValue = StrictStr | StrictBool | list[StrictStr] | None


class FormField(FormModel):
    key: str = Field(min_length=1, max_length=500)
    label: str = Field(min_length=1, max_length=2000)
    section: str = ""
    kind: Literal["text", "textarea", "email", "tel", "url", "number", "date", "select", "radio", "checkbox", "file", "unknown"]
    required: bool | None = None
    options: list[str] = Field(default_factory=list)
    limit: FormLimit | None = None
    original_value: FormValue = None
    proposed_value: FormValue = None
    observed_value: FormValue = None
    observation: Literal["unobserved", "observed", "unreadable", "missing"] = "unobserved"
    observed_at: datetime | None = None
    original_files: list[ObservedFile] = Field(default_factory=list)
    observed_files: list[ObservedFile] = Field(default_factory=list)
    document_id: int | None = Field(default=None, gt=0)
    source: Literal["confirmed_profile", "selected_resume", "selected_cover_letter", "user_statement", "user_existing", "none"] = "none"
    evidence: str = Field(default="", max_length=10000)
    sensitive: bool = False
    user_confirmed: bool = False
    change_confirmed: bool = False
    validation_errors: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def observed_time(self):
        if self.observation == "observed" and (self.observed_at is None or self.observed_at.utcoffset() is None):
            raise ValueError("Observed fields require observed_at with a timezone")
        if self.kind == "checkbox":
            if any(value is not None and not isinstance(value, bool) for value in
                   (self.original_value, self.proposed_value, self.observed_value)):
                raise ValueError("Checkbox values must be booleans; required consent must be checked")
        elif self.kind not in {"select", "file", "unknown"}:
            if any(value is not None and not isinstance(value, str) for value in
                   (self.original_value, self.proposed_value, self.observed_value)):
                raise ValueError("Text, date, number and radio values must be strings")
        if self.kind != "file" and (self.document_id is not None or self.original_files or self.observed_files):
            raise ValueError("Only file controls can refer to attachments")
        return self


class ApplicationFormContent(FormModel):
    schema_version: Literal[1] = 1
    session_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    application_id: int = Field(gt=0)
    application_revision: int = Field(gt=0)
    profile_revision: int = Field(gt=0)
    company_name: str = Field(min_length=1)
    job_title: str = Field(min_length=1)
    form_url: str = ""
    posting_status: Literal["active", "closed", "unknown"] = "unknown"
    identity_confirmed: bool = False
    step: str = "Application"
    inventory_complete: bool = False
    all_steps_complete: bool = False
    documents: list[FormDocument] = Field(default_factory=list, max_length=2)
    fields: list[FormField] = Field(default_factory=list, max_length=1000)

    @field_validator("form_url")
    @classmethod
    def public_url(cls, value):
        if not value:
            return value
        parsed = urlsplit(value)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Use an HTTP(S) form URL without credentials")
        return value

    @model_validator(mode="after")
    def unique_keys(self):
        if len({f.key for f in self.fields}) != len(self.fields):
            raise ValueError("Field keys must be unique, including repeated entries")
        if len({d.kind for d in self.documents}) != len(self.documents):
            raise ValueError("Select at most one document of each kind")
        return self
