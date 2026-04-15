"""Naukri auto-apply orchestrator using APIs."""

from __future__ import annotations

import asyncio
import logging
import re
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
    try:
        applied_badge = await page.query_selector(".applied-badge, [class*='Applied']")
        print(f"Applied badge found: {applied_badge}")
        return applied_badge is not None
    except Exception as e:
        logger.debug(f"Could not check already applied: {e}")
        return False


async def verify_application_applied(page: Page) -> bool:
    """Verify that application was successfully submitted."""
    try:
        applied_badge = await page.query_selector(".applied-badge")
        if applied_badge:
            badge_text = await applied_badge.inner_text()
            if "applied" in badge_text.lower():
                logger.info(f"Found Applied badge: {badge_text}")
                return True
    except Exception as e:
        logger.debug(f"Could not check Applied badge: {e}")

    try:
        sidebar = await page.query_selector(".chatbot_DrawerContentWrapper")
        if not sidebar:
            logger.info("Sidebar closed - application may have been submitted")
            current_url = page.url
            if "myapply" in current_url or "success" in current_url:
                logger.info(f"URL shows success: {current_url}")
                return True
            return True
    except Exception as e:
        logger.debug(f"Could not check sidebar: {e}")

    return False


async def navigate_to_job(page: Page, job_url: str) -> None:
    """Navigate to job detail page, handling post-apply redirects gracefully."""
    try:
        await page.goto(job_url, wait_until="domcontentloaded")
    except Exception as e:
        # After a successful apply, Naukri sometimes redirects the browser to
        # /myapply/historypage via JS. If that interrupts our next navigation,
        # wait for it to settle then retry once.
        err_str = str(e).lower()
        if "interrupted" in err_str or "another navigation" in err_str:
            logger.warning(f"[navigate] Interrupted ({e}) — waiting for redirect to settle")
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=8000)
            except Exception:
                pass
            await asyncio.sleep(1)
            await page.goto(job_url, wait_until="domcontentloaded")
            print(f"[navigate] Retried after redirect. Now at: {page.url}")
        else:
            raise
    print(f"Navigated to job URL: {job_url}")
    await asyncio.sleep(2)


async def answer_questions_via_ui(
    page: Page,
    questions: list[dict],
    answers: dict[str, str],
) -> bool:
    """Submit all answers through the Naukri chatbot UI.

    Instead of calling /respond directly (which requires chatbot SDK init),
    we type into the visible contenteditable div and click the Send div —
    the browser handles all session/auth management automatically.

    Naukri chatbot DOM (confirmed from live HTML dump):
      Input:  div.textArea[contenteditable='true']     (inside .chatbot_InputContainer)
      Submit: div.sendMsg                               (inside div.send — 'disabled' class removed after typing)
    """
    # Intercept real /respond requests for diagnostic logging
    async def log_respond_request(request):
        if "/respond" in request.url:
            try:
                body = request.post_data
                print(f"[BROWSER /respond] URL={request.url}")
                print(f"[BROWSER /respond] Payload={body}")
                logger.info(f"[BROWSER /respond] payload={body}")
            except Exception as e:
                logger.debug(f"Could not log /respond request: {e}")

    page.on("request", log_respond_request)

    # Wait for chatbot drawer to open
    try:
        await page.wait_for_selector(".chatbot_DrawerContentWrapper", timeout=12000)
        print("[UI] Chatbot drawer is open")
        logger.info("[UI] Chatbot drawer confirmed open")
    except Exception as e:
        logger.warning(f"[UI] Chatbot drawer did not open: {e}")
        return False

    # Confirmed selectors from live HTML dump
    # The input is a contenteditable div, NOT <input> or <textarea>
    input_selectors = [
        "div.textArea[contenteditable='true']",
        ".chatbot_InputContainer [contenteditable='true']",
        ".chatbot_SendMessageContainer [contenteditable='true']",
        "[contenteditable='true']",
    ]
    # Submit is a div, NOT a <button>
    submit_selectors = [
        "div.sendMsg",
        ".send .sendMsg",
        "[id^='sendMsg_'] .sendMsg",
        "[id^='sendMsg_']",
    ]

    for i, question in enumerate(questions):
        q_id = question["id"]
        answer = answers.get(q_id, "")
        print(f"[UI] Q{i+1}/{len(questions)}: {question['name']!r} -> {answer!r}")
        logger.info(f"[UI] Answering Q{i+1}: {question['name']} -> {answer!r}")

        # Wait up to 10 s for a visible, enabled contenteditable input
        input_el = None
        for attempt in range(20):
            for sel in input_selectors:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    input_el = el
                    print(f"[UI] Found input via: {sel}")
                    break
            if input_el:
                break
            await asyncio.sleep(0.5)

        if not input_el:
            drawer = await page.query_selector(".chatbot_DrawerContentWrapper")
            if drawer:
                html = await drawer.inner_html()
                print(f"[UI] Drawer HTML (no input found):\n{html[:2000]}")
                logger.warning(f"[UI] No input found for Q{i+1}. Drawer HTML: {html[:2000]}")
            else:
                logger.warning(f"[UI] No input and no drawer for Q{i+1}")
            return False

        # Click to focus, then type the answer.
        # Use keyboard.type() instead of fill() so input events fire correctly
        # (which removes the 'disabled' class from div.send, enabling the submit div).
        await input_el.click()
        await asyncio.sleep(0.1)
        # Clear any existing content via Ctrl+A + Delete
        await page.keyboard.press("Control+a")
        await page.keyboard.press("Delete")
        await page.keyboard.type(answer)
        print(f"[UI] Typed answer: {answer!r}")
        await asyncio.sleep(0.5)  # Give time for 'disabled' class to be removed

        # Click the send div (not a button — Playwright .click() works on any element)
        submitted = False
        for sel in submit_selectors:
            btn = await page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.click()
                print(f"[UI] Submitted via: {sel}")
                logger.info(f"[UI] Q{i+1} submitted via {sel}")
                submitted = True
                break

        if not submitted:
            # Fallback: Enter key
            await input_el.press("Enter")
            print("[UI] Submitted via Enter key")
            logger.info(f"[UI] Q{i+1} submitted via Enter")

        # Wait for chatbot to process and render next question
        await asyncio.sleep(2)

    # After all answers, wait for the chatbot to auto-submit the application
    logger.info("[UI] All answers submitted, waiting for auto-submit...")
    await asyncio.sleep(8)
    return True


