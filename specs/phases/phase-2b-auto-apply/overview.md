# Phase 2b — Overview: Auto-Apply

**Status:** In Progress  
**Target:** TBD  
**Release:** v0.2.1 (planned)

---

## Goal

Implement auto-apply functionality for Naukri jobs above the configured threshold, with intelligent batch screening question answering.

---

## Scope

1. **Auto-apply engine** — Navigate to job page, fill form, upload resume, submit
2. **Batch Screening** — Scrape all questions from form first, then single LLM call for all answers
3. **Enhanced CSV tracking** — Apply status updates (Applied/Failed/Skipped/Already Applied)

---

## Why This Matters

Phase 2a provides enhanced profile data. Phase 2b converts the shortlist into actual applications — completing the "job hunting" loop. Without auto-apply, the agent is a research tool; with it, it becomes a true job hunting assistant.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Phase 2b Architecture                            │
└─────────────────────────────────────────────────────────────────────┘

     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
     │ score_jobs   │ ──▶ │filter_shortlist│ ──▶ │ apply_jobs   │
     │    Node      │     │    Node       │     │    Node      │
     └──────────────┘     └──────────────┘     └──────────────┘
                                                      │
                                                      ▼
                              ┌────────────────────────────────────────┐
                              │         Apply Flow                     │
                              │  ┌────────────┐  ┌────────────────┐   │
                              │  │navigate_to │─▶│check_already   │   │
                              │  │job detail  │  │applied         │   │
                              │  └────────────┘  └────────────────┘   │
                              │         │                │            │
                              │         ▼                ▼            │
                              │  ┌─────────────────────────────────┐  │
                              │  │     Fill Form + Screening       │  │
                              │  │  ┌───────────┐ ┌─────────────┐  │  │
                              │  │  │fill_basic │ │answer_batch │  │  │
                              │  │  │_info      │ │_questions   │  │  │
                              │  │  └───────────┘ └─────────────┘  │  │
                              │  └─────────────────────────────────┘  │
                              │                │                      │
                              │                ▼                      │
                              │  ┌────────────────┐  ┌────────────┐  │
                              │  │upload_resume   │─▶│submit_apply│  │
                              │  └────────────────┘  └────────────┘  │
                              └────────────────────────────────────────┘

     ┌──────────────────────────────────────────────────────────────────┐
     │              Batch Screening: Single LLM Call                   │
     │                                                                  │
     │   1. Scrape ALL form questions from page                        │
     │   2. Send all questions to LLM in ONE call                       │
     │   3. Receive all answers in response                             │
     │   4. Fill form fields                                            │
     └──────────────────────────────────────────────────────────────────┘
```

---

## Apply Jobs Node

**File:** `src/job_hunter/graph/nodes.py`

| Responsibility | Description |
|---------------|-------------|
| Filter jobs above `apply_threshold` | Select jobs where `match_score >= 75` (default) |
| User confirmation prompt | For each job: "Apply to '{title}' at {company}? [y/n/q]" |
| Apply loop management | Track applied/failed/skipped counts |
| Update CSV status | Write apply results back to CSV |

**User Interaction Flow:**

```
Jobs above threshold: 5

1. "Apply to 'Senior Engineer' at Acme Corp? [y/n/q]: " y
   → Attempting apply...
   → Success! Marked 'Applied'

2. "Apply to 'Tech Lead' at Beta Inc? [y/n/q]: " n
   → Marked 'Skipped'

3. "Apply to 'AI Engineer' at Gamma Ltd? [y/n/q]: " q
   → Quit. Remaining 2 jobs stay 'Pending'
```

---

## Batch Screening Handler

**Approach**: Instead of answering one question at a time, scrape all questions first, then send batch to LLM with both profile and detailed profile.

**Available context**:
- Basic profile: name, skills, experience, roles
- Detailed profile (from Phase 2a): tech_experience years, achievements, challenges, interests
- Screening config: from screening.yaml

```python
async def answer_screening_batch(page, profile, config, detailed_profile) -> dict[str, str]:
    """Answer all screening questions in a single LLM call."""
    
    # Step 1: Scrape all questions from the form
    questions = []
    inputs = await page.query_selector_all("input, select, textarea")
    for inp in inputs:
        label = await _get_field_label(inp, page)
        if label:
            questions.append(label)
    
    # Step 2: Send ALL questions to LLM in one call (with profile + detailed_profile)
    prompt = f"""You are a job seeker filling out a job application form.

Answer ALL questions concisely and professionally. Return a JSON object
mapping each question to its answer.

---
PROFILE:
- Name: {profile.name}
- Experience: {profile.total_experience_years} years
- Skills: {', '.join(profile.skills[:10])}
- Current Role: {profile.past_roles[0] if profile.past_roles else 'N/A'}

TECH STACK EXPERIENCE:
{chr(10).join(f"- {k}: {v} years" for k, v in list(detailed_profile.get('tech_experience', {}).items())[:5])}

ACHIEVEMENTS:
{chr(10).join(f"- {a}" for a in detailed_profile.get('achievements', [])[:3])}

SCREENING CONFIG (from screening.yaml):
- Notice Period: {config.screening_answers.notice_period}
- Expected CTC: {config.screening_answers.expected_ctc_lpa} LPA
- Current CTC: {config.screening_answers.current_ctc_lpa} LPA
- Relocation: {config.screening_answers.willing_to_relocate}
- Reason for Change: {config.screening_answers.reason_for_change}

EXTENDED ANSWERS (from profile_detailed.yaml):
- Strengths: {detailed_profile.get('screening_answers_extended', {}).get('strengths', '')}
- Weaknesses: {detailed_profile.get('screening_answers_extended', {}).get('weaknesses', '')}

---
QUESTIONS TO ANSWER:
{chr(10).join(f"{i+1}. {q}" for i, q in enumerate(questions))}

Output as JSON:
{{
  "question_1": "answer",
  "question_2": "answer",
  ...
}}"""
    
    answers = llm.generate_json(prompt)
    return answers
