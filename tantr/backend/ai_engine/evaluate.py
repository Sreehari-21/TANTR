"""
TANTR AI Professor Engine - commit evaluation.

Uses OpenAI when OPENAI_API_KEY is set; otherwise a structured placeholder rubric.
Returns overall score, feedback, suggestions, and optional per-metric scores.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from config import settings

logger = logging.getLogger(__name__)

_MAX_DIFF = 12_000
_MAX_FILE_SNIPPET = 2_000


def evaluate_commit(
    diff: str,
    files: dict[str, str],
    analysis_results: dict[str, Any],
    *,
    commit_message: str | None = None,
    difficulty: dict[str, Any] | None = None,
    assignment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Evaluate a commit as a computer science professor would.

    Returns:
        {
            "score": float,              # 0-100 overall
            "feedback": str,
            "suggestions": list[str],
            "metrics": {                 # optional per-metric 0-100
                "code_quality": float,
                "efficiency": float,
                "documentation": float,
                "testing": float,
                "commit_consistency": float,
            },
            "source": "openai" | "placeholder",
        }
    """
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
        try:
            result = _openai_evaluate(
                diff, files, analysis_results,
                commit_message=commit_message,
                difficulty=difficulty,
                assignment=assignment,
            )
            result["source"] = "openai"
            return result
        except Exception as e:
            logger.warning("OpenAI evaluation failed, using placeholder: %s", e)
    result = _placeholder_evaluate(
        diff, files, analysis_results,
        commit_message=commit_message,
        difficulty=difficulty,
        assignment=assignment,
    )
    result["source"] = "placeholder"
    return result


def _clamp(val: Any, default: float = 70.0) -> float:
    try:
        v = float(val)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(100.0, v))


def _openai_evaluate(
    diff: str,
    files: dict[str, str],
    analysis_results: dict[str, Any],
    *,
    commit_message: str | None = None,
    difficulty: dict[str, Any] | None = None,
    assignment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    model = settings.OPENAI_MODEL or "gpt-4o-mini"

    diff_trunc = (diff or "")[:_MAX_DIFF]
    file_summaries = []
    for path, content in list(files.items())[:12]:
        snippet = (content or "")[:_MAX_FILE_SNIPPET]
        file_summaries.append(f"--- {path} ---\n{snippet}")

    analysis_json = json.dumps(
        {
            "complexity_score": analysis_results.get("complexity_score"),
            "style_score": analysis_results.get("style_score"),
            "documentation_score": analysis_results.get("documentation_score"),
            "warnings_count": len(analysis_results.get("warnings") or []),
            "warnings_sample": (analysis_results.get("warnings") or [])[:8],
            "commit_message": commit_message,
            "difficulty": (difficulty or {}).get("level"),
            "assignment_title": (assignment or {}).get("title"),
        },
        default=str,
    )

    system = (
        "You are a strict but fair computer science professor grading a student Git commit. "
        "Respond with a single JSON object only (no markdown) with keys:\n"
        "- score (number 0-100 overall)\n"
        "- metrics (object with code_quality, efficiency, documentation, testing, "
        "commit_consistency — each number 0-100)\n"
        "- feedback (string, 2-4 sentences, professor tone)\n"
        "- suggestions (array of 3-6 short actionable strings)\n"
        "Consider correctness, algorithm efficiency for the problem difficulty, "
        "readability, documentation, tests, and commit message quality. "
        "If an assignment brief is provided, grade how well the commit addresses it. "
        "Do not inflate scores; reserve 90+ for excellent work."
    )
    assignment_block = ""
    if assignment and (assignment.get("title") or assignment.get("brief")):
        assignment_block = (
            f"Assignment title: {assignment.get('title') or '(untitled)'}\n"
            f"Assignment brief:\n{(assignment.get('brief') or '')[:2000]}\n\n"
        )
    user = (
        f"{assignment_block}"
        f"Static analysis summary:\n{analysis_json}\n\n"
        f"Git diff:\n{diff_trunc}\n\n"
        f"File snippets:\n{chr(10).join(file_summaries) or '(no files)'}"
    )

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    try:
        kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kwargs)
    except Exception:
        kwargs.pop("response_format", None)
        resp = client.chat.completions.create(**kwargs)
    raw = (resp.choices[0].message.content or "").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(raw[start:end])
        else:
            raise ValueError("OpenAI response was not valid JSON") from None

    score = _clamp(parsed.get("score", 70))
    feedback = str(parsed.get("feedback", "")).strip() or "No feedback returned."
    suggestions = parsed.get("suggestions")
    if not isinstance(suggestions, list):
        suggestions = []
    suggestions = [str(s).strip() for s in suggestions if str(s).strip()][:8]

    metrics_in = parsed.get("metrics") if isinstance(parsed.get("metrics"), dict) else {}
    metrics = {
        "code_quality": _clamp(metrics_in.get("code_quality", score)),
        "efficiency": _clamp(metrics_in.get("efficiency", score)),
        "documentation": _clamp(metrics_in.get("documentation", score)),
        "testing": _clamp(metrics_in.get("testing", score)),
        "commit_consistency": _clamp(metrics_in.get("commit_consistency", score)),
    }

    return {
        "score": round(score, 1),
        "feedback": feedback,
        "suggestions": suggestions,
        "metrics": metrics,
    }