def _pick_best_option(answer: str, options: list[dict]) -> str:
    """Match a free-form LLM answer to the closest chatbot option value.

    Radio/select button questions only accept exact option values.
    e.g. options=[{name:'yes', value:'yes'}, {name:'no', value:'no'}]
    LLM might say 'Yes, I can join immediately' — we map that to 'yes'.
    """
    answer_lower = answer.lower().strip()

    # 1. Exact match on value
    for opt in options:
        if opt.get("value", "").lower() == answer_lower:
            return opt["value"]

    # 2. Option name or value appears in answer
    for opt in options:
        opt_name = opt.get("name", "").lower()
        opt_val = opt.get("value", "").lower()
        if opt_name and opt_name in answer_lower:
            return opt["value"]
        if opt_val and opt_val in answer_lower:
            return opt["value"]

    # 3. Semantic yes/no detection
    yes_words = {"yes", "y", "ok", "okay", "sure", "can", "will", "immediately",
                 "comfortable", "agree", "available", "currently"}
    no_words = {"no", "not", "cannot", "can't", "won't", "don't", "haven't",
                "shouldn't", "uncomfortable", "disagree"}

    answer_words = set(re.findall(r"\b\w+\b", answer_lower))
    if answer_words & yes_words:
        for opt in options:
            if "yes" in opt.get("value", "").lower() or "yes" in opt.get("name", "").lower():
                return opt["value"]
    if answer_words & no_words:
        for opt in options:
            if "no" in opt.get("value", "").lower() or "no" in opt.get("name", "").lower():
                return opt["value"]

    # 4. Default: first option
    logger.warning(f"Cannot match {answer!r} to options {options}, using first")
    return options[0]["value"] if options else answer


def _extract_question_text(speech_response: list[dict]) -> str:
    """Extract the last question text from a chatbot speechResponse array.

    The chatbot may send multiple speech items (e.g. greeting + question).
    The question is always the LAST text item.
    """
    texts = [item["response"] for item in speech_response if item.get("type") == "text"]
    return texts[-1].strip() if texts else ""


