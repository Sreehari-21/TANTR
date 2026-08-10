"""
TANTR Professor Rubric Engine.

Computes per-metric scores (0–100), difficulty-aware adjustments, optional AI blend,
and human-readable explanations for the frontend.
"""

from __future__ import annotations

import re
from typing import Any

from config import settings


WEIGHTS = {
    "code_quality": "GRADE_WEIGHT_QUALITY",
    "efficiency": "GRADE_WEIGHT_EFFICIENCY",
    "documentation": "GRADE_WEIGHT_DOCUMENTATION",
    "testing": "GRADE_WEIGHT_TESTING",
    "commit_consistency": "GRADE_WEIGHT_CONSISTENCY",
}

_ALGO_KEYWORDS = re.compile(
    r"\b(sort|search|binary|dfs|bfs|dijkstra|dynamic|recursion|memoiz|"
    r"graph|tree|heap|hash|knapsack|backtrack|complexity|O\(|Big.?O)\b",
    re.IGNORECASE,
)

_COMMIT_MSG_GOOD = re.compile(
    r"^(feat|fix|docs|refactor|test|chore|perf)(\(.+\))?:|^[A-Z].{8,}",
    re.MULTILINE,
)


def normalize_score(val: Any, *, missing: float | None = None) -> float | None:
    """Normalize analyzer scores to 0–100. Returns None if missing and no default."""
    if val is None:
        return missing
    v = float(val)
    if v <= 10:
        return round(min(100.0, v * 10.0), 2)
    return round(min(100.0, max(0.0, v)), 2)


def estimate_difficulty(files: dict[str, str], analysis_results: dict[str, Any]) -> dict[str, Any]:
    """
    Estimate commit difficulty: introductory | intermediate | advanced.
    Used to adjust efficiency expectations (harder work isn't punished for complexity alone).
    """
    py_files = {p: c for p, c in files.items() if p.endswith(".py")}
    loc = sum(len(c.splitlines()) for c in py_files.values())
    algo_hits = sum(len(_ALGO_KEYWORDS.findall(c)) for c in py_files.values())
    warnings = len(analysis_results.get("warnings") or [])
    complexity = normalize_score(analysis_results.get("complexity_score"), missing=70.0) or 70.0

    # Higher cyclomatic difficulty when complexity_score is lower (more complex code)
    complexity_penalty = max(0.0, 85.0 - complexity)

    points = 0
    if loc > 80:
        points += 2
    elif loc > 30:
        points += 1
    if algo_hits >= 3:
        points += 2
    elif algo_hits >= 1:
        points += 1
    if complexity_penalty >= 25:
        points += 2
    elif complexity_penalty >= 10:
        points += 1
    if warnings >= 8:
        points -= 1

    if points >= 4:
        level = "advanced"
        multiplier = 1.08
    elif points >= 2:
        level = "intermediate"
        multiplier = 1.03
    else:
        level = "introductory"
        multiplier = 1.0

    return {
        "level": level,
        "multiplier": multiplier,
        "signals": {
            "loc": loc,
            "algo_keyword_hits": algo_hits,
            "complexity_score": complexity,
            "warnings": warnings,
            "points": points,
        },
    }


def score_code_quality(analysis_results: dict[str, Any]) -> tuple[float, str]:
    style = normalize_score(analysis_results.get("style_score"))
    complexity = normalize_score(analysis_results.get("complexity_score"))
    warnings = analysis_results.get("warnings") or []

    parts: list[float] = []
    if style is not None:
        parts.append(style)
    if complexity is not None:
        parts.append(complexity * 0.85 + 15.0)  # readability from maintainability blend

    if not parts:
        base = 50.0
        explain = "No style/complexity signals found; starting from a neutral baseline (50)."
    else:
        base = sum(parts) / len(parts)
        explain = (
            f"Style {style if style is not None else 'n/a'} and "
            f"structure {complexity if complexity is not None else 'n/a'} "
            f"averaged for code quality."
        )

    penalty = min(20.0, len(warnings) * 1.5)
    score = max(0.0, min(100.0, base - penalty))
    if penalty:
        explain += f" Deducted {penalty:.0f} for {len(warnings)} analyzer warning(s)."
    return round(score, 2), explain


