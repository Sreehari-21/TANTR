"""
Heuristic testing score (0–100) from repo file paths and contents.
"""

import re
from typing import Any


_TEST_PATH = re.compile(
    r"(^|/)(tests?/|test_[^/]+\.py|[^/]+_test\.py$)",
    re.IGNORECASE,
)


def score_testing_from_files(files: dict[str, str]) -> float:
    """
    Infer testing discipline from filenames and typical test patterns.
    No execution—static signals only.
    """
    if not files:
        return 55.0

    test_paths = [p for p in files if _TEST_PATH.search(p.replace("\\", "/"))]
    if not test_paths:
        return 55.0

    score = 72.0
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
    score += min(23.0, hits * 5.0)
    return round(min(100.0, score), 1)