def _placeholder_evaluate(
    diff: str,
    files: dict[str, str],
    analysis_results: dict[str, Any],
    *,
    commit_message: str | None = None,
    difficulty: dict[str, Any] | None = None,
    assignment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    def _to_100(val: Any, default: float = 55.0) -> float:
        if val is None:
            return default
        v = float(val)
        if v <= 10:
            return v * 10.0
        return min(100.0, v)

    complexity = _to_100(analysis_results.get("complexity_score"), 55.0)
    style = _to_100(analysis_results.get("style_score"), 55.0)
    documentation = _to_100(analysis_results.get("documentation_score"), 45.0)
    warnings = analysis_results.get("warnings") or []

    code_quality = 0.55 * style + 0.45 * complexity
    code_quality = max(0.0, code_quality - min(18.0, len(warnings) * 1.5))

    efficiency = complexity
    if difficulty and difficulty.get("multiplier"):
        efficiency = min(100.0, efficiency * float(difficulty["multiplier"]))

    testing = 42.0
    for path in files:
        if "test" in path.lower():
            testing = 70.0
            break

    msg = (commit_message or "").strip()
    consistency = 80.0
    if not msg or len(msg) < 8:
        consistency = 45.0
    consistency = max(0.0, consistency - min(25.0, len(warnings) * 3.0))

    metrics = {
        "code_quality": round(code_quality, 1),
        "efficiency": round(efficiency, 1),
        "documentation": round(documentation, 1),
        "testing": round(testing, 1),
        "commit_consistency": round(consistency, 1),
    }
    score = (
        0.30 * metrics["code_quality"]
        + 0.25 * metrics["efficiency"]
        + 0.20 * metrics["documentation"]
        + 0.15 * metrics["testing"]
        + 0.10 * metrics["commit_consistency"]
    )
    score = round(min(100.0, max(0.0, score)), 1)

    feedback_parts = []
    if assignment and assignment.get("title"):
        feedback_parts.append(f"Reviewed against assignment “{assignment['title']}”.")
    level = (difficulty or {}).get("level") or "unknown"
    if score >= 85:
        feedback_parts.append(
            f"Excellent commit for {level} work — structure and clarity stand out."
        )
    elif score >= 70:
        feedback_parts.append(
            f"Solid {level} commit. Strengthen weaker rubric areas to push into the A range."
        )
    elif score >= 55:
        feedback_parts.append(
            "Acceptable baseline, but several professor rubric criteria need attention."
        )
    else:
        feedback_parts.append(
            "This submission falls short of course standards — prioritize fixes below."
        )

    if style < 70:
        feedback_parts.append("Style/lint issues are holding quality back (PEP 8 / flake8).")
    if complexity < 65:
        feedback_parts.append("Complexity is high; extract helpers and reduce branching.")
    if documentation < 55:
        feedback_parts.append("Documentation is thin — add module and function docstrings.")
    if testing < 60:
        feedback_parts.append("Add or expand automated tests (pytest) for core behavior.")
    if warnings:
        feedback_parts.append(f"Resolve the {len(warnings)} static-analysis finding(s).")

    suggestions = [f"Fix: {w}" for w in warnings[:5]]
    if style < 70:
        suggestions.append("Run flake8/pylint and clear remaining style violations.")
    if complexity < 65:
        suggestions.append("Reduce cyclomatic complexity by extracting helper functions.")
    if documentation < 55:
        suggestions.append("Add Google-style docstrings for public functions and classes.")
    if testing < 60:
        suggestions.append("Add tests/ with pytest functions named test_*.")
    if not msg or len(msg) < 10:
        suggestions.append("Use a descriptive commit message (what changed and why).")
    if not suggestions:
        suggestions.append("Keep iterating — add edge-case tests and tighten naming.")

    return {
        "score": score,
        "feedback": " ".join(feedback_parts),
        "suggestions": suggestions[:8],
        "metrics": metrics,
    }
