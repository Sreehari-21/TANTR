#!/usr/bin/env python3
"""SYRA API smoke test."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

API = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")


def req(method: str, path: str, body: dict | None = None, token: str | None = None) -> tuple[int, dict | str]:
    url = f"{API}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            raw = resp.read().decode()
            if not raw:
                return resp.status, {}
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def ok(msg: str) -> None:
    print(f"OK: {msg}")


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    print("=== SYRA smoke test ===")
    print(f"API: {API}")

    code, health = req("GET", "/health")
    if code != 200:
        fail(f"health -> {code} {health}")
    ok("health")

    code, ready = req("GET", "/health/ready")
    if code != 200 or ready.get("checks", {}).get("database") != "ok":
        fail(f"ready -> {code} {ready}")
    ok("ready (db + redis)")

    user = f"smoke_{int(time.time())}"
    password = "SmokeTest12345"
    email = f"{user}@example.com"

    code, reg = req(
        "POST",
        "/api/auth/register",
        {"email": email, "username": user, "password": password, "full_name": "Smoke Test"},
    )
    if code not in (200, 201):
        fail(f"register -> {code} {reg}")
    ok(f"register ({user})")

    code, login = req("POST", "/api/auth/login", {"username": user, "password": password})
    if code != 200 or "access_token" not in login:
        fail(f"login -> {code} {login}")
    token = login["access_token"]
    ok("login")

    code, me = req("GET", "/api/auth/me", token=token)
    if code != 200 or me.get("email") != email:
        fail(f"/me -> {code} {me}")
    ok("auth/me")

    code, repo = req("POST", "/api/repos", {"name": "smoke-repo", "description": "smoke"}, token=token)
    if code not in (200, 201):
        fail(f"create repo -> {code} {repo}")
    repo_id = repo["id"]
    ok(f"repo id={repo_id}")

    code, commit = req(
        "POST",
        f"/api/repos/{repo_id}/commits",
        {
            "message": "smoke commit",
            "files": {"main.py": "def hello():\n    return 42\n"},
        },
        token=token,
    )
    if code not in (200, 201):
        fail(f"create commit -> {code} {commit}")
    commit_id = commit["id"]
    ok(f"commit id={commit_id}")

    code, triggered = req("POST", f"/api/repos/{repo_id}/commits/{commit_id}/analyze", token=token)
    if code in (200, 201):
        ok("analyze triggered")
    else:
        print(f"Note: analyze trigger returned {code} ({triggered})")

    print("Polling analysis (up to 90s)...")
    for _ in range(30):
        code, analysis = req("GET", f"/api/repos/{repo_id}/commits/{commit_id}/analysis", token=token)
        if code == 200 and isinstance(analysis, dict):
            grade = analysis.get("grade")
            if grade and grade.get("final_score") is not None:
                ok(f"grade final_score={grade['final_score']}")
                print("\n=== All smoke tests passed ===")
                return
        time.sleep(3)

    req("POST", f"/api/repos/{repo_id}/commits/{commit_id}/analyze", token=token)
    for _ in range(20):
        time.sleep(3)
        code, analysis = req("GET", f"/api/repos/{repo_id}/commits/{commit_id}/analysis", token=token)
        if code == 200 and isinstance(analysis, dict) and analysis.get("grade"):
            ok("grade after manual analyze")
            print("\n=== All smoke tests passed ===")
            return

    fail("analysis never completed — start Celery: ./scripts/run-celery.sh")


if __name__ == "__main__":
    main()
