"""
SYRA Git Service - Repository path resolution and validation.
Repositories are stored at: {REPOS_BASE_PATH}/{user_id}/{repo_name}
"""

import re
from pathlib import Path

from config import settings


# Allow only safe characters in repo name (alphanumeric, underscore, hyphen, dot)
REPO_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")


def get_repo_path(user_id: int, repo_name: str) -> Path:
    """Return the absolute path for a user's repository directory."""
    if not REPO_NAME_PATTERN.match(repo_name):
        raise ValueError(f"Invalid repository name: {repo_name!r}")
    base = Path(settings.REPOS_BASE_PATH).resolve()
    return base / str(user_id) / repo_name


def ensure_repo_path(user_id: int, repo_name: str) -> Path:
    """Return repo path and ensure parent directory exists (does not create .git)."""
    path = get_repo_path(user_id, repo_name)
    path.mkdir(parents=True, exist_ok=True)
    return path
