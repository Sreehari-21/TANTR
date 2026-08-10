"""
TANTR Analyzer - Structured metrics for static code analysis.
Used by static_analyzer and the commit analysis pipeline.
"""

from __future__ import annotations

from typing import Any


def analysis_result(
    complexity_score: float | None,
    style_score: float | None,
    documentation_score: float | None,
    warnings: list[str],
    raw: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a structured analysis result (0-10 scale for scores).
    Suitable for JSON serialization and CommitAnalysis storage.
    """
    def _to_ten(val: float | None) -> float | None:
        if val is None:
            return None
        # Convert 0-100 to 0-10, round to 1 decimal
        return round(val / 10.0, 1)

    return {
        "complexity_score": _to_ten(complexity_score),
        "style_score": _to_ten(style_score),
        "documentation_score": _to_ten(documentation_score),
        "warnings": list(warnings),
        "raw": raw or {},
    }


def to_commit_analysis_format(result: dict[str, Any]) -> dict[str, Any]:
    """
    Convert static analyzer result to CommitAnalysis model format.
    Keeps scores as 0-100 for DB storage; warnings as list.
    """
    return {
        "complexity_score": result.get("complexity_score"),  # keep 0-100 if from run_analysis
        "style_score": result.get("style_score"),
        "documentation_score": result.get("documentation_score"),
        "warnings": result.get("warnings", []),
        "static_analysis_raw": result.get("raw", result.get("static_analysis_raw", {})),
    }
