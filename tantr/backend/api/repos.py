"""
TANTR API - Repositories (create, list, get, update, tree).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from models import get_db, User, Repository
from schemas.repo import RepoCreate, RepoUpdate, RepoResponse
from api.dependencies import get_current_user
from vcs import init_repository, get_commit_files, VcsError, validate_repo_name
from services.rubric import normalize_weight_dict

router = APIRouter()


def _repo_owned(db: Session, user_id: int, repo_id: int) -> Repository | None:
    return db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.owner_id == user_id,
    ).first()


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

    weights = None
    if data.rubric_weights is not None:
        raw = data.rubric_weights.model_dump() if hasattr(data.rubric_weights, "model_dump") else dict(data.rubric_weights)
        try:
            weights = normalize_weight_dict(raw)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    repo = Repository(
        name=data.name,
        description=data.description,
        owner_id=current_user.id,
        head_sha=None,
        assignment_title=data.assignment_title,
        assignment_brief=data.assignment_brief,
        rubric_weights=weights,
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
    repo = _repo_owned(db, current_user.id, repo_id)
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return repo


@router.patch("/{repo_id}", response_model=RepoResponse)
def update_repository(
    repo_id: int,
    data: RepoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = _repo_owned(db, current_user.id, repo_id)
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    payload = data.model_dump(exclude_unset=True)
    if "rubric_weights" in payload:
        raw = payload.pop("rubric_weights")
        if raw is None:
            repo.rubric_weights = None
        else:
            if hasattr(raw, "model_dump"):
                raw = raw.model_dump()
            try:
                repo.rubric_weights = normalize_weight_dict(raw)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    for key, value in payload.items():
        setattr(repo, key, value)

    db.commit()
    db.refresh(repo)
    return repo


@router.get("/{repo_id}/tree")
def get_repo_tree(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return files at HEAD as { path: content } (GitHub-like tree)."""
    repo = _repo_owned(db, current_user.id, repo_id)
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    if not repo.head_sha:
        return {"sha": None, "files": {}}
    try:
        files = get_commit_files(db, repo.head_sha)
    except VcsError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"sha": repo.head_sha, "files": files}
