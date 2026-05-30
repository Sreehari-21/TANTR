"""
SYRA static code analysis (pylint, flake8, radon).

Usage:
  from analyzer import run_analysis, analyze
  result = run_analysis(source_path=Path("/repos/1/my-repo"))
  result = analyze(file_path="main.py")  # or source_code="def foo(): pass"
  # result: complexity_score, style_score, documentation_score, warnings (0-10 scale)
"""

from analyzer.analysis import run_analysis
from analyzer.static_analyzer import analyze
from analyzer.metrics import analysis_result, to_commit_analysis_format

__all__ = ["run_analysis", "analyze", "analysis_result", "to_commit_analysis_format"]
