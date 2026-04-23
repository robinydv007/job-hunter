"""LangGraph state definition for the job hunter pipeline."""

from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict

from job_hunter.config import AppConfig, UserConfig, PlatformConfig
from job_hunter.resume.schema import ResumeProfile


class JobListing(TypedDict, total=False):
    title: str
    company: str
    location: str
    work_mode: str
    experience_required: str
    salary_lpa: str
    job_url: str
    job_id: str
    description: str
    posted_date: str
    job_board: str
    search_keyword: str  # keyword used to find this job (for title-remainder scoring)


class ScoredJob(TypedDict, total=False):
    job: JobListing
    match_score: int
    matched_skills: list[str]
    why_selected: str
    apply_status: str
    apply_timestamp: str
    apply_error: str
    questionnaire: str
    questionnaire_timestamp: str


class JobHunterState(TypedDict, total=False):
    config: AppConfig
    user_config: UserConfig | None
    platform_config: PlatformConfig | None
    resume_path: str
    force_parse: bool  # Force re-parse resume even if cache exists
    profile: ResumeProfile | None
    detailed_profile: (
        dict | None
    )  # Extended profile with tech_experience, achievements, etc.
    raw_jobs: list[JobListing]
    scored_jobs: list[ScoredJob]
    shortlisted_jobs: list[ScoredJob]
    csv_path: str
    browser_page: Any  # Playwright Page object
    threshold_used: int  # Shortlist threshold resolved at score time
    # Apply outcome counters — populated by apply_jobs_node, consumed by update_history_node
    apply_applied_count: int
    apply_skipped_count: int
    apply_failed_count: int
