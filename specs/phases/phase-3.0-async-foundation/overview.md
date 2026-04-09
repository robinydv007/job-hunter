# Phase 3.0 — Overview: Async Architecture Foundation

**Status:** Not Started  
**Target:** TBD  
**Release:** v0.3.0 (planned)

---

## Goal

Resolve the async/sync conflict that blocked ENH-017 (pipeline reorder: parse before login) and establish a clean async architecture that unblocks multi-platform support. This is the **prerequisite phase** before Phase 3.1 (Multi-Platform Search) can begin.

---

## Why This Phase Exists

Two prior attempts to add a login node to the LangGraph workflow both failed:

| Attempt | Approach | Result |
|---------|----------|--------|
| 1 | Async `login_platforms_node` in LangGraph | FAILED — pipeline hangs at `search_naukri()` |
| 2 | Sync node with `asyncio.new_event_loop()` | FAILED — Playwright hangs in nested event loop |

**Root cause:** `search_naukri()` is a sync function that uses `nest_asyncio.apply()` + `loop.run_until_complete()` to call async Playwright code. When an async node runs first (login), it pollutes the event loop, and subsequent sync nodes with `nest_asyncio` hang.

This is not a login problem — it is an **architecture problem**. The entire pipeline mixes sync and async incorrectly. The solution is to convert the pipeline to native async throughout.

---

## Scope

1. **Convert pipeline to async** — All LangGraph nodes become `async def`, all Playwright-calling functions become native async, remove `nest_asyncio` dependency
2. **Add login node to workflow** — Login moves from CLI into the LangGraph graph as a proper async node
3. **Reorder pipeline flow** — New flow: `load_config → parse_resume → login → search_jobs → ...`
4. **Remove CLI login** — CLI starts browser only; login happens inside the graph after resume parsing

---

## Current Flow (Before Phase 3.0)

```
CLI: Start browser → Login to Naukri → Build workflow → Run workflow
                             ↓
LangGraph (sync nodes, nest_asyncio hacks):
  load_config → parse_resume → search_jobs → score_jobs → filter_shortlist → export_csv → update_history
```

**Problems:**
- Login happens before resume parsing — no profile data available for login decisions
- `search_naukri()` uses `nest_asyncio.apply()` + `loop.run_until_complete()` — a sync wrapper around async Playwright
- `parse_resume_node()` uses `nest_asyncio.apply()` — same pattern
- No way to add async nodes (login, multi-platform) without breaking the event loop

---

## New Flow (After Phase 3.0)

```
CLI: Start browser (no login) → Build workflow → Run async workflow
                                            ↓
LangGraph (all async nodes, no nest_asyncio):
  load_config → parse_resume → login_platforms → search_jobs → score_jobs → filter_shortlist → export_csv → update_history
```

**Benefits:**
- Resume is parsed **before** login — profile data available for platform selection
- Login is a proper async node — no event loop conflicts
- Multi-platform login possible in parallel via `asyncio.gather()`
- All Playwright operations use native async — no `nest_asyncio` hacks
- Clean architecture — no sync/async boundary violations

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                 Phase 3.0 Architecture Change                        │
└─────────────────────────────────────────────────────────────────────┘

  BEFORE (sync + nest_asyncio):          AFTER (native async):
  ┌──────────────────────┐              ┌──────────────────────┐
  │ CLI                  │              │ CLI                  │
  │  start browser       │              │  start browser       │
  │  login_naukri() ←─┐ │              │  (no login here)     │
  │  build workflow    │ │              │  build workflow       │
  │  invoke(workflow)  │ │              │  ainvoke(workflow)   │
  └──────────────────────┘              └──────────────────────┘
          │                                      │
          ▼                                      ▼
  ┌──────────────────────┐              ┌──────────────────────┐
  │ LangGraph (sync)     │              │ LangGraph (async)    │
  │                      │              │                      │
  │ load_config (sync)   │              │ load_config (async)  │
  │ parse_resume (sync)  │              │ parse_resume (async) │
  │    └─ nest_asyncio   │              │    └─ await native   │
  │ search_jobs (sync)   │              │ login_platforms NEW  │
  │    └─ nest_asyncio   │              │ search_jobs (async)  │
  │ score_jobs (sync)    │              │    └─ await native   │
  │ filter (sync)        │              │ score_jobs (async)   │
  │ export_csv (sync)    │              │ filter (async)       │
  │ update_history (sync)│              │ export_csv (async)   │
  └──────────────────────┘              │ update_history (async)│
                                        └──────────────────────┘
