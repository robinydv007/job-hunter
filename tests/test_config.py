"""Tests for Phase 3.2 config bootstrap, precedence, seeding, and CSV export stability."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
import yaml

import job_hunter.config as cfg
from job_hunter.config import (
    AppConfig,
    PlatformConfig,
    ResumeProfile,
    UserConfig,
    create_app_template,
    create_platform_template,
    create_user_template,
    ensure_config_files_exist,
    load_app_config,
    load_effective_app_config,
    load_platform_config,
    load_resume_profile,
    load_user_config,
)
from job_hunter.export.csv_export import ROW_MAPPING, export_to_csv


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def isolated_config(tmp_path, monkeypatch):
    """Redirect CONFIG_DIR and DATA_DIR to a temp directory for each test."""
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    monkeypatch.setattr(cfg, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(cfg, "DATA_DIR", data_dir)
    return config_dir, data_dir


# ---------------------------------------------------------------------------
# Missing-file bootstrap
# ---------------------------------------------------------------------------


def test_load_app_config_missing_file_returns_defaults(tmp_path):
    result = load_app_config(tmp_path / "nonexistent.yaml")
    assert isinstance(result, AppConfig)
    assert result.scoring.shortlist_threshold == 60
    assert result.search.platforms == ["naukri"]


def test_load_user_config_missing_file_returns_defaults(tmp_path):
    result = load_user_config(tmp_path / "nonexistent.yaml")
    assert isinstance(result, UserConfig)
    assert result.profile.name is None
    assert result.experience.primary_stack == []


def test_load_platform_config_missing_file_returns_defaults(tmp_path):
    result = load_platform_config(tmp_path / "nonexistent.yaml")
    assert isinstance(result, PlatformConfig)
    assert result.naukri.login_required is True
    assert result.naukri.max_pages is None


def test_load_resume_profile_missing_file_returns_none(tmp_path):
    result = load_resume_profile(tmp_path / "nonexistent.json")
    assert result is None


def test_ensure_config_files_exist_creates_all_three(isolated_config):
    config_dir, data_dir = isolated_config
    created = ensure_config_files_exist()
    assert (config_dir / "app.yaml").exists()
    assert (config_dir / "user.yaml").exists()
    assert (config_dir / "platform.yaml").exists()
    assert len(created) == 3


def test_ensure_config_files_exist_created_files_are_valid_yaml(isolated_config):
    config_dir, _ = isolated_config
    ensure_config_files_exist()
    for name in ("app.yaml", "user.yaml", "platform.yaml"):
        content = yaml.safe_load((config_dir / name).read_text())
        assert isinstance(content, dict)


# ---------------------------------------------------------------------------
# Non-overwrite behavior
# ---------------------------------------------------------------------------


def test_ensure_config_files_exist_does_not_overwrite_existing(isolated_config):
    config_dir, _ = isolated_config
    config_dir.mkdir(parents=True, exist_ok=True)
    sentinel = "# sentinel content\n"
    (config_dir / "app.yaml").write_text(sentinel)

    ensure_config_files_exist()

    assert (config_dir / "app.yaml").read_text() == sentinel


def test_ensure_config_files_exist_partial_missing_creates_only_absent(isolated_config):
    config_dir, _ = isolated_config
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "app.yaml").write_text("search:\n  platforms: [naukri]\n")

    created = ensure_config_files_exist()

    assert config_dir / "app.yaml" not in created
    assert config_dir / "user.yaml" in created
    assert config_dir / "platform.yaml" in created


def test_ensure_config_files_exist_no_files_created_when_all_exist(isolated_config):
    config_dir, _ = isolated_config
    config_dir.mkdir(parents=True)
    for name in ("app.yaml", "user.yaml", "platform.yaml"):
        (config_dir / name).write_text("placeholder: true\n")

    created = ensure_config_files_exist()

    assert created == {}


# ---------------------------------------------------------------------------
# Precedence and defaults
# ---------------------------------------------------------------------------


def test_load_app_config_reads_scoring_threshold(tmp_path):
    path = tmp_path / "app.yaml"
    path.write_text("scoring:\n  shortlist_threshold: 55\n")
    result = load_app_config(path)
    assert result.scoring.shortlist_threshold == 55


def test_load_app_config_partial_file_keeps_unset_defaults(tmp_path):
    path = tmp_path / "app.yaml"
    path.write_text("scoring:\n  shortlist_threshold: 40\n")
    result = load_app_config(path)
    assert result.scoring.apply_threshold == 75
    assert result.search.platforms == ["naukri"]


def test_load_platform_config_naukri_overrides_read(tmp_path):
    path = tmp_path / "platform.yaml"
    path.write_text("naukri:\n  max_pages: 7\n  headless: true\n")
    result = load_platform_config(path)
    assert result.naukri.max_pages == 7
    assert result.naukri.headless is True


def test_scoring_weights_accessible_via_properties(tmp_path):
    path = tmp_path / "app.yaml"
    path.write_text(
        "scoring:\n  weights:\n    skills: 0.40\n    role: 0.20\n"
        "    experience: 0.20\n    company: 0.10\n    location: 0.05\n    work_mode: 0.05\n"
    )
    result = load_app_config(path)
    assert result.scoring.skill_weight == pytest.approx(0.40)
    assert result.scoring.role_weight == pytest.approx(0.20)


# ---------------------------------------------------------------------------
# Backward compatibility — old field names
# ---------------------------------------------------------------------------


def test_load_app_config_migrates_old_scoring_weight_keys(tmp_path):
    path = tmp_path / "app.yaml"
    path.write_text(
        "scoring:\n  skill_weight: 0.40\n  role_weight: 0.25\n"
        "  experience_weight: 0.15\n  company_weight: 0.10\n"
        "  location_weight: 0.05\n  work_mode_weight: 0.05\n"
    )
    result = load_app_config(path)
    assert result.scoring.weights.skills == pytest.approx(0.40)
    assert result.scoring.weights.role == pytest.approx(0.25)


def test_load_app_config_migrates_old_salary_keys(tmp_path):
    path = tmp_path / "app.yaml"
    path.write_text("search:\n  salary_min_lpa: 12\n  salary_max_lpa: 25\n")
    result = load_app_config(path)
    assert result.search.salary_range is not None
    assert result.search.salary_range.min_lpa == 12
    assert result.search.salary_range.max_lpa == 25


def test_load_app_config_migrates_old_experience_years_key(tmp_path):
    path = tmp_path / "app.yaml"
    path.write_text("search:\n  experience_years: 5\n")
    result = load_app_config(path)
    assert result.search.experience_range is not None
    assert result.search.experience_range.min == 5


def test_load_app_config_migrates_old_freshness_key(tmp_path):
    path = tmp_path / "app.yaml"
    path.write_text("search:\n  freshness: 14\n")
    result = load_app_config(path)
    assert result.search.freshness_days == 14


def test_load_app_config_new_keys_not_overridden_by_compat(tmp_path):
    """New-style weights.skills takes precedence over missing old keys."""
    path = tmp_path / "app.yaml"
    path.write_text("scoring:\n  weights:\n    skills: 0.50\n")
    result = load_app_config(path)
    assert result.scoring.weights.skills == pytest.approx(0.50)


# ---------------------------------------------------------------------------
# Resume seeding behavior
# ---------------------------------------------------------------------------


def test_ensure_config_files_exist_seeds_user_yaml_from_resume(isolated_config):
    config_dir, _ = isolated_config
    resume = ResumeProfile(
        name="Alice",
        email="alice@example.com",
        phone="9999999999",
        total_experience_years=6,
        target_roles=["Backend Engineer", "SRE"],
        tech_stack=["Python", "Go"],
    )

    ensure_config_files_exist(resume_profile=resume)

    user_data = yaml.safe_load((config_dir / "user.yaml").read_text())
    assert user_data["profile"]["name"] == "Alice"
    assert user_data["profile"]["email"] == "alice@example.com"
    assert user_data["experience"]["total_experience_years"] == 6
    assert "Backend Engineer" in user_data["experience"]["secondary_stack"]


def test_ensure_config_files_exist_does_not_seed_when_user_yaml_exists(isolated_config):
    config_dir, _ = isolated_config
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "user.yaml").write_text("profile:\n  name: Existing User\n")

    resume = ResumeProfile(name="Resume User", total_experience_years=3)
    ensure_config_files_exist(resume_profile=resume)

    user_data = yaml.safe_load((config_dir / "user.yaml").read_text())
    assert user_data["profile"]["name"] == "Existing User"


def test_ensure_config_files_exist_seed_without_resume_uses_blank_template(isolated_config):
    config_dir, _ = isolated_config
    ensure_config_files_exist(resume_profile=None)
    user_data = yaml.safe_load((config_dir / "user.yaml").read_text())
    assert user_data["profile"]["name"] is None
    assert user_data["experience"]["total_experience_years"] is None


# ---------------------------------------------------------------------------
# Platform overrides
# ---------------------------------------------------------------------------


def test_load_effective_app_config_platform_max_pages_overrides_app(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "app.yaml").write_text("naukri:\n  max_pages: 2\n")
    (config_dir / "platform.yaml").write_text("naukri:\n  max_pages: 9\n")

    monkeypatch.setattr(cfg, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(cfg, "DATA_DIR", tmp_path / "data")

    result = load_effective_app_config()
    assert result.naukri.max_pages == 9


def test_load_effective_app_config_platform_headless_overrides_app(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "app.yaml").write_text("naukri:\n  headless: false\n")
    (config_dir / "platform.yaml").write_text("naukri:\n  headless: true\n")

    monkeypatch.setattr(cfg, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(cfg, "DATA_DIR", tmp_path / "data")

    result = load_effective_app_config()
    assert result.naukri.headless is True


def test_load_effective_app_config_user_profile_name_merged(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "user.yaml").write_text("profile:\n  name: Bob\n")

    monkeypatch.setattr(cfg, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(cfg, "DATA_DIR", tmp_path / "data")

    result = load_effective_app_config()
    assert result.profile.name == "Bob"


def test_load_effective_app_config_no_platform_file_uses_app_defaults(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "app.yaml").write_text("naukri:\n  max_pages: 5\n")

    monkeypatch.setattr(cfg, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(cfg, "DATA_DIR", tmp_path / "data")

    result = load_effective_app_config()
    assert result.naukri.max_pages == 5


# ---------------------------------------------------------------------------
# Role-family
# ---------------------------------------------------------------------------


def test_role_families_loaded_from_app_yaml(tmp_path):
    path = tmp_path / "app.yaml"
    path.write_text("search:\n  role_families:\n  - backend\n  - platform\n")
    result = load_app_config(path)
    assert result.search.role_families == ["backend", "platform"]


def test_role_families_default_empty(tmp_path):
    path = tmp_path / "app.yaml"
    path.write_text("search:\n  preferred_roles:\n  - SRE\n")
    result = load_app_config(path)
    assert result.search.role_families == []


# ---------------------------------------------------------------------------
# CSV export stability
# ---------------------------------------------------------------------------


def test_export_to_csv_produces_expected_columns(tmp_path):
    out = tmp_path / "jobs.csv"
    export_to_csv([], out)
    with open(out, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert list(reader.fieldnames) == list(ROW_MAPPING.keys())


def test_export_to_csv_handles_partial_job_dict(tmp_path):
    out = tmp_path / "jobs.csv"
    scored_job = {
        "job": {"title": "Engineer", "company": "Acme"},
        "match_score": 80,
        "matched_skills": ["Python"],
    }
    export_to_csv([scored_job], out)
    with open(out, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["Job Title"] == "Engineer"
    assert rows[0]["Match Score"] == "80"
    assert rows[0]["Matched Skills"] == "Python"
    assert rows[0]["Apply Status"] == "Pending"
    assert rows[0]["Apply Error"] == ""


def test_export_to_csv_multiple_jobs(tmp_path):
    out = tmp_path / "jobs.csv"
    jobs = [
        {"job": {"title": f"Job {i}"}, "match_score": i * 10}
        for i in range(1, 4)
    ]
    export_to_csv(jobs, out)
    with open(out, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    assert rows[2]["Job Title"] == "Job 3"


def test_export_to_csv_truncates_long_description(tmp_path):
    out = tmp_path / "jobs.csv"
    long_desc = "x" * 600
    export_to_csv([{"job": {"description": long_desc}}], out)
    with open(out, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows[0]["Job Description"]) == 503  # 500 chars + "..."


def test_export_to_csv_creates_parent_dirs(tmp_path):
    out = tmp_path / "nested" / "deep" / "jobs.csv"
    export_to_csv([], out)
    assert out.exists()


def test_export_to_csv_column_schema_stable():
    expected = [
        "Job Title", "Company", "Location", "Experience Required",
        "Match Score", "Job Description", "Why Selected", "Matched Skills",
        "Questionnaire", "Job Board", "Job URL", "Work Mode", "Salary LPA",
        "Posted Date", "Data Source", "Apply Status", "Apply Timestamp",
        "Questionnaire Timestamp", "Apply Error",
    ]
    assert list(ROW_MAPPING.keys()) == expected
