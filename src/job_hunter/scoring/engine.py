"""Job relevance scoring engine with weighted rubric (v2).

Scoring dimensions and weights:
  Skills Match      35%  — word-boundary + alias matching against required_skills
  Role Alignment    20%  — fuzzy role match with seniority awareness
  Experience Fit    20%  — years match with graceful penalty curves
  Company Quality   10%  — rating + review count as confidence signal
  Preferred Location  8%  — city/metro match against preferred_locations
  Work Mode          7%  — hybrid/remote/onsite preference matching
"""

from __future__ import annotations

import re
from typing import Any

from job_hunter.config import AppConfig
from job_hunter.resume.schema import ResumeProfile
from job_hunter.graph.state import JobListing, ScoredJob

SKILL_WEIGHT = 0.35
ROLE_WEIGHT = 0.20
EXPERIENCE_WEIGHT = 0.20
COMPANY_WEIGHT = 0.10
LOCATION_WEIGHT = 0.08
WORK_MODE_WEIGHT = 0.07

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

SKILL_ALIASES: dict[str, list[str]] = {
    "node.js": ["nodejs", "node js", "node"],
    "typescript": ["ts", "type script"],
    "javascript": ["js", "java script", "ecmascript"],
    "postgresql": ["postgres", "psql"],
    "mongodb": ["mongo db", "mongo"],
    "express": ["express.js", "expressjs"],
    "nestjs": ["nest js", "nest.js"],
    "react": ["react.js", "reactjs", "react.js"],
    "angular": ["angular.js", "angularjs"],
    "aws": ["amazon web services"],
    "gcp": ["google cloud platform", "google cloud"],
    "kafka": ["apache kafka"],
    "redis": ["redis cache"],
    "python": ["py"],
    "fastapi": ["fast api"],
    "laravel": ["laravel php"],
    "php": ["php laravel"],
    "rabbitmq": ["rabbit mq"],
    "microservices": ["micro services"],
    "ci/cd": [
        "cicd",
        "ci cd",
        "continuous integration",
        "continuous delivery",
        "continuous deployment",
    ],
    "system design": ["distributed systems", "scalable architecture"],
    "observability": ["monitoring", "logging", "tracing"],
}

_TITLE_STOP_WORDS = {
    "senior",
    "junior",
    "lead",
    "head",
    "principal",
    "staff",
    "associate",
    "manager",
    "director",
    "engineer",
    "developer",
    "architect",
    "analyst",
    "consultant",
    "specialist",
    "expert",
    "intern",
    "trainee",
    "fresher",
    "at",
    "for",
    "the",
    "and",
    "or",
    "of",
    "in",
    "a",
    "with",
    "to",
}


def _normalize(text: str) -> set[str]:
    return set(t.strip().lower() for t in text.replace(",", " ").split() if t.strip())


def _build_skill_alias_map() -> dict[str, str]:
    alias_to_canonical: dict[str, str] = {}
    for canonical, aliases in SKILL_ALIASES.items():
        alias_to_canonical[canonical.lower()] = canonical.lower()
        for alias in aliases:
            alias_to_canonical[alias.lower()] = canonical.lower()
    return alias_to_canonical


def _resolve_skill(skill: str, alias_map: dict[str, str]) -> str:
    return alias_map.get(skill.lower().strip(), skill.lower().strip())


def _word_boundary_match(skill: str, text: str) -> bool:
    escaped = re.escape(skill)
    pattern = r"\b" + escaped + r"\b"
    return bool(re.search(pattern, text, re.IGNORECASE))


