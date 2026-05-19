"""Configuration loading, validation, and bootstrap.

New config model (Phase 3.2):
- config/app.yaml: search, scoring, apply, screening policy (platform-agnostic strategy)
- config/user.yaml: candidate truth, screening answers, corrections
- config/platform.yaml: platform-specific behavior and overrides
- data/profile_cache.json: resume-extracted facts (generated-only)

Precedence: platform > app > user > cache > code defaults
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class SearchExperienceRange(BaseModel):
    min: int | None = None
    max: int | None = None


class SearchSalaryRange(BaseModel):
    min_lpa: float | None = None
    max_lpa: float | None = None


class SearchConfig(BaseModel):
    platforms: list[str] = Field(default_factory=lambda: ["naukri"])
    preferred_roles: list[str] = Field(default_factory=list)
    role_families: list[str] = Field(default_factory=list)
    seniority_level: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    experience_range: SearchExperienceRange | None = None
    salary_range: SearchSalaryRange | None = None
    min_company_rating: float | None = None
    company_size_preference: list[str] = Field(default_factory=list)
    company_type_preference: list[str] = Field(default_factory=list)
    industry_preference: list[str] = Field(default_factory=list)
    work_mode_preference: str = "hybrid"
    work_mode_filter: list[str] = Field(default_factory=list)
    job_types: list[str] = Field(default_factory=list)
    excluded_companies: list[str] = Field(default_factory=list)
    excluded_keywords: list[str] = Field(default_factory=list)
    included_keywords: list[str] = Field(default_factory=list)
    title_exclude_keywords: list[str] = Field(default_factory=list)
    freshness_days: int | None = None
    max_jobs: int | None = None
    max_jobs_per_query: int | None = None
    custom_requirements: list[str] = Field(default_factory=list)
    delay_min_seconds: float = 3.0
    delay_max_seconds: float = 8.0

    @property
    def max_locations(self) -> int:
        return 3

    @property
    def max_roles(self) -> int:
        return 5

    @property
    def salary_min_lpa(self) -> float:
        return self.salary_range.min_lpa if self.salary_range else 0.0

    @property
    def salary_max_lpa(self) -> float:
        return self.salary_range.max_lpa if self.salary_range else 0.0

    @property
    def experience_years(self) -> int:
        return self.experience_range.min if self.experience_range else 0

    @property
    def freshness(self) -> int:
        return self.freshness_days or 0


class AppProfile(BaseModel):
    """Identity and path settings that have no home in search/scoring/user config."""

    name: str = ""
    total_experience: int = 0
    expected_salary_lpa: float = 0
    notice_period: str = ""
    resume_path: str = "resume.pdf"


class NaukriConfig(BaseModel):
    """Backward-compatible naukri section."""

    login_required: bool = True
    headless: bool = False
    page_timeout: int = 30000
    max_pages: int = 3
    delay_between_pages: int = 3


class ScoringWeights(BaseModel):
    skills: float = 0.35
    role: float = 0.20
    experience: float = 0.20
    company: float = 0.10
    location: float = 0.08
    work_mode: float = 0.07


class ScoringLLMConfig(BaseModel):
    enabled: bool = False
    batch_size: int | None = None
    shortlist_threshold: int | None = None
    custom_requirements: list[str] = Field(default_factory=list)
    consider_location: bool = False
    consider_work_mode: bool = False


class ScoringConfig(BaseModel):
    shortlist_threshold: int = 60
    apply_threshold: int = 75
    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    llm_scoring: ScoringLLMConfig | None = None

    @property
    def skill_weight(self) -> float:
        return self.weights.skills

    @property
    def role_weight(self) -> float:
        return self.weights.role

    @property
    def experience_weight(self) -> float:
        return self.weights.experience

    @property
    def company_weight(self) -> float:
        return self.weights.company

    @property
    def location_weight(self) -> float:
        return self.weights.location

    @property
    def work_mode_weight(self) -> float:
        return self.weights.work_mode


class AutoApplyConfig(BaseModel):
    enabled: bool = False
    max_per_day: int | None = None
    max_per_run: int | None = None
    delay_between_seconds: float = 5.0
    require_confirmation: bool | None = None
    skip_if_already_applied: bool | None = None
    custom_requirements: list[str] = Field(default_factory=list)


class ScreeningPolicy(BaseModel):
    enabled: bool = False
    batch_size: int | None = None
    custom_requirements: list[str] = Field(default_factory=list)


class AppConfig(BaseModel):
    search: SearchConfig = Field(default_factory=SearchConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    auto_apply: AutoApplyConfig = Field(default_factory=AutoApplyConfig)
    screening: ScreeningPolicy | None = None
    profile: AppProfile = Field(default_factory=AppProfile)
    naukri: NaukriConfig = Field(default_factory=NaukriConfig)
    profile_overrides: ProfileOverrides | None = None
    profile_enrichment: ProfileEnrichment | None = None


class UserProfileUrls(BaseModel):
    github: str | None = None
    linkedin: str | None = None
    portfolio: str | None = None


class UserProfile(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    current_location: str | None = None
    notice_period_days: int | None = None
    serving_notice_period: bool | None = None
    currently_working: bool | None = None
    current_company: str | None = None
    current_designation: str | None = None
    current_ctc_lpa: float | None = None
    previous_company: str | None = None
    previous_designation: str | None = None
    previous_ctc_lpa: float | None = None
    last_working_day: str | None = None
    pan_number: str | None = None
    alternate_email: str | None = None
    urls: UserProfileUrls = Field(default_factory=UserProfileUrls)
    additional_info: dict[str, Any] = Field(default_factory=dict)
    custom_requirements: list[str] = Field(default_factory=list)


class UserExperience(BaseModel):
    total_experience_years: int | None = None
    skills_with_experience: dict[str, int] = Field(default_factory=dict)
    aliases: dict[str, list[str]] = Field(default_factory=dict)
    primary_stack: list[str] = Field(default_factory=list)
    secondary_stack: list[str] = Field(default_factory=list)
    domain_experience: dict[str, int] = Field(default_factory=dict)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class UserNarrative(BaseModel):
    career_goal: str | None = None
    strengths: str | None = None
    what_i_bring: str | None = None
    reason_for_change: str | None = None
    preferred_company_type: list[str] = Field(default_factory=list)
    preferred_work_style: str | None = None
    custom: dict[str, Any] = Field(default_factory=dict)


class ScreeningAnswersDefaults(BaseModel):
    current_ctc_lpa: float | None = None
    expected_ctc_lpa: float | None = None
    notice_period: str | int | None = None
    reason_for_change: str | None = None
    visa_status: str | None = None
    remote_work_preference: str | None = None
    willing_to_relocate: bool | None = None
    comfortable_with_shifts: bool | None = None
    work_authorization: str | None = None
    background_check_consent: bool | None = None
    references_available: bool | None = None


class ScreeningAnswersConfig(BaseModel):
    enabled: bool = False
    defaults: ScreeningAnswersDefaults = Field(default_factory=ScreeningAnswersDefaults)
    answers: dict[str, Any] = Field(default_factory=dict)
    role_specific: dict[str, dict[str, Any]] = Field(default_factory=dict)
    custom_requirements: list[str] = Field(default_factory=list)
    custom_answers: dict[str, Any] = Field(default_factory=dict)


class ProfileOverrides(BaseModel):
    """Backward-compatible profile overrides."""

    total_experience_years: int | None = None
    skills: list[str] = Field(default_factory=list)
    tech_experience: dict[str, int] = Field(default_factory=dict)


class ProfileEnrichment(BaseModel):
    """Backward-compatible profile enrichment."""

    career_goal: str = ""
    strengths: str = ""
    what_can_you_bring: str = ""
    reason_for_change: str = ""
    preferred_company_types: list[str] = Field(default_factory=list)
    open_to_contract: bool | None = None
    additional_skills: list[str] = Field(default_factory=list)


class UserEducation(BaseModel):
    degree: str | None = None
    specialization: str | None = None
    institution: str | None = None
    graduation_year: int | None = None
    grade: str | None = None  # CGPA or percentage, e.g. "8.5 CGPA" or "78%"


class UserConfig(BaseModel):
    profile: UserProfile = Field(default_factory=UserProfile)
    education: list[UserEducation] = Field(default_factory=list)
    experience: UserExperience = Field(default_factory=UserExperience)
    narrative: UserNarrative = Field(default_factory=UserNarrative)
    screening_answers: ScreeningAnswersConfig = Field(default_factory=ScreeningAnswersConfig)


class PlatformNaukriConfig(BaseModel):
    enabled: bool = True
    login_required: bool = True
    headless: bool = False
    page_timeout: int | None = None
    max_pages: int | None = None
    delay_between_pages: float | None = None
    search: dict[str, Any] = Field(default_factory=dict)
    apply: dict[str, Any] = Field(default_factory=dict)
    custom_requirements: list[str] = Field(default_factory=list)


class PlatformLinkedinConfig(BaseModel):
    enabled: bool | None = None
    search: dict[str, Any] = Field(default_factory=dict)
    apply: dict[str, Any] = Field(default_factory=dict)
    custom_requirements: list[str] = Field(default_factory=list)


class PlatformConfig(BaseModel):
    naukri: PlatformNaukriConfig = Field(default_factory=PlatformNaukriConfig)
    linkedin: PlatformLinkedinConfig = Field(default_factory=PlatformLinkedinConfig)


class ResumeProfile(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    skills: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    total_experience_years: int = 0
    past_roles: list[str] = Field(default_factory=list)
    industry_domain: str = ""
    location_preference: str = ""
    salary_expectation: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    summary: str = ""
    detailed: dict[str, Any] = Field(default_factory=dict)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"


def load_app_config(config_path: Path | None = None) -> AppConfig:
    if config_path is None:
        config_path = CONFIG_DIR / "app.yaml"
    if not config_path.exists():
        return AppConfig()
    with open(config_path) as f:
        raw = yaml.safe_load(f) or {}

    if "scoring" in raw:
        scoring = raw["scoring"]
        if "weights" in scoring:
            weights = scoring["weights"]
        else:
            weights = {}
            scoring["weights"] = weights
        for old_key, new_key in [
            ("skill_weight", "skills"),
            ("role_weight", "role"),
            ("experience_weight", "experience"),
            ("company_weight", "company"),
            ("location_weight", "location"),
            ("work_mode_weight", "work_mode"),
        ]:
            if old_key in scoring:
                weights[new_key] = scoring.pop(old_key)

    if "search" in raw:
        search = raw["search"]
        for old_key in ["salary_min_lpa", "salary_max_lpa", "experience_years", "freshness"]:
            if old_key in search:
                value = search.pop(old_key)
                if old_key == "salary_min_lpa":
                    search.setdefault("salary_range", {})["min_lpa"] = value
                elif old_key == "salary_max_lpa":
                    search.setdefault("salary_range", {})["max_lpa"] = value
                elif old_key == "experience_years":
                    search.setdefault("experience_range", {})["min"] = value
                elif old_key == "freshness":
                    search["freshness_days"] = value

    return AppConfig(**raw)


def load_effective_app_config() -> AppConfig:
    """Load app config merged with user config for backward compatibility."""
    app = load_app_config()
    user = load_user_config()

    if user.profile.name:
        app.profile.name = user.profile.name
    if user.experience.total_experience_years:
        app.profile.total_experience = user.experience.total_experience_years
    if user.profile.current_ctc_lpa:
        app.profile.expected_salary_lpa = user.profile.current_ctc_lpa
    if user.profile.notice_period_days:
        app.profile.notice_period = f"{user.profile.notice_period_days} days"

    # Seed search.preferred_roles from resume if not explicitly set in app.yaml
    if user.experience.secondary_stack and not app.search.preferred_roles:
        app.search.preferred_roles = user.experience.secondary_stack

    # Seed search.preferred_locations from user location if not set in app.yaml
    if user.profile.current_location and not app.search.preferred_locations:
        app.search.preferred_locations = [user.profile.current_location]

    # User narrative overrides work_mode_preference if not explicitly set in app.yaml
    if user.narrative.preferred_work_style and app.search.work_mode_preference == "hybrid":
        app.search.work_mode_preference = user.narrative.preferred_work_style.lower()

    # Profile overrides/enrichment backward compat
    if user.experience.skills_with_experience:
        app.profile_overrides = ProfileOverrides(
            skills=list(user.experience.skills_with_experience.keys()),
            tech_experience=user.experience.skills_with_experience,
        )
    if user.narrative.strengths or user.narrative.what_i_bring:
        app.profile_enrichment = ProfileEnrichment(
            strengths=user.narrative.strengths or "",
            what_can_you_bring=user.narrative.what_i_bring or "",
            reason_for_change=user.narrative.reason_for_change or "",
        )

    naukri_cfg = load_platform_config().naukri
    app.naukri.login_required = naukri_cfg.login_required
    app.naukri.headless = naukri_cfg.headless
    if naukri_cfg.page_timeout:
        app.naukri.page_timeout = naukri_cfg.page_timeout
    if naukri_cfg.max_pages:
        app.naukri.max_pages = naukri_cfg.max_pages
    if naukri_cfg.delay_between_pages:
        app.naukri.delay_between_pages = naukri_cfg.delay_between_pages

    return app


def load_user_config(config_path: Path | None = None) -> UserConfig:
    if config_path is None:
        config_path = CONFIG_DIR / "user.yaml"
    if not config_path.exists():
        return UserConfig()
    with open(config_path) as f:
        raw = yaml.safe_load(f) or {}
    return UserConfig(**raw)


def load_platform_config(config_path: Path | None = None) -> PlatformConfig:
    if config_path is None:
        config_path = CONFIG_DIR / "platform.yaml"
    if not config_path.exists():
        return PlatformConfig()
    with open(config_path) as f:
        raw = yaml.safe_load(f) or {}
    return PlatformConfig(**raw)


def load_resume_profile(profile_path: Path | None = None) -> ResumeProfile | None:
    if profile_path is None:
        profile_path = DATA_DIR / "profile_cache.json"
    if not profile_path.exists():
        return None
    import json
    with open(profile_path) as f:
        raw = json.load(f)
    return ResumeProfile(**raw)


def build_effective_config():
    """Build effective config with proper precedence: platform > app > user > cache > defaults."""
    app = load_effective_app_config()
    user = load_user_config()
    platform = load_platform_config()
    cache = load_resume_profile()
    return {
        "app": app,
        "user": user,
        "platform": platform,
        "cache": cache,
    }


def get_screening_answers(user_cfg: UserConfig | None = None) -> ScreeningAnswersDefaults:
    """Get screening answers from user config."""
    if user_cfg is None:
        user_cfg = load_user_config()
    return user_cfg.screening_answers.defaults


def create_app_template() -> dict[str, Any]:
    """Create default app.yaml template."""
    return {
        "search": {
            "platforms": ["naukri"],
            "preferred_roles": [],
            "role_families": [],
            "seniority_level": [],
            "preferred_locations": [],
            "experience_range": None,
            "salary_range": None,
            "min_company_rating": None,
            "company_size_preference": [],
            "company_type_preference": [],
            "industry_preference": [],
            "work_mode_preference": "hybrid",
            "work_mode_filter": [],
            "job_types": [],
            "excluded_companies": [],
            "excluded_keywords": [],
            "included_keywords": [],
            "title_exclude_keywords": [],
            "freshness_days": None,
            "max_jobs": None,
            "max_jobs_per_query": 20,
            "custom_requirements": [],
        },
        "scoring": {
            "shortlist_threshold": 30,
            "apply_threshold": 75,
            "weights": {
                "skills": 0.35,
                "role": 0.20,
                "experience": 0.20,
                "company": 0.10,
                "location": 0.08,
                "work_mode": 0.07,
            },
            "llm_scoring": {
                "enabled": False,
                "batch_size": None,
                "shortlist_threshold": None,
                "apply_threshold": None,
                "custom_requirements": [],
                "consider_location": False,
                "consider_work_mode": False,
            },
        },
        "auto_apply": {
            "enabled": False,
            "max_per_day": None,
            "max_per_run": None,
            "delay_between_seconds": None,
            "require_confirmation": None,
            "skip_if_already_applied": None,
            "custom_requirements": [],
        },
        "screening": {
            "enabled": False,
            "batch_size": None,
            "custom_requirements": [],
        },
        "profile": {
            "name": "",
            "total_experience": 0,
            "expected_salary_lpa": 0,
            "notice_period": "",
            "resume_path": "resume.pdf",
        },
        "naukri": {
            "login_required": True,
            "headless": False,
            "page_timeout": 30000,
            "max_pages": 3,
            "delay_between_pages": 3,
        },
    }


def create_user_template() -> dict[str, Any]:
    """Create default user.yaml template."""
    return {
        "profile": {
            "name": None,
            "email": None,
            "phone": None,
            "current_location": None,
            "notice_period_days": None,
            "serving_notice_period": None,
            "currently_working": None,
            "current_company": None,
            "current_designation": None,
            "current_ctc_lpa": None,
            "previous_company": None,
            "previous_designation": None,
            "previous_ctc_lpa": None,
            "last_working_day": None,
            "pan_number": None,
            "alternate_email": None,
            "urls": {
                "github": None,
                "linkedin": None,
                "portfolio": None,
            },
            "additional_info": {},
            "custom_requirements": [],
        },
        "education": [],
        "experience": {
            "total_experience_years": None,
            "skills_with_experience": {},
            "aliases": {},
            "primary_stack": [],
            "secondary_stack": [],
            "domain_experience": {},
            "certifications": [],
            "achievements": [],
        },
        "narrative": {
            "career_goal": None,
            "strengths": None,
            "what_i_bring": None,
            "reason_for_change": None,
            "preferred_company_type": [],
            "preferred_work_style": None,
            "custom": {},
        },
        "screening_answers": {
            "enabled": False,
            "defaults": {
                "current_ctc_lpa": None,
                "expected_ctc_lpa": None,
                "notice_period": None,
                "reason_for_change": None,
                "visa_status": None,
                "remote_work_preference": None,
                "willing_to_relocate": None,
                "comfortable_with_shifts": None,
                "work_authorization": None,
                "background_check_consent": None,
                "references_available": None,
            },
            "answers": {},
            "role_specific": {},
            "custom_requirements": [],
            "custom_answers": {},
        },
    }


def create_platform_template() -> dict[str, Any]:
    """Create default platform.yaml template."""
    return {
        "naukri": {
            "enabled": True,
            "login_required": True,
            "headless": False,
            "page_timeout": None,
            "max_pages": None,
            "delay_between_pages": None,
            "search": {},
            "apply": {},
            "custom_requirements": [],
        },
        "linkedin": {
            "enabled": None,
            "search": {},
            "apply": {},
            "custom_requirements": [],
        },
    }


def ensure_config_files_exist(resume_profile: ResumeProfile | None = None) -> dict[str, bool]:
    """Ensure all config files exist, creating missing ones from templates.

    If resume_profile is provided, seeds app.yaml and user.yaml with resume data.
    Never overwrites existing files.

    Returns dict of str(file_path) -> created (bool).
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    created: dict[str, bool] = {}

    app_path = CONFIG_DIR / "app.yaml"
    if not app_path.exists():
        app_data = create_app_template()
        if resume_profile:
            roles = resume_profile.target_roles or resume_profile.past_roles[:3]
            if roles:
                app_data["search"]["preferred_roles"] = roles
            if resume_profile.location_preference:
                app_data["search"]["preferred_locations"] = [resume_profile.location_preference]
        with open(app_path, "w") as f:
            yaml.dump(app_data, f, default_flow_style=False, sort_keys=False)
        created[str(app_path)] = True

    user_path = CONFIG_DIR / "user.yaml"
    if not user_path.exists():
        user_data = create_user_template()
        if resume_profile:
            pf = resume_profile
            if pf.name:
                user_data["profile"]["name"] = pf.name
            if pf.email:
                user_data["profile"]["email"] = pf.email
            if pf.phone:
                user_data["profile"]["phone"] = pf.phone
            if pf.total_experience_years:
                user_data["experience"]["total_experience_years"] = pf.total_experience_years
            if pf.tech_stack:
                user_data["experience"]["primary_stack"] = pf.tech_stack
            if pf.detailed.get("achievements"):
                user_data["experience"]["achievements"] = pf.detailed["achievements"]
            if pf.target_roles:
                user_data["experience"]["secondary_stack"] = pf.target_roles
            if pf.detailed.get("tech_experience"):
                user_data["experience"]["skills_with_experience"] = pf.detailed["tech_experience"]
        with open(user_path, "w") as f:
            yaml.dump(user_data, f, default_flow_style=False, sort_keys=False)
        created[str(user_path)] = True

    platform_path = CONFIG_DIR / "platform.yaml"
    if not platform_path.exists():
        with open(platform_path, "w") as f:
            yaml.dump(create_platform_template(), f, default_flow_style=False, sort_keys=False)
        created[str(platform_path)] = True

    return created


