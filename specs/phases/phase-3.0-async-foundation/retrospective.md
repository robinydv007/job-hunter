# Phase 3.0 — Retrospective: Async Architecture Foundation

**Completed:** 2026-05-22  
**Release:** v0.3.0

---

## What We Built

Converted the entire LangGraph pipeline from a mix of sync and async nodes (with `nest_asyncio` hacks) to fully native async throughout. Added `login_platforms_node` as a proper graph node that runs after resume parsing. Resolved ENH-017, which had failed twice previously due to event loop conflicts.

---

## What Went Well

- **Pre-start audit saved time.** Reading the code before implementing revealed that Tasks 1 and 2 (search_naukri, parse_resume_node) were already async from Phase 3.2 work. Avoided duplicate effort.
- **Conversion was clean.** Changing `def` to `async def` on the remaining 5 nodes was mechanical. LangGraph handled the async transition transparently — no behavioral changes.
- **`login_platform()` dispatcher pattern is extensible.** Adding a new platform in Phase 3.1 means adding one `elif` in `browser.py` — no changes to the node itself.
- **`score_jobs_node` got a bonus improvement.** Since it's now async, it calls `await score_jobs_with_llm()` directly instead of going through the `score_jobs_with_llm_sync` wrapper. Cleaner and one less indirection.
- **E2E validated cleanly.** The pipeline ran end-to-end on the first try after the fix below.

---

## What Was Discovered

- **`filter_shortlist_node` had a latent bug.** `config.search.max_jobs` can be `None`, and `None > 0` raises `TypeError`. This bug existed before Phase 3.0 but was exposed when the node became async (LangGraph surfaces errors differently in async mode). Fixed with `(config.search.max_jobs or 0) > 0`.
- **Tasks 1 and 2 were already done** — spec was written in April before Phase 3.2 work happened. Pre-start audit is worth doing on any phase that has a long gap between spec and implementation.

---

## What Could Be Better

- The `login_platforms_node` currently logs in sequentially. For Phase 3.1 (multi-platform), parallel login via `asyncio.gather()` would be faster. This is a known non-goal for Phase 3.0 — worth adding to Phase 3.1 scope.
- `score_jobs_with_llm_sync` still exists as a standalone sync wrapper for testing/scripting use. Now uses `asyncio.run()` instead of `nest_asyncio` — acceptable, but if tests ever run inside an async context this wrapper will fail. Consider converting test fixtures to async in Phase 3.1.

---

## Metrics

| Metric | Value |
|--------|-------|
| Implementation time | 1 session |
| Files changed | 8 source files + 3 spec files |
| Tests before | 34 passing |
| Tests after | 34 passing |
| Bugs discovered | 1 (filter_shortlist None comparison) |
| ENH items closed | ENH-017 |
| `nest_asyncio` removed | Yes — from pyproject.toml and all source files |

---

## Phase 3.1 Readiness

Phase 3.0's login_platforms_node is already wired to iterate `config.search.platforms`. Adding LinkedIn, Hirist, or any other platform in Phase 3.1 requires:
1. A new scraper module in `src/job_hunter/search/<platform>.py`
2. An `elif platform == "<platform>":` branch in `browser.py`'s `login_platform()` dispatcher
3. A search call added to `search_jobs_node`'s platform loop

The architecture is ready.
