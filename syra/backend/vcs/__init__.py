"""SYRA custom VCS package — Git-shaped, no Git dependency."""

from vcs.store import (
    VcsError,
    commit_files,
    get_commit_diff,
    get_commit_files,
    get_commit_history,
    init_repository,
    validate_repo_name,
)

__all__ = [
    "VcsError",
    "init_repository",
    "commit_files",
    "get_commit_diff",
    "get_commit_files",
    "get_commit_history",
    "validate_repo_name",
]
