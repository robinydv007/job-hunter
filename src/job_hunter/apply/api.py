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


# NOTE: get_questions_from_browser and get_questions have been removed.
# Question interception is handled exclusively by click_and_get_questions()
# in naukri_apply.py, which uses page.expect_response() for reliable async capture.


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

    logger.debug(f"[/respond] Sending: answer={answer!r}, conversation={app_name}")
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

    try:
        data = await response.json()
    except Exception:
        body = await response.text()
        raise ApplyAPIError(
            f"Chatbot /respond returned non-JSON (HTTP {response.status}): {body[:300]}"
        )

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

    logger.debug(f"[submit_application] Posting with answers={answers}, sid={sid!r}")
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
    logger.debug(f"[submit_application] Response: {data}")
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

