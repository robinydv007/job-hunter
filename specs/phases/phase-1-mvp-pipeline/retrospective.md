# Phase 1 — Retrospective: MVP Core Pipeline

**Completed:** 2026-04-05  
**Release:** v0.1.0

---

## What Went Well

- **LangGraph StateGraph** — The linear pipeline model made debugging straightforward: each node's inputs and outputs could be inspected independently by checking the `JobHunterState` at any step. Adding or modifying a node required no changes to other nodes.
- **Pydantic for data contracts** — `ResumeProfile`, `JobListing`, and `ScoredJob` models caught malformed LLM output and scraper data early, preventing silent failures downstream.
- **7-selector scraper resilience** — The progressive CSS strategy successfully found jobs across multiple Naukri UI states encountered during testing (search results page, lazy-load states, partial DOM loads).
- **Cross-run deduplication** — The fingerprinting approach (scanning past CSV files) worked cleanly. Over multiple test runs, no job appeared in two consecutive shortlists.
- **LLM resume extraction quality** — Groq `llama-3.3-70b-versatile` consistently extracted skills, experience, and target roles with high fidelity from a real-world PDF resume.

## What Could Have Been Better

- **No unit tests written** — The entire Phase 1 was validated through manual end-to-end runs. This is acceptable for a solo-run MVP but is a gap for long-term maintainability. Tests should be a Phase 2 deliverable.
- **Required_skills extraction is a heuristic** — Currently uses a static keyword list to detect skills from job descriptions. This misses domain-specific or less common tools. An LLM-based skills extraction per job would be more accurate but expensive.
- **Location scoring skip** — Leaving location at 0% weight means the scoring engine is functionally 93% weighted on 4 factors. This is fine but the field being there at 0% causes confusion.
- **BUG-001 not fixed before MVP completion** — The missing interactive prompts bug was discovered during testing but not fixed. It should be addressed at the start of Phase 2.

## Lessons Learned

1. **Scraper first, scorer second** — It was tempting to build the scoring engine first (it's more interesting), but the scraper is the true critical path. Build and validate the data source before writing anything that depends on it.
2. **Cache aggressively for LLM calls** — Resume parsing would have consumed most of the Groq free tier quota if re-run on every test. The `data/profile.json` cache was essential for fast iteration.
3. **Non-headless browser adds friction but prevents failures** — Having a browser window pop up during every test was distracting, but attempts to run headlessly consistently triggered Naukri CAPTCHAs.

## Metrics

| Metric | Value |
|--------|-------|
| Duration | ~3 days |
| New modules created | 6 (parser, scraper, engine, exporter, nodes, workflow) |
| Pipeline nodes implemented | 6 |
| CSV columns in export | 15 |
| Test coverage | 0% (manual validation only) |
| Bugs discovered | 2 (BUG-001 + location weight issue) |
| End-to-end runs completed | ~10 test runs |

## Open Items for Phase 2

| Item | Type | Priority |
|------|------|---------|
| BUG-001: Interactive config prompts | Bug | P1 |
| Location weight fix / work-mode filter | Enhancement | P2 |
| Resume cache invalidation on change | Tech Debt | P2 |
| LLM-based required_skills extraction per job | Enhancement | P3 |
| Unit tests for scoring, parser, scraper | Tech Debt | P1 |
| Multi-platform search (LinkedIn, Hirist, Instahyre) | Feature | P1 |
| Auto-apply pipeline (the core Phase 2 feature) | Feature | P0 |
