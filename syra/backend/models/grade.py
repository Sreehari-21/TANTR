"""
SYRA - Grade model (final score for a commit).
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.database import Base


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    commit_id = Column(Integer, ForeignKey("commits.id", ondelete="CASCADE"), nullable=False, unique=True)
    # Component scores (0–100 scale, then weighted)
    code_quality = Column(Float, nullable=True)
    efficiency = Column(Float, nullable=True)
    documentation = Column(Float, nullable=True)
    testing = Column(Float, nullable=True)
    commit_consistency = Column(Float, nullable=True)
    # Final score from rubric engine (weighted metrics + optional AI blend)
    final_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    commit = relationship("Commit", back_populates="grade")
