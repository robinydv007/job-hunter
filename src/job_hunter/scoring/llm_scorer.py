"""LLM-based job scoring module."""

from __future__ import annotations

import json
import re
from typing import Any

from job_hunter.config import AppConfig
from job_hunter.graph.state import JobListing, ScoredJob
from job_hunter.llm.provider import get_llm
from job_hunter.resume.schema import ResumeProfile


def _build_job_for_llm(job: JobListing) -> dict[str, Any]:
    """Build a minimal job dict for LLM (exclude link, posted_date, data_source, job_board, job_url)."""
    return {
        "job_id": job.get("job_id", ""),
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "location": job.get("location", ""),
        "work_mode": job.get("work_mode", ""),
        "experience_required": job.get("experience_required", ""),
        "salary_lpa": job.get("salary_lpa", ""),
        "description": job.get("description", ""),
        "required_skills": job.get("required_skills", []),
        "company_rating": job.get("company_rating", ""),
        "review_count": job.get("review_count", ""),
        "industry": job.get("industry", ""),
        "department": job.get("department", ""),
    }


def _build_prompt(
    profile: ResumeProfile,
    jobs: list[dict[str, Any]],
    llm_config: AppConfig.scoring.llm_scoring,
    config: AppConfig,
) -> str:
    """Build the LLM prompt for scoring jobs."""

    skills = ", ".join(profile.skills + profile.tech_stack)
    preferred_roles = (
        ", ".join(config.profile.preferred_roles)
        if config.profile.preferred_roles
        else "Not specified"
    )
    past_roles = (
        ", ".join(profile.past_roles) if profile.past_roles else "Not specified"
    )

    preferred_locations = (
        ", ".join(profile.preferred_locations)
        if profile.preferred_locations
        else "Not specified"
    )
    remote_preference = (
        config.profile.remote_preference
        if config.profile.remote_preference
        else "Not specified"
    )

    conditional_criteria = []
    if llm_config.consider_location:
        conditional_criteria.append(
            "8. **Location Match**: Does job location align with candidate's preferred locations?"
        )
    if llm_config.consider_work_mode:
        conditional_criteria.append(
            "9. **Work Mode Match**: Does job's remote/hybrid/onsite align with candidate's preference?"
        )

    conditional_section = (
        "\n".join(conditional_criteria)
        if conditional_criteria
        else "None (only core factors considered)"
    )

    prompt = f"""You are a job matching expert. Score each job against the candidate profile.

## Candidate Profile
- Name: {profile.name}
- Total Experience: {profile.total_experience_years} years
- Skills: {skills}
- Preferred Roles: {preferred_roles}
- Past Roles: {past_roles}
- Industry Domain: {profile.industry_domain}
- Preferred Locations: {preferred_locations}
- Remote Preference: {remote_preference}

## Jobs to Score
{json.dumps(jobs, indent=2)}

## Scoring Criteria

### ALWAYS CONSIDER:
1. **Skills Match**: Does the job require technical skills that the candidate possesses?
2. **Role Alignment**: Does the job title align with the candidate's target or past roles?
3. **Experience Fit**: Does the job's experience requirement match the candidate's experience?
4. **Company Rating**: Company rating (if available) - higher is better
5. **Company Reviews**: Number of reviews indicates company size/stability
6. **Industry Match**: Does the job's industry align with candidate's industry domain?
7. **Department Match**: Does the job's department/team align with candidate's background?

### CONDITIONAL (based on user config):
{conditional_section}

## Output Format

Return ONLY a valid JSON object (no markdown, no explanation), with the following structure:
{{
  "scores": [
    {{
      "job_id": "unique_identifier_from_job",
      "title": "Job Title",
      "company": "Company Name",
      "score": 85,
      "reasoning": "Brief explanation covering key factors"
    }},
    ...
  ]
}}

Score must be an integer from 0-100. Provide clear reasoning for each score. Be consistent and fair in evaluation across all jobs."""

    return prompt


def _parse_llm_response(response_content: str) -> list[dict[str, Any]]:
    """Parse LLM JSON response, handling potential markdown formatting."""
    try:
        json_str = response_content.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()

        data = json.loads(json_str)
        return data.get("scores", [])
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[WARN] Failed to parse LLM response as JSON: {e}")
        scores_match = re.findall(
            r'"job_id":\s*"([^"]+)".*?"title":\s*"([^"]+)".*?"company":\s*"([^"]+)".*?"score":\s*(\d+).*?"reasoning":\s*"([^"]+)"',
            response_content,
            re.DOTALL,
        )
        if scores_match:
            return [
                {
                    "job_id": m[0],
                    "title": m[1],
                    "company": m[2],
                    "score": int(m[3]),
                    "reasoning": m[4].strip(),
                }
                for m in scores_match
            ]
        raise ValueError("Could not parse LLM response as JSON")


async def score_jobs_with_llm(
    jobs: list[JobListing],
    profile: ResumeProfile,
    config: AppConfig,
) -> list[ScoredJob]:
    """Score jobs using LLM in batches."""
    llm_config = config.scoring.llm_scoring
    if not llm_config or not llm_config.enabled:
        raise ValueError("LLM scoring is not enabled")

    batch_size = llm_config.batch_size or 10
    all_results: list[ScoredJob] = []

    job_dict = {job.get("job_id", job.get("title", "")): job for job in jobs}

    batches = [jobs[i : i + batch_size] for i in range(0, len(jobs), batch_size)]
    print(f"[INFO] Scoring {len(jobs)} jobs in {len(batches)} batches of {batch_size}")

    provider = get_llm()

    for idx, batch in enumerate(batches):
        print(f"[INFO] Processing batch {idx + 1}/{len(batches)} ({len(batch)} jobs)")

        jobs_for_llm = [_build_job_for_llm(job) for job in batch]
        prompt = _build_prompt(profile, jobs_for_llm, llm_config, config)

        try:
            response = await provider.ainvoke(prompt)
            response_content = (
                response.content if hasattr(response, "content") else str(response)
            )

            scores = _parse_llm_response(response_content)

            for score_entry in scores:
                job_id = score_entry.get("job_id", "")
                matched_job = job_dict.get(job_id)

                if not matched_job:
                    for job in batch:
                        if job.get("title") == score_entry.get("title"):
                            matched_job = job
                            break

                if matched_job:
                    scored: ScoredJob = {
                        "job": JobListing(**matched_job)
                        if isinstance(matched_job, dict)
                        else matched_job,
                        "match_score": max(0, min(100, score_entry.get("score", 0))),
                        "matched_skills": [],
                        "why_selected": score_entry.get("reasoning", ""),
                        "apply_status": (
                            "Pending"
                            if score_entry.get("score", 0)
                            >= llm_config.shortlist_threshold
                            else "Skipped"
                        ),
                    }
                    all_results.append(scored)
                else:
                    print(
                        f"[WARN] Could not match scored job: {score_entry.get('title')}"
                    )

        except Exception as e:
            print(f"[ERROR] LLM scoring failed for batch {idx + 1}: {e}")
            raise

    return all_results


def score_jobs_with_llm_sync(
    jobs: list[JobListing],
    profile: ResumeProfile,
    config: AppConfig,
) -> list[ScoredJob]:
    """Synchronous wrapper for score_jobs_with_llm."""
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()
    return asyncio.run(score_jobs_with_llm(jobs, profile, config))
