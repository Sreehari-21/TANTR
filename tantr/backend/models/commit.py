"""
TANTR - Commit model.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.database import Base


class Commit(Base):
    __tablename__ = "commits"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    sha = Column(String(64), nullable=False, index=True)  # Custom VCS commit SHA (sha256)
    tree_sha = Column(String(64), nullable=True)
    parent_sha = Column(String(64), nullable=True)
    message = Column(Text, nullable=True)
    author_name = Column(String(255), nullable=True)
    author_email = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    repository = relationship("Repository", back_populates="commits")
    analysis = relationship("CommitAnalysis", back_populates="commit", uselist=False, cascade="all, delete-orphan")
    grade = relationship("Grade", back_populates="commit", uselist=False, cascade="all, delete-orphan")
