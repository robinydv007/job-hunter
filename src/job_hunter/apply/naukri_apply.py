"""Naukri auto-apply orchestrator using APIs."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from playwright.async_api import Page

from job_hunter.apply import api

logger = logging.getLogger(__name__)


@dataclass
class ApplyResult:
    """Result of an apply attempt."""

    job_id: str
    status: str
    message: str = ""
    error: str | None = None
    timestamp: str = ""


async def check_already_applied(page: Page) -> bool:
    """Check if already applied to this job.

    Args:
        page: Playwright page instance

    Returns:
        True if already applied
    """
    applied_badge = await page.query_selector(".applied-badge, [class*='Applied']")
    return applied_badge is not None


async def navigate_to_job(page: Page, job_url: str) -> None:
    """Navigate to job detail page.

    Args:
        page: Playwright page instance
        job_url: URL of the job
    """
    await page.goto(job_url)
    await page.wait_for_load_state("domcontentloaded")
    await asyncio.sleep(2)


async def click_and_get_questions(page: Page) -> tuple[bool, list, str]:
    """Click Apply button and intercept the API response.

    Returns:
        Tuple of (success, questions, conversation_id)
    """
    # Set up response handler BEFORE clicking
    questions_data = {}

    async def handle_response(response):
        url = response.url
        if "/apply-workflow/v1/apply" in url:
            try:
                data = await response.json()
                questions_data["data"] = data
                logger.info(
                    f"Intercepted /apply API response with {len(data.get('jobs', []))} jobs"
                )
            except Exception as e:
                logger.error(f"Failed to parse /apply response: {e}")

    page.on("response", handle_response)

    # Try multiple selectors for the apply button
    selectors = [
        ".apply-button",
        "button.apply-button",
        ".apply-button.n3",
        "a.apply-button",
        "[class*='applyBtn']",
    ]

    for selector in selectors:
        apply_button = await page.query_selector(selector)
        if apply_button:
            try:
                await apply_button.click()
                logger.info(f"Clicked apply button with selector: {selector}")
                break
            except Exception as e:
                logger.debug(f"Failed to click {selector}: {e}")
                continue
    else:
        logger.warning("Apply button not found")
        return False, [], ""

    # Wait for API response (max 15 seconds)
    for _ in range(30):  # 30 * 0.5 = 15 seconds
        await asyncio.sleep(0.5)
        if questions_data.get("data"):
            break

    data = questions_data.get("data", {})

    if not data:
        logger.warning("No /apply API response intercepted")
        # Check if sidebar opened
        sidebar = await page.query_selector(".chatbot_DrawerContentWrapper")
        if sidebar:
            text = await sidebar.inner_text()
            logger.warning(f"Sidebar opened but no API response. Content: {text[:500]}")
        else:
            logger.warning("Sidebar did NOT open!")
        return True, [], ""

    if data.get("statusCode") != 0:
        logger.error(f"API error: {data}")
        return True, [], ""

    jobs = data.get("jobs", [])
    if not jobs:
        return True, [], ""

    questionnaire = jobs[0].get("questionnaire", [])
    conversation_id = data.get("chatbotResponse", {}).get("conversation_session_id", "")

    questions = []
    for q in questionnaire:
        questions.append(
            {
                "id": q["questionId"],
                "name": q["questionName"],
                "type": q.get("questionType", "Text Box"),
                "mandatory": q.get("isMandatory", True),
            }
        )

    logger.info(f"Got {len(questions)} questions from API")
    return True, questions, conversation_id


async def get_llm_answers(
    questions: list[dict[str, Any]],
    profile: Any,
    config: Any,
    detailed_profile: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Get LLM-generated answers for all questions.

    Args:
        questions: List of question dicts
        profile: User profile object
        config: Config object with screening answers
        detailed_profile: Optional detailed profile

    Returns:
        Dict mapping question_id to answer
    """
    from job_hunter.llm.provider import get_llm_provider

    llm = get_llm_provider()

    question_list = "\n".join(f"- {q['id']}: {q['name']}" for q in questions)

    prompt = f"""You are a job seeker filling out a job application form on Naukri.
    
Answer ALL questions concisely. Return a JSON object mapping question ID to your answer.

PROFILE:
- Experience: {profile.total_experience_years} years
- Skills: {", ".join(profile.skills[:10])}
- Current Role: {profile.past_roles[0] if profile.past_roles else "N/A"}

SCREENING ANSWERS:
- Notice Period: {config.screening_answers.notice_period}
- Expected CTC: {config.screening_answers.expected_ctc_lpa} LPA
- Current CTC: {config.screening_answers.current_ctc_lpa} LPA
- Willing to Relocate: {config.screening_answers.willing_to_relocate}

QUESTIONS:
{question_list}

Return JSON (question_id -> answer):
{{"38621838": "5", "38621846": "12", ...}}"""

    try:
        result = await llm.generate_json(prompt)
        return result
    except Exception as e:
        logger.error(f"LLM answer generation failed: {e}")
        raise


