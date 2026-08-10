"""
SYRA AI Professor Engine - commit evaluation.

Usage:
  from ai_engine import evaluate_commit
  result = evaluate_commit(diff="...", files={...}, analysis_results={...})
  # result: score, feedback, suggestions
"""

from ai_engine.evaluate import evaluate_commit

__all__ = ["evaluate_commit"]
