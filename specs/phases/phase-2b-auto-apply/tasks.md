# Phase 2b — Tasks: Auto-Apply

> **Status: Complete** — All tasks done, testing complete, user verified

## Prerequisites (Phase 2a complete - all items checked)

- [x] `config/screening.yaml` created and loaded
- [x] `config/user.yaml` updated (screening_answers removed, resume_path added with default resume.pdf)
- [x] Single LLM call extracts both basic and detailed profiles
- [x] `data/profile_detailed.yaml` created with extended profile (tech_experience, achievements, etc.)
- [x] Resume change detection works
- [x] Subsequent runs use cached profiles
- [x] `load_profile_with_detailed()` available to get both profile + detailed together

## Task Checklist

### 0. API Flow Verification (Exploration)
- [x] Run `scripts/explore_apply_api.py` to verify API flow
- [x] Capture and analyze API responses
- [x] Verify /apply returns all questions at once
- [x] Verify /respond works for each answer
- [x] Verify browser auto-submits after all responses
- [x] Document any additional findings

### 1. Apply Package Setup
- [x] Create `src/job_hunter/apply/__init__.py` package init
- [x] Create `src/job_hunter/apply/api.py` for API client (/apply and /respond)
- [x] Create `src/job_hunter/apply/naukri_apply.py` for auto-apply logic
- [x] Skip `client.py` - not needed (page.request inherits session)

### 2. API Client (`api.py`)
- [x] Implement `get_questions(page, job_id, skills)` - Call /apply API
- [x] Implement `send_response(page, job_id, question_id, answer, app_name)` - Call /respond API
- [x] Implement `extract_conversation_id(response)` - Extract from /apply response
- [x] Test: Verify API calls work and return expected data

### 3. Session Management
- [x] Use Playwright's `page.request` (inherits browser session)
- [x] Test: Verify API calls have correct authentication

### 4. Naukri Auto-Apply Module (`naukri_apply.py`)
- [x] Implement `apply_to_job(page, job, profile, config, detailed_profile)` - Main orchestrator
- [x] Implement `get_questions_from_response(response)` - Parse questionnaire
- [x] Implement `navigate_to_job(page, url)` - Go to job detail
- [x] Implement `check_already_applied(page)` - Detect "Applied" badge
- [x] Implement `wait_for_submission(page, timeout)` - Wait for auto-submit
- [x] Implement `verify_application_applied(page)` - Detect success/failure
- [x] Add random delays between /respond calls
- [x] Handle API errors: log and mark as failed
- [x] Test: Manual test with one job application

### 5. LLM Batch Answering
- [x] Implement `get_llm_answers(questions, profile, config, detailed_profile)` in `naukri_apply.py`
- [x] Handle LLM errors: retry once, then mark failed
- [x] Test: Verify LLM returns valid answers for all question types

### 6. Apply Jobs Node (LangGraph)
- [x] Add `apply_jobs_node(state)` in `src/job_hunter/graph/nodes.py`
- [x] Filter jobs where `match_score >= apply_threshold` and `apply_status == "Pending"`
- [x] Implement user prompt: "Apply to '{title}' at {company}? [y/n/q]"
- [x] Handle user inputs: y=apply, n=skip, q=quit
- [x] Track `applied_count`, `failed_count`, `skipped_count`
- [x] Update job's `apply_status` after each attempt
- [x] Implement retry logic (1 retry on failure with 5s wait)
- [x] Call `apply_to_job()` for each user-confirmed job
- [x] Update workflow in `src/job_hunter/graph/workflow.py` to add new node

### 7. CSV Export Enhancement
- [x] Add `apply_timestamp` column to CSV export in `src/job_hunter/export/csv_export.py`
- [x] Add `apply_error` column for failure details
- [x] Update `apply_status` values: Applied, Failed, Skipped, Already Applied
- [x] Re-export CSV with updated statuses after apply loop completes
- [x] Test: Verify CSV shows correct status after apply run

### 8. Config & State Updates
- [x] Add `auto_apply_config` to `JobHunterState` in `src/job_hunter/graph/state.py`
- [x] Ensure config loads correctly
- [x] Verify: config loads from user.yaml

### 9. End-to-End Validation
- [x] Run pipeline with auto_apply disabled - confirm no changes to behavior
- [x] Enable auto_apply in config, run pipeline with threshold set to low value (e.g., 30)
- [x] Confirm user prompted for each job above threshold
- [x] Test apply flow: y → apply → success → CSV shows "Applied"
- [x] Test skip: n → CSV shows "Skipped"
- [x] Test quit: q → remaining jobs stay "Pending"
- [x] Test retry on failure: first attempt fails → retry → success/fail
- [x] Verify batch screening: all questions answered via single LLM call

### 10. Documentation
- [x] Update `specs/status.md` - mark Phase 2b as in-progress
- [x] Add Phase 2b entry to `specs/changelog/2026-04.md`

---

## Implementation Notes (API-Based)

- **API-based approach**: Use Naukri's /apply and /respond APIs instead of browser form filling
- **No contenteditable handling needed**: API calls work reliably
- **No Save/Next clicking**: API handles state transitions
- **Job ID**: Extract from existing job data (not URL parsing)
- **Authentication**: Use Playwright's page.request (inherits browser session)
- **Batch LLM**: One call for all questions
- **Auto-submit**: Browser auto-submits after all /respond calls complete
- **Success detection**: Check for "Thank for your response" in sidebar

---

## Testing Checklist

| Test | Expected Result |
|------|-----------------|
| Auto-apply disabled | Pipeline works as Phase 1 (no apply prompts) |
| Auto-apply enabled | User prompted for each job above threshold |
| y (apply) → success | CSV shows "Applied", apply_timestamp set |
| y (apply) → failure | CSV shows "Failed", apply_error with reason |
| n (skip) | CSV shows "Skipped" |
| q (quit) | Remaining jobs stay "Pending" |
| Already applied | CSV shows "Already Applied" |
| Batch screening | All form questions answered in one LLM call |

---

## Files Created/Modified

| File | Change |
|------|--------|
| `src/job_hunter/apply/__init__.py` | New package init |
| `src/job_hunter/apply/api.py` | New - API client (/apply, /respond) |
| `src/job_hunter/apply/client.py` | New - Session management |
| `src/job_hunter/apply/naukri_apply.py` | New - Auto-apply orchestrator |
| `src/job_hunter/graph/nodes.py` | Add apply_jobs_node |
| `src/job_hunter/graph/workflow.py` | Add node to workflow |
| `src/job_hunter/graph/state.py` | Add auto_apply_config to state |
| `src/job_hunter/export/csv_export.py` | Add apply columns |
