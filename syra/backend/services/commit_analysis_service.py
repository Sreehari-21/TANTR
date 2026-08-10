"""
SYRA Commit Analysis Pipeline.

Connects: Git retrieval → Static analysis → AI evaluation → Rubric grade → DB storage.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from models import Commit, Repository, CommitAnalysis, Grade
from vcs import get_commit_diff, get_commit_files, VcsError
from analyzer.analysis import run_analysis
from ai_engine.evaluate import evaluate_commit
from services.testing_heuristic import score_testing_from_files
from services.rubric import compute_grade, estimate_difficulty


class CommitAnalysisError(Exception):
    """Raised when commit analysis fails."""

    pass


def analyze_commit(commit_id: int, db: Session) -> dict:
    """
    Run the full commit analysis pipeline and save results.

    1. Retrieve commit diff and files via custom VCS
    2. Run static analysis on the files
    3. Score testing (heuristics + optional pytest)
    4. Call evaluate_commit (AI Professor Engine)
    5. Compute rubric grade (difficulty-aware + AI blend)
    6. Store results in CommitAnalysis and Grade tables
    """
    commit = db.query(Commit).filter(Commit.id == commit_id).first()
    if not commit:
        raise CommitAnalysisError(f"Commit {commit_id} not found")

    repo = db.query(Repository).filter(Repository.id == commit.repository_id).first()
    if not repo:
        raise CommitAnalysisError(f"Repository for commit {commit_id} not found")

    try:
        diff = get_commit_diff(db, commit.sha)
        files = get_commit_files(db, commit.sha)
    except VcsError as e:
        return _fail_analysis(db, commit_id, str(e))

    if files:
        analysis_results = run_analysis(files=files)
    else:
        analysis_results = _empty_analysis()

    testing_score, testing_explain, testing_raw = score_testing_from_files(files)
    difficulty = estimate_difficulty(files, analysis_results)

    try:
        evaluation = evaluate_commit(
            diff=diff,
            files=files,
            analysis_results=analysis_results,
            commit_message=commit.message,
            difficulty=difficulty,
        )
    except Exception as e:
        return _fail_analysis(db, commit_id, str(e))

    return _save_results(
        db,
        commit_id,
        analysis_results,
        evaluation,
        files,
        commit_message=commit.message,
        testing_score=testing_score,
        testing_explain=testing_explain,
        testing_raw=testing_raw,
    )


def _empty_analysis() -> dict:
    return {
        "complexity_score": None,
        "style_score": None,
        "documentation_score": None,
        "warnings": [],
        "static_analysis_raw": {},
    }


def _fail_analysis(db: Session, commit_id: int, error: str) -> dict:
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
    *,
    commit_message: str | None,
    testing_score: float,
    testing_explain: str,
    testing_raw: dict,
) -> dict:
    rubric = compute_grade(
        analysis_results=analysis_results,
        files=files,
        commit_message=commit_message,
        testing_score=testing_score,
        testing_explain=testing_explain,
        evaluation=evaluation,
    )

    analysis = db.query(CommitAnalysis).filter(CommitAnalysis.commit_id == commit_id).first()
    if not analysis:
        analysis = CommitAnalysis(commit_id=commit_id)
        db.add(analysis)

    raw = dict(analysis_results.get("static_analysis_raw") or {})
    raw["rubric"] = {
        "weights": rubric["weights"],
        "difficulty": rubric["difficulty"],
        "explanations": rubric["explanations"],
        "metrics_final": rubric["metrics_final"],
        "ai_score": rubric["ai_score"],
        "ai_blend": rubric["ai_blend"],
        "ai_source": evaluation.get("source"),
        "testing": testing_raw,
    }
    analysis.static_analysis_raw = raw
    analysis.complexity_score = analysis_results.get("complexity_score")
    analysis.style_score = analysis_results.get("style_score")
    analysis.documentation_score = analysis_results.get("documentation_score")
    analysis.warnings = analysis_results.get("warnings")
    analysis.ai_feedback = evaluation.get("feedback")
    analysis.ai_suggestions = evaluation.get("suggestions")
    analysis.status = "completed"
    db.flush()

    grade = db.query(Grade).filter(Grade.commit_id == commit_id).first()
    if not grade:
        grade = Grade(commit_id=commit_id)
        db.add(grade)

    grade.code_quality = rubric["code_quality"]
    grade.efficiency = rubric["efficiency"]
    grade.documentation = rubric["documentation"]
    grade.testing = rubric["testing"]
    grade.commit_consistency = rubric["commit_consistency"]
    grade.final_score = rubric["final_score"]
    db.flush()

    db.commit()
    db.refresh(analysis)
    db.refresh(grade)

    return {
        "commit_id": commit_id,
        "status": "completed",
        "commit_analysis_id": analysis.id,
        "grade_id": grade.id,
        "final_score": rubric["final_score"],
        "difficulty": rubric["difficulty"].get("level"),
    }
