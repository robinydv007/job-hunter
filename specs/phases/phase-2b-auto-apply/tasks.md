# Phase 2b — Tasks: Auto-Apply

> **Status: NOT STARTED** — Replanning with API-based approach

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
- [ ] Run `scripts/explore_apply_api.py` to verify API flow
- [ ] Capture and analyze API responses
- [ ] Verify /apply returns all questions at once
- [ ] Verify /respond works for each answer
- [ ] Verify browser auto-submits after all responses
- [ ] Document any additional findings

### 1. Apply Package Setup
- [ ] Create `src/job_hunter/apply/__init__.py` package init
- [ ] Create `src/job_hunter/apply/api.py` for API client (/apply and /respond)
- [ ] Create `src/job_hunter/apply/client.py` for session management
- [ ] Create `src/job_hunter/apply/naukri_apply.py` for auto-apply logic

### 2. API Client (`api.py`)
- [ ] Implement `get_questions(page, job_id, skills)` - Call /apply API
  - Extract job_id from job data (not URL parsing)
  - Get mandatory/optional skills from job or empty list
  - Parse questionnaire from response
  - Return list of questions with id, name, type, mandatory
- [ ] Implement `send_response(page, job_id, question_id, answer, app_name)` - Call /respond API
  - Build payload with input.text as answer
  - Handle response to get next question
  - Return response data
- [ ] Implement `extract_conversation_id(response)` - Extract from /apply response
- [ ] Test: Verify API calls work and return expected data

### 3. Session Management (`client.py`)
- [ ] Implement `get_auth_headers(page)` - Extract auth tokens from browser context
  - Or verify page.request can be used directly (inherits session)
- [ ] Test: Verify API calls have correct authentication

### 4. Naukri Auto-Apply Module (`naukri_apply.py`)
- [ ] Implement `apply_to_job(page, job, profile, config, detailed_profile)` - Main orchestrator
  - Step 1: Navigate to job detail page
  - Step 2: Click Apply button to trigger /apply API
  - Step 3: Get questions from intercepted response
  - Step 4: Get LLM answers for all questions (batch)
  - Step 5: Send each answer via /respond API
  - Step 6: Wait for auto-submit (browser calls /apply with all answers)
  - Step 7: Detect success/failure
- [ ] Implement `get_questions_from_response(response)` - Parse questionnaire
- [ ] Implement `navigate_to_job(page, url)` - Go to job detail
- [ ] Implement `check_already_applied(page)` - Detect "Applied" badge
- [ ] Implement `wait_for_submission(page, timeout)` - Wait for auto-submit
  - Check for success message ("Thank for your response")
  - Check for "Applied" badge
- [ ] Implement `detect_submission_result(page)` - Determine if applied successfully
- [ ] Add random delays between /respond calls
- [ ] Handle CAPTCHA: pause and prompt user to solve manually
- [ ] Handle API errors: log and mark as failed
- [ ] Test: Manual test with one job application

### 5. LLM Batch Answering
- [ ] Implement `get_llm_answers(questions, profile, config, detailed_profile)` in `naukri_apply.py`
  - Send all questions to LLM in one call
  - Return dict mapping questionId → answer
- [ ] Handle LLM errors: retry once, then mark failed
- [ ] Test: Verify LLM returns valid answers for all question types

### 6. Apply Jobs Node (LangGraph)
- [ ] Add `apply_jobs_node(state)` in `src/job_hunter/graph/nodes.py`
- [ ] Filter jobs where `match_score >= apply_threshold` and `apply_status == "Pending"`
- [ ] Implement user prompt: "Apply to '{title}' at {company}? [y/n/q]"
- [ ] Handle user inputs: y=apply, n=skip, q=quit
- [ ] Track `applied_count`, `failed_count`, `skipped_count`
- [ ] Update job's `apply_status` after each attempt
- [ ] Implement retry logic (1 retry on failure with 5s wait)
- [ ] Call `apply_to_job()` for each user-confirmed job
- [ ] Update workflow in `src/job_hunter/graph/workflow.py` to add new node

### 7. CSV Export Enhancement
- [ ] Add `apply_timestamp` column to CSV export in `src/job_hunter/export/csv_export.py`
- [ ] Add `apply_error` column for failure details
- [ ] Update `apply_status` values: Applied, Failed, Skipped, Already Applied
- [ ] Re-export CSV with updated statuses after apply loop completes
- [ ] Test: Verify CSV shows correct status after apply run

### 8. Config & State Updates
- [ ] Add `auto_apply_config` to `JobHunterState` in `src/job_hunter/graph/state.py`
  - `enabled: bool` - Whether auto-apply is enabled
  - `threshold: int` - Minimum match score to apply (default 75)
  - `require_confirmation: bool` - Require user confirmation (default true)
- [ ] Ensure config loads correctly
- [ ] Verify: config loads from user.yaml

### 9. End-to-End Validation
- [ ] Run pipeline with auto_apply disabled - confirm no changes to behavior
- [ ] Enable auto_apply in config, run pipeline with threshold set to low value (e.g., 30)
- [ ] Confirm user prompted for each job above threshold
- [ ] Test apply flow: y → apply → success → CSV shows "Applied"
- [ ] Test skip: n → CSV shows "Skipped"
- [ ] Test quit: q → remaining jobs stay "Pending"
- [ ] Test retry on failure: first attempt fails → retry → success/fail
- [ ] Verify batch screening: all questions answered via single LLM call

### 10. Documentation
- [ ] Update `specs/status.md` - mark Phase 2b as in-progress
- [ ] Add Phase 2b entry to `specs/changelog/2026-04.md`

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
