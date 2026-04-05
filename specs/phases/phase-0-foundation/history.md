# Phase 0 — History Log

> Append-only log. Never edit existing entries. Format: [TYPE] YYYY-MM-DD — Short title

---

[DECISION] 2026-04-04 — Chose UV as Python package manager
Topics: tooling, packaging, dependency-management
Affects-phases: all
Affects-docs: specs/architecture/overview.md#technology-stack
Detail: Selected UV over pip and poetry for its speed and native lockfile (uv.lock). All contributors should use `uv run` to execute commands rather than activating a virtualenv manually.

[DECISION] 2026-04-04 — LangGraph chosen for pipeline orchestration
Topics: langgraph, orchestration, architecture
Affects-phases: phase-1-mvp-pipeline
Affects-docs: specs/architecture/overview.md#execution-pipeline
Detail: LangGraph's StateGraph model allows adding new pipeline nodes (Phase 2 auto-apply) without restructuring existing ones. The single `JobHunterState` acts as the shared data bus between all nodes.

[DECISION] 2026-04-04 — Non-headless Playwright as the default browser mode
Topics: playwright, browser, anti-bot
Affects-phases: phase-1-mvp-pipeline
Affects-docs: specs/architecture/overview.md#browser-manager
Detail: Naukri's bot detection triggers significantly more often in headless mode. Non-headless is safer and the `--headless` flag is provided as an opt-in escape hatch. Anti-bot evasion headers (webdriver spoofing, locale, timezone) are applied in both modes.

[DECISION] 2026-04-04 — Groq primary LLM with OpenAI gpt-4o fallback
Topics: llm, groq, openai, resilience
Affects-phases: phase-1-mvp-pipeline
Affects-docs: specs/architecture/overview.md#llm-provider
Detail: Groq's free tier speeds up development iteration. The LLMProvider auto-switches to OpenAI on rate-limit / 429 / quota / overloaded errors without user intervention, ensuring the pipeline doesn't fail for paid API users.

[NOTE] 2026-04-04 — SDD architecture adopted retroactively
Topics: sdd, specs, process
Affects-phases: none
Affects-docs: specs/README.md, CLAUDE.md
Detail: The SDD (Spec-Driven Development) framework was applied to this project after the MVP was already in progress. Phase 0 and Phase 1 documents were created retroactively to provide complete historical context for future phases and contributors.

[SCOPE_CHANGE] 2026-04-04 — Removed changelog directory from initial SDD template
Topics: sdd, specs
Affects-phases: none
Affects-docs: specs/README.md
Detail: The changelog directory referenced in specs/README.md was not created in this project's SDD setup. This is a known gap — to be populated during Phase 1 completion or retroactively by `/sync-docs`.
