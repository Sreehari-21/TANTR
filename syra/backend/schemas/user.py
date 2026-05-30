"""
User schemas.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str | None
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True
