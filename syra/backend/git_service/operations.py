"""
SYRA Git Service - Git operations (init, commit, history, diff).

Uses GitPython when the system `git` binary is available; otherwise falls back to
Dulwich (pure Python) so local dev works without Xcode Command Line Tools.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypeVar

from config import settings
from git_service.repo_path import ensure_repo_path, get_repo_path

T = TypeVar("T")


class GitServiceError(Exception):
    """Raised when a Git operation fails."""

    pass


def _use_gitpython() -> bool:
    try:
        import git  # noqa: F401

        return True
    except ImportError:
        return False


def _with_git_backend(fn_gitpython: Callable[..., T], fn_dulwich: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    if _use_gitpython():
        return fn_gitpython(*args, **kwargs)
    return fn_dulwich(*args, **kwargs)


# --- GitPython backend ---


def _open_repo_gitpython(user_id: int, repo_name: str):
    import git
    from git import Repo
    from git.exc import InvalidGitRepositoryError

    path = get_repo_path(user_id, repo_name)
    if not path.exists():
        raise GitServiceError(f"Repository path does not exist: {path}")
    try:
        return Repo(path)
    except InvalidGitRepositoryError:
        raise GitServiceError(f"Not a valid Git repository: {path}")


def _init_repository_gitpython(user_id: int, repo_name: str) -> Path:
    from git import Repo

    path = ensure_repo_path(user_id, repo_name)
    if (path / ".git").exists():
        return path
    Repo.init(path, bare=False)
    return path


def _commit_files_gitpython(
    user_id: int,
    repo_name: str,
    message: str,
    files: dict[str, str],
    author_name: str,
    author_email: str,
) -> str:
    import git
    from git.exc import GitCommandError

    if not files:
        raise GitServiceError("No files to commit")
    repo = _open_repo_gitpython(user_id, repo_name)
    root = Path(repo.working_dir)
    actor = git.Actor(author_name, author_email)

    for file_path, content in files.items():
        file_path = file_path.lstrip("/").replace("\\", "/")
        if ".." in file_path or file_path.startswith("/"):
            raise GitServiceError(f"Invalid file path: {file_path}")
        full_path = root / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

    paths_to_add = [p.lstrip("/").replace("\\", "/") for p in files.keys()]
    repo.index.add(paths_to_add)

    try:
        commit = repo.index.commit(message, author=actor, committer=actor)
        return commit.hexsha
    except GitCommandError as e:
        raise GitServiceError(str(e)) from e


def _get_commit_history_gitpython(
    user_id: int,
    repo_name: str,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    from git.exc import GitCommandError

    repo = _open_repo_gitpython(user_id, repo_name)
    try:
        commits = list(repo.iter_commits(max_count=skip + limit))
    except (ValueError, GitCommandError):
        return []
    commits = commits[skip : skip + limit]
    return [
        {
            "sha": c.hexsha,
            "message": c.message.strip() if c.message else "",
            "author_name": c.author.name if c.author else None,
            "author_email": c.author.email if c.author else None,
            "committed_datetime": c.committed_datetime,
        }
        for c in commits
    ]


def _get_commit_diff_gitpython(
    user_id: int,
    repo_name: str,
    sha: str,
    parent_sha: str | None = None,
) -> str:
    from git.exc import GitCommandError

    repo = _open_repo_gitpython(user_id, repo_name)
    try:
        commit = repo.commit(sha)
    except (ValueError, GitCommandError):
        raise GitServiceError(f"Commit not found: {sha}") from None

    if parent_sha is not None:
        try:
            parent = repo.commit(parent_sha)
            diff = parent.diff(commit, create_patch=True)
        except (ValueError, GitCommandError):
            raise GitServiceError(f"Parent commit not found: {parent_sha}") from None
    elif commit.parents:
        diff = commit.parents[0].diff(commit, create_patch=True)
    else:
        empty_tree_sha = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
        try:
            empty_tree = repo.tree(empty_tree_sha)
            diff = empty_tree.diff(commit.tree, create_patch=True)
        except (ValueError, GitCommandError):
            diff = []

    return "".join(diff_iter.diff.decode("utf-8", errors="replace") for diff_iter in diff)


def _get_commit_files_gitpython(user_id: int, repo_name: str, sha: str) -> dict[str, str]:
    from git.exc import GitCommandError

    repo = _open_repo_gitpython(user_id, repo_name)
    try:
        commit = repo.commit(sha)
    except (ValueError, GitCommandError):
        raise GitServiceError(f"Commit not found: {sha}") from None

    files: dict[str, str] = {}
    try:
        for blob in commit.tree.traverse():
            if blob.type == "blob" and blob.path.endswith(".py"):
                data = blob.data_stream.read()
                files[blob.path] = data.decode("utf-8", errors="replace")
    except Exception as e:
        raise GitServiceError(f"Failed to read commit tree: {e}") from e
    return files


# --- Dulwich backend ---


def _open_repo_dulwich(user_id: int, repo_name: str):
    from dulwich.errors import NotGitRepository
    from dulwich.repo import Repo

    path = get_repo_path(user_id, repo_name)
    if not path.exists():
        raise GitServiceError(f"Repository path does not exist: {path}")
    try:
        return Repo(str(path))
    except NotGitRepository:
        raise GitServiceError(f"Not a valid Git repository: {path}") from None


def _init_repository_dulwich(user_id: int, repo_name: str) -> Path:
    from dulwich.repo import Repo

    path = ensure_repo_path(user_id, repo_name)
    if (path / ".git").exists():
        return path
    # Directory may already exist from ensure_repo_path; do not pass mkdir=True.
    Repo.init(str(path))
    return path


def _normalize_paths(files: dict[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for file_path, content in files.items():
        rel = file_path.lstrip("/").replace("\\", "/")
        if ".." in rel or rel.startswith("/"):
            raise GitServiceError(f"Invalid file path: {file_path}")
        normalized[rel] = content
    return normalized


def _commit_files_dulwich(
    user_id: int,
    repo_name: str,
    message: str,
    files: dict[str, str],
    author_name: str,
    author_email: str,
) -> str:
    from dulwich import porcelain

    if not files:
        raise GitServiceError("No files to commit")
    repo = _open_repo_dulwich(user_id, repo_name)
    root = Path(repo.path)
    normalized = _normalize_paths(files)

    for rel, content in normalized.items():
        full_path = root / rel
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

    paths = [rel.encode("utf-8") for rel in normalized]
    porcelain.add(repo, paths=paths)
    commit_sha = porcelain.commit(
        repo,
        message=message.encode("utf-8"),
        author=f"{author_name} <{author_email}>".encode("utf-8"),
        committer=f"{author_name} <{author_email}>".encode("utf-8"),
    )
    return commit_sha.decode("ascii")


def _get_commit_history_dulwich(
    user_id: int,
    repo_name: str,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    repo = _open_repo_dulwich(user_id, repo_name)
    commits: list[dict[str, Any]] = []
    for entry in repo.get_walker():
        commit = entry.commit
        author = commit.author.decode("utf-8", errors="replace")
        name, email = author, None
        if b"<" in commit.author and b">" in commit.author:
            left, right = author.rsplit("<", 1)
            name = left.strip()
            email = right.rstrip(">").strip()
        commits.append(
            {
                "sha": commit.id.decode("ascii"),
                "message": commit.message.decode("utf-8", errors="replace").strip(),
                "author_name": name,
                "author_email": email,
                "committed_datetime": datetime.fromtimestamp(commit.commit_time, tz=timezone.utc),
            }
        )
    return commits[skip : skip + limit]


def _get_commit_diff_dulwich(
    user_id: int,
    repo_name: str,
    sha: str,
    parent_sha: str | None = None,
) -> str:
    from dulwich.objects import Tree
    from dulwich.patch import write_tree_diff

    repo = _open_repo_dulwich(user_id, repo_name)
    sha_b = sha.encode("ascii")
    if sha_b not in repo:
        raise GitServiceError(f"Commit not found: {sha}")

    commit = repo[sha_b]
    if parent_sha is not None:
        parent_b = parent_sha.encode("ascii")
        if parent_b not in repo:
            raise GitServiceError(f"Parent commit not found: {parent_sha}")
        old_tree = repo[parent_b].tree
    elif commit.parents:
        old_tree = repo[commit.parents[0]].tree
    else:
        old_tree = Tree()

    new_tree = commit.tree
    out = io.BytesIO()
    write_tree_diff(out, repo.object_store, old_tree, new_tree)
    return out.getvalue().decode("utf-8", errors="replace")


def _get_commit_files_dulwich(user_id: int, repo_name: str, sha: str) -> dict[str, str]:
    repo = _open_repo_dulwich(user_id, repo_name)
    sha_b = sha.encode("ascii")
    if sha_b not in repo:
        raise GitServiceError(f"Commit not found: {sha}")

    commit = repo[sha_b]
    files: dict[str, str] = {}

    def walk_tree(tree_sha: bytes, prefix: str = "") -> None:
        tree = repo[tree_sha]
        for entry in tree.items():
            name = entry.path.decode("utf-8", errors="replace")
            rel = f"{prefix}/{name}" if prefix else name
            if entry.mode >> 12 == 0o04:
                walk_tree(entry.sha, rel)
            elif rel.endswith(".py"):
                blob = repo[entry.sha]
                files[rel] = blob.data.decode("utf-8", errors="replace")

    walk_tree(commit.tree)
    return files


# --- Public API ---


def init_repository(user_id: int, repo_name: str) -> Path:
    """Create the directory for the repository and initialize a new Git repository."""
    return _with_git_backend(_init_repository_gitpython, _init_repository_dulwich, user_id, repo_name)


def commit_files(
    user_id: int,
    repo_name: str,
    message: str,
    files: dict[str, str],
    author_name: str,
    author_email: str,
) -> str:
    """Write files, stage them, and create a commit. Returns the new commit SHA."""
    return _with_git_backend(
        _commit_files_gitpython,
        _commit_files_dulwich,
        user_id,
        repo_name,
        message,
        files,
        author_name,
        author_email,
    )


def get_commit_history(
    user_id: int,
    repo_name: str,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return commit history for the repository (newest first)."""
    return _with_git_backend(
        _get_commit_history_gitpython,
        _get_commit_history_dulwich,
        user_id,
        repo_name,
        skip,
        limit,
    )


def get_commit_diff(
    user_id: int,
    repo_name: str,
    sha: str,
    parent_sha: str | None = None,
) -> str:
    """Return the diff for the given commit (against its first parent by default)."""
    return _with_git_backend(
        _get_commit_diff_gitpython,
        _get_commit_diff_dulwich,
        user_id,
        repo_name,
        sha,
        parent_sha,
    )


def get_commit_files(user_id: int, repo_name: str, sha: str) -> dict[str, str]:
    """Return Python file contents at the given commit (path -> content)."""
    return _with_git_backend(_get_commit_files_gitpython, _get_commit_files_dulwich, user_id, repo_name, sha)
