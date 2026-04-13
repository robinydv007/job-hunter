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
    """Check if already applied to this job."""
    applied_badge = await page.query_selector(".applied-badge, [class*='Applied']")
    return applied_badge is not None


async def verify_application_applied(page: Page) -> bool:
    """Verify that application was successfully submitted."""
    # Check for Applied badge
    applied_badge = await page.query_selector(".applied-badge")
    if applied_badge:
        badge_text = await applied_badge.inner_text()
        if "applied" in badge_text.lower():
            logger.info(f"Found Applied badge: {badge_text}")
            return True

    # Check if sidebar closed (indicates successful submission)
    sidebar = await page.query_selector(".chatbot_DrawerContentWrapper")
    if not sidebar:
        logger.info("Sidebar closed - application may have been submitted")
        current_url = page.url
        if "myapply" in current_url or "success" in current_url:
            logger.info(f"URL shows success: {current_url}")
            return True
        return True

    # Check sidebar content for success
    sidebar_text = await sidebar.inner_text().lower()
    if (
        "thank" in sidebar_text
        or "success" in sidebar_text
        or "applied" in sidebar_text
    ):
        logger.info(f"Sidebar shows success: {sidebar_text[:100]}")
        return True

    return False


async def navigate_to_job(page: Page, job_url: str) -> None:
    """Navigate to job detail page."""
    await page.goto(job_url)
    await page.wait_for_load_state("domcontentloaded")
    await asyncio.sleep(2)


async def click_and_get_questions(page: Page) -> tuple[bool, list, str]:
    """Click Apply button and intercept the API response."""
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

    for _ in range(30):
        await asyncio.sleep(0.5)
        if questions_data.get("data"):
            break

    data = questions_data.get("data", {})

    if not data:
        logger.warning("No /apply API response intercepted")
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
    """Get LLM-generated answers for all questions."""
    from job_hunter.llm.provider import get_llm
    import json

    llm = get_llm()

    question_list = "\n".join(f"- {q['id']}: {q['name']}" for q in questions)

    prompt = f"""You are a job seeker filling out a job application form on Naukri.
    
Answer ALL questions concisely. Return a JSON object mapping question ID to your answer.

PROFILE:
- Experience: {profile.total_experience_years} years
- Skills: {", ".join(profile.skills[:10])}
- Current Role: {profile.past_roles[0] if profile.past_roles else "N/A"}

SCREENING ANSWERS:
- Notice Period: {config.screening.screening_answers.notice_period}
- Expected CTC: {config.screening.screening_answers.expected_ctc_lpa} LPA
- Current CTC: {config.screening.screening_answers.current_ctc_lpa} LPA
- Willing to Relocate: {config.screening.screening_answers.willing_to_relocate}

QUESTIONS:
{question_list}

Return JSON (question_id -> answer):
{{"38621838": "5", "38621846": "12", ...}}"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = content[start:end]
            answers = json.loads(json_str)
            return answers
        else:
            raise ValueError("No JSON found in LLM response")
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
    """Apply to a single job using Naukri APIs."""
    import re

    job_id_full = job.get("id") or job.get("job_id") or ""
    match = re.search(r"(\d{10,})", job_id_full)
    job_id = match.group(1) if match else job_id_full
    job_url = job.get("job_url")
    job_title = job.get("title", "Unknown")
    company = job.get("company", "Unknown")

    logger.info(f"Applying to '{job_title}' at {company}")

    if not job_url:
        return ApplyResult(
            job_id=job_id,
            status="Failed",
            error="No job URL found",
            timestamp=datetime.now().isoformat(),
        )

    try:
        await navigate_to_job(page, job_url)

        # Check if already applied
        if await check_already_applied(page):
            return ApplyResult(
                job_id=job_id,
                status="Already Applied",
                message="Already applied to this job",
                timestamp=datetime.now().isoformat(),
            )

        # Click apply button and get questions
        success, questions, conversation_id = await click_and_get_questions(page)

        if not success:
            return ApplyResult(
                job_id=job_id,
                status="Skipped",
                error="Apply button not found (company site)",
                timestamp=datetime.now().isoformat(),
            )

        # Handle no questions case
        if not questions:
            current_url = page.url
            if "naukri.com" not in current_url:
                return ApplyResult(
                    job_id=job_id,
                    status="Skipped",
                    error="External company site",
                    timestamp=datetime.now().isoformat(),
                )

            if await check_already_applied(page):
                return ApplyResult(
                    job_id=job_id,
                    status="Already Applied",
                    message="Already applied",
                    timestamp=datetime.now().isoformat(),
                )

            return ApplyResult(
                job_id=job_id,
                status="Skipped",
                error="No screening questions",
                timestamp=datetime.now().isoformat(),
            )

        logger.info(f"Received {len(questions)} questions")

        # Get LLM answers
        answers = await get_llm_answers(questions, profile, config, detailed_profile)

        # Submit each answer
        for i, question in enumerate(questions):
            q_id = question["id"]
            answer = answers.get(q_id, "")
            logger.info(
                f"Answering question {i + 1}/{len(questions)}: {question['name']}"
            )

            response_data = await api.send_response(
                page, job_id, answer, conversation_id
            )
            is_last = api.is_last_question(response_data)
            await asyncio.sleep(0.5)

            if is_last:
                logger.info(
                    "Last question answered, waiting for browser auto-submit..."
                )
                await asyncio.sleep(8)
                break

        # Verify application
        if await verify_application_applied(page):
            return ApplyResult(
                job_id=job_id,
                status="Applied",
                message="Successfully applied",
                timestamp=datetime.now().isoformat(),
            )

        if await check_already_applied(page):
            return ApplyResult(
                job_id=job_id,
                status="Already Applied",
                message="Already applied",
                timestamp=datetime.now().isoformat(),
            )

        # Check sidebar for confirmation
        sidebar = await page.query_selector(".chatbot_DrawerContentWrapper")
        if sidebar:
            text = await sidebar.inner_text()
            if "thank" in text.lower():
                return ApplyResult(
                    job_id=job_id,
                    status="Applied",
                    message="Applied (sidebar confirmation)",
                    timestamp=datetime.now().isoformat(),
                )

        return ApplyResult(
            job_id=job_id,
            status="Applied",
            message="Applied (assumed)",
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
