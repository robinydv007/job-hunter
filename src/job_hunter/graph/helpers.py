"""Helper functions for run history management."""

from __future__ import annotations

import json
from pathlib import Path


def _get_run_history_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "run_history.json"


def _load_run_history() -> list[dict]:
    path = _get_run_history_path()
    if not path.exists():
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_run_history(history: list[dict]) -> None:
    path = _get_run_history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(history, f, indent=2)


def record_run(platform: str, freshness_used: int, jobs_found: int) -> None:
    """Append a run record to data/run_history.json."""
    history = _load_run_history()
    history.append(
        {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "freshness_used": freshness_used,
            "jobs_found": jobs_found,
            "platform": platform,
        }
    )
    _save_run_history(history)


def update_run_stats(jobs_shortlisted: int, jobs_applied: int) -> None:
    """Update the last run record with final stats after pipeline completes."""
    history = _load_run_history()
    if not history:
        return
    history[-1]["jobs_shortlisted"] = jobs_shortlisted
    history[-1]["jobs_applied"] = jobs_applied
    _save_run_history(history)
