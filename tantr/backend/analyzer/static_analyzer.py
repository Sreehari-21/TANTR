"""
TANTR Analyzer - Static code analysis entry point.
Accepts file path or source code; runs pylint, flake8, radon.
Returns structured JSON for use by the commit analysis pipeline.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from analyzer.analysis import run_analysis
from analyzer.metrics import analysis_result


def analyze(
    file_path: str | Path | None = None,
    source_code: str | None = None,
    *,
    files: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Run static analysis (pylint, flake8, radon) and return structured metrics.

    Accepts either:
      - file_path: path to a .py file or directory containing Python files
      - source_code: Python source as string (analyzed as temp file)
      - files: dict of path -> content (multiple files, e.g. from commit)

    Returns:
      {
        "complexity_score": 7,      # 0-10
        "style_score": 8,           # 0-10
        "documentation_score": 4,   # 0-10
        "warnings": ["unused variable", "missing docstring"],
        "raw": { ... }             # full tool outputs for pipeline
      }
    """
    if files is not None:
        raw = run_analysis(files=files)
    elif source_code is not None:
        with tempfile.TemporaryDirectory(prefix="tantr_") as tmp:
            py_file = Path(tmp) / "code.py"
            py_file.write_text(source_code, encoding="utf-8")
            raw = run_analysis(source_path=Path(tmp))
    elif file_path is not None:
        path = Path(file_path)
        if path.is_file() and path.suffix == ".py":
            raw = run_analysis(files={path.name: path.read_text(encoding="utf-8", errors="replace")})
        elif path.is_dir():
            raw = run_analysis(source_path=path)
        else:
            return analysis_result(None, None, None, ["Invalid file path or not a Python file"], {})
    else:
        return analysis_result(None, None, None, ["Provide file_path, source_code, or files"], {})

    # run_analysis returns 0-100 scores; metrics.analysis_result converts to 0-10
    return analysis_result(
        complexity_score=raw.get("complexity_score"),
        style_score=raw.get("style_score"),
        documentation_score=raw.get("documentation_score"),
        warnings=raw.get("warnings", []),
        raw=raw.get("static_analysis_raw", raw),
    )
