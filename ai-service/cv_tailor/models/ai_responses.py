"""Response shapes are separate from factual and domain validation."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClaimVerification(ResponseModel):
    supported: bool
    unsupported: list[str]


class ResumeExperience(ResponseModel):
    title: str
    company: str
    location: str
    date: str
    bullets: list[str]


class ResumeProject(ResponseModel):
    name: str
    tech: str
    date: str
    bullets: list[str]


class SkillGroup(ResponseModel):
    category: str
    items: str


class ResumeContent(ResponseModel):
    summary: str
    experience: list[ResumeExperience]
    projects: list[ResumeProject]
    skills: list[SkillGroup]
    certifications: str

    @field_validator("skills", mode="before")
    @classmethod
    def legacy_skills(cls, value):
        return [{"category": k, "items": v} for k, v in value.items()] if isinstance(value, dict) else value


class JobDetails(ResponseModel):
    job_title: str | None
    company_name: str | None
    job_description: str | None


class BlockRewrite(ResponseModel):
    id: str
    text: str
    note: str = ""


class BlockRewrites(ResponseModel):
    blocks: list[BlockRewrite]


class DeliveryFeedback(ResponseModel):
    eye_contact: str | None
    expression: str | None
    posture: str | None
    pacing: str | None


class InterviewFeedback(ResponseModel):
    content_score: int = Field(ge=1, le=10)
    delivery_score: int | None = Field(ge=1, le=10)
    overall_score: int = Field(ge=1, le=10)
    verdict: str
    strengths: list[str]
    improvements: list[str]
    tip: str
    keyword_hits: list[str]
    keyword_misses: list[str]
    delivery_feedback: DeliveryFeedback


class CodeReview(ResponseModel):
    time_complexity: str
    space_complexity: str
    correctness: Literal["correct", "partially correct", "incorrect"]
    strengths: list[str]
    issues: list[str]
    suggestions: list[str]
    overall_score: int = Field(ge=1, le=10)
    verdict: str


class CodeExample(ResponseModel):
    input: str
    output: str


class CodingProblem(ResponseModel):
    title: str
    difficulty: Literal["Easy", "Medium", "Hard"]
    tags: list[str]
    description: str
    examples: list[CodeExample]
    constraints: list[str]
    starter_code: str


class CodingProblems(ResponseModel):
    problems: list[CodingProblem]
