"""
SYRA API - Commits (create, history, diff, get analysis).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from models import get_db, User, Repository, Commit, CommitAnalysis, Grade
from schemas.commit import CommitCreate, CommitResponse, CommitAnalysisResponse, GradeResponse, CommitWithAnalysisResponse
from api.dependencies import get_current_user
from git_service import get_commit_diff, GitServiceError

router = APIRouter()
log = logging.getLogger("syra.commits")


def _repo_access(db: Session, user_id: int, repo_id: int) -> Repository | None:
    return db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.owner_id == user_id,
    ).first()


def _analyze_commit_background(commit_id: int) -> None:
    """Run analysis in-process when Celery is unavailable (local dev)."""
    from tasks.commit_tasks import analyze_commit_task

    try:
        analyze_commit_task(commit_id)
    except Exception:
        log.exception("In-process commit analysis failed for commit_id=%s", commit_id)


@router.post("/repos/{repo_id}/commits", response_model=CommitResponse, status_code=status.HTTP_201_CREATED)
def create_commit(
    repo_id: int,
    data: CommitCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from git_service import commit_files, GitServiceError

    repo = _repo_access(db, current_user.id, repo_id)
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    author_name = current_user.full_name or current_user.username
    author_email = current_user.email
    try:
        sha = commit_files(
            current_user.id,
            repo.name,
            data.message,
            data.files,
            author_name=author_name,
            author_email=author_email,
        )
    except GitServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    commit = Commit(
        repository_id=repo_id,
        sha=sha,
        message=data.message,
        author_name=author_name,
        author_email=author_email,
    )
    db.add(commit)
    db.commit()
    db.refresh(commit)
    # Prefer Celery; fall back to in-process analysis so dev works without a worker
    enqueued = False
    try:
        from tasks.commit_tasks import analyze_commit_task

        analyze_commit_task.delay(commit.id)
        enqueued = True
    except Exception as e:
        log.warning(
            "Celery enqueue failed for commit_id=%s (%s); using background task",
            commit.id,
            e,
        )
    if not enqueued:
        background_tasks.add_task(_analyze_commit_background, commit.id)
    return commit


@router.get("/repos/{repo_id}/commits", response_model=list[CommitResponse])
def commit_history(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    repo = _repo_access(db, current_user.id, repo_id)
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    commits = db.query(Commit).filter(Commit.repository_id == repo_id).order_by(Commit.created_at.desc()).offset(skip).limit(limit).all()
    return commits


@router.get("/repos/{repo_id}/commits/{commit_id}/diff", response_class=PlainTextResponse)
def get_commit_diff_endpoint(
    repo_id: int,
    commit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the Git diff for the given commit (vs its parent)."""
    repo = _repo_access(db, current_user.id, repo_id)
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    commit = db.query(Commit).filter(
        Commit.id == commit_id,
        Commit.repository_id == repo_id,
    ).first()
    if not commit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commit not found")
    try:
        diff_text = get_commit_diff(current_user.id, repo.name, commit.sha)
    except GitServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return PlainTextResponse(diff_text)


@router.post("/repos/{repo_id}/commits/{commit_id}/analyze")
def trigger_commit_analysis(
    repo_id: int,
    commit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run the full analysis pipeline for this commit."""
    from services.commit_analysis_service import analyze_commit, CommitAnalysisError

    repo = _repo_access(db, current_user.id, repo_id)
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    commit = db.query(Commit).filter(
        Commit.id == commit_id,
        Commit.repository_id == repo_id,
    ).first()
    if not commit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commit not found")
    try:
        result = analyze_commit(commit_id, db)
        return result
    except CommitAnalysisError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/repos/{repo_id}/commits/{commit_id}/analysis", response_model=CommitWithAnalysisResponse)
def get_commit_analysis(
    repo_id: int,
    commit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = _repo_access(db, current_user.id, repo_id)
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    commit = db.query(Commit).filter(
        Commit.id == commit_id,
        Commit.repository_id == repo_id,
    ).first()
    if not commit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commit not found")
    # Build response with optional analysis and grade
    out = CommitResponse.model_validate(commit)
    analysis_data = None
    if commit.analysis:
        analysis_data = CommitAnalysisResponse.model_validate(commit.analysis)
    grade_data = None
    if commit.grade:
        grade_data = GradeResponse.model_validate(commit.grade)
    return CommitWithAnalysisResponse(
        **out.model_dump(),
        analysis=analysis_data,
        grade=grade_data,
    )
