"""CSV export system for shortlisted jobs."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def _truncate(text: str, max_len: int = 500) -> str:
    return text[:max_len] + "..." if len(text) > max_len else text


def _get_nested(job: dict, key: str, default: Any = "") -> Any:
    return job.get(key, default)


ROW_MAPPING: dict[str, callable[[Any], Any]] = {
    "job_title": lambda sj: _get_nested(sj.get("job", {}), "title"),
    "company": lambda sj: _get_nested(sj.get("job", {}), "company"),
    "job_board": lambda sj: _get_nested(sj.get("job", {}), "job_board"),
    "location": lambda sj: _get_nested(sj.get("job", {}), "location"),
    "work_mode": lambda sj: _get_nested(sj.get("job", {}), "work_mode"),
    "experience_required": lambda sj: _get_nested(
        sj.get("job", {}), "experience_required"
    ),
    "salary_lpa": lambda sj: _get_nested(sj.get("job", {}), "salary_lpa"),
    "match_score": lambda sj: sj.get("match_score", 0),
    "matched_skills": lambda sj: "; ".join(sj.get("matched_skills", [])),
    "why_selected": lambda sj: sj.get("why_selected", "").replace("\n", " | "),
    "job_url": lambda sj: _get_nested(sj.get("job", {}), "job_url"),
    "posted_date": lambda sj: _get_nested(sj.get("job", {}), "posted_date"),
    "job_description": lambda sj: _truncate(
        _get_nested(sj.get("job", {}), "description")
    ),
    "apply_status": lambda sj: sj.get("apply_status", "Pending"),
    "apply_timestamp": lambda sj: sj.get("apply_timestamp", ""),
    "apply_error": lambda sj: sj.get("apply_error", ""),
    "data_source": lambda sj: _get_nested(sj.get("job", {}), "data_source", "mock"),
}


def export_to_csv(scored_jobs: list[Any], csv_path: str | Path) -> None:
    """Export shortlisted jobs to a CSV file."""
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ROW_MAPPING.keys())
        writer.writeheader()

        for sj in scored_jobs:
            row = {col: fn(sj) for col, fn in ROW_MAPPING.items()}
            writer.writerow(row)
