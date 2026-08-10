"""
SYRA AI Professor Engine - commit evaluation.

Uses OpenAI when OPENAI_API_KEY is set; otherwise placeholder scoring.
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
) -> dict[str, Any]:
    """
    Evaluate a commit as a computer science professor would.

    Args:
        diff: Git diff string for the commit
        files: Dict of file path -> content (changed/new files)
        analysis_results: Output from static analyzer (complexity_score, style_score,
                          documentation_score, warnings, optionally static_analysis_raw)

    Returns:
        {
            "score": float,       # 0-100 overall
            "feedback": str,     # Professor-style feedback
            "suggestions": list[str]  # Improvement suggestions
        }
    """
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
        try:
            return _openai_evaluate(diff, files, analysis_results)
        except Exception as e:
            logger.warning("OpenAI evaluation failed, using placeholder: %s", e)
    return _placeholder_evaluate(diff, files, analysis_results)


def _openai_evaluate(
    diff: str,
    files: dict[str, str],
    analysis_results: dict[str, Any],
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
        },
        default=str,
    )

    system = (
        "You are a computer science professor grading a student commit. "
        "Respond with a single JSON object only, no markdown, with keys: "
        "score (number 0-100), feedback (string, 2-4 sentences), "
        "suggestions (array of 3-6 short actionable strings). "
        "Consider: correctness, algorithm efficiency, readability, documentation, best practices."
    )
    user = (
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
    score = float(parsed.get("score", 70))
    score = max(0.0, min(100.0, score))
    feedback = str(parsed.get("feedback", "")).strip() or "No feedback returned."
    suggestions = parsed.get("suggestions")
    if not isinstance(suggestions, list):
        suggestions = []
    suggestions = [str(s).strip() for s in suggestions if str(s).strip()]

    return {
        "score": round(score, 1),
        "feedback": feedback,
        "suggestions": suggestions,
    }


def _placeholder_evaluate(
    diff: str,
    files: dict[str, str],
    analysis_results: dict[str, Any],
) -> dict[str, Any]:
    """
    Placeholder implementation using analysis_results.
    Replace this with OpenAI API call when ready.
    """
    # Normalize scores to 0-100 (analyzer may return 0-10 or 0-100)
    def _to_100(val: Any) -> float:
        if val is None:
            return 70.0  # default when missing
        v = float(val)
        if v <= 10:
            return v * 10.0
        return min(100.0, v)

    complexity = _to_100(analysis_results.get("complexity_score"))
    style = _to_100(analysis_results.get("style_score"))
    documentation = _to_100(analysis_results.get("documentation_score"))
    warnings = analysis_results.get("warnings") or []

    # Weighted score: code quality components
    score = (
        0.40 * style
        + 0.35 * complexity
        + 0.25 * documentation
    )

    # Penalty for warnings (each warning reduces score slightly)
    penalty = min(15.0, len(warnings) * 2.0)
    score = max(0.0, score - penalty)
    score = round(min(100.0, score), 1)

    # Build feedback
    feedback_parts = []
    if score >= 80:
        feedback_parts.append("Solid work! Your code demonstrates good structure and readability.")
    elif score >= 60:
        feedback_parts.append("Good effort. There is room for improvement in code quality and style.")
    else:
        feedback_parts.append("This commit needs more attention to code quality and best practices.")

    if style < 70:
        feedback_parts.append("Style could be improved—consider following PEP 8 and reducing lint issues.")
    if complexity < 70:
        feedback_parts.append("Some functions may be too complex; consider breaking them down.")
    if documentation < 50:
        feedback_parts.append("Documentation is sparse; add docstrings for modules and key functions.")
    if warnings:
        feedback_parts.append(f"Address the {len(warnings)} issue(s) reported by the static analyzer.")

    feedback = " ".join(feedback_parts)

    # Build suggestions from warnings and low scores
    suggestions = []
    for w in warnings[:5]:  # top 5 warnings
        suggestions.append(f"Fix: {w}")
    if style < 70 and "style" not in str(suggestions).lower():
        suggestions.append("Run flake8 and pylint to identify style issues.")
    if complexity < 70 and "complexity" not in str(suggestions).lower():
        suggestions.append("Reduce cyclomatic complexity by extracting helper functions.")
    if documentation < 50:
        suggestions.append("Add module and function docstrings following Google or NumPy style.")
    if not diff.strip() and files:
        suggestions.append("Ensure meaningful commit messages describe your changes.")

    return {
        "score": score,
        "feedback": feedback,
        "suggestions": suggestions,
    }