def score_efficiency(analysis_results: dict[str, Any], difficulty: dict[str, Any]) -> tuple[float, str]:
    """
    Efficiency rewards maintainable complexity — not 'write nothing'.
    Difficulty multiplier softens penalties for advanced algorithmic work.
    """
    complexity = normalize_score(analysis_results.get("complexity_score"), missing=55.0) or 55.0
    raw = analysis_results.get("static_analysis_raw") or {}
    radon = raw.get("radon") or {}
    mi = radon.get("maintainability_score")
    mi_n = normalize_score(mi, missing=complexity) or complexity

    # Blend: 60% complexity score, 40% maintainability
    base = 0.60 * complexity + 0.40 * mi_n
    adjusted = min(100.0, base * float(difficulty.get("multiplier") or 1.0))
    explain = (
        f"Efficiency from complexity ({complexity:.0f}) and maintainability ({mi_n:.0f}). "
        f"Difficulty={difficulty.get('level')} (×{difficulty.get('multiplier')})."
    )
    return round(adjusted, 2), explain


def score_documentation(analysis_results: dict[str, Any], files: dict[str, str]) -> tuple[float, str]:
    doc = normalize_score(analysis_results.get("documentation_score"))
    py_files = {p: c for p, c in files.items() if p.endswith(".py")}
    if not py_files:
        return 40.0, "No Python files to score documentation."

    docstring_hits = 0
    def_count = 0
    for content in py_files.values():
        def_count += len(re.findall(r"^\s*def\s+\w+", content, re.MULTILINE))
        def_count += len(re.findall(r"^\s*class\s+\w+", content, re.MULTILINE))
        docstring_hits += len(re.findall(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', content))

    coverage = 0.0
    if def_count > 0:
        coverage = min(100.0, (docstring_hits / def_count) * 100.0)
    else:
        coverage = 60.0 if docstring_hits else 35.0

    if doc is None:
        score = coverage
        explain = f"Documentation from docstring coverage (~{coverage:.0f}%)."
    else:
        score = 0.55 * doc + 0.45 * coverage
        explain = f"Blended analyzer docs ({doc:.0f}) with docstring coverage ({coverage:.0f})."
    return round(min(100.0, score), 2), explain


def score_consistency(
    analysis_results: dict[str, Any],
    commit_message: str | None,
    files: dict[str, str],
) -> tuple[float, str]:
    warnings = analysis_results.get("warnings") or []
    score = 100.0
    notes: list[str] = []

    warn_penalty = min(35.0, len(warnings) * 4.0)
    score -= warn_penalty
    if warn_penalty:
        notes.append(f"−{warn_penalty:.0f} for {len(warnings)} warning(s)")

    msg = (commit_message or "").strip()
    if not msg or msg.lower() in {"update", "fix", "wip", "commit", "asdf"}:
        score -= 20.0
        notes.append("−20 for weak/empty commit message")
    elif len(msg) < 10:
        score -= 12.0
        notes.append("−12 for short commit message")
    elif _COMMIT_MSG_GOOD.search(msg):
        score += 5.0
        notes.append("+5 for clear commit message")

    if not files:
        score -= 10.0
        notes.append("−10 for empty file set")

    score = max(0.0, min(100.0, score))
    explain = "Commit consistency: " + ("; ".join(notes) if notes else "clean signals.")
    return round(score, 2), explain


def get_weights(override: dict[str, float] | None = None) -> dict[str, float]:
    if override:
        return normalize_weight_dict(override)
    w = {
        "code_quality": float(settings.GRADE_WEIGHT_QUALITY),
        "efficiency": float(settings.GRADE_WEIGHT_EFFICIENCY),
        "documentation": float(settings.GRADE_WEIGHT_DOCUMENTATION),
        "testing": float(settings.GRADE_WEIGHT_TESTING),
        "commit_consistency": float(settings.GRADE_WEIGHT_CONSISTENCY),
    }
    total = sum(w.values()) or 1.0
    return {k: v / total for k, v in w.items()}


def normalize_weight_dict(raw: dict[str, Any]) -> dict[str, float]:
    """Accept percentages (sum≈100) or fractions (sum≈1); return normalized fractions."""
    keys = (
        "code_quality",
        "efficiency",
        "documentation",
        "testing",
        "commit_consistency",
    )
    missing = [k for k in keys if k not in raw]
    if missing:
        raise ValueError(f"rubric_weights missing keys: {', '.join(missing)}")
    vals = {k: float(raw[k]) for k in keys}
    if any(v < 0 for v in vals.values()):
        raise ValueError("rubric_weights must be non-negative")
    total = sum(vals.values())
    if total <= 0:
        raise ValueError("rubric_weights must sum to a positive value")
    # If user entered percents like 30/25/20/15/10
    if total > 1.5:
        vals = {k: v / 100.0 for k, v in vals.items()}
        total = sum(vals.values())
    return {k: v / total for k, v in vals.items()}


def compute_grade(
    *,
    analysis_results: dict[str, Any],
    files: dict[str, str],
    commit_message: str | None,
    testing_score: float,
    testing_explain: str,
    evaluation: dict[str, Any] | None = None,
    weight_override: dict[str, float] | None = None,
    assignment_title: str | None = None,
) -> dict[str, Any]:
    """
    Full rubric computation.

    Returns component scores, final_score, difficulty, explanations, and blend metadata.
    """
    difficulty = estimate_difficulty(files, analysis_results)
    quality, q_ex = score_code_quality(analysis_results)
    efficiency, e_ex = score_efficiency(analysis_results, difficulty)
    documentation, d_ex = score_documentation(analysis_results, files)
    consistency, c_ex = score_consistency(analysis_results, commit_message, files)
    testing = float(testing_score)

    # Optional AI metric overrides when structured rubric present
    ai_metrics = (evaluation or {}).get("metrics") or {}
    if isinstance(ai_metrics, dict) and ai_metrics:
        if ai_metrics.get("code_quality") is not None:
            quality = 0.5 * quality + 0.5 * float(ai_metrics["code_quality"])
            q_ex += " Blended with AI quality judgment."
        if ai_metrics.get("efficiency") is not None:
            efficiency = 0.5 * efficiency + 0.5 * float(ai_metrics["efficiency"])
            e_ex += " Blended with AI efficiency judgment."
        if ai_metrics.get("documentation") is not None:
            documentation = 0.5 * documentation + 0.5 * float(ai_metrics["documentation"])
            d_ex += " Blended with AI documentation judgment."
        if ai_metrics.get("testing") is not None:
            testing = 0.5 * testing + 0.5 * float(ai_metrics["testing"])
            testing_explain += " Blended with AI testing judgment."
        if ai_metrics.get("commit_consistency") is not None:
            consistency = 0.5 * consistency + 0.5 * float(ai_metrics["commit_consistency"])
            c_ex += " Blended with AI consistency judgment."

    weights = get_weights(weight_override)
    metrics_final = (
        weights["code_quality"] * quality
        + weights["efficiency"] * efficiency
        + weights["documentation"] * documentation
        + weights["testing"] * testing
        + weights["commit_consistency"] * consistency
    )

    ai_score = evaluation.get("score") if evaluation else None
    blend = float(settings.GRADE_AI_BLEND or 0.0)
    blend = max(0.0, min(1.0, blend))
    if ai_score is not None and blend > 0:
        final = (1.0 - blend) * metrics_final + blend * float(ai_score)
        blend_note = f"Final blends metrics ({100*(1-blend):.0f}%) with AI ({100*blend:.0f}%)."
    else:
        final = metrics_final
        blend_note = "Final score from static rubric only (no AI blend)."

    final = round(min(100.0, max(0.0, final)), 2)

    explanations = {
        "code_quality": q_ex,
        "efficiency": e_ex,
        "documentation": d_ex,
        "testing": testing_explain,
        "commit_consistency": c_ex,
        "final": blend_note,
        "difficulty": (
            f"Detected {difficulty['level']} difficulty "
            f"(LOC={difficulty['signals']['loc']}, "
            f"algo signals={difficulty['signals']['algo_keyword_hits']})."
        ),
    }
    if assignment_title:
        explanations["assignment"] = f"Graded against assignment: {assignment_title}"

    return {
        "code_quality": round(quality, 2),
        "efficiency": round(efficiency, 2),
        "documentation": round(documentation, 2),
        "testing": round(testing, 2),
        "commit_consistency": round(consistency, 2),
        "final_score": final,
        "weights": {k: round(v, 4) for k, v in weights.items()},
        "difficulty": difficulty,
        "explanations": explanations,
        "metrics_final": round(metrics_final, 2),
        "ai_score": float(ai_score) if ai_score is not None else None,
        "ai_blend": blend if ai_score is not None else 0.0,
        "assignment_title": assignment_title,
    }
