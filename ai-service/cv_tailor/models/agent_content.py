from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class TextContent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=100000)


class Source(BaseModel):
    title: str
    url: str = Field(pattern=r"^https?://")


class ResearchContent(TextContent):
    sources: list[Source] = Field(min_length=1)


class Requirement(BaseModel):
    requirement: str
    importance: Literal["required", "preferred", "unclear"]
    assessment: Literal["supported", "needs_clarification", "known_gap"]
    evidence: str


class FitContent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str
    requirements: list[Requirement]
    practical_constraints: list[str] = []
