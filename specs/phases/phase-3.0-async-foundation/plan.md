# Phase 3.0 — Plan: Async Architecture Foundation

## Implementation Approach

Convert the entire LangGraph pipeline from sync nodes with `nest_asyncio` hacks to native async nodes. Add login as an async node inside the graph. Remove all `nest_asyncio` usage.

---

## Step 1: Convert Core Functions to Async

### 1.1 Convert `search_naukri()` to native async

**File:** `src/job_hunter/search/naukri.py`

**Current (sync + nest_asyncio):**
```python
def search_naukri(profile, search_config, naukri_config, page, ...):
    import asyncio
    import nest_asyncio
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    jobs = loop.run_until_complete(scrape_jobs_from_page(...))
    # ... more loop.run_until_complete() calls
```

**New (native async):**
```python
async def search_naukri(profile, search_config, naukri_config, page, ...):
    # Direct await — no nest_asyncio, no event loop hacking
    jobs = await scrape_jobs_from_page(...)
    # ... direct await for all async calls
```

**Changes:**
- Remove `import asyncio, nest_asyncio` at top of function
- Remove `nest_asyncio.apply()` call
- Remove `loop = asyncio.get_event_loop()`
- Replace all `loop.run_until_complete(coro)` with `await coro`
- Change function signature from `def` to `async def`
- The inner `scrape_jobs_from_page()` is already async — no changes needed there
- Delay between queries: `await asyncio.sleep(delay)` (already uses asyncio)

### 1.2 Convert `parse_resume_node()` to native async

**File:** `src/job_hunter/graph/nodes.py`

**Current (sync + nest_asyncio):**
```python
def parse_resume_node(state: JobHunterState) -> dict:
    import asyncio
    import nest_asyncio
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    profile, detailed = loop.run_until_complete(parse_resume_full(...))
```

**New (native async):**
```python
async def parse_resume_node(state: JobHunterState) -> dict:
    profile, detailed = await parse_resume_full(...)
```

**Changes:**
- Remove `import asyncio, nest_asyncio` at top of function
- Remove `nest_asyncio.apply()` call
- Replace `loop.run_until_complete(parse_resume_full(...))` with `await parse_resume_full(...)`
- Change function signature from `def` to `async def`
- `parse_resume_full()` is already async — no changes needed there

---

## Step 2: Convert All Remaining Nodes to Async

**File:** `src/job_hunter/graph/nodes.py`

Convert all nodes to `async def` for consistency. Even nodes that don't currently use async may need it in the future (e.g., export could write to cloud storage).

| Node | Current | New | Async Operations? |
|------|---------|-----|-------------------|
| `load_config_node` | `def` | `async def` | No (but consistent) |
| `parse_resume_node` | `def` + nest_asyncio | `async def` + `await` | Yes — LLM call |
| `search_jobs_node` | `def` | `async def` + `await` | Yes — Playwright, now calls `await search_naukri()` |
| `score_jobs_node` | `def` | `async def` | Maybe — LLM scoring is async |
| `filter_shortlist_node` | `def` | `async def` | No (but consistent) |
| `export_csv_node` | `def` | `async def` | No (but consistent) |
| `update_history_node` | `def` | `async def` | No (but consistent) |

**Note:** LangGraph handles async nodes natively via `ainvoke()`. Sync-only nodes that become `async def` just work — they return dicts as before, just wrapped in a coroutine that LangGraph awaits.

---

## Step 3: Add Login Platforms Node

### 3.1 Create `login_platforms_node()`

**File:** `src/job_hunter/graph/nodes.py`

