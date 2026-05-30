"""
SYRA Git Service - Git repository handling via GitPython.

Repositories are stored at: {REPOS_BASE_PATH}/{user_id}/{repo_name}
"""

from git_service.repo_path import get_repo_path, ensure_repo_path
from git_service.operations import (
    GitServiceError,
    init_repository,
    commit_files,
    get_commit_history,
    get_commit_diff,
    get_commit_files,
)

__all__ = [
    "get_repo_path",
    "ensure_repo_path",
    "GitServiceError",
    "init_repository",
    "commit_files",
    "get_commit_history",
    "get_commit_diff",
    "get_commit_files",
]
