# Phase 2b — Plan: Auto-Apply

## Implementation Approach

Build the auto-apply flow after the scoring phase in the LangGraph pipeline. Use batch screening to minimize LLM calls.

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
├── screening.py     # Batch screening handler
└── naukri_apply.py  # Naukri auto-apply logic
```

**screening.py:**
- `scrape_all_questions(page)` - Find all form fields with labels
- `answer_screening_batch(page, profile, config, detailed_profile)` - Single LLM call
- `fill_form_answers(page, answers)` - Fill all answered fields

**naukri_apply.py:**
- `navigate_to_job(page, url)` - Go to job detail
- `check_already_applied(page)` - Detect "Applied" badge
- `fill_basic_info(page, profile)` - Name, email, phone
- `upload_resume(page, resume_path)` - Upload from configured path
- `submit_application(page)` - Submit and detect result
- `apply_to_job(page, job, ...)` - Orchestrator function

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

#### 3. CSV Enhancement (`export/csv_export.py`)

**Changes:**
- Add `apply_timestamp` column
- Add `apply_error` column
- Update `apply_status` values: Applied, Failed, Skipped, Already Applied
- Re-export CSV after apply phase with updated statuses

---

### Data Flow

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
┌─────────────────────────────┐
│ 1. Navigate to job URL      │
│ 2. Check already applied   │
│ 3. Fill basic info         │
│ 4. Upload resume           │
│ 5. Batch screening (LLM)  │
│ 6. Submit                 │
│ 7. Detect result          │
└─────────────────────────────┘
    │
    ▼
update apply_status → Applied/Failed
         │
         ▼
All jobs processed → export_csv (with updated statuses)
```

---

### Batch Screening Flow

```
Page loads job application form
         │
         ▼
scrape_all_questions()
- Find all <input>, <select>, <textarea>
- Extract labels for each field
- Return list of question strings
         │
         ▼
answer_screening_batch()
- Build prompt with ALL questions
- Include profile, detailed_profile, screening.yaml context
- Single LLM call → JSON with all answers
         │
         ▼
fill_form_answers()
- Iterate through answered fields
- Handle: text inputs, dropdowns, radio buttons, textareas
- Return success/failure
```

---

### Dependencies

- Phase 2a (Detailed Profile) complete
- `profile_detailed.yaml` available
- `screening.yaml` loaded in config
- `resume_path` configured in user.yaml
- LangGraph workflow updated with new node

---

### Risks Identified

| Risk | Mitigation |
|------|------------|
| Naukri anti-bot triggers | Non-headless mode, random delays, user can intervene |
| Form fields change | Log selectors used, clear error messages |
| LLM rate limits | Single batch call instead of per-question |
| Resume upload fails | Clear error, allow manual retry |

---

## Effort

~3-4 days for Phase 2b - primarily browser automation and testing.