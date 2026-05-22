# Phase 3.0 — Tasks: Async Architecture Foundation

> **Status: COMPLETE** — All tasks done; E2E validated 2026-05-22

## Prerequisites

- [x] Phase 2b Auto-Apply pipeline is stable and tested (v0.2.1)
- [x] All existing nodes working end-to-end
- [x] `apply_jobs_node` functional with CLI-based login
- [x] CSV export with apply status columns working
- [x] Git branch created for Phase 3.0 work (isolated from main)

## Task Checklist

### 0. ENH-21: Merge Resume Cache (Profile Consolidation)
- [x] Refactor `src/job_hunter/resume/parser.py`:
  - [x] Replace dual file save (`profile.json` + `profile_detailed.yaml`) with single `profile_cache.json`
  - [x] Combine both basic and detailed fields into one JSON structure with `detailed` sub-key
  - [x] Replace load functions: `load_profile()` + `load_detailed_profile()` → `load_profile_cache()`
  - [x] Remove `save_detailed_profile()`, `load_detailed_profile()`, `load_profile_with_detailed()`
  - [x] Update `parse_resume_full()` to write merged cache
- [x] Refactor `src/job_hunter/resume/schema.py`:
  - [x] Add optional `detailed: dict` field to `ResumeProfile` schema
- [x] Refactor `src/job_hunter/graph/nodes.py`:
  - [x] Update `parse_resume_node` to use single loader (`load_profile_cache()`)
  - [x] Update return value: `profile` and `detailed_profile` from merged cache
- [x] Refactor `src/job_hunter/cli.py`:
  - [x] Update `clean` command: remove `profile_cache.json` instead of old filenames
- [x] Delete old files after migration test:
  - [ ] Delete `data/profile.json` and `data/profile_detailed.yaml`
- [x] Verify acceptance criteria:
  - [x] Single `data/profile_cache.json` written after resume parse
  - [x] Both basic and detailed fields available from one load call
  - [x] No remaining references to `profile.json` or `profile_detailed.yaml`
  - [x] Resume change detection (hash) continues to work unchanged
  - [x] Subsequent runs use cache without LLM call
- [x] Related: ENH-022 (user-owned profile.yaml) builds on this

### 1. Convert search_naukri to Native Async ✅ Done (Phase 3.2)
- [x] Refactor `src/job_hunter/search/naukri.py`:
  - `search_naukri()` is already `async def` — no nest_asyncio or loop.run_until_complete
- [x] Verify: `search_naukri()` no longer uses `nest_asyncio` or `loop.run_until_complete`
- [x] Test: Confirmed working in Phase 3.2 e2e test

### 2. Convert parse_resume_node to Native Async ✅ Done (Phase 3.2)
- [x] Refactor `src/job_hunter/graph/nodes.py`:
  - `parse_resume_node()` is already `async def` — native await used
- [x] Verify: `parse_resume_node()` no longer uses `nest_asyncio`
- [x] Test: Confirmed working in Phase 3.2 e2e test

### 3. Convert All Remaining Nodes to Async ✅ Done
- [x] Change all node signatures to `async def`:
  - [x] `load_config_node` → `async def load_config_node`
  - [x] `score_jobs_node` → `async def score_jobs_node`
  - [x] `filter_shortlist_node` → `async def filter_shortlist_node`
  - [x] `export_csv_node` → `async def export_csv_node`
  - [x] `update_history_node` → `async def update_history_node`
- [x] score_jobs_node now calls `await score_jobs_with_llm()` directly — sync wrapper removed from hot path
- [x] Verify: All nodes have `async def` signatures
- [x] Test: 34 tests pass

### 4. Create Login Platforms Node ✅ Done
- [x] Add `async def login_platforms_node(state)` to `src/job_hunter/graph/nodes.py`
  - Reads `config.search.platforms`, calls `await login_platform(page, platform)`
  - Populates `logged_in_platforms` in state
  - Skips login gracefully if no platforms; raises RuntimeError only if ALL fail
- [x] Add `async def login_platform(page, platform)` to `src/job_hunter/browser.py`
  - Dispatcher: "naukri" → `BrowserManager().login_naukri(page=page)`, else returns False
- [x] Refactor `BrowserManager.login_naukri()` to accept optional `page` param
  - `target_page = page or self._page` — all internal refs use `target_page`
  - Backward compatible: CLI/standalone calls without `page` still work

### 5. Update State Schema ✅ Done
- [x] Add `logged_in_platforms: list[str]` to `JobHunterState` in `src/job_hunter/graph/state.py`
- [x] Add `"logged_in_platforms": []` to `initial_state` in `cli.py`

