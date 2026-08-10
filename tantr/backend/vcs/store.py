"""
Custom content-addressed VCS for TANTR.

Git-*shaped* model (blob → tree → commit) without GitPython, Dulwich, or system git.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from models.vcs_object import VcsObject

REPO_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")


class VcsError(Exception):
    """Raised when a VCS operation fails."""


def validate_repo_name(repo_name: str) -> None:
    if not REPO_NAME_PATTERN.match(repo_name):
        raise ValueError(f"Invalid repository name: {repo_name!r}")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_blob(content: str) -> str:
    raw = content.encode("utf-8")
    return _sha256_hex(b"blob " + str(len(raw)).encode() + b"\0" + raw)


def hash_tree(entries: list[dict[str, str]]) -> str:
    normalized = sorted(
        [{"path": e["path"], "type": e["type"], "sha": e["sha"]} for e in entries],
        key=lambda x: x["path"],
    )
    raw = json.dumps(normalized, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _sha256_hex(b"tree " + str(len(raw)).encode() + b"\0" + raw)


def hash_commit(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")
    return _sha256_hex(b"commit " + str(len(raw)).encode() + b"\0" + raw)


def _put(db: Session, sha: str, kind: str, payload: str) -> None:
    existing = db.get(VcsObject, sha)
    if existing:
        return
    db.add(VcsObject(sha=sha, kind=kind, payload=payload))


def _get(db: Session, sha: str, expected: str | None = None) -> VcsObject:
    obj = db.get(VcsObject, sha)
    if not obj:
        raise VcsError(f"Object not found: {sha}")
    if expected and obj.kind != expected:
        raise VcsError(f"Expected {expected}, got {obj.kind} for {sha}")
    return obj


def store_blob(db: Session, content: str) -> str:
    sha = hash_blob(content)
    _put(db, sha, "blob", content)
    return sha


def store_tree(db: Session, files: dict[str, str]) -> str:
    entries: list[dict[str, str]] = []
    for path, content in files.items():
        rel = path.lstrip("/").replace("\\", "/")
        if not rel or ".." in rel or rel.startswith("/"):
            raise VcsError(f"Invalid file path: {path}")
        blob_sha = store_blob(db, content)
        entries.append({"path": rel, "type": "blob", "sha": blob_sha})
    tree_sha = hash_tree(entries)
    payload = json.dumps(
        sorted(entries, key=lambda e: e["path"]),
        separators=(",", ":"),
        ensure_ascii=False,
    )
    _put(db, tree_sha, "tree", payload)
    return tree_sha


def read_tree(db: Session, tree_sha: str) -> dict[str, str]:
    tree = _get(db, tree_sha, "tree")
    entries = json.loads(tree.payload)
    files: dict[str, str] = {}
    for entry in entries:
        if entry.get("type") != "blob":
            continue
        blob = _get(db, entry["sha"], "blob")
        files[entry["path"]] = blob.payload
    return files


def store_commit_object(
    db: Session,
    *,
    tree_sha: str,
    parent_sha: str | None,
    message: str,
    author_name: str,
    author_email: str,
) -> str:
    payload = {
        "tree": tree_sha,
        "parent": parent_sha,
        "message": message,
        "author_name": author_name,
        "author_email": author_email,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    sha = hash_commit(payload)
    _put(db, sha, "commit", json.dumps(payload, separators=(",", ":"), sort_keys=True))
    return sha


def read_commit_object(db: Session, sha: str) -> dict[str, Any]:
    obj = _get(db, sha, "commit")
    return json.loads(obj.payload)


def unified_diff(old: str, new: str, path: str) -> str:
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            lineterm="\n",
        )
    )


def diff_trees(db: Session, old_tree_sha: str | None, new_tree_sha: str) -> str:
    new_files = read_tree(db, new_tree_sha)
    old_files = read_tree(db, old_tree_sha) if old_tree_sha else {}
    paths = sorted(set(old_files) | set(new_files))
    parts: list[str] = []
    for path in paths:
        old = old_files.get(path, "")
        new = new_files.get(path, "")
        if old == new:
            continue
        if path not in old_files:
            parts.append(f"diff --tantr a/{path} b/{path}\nnew file mode blob\n")
        elif path not in new_files:
            parts.append(f"diff --tantr a/{path} b/{path}\ndeleted file mode blob\n")
        else:
            parts.append(f"diff --tantr a/{path} b/{path}\n")
        parts.append(unified_diff(old, new, path))
    return "".join(parts)


def init_repository(db: Session, repo) -> None:
    validate_repo_name(repo.name)
    if getattr(repo, "head_sha", None) is None:
        repo.head_sha = None


def commit_files(
    db: Session,
    repo,
    message: str,
    files: dict[str, str],
    *,
    author_name: str,
    author_email: str,
) -> str:
    if not files:
        raise VcsError("No files to commit")

    parent_sha = getattr(repo, "head_sha", None)
    merged = dict(files)
    if parent_sha:
        try:
            parent = read_commit_object(db, parent_sha)
            prev = read_tree(db, parent["tree"])
            merged = {**prev, **files}
        except VcsError:
            pass

    tree_sha = store_tree(db, merged)
    sha = store_commit_object(
        db,
        tree_sha=tree_sha,
        parent_sha=parent_sha,
        message=message,
        author_name=author_name,
        author_email=author_email,
    )
    repo.head_sha = sha
    db.flush()
    return sha


def get_commit_files(db: Session, sha: str) -> dict[str, str]:
    commit = read_commit_object(db, sha)
    return read_tree(db, commit["tree"])


def get_commit_diff(db: Session, sha: str) -> str:
    commit = read_commit_object(db, sha)
    parent = commit.get("parent")
    old_tree = None
    if parent:
        parent_obj = read_commit_object(db, parent)
        old_tree = parent_obj["tree"]
    return diff_trees(db, old_tree, commit["tree"])


def get_commit_history(
    db: Session,
    head_sha: str | None,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    sha = head_sha
    seen = 0
    while sha and len(out) < limit:
        try:
            c = read_commit_object(db, sha)
        except VcsError:
            break
        if seen >= skip:
            out.append(
                {
                    "sha": sha,
                    "message": c.get("message") or "",
                    "author_name": c.get("author_name"),
                    "author_email": c.get("author_email"),
                    "committed_datetime": c.get("timestamp"),
                    "tree": c.get("tree"),
                    "parent": c.get("parent"),
                }
            )
        seen += 1
        sha = c.get("parent")
    return out