```python
async def login_platforms_node(state: JobHunterState) -> dict:
    """Login to configured platforms. Runs after resume parsing."""
    config = state["config"]
    page = state.get("browser_page")
    platforms = config.search.platforms

    if not platforms:
        console.print("[yellow]No platforms configured for login[/]")
        return {"logged_in_platforms": []}

    if not page:
        raise RuntimeError("Browser page is None, cannot login")

    logged_in = []
    for platform in platforms:
        try:
            success = await login_platform(page, platform, config)
            if success:
                logged_in.append(platform)
                console.print(f"[green]Logged in to {platform}[/]")
            else:
                console.print(f"[yellow]Failed to login to {platform}[/]")
        except Exception as e:
            console.print(f"[red]Error logging in to {platform}: {e}[/]")

    if not logged_in:
        console.print("[red]Failed to login to all platforms[/]")
        raise RuntimeError("Could not login to any platform")

    return {"logged_in_platforms": logged_in}
```

### 3.2 Add `login_platform()` helper

**File:** `src/job_hunter/browser.py`

```python
async def login_platform(page: Page, platform: str, config: AppConfig) -> bool:
    """Login to a single platform by name."""
    if platform == "naukri":
        browser = BrowserManager.__new__(BrowserManager)
        browser._page = page
        browser._browser = None
        browser._context = None
        return await browser.login_naukri()
    else:
        console.print(f"[yellow]Unknown platform: {platform}[/]")
        return False
```

**Important:** The `login_naukri()` method needs a small refactor to accept an existing `page` object instead of requiring `self._page`. This avoids creating a new BrowserManager instance.

### 3.3 Refactor `BrowserManager.login_naukri()`

**Current:** Uses `self._page` (internal attribute).

**New:** Accept `page` as optional parameter, fallback to `self._page`:

```python
async def login_naukri(self, email=None, password=None, page=None) -> bool:
    target_page = page or self._page
    if not target_page:
        raise RuntimeError("No page available. Call start() first.")
    # ... rest of login logic uses target_page instead of self._page
```

This keeps backward compatibility with CLI usage while enabling graph node usage.

---

## Step 4: Update State Schema

**File:** `src/job_hunter/graph/state.py`

Add field to `JobHunterState`:

```python
class JobHunterState(TypedDict, total=False):
    # ... existing fields ...
    logged_in_platforms: list[str]  # Platforms successfully logged into
```

---

## Step 5: Reorder Workflow

**File:** `src/job_hunter/graph/workflow.py`

**Current:**
```python
workflow.add_edge("load_config", "parse_resume")
workflow.add_edge("parse_resume", "search_jobs")
```

**New:**
```python
workflow.add_edge("load_config", "parse_resume")
workflow.add_edge("parse_resume", "login_platforms")
workflow.add_edge("login_platforms", "search_jobs")
```

Also add the new node:
```python
from job_hunter.graph.nodes import login_platforms_node
workflow.add_node("login_platforms", login_platforms_node)
```

**Full new flow:**
```
load_config → parse_resume → login_platforms → search_jobs → score_jobs → filter_shortlist → export_csv → update_history → END
```

---

## Step 6: Update CLI

**File:** `src/job_hunter/cli.py`

**Current (login in CLI):**
```python
async def run_pipeline():
    browser = BrowserManager(headless=headless)
    page = await browser.start()

    try:
        logged_in = await browser.login_naukri()  # ← LOGIN HERE
        if not logged_in:
            raise SystemExit(1)

        initial_state = { ... }
        workflow = build_workflow()
        result = workflow.invoke(initial_state)  # ← SYNC INVOKE
```

**New (login in graph):**
```python
async def run_pipeline():
    browser = BrowserManager(headless=headless)
    page = await browser.start()

    try:
        # No login here — login happens inside the workflow
        initial_state = {
            "config": app_config,
            "resume_path": resume,
            "force_parse": force_parse,
            "profile": None,
            "detailed_profile": None,
            "raw_jobs": [],
            "scored_jobs": [],
            "shortlisted_jobs": [],
            "csv_path": "",
            "browser_page": page,
        }

        workflow = build_workflow()
        result = await workflow.ainvoke(initial_state)  # ← ASYNC INVOKE
```

**Changes:**
- Remove `browser.login_naukri()` call and its error handling
- Keep browser start/close lifecycle
- Change `workflow.invoke(initial_state)` to `await workflow.ainvoke(initial_state)`

---

## Step 7: Remove nest_asyncio Dependency

