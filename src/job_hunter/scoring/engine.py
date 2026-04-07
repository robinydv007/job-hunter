"""Job relevance scoring engine — zero static data.

All domain knowledge comes from Constants (config/constants.yaml).
All user preferences come from AppConfig (config/user.yaml).
"""

from __future__ import annotations

import re

from job_hunter.config import AppConfig
from job_hunter.config.constants import Constants
from job_hunter.graph.state import JobListing, ScoredJob
from job_hunter.resume.schema import ResumeProfile


def _normalize(text: str) -> set[str]:
    return set(t.strip().lower() for t in text.replace(",", " ").split() if t.strip())


def _build_alias_map(constants: Constants) -> dict[str, str]:
    alias_to_canonical: dict[str, str] = {}
    for canonical, aliases in constants.skill_aliases.items():
        alias_to_canonical[canonical.lower()] = canonical.lower()
        for alias in aliases:
            alias_to_canonical[alias.lower()] = canonical.lower()
    return alias_to_canonical


def _resolve_skill(skill: str, alias_map: dict[str, str]) -> str:
    return alias_map.get(skill.lower().strip(), skill.lower().strip())


def _score_skills(
    job: dict, profile: ResumeProfile, constants: Constants
) -> tuple[int, list[str]]:
    alias_map = _build_alias_map(constants)

    all_user_skills = [s.lower().strip() for s in profile.skills + profile.tech_stack]
    user_canonical = {_resolve_skill(s, alias_map) for s in all_user_skills}

    job_required = job.get("required_skills", [])
    if not job_required:
        return 50, []

    job_skills_raw = [s.lower().strip() for s in job_required if s.strip()]
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

        for user_skill in all_user_skills:
            if len(req) > 3 and len(user_skill) > 3:
                if (
                    req[:2].lower() == user_skill[:2].lower()
                    and abs(len(req) - len(user_skill)) <= 2
                ):
                    continue
                if req in user_skill or user_skill in req:
                    canon = _resolve_skill(user_skill, alias_map)
                    if canon not in matched_canonical:
                        matched.append(req)
                        matched_canonical.add(canon)
                        break

    total = len(job_skills_raw)
    if total == 0:
        return 50, []

    return min(int((len(matched) / total) * 100), 100), matched


def _score_experience(job: dict, profile: ResumeProfile, constants: Constants) -> int:
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

    penalties = constants.experience_penalties

    if user_exp > max_exp:
        over = user_exp - max_exp
        over_map = penalties.get("over", {})
        int_keys = [k for k in over_map.keys() if isinstance(k, int)]
        for threshold in sorted(int_keys):
            if over <= threshold:
                return over_map[threshold]
        return max(0, 40 - (over - 6) * 8)

    under = min_exp - user_exp
    under_map = penalties.get("under", {})
    int_keys = [k for k in under_map.keys() if isinstance(k, int)]
    for threshold in sorted(int_keys):
        if under <= threshold:
            return under_map[threshold]
    return max(0, 20 - (under - 3) * 10)


def _score_role(
    job: dict, profile: ResumeProfile, config: AppConfig, constants: Constants
) -> int:
    job_title = job.get("title", "").lower()
    preferred_roles = (
        [r.lower() for r in config.profile.preferred_roles]
        if config.profile.preferred_roles
        else []
    )
    past_roles = [r.lower() for r in profile.past_roles]
    all_roles = preferred_roles + past_roles

    if not all_roles:
        return 50

    for role in all_roles:
        if role in job_title or job_title in role:
            return 100

    job_words = _normalize(job_title)
    best_overlap = 0.0
    for role in all_roles:
        role_words = _normalize(role)
        overlap = job_words & role_words
        if overlap:
            ratio = len(overlap) / max(len(role_words), len(job_words))
            best_overlap = max(best_overlap, ratio)

    thresholds = constants.role_overlap_thresholds
    for threshold in sorted(thresholds.keys(), reverse=True):
        if best_overlap >= threshold:
            return thresholds[threshold]

    return constants.role_overlap_default


def _score_company(job: dict, constants: Constants) -> int:
    rating_str = job.get("company_rating", "")
    review_str = job.get("review_count", "")

    if not rating_str:
        return 50

    try:
        rating = float(rating_str)
    except (ValueError, TypeError):
        return 50

    bands = constants.company_rating_bands
    base = constants.company_rating_default
    for threshold in sorted(bands.keys(), reverse=True):
        if rating >= threshold:
            base = bands[threshold]
            break

    if review_str:
        try:
            reviews = int(review_str.replace(",", ""))
            for threshold in sorted(constants.review_count_boosts.keys(), reverse=True):
                if reviews >= threshold:
                    base = min(base + constants.review_count_boosts[threshold], 100)
                    break
        except (ValueError, TypeError):
            pass

    return base


def _score_location(job: dict, profile: ResumeProfile, constants: Constants) -> int:
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

    metro_cities = constants.metro_cities

    def _city_match(loc: str) -> tuple[bool, str]:
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


def _score_work_mode(job: dict, config: AppConfig, constants: Constants) -> int:
    work_mode = job.get("work_mode", "").lower()
    preference = (
        config.profile.remote_preference.lower()
        if config.profile.remote_preference
        else ""
    )
    location = job.get("location", "").lower()

    if not preference:
        return constants.work_mode_scores.get("default", 60)

    mode_scores = constants.work_mode_scores.get(preference, {})
    if not mode_scores:
        return constants.work_mode_scores.get("default", 60)

    for check in ["remote", "hybrid", "onsite", "office", "work from home"]:
        if check in work_mode or check in location:
            normalized = "remote" if check in ("remote", "work from home") else check
            if normalized in mode_scores:
                return mode_scores[normalized]

    return mode_scores.get("default", constants.work_mode_scores.get("default", 60))


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


def score_job(
    job: dict, profile: ResumeProfile, config: AppConfig, constants: Constants
) -> ScoredJob:
    title = job.get("title", "").lower()
    exclude_keywords = config.search.title_exclude_keywords or []
    for kw in exclude_keywords:
        if re.search(r"\b" + re.escape(kw.lower()) + r"\b", title):
            return _create_zero_score_job(job, config)

    s_skills, matched_skills = _score_skills(job, profile, constants)
    s_role = _score_role(job, profile, config, constants)
    s_exp = _score_experience(job, profile, constants)
    s_company = _score_company(job, constants)
    s_location = _score_location(job, profile, constants)
    s_work_mode = _score_work_mode(job, config, constants)

    composite = int(
        s_skills * config.scoring.skill_weight
        + s_role * config.scoring.role_weight
        + s_exp * config.scoring.experience_weight
        + s_company * config.scoring.company_weight
        + s_location * config.scoring.location_weight
        + s_work_mode * config.scoring.work_mode_weight
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
    result: ScoredJob = {
        "job": JobListing(**job) if isinstance(job, dict) else job,
        "match_score": 0,
        "matched_skills": [],
        "why_selected": f"- Title contains excluded keyword: {job.get('title', '')}",
        "apply_status": "Skipped",
    }
    return result
