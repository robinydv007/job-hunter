# Project Status
**Last Updated**: 2026-04-06  
**Current Phase**: Phase 1 — MVP Core Pipeline (`complete`)  
**Latest Release**: v0.1.0  
**Health**: On Track ✅

## Summary

Job Hunter AI Agent is a local Python CLI tool that automates job hunting on Indian platforms. Given a user resume and config file, it independently discovers jobs on Naukri, scores them against your profile using a 6-factor weighted rubric, and exports a ranked shortlist to CSV. Phases 0 (Foundation) and 1 (MVP Pipeline) are complete. The agent is fully functional for the MVP use case. Phase 2 (Auto-Apply & Enrichment) is the next planned phase.

## Completed Phases
| Phase | Name | Status | Release |
|-------|------|--------|---------|
| 0 | Foundation & Infrastructure | ✅ Complete | v0.0.1 |
| 1 | MVP Core Pipeline | ✅ Complete | v0.1.0 |

## Active Phase
*(No active phase — Phase 1 is complete. Phase 2 not yet started.)*

## Upcoming Phases
| Phase | Name | Status | Key Deliverables |
|-------|------|--------|------------------|
| 2 | Auto-Apply & Enrichment | 🔲 Not Started | Auto-apply to jobs above threshold, smart QA, multi-platform search, company intelligence |

## Blockers
| ID | Description | Severity |
|----|-------------|----------|
| _(none)_ | | |

## Critical Items (P0)
| ID | Type | Description |
|----|------|-------------|
| _(none)_ | | |

## Open P1 Items
| ID | Type | Description |
|----|------|-------------|
| _(none)_ | | |

## Next Actions
1. Write Phase 2 plan: `specs/phases/phase-2-auto-apply/overview.md`
2. Run `/start-phase` to begin Phase 2

## Key Decisions Made
- **UV** chosen as Python package manager (speed + native lockfile)
- **LangGraph StateGraph** for pipeline orchestration (extensible for Phase 2 nodes)
- **Non-headless Playwright** as default (headless triggers Naukri bot detection)
- **Groq primary / OpenAI fallback** for LLM calls
- **Location weight = 0.0** in scoring engine (intentional — remote/hybrid listings unreliable)

## Recent Changes
- 2026-04-06: enh(ENH-013) — extract static scoring data to `config/constants.yaml`; add scoring weights to user.yaml; strip ~270 lines of hardcoded data from engine.py
- 2026-04-06: enh(ENH-012) — fix Naukri base_url bug by extracting to `config/job_boards/naukri.py`
- 2026-04-06: enh(ENH-014) — refactor CSV export with single source of truth (`ROW_MAPPING` dict)
- 2026-04-06: fix(scoring) — experience penalty key type mismatch (YAML int keys vs string conversion)
- 2026-04-06: fix(config) — path resolution for config/__init__.py (parents[2] -> parents[3])
- 2026-04-06: fix(console) — unicode encode error on Windows (→ ->)
- 2026-04-06: feat(scoring) — revamp scoring v2 with 6 dimensions: skills 35%, role 20%, experience 20%, company 10%, location 8%, work_mode 7%; add skill aliases, word-boundary matching, concatenated skill splitting
- 2026-04-06: feat(search) — add company rating & review extraction from Naukri job cards
- 2026-04-06: feat(search) — implement pagination for Naukri search with smart page calculation (max 5 pages per query, exits early when max_jobs reached)
- 2026-04-05: feat(cli) — resume caching with --force-parse override; skips LLM parse when profile cached
- 2026-04-05: feat(search) — user.yaml preferred_roles takes priority over parsed target_roles
- 2026-04-05: feat(scoring) — title tech penalty halves score if job title requires tech user lacks
- 2026-04-05: BUG-001 fixed — interactive config prompts now run before pipeline starts
- 2026-04-05: Phase 1 MVP pipeline completed — all 6 LangGraph nodes implemented and validated
- 2026-04-05: Architecture overview (`specs/architecture/overview.md`) written
- 2026-04-05: BUG-001 discovered and logged to backlog
- 2026-04-04: Phase 0 Foundation completed — project skeleton, SDD setup, CLI, LLM provider, browser manager
