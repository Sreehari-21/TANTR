"""
TANTR Analyzer - Main entry: run all static analysis and return structured metrics.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from analyzer.runner_pylint import run_pylint
from analyzer.runner_flake8 import run_flake8
from analyzer.runner_radon import run_radon


def run_analysis(source_path: Path | None = None, files: dict[str, str] | None = None) -> dict[str, Any]:
    """
    Run pylint, flake8, and radon on the given source.

    Either:
      - source_path: path to a directory containing Python files, or
      - files: dict of path -> content (written to a temp dir for analysis).

    Returns structured result suitable for CommitAnalysis:
      - complexity_score: float 0-100
      - style_score: float 0-100
      - documentation_score: float 0-100
      - warnings: list[str]
      - static_analysis_raw: dict with raw tool outputs
    """
    if source_path is None and not files:
        return _empty_result()
    if source_path is not None and files is not None:
        raise ValueError("Provide either source_path or files, not both")

    if files is not None:
        with tempfile.TemporaryDirectory(prefix="tantr_analyzer_") as tmp:
            root = Path(tmp)
            for rel_path, content in files.items():
                rel_path = rel_path.lstrip("/").replace("\\", "/")
                if ".." in rel_path:
                    continue
                full = root / rel_path
                if not rel_path.endswith(".py"):
                    continue
                full.parent.mkdir(parents=True, exist_ok=True)
                full.write_text(content, encoding="utf-8")
            return _run_all(root, root)
    else:
        source_path = Path(source_path)
        if not source_path.is_dir():
            return _empty_result()
        return _run_all(source_path, source_path)


def _empty_result() -> dict[str, Any]:
    return {
        "complexity_score": None,
        "style_score": None,
        "documentation_score": None,
        "warnings": [],
        "static_analysis_raw": {},
    }


def _run_all(root: Path, source_path: Path) -> dict[str, Any]:
    pylint_result = run_pylint(source_path)
    flake8_result = run_flake8(source_path)
    radon_result = run_radon(source_path)

    warnings = []
    warnings.extend(pylint_result.get("messages") or [])
    warnings.extend(flake8_result.get("messages") or [])
    warnings.extend(radon_result.get("messages") or [])

    # Style: average of pylint and flake8 (both 0-100)
    style_scores = []
    if pylint_result.get("score") is not None:
        style_scores.append(pylint_result["score"])
    if flake8_result.get("score") is not None:
        style_scores.append(flake8_result["score"])
    style_score = (sum(style_scores) / len(style_scores)) if style_scores else None
    if style_score is not None:
        style_score = round(style_score, 2)

    # Complexity: from radon (lower complexity = higher score)
    complexity_score = radon_result.get("complexity_score")
    if complexity_score is not None and radon_result.get("maintainability_score") is not None:
        # Blend cyclomatic-based score with maintainability index
        mi = radon_result["maintainability_score"]
        complexity_score = round((complexity_score + mi) / 2.0, 2)

    # Documentation: from radon raw metrics
    documentation_score = radon_result.get("documentation_score")

    static_analysis_raw = {
        "pylint": {
            "score": pylint_result.get("score"),
            "message_count": len(pylint_result.get("messages") or []),
        },
        "flake8": {
            "score": flake8_result.get("score"),
            "issue_count": flake8_result.get("raw", {}).get("issue_count", 0),
        },
        "radon": {
            "complexity_score": radon_result.get("complexity_score"),
            "maintainability_score": radon_result.get("maintainability_score"),
            "documentation_score": radon_result.get("documentation_score"),
            "raw": radon_result.get("raw"),
        },
    }

    return {
        "complexity_score": complexity_score,
        "style_score": style_score,
        "documentation_score": documentation_score,
        "warnings": warnings,
        "static_analysis_raw": static_analysis_raw,
    }
