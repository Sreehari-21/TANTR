"""
SYRA Commit Analysis Pipeline.

Connects: Git retrieval → Static analysis → AI evaluation → DB storage.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from models import Commit, Repository, CommitAnalysis, Grade
from git_service import get_commit_diff, get_commit_files, GitServiceError
from analyzer.analysis import run_analysis
from ai_engine.evaluate import evaluate_commit
from services.testing_heuristic import score_testing_from_files


class CommitAnalysisError(Exception):
    """Raised when commit analysis fails."""
    pass


def analyze_commit(commit_id: int, db: Session) -> dict:
    """
    Run the full commit analysis pipeline and save results.

    1. Retrieve commit diff and changed files via Git service
    2. Run static analysis on the files
    3. Call evaluate_commit (AI Professor Engine)
    4. Store results in CommitAnalysis and Grade tables

    Returns:
        {
            "commit_id": int,
            "status": "completed" | "failed",
            "commit_analysis_id": int | None,
            "grade_id": int | None,
        }
    """
    commit = db.query(Commit).filter(Commit.id == commit_id).first()
    if not commit:
        raise CommitAnalysisError(f"Commit {commit_id} not found")

    repo = db.query(Repository).filter(Repository.id == commit.repository_id).first()
    if not repo:
        raise CommitAnalysisError(f"Repository for commit {commit_id} not found")

    user_id = repo.owner_id
    repo_name = repo.name
    sha = commit.sha

    # 1. Get diff and files from Git
    try:
        diff = get_commit_diff(user_id, repo_name, sha)
        files = get_commit_files(user_id, repo_name, sha)
    except GitServiceError as e:
        return _fail_analysis(db, commit_id, str(e))

    # Ensure we have Python files to analyze; use repo path if empty
    if not files:
        from git_service.repo_path import get_repo_path
        repo_path = get_repo_path(user_id, repo_name)
        if repo_path.exists():
            analysis_results = run_analysis(source_path=repo_path)
        else:
            analysis_results = _empty_analysis()
    else:
        # 2. Run static analysis on changed files
        analysis_results = run_analysis(files=files)

    # 3. AI evaluation
    try:
        evaluation = evaluate_commit(diff=diff, files=files, analysis_results=analysis_results)
    except Exception as e:
        return _fail_analysis(db, commit_id, str(e))

    # 4. Store CommitAnalysis and Grade
    return _save_results(db, commit_id, analysis_results, evaluation, files)


def _empty_analysis() -> dict:
    return {
        "complexity_score": None,
        "style_score": None,
        "documentation_score": None,
        "warnings": [],
        "static_analysis_raw": {},
    }


def _fail_analysis(db: Session, commit_id: int, error: str) -> dict:
    """Create failed CommitAnalysis record and return status."""
    existing = db.query(CommitAnalysis).filter(CommitAnalysis.commit_id == commit_id).first()
    if existing:
        existing.status = "failed"
        existing.ai_feedback = error
        db.commit()
        analysis_id = existing.id
    else:
        analysis = CommitAnalysis(
            commit_id=commit_id,
            status="failed",
            ai_feedback=f"Analysis failed: {error}",
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        analysis_id = analysis.id
    return {
        "commit_id": commit_id,
        "status": "failed",
        "commit_analysis_id": analysis_id,
        "grade_id": None,
    }


def _save_results(
    db: Session,
    commit_id: int,
    analysis_results: dict,
    evaluation: dict,
    files: dict[str, str],
) -> dict:
    """Persist CommitAnalysis and Grade; return status."""
    # Upsert CommitAnalysis
    analysis = db.query(CommitAnalysis).filter(CommitAnalysis.commit_id == commit_id).first()
    if not analysis:
        analysis = CommitAnalysis(commit_id=commit_id)
        db.add(analysis)

    analysis.static_analysis_raw = analysis_results.get("static_analysis_raw")
    analysis.complexity_score = analysis_results.get("complexity_score")
    analysis.style_score = analysis_results.get("style_score")
    analysis.documentation_score = analysis_results.get("documentation_score")
    analysis.warnings = analysis_results.get("warnings")
    analysis.ai_feedback = evaluation.get("feedback")
    analysis.ai_suggestions = evaluation.get("suggestions")
    analysis.status = "completed"
    db.flush()

    # Compute Grade using the grading formula
    # final = 0.30*quality + 0.25*efficiency + 0.20*doc + 0.15*testing + 0.10*consistency
    code_quality = _to_100(analysis_results.get("style_score"), analysis_results.get("complexity_score"))
    efficiency = _to_100(analysis_results.get("complexity_score"))  # lower complexity = better efficiency
    documentation = _to_100(analysis_results.get("documentation_score"))
    testing = score_testing_from_files(files)
    commit_consistency = min(100.0, 100.0 - len(analysis_results.get("warnings") or []) * 5)

    final_score = (
        0.30 * code_quality
        + 0.25 * efficiency
        + 0.20 * documentation
        + 0.15 * testing
        + 0.10 * commit_consistency
    )
    final_score = round(min(100.0, max(0.0, final_score)), 2)

    # Upsert Grade
    grade = db.query(Grade).filter(Grade.commit_id == commit_id).first()
    if not grade:
        grade = Grade(commit_id=commit_id)
        db.add(grade)

    grade.code_quality = code_quality
    grade.efficiency = efficiency
    grade.documentation = documentation
    grade.testing = testing
    grade.commit_consistency = commit_consistency
    grade.final_score = final_score
    db.flush()

    db.commit()
    db.refresh(analysis)
    db.refresh(grade)

    return {
        "commit_id": commit_id,
        "status": "completed",
        "commit_analysis_id": analysis.id,
        "grade_id": grade.id,
    }


def _to_100(*vals) -> float:
    """Normalize score(s) to 0-100. If multiple, average them."""
    result = []
    for v in vals:
        if v is None:
            result.append(70.0)
        else:
            x = float(v)
            result.append(x * 10.0 if x <= 10 else min(100.0, x))
    return sum(result) / len(result) if result else 70.0
