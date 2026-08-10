"""
SYRA - Celery task for commit analysis.
Commit created → job enqueued → static analysis → AI evaluation → result stored.
"""

from celery_app import app
from models.database import SessionLocal
from models import CommitAnalysis
from services.commit_analysis_service import analyze_commit


@app.task(bind=True, name="tasks.analyze_commit")
def analyze_commit_task(self, commit_id: int) -> dict:
    """
    Process a commit through the full analysis pipeline in the background.
    Called automatically when a commit is created.
    """
    db = SessionLocal()
    try:
        # Mark as processing
        existing = db.query(CommitAnalysis).filter(CommitAnalysis.commit_id == commit_id).first()
        if existing:
            existing.status = "processing"
        else:
            db.add(CommitAnalysis(commit_id=commit_id, status="processing"))
        db.commit()

        result = analyze_commit(commit_id, db)
        return result
    finally:
        db.close()
