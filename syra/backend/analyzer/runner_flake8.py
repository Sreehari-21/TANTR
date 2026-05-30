"""
SYRA Analyzer - Flake8 runner.
Returns issue count, score (0-100), and list of messages.
"""

import subprocess
from pathlib import Path
from typing import Any


def run_flake8(source_path: Path) -> dict[str, Any]:
    """
    Run flake8 on all Python files under source_path.
    Returns {"score": float 0-100, "messages": list[str], "raw": ...}.
    """
    py_files = list(source_path.rglob("*.py"))
    if not py_files:
        return {"score": 100.0, "messages": [], "raw": {"issue_count": 0}}

    paths = [str(p) for p in py_files]
    try:
        result = subprocess.run(
            ["flake8", "--max-line-length=120", "--extend-ignore=E203,W503"] + paths,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(source_path),
        )
        output = (result.stdout or "") + (result.stderr or "")
        lines = [line.strip() for line in output.strip().splitlines() if line.strip()]
    except subprocess.TimeoutExpired:
        return {"score": 0.0, "messages": ["flake8 timed out"], "raw": None}
    except FileNotFoundError:
        return {"score": None, "messages": ["flake8 not installed"], "raw": None}
    except Exception as e:
        return {"score": None, "messages": [f"flake8 error: {e}"], "raw": None}

    count = len(lines)
    # Score: 100 - min(100, count * 3), so each issue costs up to 3 points
    score = max(0.0, min(100.0, 100.0 - count * 3.0))

    return {
        "score": round(score, 2),
        "messages": lines,
        "raw": {"issue_count": count},
    }
