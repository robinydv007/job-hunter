"""Naukri Apply API client."""

from __future__ import annotations

import json
import logging
from typing import Any

from playwright.async_api import Page

logger = logging.getLogger(__name__)


APPLY_ENDPOINT = "https://www.naukri.com/cloudgateway-workflow/workflow-services/apply-workflow/v1/apply"
RESPOND_ENDPOINT = (
    "https://www.naukri.com/cloudgateway-chatbot/chatbot-services/botapi/v5/respond"
)


class ApplyAPIError(Exception):
    """Exception raised for API errors."""

    pass


async def get_questions_from_browser(page: Page) -> tuple[list[dict], str]:
    """Intercept /apply API response from browser.

    This is more reliable than calling API directly since browser handles
    all authentication and payload automatically.

    Returns:
        Tuple of (questions list, conversation_id)
    """
    questions_data = {}
    conversation_id = ""

    def handle_response(response):
        url = response.url
        if "/apply-workflow/v1/apply" in url:
            try:
                data = response.json()
                questions_data["data"] = data
                logger.info("Intercepted /apply API response")
            except:
                pass

    page.on("response", handle_response)

    # Wait for response (max 10 seconds)
    import asyncio

    for _ in range(20):  # 20 * 0.5 = 10 seconds
        await asyncio.sleep(0.5)
        if questions_data.get("data"):
            break

    data = questions_data.get("data", {})

    if not data:
        raise ApplyAPIError("No /apply API response intercepted")

    if data.get("statusCode") != 0:
        raise ApplyAPIError(f"API error: {data}")

    jobs = data.get("jobs", [])
    if not jobs:
        raise ApplyAPIError("No jobs in response")

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

    return questions, conversation_id


async def get_questions(
    page: Page,
    job_id: str,
    mandatory_skills: list[str] | None = None,
    optional_skills: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Call /apply API to get all screening questions.

    Args:
        page: Playwright page instance
        job_id: The job ID
        mandatory_skills: List of mandatory skills from job
        optional_skills: List of optional skills from job

    Returns:
        List of question dicts with id, name, type, mandatory
    """
    mandatory_skills = mandatory_skills or []
    optional_skills = optional_skills or []

    # Extract numeric job ID from full job ID (e.g., "090426023045" from "job-listings-gen-ai-engineer-...")
    import re

    match = re.search(r"(\d{10,})", job_id)
    numeric_job_id = match.group(1) if match else job_id

    payload = {
        "strJobsarr": [numeric_job_id],
        "logstr": f"—cluster—1—{numeric_job_id}—",
        "flowtype": "show",
        "crossdomain": True,
        "jquery": 1,
        "rdxMsgId": "",
        "chatBotSDK": True,
        "applyTypeId": "107",
        "closebtn": "y",
        "applySrc": "cluster",
        "sid": numeric_job_id,
        "mid": "",
        "mandatory_skills": mandatory_skills,
        "optional_skills": optional_skills,
    }

    logger.info(f"Calling /apply API with job_id: {numeric_job_id}")

    try:
        response = await page.request.post(APPLY_ENDPOINT, data=payload)
    except Exception as e:
        logger.error(f"Exception calling /apply API: {e}")
        raise ApplyAPIError(f"Failed to call /apply API: {e}")

    if not response.ok:
        logger.error(f"/apply API returned status: {response.status}")
        try:
            text = await response.text()
            logger.error(f"Response text: {text[:500]}")
        except:
            pass
        raise ApplyAPIError(f"Failed to get questions: {response.status}")

    data = await response.json()

    if data.get("statusCode") != 0:
        raise ApplyAPIError(f"API error: {data}")

    jobs = data.get("jobs", [])
    if not jobs:
        raise ApplyAPIError("No jobs in response")

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

    return questions, conversation_id


async def send_response(
    page: Page,
    job_id: str,
    answer: str,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Send a single answer via /respond API.

    Args:
        page: Playwright page instance
        job_id: The job ID
        answer: The answer to submit
        conversation_id: Optional conversation ID from /apply response

    Returns:
        Response data with next question info
    """
    app_name = f"{job_id}_apply"

    payload = {
        "input": {
            "text": [answer],
            "id": ["-1"],
        },
        "appName": app_name,
        "domain": "Naukri",
        "conversation": app_name,
        "channel": "web",
        "status": "Fresh",
        "utmSource": "",
        "utmContent": "",
        "deviceType": "WEB",
    }

    response = await page.request.post(RESPOND_ENDPOINT, data=payload)

    if not response.ok:
        raise ApplyAPIError(f"Failed to send response: {response.status}")

    data = await response.json()

    return data


async def submit_application(
    page: Page,
    job_id: str,
    answers: dict[str, str],
) -> dict[str, Any]:
    """Submit application with all answers via final /apply call.

    Args:
        page: Playwright page instance
        job_id: The job ID
        answers: Dict of question_id -> answer

    Returns:
        Response data with status
    """
    payload = {
        "strJobsarr": [job_id],
        "logstr": f"—cluster—{job_id}—",
        "flowtype": "show",
        "crossdomain": True,
        "jquery": 1,
        "rdxMsgId": "",
        "chatBotSDK": True,
        "applyTypeId": "107",
        "closebtn": "y",
        "applySrc": "cluster",
        "sid": "",
        "mid": "",
        "applyData": {
            job_id: {
                "answers": answers,
            }
        },
        "qupData": {},
    }

    response = await page.request.post(APPLY_ENDPOINT, data=payload)

    if not response.ok:
        raise ApplyAPIError(f"Failed to submit application: {response.status}")

    data = await response.json()

    return data


def is_submission_successful(data: dict[str, Any]) -> bool:
    """Check if application was successful.

    Args:
        data: Response data from final /apply call

    Returns:
        True if application succeeded
    """
    jobs = data.get("jobs", [])
    if not jobs:
        return False

    job = jobs[0]
    return job.get("status") == 200


def is_last_question(response_data: dict[str, Any]) -> bool:
    """Check if this was the last question.

    Args:
        response_data: Response from /respond API

    Returns:
        True if this was the last question
    """
    return response_data.get("isLeafNode", False) is True
