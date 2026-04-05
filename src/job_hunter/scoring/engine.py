"""Job relevance scoring engine with weighted rubric."""

from __future__ import annotations

from typing import Any

from job_hunter.config import AppConfig
from job_hunter.resume.schema import ResumeProfile
from job_hunter.graph.state import JobListing, ScoredJob

SKILL_WEIGHT = 0.30
EXPERIENCE_WEIGHT = 0.20
ROLE_WEIGHT = 0.20
KEYWORDS_WEIGHT = 0.15
SALARY_WEIGHT = 0.08
LOCATION_WEIGHT = 0.00


def _normalize(text: str) -> set[str]:
    return set(t.strip().lower() for t in text.replace(",", " ").split() if t.strip())


NON_TECHNICAL_SKILLS = {
    "team mentorship",
    "client communication",
    "sprint management",
    "roadmap planning",
    "hiring & performance reviews",
    "agile/scrum",
    "jira",
    "zoom",
    "git",
    "ui best practices",
    "reusable components",
    "frontend caching",
    "modular design",
    "sentry integration",
}

# Common role/seniority stop-words to ignore when computing title remainder
_TITLE_STOP_WORDS = {
    "senior", "junior", "lead", "head", "principal", "staff", "associate",
    "manager", "director", "engineer", "developer", "architect", "analyst",
    "consultant", "specialist", "expert", "intern", "trainee", "fresher",
    "at", "for", "the", "and", "or", "of", "in", "a"
}


def _title_remainder_bonus(job: dict, profile: ResumeProfile) -> int:
    """Bonus points based on title words left after removing the search keyword.

    Strip the search_keyword words from the job title (case-insensitive).
    Remaining words = tech/domain modifier words the job is specialising in.

    Scoring:
      +20  if any remainder word matches a user skill  (good signal)
      +10  if no remainder words exist (title == search keyword → pure role match)
        0  if remainder exists but no skill match     (unfamiliar tech)
    """
    import re

    title = job.get("title", "").lower()
    keyword = job.get("search_keyword", "").lower()

    if not title:
        return 0

    # Tokenise both title and keyword into words
    title_words = set(re.findall(r"[a-z0-9#+.]+", title))
    keyword_words = set(re.findall(r"[a-z0-9#+.]+", keyword))

    # Remainder = title words minus keyword words minus generic stop-words
    remainder = title_words - keyword_words - _TITLE_STOP_WORDS

    if not remainder:
        # Title is essentially just the search keyword — clean role match
        return 10

    # Check if any remainder word appears in user's skills
    user_skills = {s.lower().strip() for s in profile.skills + profile.tech_stack}
    for word in remainder:
        # Exact match OR word is a substring of a skill (e.g. "node" in "node.js")
        if any(word == s or (len(word) > 2 and word in s) for s in user_skills):
            return 20

    # Remainder words exist but none match user skills — unfamiliar tech
    return 0


def _score_skills(job: dict, profile: ResumeProfile) -> tuple[int, list[str]]:
    """Score skills against extracted required_skills.

    When required_skills are available (Naukri row5 tags), match them directly.
    When not available, return neutral 50 — title-remainder bonus in score_job
    provides the directional signal instead.
    """
    import re

    all_user_skills = [s.lower().strip() for s in profile.skills + profile.tech_stack]
    user_tech_skills = set(s for s in all_user_skills if s not in NON_TECHNICAL_SKILLS)

    job_required = job.get("required_skills", [])
    if not job_required:
        # No extracted required_skills — use neutral; title-remainder handles signal
        return 50, []

    required_lower = [s.lower().strip() for s in job_required]
    required_tech = [s for s in required_lower if s not in NON_TECHNICAL_SKILLS]
    matched = []
    for s in required_tech:
        if s in user_tech_skills:
            matched.append(s)
        else:
            # Fuzzy: one contains the other, both > 3 chars, skip known false pairs
            skip_prefixes = {("java", "java"), ("js", "java"), ("py", "pyth"), ("c", "c++"), ("c#", "c++")}
            for u in user_tech_skills:
                if len(s) > 3 and len(u) > 3 and (s in u or u in s):
                    if tuple(sorted([s[:4], u[:4]])) not in skip_prefixes:
                        matched.append(s)
                        break

    total = len(required_tech) if required_tech else len(required_lower)
    if total == 0:
        return 50, []
    return min(int((len(matched) / total) * 100), 100), matched


def _score_experience(job: dict, profile: ResumeProfile) -> int:
    exp_required = job.get("experience_required", "")
    if not exp_required:
        return 50

    import re

    nums = re.findall(r"(\d+)", exp_required)
    if not nums:
        return 50

    min_exp = int(nums[0])
    max_exp = int(nums[1]) if len(nums) > 1 else min_exp + 2
    user_exp = int(profile.total_experience_years)

    if min_exp <= user_exp <= max_exp + 2:
        return 100
    elif user_exp < min_exp:
        return max(0, 100 - (min_exp - user_exp) * 20)
    else:
        return max(0, 100 - (user_exp - max_exp) * 10)


