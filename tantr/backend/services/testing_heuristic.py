"""
Testing score: static heuristics + optional pytest execution.
"""

from __future__ import annotations

import logging
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from config import settings

logger = logging.getLogger(__name__)

_TEST_PATH = re.compile(
    r"(^|/)(tests?/|test_[^/]+\.py|[^/]+_test\.py$)",
    re.IGNORECASE,
)


def score_testing_from_files(files: dict[str, str]) -> tuple[float, str, dict[str, Any]]:
    """
    Score testing discipline (0–100).

    Returns (score, explanation, raw_details).
    """
    if not files:
        return 35.0, "No files present; testing score starts low.", {"mode": "empty"}

    test_paths = [p for p in files if _TEST_PATH.search(p.replace("\\", "/"))]
    heuristic, h_explain = _heuristic_score(files, test_paths)

    details: dict[str, Any] = {
        "mode": "heuristic",
        "test_paths": test_paths,
        "heuristic_score": heuristic,
    }

    if settings.RUN_PYTEST_ON_ANALYZE and test_paths:
        pytest_score, pytest_explain, pytest_raw = _run_pytest(files)
        details["pytest"] = pytest_raw
        if pytest_raw.get("ran"):
            # Prefer execution when available
            score = 0.35 * heuristic + 0.65 * pytest_score
            details["mode"] = "pytest+heuristic"
            explain = f"{pytest_explain} Heuristic baseline {heuristic:.0f}."
            return round(min(100.0, score), 1), explain, details

    return round(heuristic, 1), h_explain, details


def _heuristic_score(files: dict[str, str], test_paths: list[str]) -> tuple[float, str]:
    if not test_paths:
        # Soft penalty — beginners still get a path to improve
        return 42.0, "No test files detected (looked for tests/, test_*.py, *_test.py)."

    score = 68.0
    patterns = (
        r"\bpytest\b",
        r"\bunittest\b",
        r"\bTestCase\b",
        r"\bassert\s+",
        r"@pytest\.",
        r"def\s+test_\w+",
    )
    combined = "\n".join(files.get(p, "") for p in test_paths)
    hits = sum(1 for pat in patterns if re.search(pat, combined, re.MULTILINE))
    score += min(28.0, hits * 5.0)
    explain = (
        f"Found {len(test_paths)} test file(s) with {hits}/6 testing pattern hits → {min(100, score):.0f}."
    )
    return min(100.0, score), explain


def _run_pytest(files: dict[str, str]) -> tuple[float, str, dict[str, Any]]:
    timeout = int(settings.PYTEST_TIMEOUT_SECONDS or 20)
    raw: dict[str, Any] = {"ran": False}
    try:
        with tempfile.TemporaryDirectory(prefix="tantr_pytest_") as tmp:
            root = Path(tmp)
            for rel, content in files.items():
                rel = rel.lstrip("/").replace("\\", "/")
                if ".." in rel:
                    continue
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            cmd = [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--tb=no",
                "--maxfail=5",
                str(root),
            ]
            proc = subprocess.run(
                cmd,
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            raw["ran"] = True
            raw["returncode"] = proc.returncode
            raw["stdout"] = (proc.stdout or "")[-2000:]
            raw["stderr"] = (proc.stderr or "")[-1000:]

            # Parse "N passed" / "N failed"
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            passed = _parse_count(out, r"(\d+)\s+passed")
            failed = _parse_count(out, r"(\d+)\s+failed")
            errors = _parse_count(out, r"(\d+)\s+error")
            raw["passed"] = passed
            raw["failed"] = failed
            raw["errors"] = errors

            total = passed + failed + errors
            if total == 0 and proc.returncode != 0:
                return 45.0, "Pytest ran but collected no passing tests.", raw
            if total == 0:
                return 55.0, "Pytest collected no tests.", raw

            ratio = passed / total
            score = 40.0 + ratio * 60.0
            if failed or errors:
                score = min(score, 85.0)
            explain = f"Pytest: {passed} passed, {failed} failed, {errors} errors → {score:.0f}."
            return round(score, 1), explain, raw
    except FileNotFoundError:
        raw["error"] = "pytest not installed"
        return 0.0, "Pytest unavailable.", raw
    except subprocess.TimeoutExpired:
        raw["ran"] = True
        raw["error"] = "timeout"
        return 30.0, f"Pytest timed out after {timeout}s.", raw
    except Exception as e:
        logger.warning("pytest run failed: %s", e)
        raw["error"] = str(e)
        return 0.0, "Pytest could not run.", raw


def _parse_count(text: str, pattern: str) -> int:
    m = re.search(pattern, text)
    return int(m.group(1)) if m else 0
