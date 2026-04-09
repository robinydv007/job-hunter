# Phase 2b — Plan: Auto-Apply

## Status: NOT STARTED - Replanning after implementation challenges

## Implementation Approach

Build the auto-apply flow after the scoring phase in the LangGraph pipeline. Use **state machine approach** (read-analyze-act loop) instead of original batch screening due to Naukri's sequential question display.

---

### Pipeline: Extended StateGraph

```
load_config → parse_resume → search_jobs → score_jobs → filter_shortlist → apply_jobs → export_csv → END
```

New node `apply_jobs` added after `filter_shortlist` and before `export_csv`.

---

### Module Design

#### 1. Apply Package (`src/job_hunter/apply/`)

**Package structure:**
```
apply/
├── __init__.py       # Package exports
├── analyzer.py       # LLM analysis of sidebar content → action decision
├── actions.py        # Execute actions (fill, select, click, upload, submit)
├── storage.py        # Store learned field mappings for optimization
└── naukri_apply.py   # Main orchestrator - read-analyze-act loop
```

**Key Functions:**

- `analyzer.py`:
  - `get_sidebar_content(page)` - Extract text, buttons, inputs from sidebar
  - `analyze_sidebar(content, profile, config)` - LLM decides action
  - `check_for_submit_state(content)` - Quick check if ready to submit

- `actions.py`:
  - `fill_field_action(page, field_label, answer)` - Handles input AND contenteditable
  - `select_option_action(page, field_label, answer)` - Click matching option div
  - `upload_resume_action(page, resume_path)` - Upload with skip fallback
  - `click_button_action(page, button_text)` - Click by text
  - `submit_action(page)` - Click final submit
  - `execute_action(page, decision)` - Route to appropriate action

- `naukri_apply.py`:
  - `apply_to_job(page, job, config, resume_path)` - Main orchestrator
  - `navigate_to_job(page, url)` - Go to job detail
  - `check_already_applied(page)` - Detect "Applied" badge
  - `open_apply_sidebar(page)` - Click apply button to open sidebar

- `storage.py`:
  - `load_field_mappings()` - Load from JSON
  - `save_field_mappings(mappings)` - Save to JSON

#### 2. Apply Jobs Node (`graph/nodes.py`)

**Responsibilities:**
- Filter jobs above `apply_threshold` with `apply_status == "Pending"`
- Prompt user for each job: "Apply to '{title}' at {company}? [y/n/q]"
- Call `apply_to_job()` for confirmed jobs
- Update job's `apply_status` after each attempt
- Track counts: applied, failed, skipped

**User interaction:**
- `y` - Apply to this job
- `n` - Skip this job (mark as Skipped)
- `q` - Quit apply loop (remaining jobs stay Pending)

**Confirmation Flow:**
- User confirms at START of each job (not after filling all fields)
- Before clicking final Submit button, user is asked again to review
- This allows user to see what's been filled before final submission

#### 3. CSV Enhancement (`export/csv_export.py`)

**Changes:**
- Add `apply_timestamp` column
- Add `apply_error` column
- Update `apply_status` values: Applied, Failed, Skipped, Already Applied
- Re-export CSV after apply phase with updated statuses

---

### Data Flow: State Machine Approach

```
filter_shortlist returns shortlisted jobs
         │
         ▼
apply_jobs_node(state)
         │
         ▼
   ┌─────────────────────────────┐
   │ For each job >= threshold: │
   │   Prompt user (y/n/q)       │
   └─────────────────────────────┘
         │
    ┌────┴────┐
    │         │
   Apply    Skip
    │         │
    ▼         ▼
apply_to_job  update status to "Skipped"
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ STATE MACHINE LOOP (max 20 iterations):            │
│  1. Read sidebar content (.chatbot_DrawerContent)   │
│  2. Send to LLM → get action + answer               │
│  3. Execute action                                   │
│  4. If fill/select → auto-click Save/Next           │
│  5. Check if submit ready                           │
│  6. If ready → ask user confirmation → submit      │
│  7. Detect success/failure → break                  │
└─────────────────────────────────────────────────────┘
    │
    ▼
update apply_status → Applied/Failed
         │
         ▼
All jobs processed → export_csv (with updated statuses)
```

---

### Batch Screening vs State Machine

**Original Plan (Batch):**
```
1. Scrape ALL questions from form
2. Single LLM call with all questions
3. Fill all answers
4. Submit
```
**Problem:** Naukri shows questions ONE AT A TIME, not all at once.

**New Approach (State Machine):**
```
Loop:
  1. Read current sidebar state
  2. LLM analyzes and decides action
  3. Execute action
  4. Click Save/Next if needed
  5. Repeat until submit
```
**Benefit:** Handles dynamic sequential form flow

---

### LLM Action Types

The analyzer should return one of these actions:

| Action | Description | Example |
|--------|-------------|---------|
| `fill_field` | Fill text in input or contenteditable | Current CTC, Expected CTC |
| `select_option` | Click matching option (radio/div) | Notice Period: "Immediate" |
| `upload_resume` | Upload resume file | Resume upload |
| `click_button` | Click a button by text | "Save", "Next", "Continue" |
| `skip` | Skip this question | "I'll do it later" for resume |
| `submit` | Click final submit button | Application submission |
| `wait` | Wait and retry | Form still loading |

---

### Dependencies

- Phase 2a (Detailed Profile) complete
- `profile_detailed.yaml` available
- `screening.yaml` loaded in config
- `resume_path` configured in user.yaml
- LangGraph workflow updated with new node
- **Naukri search must be working** (currently blocked)

---

### Risks Identified

| Risk | Mitigation |
|------|------------|
| Naukri search blocking | Must resolve before Phase 2b can work |
| Naukri anti-bot triggers | Non-headless mode, random delays, user can intervene |
| Form fields change | Store learned mappings, log selectors used |
| LLM rate limits | One call per question (sequential nature) |
| Resume upload fails | "I'll do it later" skip option |
| Submit button blocked | Handle chatbot overlay, wait for it to disappear |

---

### Effort

~3-4 days for Phase 2b - primarily browser automation and testing.

**Note:** Naukri search must be fixed first (separate issue from Phase 2b).