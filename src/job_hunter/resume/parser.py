"""LLM-based resume parser with Pydantic validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from job_hunter.llm.provider import get_llm
from job_hunter.resume.schema import ResumeProfile

RESUME_PARSE_PROMPT = """You are an expert resume parser. Extract structured information from the following resume text.

Return ONLY a valid JSON object matching this schema. Use empty strings or empty arrays for missing fields. Do NOT include any explanation or markdown.

Required fields:
- name: Full name
- email: Email address
- phone: Phone number
- skills: List of all skills/technologies mentioned
- tech_stack: List of programming languages, frameworks, tools (subset of skills)
- total_experience_years: Total years of experience as a number
- past_roles: List of job titles/roles held
- industry_domain: Primary industry (e.g. "SaaS", "Fintech", "E-commerce")
- location_preference: Preferred work location if mentioned
- salary_expectation: Expected salary if mentioned
- target_roles: Inferred target job titles based on experience
- education: List of degrees/certifications
- summary: 2-3 sentence professional summary

Resume text:
{resume_text}
"""

RESUME_FULL_PROMPT = """You are an expert resume parser. Extract ALL information from this resume.

Return ONLY a valid JSON object with TWO sections: "basic" and "detailed". Do NOT include any explanation or markdown.

BASIC SECTION (for profile.json - same as before):
- name: Full name
- email: Email address
- phone: Phone number
- skills: List of all skills/technologies mentioned
- tech_stack: List of programming languages, frameworks, tools
- total_experience_years: Total years of experience as a number
- past_roles: List of job titles/roles held
- industry_domain: Primary industry
- location_preference: Preferred work location if mentioned
- salary_expectation: Expected salary if mentioned
- target_roles: Inferred target job titles based on experience
- education: List of degrees/certifications
- summary: 2-3 sentence professional summary

DETAILED SECTION (for profile_detailed.yaml):
- tech_experience: Dictionary mapping technology to years of experience (e.g. {{"Python": 5, "AWS": 2, "React": 3}})
- achievements: List of 3-5 notable achievements (quantify where possible)
- challenges_solved: List of technical challenges overcome
- interests: List of professional interests
- key_responsibilities: List of main responsibilities from past roles

Resume text:
{resume_text}

Output as valid JSON with keys "basic" and "detailed":"""


def extract_text_from_file(file_path: str | Path) -> str:
    """Extract text from PDF, DOCX, or TXT resume files."""
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8")

    elif suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    elif suffix == ".docx":
        from docx import Document

        doc = Document(str(file_path))
        return "\n".join(p.text for p in doc.paragraphs)

    else:
        raise ValueError(f"Unsupported file type: {suffix}. Use .pdf, .docx, or .txt")


async def parse_resume(
    file_path: str | Path, profile_path: str | Path | None = None
) -> ResumeProfile:
    """Parse a resume file and return a structured profile."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    resume_text = extract_text_from_file(file_path)

    llm = get_llm()
    response = await llm.ainvoke(RESUME_PARSE_PROMPT.format(resume_text=resume_text))
    content = response.content if hasattr(response, "content") else str(response)

    # Ensure content is a string
    if isinstance(content, list):
        content = " ".join(str(c) for c in content)
    content = str(content).strip()

    # Clean markdown code blocks if present
    if content.startswith("```"):
        lines = content.split("\n")
        if len(lines) > 1:
            content = "\n".join(lines[1:])
        if "```" in content:
            content = content.rsplit("```", 1)[0]
        content = content.strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse LLM response as JSON: {e}\nResponse: {content[:500]}"
        )

    profile = ResumeProfile(**data)

    # Persist to profile_path if provided
    if profile_path is None:
        profile_path = Path(__file__).resolve().parents[3] / "data" / "profile.json"
    profile_path = Path(profile_path)
    profile_path.parent.mkdir(parents=True, exist_ok=True)

    with open(profile_path, "w") as f:
        json.dump(profile.model_dump(), f, indent=2)

    return profile


def load_profile(profile_path: str | Path | None = None) -> ResumeProfile | None:
    """Load a previously parsed profile if it exists."""
    if profile_path is None:
        profile_path = Path(__file__).resolve().parents[3] / "data" / "profile.json"
    profile_path = Path(profile_path)

    if not profile_path.exists():
        return None

    with open(profile_path) as f:
        data = json.load(f)
    return ResumeProfile(**data)