async def apply_to_job(
    page: Page,
    job: dict[str, Any],
    profile: Any,
    config: Any,
    detailed_profile: dict[str, Any] | None = None,
) -> ApplyResult:
    """Apply to a single job using Naukri APIs.

    Args:
        page: Playwright page instance
        job: Job dict with url, id, title, company
        profile: User profile object
        config: Config object with screening answers
        detailed_profile: Optional detailed profile

    Returns:
        ApplyResult with status
    """
    import re

    # Get job_id (full slug like "job-listings-gen-ai-engineer-...-090426023045")
    job_id_full = job.get("id") or job.get("job_id") or ""

    # Extract numeric job ID (e.g., "090426023045")
    match = re.search(r"(\d{10,})", job_id_full)
    job_id = match.group(1) if match else job_id_full

    job_url = job.get("job_url")
    job_title = job.get("title", "Unknown")
    company = job.get("company", "Unknown")

    logger.info(f"Job ID (full): {job_id_full}, numeric: {job_id}")

    if not job_url:
        return ApplyResult(
            job_id=job_id,
            status="Failed",
            error="No job URL found",
            timestamp=datetime.now().isoformat(),
        )

    logger.info(f"Applying to '{job_title}' at {company}")

    try:
        await navigate_to_job(page, job_url)

        already_applied = await check_already_applied(page)
        if already_applied:
            logger.info(f"Already applied to '{job_title}'")
            return ApplyResult(
                job_id=job_id,
                status="Already Applied",
                message="Already applied to this job",
                timestamp=datetime.now().isoformat(),
            )

        # Click apply button and get questions in one go
        success, questions, conversation_id = await click_and_get_questions(page)

        if not success:
            return ApplyResult(
                job_id=job_id,
                status="Skipped",
                error="Apply button not found (likely company site)",
                timestamp=datetime.now().isoformat(),
            )

        if not questions:
            return ApplyResult(
                job_id=job_id,
                status="Skipped",
                error="No screening questions (possibly company site or already applied)",
                timestamp=datetime.now().isoformat(),
            )

        logger.info(f"Received {len(questions)} questions")

        answers = await get_llm_answers(questions, profile, config, detailed_profile)

        for i, question in enumerate(questions):
            q_id = question["id"]
            answer = answers.get(q_id, "")

            logger.info(
                f"Answering question {i + 1}/{len(questions)}: {question['name']}"
            )

            response_data = await api.send_response(
                page,
                job_id,
                answer,
                conversation_id,
            )

            is_last = api.is_last_question(response_data)

            await asyncio.sleep(0.5)

            if is_last:
                logger.info("Last question answered, waiting for submission...")
                break

        await asyncio.sleep(3)

        final_data = await api.submit_application(page, job_id, answers)

        if api.is_submission_successful(final_data):
            message = final_data.get("jobs", [{}])[0].get("message", "Applied")
            logger.info(f"Successfully applied: {message}")
            return ApplyResult(
                job_id=job_id,
                status="Applied",
                message=message,
                timestamp=datetime.now().isoformat(),
            )
        else:
            error = final_data.get("jobs", [{}])[0].get("message", "Unknown error")
            logger.error(f"Application failed: {error}")
            return ApplyResult(
                job_id=job_id,
                status="Failed",
                error=error,
                timestamp=datetime.now().isoformat(),
            )

    except Exception as e:
        logger.exception(f"Error applying to '{job_title}': {e}")
        return ApplyResult(
            job_id=job_id,
            status="Failed",
            error=str(e),
            timestamp=datetime.now().isoformat(),
        )