def _find_matching_question(
    chatbot_text: str,
    questions: list[dict],
    answered_ids: set[str],
) -> dict | None:
    """Match a chatbot prompt text to the best unanswered question.

    Uses normalized substring matching: the question name and the chatbot prompt
    share enough overlapping words to identify the same question.
    Falls back to the first unanswered question if no match found.
    """
    if not chatbot_text:
        unanswered = [q for q in questions if q["id"] not in answered_ids]
        return unanswered[0] if unanswered else None

    def normalize(s: str) -> str:
        return re.sub(r"[^a-z0-9 ]", " ", s.lower())

    chatbot_norm = normalize(chatbot_text)
    chatbot_words = set(chatbot_norm.split())
    # Filter short stop words
    stop = {"is", "are", "you", "do", "have", "your", "in", "to", "the", "a", "of", "or", "and"}
    chatbot_words -= stop

    best_q = None
    best_score = 0
    for q in questions:
        if q["id"] in answered_ids:
            continue
        q_norm = normalize(q["name"])
        q_words = set(q_norm.split()) - stop
        if not q_words:
            continue
        overlap = len(chatbot_words & q_words)
        # Score = overlap / union (Jaccard-like)
        score = overlap / len(chatbot_words | q_words) if chatbot_words | q_words else 0
        if score > best_score:
            best_score = score
            best_q = q

    if best_q and best_score > 0.15:  # threshold: at least 15% word overlap
        return best_q

    # Fallback: first unanswered
    unanswered = [q for q in questions if q["id"] not in answered_ids]
    return unanswered[0] if unanswered else None


