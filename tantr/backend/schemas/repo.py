"""
Repository schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RubricWeights(BaseModel):
    code_quality: float = Field(ge=0)
    efficiency: float = Field(ge=0)
    documentation: float = Field(ge=0)
    testing: float = Field(ge=0)
    commit_consistency: float = Field(ge=0)

    @field_validator(
        "code_quality",
        "efficiency",
        "documentation",
        "testing",
        "commit_consistency",
    )
    @classmethod
    def non_negative(cls, v: float) -> float:
        return float(v)


class RepoCreate(BaseModel):
    name: str
    description: str | None = None
    assignment_title: str | None = None
    assignment_brief: str | None = None
    rubric_weights: RubricWeights | dict[str, float] | None = None


class RepoUpdate(BaseModel):
    description: str | None = None
    assignment_title: str | None = None
    assignment_brief: str | None = None
    rubric_weights: RubricWeights | dict[str, float] | None = None


class RepoResponse(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int
    head_sha: str | None = None
    assignment_title: str | None = None
    assignment_brief: str | None = None
    rubric_weights: dict[str, Any] | None = None
    created_at: datetime

    class Config:
        from_attributes = True
