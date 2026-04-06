"""Naukri platform constants."""

from pydantic import BaseModel, Field


class NaukriConstants(BaseModel):
    base_url: str = "https://www.naukri.com"
    login_url: str = "https://www.naukri.com/nlogin/login"
    timezone: str = "Asia/Kolkata"
    freshness_values: list[int] = Field(default_factory=lambda: [1, 3, 7, 15, 30])


NAUKRI = NaukriConstants()
