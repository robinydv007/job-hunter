# Phase 0 — Plan: Foundation & Infrastructure

## Implementation Approach

This phase is pre-business-logic scaffolding. The objective is to get a runnable, well-structured Python project in place with all the tooling layers defined.

### Module Structure Built

```
job-hunter-repo/
├── src/job_hunter/
│   ├── __init__.py          # Package init + version
│   ├── cli.py               # Click CLI: init, run, status commands
│   ├── config.py            # AppConfig, SearchConfig, ScoringConfig Pydantic models
│   ├── browser.py           # BrowserManager — Playwright session lifecycle
│   ├── graph/
│   │   ├── state.py         # JobHunterState TypedDict definition
│   │   └── workflow.py      # StateGraph shell (nodes wired in Phase 1)
│   └── llm/
│       └── provider.py      # LLMProvider singleton (Groq + OpenAI fallback)
├── config/
│   └── user.yaml            # Template config (created by `job-hunter init`)
├── specs/                   # Full SDD directory tree
├── scripts/                 # SDD compliance enforcement
└── .opencode/               # OpenCode commands, plugins, config
```

### Key Design Decisions

1. **UV as package manager** — Chosen over pip/poetry for speed and native lockfile support.
2. **Click + Rich for CLI** — Rich gives premium terminal output with minimal code.
3. **Pydantic v2 for config** — Full schema validation with readable error messages.
4. **LangGraph for orchestration** — Stateful StateGraph allows easy addition of new nodes in later phases without rearchitecting.
5. **Non-headless Playwright** — Headless mode triggers Naukri bot detection; non-headless is the safe default.
6. **Groq primary / OpenAI fallback** — Free tier for dev velocity, paid fallback for production reliability.
7. **SDD from day one** — The spec-driven system (phases, backlog, history, decisions) is established before writing any business logic.

### Risks Identified

| Risk | Mitigation |
|------|-----------|
| Naukri DOM changes breaking scraper | 7 progressive selector strategies in Phase 1 |
| Groq rate limits on first run | OpenAI fallback in LLM provider |
| Bot detection blocking Playwright | Anti-bot evasion headers + non-headless mode |

## Dependencies

None — this is Phase 0.

## Effort

~2 days of setup and scaffolding.
