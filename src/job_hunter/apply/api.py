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

# Headers for the /apply-workflow endpoint (Naukri API gateway).
# The browser's JS SDK adds appid/clientid/systemid via fetch() headers —
# page.request.post() does NOT auto-include them, causing 500 without them.
NAUKRI_APPLY_HEADERS = {
    "appid": "121",
    "clientid": "d3skt0p",
    "systemid": "jobseeker",
    "Content-Type": "application/json",
    "accept": "application/json",
}

# Headers for the chatbot /respond endpoint.
# The browser does NOT send appid/clientid/systemid to this endpoint.
# Confirmed from real browser curl: only Content-Type + accept + auth (via cookies).
NAUKRI_CHATBOT_HEADERS = {
    "Content-Type": "application/json",
    "accept": "application/json",
}


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
    """Send a single answer via /respond API."""
    app_name = f"{job_id}_apply"

    # Use app_name for BOTH appName and conversation.
    # The UUID (conversation_session_id) from /apply is an auth/session token, NOT the routing key.
    # Naukri's chatbot backend routes by {jobId}_apply — same as appName.
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

    print(f"[/respond] Sending: answer={answer!r}, conversation={app_name}")
    logger.info(f"[/respond] POST conversation={app_name}")

    response = await page.request.post(
        RESPOND_ENDPOINT,
        headers=NAUKRI_CHATBOT_HEADERS,
        data=json.dumps(payload).encode(),
    )

    if not response.ok:
        body = await response.text()
        logger.error(f"[/respond] HTTP {response.status}: {body[:500]}")
        raise ApplyAPIError(f"Failed to send response: {response.status}")

    data = await response.json()
    print(f"[/respond] Response: {data}")
    logger.info(f"[/respond] isLeafNode={data.get('isLeafNode')}, keys={list(data.keys())}")

    return data


async def submit_application(
    page: Page,
    job_id: str,
    answers: dict[str, str],
    mandatory_skills: list[str] | None = None,
    optional_skills: list[str] | None = None,
    sid: str = "",
) -> dict[str, Any]:
    """Submit application with all answers via final /apply call.

    This is Phase 3 of the Naukri apply flow. It replicates exactly what the
    browser's chatbot SDK sends after dataCommitted=True from /respond.

    Args:
        page: Playwright page instance
        job_id: The numeric job ID
        answers: Dict of question_id -> answer (from chatbotResponse.applyData)
        mandatory_skills: Job's mandatory skills list
        optional_skills: Job's optional skills list
        sid: Search session ID (from job URL ?sid= param, or empty string)
    """
    mandatory_skills = mandatory_skills or []
    optional_skills = optional_skills or []

    payload = {
        "strJobsarr": [job_id],
        "logstr": f"\u2014cluster\u2014{job_id}\u2014",
        "flowtype": "show",
        "crossdomain": True,
        "jquery": 1,
        "rdxMsgId": "",
        "chatBotSDK": True,
        "mandatory_skills": mandatory_skills,
        "optional_skills": optional_skills,
        "applyTypeId": "107",
        "closebtn": "y",
        "applySrc": "cluster",
        "sid": sid,
        "mid": "",
        "applyData": {
            job_id: {
                "answers": answers,
            }
        },
        "qupData": {},
    }

    print(f"[submit_application] Posting with answers={answers}, sid={sid!r}")
    logger.info(f"[submit_application] job_id={job_id}, skills={mandatory_skills[:3]}")

    # Must use NAUKRI_APPLY_HEADERS — page.request.post() doesn't auto-include
    # appid/clientid/systemid which the /apply API gateway requires for routing.
    # Without them the endpoint returns 500.
    response = await page.request.post(
        APPLY_ENDPOINT,
        headers=NAUKRI_APPLY_HEADERS,
        data=json.dumps(payload).encode(),
    )

    if not response.ok:
        body = await response.text()
        logger.error(f"[submit_application] HTTP {response.status}: {body[:500]}")
        raise ApplyAPIError(f"Failed to submit application: {response.status}")

    data = await response.json()
    print(f"[submit_application] Response: {data}")
    logger.info(f"[submit_application] statusCode={data.get('statusCode')}, jobs={len(data.get('jobs', []))}")

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
