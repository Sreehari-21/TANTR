"""
SYRA API - Repositories (create, list, get).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from models import get_db, User, Repository
from schemas.repo import RepoCreate, RepoResponse
from api.dependencies import get_current_user
from git_service import init_repository, GitServiceError

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
        init_repository(current_user.id, data.name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except GitServiceError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    repo = Repository(name=data.name, description=data.description, owner_id=current_user.id)
    db.add(repo)
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
    repos = db.query(Repository).filter(Repository.owner_id == current_user.id).offset(skip).limit(limit).all()
    return repos


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
