"""Utility functions for job processing."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


def deduplicate_jobs(jobs: list[dict], output_dir: Path | None = None) -> list[dict]:
    """Deduplicate jobs by title + company + location fingerprint."""
    seen = set()

    if output_dir and output_dir.exists():
        import csv

        for csv_file in output_dir.glob("shortlist_*.csv"):
            try:
                with open(csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        fp = hashlib.md5(
                            f"{row.get('job_title', '')}|{row.get('company', '')}|{row.get('location', '')}".lower().encode()
                        ).hexdigest()
                        seen.add(fp)
            except Exception:
                pass

    unique_jobs = []
    for job in jobs:
        fp = hashlib.md5(
            f"{job.get('title', '')}|{job.get('company', '')}|{job.get('location', '')}".lower().encode()
        ).hexdigest()
        if fp not in seen:
            seen.add(fp)
            unique_jobs.append(job)

    return unique_jobs


def apply_exclusion_filters(
    jobs: list[dict],
    excluded_companies: list[str],
    excluded_keywords: list[str],
) -> list[dict]:
    """Apply exclusion filters for companies and keywords."""
    if not excluded_companies and not excluded_keywords:
        return jobs

    excluded_companies_lower = [c.lower() for c in excluded_companies]
    excluded_keywords_lower = [k.lower() for k in excluded_keywords]

    filtered = []
    for job in jobs:
        company = job.get("company", "").lower()
        title = job.get("title", "").lower()
        description = job.get("description", "").lower()
        text = f"{title} {description}"

        if excluded_companies_lower and company in excluded_companies_lower:
            continue
        if excluded_keywords_lower and any(
            kw in text for kw in excluded_keywords_lower
        ):
            continue
        filtered.append(job)

    return filtered


def apply_title_keyword_filter(
    jobs: list[dict], title_exclude_keywords: list[str]
) -> list[dict]:
    """Drop jobs whose title contains any word from title_exclude_keywords.

    Uses word-boundary matching so "Java" won't block "JavaScript".
    """
    if not title_exclude_keywords:
        return jobs

    title_exclude_lower = [w.lower() for w in title_exclude_keywords]

    filtered = []
    for job in jobs:
        title = job.get("title", "").lower()
        excluded = any(
            re.search(r"\b" + re.escape(w) + r"\b", title) for w in title_exclude_lower
        )
        if not excluded:
            filtered.append(job)

    return filtered