def _score_role(job: dict, profile: ResumeProfile) -> int:
    job_title = job.get("title", "").lower()
    target_roles = [r.lower() for r in profile.target_roles]
    past_roles = [r.lower() for r in profile.past_roles]
    all_roles = target_roles + past_roles

    if not all_roles:
        return 50

    for role in all_roles:
        if role in job_title or job_title in role:
            return 100

    job_words = _normalize(job_title)
    for role in all_roles:
        role_words = _normalize(role)
        overlap = job_words & role_words
        if overlap:
            return 70

    return 30


def _score_keywords(job: dict, profile: ResumeProfile) -> int:
    job_text = (
        job.get("title", "")
        + " "
        + job.get("description", "")
        + " "
        + job.get("company", "")
    ).lower()

    profile_text = " ".join(
        profile.skills + profile.tech_stack + profile.industry_domain.split()
    ).lower()

    profile_words = _normalize(profile_text)
    if not profile_words:
        return 50

    job_words = _normalize(job_text)
    overlap = profile_words & job_words
    return min(int((len(overlap) / len(profile_words)) * 100), 100)


def _score_salary(job: dict, profile: ResumeProfile, config: AppConfig) -> int:
    salary_str = job.get("salary_lpa", "")
    expected = config.profile.expected_salary_lpa
    if not salary_str or expected == 0:
        return 70

    import re

    nums = re.findall(r"([\d.]+)", salary_str)
    if not nums:
        return 70

    job_min = float(nums[0])
    if job_min >= expected:
        return 100
    elif job_min >= expected * 0.8:
        return 70
    else:
        return max(0, int((job_min / expected) * 50))


def _score_location(job: dict, profile: ResumeProfile, config: AppConfig) -> int:
    job_loc = job.get("location", "").lower()
    preferred = [loc.lower() for loc in profile.preferred_locations]

    if not preferred:
        return 70

    remote_pref = config.profile.remote_preference
    if remote_pref == "remote" and "remote" in job_loc.lower():
        return 100

    for loc in preferred:
        if loc in job_loc or job_loc in loc:
            return 100

    return 30


def _generate_explanation(
    scores: dict, matched_skills: list[str], job: dict, profile: ResumeProfile
) -> str:
    lines = []

    skill_pct = scores["skills"]
    lines.append(
        f"- Skills: {skill_pct}% match ({len(matched_skills)} aligned: {', '.join(matched_skills[:5])})"
    )

    exp_str = job.get("experience_required", "unknown")
    lines.append(
        f"- Experience: requires {exp_str}, user has {profile.total_experience_years}y"
    )

    lines.append(f"- Role: {job.get('title', 'Unknown')} (match: {scores['role']}%)")

    loc = job.get("location", "unknown")
    lines.append(f"- Location: {loc}")

    sal = job.get("salary_lpa", "not disclosed")
    lines.append(f"- Salary: {sal}")

    posted = job.get("posted_date", "")
    if posted:
        lines.append(f"- Posted: {posted}")

    return "\n".join(lines)


def score_job(job: dict, profile: ResumeProfile, config: AppConfig) -> ScoredJob:
    """Score a single job against the user profile."""
    s_skills, matched_skills = _score_skills(job, profile)
    s_exp = _score_experience(job, profile)
    s_role = _score_role(job, profile)
    s_keywords = _score_keywords(job, profile)
    s_salary = _score_salary(job, profile, config)
    s_location = _score_location(job, profile, config)

    composite = int(
        s_skills * SKILL_WEIGHT
        + s_exp * EXPERIENCE_WEIGHT
        + s_role * ROLE_WEIGHT
        + s_keywords * KEYWORDS_WEIGHT
        + s_salary * SALARY_WEIGHT
        + s_location * LOCATION_WEIGHT
    )

    # Title-remainder bonus: profile-driven, zero static keyword lists
    title_bonus = _title_remainder_bonus(job, profile)
    composite = min(composite + title_bonus, 100)

    scores = {
        "skills": s_skills,
        "experience": s_exp,
        "role": s_role,
        "keywords": s_keywords,
        "salary": s_salary,
        "location": s_location,
    }

    why = _generate_explanation(scores, matched_skills, job, profile)
    if title_bonus == 20:
        why += "\n- \u2705 Title modifier matches your skills (+20)"
    elif title_bonus == 10:
        why += "\n- \u2705 Title is a pure role match (+10)"
    elif title_bonus == 0 and job.get("search_keyword"):
        why += "\n- \u26a0\ufe0f Title modifier not found in your skills (+0)"

    apply_status = (
        "Pending" if composite >= config.scoring.apply_threshold else "Skipped"
    )

    result: ScoredJob = {
        "job": JobListing(**job) if isinstance(job, dict) else job,
        "match_score": composite,
        "matched_skills": matched_skills,
        "why_selected": why,
        "apply_status": apply_status,
    }
    return result