def _split_concatenated_skills(skills: list[str]) -> list[str]:
    """Split concatenated skills like 'LLMMachine Learning' into separate skills.

    Only splits when the result produces meaningful tech skill tokens.
    Preserves common compound names like TypeScript, MongoDB, Node.js.
    """
    preserved = {
        "typescript",
        "javascript",
        "mongodb",
        "redis",
        "nodejs",
        "nestjs",
        "expressjs",
        "reactjs",
        "angularjs",
        "vuejs",
        "nextjs",
        "nuxtjs",
        "tailwindcss",
        "bootstrap",
        "postgresql",
        "mysql",
        "mariadb",
        "elasticsearch",
        "kubernetes",
        "docker",
    }

    known_skill_starts = {
        "llm",
        "ml",
        "ai",
        "gen",
        "deep",
        "machine",
        "natural",
        "computer",
        "data",
        "big",
        "cloud",
        "dev",
        "sys",
        "net",
        "web",
        "mobile",
        "ios",
        "android",
        "block",
        "crypto",
    }

    split_skills = []
    for skill in skills:
        skill_lower = skill.lower().replace(".", "").replace(" ", "").replace("-", "")
        if skill_lower in preserved or len(skill) < 8:
            split_skills.append(skill)
            continue

        parts = re.split(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", skill)
        if len(parts) > 1:
            first_part = parts[0].strip().lower().replace(".", "").replace(" ", "")
            if first_part in known_skill_starts and len(parts) > 1:
                split_skills.extend([p.strip() for p in parts if p.strip()])
            else:
                split_skills.append(skill)
        else:
            split_skills.append(skill)
    return split_skills


def _score_skills(job: dict, profile: ResumeProfile) -> tuple[int, list[str]]:
    """Score skills with alias resolution and word-boundary matching.

    Handles concatenated skills like "LLMMachine Learning" by splitting
    on camelCase boundaries.
    """
    alias_map = _build_skill_alias_map()

    all_user_skills = [s.lower().strip() for s in profile.skills + profile.tech_stack]
    user_tech_skills = set(s for s in all_user_skills if s not in NON_TECHNICAL_SKILLS)

    user_canonical = {_resolve_skill(s, alias_map) for s in user_tech_skills}

    job_required = job.get("required_skills", [])
    if not job_required:
        return 50, []

    job_required = _split_concatenated_skills(job_required)

    job_skills_raw = []
    for s in job_required:
        s_lower = s.lower().strip()
        if s_lower in NON_TECHNICAL_SKILLS:
            continue
        job_skills_raw.append(s_lower)

    if not job_skills_raw:
        return 50, []

    matched = []
    matched_canonical = set()

    for req in job_skills_raw:
        req_canonical = _resolve_skill(req, alias_map)

        if req_canonical in user_canonical and req_canonical not in matched_canonical:
            matched.append(req)
            matched_canonical.add(req_canonical)
            continue

        for user_skill in user_tech_skills:
            if len(req) > 3 and len(user_skill) > 3:
                skip_pairs = {
                    ("java", "javascript"),
                    ("js", "javascript"),
                    ("py", "python"),
                    ("c", "c++"),
                    ("c#", "c++"),
                }
                pair = tuple(sorted([req[:4], user_skill[:4]]))
                if pair in skip_pairs:
                    continue
                if req in user_skill or user_skill in req:
                    canon = _resolve_skill(user_skill, alias_map)
                    if canon not in matched_canonical:
                        matched.append(req)
                        matched_canonical.add(canon)
                        break

    if not matched:
        job_text = (job.get("title", "") + " " + job.get("description", "")).lower()
        for user_skill in user_tech_skills:
            if _word_boundary_match(user_skill, job_text):
                canon = _resolve_skill(user_skill, alias_map)
                if canon not in matched_canonical:
                    matched.append(user_skill)
                    matched_canonical.add(canon)

    total = len(job_skills_raw)
    if total == 0:
        return 50, []

    return min(int((len(matched) / total) * 100), 100), matched


def _score_experience(job: dict, profile: ResumeProfile) -> int:
    exp_required = job.get("experience_required", "")
    if not exp_required:
        return 50

    nums = re.findall(r"(\d+)", exp_required)
    if not nums:
        return 50

    min_exp = int(nums[0])
    max_exp = int(nums[1]) if len(nums) > 1 else min_exp + 2
    user_exp = int(profile.total_experience_years)

    if min_exp <= user_exp <= max_exp:
        return 100

    if user_exp > max_exp:
        over = user_exp - max_exp
        if over <= 2:
            return 90
        elif over <= 4:
            return 75
        elif over <= 6:
            return 55
        else:
            return max(0, 40 - (over - 6) * 8)

    under = min_exp - user_exp
    if under <= 1:
        return 70
    elif under <= 2:
        return 50
    elif under <= 3:
        return 30
    else:
        return max(0, 20 - (under - 3) * 10)


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

    role_words_map = {}
    for role in all_roles:
        role_words_map[role] = _normalize(role)

    job_words = _normalize(job_title)
    best_overlap = 0
    for role, role_words in role_words_map.items():
        overlap = job_words & role_words
        if overlap:
            ratio = len(overlap) / max(len(role_words), len(job_words))
            best_overlap = max(best_overlap, ratio)

    if best_overlap >= 0.5:
        return 80
    elif best_overlap >= 0.3:
        return 60
    elif best_overlap > 0:
        return 40

    return 20


def _score_company(job: dict) -> int:
    """Score company quality based on rating and review count.

    Rating is the primary signal. Review count boosts confidence.
    """
    rating_str = job.get("company_rating", "")
    review_str = job.get("review_count", "")

    if not rating_str:
        return 50

    try:
        rating = float(rating_str)
    except (ValueError, TypeError):
        return 50

    if rating >= 4.5:
        base = 100
    elif rating >= 4.0:
        base = 90
    elif rating >= 3.5:
        base = 75
    elif rating >= 3.0:
        base = 60
    elif rating >= 2.5:
        base = 40
    else:
        base = 20

    if review_str:
        try:
            reviews = int(review_str.replace(",", ""))
            if reviews >= 10000:
                base = min(base + 10, 100)
            elif reviews >= 1000:
                base = min(base + 5, 100)
        except (ValueError, TypeError):
            pass

    return base


def _score_location(job: dict, profile: ResumeProfile) -> int:
    """Score based on preferred location matching.

    Uses profile's location_preference and preferred_locations to match
    against job's location string.
    """
    job_loc = job.get("location", "").lower()
    if not job_loc:
        return 50

    pref_locations = [loc.lower().strip() for loc in profile.preferred_locations if loc]
    loc_preference = (
        profile.location_preference.strip().lower()
        if profile.location_preference
        else ""
    )
    if loc_preference and loc_preference not in pref_locations:
        pref_locations.append(loc_preference)

    if not pref_locations:
        return 60

    metro_cities = {
        "bangalore": ["bengaluru", "bangalore"],
        "delhi": ["delhi", "ncr", "gurgaon", "gurugram", "noida", "faridabad"],
        "mumbai": ["mumbai", "bombay", "navi mumbai", "thane", "pune"],
        "hyderabad": ["hyderabad", "secunderabad"],
        "chennai": ["chennai", "madras"],
        "pune": ["pune"],
        "kolkata": ["kolkata", "calcutta"],
        "bangalore": ["bengaluru", "bangalore"],
    }

    def _city_match(loc: str) -> tuple[bool, bool]:
        for metro, aliases in metro_cities.items():
            for alias in aliases:
                if alias in loc:
                    return True, metro
        return False, ""

    job_is_metro, job_metro = _city_match(job_loc)

    for pref in pref_locations:
        pref_is_metro, pref_metro = _city_match(pref)
        if pref in job_loc or job_loc in pref:
            return 100
        if job_is_metro and pref_is_metro and job_metro == pref_metro:
            return 90
        if any(p in job_loc for p in pref.split()):
            return 70

    return 30


def _score_work_mode(job: dict, config: AppConfig) -> int:
    """Score based on work mode preference matching."""
    work_mode = job.get("work_mode", "").lower()
    preference = (
        config.profile.remote_preference.lower()
        if config.profile.remote_preference
        else ""
    )
    location = job.get("location", "").lower()

    if not preference:
        return 60

    if "hybrid" in preference:
        if "hybrid" in work_mode or "hybrid" in location:
            return 100
        if "remote" in work_mode or "remote" in location:
            return 80
        if "onsite" in work_mode or "office" in location:
            return 50
        return 60

    if "remote" in preference:
        if (
            "remote" in work_mode
            or "remote" in location
            or "work from home" in location
        ):
            return 100
        if "hybrid" in work_mode or "hybrid" in location:
            return 70
        return 30

    if "onsite" in preference:
        if "onsite" in work_mode or "office" in location:
            return 100
        if "hybrid" in work_mode or "hybrid" in location:
            return 70
        return 40

    return 60


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
        f"- Experience: requires {exp_str}, user has {profile.total_experience_years}y (score: {scores['experience']}%)"
    )

    lines.append(f"- Role: {job.get('title', 'Unknown')} (match: {scores['role']}%)")

    company_rating = job.get("company_rating", "")
    review_count = job.get("review_count", "")
    if company_rating:
        review_info = f"{review_count} reviews" if review_count else ""
        lines.append(
            f"- Company: {job.get('company', 'Unknown')} ({company_rating}/5 {review_info})"
        )

    loc = job.get("location", "unknown")
    work_mode = job.get("work_mode", "")
    mode_str = f" ({work_mode})" if work_mode else ""
    lines.append(f"- Location: {loc}{mode_str} (score: {scores['location']}%)")

    sal = job.get("salary_lpa", "not disclosed")
    lines.append(f"- Salary: {sal}")

    return "\n".join(lines)