### 6. Reorder Workflow ✅ Done
- [x] Add `login_platforms` node to workflow in `src/job_hunter/graph/workflow.py`
- [x] Edge: `parse_resume → login_platforms → search_jobs`
- [x] Flow: `load_config → parse_resume → login_platforms → search_jobs → score_jobs → filter_shortlist → apply_jobs → export_csv → update_history → END`

### 7. Update CLI ✅ Done
- [x] Remove `browser.login_naukri()` call and its error handling from `cli.py`
- [x] `workflow.ainvoke(initial_state)` already in use — no change needed
- [x] Browser start/close lifecycle unchanged

### 8. Remove nest_asyncio Dependency ✅ Done
- [x] In `src/job_hunter/scoring/llm_scorer.py`: replaced `nest_asyncio.apply()` with `asyncio.run()` in `score_jobs_with_llm_sync()`
- [x] No remaining `nest_asyncio` imports anywhere in codebase
- [x] No remaining `loop.run_until_complete` calls
- [x] Removed `nest-asyncio` from `pyproject.toml` dependencies
- [x] `uv sync` confirmed removal (nest-asyncio==1.6.0 uninstalled)

### 9. End-to-End Validation ✅ Done
- [x] Run full pipeline: `uv run job-hunter run`
- [x] Verify: Resume parsed BEFORE login — console: "Processing resume..." → "Logging into Naukri..." ✅
- [x] Verify: Login inside graph — "Logged in to naukri" appears after resume panel ✅
- [x] Verify: Search returns results — 37 jobs found, 37 after dedup ✅
- [x] Verify: Scoring works — 37 jobs scored with correct percentages ✅
- [x] Fix discovered: `filter_shortlist_node` None comparison bug (`max_jobs`) — fixed and committed ✅

### 10. Update Architecture Documentation ✅ Done
- [x] Update `specs/architecture/overview.md` — pipeline flow, node name, mermaid diagram
- [x] Update `specs/phases/phase-3.0-async-foundation/history.md` with completion record
- [x] Update `specs/status.md` to mark Phase 3.0 as complete
- [x] Update `specs/phases/index.json` — status: complete
- [x] Update `specs/changelog/2026-05.md`
- [x] Mark ENH-017 resolved in backlog

---

## Implementation Notes

- **All nodes must be async.** Even nodes that don't use async operations (like `load_config_node`) should be `async def` for consistency. LangGraph handles this natively.
- **`nest_asyncio` must be completely removed.** Not just disabled — removed from dependencies. It's the root cause of the event loop conflict.
- **Login node is conditional.** If `config.search.platforms` is empty, the node skips and returns `{"logged_in_platforms": []}`.
- **CLI only manages browser lifecycle.** Start browser, pass page to workflow, close browser. No login logic in CLI.
- **Backward compatibility.** `BrowserManager.login_naukri()` still works standalone (for testing) via the `page=None` default.
- **Phase 2b must be stable.** Do not start this phase if Phase 2b is not complete and tested.

---

## Files Modified

| File | Change |
|------|--------|
| `src/job_hunter/search/naukri.py` | Convert `search_naukri()` to async, remove nest_asyncio |
| `src/job_hunter/graph/nodes.py` | Convert all nodes to async, add `login_platforms_node` |
| `src/job_hunter/graph/workflow.py` | Add login node, reorder edges |
| `src/job_hunter/graph/state.py` | Add `logged_in_platforms` field |
| `src/job_hunter/browser.py` | Add `login_platform()`, refactor `login_naukri()` to accept page param |
| `src/job_hunter/cli.py` | Remove login, use `ainvoke`, add `logged_in_platforms` to initial state |
| `pyproject.toml` | Remove `nest-asyncio` dependency |

---

## Testing Checklist

| Test | Expected Result |
|------|-----------------|
| Full async pipeline run | Same output as Phase 2b sync pipeline |
| Resume parsed before login | Console shows "Processing resume..." before "Logging into Naukri..." |
| Login success | `logged_in_platforms: ["naukri"]` in state |
| Login failure | Warning logged, pipeline continues (or raises if all fail) |
| No platforms configured | Login node skipped, `logged_in_platforms: []` |
| `--force-parse` | Force re-parse works in async mode |
| `--headless` | Headless mode works in async mode |
| No `nest_asyncio` | `grep -r nest_asyncio src/` returns nothing |
| Same CSV output | CSV identical to Phase 2b output (same columns, same data) |