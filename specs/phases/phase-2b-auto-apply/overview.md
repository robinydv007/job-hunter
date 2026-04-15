# Phase 2b — Overview: Auto-Apply

**Status:** IN PROGRESS - Implementation complete, testing  
**Target:** TBD  
**Release:** v0.2.1 (planned)

---

## Goal

Implement auto-apply functionality for Naukri jobs above the configured threshold using Naukri's internal APIs, with intelligent batch screening question answering.

---

## Scope

1. **API-based auto-apply** — Use Naukri's `/apply` and `/respond` APIs instead of browser form filling
2. **Batch Screening** — Get all questions via API, then single LLM call for all answers
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
                            │         API-Based Apply Flow           │
                            │                                        │
                            │  1. Click Apply → POST /apply           │
                            │  2. Get ALL questions from response   │
                            │  3. LLM batch answer (single call)    │
                            │  4. POST /respond for each answer      │
                            │  5. Browser auto-submits              │
                            └────────────────────────────────────────┘
```

---

## Key Discovery: Naukri API Flow

Through network inspection (DevTools → Network tab), discovered that Naukri uses APIs instead of browser form filling:

### Flow:
```
1. Click "Apply" button (browser) → POST /apply → returns ALL questions
2. For each question → POST /respond with answer
3. After all /respond calls → browser auto-calls POST /apply with ALL answers → submits!
```

### Benefits over Browser Automation:
- **No contenteditable issues** - API calls work reliably
- **No need to click Save/Next** - API handles state
- **More stable** - API structure doesn't change with UI updates
- **Batch LLM** - One call for all answers

---

## API Details (Verified via Network Inspection)

### API Flow Verified: 9 API Calls Sequence

| # | API | Purpose |
|---|-----|---------|
| 1 | `POST /apply` | Get ALL questions at once (returns 7 questions) |
| 2-7 | `POST /respond` | Answer each question sequentially (6 calls) |
| 8 | `POST /respond` | Final submit trigger (empty answer) |
| 9 | `POST /apply` | Auto-submit with ALL answers in payload → SUCCESS! |

### 1. `/apply` - Get Questions

**URL:** `POST https://www.naukri.com/cloudgateway-workflow/workflow-services/apply-workflow/v1/apply`

**Payload:**
```json
{
  "strJobsarr": ["250326025777"],
  "logstr": "—cluster-11-F-0-1—17757311497391557_1—",
  "flowtype": "show",
  "chatBotSDK": true,
  "applyTypeId": "107",
  "applySrc": "cluster",
  "sid": "17757311497391557_1",
  "mandatory_skills": ["Typescript"],
  "optional_skills": ["Langchain", "Fullstack Development", "Node.Js", "React.Js", "Ai Platform"]
}
```

**Response:**
```json
{
  "statusCode": 0,
  "jobs": [{
    "jobId": "250326025777",
    "questionnaire": [
      {"questionId": "38621838", "questionName": "How many years of experience do you have in Typescript?", "questionType": "Text Box", "isMandatory": true},
      ...
    ],
    "chatbotResponse": {
      "conversation_session_id": "d26cbab0-8c8d-43c6-9699-719ceac2e461"
    }
  }]
}
```

### 2. `/respond` - Send Each Answer

**URL:** `POST https://www.naukri.com/cloudgateway-chatbot/chatbot-services/botapi/v5/respond`

**Payload:**
```json
{
  "input": {
    "text": ["5"],           // The answer
    "id": ["-1"]
  },
  "appName": "250326025777_apply",
  "conversation": "250326025777_apply",
  "domain": "Naukri",
  "channel": "web",
  "status": "Fresh",
  "deviceType": "WEB"
}
```

**Response:**
```json
{
  "speechResponse": [{"response": "Next question...", "type": "text"}],
  "isLeafNode": false,           // false = more questions, true = last question done
  "applyData": {
    "250326025777": {
      "answers": {"38621838": "5", "38621840": "1"}
    }
  },
  "conversation_session_id": "d26cbab0-8c8d-43c6-9699-719ceac2e461"
}
```

### 3. Final `/apply` - Auto-submit

After all `/respond` calls complete, browser auto-calls `/apply` with all answers:

**Payload:**
```json
{
  "strJobsarr": ["250326025777"],
  "applyData": {
    "250326025777": {
      "answers": {
        "38621838": "1",
        "38621840": "1",
        "38621842": "5",
        "38621844": "6",
        "38621846": "22",
        "38621848": "30",
        "38621850": "Immediate"
      }
    }
  }
}
```

**Success Response:**
```json
{
  "statusCode": 0,
  "jobs": [{
    "status": 200,
    "message": "You have successfully applied to this job.",
    "jobId": "250326025777"
  }],
  "applyStatus": {"250326025777": 200}
}
```

### Key Implementation Details

