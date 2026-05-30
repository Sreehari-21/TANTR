"""
Commit and analysis schemas.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel
from typing import Any


class CommitCreate(BaseModel):
    message: str
    files: dict[str, str]  # path -> content


class CommitResponse(BaseModel):
    id: int
    repository_id: int
    sha: str
    message: str | None
    author_name: str | None
    author_email: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class CommitAnalysisResponse(BaseModel):
    id: int
    commit_id: int
    static_analysis_raw: dict[str, Any] | None
    complexity_score: float | None
    style_score: float | None
    documentation_score: float | None
    warnings: list[str] | None
    ai_feedback: str | None
    ai_suggestions: list[str] | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class GradeResponse(BaseModel):
    id: int
    commit_id: int
    code_quality: float | None
    efficiency: float | None
    documentation: float | None
    testing: float | None
    commit_consistency: float | None
    final_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class CommitWithAnalysisResponse(CommitResponse):
    analysis: CommitAnalysisResponse | None = None
    grade: GradeResponse | None = None
