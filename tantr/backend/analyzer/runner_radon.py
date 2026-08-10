"""
TANTR Analyzer - Radon runner (complexity, maintainability, raw metrics for docs).
Returns complexity score, maintainability score, and documentation hint from raw metrics.
"""

from pathlib import Path
from typing import Any


def run_radon(source_path: Path) -> dict[str, Any]:
    """
    Run radon on all Python files under source_path.
    Returns {
      "complexity_score": float 0-100 (lower complexity = higher score),
      "maintainability_score": float 0-100,
      "documentation_score": float 0-100 (from comment/docstring ratio),
      "messages": list[str],
      "raw": ...
    }.
    """
    py_files = list(source_path.rglob("*.py"))
    if not py_files:
        return {
            "complexity_score": 100.0,
            "maintainability_score": 100.0,
            "documentation_score": 100.0,
            "messages": [],
            "raw": {},
        }

    try:
        from radon.complexity import cc_visit
        from radon.metrics import mi_visit
        from radon.raw import analyze
    except ImportError:
        return {
            "complexity_score": None,
            "maintainability_score": None,
            "documentation_score": None,
            "messages": ["radon not installed"],
            "raw": None,
        }

    all_cc = []
    all_mi = []
    doc_ratios = []
    messages = []

    for path in py_files:
        try:
            code = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            messages.append(f"{path}: read error: {e}")
            continue

        # Cyclomatic complexity (Function has .complexity, Class has .real_complexity)
        try:
            blocks = cc_visit(code)
            for b in blocks:
                if hasattr(b, "real_complexity"):
                    all_cc.append(b.real_complexity)
                elif hasattr(b, "complexity"):
                    all_cc.append(b.complexity)
            if not blocks and code.strip():
                all_cc.append(1)
        except Exception as e:
            messages.append(f"{path}: complexity error: {e}")

        # Maintainability index (radon: higher is better, typically 0-100)
        try:
            mi = mi_visit(code, True)
            if mi is not None:
                all_mi.append(mi)
        except Exception:
            pass

        # Raw metrics for documentation (comments + multi-line strings / docstrings)
        try:
            raw = analyze(code)
            loc = getattr(raw, "loc", 1) or 1
            comments = getattr(raw, "comments", 0)
            multi = getattr(raw, "multi", 0)  # multi-line strings often docstrings
            doc_lines = comments + multi
            ratio = doc_lines / loc if loc else 0
            doc_ratios.append(min(1.0, ratio * 2))  # 0.5 ratio -> 1.0, scale so 25% docs -> 50 score
        except Exception:
            doc_ratios.append(0.0)

    # Complexity score: lower avg complexity = higher score. CC 1-5=A, 6-10=B, ...
    # Score = max(0, 100 - avg_cc * 8), so avg 12.5 gives 0
    complexity_score = 100.0
    if all_cc:
        avg_cc = sum(all_cc) / len(all_cc)
        complexity_score = max(0.0, min(100.0, 100.0 - avg_cc * 8.0))
        for cc in all_cc:
            if cc > 10:
                messages.append(f"High cyclomatic complexity: {cc}")

    # Maintainability: radon MI can be 0-100 or similar; normalize to 0-100
    maintainability_score = 100.0
    if all_mi:
        avg_mi = sum(all_mi) / len(all_mi)
        maintainability_score = max(0.0, min(100.0, avg_mi))

    # Documentation: average of doc ratios scaled to 0-100
    documentation_score = 100.0
    if doc_ratios:
        avg_ratio = sum(doc_ratios) / len(doc_ratios)
        documentation_score = round(avg_ratio * 100.0, 2)
        documentation_score = max(0.0, min(100.0, documentation_score))

    return {
        "complexity_score": round(complexity_score, 2),
        "maintainability_score": round(maintainability_score, 2),
        "documentation_score": documentation_score,
        "messages": messages,
        "raw": {
            "avg_complexity": sum(all_cc) / len(all_cc) if all_cc else None,
            "avg_mi": sum(all_mi) / len(all_mi) if all_mi else None,
            "file_count": len(py_files),
        },
    }
