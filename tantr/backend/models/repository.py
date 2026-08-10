"""
TANTR - Repository model.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # Custom VCS HEAD commit sha (content-addressed, not Git)
    head_sha = Column(String(64), nullable=True, index=True)
    # Optional course assignment + custom rubric weights (percentages or fractions)
    assignment_title = Column(String(255), nullable=True)
    assignment_brief = Column(Text, nullable=True)
    rubric_weights = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="repositories")
    commits = relationship("Commit", back_populates="repository", cascade="all, delete-orphan")