def seed_config_from_profile(
    profile: ResumeProfile,
    detailed_profile: dict[str, Any] | None,
    created: dict[str, bool],
) -> None:
    """Re-seed freshly-created config files with data from a just-parsed resume profile.

    Only updates files in `created` (output of ensure_config_files_exist), and only fills
    fields still at empty/None defaults — never clobbers values the user has set.
    """
    app_path = str(CONFIG_DIR / "app.yaml")
    user_path = str(CONFIG_DIR / "user.yaml")

    if created.get(app_path):
        with open(app_path) as f:
            app_data = yaml.safe_load(f) or {}
        search = app_data.setdefault("search", {})
        roles = profile.target_roles or profile.past_roles[:3]
        if roles and not search.get("preferred_roles"):
            search["preferred_roles"] = roles
        if profile.location_preference and not search.get("preferred_locations"):
            search["preferred_locations"] = [profile.location_preference]
        with open(app_path, "w") as f:
            yaml.dump(app_data, f, default_flow_style=False, sort_keys=False)

    if created.get(user_path):
        with open(user_path) as f:
            user_data = yaml.safe_load(f) or {}
        pf_section = user_data.setdefault("profile", {})
        if profile.name and not pf_section.get("name"):
            pf_section["name"] = profile.name
        if profile.email and not pf_section.get("email"):
            pf_section["email"] = profile.email
        exp_section = user_data.setdefault("experience", {})
        if profile.total_experience_years and not exp_section.get("total_experience_years"):
            exp_section["total_experience_years"] = profile.total_experience_years
        if detailed_profile:
            tech_exp = detailed_profile.get("tech_experience", {})
            if tech_exp and not exp_section.get("skills_with_experience"):
                exp_section["skills_with_experience"] = tech_exp
        with open(user_path, "w") as f:
            yaml.dump(user_data, f, default_flow_style=False, sort_keys=False)


def bootstrap_config(resume_path: str | Path | None = None) -> dict[str, Any]:
    """Bootstrap config: ensure files exist, load effective config.

    If resume_path provided and cache exists, also load for seeding.
    """
    resume_profile = None
    if resume_path:
        resume_profile = load_resume_profile(
            DATA_DIR / "profile_cache.json" if resume_path else None
        )

    created = ensure_config_files_exist(resume_profile)
    effective = build_effective_config()
    return {
        "created": created,
        "config": effective,
    }