async def click_and_get_questions(page: Page) -> tuple[bool, list, str, dict, int]:
    """Click Apply button and intercept the API response.

    Returns:
        (success, questions, conversation_id, chatbot_response, initial_node)
    """
    print("Clicking apply button...")
    print('outside handle response method...')

    # Find the apply button first
    selectors = [
        ".apply-button",
        "button.apply-button",
        ".apply-button.n3",
        "a.apply-button",
        "[class*='applyBtn']",
    ]

    apply_button = None
    matched_selector = None
    for selector in selectors:
        btn = await page.query_selector(selector)
        if btn:
            apply_button = btn
            matched_selector = selector
            break

    if not apply_button:
        logger.warning("Apply button not found — likely 'Apply on company site' job, skipping")
        print("Apply button not found")
        return False, [], "", {}, -1

    # Use expect_response to correctly intercept and await the async JSON parse.
    # page.on("response", async_handler) is broken — Playwright never awaits the coroutine,
    # so response.json() never resolves and questions_data stays empty.
    data = {}
    try:
        async with page.expect_response(
            lambda r: "/apply-workflow/v1/apply" in r.url, timeout=15000
        ) as response_info:
            await apply_button.click()
            logger.info(f"Clicked apply button with selector: {matched_selector}")

        print('handle response method called...')
        response = await response_info.value
        data = await response.json()
        logger.info(
            f"Intercepted /apply API response with {len(data.get('jobs', []))} jobs"
        )
    except Exception as e:
        logger.warning(f"No /apply API response intercepted: {e}")
        sidebar = await page.query_selector(".chatbot_DrawerContentWrapper")
        if sidebar:
            text = await sidebar.inner_text()
            logger.warning(f"Sidebar opened but no API response. Content: {text[:500]}")
        else:
            logger.warning("Sidebar did NOT open!")
        return True, [], "", {}, -1

    if not data:
        logger.warning("No /apply API response intercepted")
        return True, [], "", {}, -1

    if data.get("statusCode") != 0:
        logger.error(f"API error: {data}")
        return True, [], "", {}, -1

    jobs = data.get("jobs", [])
    if not jobs:
        return True, [], "", {}, -1

    questionnaire = jobs[0].get("questionnaire", [])
    chatbot_response = data.get("chatbotResponse", {})
    conversation_id = chatbot_response.get("conversation_session_id", "")

    # Log full chatbotResponse so we can see ALL available fields if needed
    print(f"[/apply] Full chatbotResponse: {chatbot_response}")
    logger.info(f"[/apply] chatbotResponse keys: {list(chatbot_response.keys())}")
    logger.info(f"[/apply] conversation_session_id: {conversation_id}")

    # Find already-answered question IDs from applyData.
    # When a session is resumed (same job applied again), some questions are pre-answered.
    # The chatbot is already on the NEXT unanswered question — we must skip past answered ones.
    apply_data = chatbot_response.get("applyData", {})
    already_answered_ids: set[str] = set()
    for job_answers in apply_data.values():
        already_answered_ids.update(str(k) for k in job_answers.get("answers", {}).keys())
    if already_answered_ids:
        print(f"[/apply] Already answered question IDs (skipping): {already_answered_ids}")
        logger.info(f"[/apply] Skipping already-answered: {already_answered_ids}")

    all_questions = []
    for q in questionnaire:
        all_questions.append(
            {
                "id": q["questionId"],
                "name": q["questionName"],
                "type": q.get("questionType", "Text Box"),
                "mandatory": q.get("isMandatory", True),
            }
        )

    initial_node = chatbot_response.get("currentNode", -1)

    # Only return questions that still need to be answered
    questions = [q for q in all_questions if q["id"] not in already_answered_ids]
    logger.info(f"Total questions: {len(all_questions)}, unanswered: {len(questions)}")
    print(f"[/apply] Unanswered questions to answer: {[q['name'] for q in questions]}")

    return True, questions, conversation_id, chatbot_response, initial_node


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

    # Include type so LLM knows when to give a short option value vs free text
    question_list = "\n".join(
        f"- {q['id']}: {q['name']} [type: {q['type']}]"
        for q in questions
    )

    prompt = f"""You are a job seeker filling out a job application form on Naukri.
Answer ALL questions concisely. Return a JSON object mapping question ID to your answer.

CRITICAL RULES:
- For 'Radio Button' or 'single_select' type questions: answer with ONLY the exact option value,
  typically 'yes' or 'no'. Never write full sentences for radio buttons.
- For 'Text Box' questions: give a brief, direct answer (1-2 sentences max).
- If a question says 'don't apply if...' and you do NOT qualify, still answer honestly
  (the system will handle eligibility separately).

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

Return JSON only (question_id -> answer string):
{{"38621838": "5", "38621846": "yes", ...}}"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        print(f"[LLM] Raw response:\n{content}")
        logger.info(f"[LLM] Raw response: {content}")
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = content[start:end]
            answers = json.loads(json_str)
            print(f"[LLM] Parsed answers: {answers}")
            logger.info(f"[LLM] Parsed answers: {answers}")
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

    # Extract sid from job URL query params (Naukri search session ID)
    # e.g. https://www.naukri.com/job-listings-...?sid=17757311497391557_2&...
    sid = ""
    if job_url and "sid=" in job_url:
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(job_url)
            qs = parse_qs(parsed.query)
            sid = qs.get("sid", [""])[0]
        except Exception:
            pass

    # Extract skills from job dict for the final apply payload
    required_skills = job.get("required_skills", [])
    mandatory_skills = job.get("mandatory_skills", required_skills)
    optional_skills = job.get("optional_skills", [])

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
        success, questions, conversation_id, chatbot_response_data, chatbot_initial_node = await click_and_get_questions(page)
        print(f"Success: {success}, Questions: {questions}, Conversation ID: {conversation_id}")
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

        # Submit answers — RESPONSE-DRIVEN loop.
        # The chatbot tells us what it wants next via speechResponse.
        # We read the chatbot's prompt text after each response to find the right answer,
        # rather than iterating our list by index (which breaks when chatbot skips nodes).
        answered_ids: set[str] = set()
        prev_node = chatbot_initial_node
        max_iterations = len(questions) * 3 + 5  # safety cap

        # Seed: what question is the chatbot asking right now?
        current_prompt = _extract_question_text(
            chatbot_response_data.get("speechResponse", [])
        )

        for iteration in range(max_iterations):
            if not [q for q in questions if q["id"] not in answered_ids]:
                logger.info("All questions answered")
                break

            # Find which question the chatbot is currently asking
            matched_q = _find_matching_question(current_prompt, questions, answered_ids)
            if matched_q is None:
                logger.warning("No unanswered question matched chatbot prompt — done")
                break

            q_id = matched_q["id"]
            q_type = matched_q.get("type", "Text Box")
            answer = answers.get(q_id, "")
            logger.info(f"[iter {iteration+1}] Chatbot asks: {repr(current_prompt[:80])}")
            logger.info(f"[iter {iteration+1}] Matched: {repr(matched_q['name'])} [{q_type}] -> {answer!r}")
            print(f"[loop] Q matched: {repr(matched_q['name'])} -> {answer!r}")

            max_retries = 3
            for attempt in range(max_retries + 1):
                try:
                    response_data = await api.send_response(
                        page, job_id, answer, conversation_id
                    )
                except Exception as e:
                    logger.error(f"[respond] failed: {e} — falling back to UI")
                    remaining = [q for q in questions if q["id"] not in answered_ids]
                    remaining_answers = {q["id"]: answers.get(q["id"], "") for q in remaining}
                    ui_success = await answer_questions_via_ui(page, remaining, remaining_answers)
                    if not ui_success:
                        return ApplyResult(
                            job_id=job_id,
                            status="Failed",
                            error=f"Both API and UI submission failed: {e}",
                            timestamp=datetime.now().isoformat(),
                        )
                    return ApplyResult(
                        job_id=job_id,
                        status="Applied",
                        message="Applied (UI fallback after API failure)",
                        timestamp=datetime.now().isoformat(),
                    )

                current_node = response_data.get("currentNode", -1)
                logger.info(f"[respond] attempt {attempt+1}: prevNode={prev_node}, currentNode={current_node}, dataCommitted={response_data.get('dataCommitted')}")
                print(f"[/respond] iter={iteration+1} attempt={attempt+1} node={current_node} response: {response_data}")

                # dataCommitted = chatbot conversation complete → trigger Phase 3 apply
                if response_data.get("dataCommitted"):
                    logger.info("dataCommitted=True — calling submit_application (Phase 3)")
                    print("[/respond] dataCommitted=True — submitting application via /apply")

                    final_apply_data = response_data.get("applyData", {})
                    job_answers = final_apply_data.get(job_id, {}).get("answers", {})
                    print(f"[submit] answers={job_answers}, sid={sid!r}")

                    try:
                        submit_result = await api.submit_application(
                            page, job_id, job_answers,
                            mandatory_skills=mandatory_skills,
                            optional_skills=optional_skills,
                            sid=sid,
                        )
                        if api.is_submission_successful(submit_result):
                            logger.info("submit_application: success")
                            return ApplyResult(
                                job_id=job_id,
                                status="Applied",
                                message="Successfully applied (confirmed)",
                                timestamp=datetime.now().isoformat(),
                            )
                        else:
                            logger.warning(f"[submit] Non-200: {submit_result}")
                    except Exception as e:
                        logger.error(f"[submit] Error: {e}")

                    # Fallback: reload and check badge
                    await asyncio.sleep(3)
                    await page.reload()
                    await page.wait_for_load_state("domcontentloaded")
                    await asyncio.sleep(2)
                    applied = await check_already_applied(page)
                    return ApplyResult(
                        job_id=job_id,
                        status="Applied",
                        message=f"Applied (dataCommitted, badge={'confirmed' if applied else 'pending'})",
                        timestamp=datetime.now().isoformat(),
                    )

                # Answer accepted when chatbot node advanced
                if current_node > prev_node:
                    answered_ids.add(q_id)
                    prev_node = current_node
                    # Update current_prompt to what chatbot is asking now
                    current_prompt = _extract_question_text(
                        response_data.get("speechResponse", [])
                    )
                    logger.info(f"Answer accepted. Next chatbot prompt: {repr(current_prompt[:80])}")
                    break  # move to next iteration

                # Same node = answer rejected
                options = response_data.get("options", [])
                if options and attempt < max_retries:
                    old_answer = answer
                    answer = _pick_best_option(answer, options)
                    logger.warning(f"Rejected (node={current_node}), retry: {old_answer!r} -> {answer!r}")
                    print(f"[retry] retrying with {answer!r}")
                else:
                    # Give up on this question — mark answered to avoid infinite loop
                    logger.warning(f"Could not answer {matched_q['name']!r} after {attempt+1} attempts, skipping")
                    answered_ids.add(q_id)
                    current_prompt = _extract_question_text(
                        response_data.get("speechResponse", [])
                    )
                    break

            await asyncio.sleep(0.5)


        # Verify application (with error handling for navigation)
        try:
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
                print(f"[Verify] Chatbot drawer text: {text[:500]}")
                logger.info(f"[Verify] Chatbot drawer text: {text[:500]}")
                if "thank" in text.lower() or "applied" in text.lower() or "success" in text.lower():
                    return ApplyResult(
                        job_id=job_id,
                        status="Applied",
                        message="Applied (sidebar confirmation)",
                        timestamp=datetime.now().isoformat(),
                    )
            else:
                print("[Verify] Chatbot drawer closed after submission — treating as success")
                logger.info("[Verify] Sidebar closed, assuming applied")
        except Exception as e:
            logger.warning(
                f"Error during verification (possibly due to navigation): {e}"
            )
            # If we got here after all questions, assume applied
            return ApplyResult(
                job_id=job_id,
                status="Applied",
                message="Applied (assuming success after all responses)",
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
