"""LangGraph state definition for the job hunter pipeline."""

from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict

from job_hunter.config import AppConfig
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


class ScoredJob(TypedDict, total=False):
    job: JobListing
    match_score: int
    matched_skills: list[str]
    why_selected: str
    apply_status: str


class JobHunterState(TypedDict):
    config: AppConfig
    resume_path: str
    profile: ResumeProfile | None
    raw_jobs: list[JobListing]
    scored_jobs: list[ScoredJob]
    shortlisted_jobs: list[ScoredJob]
    csv_path: str
    browser_page: Any  # Playwright Page object
