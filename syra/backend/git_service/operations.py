"""
SYRA Git Service - Git operations (init, commit, history, diff).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import git
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from config import settings
from git_service.repo_path import get_repo_path, ensure_repo_path


class GitServiceError(Exception):
    """Raised when a Git operation fails."""
    pass


def _open_repo(user_id: int, repo_name: str) -> Repo:
    path = get_repo_path(user_id, repo_name)
    if not path.exists():
        raise GitServiceError(f"Repository path does not exist: {path}")
    try:
        return Repo(path)
    except InvalidGitRepositoryError:
        raise GitServiceError(f"Not a valid Git repository: {path}")


def init_repository(user_id: int, repo_name: str) -> Path:
    """
    Create the directory for the repository and initialize a new Git repository.
    Returns the path to the repo. Idempotent if repo already exists (no-op).
    """
    path = ensure_repo_path(user_id, repo_name)
    git_dir = path / ".git"
    if git_dir.exists():
        return path
    Repo.init(path, bare=False)
    return path


def commit_files(
    user_id: int,
    repo_name: str,
    message: str,
    files: dict[str, str],
    author_name: str,
    author_email: str,
) -> str:
    """
    Write the given files (path -> content) to the working tree, stage them,
    and create a commit. Returns the new commit's SHA (hexsha).
    """
    if not files:
        raise GitServiceError("No files to commit")
    repo = _open_repo(user_id, repo_name)
    root = Path(repo.working_dir)
    actor = git.Actor(author_name, author_email)

    for file_path, content in files.items():
        # Normalize path and prevent path traversal
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
        raise GitServiceError(str(e))


def get_commit_history(
    user_id: int,
    repo_name: str,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Return commit history for the repository (newest first).
    Each item: sha, message, author_name, author_email, committed_datetime.
    """
    repo = _open_repo(user_id, repo_name)
    try:
        commits = list(repo.iter_commits(max_count=skip + limit))
    except (ValueError, GitCommandError):
        return []
    # skip and limit
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


def get_commit_diff(
    user_id: int,
    repo_name: str,
    sha: str,
    parent_sha: str | None = None,
) -> str:
    """
    Return the diff for the given commit (against its first parent by default).
    If parent_sha is given, diff is from parent_sha to sha.
    """
    repo = _open_repo(user_id, repo_name)
    try:
        commit = repo.commit(sha)
    except (ValueError, GitCommandError):
        raise GitServiceError(f"Commit not found: {sha}")

    if parent_sha is not None:
        try:
            parent = repo.commit(parent_sha)
            diff = parent.diff(commit, create_patch=True)
        except (ValueError, GitCommandError):
            raise GitServiceError(f"Parent commit not found: {parent_sha}")
    else:
        if commit.parents:
            diff = commit.parents[0].diff(commit, create_patch=True)
        else:
            # Root commit: diff against Git's empty tree
            empty_tree_sha = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
            try:
                empty_tree = repo.tree(empty_tree_sha)
                diff = empty_tree.diff(commit.tree, create_patch=True)
            except (ValueError, GitCommandError):
                diff = []

    return "".join(diff_iter.diff.decode("utf-8", errors="replace") for diff_iter in diff)


def get_commit_files(
    user_id: int,
    repo_name: str,
    sha: str,
) -> dict[str, str]:
    """
    Return Python file contents at the given commit (path -> content).
    Used for static analysis of changed/touched files.
    """
    repo = _open_repo(user_id, repo_name)
    try:
        commit = repo.commit(sha)
    except (ValueError, GitCommandError):
        raise GitServiceError(f"Commit not found: {sha}")

    files = {}
    try:
        for blob in commit.tree.traverse():
            if blob.type == "blob" and blob.path.endswith(".py"):
                data = blob.data_stream.read()
                content = data.decode("utf-8", errors="replace")
                files[blob.path] = content
    except Exception as e:
        raise GitServiceError(f"Failed to read commit tree: {e}")

    return files
