"""LLM-based resume parser with Pydantic validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from job_hunter.llm.provider import get_llm
from job_hunter.resume.schema import ResumeProfile

RESUME_FULL_PROMPT = """You are an expert resume parser. Extract ALL information from this resume.

Return ONLY a valid JSON object with TWO sections: "basic" and "detailed". Do NOT include any explanation or markdown.

BASIC SECTION:
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

DETAILED SECTION:
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


def get_profile_cache_path() -> Path:
    """Get the profile cache file path."""
    return get_data_dir() / "profile_cache.json"


def save_profile_cache(data: dict) -> None:
    """Save merged profile (basic + detailed) to single JSON file."""
    cache_path = get_profile_cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)


def load_profile_cache() -> dict | None:
    """Load merged profile cache from single JSON file."""
    cache_path = get_profile_cache_path()
    if not cache_path.exists():
        return None
    with open(cache_path) as f:
        return json.load(f)


def load_profile_from_cache() -> tuple[ResumeProfile | None, dict | None]:
    """Load profile from cache. Returns tuple of (ResumeProfile, detailed_dict)."""
    cached = load_profile_cache()
    if not cached:
        return None, None
    basic_data = {k: v for k, v in cached.items() if k != "detailed"}
    profile = ResumeProfile(**basic_data)
    detailed = cached.get("detailed", {})
    return profile, detailed


async def parse_resume_full(
    file_path: str | Path,
    force: bool = False,
) -> tuple[ResumeProfile, dict]:
    """Parse resume and extract both basic + detailed profile in a single LLM call.

    Returns:
        tuple of (ResumeProfile, detailed_dict)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    current_hash = get_file_hash(file_path)
    cache_path = get_profile_cache_path()

    hash_file = get_data_dir() / "resume_hash.txt"
    stored_hash = None
    if hash_file.exists():
        stored_hash = hash_file.read_text().strip()

    if not force and stored_hash == current_hash and cache_path.exists():
        cached = load_profile_cache()
        if cached:
            basic_data = cached.get("basic", {})
            if not basic_data:
                basic_data = {k: v for k, v in cached.items() if k != "detailed"}
            profile = ResumeProfile(**basic_data)
            detailed = cached.get("detailed", {})
            return profile, detailed

    resume_text = extract_text_from_file(file_path)

    llm = get_llm()
    response = await llm.ainvoke(RESUME_FULL_PROMPT.format(resume_text=resume_text))
    content = response.content if hasattr(response, "content") else str(response)

    if isinstance(content, list):
        content = " ".join(str(c) for c in content)
    content = str(content).strip()

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

    basic_data = data.get("basic", data)

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
    detailed_data = data.get("detailed", {})

    merged_cache = {**basic_data, "detailed": detailed_data}
    save_profile_cache(merged_cache)

    hash_file.parent.mkdir(parents=True, exist_ok=True)
    hash_file.write_text(current_hash)

    return profile, detailed_data


async def parse_resume(
    file_path: str | Path, profile_path: str | Path | None = None
) -> ResumeProfile:
    """Parse a resume file and return a structured profile."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    profile, _ = await parse_resume_full(file_path)
    return profile