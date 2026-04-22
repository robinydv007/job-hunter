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
    "Job Title": lambda sj: _get_nested(sj.get("job", {}), "title"),
    "Company": lambda sj: _get_nested(sj.get("job", {}), "company"),
    "Location": lambda sj: _get_nested(sj.get("job", {}), "location"),
    "Experience Required": lambda sj: _get_nested(
        sj.get("job", {}), "experience_required"
    ),
    "Match Score": lambda sj: sj.get("match_score", 0),
    "Job Description": lambda sj: _truncate(
        _get_nested(sj.get("job", {}), "description")
    ),
    "Why Selected": lambda sj: sj.get("why_selected", "").replace("\n", " | "),
    "Matched Skills": lambda sj: "; ".join(sj.get("matched_skills", [])),
    "Questionnaire": lambda sj: sj.get("questionnaire", "[]"),
    "Job Board": lambda sj: _get_nested(sj.get("job", {}), "job_board"),
    "Job URL": lambda sj: _get_nested(sj.get("job", {}), "job_url"),
    "Work Mode": lambda sj: _get_nested(sj.get("job", {}), "work_mode"),
    "Salary LPA": lambda sj: _get_nested(sj.get("job", {}), "salary_lpa"),
    "Posted Date": lambda sj: _get_nested(sj.get("job", {}), "posted_date"),
    "Data Source": lambda sj: _get_nested(sj.get("job", {}), "data_source", "mock"),
    "Apply Status": lambda sj: sj.get("apply_status", "Pending"),
    "Apply Timestamp": lambda sj: sj.get("apply_timestamp", ""),
    "Questionnaire Timestamp": lambda sj: sj.get("questionnaire_timestamp", ""),
    "Apply Error": lambda sj: sj.get("apply_error", ""),
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