```

---

## Naukri Auto-Apply Module

**File:** `src/job_hunter/apply/naukri_apply.py`

| Function | Description |
|----------|-------------|
| `navigate_to_job(page, url)` | Go to job detail page, wait for load |
| `check_already_applied(page)` | Detect "Applied" badge, return boolean |
| `fill_basic_info(page, profile)` | Fill name, email, phone from profile |
| `upload_resume(page, resume_path)` | Find file input, upload from absolute path |
| `answer_screening_batch(page, ...)` | Batch answer all questions via single LLM call |
| `submit_application(page)` | Click submit, capture success/failure |
| `apply_to_job(page, job, ...)` | Orchestrator: full apply flow |

---

## CSV Schema Enhancement

| Column | Description | Phase 1 | Phase 2b |
|--------|-------------|---------|----------|
| `apply_status` | Application outcome | `Pending` only | `Pending`/`Applied`/`Failed`/`Skipped`/`Already Applied` |
| `apply_timestamp` | When applied | — | Timestamp |
| `apply_error` | Error message if failed | — | Error details |

---

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Resume file not found | Error logged, job marked `Failed`, continue to next |
| Network timeout during apply | Retry once (5s wait), then mark `Failed` |
| Naukri shows CAPTCHA | Pause, alert user: "Please solve CAPTCHA manually, then press Enter" |
| Already applied (detected) | Mark `Already Applied`, no retry |
| Form validation errors | Log specific error, mark `Failed`, continue |
| Browser session expired | Alert user, offer to re-login |
| Apply button not found | Log error, mark `Failed`, continue |

---

## Deliverables

| Deliverable | File(s) | Description |
|-------------|---------|-------------|
| Apply package | `src/job_hunter/apply/` | New package with modules |
| Batch screening | `src/job_hunter/apply/screening.py` | Single LLM call for all questions |
| Apply node | `src/job_hunter/graph/nodes.py` | LangGraph apply node |
| CSV enhancement | `src/job_hunter/export/csv_export.py` | Add apply status columns |

---

## Acceptance Criteria

- [ ] `apply_jobs_node` prompts for each job above threshold
- [ ] User can type `y` (apply), `n` (skip), `q` (quit)
- [ ] Successfully applied jobs show `Applied` status in CSV
- [ ] Failed applications show `Failed` with error message in CSV
- [ ] Batch screening answers all questions in single LLM call
- [ ] Resume uploaded correctly from configured path
- [ ] Auto-apply can be disabled via config (`enabled: false`)

---

## Exit Criteria

User can run `job-hunter run`, receive a shortlist, confirm apply for selected jobs, and see their applications submitted on Naukri — with statuses tracked in the CSV output.

---

## Known Risks

| Risk | Mitigation |
|------|------------|
| Naukri anti-bot during apply | Use non-headless browser (user can see), add random delays |
| Form field selectors break | Log selectors used, make error messages clear for debugging |
| LLM rate limits on screening | Batch all questions to minimize calls |
| Resume upload fails | Show clear error, allow retry or manual upload |

---

## File Structure

```
src/job_hunter/
├── apply/
│   ├── __init__.py          # Package init
│   ├── naukri_apply.py      # Auto-apply logic
│   └── screening.py         # Batch screening handler
├── graph/
│   └── nodes.py             # ADD: apply_jobs_node
└── export/
    └── csv_export.py        # MODIFY: add apply status columns
```

---

## Prerequisites

- Phase 2a (Detailed Profile) is complete
- `profile_detailed.yaml` exists with extended profile data
- `screening.yaml` loaded in config
- Resume path configured in user.yaml
- ENH-017 (pipeline reordering) assumed complete before Phase 2b starts

## Actual Naukri Apply Flow (Exploration Results)

During exploration with Playwright on Naukri.com, the following was discovered:

### Apply Trigger
- **Selector:** `.apply-button`
- **Behavior:** Clicking opens a sidebar on the RIGHT side of the screen (not a new page or modal)

### Sidebar Form Fields (for logged-in users)
- Resume upload: `input[type="file"]`
- Experience dropdown: `#experienceDD`
- Location input field

### Key Implementation Notes
- Apply is sidebar-based, not page-based
- For logged-in users, most fields are pre-filled with profile data
- Resume upload requires absolute file path
- Need to handle sidebar open/close states