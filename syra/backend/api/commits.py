"""
SYRA API - Commits (create, history, diff, files, analysis).
Uses custom content-addressed VCS (not Git).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from models import get_db, User, Repository, Commit
from schemas.commit import (
    CommitCreate,
    CommitResponse,
    CommitAnalysisResponse,
    GradeResponse,
    CommitWithAnalysisResponse,
)
from api.dependencies import get_current_user
from vcs import commit_files, get_commit_diff, get_commit_files, VcsError

router = APIRouter()
log = logging.getLogger("syra.commits")


def _repo_access(db: Session, user_id: int, repo_id: int) -> Repository | None:
    return db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.owner_id == user_id,
    ).first()


def _analyze_commit_background(commit_id: int) -> None:
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
    repo = _repo_access(db, current_user.id, repo_id)
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    author_name = current_user.full_name or current_user.username
    author_email = current_user.email
    parent_sha = repo.head_sha

    try:
        sha = commit_files(
            db,
            repo,
            data.message,
            data.files,
            author_name=author_name,
            author_email=author_email,
        )
    except VcsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Resolve tree from VCS commit object
    from vcs.store import read_commit_object

    vcs_commit = read_commit_object(db, sha)
    commit = Commit(
        repository_id=repo_id,
        sha=sha,
        tree_sha=vcs_commit.get("tree"),
        parent_sha=parent_sha,
        message=data.message,
        author_name=author_name,
        author_email=author_email,
    )
    db.add(commit)
    db.commit()
    db.refresh(commit)

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
    return (
        db.query(Commit)
        .filter(Commit.repository_id == repo_id)
        .order_by(Commit.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/repos/{repo_id}/commits/{commit_id}/diff", response_class=PlainTextResponse)
def get_commit_diff_endpoint(
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
    try:
        diff_text = get_commit_diff(db, commit.sha)
    except VcsError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return PlainTextResponse(diff_text)


@router.get("/repos/{repo_id}/commits/{commit_id}/files")
def get_commit_files_endpoint(
    repo_id: int,
    commit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return path → content at this commit (for file tree / editor)."""
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
        files = get_commit_files(db, commit.sha)
    except VcsError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"sha": commit.sha, "files": files}


@router.post("/repos/{repo_id}/commits/{commit_id}/analyze")
def trigger_commit_analysis(
    repo_id: int,
    commit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
        return analyze_commit(commit_id, db)
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
    out = CommitResponse.model_validate(commit)
    analysis_data = CommitAnalysisResponse.model_validate(commit.analysis) if commit.analysis else None
    grade_data = GradeResponse.model_validate(commit.grade) if commit.grade else None
    return CommitWithAnalysisResponse(
        **out.model_dump(),
        analysis=analysis_data,
        grade=grade_data,
    )
