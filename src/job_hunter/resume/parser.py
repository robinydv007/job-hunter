"""LLM-based resume parser with Pydantic validation."""

from __future__ import annotations

import json
from pathlib import Path

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