1. **Job ID**: From job data, not URL parsing
2. **appName**: `{jobId}_apply` (e.g., `250326025777_apply`)
3. **conversation**: Same as appName
4. **Progress tracking**: `isLeafNode: true` signals last question answered
5. **Success detection**: Final `/apply` returns `status: 200`, `message: "You have successfully applied to this job."`

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

## Batch Screening Handler (API-Based)

**Approach**: Get all questions via `/apply` API, then send batch to LLM with both profile and detailed profile.

**Available context**:
- Basic profile: name, skills, experience, roles
- Detailed profile (from Phase 2a): tech_experience years, achievements, challenges, interests
- Screening config: from screening.yaml

```python
async def answer_screening_batch(questions: list[dict], profile, config, detailed_profile) -> dict[str, str]:
    """Answer all screening questions in a single LLM call."""
    
    # Extract questions from API response
    question_list = [
        {"id": q["questionId"], "name": q["questionName"]}
        for q in questions
    ]
    
    # Send ALL questions to LLM in one call
    prompt = f"""You are a job seeker filling out a job application form.

Answer ALL questions concisely and professionally. Return a JSON object
mapping questionId to your answer.

---
PROFILE:
- Name: {profile.name}
- Experience: {profile.total_experience_years} years
- Skills: {', '.join(profile.skills[:10])}

TECH STACK EXPERIENCE:
{chr(10).join(f"- {k}: {v} years" for k, v in list(detailed_profile.get('tech_experience', {}).items())[:5])}

SCREENING CONFIG (from screening.yaml):
- Notice Period: {config.screening_answers.notice_period}
- Expected CTC: {config.screening_answers.expected_ctc_lpa} LPA
- Current CTC: {config.screening_answers.current_ctc_lpa} LPA
- Relocation: {config.screening_answers.willing_to_relocate}
- Reason for Change: {config.screening_answers.reason_for_change}

---
QUESTIONS TO ANSWER:
{chr(10).join(f"- {q['id']}: {q['name']}" for q in question_list)}

Output as JSON (questionId → answer):
{{"38621838": "5", "38621846": "12", ...}}"""
    
    answers = llm.generate_json(prompt)
    return answers
```

---

## Naukri Auto-Apply Module

**File:** `src/job_hunter/apply/naukri_apply.py`

| Function | Description |
|----------|-------------|
| `apply_to_job(page, job, profile, config)` | Main orchestrator - full flow |
| `get_questions(page, job_id)` | Call /apply API, return questions |
| `send_response(page, job_id, question_id, answer)` | Call /respond API |
| `navigate_to_job(page, url)` | Go to job detail page, wait for load |
| `check_already_applied(page)` | Detect "Applied" badge, return boolean |
| `wait_for_submission(page)` | Wait for auto-submit, detect success/failure |

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
| API error response | Log specific error, mark `Failed`, continue |
| Browser session expired | Alert user, offer to re-login |
| Resume required in questionnaire | Some jobs may require resume - handled separately |

---

## Deliverables

| Deliverable | File(s) | Description |
|-------------|---------|-------------|
| Apply package | `src/job_hunter/apply/` | New package with modules |
| API client | `src/job_hunter/apply/api.py` | /apply and /respond API calls |
| Apply orchestrator | `src/job_hunter/apply/naukri_apply.py` | Main flow orchestration |
| Apply node | `src/job_hunter/graph/nodes.py` | LangGraph apply node |
| CSV enhancement | `src/job_hunter/export/csv_export.py` | Add apply status columns |

---

## Acceptance Criteria

- [ ] `apply_jobs_node` prompts for each job above threshold
- [ ] User can type `y` (apply), `n` (skip), `q` (quit)
- [ ] Successfully applied jobs show `Applied` status in CSV
- [ ] Failed applications show `Failed` with error message in CSV
- [ ] Batch screening answers all questions in single LLM call
- [ ] Auto-apply can be disabled via config (`enabled: false`)

---

## Exit Criteria

User can run `job-hunter run`, receive a shortlist, confirm apply for selected jobs, and see their applications submitted on Naukri — with statuses tracked in the CSV output.

---

## Known Risks

| Risk | Mitigation |
|------|------------|
| Naukri search blocking | Must resolve before Phase 2b can work (ENH-016) |
| API changes | Log API payloads/responses for debugging |
| Session expiry | Handle 401 errors, offer re-login |
| Resume required | Some jobs may require resume upload separately |
| Already applied | Check "Applied" badge before attempting |

---

## File Structure

```
src/job_hunter/
├── apply/
│   ├── __init__.py          # Package init
│   ├── api.py               # API client (/apply, /respond)
│   ├── client.py            # Session management
│   └── naukri_apply.py      # Main orchestrator
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

---

## Exploration Script

Before full implementation, create exploration script to verify API flow:
```
scripts/explore_apply_api.py
```

This will:
1. Login to Naukri
2. Navigate to a job
3. Click Apply button
4. Intercept all API responses
5. Print captured data for verification
