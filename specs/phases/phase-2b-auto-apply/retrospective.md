# Phase 2b — Retrospective: Auto-Apply

> **Phase:** 2b (Auto-Apply & Batch Screening)  
> **Status:** Complete  
> **Release:** v0.2.1  
> **Completed:** 2026-04-15

---

## What Went Well

1. **API-Based Approach** — Discovered Naukri's internal APIs through network inspection. This was a game-changer: instead of fragile browser automation with contenteditable elements, we used reliable API calls.

2. **User Verification** — Testing with actual jobs confirmed the implementation works for most cases. The user confirmed it works fine.

3. **Error Handling** — Added try/except blocks around page queries to handle navigation timing issues after application submission.

4. **Fallback Mechanism** — Implemented UI-based fallback when API calls fail, ensuring reliability.

5. **Retry Logic** — When answers are rejected, the system retries with different answer selections (up to 3 attempts).

---

## What Didn't Go Well

1. **Multiple Implementation Attempts** — Initially tried state machine approach with contenteditable handling. Took several iterations to discover the API-based approach.

2. **Debug Print Statements** — Several `print()` statements remain in the code that should use logger instead.

3. **ENH-018 Not Implemented** — Review/edit/regenerate answers feature was de-scoped to get the core functionality working.

4. **CAPTCHA Handling Not Implemented** — Noted in tasks but not implemented (user handles manually).

---

## Lessons Learned

1. **Network Inspection > DOM Inspection** — Naukri's apply flow uses APIs, not form submissions. Future platform integrations should start with network inspection.

2. **Response-Driven Loop** — The chatbot API returns the next question via `speechResponse`. Matching chatbot prompt text to question list is more robust than index-based iteration.

3. **Browser Auto-Submit** — After all `/respond` calls complete, the browser automatically calls `/apply` with all answers. Don't need manual final submit.

---

## Deliverables

| Deliverable | File(s) | Status |
|-------------|---------|--------|
| Apply package | `src/job_hunter/apply/` | ✅ Complete |
| API client | `src/job_hunter/apply/api.py` | ✅ Complete |
| Apply orchestrator | `src/job_hunter/apply/naukri_apply.py` | ✅ Complete |
| Apply node | `src/job_hunter/graph/nodes.py` | ✅ Complete |
| CSV enhancement | `src/job_hunter/export/csv_export.py` | ✅ Complete |

---

## Open Items for Future Phases

- **ENH-018** — Review/edit/regenerate answers before apply (nice to have)
- **CAPTCHA detection** — Pause and prompt user to solve manually
- **Debug cleanup** — Replace `print()` statements with proper logging

---

## Next Phase

Phase 3.0 — Async Architecture Foundation
- Resolve ENH-017: Reorder pipeline (parse resume before login)
- Login node with resume-before-login flow
