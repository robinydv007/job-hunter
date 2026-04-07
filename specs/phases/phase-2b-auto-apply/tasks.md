# Phase 2b — Tasks: Auto-Apply

> **Status: PLANNED** — To start after Phase 2a

## Prerequisites (Must complete Phase 2a first)

- [ ] `config/screening.yaml` created and loaded
- [ ] `config/user.yaml` updated (screening_answers removed, resume_path added with default resume.pdf)
- [ ] Single LLM call extracts both basic and detailed profiles
- [ ] `data/profile_detailed.yaml` created with extended profile (tech_experience, achievements, etc.)
- [ ] Resume change detection works
- [ ] Subsequent runs use cached profiles
- [ ] `load_profile_with_detailed()` available to get both profile + detailed together

## Task Checklist

### 1. Apply Package Setup
- [ ] Create `src/job_hunter/apply/__init__.py` package init
- [ ] Create `src/job_hunter/apply/screening.py` for batch screening
- [ ] Create `src/job_hunter/apply/naukri_apply.py` for auto-apply logic

### 2. Batch Screening Handler
- [ ] Implement `scrape_all_questions(page)` in `screening.py`
  - Find all input/select/textarea fields with labels
  - Return list of question strings
- [ ] Implement `answer_screening_batch(page, profile, config, detailed_profile)` in `screening.py`
  - Single LLM call with all questions
  - Returns dict mapping question → answer
- [ ] Implement `fill_form_answers(page, answers)` in `screening.py`
  - Fill all answered fields in the form
  - Handle dropdown selects, radio buttons, text inputs, textareas
- [ ] Test: Run on sample Naukri form to verify question extraction

### 3. Naukri Auto-Apply Module
- [ ] Implement `navigate_to_job(page, url)` in `naukri_apply.py`
- [ ] Implement `check_already_applied(page)` - detect "Applied" badge
- [ ] Implement `fill_basic_info(page, profile)` - name, email, phone
- [ ] Implement `upload_resume(page, resume_path)` - file input upload
- [ ] Implement `find_and_click_apply_button(page)` - locate submit trigger
- [ ] Implement `submit_application(page)` - click submit, detect success/failure
- [ ] Implement `apply_to_job(page, job, profile, config, detailed_profile)` orchestrator
- [ ] Add random delays between steps to avoid bot detection
- [ ] Handle CAPTCHA: pause and prompt user to solve manually
- [ ] Handle form validation errors: log and mark as failed
- [ ] Test: Manual test with one job application

### 4. Apply Jobs Node (LangGraph)
- [ ] Add `apply_jobs_node(state)` in `src/job_hunter/graph/nodes.py`
- [ ] Filter jobs where `match_score >= apply_threshold` and `apply_status == "Pending"`
- [ ] Implement user prompt: "Apply to '{title}' at {company}? [y/n/q]"
- [ ] Handle user inputs: y=apply, n=skip, q=quit
- [ ] Track `applied_count`, `failed_count`, `skipped_count`
- [ ] Update job's `apply_status` after each attempt
- [ ] Implement retry logic (1 retry on failure with 5s wait)
- [ ] Call `apply_to_job()` for each user-confirmed job
- [ ] Update workflow in `src/job_hunter/graph/workflow.py` to add new node

### 5. CSV Export Enhancement
- [ ] Add `apply_timestamp` column to CSV export in `src/job_hunter/export/csv_export.py`
- [ ] Add `apply_error` column for failure details
- [ ] Update `apply_status` values: Applied, Failed, Skipped, Already Applied
- [ ] Re-export CSV with updated statuses after apply loop completes
- [ ] Test: Verify CSV shows correct status after apply run

### 6. Config & State Updates
- [ ] Add `auto_apply_config` to `JobHunterState` in `src/job_hunter/graph/state.py`
- [ ] Ensure `require_confirmation: true` defaults in config
- [ ] Ensure `enabled: false` defaults in config (user enables when ready)
- [ ] Verify: config loads correctly from screening.yaml

### 7. End-to-End Validation
- [ ] Run pipeline with auto_apply disabled - confirm no changes to behavior
- [ ] Enable auto_apply in config, run pipeline with threshold set to low value (e.g., 30)
- [ ] Confirm user prompted for each job above threshold
- [ ] Test apply flow: y → apply → success → CSV shows "Applied"
- [ ] Test skip: n → CSV shows "Skipped"
- [ ] Test quit: q → remaining jobs stay "Pending"
- [ ] Test retry on failure: first attempt fails → retry → success/fail
- [ ] Verify batch screening: all questions answered via single LLM call

### 8. Documentation
- [ ] Update `specs/status.md` - mark Phase 2b as in-progress
- [ ] Add Phase 2b entry to `specs/changelog/YYYY-MM.md`

---

## Implementation Notes

- Batch screening: scrape all questions first, then single LLM call for all answers
- User confirms each application - no batch mode in Phase 2b
- Auto-apply disabled by default - user explicitly enables via config
- Resume uploaded from configured path in user.yaml

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
| `src/job_hunter/apply/screening.py` | New - batch screening handler |
| `src/job_hunter/apply/naukri_apply.py` | New - auto-apply logic |
| `src/job_hunter/graph/nodes.py` | Add apply_jobs_node |
| `src/job_hunter/graph/workflow.py` | Add node to workflow |
| `src/job_hunter/graph/state.py` | Add auto_apply_config to state |
| `src/job_hunter/export/csv_export.py` | Add apply columns |