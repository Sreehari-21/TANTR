"""
Repository schemas.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class RepoCreate(BaseModel):
    name: str
    description: str | None = None


class RepoResponse(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int
    head_sha: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