def score_job(job: dict, profile: ResumeProfile, config: AppConfig) -> ScoredJob:
    """Score a single job against the user profile using v2 rubric."""
    title = job.get("title", "").lower()
    exclude_keywords = (
        config.search.title_exclude_keywords
        if config.search.title_exclude_keywords
        else []
    )
    for kw in exclude_keywords:
        if re.search(r"\b" + re.escape(kw.lower()) + r"\b", title):
            return _create_zero_score_job(job, config)

    s_skills, matched_skills = _score_skills(job, profile)
    s_role = _score_role(job, profile)
    s_exp = _score_experience(job, profile)
    s_company = _score_company(job)
    s_location = _score_location(job, profile)
    s_work_mode = _score_work_mode(job, config)

    composite = int(
        s_skills * SKILL_WEIGHT
        + s_role * ROLE_WEIGHT
        + s_exp * EXPERIENCE_WEIGHT
        + s_company * COMPANY_WEIGHT
        + s_location * LOCATION_WEIGHT
        + s_work_mode * WORK_MODE_WEIGHT
    )

    composite = max(0, min(composite, 100))

    scores = {
        "skills": s_skills,
        "role": s_role,
        "experience": s_exp,
        "company": s_company,
        "location": s_location,
        "work_mode": s_work_mode,
    }

    why = _generate_explanation(scores, matched_skills, job, profile)

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


def _create_zero_score_job(job: dict, config: AppConfig) -> ScoredJob:
    """Create a zero-score job result for excluded positions."""
    result: ScoredJob = {
        "job": JobListing(**job) if isinstance(job, dict) else job,
        "match_score": 0,
        "matched_skills": [],
        "why_selected": f"- Title contains excluded keyword: {job.get('title', '')}",
        "apply_status": "Skipped",
    }
    return result
