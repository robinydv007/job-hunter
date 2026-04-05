"""Configuration loading, validation, and interactive prompting."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class Profile(BaseModel):
    name: str = ""
    total_experience: int = 0
    preferred_roles: list[str] = Field(default_factory=list)
    expected_salary_lpa: float = 0
    notice_period: str = ""
    preferred_locations: list[str] = Field(default_factory=list)
    remote_preference: str = "hybrid"
    company_size_preference: list[str] = Field(default_factory=list)
    industry_preference: list[str] = Field(default_factory=list)


class SearchConfig(BaseModel):
    platforms: list[str] = Field(default_factory=lambda: ["naukri"])
    salary_min_lpa: float = 0
    salary_max_lpa: float = 0
    experience_years: int = 0
    max_jobs: int = 50
    freshness: int = 0  # 0=auto, 1/3/7/15/30=days
    max_roles: int = 5
    max_locations: int = 3
    work_mode_filter: list[str] = Field(default_factory=list)
    job_types: list[str] = Field(default_factory=list)
    excluded_companies: list[str] = Field(default_factory=list)
    excluded_keywords: list[str] = Field(default_factory=list)
    delay_min_seconds: float = 3.0
    delay_max_seconds: float = 8.0


class ScoringConfig(BaseModel):
    shortlist_threshold: int = 60
    apply_threshold: int = 75


class AutoApplyConfig(BaseModel):
    enabled: bool = False
    max_per_day: int = 10
    max_per_run: int = 5
    delay_between_seconds: int = 30
    require_confirmation: bool = True
    skip_if_already_applied: bool = True


class ScreeningAnswers(BaseModel):
    willing_to_relocate: bool = False
    comfortable_with_shifts: bool = False
    current_ctc_lpa: float = 0
    expected_ctc_lpa: float = 0
    notice_period: str = ""
    reason_for_change: str = ""
    visa_status: str = "not applicable"
    remote_work_preference: str = "flexible"
    current_employer: str = ""
    current_designation: str = ""
    years_in_current_role: float = 0
    highest_qualification: str = ""
    university_name: str = ""
    passing_year: int = 0
    gaps_in_employment: str = ""
    work_authorization: str = ""
    background_check_consent: bool = True
    references_available: bool = True


class AppConfig(BaseModel):
    profile: Profile = Field(default_factory=Profile)
    search: SearchConfig = Field(default_factory=SearchConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    screening_answers: ScreeningAnswers = Field(default_factory=ScreeningAnswers)
    auto_apply: AutoApplyConfig = Field(default_factory=AutoApplyConfig)


REQUIRED_PROFILE_FIELDS = [
    "name",
    "total_experience",
    "preferred_roles",
    "expected_salary_lpa",
    "notice_period",
]


def load_raw_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load raw YAML dict without Pydantic validation (for pre-validation prompting)."""
    if config_path is None:
        config_path = Path(__file__).resolve().parents[2] / "config" / "user.yaml"
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    return raw


def validate_raw_profile(raw: dict[str, Any]) -> list[str]:
    """Check for missing required fields in raw YAML dict."""
    profile = raw.get("profile") or {}
    missing = []
    for field in REQUIRED_PROFILE_FIELDS:
        value = profile.get(field)
        if not value or (isinstance(value, list) and len(value) == 0):
            missing.append(field)
    return missing


def prompt_missing_fields_raw(missing: list[str]) -> dict[str, Any]:
    """Interactively prompt for missing config fields."""
    from rich.prompt import Prompt

    answers: dict[str, Any] = {}
    field_labels = {
        "name": "Full name",
        "total_experience": "Years of total experience",
        "preferred_roles": "Preferred job roles (comma-separated)",
        "expected_salary_lpa": "Expected salary (LPA)",
        "notice_period": "Notice period (e.g. 30 days, immediate)",
        "preferred_locations": "Preferred locations (comma-separated)",
    }

    for field in missing:
        label = field_labels.get(field, field)
        value = Prompt.ask(f"  [bold]{label}[/]")
        if field in ("preferred_roles", "preferred_locations"):
            answers[field] = [v.strip() for v in value.split(",") if v.strip()]
        elif field == "total_experience":
            answers[field] = int(value)
        elif field == "expected_salary_lpa":
            answers[field] = float(value)
        else:
            answers[field] = value

    return answers


def save_raw_config(
    updates: dict[str, Any], config_path: str | Path | None = None
) -> None:
    """Merge updates into the profile section of the raw YAML config."""
    if config_path is None:
        config_path = Path(__file__).resolve().parents[2] / "config" / "user.yaml"
    config_path = Path(config_path)

    with open(config_path) as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    raw.setdefault("profile", {}).update(updates)

    with open(config_path, "w") as f:
        yaml.dump(raw, f, default_flow_style=False, sort_keys=False)


def load_config(config_path: str | Path | None = None) -> AppConfig:
    if config_path is None:
        config_path = Path(__file__).resolve().parents[2] / "config" / "user.yaml"
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    return AppConfig(**raw)


def validate_profile(profile: Profile) -> list[str]:
    missing = []
    for field in REQUIRED_PROFILE_FIELDS:
        value = getattr(profile, field)
        if not value or (isinstance(value, list) and len(value) == 0):
            missing.append(field)
    return missing


def prompt_missing_fields(profile: Profile, missing: list[str]) -> dict[str, Any]:
    from rich.prompt import Prompt

    answers: dict[str, Any] = {}
    field_labels = {
        "name": "Full name",
        "total_experience": "Years of total experience",
        "preferred_roles": "Preferred job roles (comma-separated)",
        "expected_salary_lpa": "Expected salary (LPA)",
        "notice_period": "Notice period (e.g. 30 days, immediate)",
        "preferred_locations": "Preferred locations (comma-separated)",
    }

    for field in missing:
        label = field_labels.get(field, field)
        value = Prompt.ask(f"  [bold]{label}[/]")
        if field in ("preferred_roles", "preferred_locations"):
            answers[field] = [v.strip() for v in value.split(",") if v.strip()]
        elif field == "total_experience":
            answers[field] = int(value)
        elif field == "expected_salary_lpa":
            answers[field] = float(value)
        else:
            answers[field] = value

    return answers


def save_updated_config(
    updates: dict[str, Any], config_path: str | Path | None = None
) -> None:
    if config_path is None:
        config_path = Path(__file__).resolve().parents[2] / "config" / "user.yaml"
    config_path = Path(config_path)

    with open(config_path) as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    raw.setdefault("profile", {}).update(updates)

    with open(config_path, "w") as f:
        yaml.dump(raw, f, default_flow_style=False, sort_keys=False)