```

---

## Key Design Decisions

### 1. All nodes must be async

LangGraph supports both sync and async nodes, but mixing them causes event loop issues. Converting all nodes to async eliminates the root cause entirely.

### 2. Remove nest_asyncio dependency entirely

`nest_asyncio` is a workaround that creates fragile event loop interactions. Removing it ensures clean async propagation and eliminates hard-to-debug hangs.

### 3. CLI only manages browser lifecycle

The CLI starts/stops the browser but does NOT log in. Login responsibility moves to the `login_platforms` node inside the graph.

### 4. Login node runs after parse_resume

This is the core flow change ENH-017 was trying to achieve. Resume is parsed first so profile data is available for platform selection and personalized login.

### 5. Graceful failure for login

If login fails for a platform, log a warning and skip that platform. Do not crash the entire pipeline. This supports future multi-platform scenarios where one platform may be down.

---

## Deliverables

| Deliverable | File(s) | Description |
|-------------|---------|-------------|
| Async search_naukri | `src/job_hunter/search/naukri.py` | Convert from sync+nest_asyncio to native async |
| Async parse_resume_node | `src/job_hunter/graph/nodes.py` | Convert from sync+nest_asyncio to native async |
| All nodes async | `src/job_hunter/graph/nodes.py` | Convert all remaining nodes to async |
| Login platforms node | `src/job_hunter/graph/nodes.py` | New async node for platform login |
| Login helper | `src/job_hunter/browser.py` | Add `login_platform()` dispatcher |
| Updated workflow | `src/job_hunter/graph/workflow.py` | Add login node, reorder edges |
| Updated state | `src/job_hunter/graph/state.py` | Add `logged_in_platforms` field |
| Updated CLI | `src/job_hunter/cli.py` | Remove login, use `ainvoke`, pass browser_page |
| Remove nest_asyncio | `pyproject.toml`, all `.py` files | Remove nest_asyncio dependency |

---

## Acceptance Criteria

- [ ] All LangGraph nodes are `async def` — no sync nodes remain
- [ ] `nest_asyncio` is not imported anywhere in the codebase
- [ ] Pipeline runs end-to-end with same results as current sync pipeline
- [ ] Login happens inside the graph after resume parsing, not in CLI
- [ ] Pipeline flow is: `load_config → parse_resume → login_platforms → search_jobs → ...`
- [ ] Failed login for a platform logs a warning and skips (does not crash pipeline)
- [ ] `logged_in_platforms` field is populated in state after login node
- [ ] CLI only starts browser — no login call
- [ ] `workflow.ainvoke()` used instead of `workflow.invoke()`

---

## Exit Criteria

The pipeline runs with identical output to Phase 2b, but with async architecture throughout. Login happens inside the graph after resume parsing. No `nest_asyncio` dependency. Multi-platform login node is ready for Phase 3.1 (just add new platform login functions).

---

## Known Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| LangGraph async node execution differs from sync | Medium | Test each node individually before wiring into workflow |
| Playwright `page` object across async boundaries | Medium | Pass `page` through state, verify session persists |
| Breaking existing pipeline behavior | High | Run full E2E test before merging; keep CLI fallback if needed |
| `nest_asyncio` removal affects other libraries | Low | Audit all imports; only used in 2 places currently |
| Login failure in graph vs CLI | Medium | Add robust error handling in login node; allow pipeline to continue without login for development |

---

## Dependencies

- **Phase 2b** (Auto-Apply) should be complete or at least its core pipeline stable
- Phase 3.0 does NOT depend on Phase 2b being fully complete — the async refactor can proceed independently on the core pipeline
- **Phase 3.1** (Multi-Platform) depends on Phase 3.0 being complete

---

## What This Phase Does NOT Include

- Multi-platform scrapers (LinkedIn, Hirist, etc.) — that is Phase 3.1
- Company intelligence features — that is Phase 3.2
- Auto-apply node — that is Phase 2b
- Any new user-facing features beyond the login reorder