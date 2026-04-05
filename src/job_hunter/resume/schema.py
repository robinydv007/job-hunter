"""Pydantic schema for the structured profile extracted from a resume."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ResumeProfile(BaseModel):
    """Structured profile parsed from a resume."""

    name: str = ""
    email: str = ""
    phone: str = ""
    skills: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    total_experience_years: float = 0
    past_roles: list[str] = Field(default_factory=list)
    industry_domain: str = ""
    location_preference: str = ""
    preferred_locations: list[str] = Field(default_factory=list)
    salary_expectation: str = ""
    target_roles: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    summary: str = ""
