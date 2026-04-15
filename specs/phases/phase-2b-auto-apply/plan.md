# Phase 2b — Plan: Auto-Apply

## Status: NOT STARTED - Replanning with API-based approach

## Implementation Approach

Build the auto-apply flow after the scoring phase in the LangGraph pipeline. Use **Naukri API approach** discovered via network inspection - much more reliable than browser automation.

---

### Pipeline: Extended StateGraph

```
load_config → parse_resume → search_jobs → score_jobs → filter_shortlist → apply_jobs → export_csv → END
```

New node `apply_jobs` added after `filter_shortlist` and before `export_csv`.

---

### Key Discovery: Naukri Apply API Flow

Through network inspection (DevTools → Network tab), discovered that Naukri uses APIs instead of browser form filling:

```
1. Click "Apply" button (browser) → triggers POST /apply → returns ALL questions
2. For each question → POST /respond with answer
3. After all /respond calls → browser auto-calls POST /apply with ALL answers → submits!
```

**Benefits:**
- No need to handle contenteditable divs
- No need to click Save/Next for each question
- Just API calls - much more stable
- Batch LLM: one call for all answers

---

### API Details

#### 1. `/apply` - Get Questions (auto-triggered on click)

```
URL: POST https://www.naukri.com/cloudgateway-workflow/workflow-services/apply-workflow/v1/apply

Headers:
  - appid: 121
  - clientid: d3skt0p
  - systemid: jobseeker
  - authorization: ACCESSTOKEN=<token from browser>
  - content-type: application/json

Payload:
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

Response → "questionnaire": [
  {
    "questionId": "38621838",
    "questionName": "How many years of experience do you have in Typescript?",
    "questionType": "Text Box",
    "isMandatory": true
  },
  ...
]
```

#### 2. `/respond` - Send Each Answer

```
URL: POST https://www.naukri.com/cloudgateway-chatbot/chatbot-services/botapi/v5/respond

Headers:
  - authorization: Bearer <token from browser>
  - content-type: application/json

Payload:
{
  "input": {
    "text": ["5"],              // The answer
    "id": ["-1"]
  },
  "appName": "250326025777_apply",
  "domain": "Naukri",
  "conversation": "250326025777_apply",
  "channel": "web",
  "status": "Fresh",
  "deviceType": "WEB"
}

Response → Next question in "speechResponse", or success state with "Thank for your response"
```

#### 3. Final `/apply` - Auto-submit

After all `/respond` calls complete, browser auto-calls `/apply` again with all answers in payload:
```
{
  "applyData": {
    "250326025777": {
      "answers": {
        "38621838": "5",
        "38621840": "2",
        ...
      }
    }
  }
}
```

---

### Module Design

#### 1. Apply Package (`src/job_hunter/apply/`)

**Package structure:**
```
apply/
├── __init__.py       # Package exports
├── api.py            # API client for /apply and /respond
├── client.py         # Session & auth management
└── naukri_apply.py   # Main orchestrator
```

**Key Functions:**

- `api.py`:
  - `get_questions(page, job_id, skills)` - Call /apply to get all questions
  - `send_response(page, job_id, question_id, answer)` - Call /respond for single answer
  - `extract_conversation_id(response)` - Extract from /apply response

- `client.py`:
  - `get_auth_headers(page)` - Extract authorization tokens (or use page.request directly)

- `naukri_apply.py`:
  - `apply_to_job(page, job, profile, config)` - Main orchestrator
  - `navigate_to_job(page, url)` - Go to job detail
  - `check_already_applied(page)` - Detect "Applied" badge
  - `wait_for_submission(page)` - Wait for auto-submit after all responses

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
- User confirms at START of each job
- Show job info (title, company, match score) before applying

#### 3. CSV Enhancement (`export/csv_export.py`)

**Changes:**
- Add `apply_timestamp` column
- Add `apply_error` column
- Update `apply_status` values: Applied, Failed, Skipped, Already Applied
- Re-export CSV after apply phase with updated statuses

---

### Data Flow: API-Based Approach

```
filter_shortlist returns shortlisted jobs
         │
         ▼
apply_jobs_node(state)
         │
         ▼
   ┌─────────────────────────────┐
   │ For each job >= threshold:  │
   │   Prompt user (y/n/q)        │
   └─────────────────────────────┘
         │
    ┌────┴────┐
    │         │
   Apply     Skip
    │         │
    ▼         ▼
apply_to_job  update status to "Skipped"
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ API-BASED APPLY FLOW:                              │
│  1. Click Apply button (browser)                  │
│  2. Intercept questions from /apply response       │
│  3. Send all questions to LLM → get answers       │
│  4. For each answer → POST /respond                │
│  5. Wait for auto-submit (browser calls /apply)   │
│  6. Detect success ("Thank for your response")     │
└─────────────────────────────────────────────────────┘
    │
    ▼
update apply_status → Applied/Failed
         │
         ▼
All jobs processed → export_csv (with updated statuses)
```

---

### Exploration Script

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

---

### Dependencies

- Phase 2a (Detailed Profile) complete
- `profile_detailed.yaml` available
- `screening.yaml` loaded in config
- `resume_path` configured in user.yaml
- LangGraph workflow updated with new node
- **Naukri search must be working** (currently blocked - ENH-016)

---

### Risks Identified

| Risk | Mitigation |
|------|------------|
| Naukri search blocking | Must resolve before Phase 2b can work (ENH-016) |
| API changes | Log API payloads/responses for debugging |
| Session expiry | Handle 401 errors, offer re-login |
| Resume required | Some jobs may require resume upload separately |
| Already applied | Check "Applied" badge before attempting |

---

### Effort

~2-3 days for Phase 2b - primarily API integration and testing.

**Note:** Naukri search must be fixed first (ENH-016 - pagination fix).