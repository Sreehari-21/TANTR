"""
SYRA custom VCS object store (content-addressed blobs, trees, commits).
No Git binary or Git libraries — pure application-level version control.
"""

from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.sql import func

from models.database import Base


class VcsObject(Base):
    """
    Content-addressed object.

    kind:
      - blob:   payload = file text
      - tree:   payload = JSON list of {path, type, sha}
      - commit: payload = JSON {tree, parent, message, author_name, author_email, timestamp}
    """

    __tablename__ = "vcs_objects"

    sha = Column(String(64), primary_key=True)
    kind = Column(String(16), nullable=False, index=True)
    payload = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_vcs_objects_kind_sha", "kind", "sha"),)
