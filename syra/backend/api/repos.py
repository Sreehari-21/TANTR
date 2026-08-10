"""
SYRA API - Repositories (create, list, get, tree).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from models import get_db, User, Repository
from schemas.repo import RepoCreate, RepoResponse
from api.dependencies import get_current_user
from vcs import init_repository, get_commit_files, VcsError, validate_repo_name

router = APIRouter()


@router.post("", response_model=RepoResponse, status_code=status.HTTP_201_CREATED)
def create_repository(
    data: RepoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Repository).filter(
        Repository.owner_id == current_user.id,
        Repository.name == data.name,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Repository name already exists")
    try:
        validate_repo_name(data.name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    repo = Repository(
        name=data.name,
        description=data.description,
        owner_id=current_user.id,
        head_sha=None,
    )
    db.add(repo)
    db.flush()
    init_repository(db, repo)
    db.commit()
    db.refresh(repo)
    return repo


@router.get("", response_model=list[RepoResponse])
def list_my_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    return (
        db.query(Repository)
        .filter(Repository.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{repo_id}", response_model=RepoResponse)
def get_repository(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.owner_id == current_user.id,
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return repo


@router.get("/{repo_id}/tree")
def get_repo_tree(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return files at HEAD as { path: content } (GitHub-like tree)."""
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.owner_id == current_user.id,
    ).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    if not repo.head_sha:
        return {"sha": None, "files": {}}
    try:
        files = get_commit_files(db, repo.head_sha)
    except VcsError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"sha": repo.head_sha, "files": files}
