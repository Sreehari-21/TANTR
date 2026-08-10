"""
TANTR - CommitAnalysis model (static analysis + AI feedback).
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.database import Base


class CommitAnalysis(Base):
    __tablename__ = "commit_analyses"

    id = Column(Integer, primary_key=True, index=True)
    commit_id = Column(Integer, ForeignKey("commits.id", ondelete="CASCADE"), nullable=False, unique=True)
    # Static analysis results (JSON from pylint, flake8, radon)
    static_analysis_raw = Column(JSON, nullable=True)
    complexity_score = Column(Float, nullable=True)
    style_score = Column(Float, nullable=True)
    documentation_score = Column(Float, nullable=True)
    warnings = Column(JSON, nullable=True)  # list of warning strings
    # AI evaluation
    ai_feedback = Column(Text, nullable=True)
    ai_suggestions = Column(JSON, nullable=True)  # list of suggestion strings
    status = Column(String(50), default="pending", nullable=False)  # pending, processing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    commit = relationship("Commit", back_populates="analysis")
