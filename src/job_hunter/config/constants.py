"""Project-wide domain knowledge constants."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class Constants(BaseModel):
    """Project-wide domain knowledge constants — not user-specific."""

    skill_aliases: dict[str, list[str]] = Field(default_factory=dict)
    company_rating_bands: dict[float, int] = Field(
        default_factory=lambda: {
            4.5: 100,
            4.0: 90,
            3.5: 75,
            3.0: 60,
            2.5: 40,
        }
    )
    company_rating_default: int = 20
    review_count_boosts: dict[int, int] = Field(
        default_factory=lambda: {10000: 10, 1000: 5}
    )
    experience_penalties: dict[str, Any] = Field(
        default_factory=lambda: {
            "over": {
                2: 90,
                4: 75,
                6: 55,
                "default_formula": "40 - (over - 6) * 8",
            },
            "under": {
                1: 70,
                2: 50,
                3: 30,
                "default_formula": "20 - (under - 3) * 10",
            },
        }
    )
    role_overlap_thresholds: dict[float, int] = Field(
        default_factory=lambda: {0.5: 80, 0.3: 60, 0.01: 40}
    )
    role_overlap_default: int = 20
    work_mode_scores: dict[str, Any] = Field(
        default_factory=lambda: {
            "hybrid": {"hybrid": 100, "remote": 80, "onsite": 50, "default": 60},
            "remote": {"remote": 100, "hybrid": 70, "default": 30},
            "onsite": {"onsite": 100, "hybrid": 70, "default": 40},
            "default": 60,
        }
    )
    metro_cities: dict[str, list[str]] = Field(default_factory=dict)


@lru_cache(maxsize=1)
def load_constants(constants_path: str | Path | None = None) -> Constants:
    """Load project-wide constants from config/constants.yaml (cached)."""
    if constants_path is None:
        constants_path = (
            Path(__file__).resolve().parents[3] / "config" / "constants.yaml"
        )
    constants_path = Path(constants_path)

    if not constants_path.exists():
        return Constants()

    with open(constants_path) as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    return Constants(**raw)
