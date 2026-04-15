# Phase 3.0 — Tasks: Async Architecture Foundation

> **Status: NOT STARTED** — Awaiting Phase 2b completion

## Prerequisites (Must complete Phase 2b first)

- [ ] Phase 2b Auto-Apply pipeline is stable and tested
- [ ] All existing nodes working end-to-end
- [ ] `apply_jobs_node` functional with CLI-based login
- [ ] CSV export with apply status columns working
- [ ] Git branch created for Phase 3.0 work (isolated from main)

## Task Checklist

### 1. Convert search_naukri to Native Async
- [ ] Refactor `src/job_hunter/search/naukri.py`:
  - Change `def search_naukri()` → `async def search_naukri()`
  - Remove `import asyncio` and `import nest_asyncio` from inside function
  - Remove `nest_asyncio.apply()` call
  - Remove `loop = asyncio.get_event_loop()` and all `loop.run_until_complete()` calls
  - Replace `loop.run_until_complete(scrape_jobs_from_page(...))` → `await scrape_jobs_from_page(...)`
  - Replace `loop.run_until_complete(asyncio.sleep(delay))` → `await asyncio.sleep(delay)`
- [ ] Verify: `search_naukri()` no longer uses `nest_asyncio` or `loop.run_until_complete`
- [ ] Test: Call `await search_naukri()` directly from an async context — produces same results

### 2. Convert parse_resume_node to Native Async
- [ ] Refactor `src/job_hunter/graph/nodes.py`:
  - Change `def parse_resume_node()` → `async def parse_resume_node()`
  - Remove `import asyncio` and `import nest_asyncio` from inside function
  - Remove `nest_asyncio.apply()` call
  - Remove `loop = asyncio.get_event_loop()` and `loop.run_until_complete()`
  - Replace `loop.run_until_complete(parse_resume_full(...))` → `await parse_resume_full(...)`
- [ ] Verify: `parse_resume_node()` no longer uses `nest_asyncio`
- [ ] Test: Resume parsing works with `await` in async context

### 3. Convert All Remaining Nodes to Async
- [ ] Change all node signatures to `async def`:
  - [ ] `load_config_node` → `async def load_config_node`
  - [ ] `score_jobs_node` → `async def score_jobs_node`
  - [ ] `filter_shortlist_node` → `async def filter_shortlist_node`
  - [ ] `export_csv_node` → `async def export_csv_node`
  - [ ] `update_history_node` → `async def update_history_node`
- [ ] Add `await` to any async calls inside these nodes (LLM scoring, file I/O)
- [ ] Verify: All nodes have `async def` signatures
- [ ] Test: All nodes return correct state dicts when awaited

### 4. Create Login Platforms Node
- [ ] Add `async def login_platforms_node(state)` to `src/job_hunter/graph/nodes.py`
  - Read `config.search.platforms` to determine which platforms to login to
  - Iterate over platforms, call `await login_platform(page, platform, config)`
  - Populate `logged_in_platforms` in state
  - Handle login failures gracefully: log warning, skip platform, continue
  - Raise RuntimeError only if ALL platforms fail
- [ ] Add `async def login_platform(page, platform, config)` to `src/job_hunter/browser.py`
  - Dispatcher function: routes to platform-specific login (naukri, etc.)
  - Returns `bool` for success/failure
  - Currently supports "naukri" only (extensible for Phase 3.1)
- [ ] Refactor `BrowserManager.login_naukri()` to accept optional `page` parameter
  - `async def login_naukri(self, email=None, password=None, page=None) -> bool`
  - Use `page or self._page` throughout
  - Keeps backward compatibility with CLI usage
- [ ] Test: Login works with page passed from graph node
- [ ] Test: Login failure for a platform logs warning and continues
- [ ] Test: All platforms failing raises RuntimeError

### 5. Update State Schema
- [ ] Add `logged_in_platforms: list[str]` to `JobHunterState` in `src/job_hunter/graph/state.py`
- [ ] Update `initial_state` in `cli.py` to include `"logged_in_platforms": []`
- [ ] Test: State propagates `logged_in_platforms` through workflow

### 6. Reorder Workflow
- [ ] Add `login_platforms` node to workflow in `src/job_hunter/graph/workflow.py`
- [ ] Change edge: `parse_resume → login_platforms` (was `parse_resume → search_jobs`)
- [ ] Add edge: `login_platforms → search_jobs`
- [ ] Verify flow: `load_config → parse_resume → login_platforms → search_jobs → score_jobs → filter_shortlist → export_csv → update_history → END`
- [ ] Test: Workflow compiles and runs without errors

### 7. Update CLI
- [ ] Remove `browser.login_naukri()` call and its error handling from `cli.py`
- [ ] Change `workflow.invoke(initial_state)` → `await workflow.ainvoke(initial_state)`
- [ ] Keep browser start/close lifecycle unchanged
- [ ] Keep all other CLI logic unchanged (resume path resolution, config validation, etc.)
- [ ] Test: `job-hunter run --resume resume.pdf` works end-to-end

### 8. Remove nest_asyncio Dependency
- [ ] Search entire codebase for `nest_asyncio` — verify no remaining imports
- [ ] Search entire codebase for `loop.run_until_complete` — verify no remaining calls
- [ ] Remove `nest-asyncio` from `pyproject.toml` dependencies
- [ ] Run `uv sync` to verify dependency removal
- [ ] Test: Full pipeline runs without `nest_asyncio` installed

### 9. End-to-End Validation
- [ ] Run full pipeline: `job-hunter run --resume resume.pdf`
- [ ] Verify: Resume is parsed BEFORE login (check console output order)
- [ ] Verify: Login happens inside the graph (check console output for login message)
- [ ] Verify: Search returns same results as before refactor
- [ ] Verify: Scoring produces same results as before refactor
- [ ] Verify: CSV export produces same output as before refactor
- [ ] Verify: `logged_in_platforms` populated in state (e.g., `["naukri"]`)
- [ ] Test: Login failure — pipeline should skip platform and log warning
- [ ] Test: No platforms configured — pipeline should skip login node and continue
- [ ] Test: `--force-parse` flag still works
- [ ] Test: `--headless` flag still works

### 10. Update Architecture Documentation
- [ ] Update `specs/architecture/overview.md` with new pipeline flow diagram
- [ ] Update `specs/phases/phase-3.0-async-foundation/history.md` with completion record
- [ ] Update `specs/status.md` to mark Phase 3.0 as complete
- [ ] Update `specs/roadmap/roadmap.md` with completion dates
- [ ] Add Phase 3.0 entry to `specs/changelog/2026-04.md`

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