def get_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file for change detection."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_data_dir() -> Path:
    """Get the data directory path."""
    return Path(__file__).resolve().parents[3] / "data"


async def parse_resume_full(
    file_path: str | Path,
    profile_path: str | Path | None = None,
    detailed_path: str | Path | None = None,
) -> tuple[ResumeProfile, dict]:
    """Parse resume and extract both basic + detailed profile in a single LLM call.

    Returns:
        tuple of (ResumeProfile, detailed_dict)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    # Calculate current resume hash
    current_hash = get_file_hash(file_path)

    # Check if we should regenerate (resume changed or no cache)
    if profile_path is None:
        profile_path = get_data_dir() / "profile.json"
    if detailed_path is None:
        detailed_path = get_data_dir() / "profile_detailed.yaml"

    profile_path = Path(profile_path)
    detailed_path = Path(detailed_path)

    # Load stored hash if exists
    hash_file = get_data_dir() / "resume_hash.txt"
    stored_hash = None
    if hash_file.exists():
        stored_hash = hash_file.read_text().strip()

    # Check if cache exists and resume hasn't changed
    if stored_hash == current_hash and profile_path.exists() and detailed_path.exists():
        # Load from cache
        profile = load_profile(profile_path)
        detailed = load_detailed_profile(detailed_path)
        if profile and detailed:
            return profile, detailed

    # Need to regenerate - extract full profile
    resume_text = extract_text_from_file(file_path)

    llm = get_llm()
    response = await llm.ainvoke(RESUME_FULL_PROMPT.format(resume_text=resume_text))
    content = response.content if hasattr(response, "content") else str(response)

    if isinstance(content, list):
        content = " ".join(str(c) for c in content)
    content = str(content).strip()

    # Clean markdown code blocks
    if content.startswith("```"):
        lines = content.split("\n")
        if len(lines) > 1:
            content = "\n".join(lines[1:])
        if "```" in content:
            content = content.rsplit("```", 1)[0]
        content = content.strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse LLM response as JSON: {e}\nResponse: {content[:500]}"
        )

    # Parse basic profile
    basic_data = data.get("basic", data)  # Fallback to full data if no "basic" key

    # Clean None values - convert to empty strings for string fields
    for field in [
        "name",
        "email",
        "phone",
        "industry_domain",
        "location_preference",
        "salary_expectation",
        "summary",
    ]:
        if basic_data.get(field) is None:
            basic_data[field] = ""

    for field in ["skills", "tech_stack", "past_roles", "target_roles", "education"]:
        if basic_data.get(field) is None:
            basic_data[field] = []

    if basic_data.get("total_experience_years") is None:
        basic_data["total_experience_years"] = 0

    if basic_data.get("preferred_locations") is None:
        basic_data["preferred_locations"] = []

    profile = ResumeProfile(**basic_data)

    # Parse detailed profile
    detailed_data = data.get("detailed", {})

    # Save both profiles
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    with open(profile_path, "w") as f:
        json.dump(profile.model_dump(), f, indent=2)

    save_detailed_profile(detailed_data, detailed_path)

    # Save resume hash
    hash_file.parent.mkdir(parents=True, exist_ok=True)
    hash_file.write_text(current_hash)

    return profile, detailed_data


def save_detailed_profile(
    detailed_data: dict, detailed_path: str | Path | None = None
) -> None:
    """Save detailed profile to YAML file."""
    if detailed_path is None:
        detailed_path = get_data_dir() / "profile_detailed.yaml"
    detailed_path = Path(detailed_path)
    detailed_path.parent.mkdir(parents=True, exist_ok=True)

    with open(detailed_path, "w") as f:
        yaml.dump(detailed_data, f, default_flow_style=False, sort_keys=False)


def load_detailed_profile(detailed_path: str | Path | None = None) -> dict | None:
    """Load detailed profile from YAML file."""
    if detailed_path is None:
        detailed_path = get_data_dir() / "profile_detailed.yaml"
    detailed_path = Path(detailed_path)

    if not detailed_path.exists():
        return None

    with open(detailed_path) as f:
        return yaml.safe_load(f) or {}


def load_profile_with_detailed() -> tuple[ResumeProfile | None, dict | None]:
    """Load both basic profile and detailed profile together.

    Returns:
        tuple of (ResumeProfile, detailed_dict) - both can be None if not found
    """
    profile = load_profile()
    detailed = load_detailed_profile()
    return profile, detailed