### 7.1 Remove from codebase

Remove all `import nest_asyncio` and `nest_asyncio.apply()` calls:

| File | Lines to Remove |
|------|-----------------|
| `src/job_hunter/search/naukri.py` | `import nest_asyncio`, `nest_asyncio.apply()`, `loop = asyncio.get_event_loop()`, all `loop.run_until_complete()` |
| `src/job_hunter/graph/nodes.py` | `import asyncio`, `import nest_asyncio`, `nest_asyncio.apply()`, `loop = asyncio.get_event_loop()`, `loop.run_until_complete()` in `parse_resume_node` |

### 7.2 Remove from dependencies

**File:** `pyproject.toml`

Remove `nest-asyncio` from the dependencies list.

---

## Data Flow (After Phase 3.0)

```
CLI:                          LangGraph Async Pipeline:
start browser ──┐              ┌──────────────────┐
                │              │ load_config       │ (async)
                │              │ parse_resume      │ (async) ← parses resume FIRST
                │              │ login_platforms   │ (async) ← NEW: login AFTER resume
                │              │ search_jobs       │ (async) ← native await, no nest_asyncio
                │              │ score_jobs        │ (async)
                │              │ filter_shortlist  │ (async)
                │              │ export_csv        │ (async)
                │              │ update_history    │ (async)
                │              └──────────────────┘
close browser ──┘
```

---

## Key Flow Change: Resume Before Login

```
OLD FLOW:                         NEW FLOW:
┌─────────────────────┐          ┌─────────────────────┐
│ CLI: Start browser  │          │ CLI: Start browser  │
│ CLI: Login to Naukri│ ← FIRST │                      │
│ Build workflow       │          │ Build workflow       │
│ Run workflow:        │          │ Run async workflow:  │
│   load_config       │          │   load_config        │
│   parse_resume      │          │   parse_resume       │ ← BEFORE LOGIN
│   search_jobs       │          │   login_platforms    │ ← NEW NODE
│   ...               │          │   search_jobs        │
└─────────────────────┘          └─────────────────────┘
```

**Why this matters:**
- Profile data is available at login time — enables platform selection based on profile
- Multi-platform login can be conditional on profile preferences
- Login failure only affects the platforms that fail, not the entire CLI

---

## Testing Strategy

### Unit Tests
- Test each async node independently with mock state
- Test `search_naukri()` as `await search_naukri()` directly
- Test `parse_resume_node()` with mock LLM
- Test `login_platforms_node()` with mock browser page

### Integration Tests
- Test full pipeline with `workflow.ainvoke()` — same results as sync pipeline
- Test login failure: should skip platform and continue
- Test with no platforms configured: should skip login and proceed
- Test browser lifecycle: start → workflow → close

### End-to-End Test
- Run full `job-hunter run` command
- Verify identical output to Phase 2b
- Verify login happens after resume parsing
- Verify `logged_in_platforms` is populated in state

---

## Rollback Plan

If async conversion causes critical issues:
1. Revert to sync pipeline with `nest_asyncio` (current state)
2. Move login back to CLI
3. Keep Phase 3.0 spec for future retry

Since this is a significant architecture change, always test on a branch before merging.

---

## Dependencies

- Phase 2b pipeline must be stable before this refactor
- All existing nodes must be present and working before conversion
- `nest_asyncio` must be present for rollback capability

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| LangGraph async node execution differs from sync | Medium | Test each node individually before wiring |
| Playwright page object across async boundaries | Medium | Pass page through state, verify session persists |
| Breaking existing output/behavior | High | Full E2E comparison test, git branch isolation |
| nest_asyncio removal breaks other code | Low | Audit all imports — only used in 2 places |
| Login failure in graph crashes pipeline | Medium | Robust error handling in login node, skip-on-failure |

---

## Effort

Estimated **5-7 days**:
- Step 1-2 (async conversion): 2-3 days
- Step 3 (login node): 1-2 days
- Step 4-7 (state, workflow, CLI, cleanup): 1 day
- Testing and validation: 1-2 days