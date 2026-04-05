"""CSV export system for shortlisted jobs."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

MVP_COLUMNS = [
    "job_title",
    "company",
    "job_board",
    "location",
    "work_mode",
    "experience_required",
    "salary_lpa",
    "match_score",
    "matched_skills",
    "why_selected",
    "job_url",
    "posted_date",
    "job_description",
    "apply_status",
    "data_source",
]


def export_to_csv(scored_jobs: list[Any], csv_path: str | Path) -> None:
    """Export shortlisted jobs to a CSV file."""
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MVP_COLUMNS, extrasaction="ignore")
        writer.writeheader()

        for sj in scored_jobs:
            job = sj.get("job", {})
            desc = job.get("description", "")
            data_source = job.get("data_source", "mock")
            row = {
                "job_title": job.get("title", ""),
                "company": job.get("company", ""),
                "job_board": job.get("job_board", ""),
                "location": job.get("location", ""),
                "work_mode": job.get("work_mode", ""),
                "experience_required": job.get("experience_required", ""),
                "salary_lpa": job.get("salary_lpa", ""),
                "match_score": sj.get("match_score", 0),
                "matched_skills": "; ".join(sj.get("matched_skills", [])),
                "why_selected": sj.get("why_selected", "").replace("\n", " | "),
                "job_url": job.get("job_url", ""),
                "posted_date": job.get("posted_date", ""),
                "job_description": (desc[:500] + "...") if len(desc) > 500 else desc,
                "apply_status": sj.get("apply_status", "Pending"),
                "data_source": data_source,
            }
            writer.writerow(row)
