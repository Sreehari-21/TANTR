"""
SYRA Analyzer - Pylint runner.
Returns a score (0-10 from pylint, we use 0-100) and list of messages.
"""

import io
import json
from pathlib import Path
from typing import Any


def run_pylint(source_path: Path) -> dict[str, Any]:
    """
    Run pylint on all Python files under source_path.
    Returns {"score": float 0-100, "messages": list[str], "raw": ...}.
    """
    try:
        from pylint.lint import Run as PylintRun
    except ImportError:
        return {"score": None, "messages": ["pylint not installed"], "raw": None}

    py_files = list(source_path.rglob("*.py"))
    if not py_files:
        return {"score": 100.0, "messages": [], "raw": {"note": "No Python files"}}

    paths = [str(p) for p in py_files]
    messages = []
    run = None

    # Prefer CollectingReporter; fallback to JSONReporter for message list
    try:
        from pylint.reporters import CollectingReporter
        reporter = CollectingReporter()
        run = PylintRun(paths, reporter=reporter, exit=False)
        for msg in reporter.messages:
            messages.append(f"{getattr(msg, 'path', '')}:{getattr(msg, 'line', 0)}: {getattr(msg, 'msg_id', '')} ({getattr(msg, 'symbol', '')}): {getattr(msg, 'msg', '')}")
    except (ImportError, AttributeError):
        out = io.StringIO()
        try:
            from pylint.reporters import JSONReporter
            reporter = JSONReporter(out)
            run = PylintRun(paths, reporter=reporter, exit=False)
            raw_json = out.getvalue()
            if raw_json:
                data = json.loads(raw_json)
                for item in data if isinstance(data, list) else data.get("messages", []):
                    if isinstance(item, dict):
                        messages.append(f"{item.get('path', '')}:{item.get('line', 0)}: {item.get('message-id', '')} ({item.get('symbol', '')}): {item.get('message', '')}")
        except Exception:
            pass
    if run is None:
        try:
            run = PylintRun(paths, exit=False)
        except Exception as e:
            return {"score": None, "messages": [f"pylint error: {e}"], "raw": None}

    # Pylint global note is 0-10; convert to 0-100
    score = 100.0
    try:
        note = run.linter.stats.get("global_note", 10.0)
        score = float(note) * 10.0  # 0-10 -> 0-100
        score = max(0.0, min(100.0, score))
    except Exception:
        score = max(0.0, 100.0 - len(messages) * 2.5)
        score = min(100.0, score)

    return {
        "score": round(score, 2),
        "messages": messages,
        "raw": {"message_count": len(messages)},
    }
