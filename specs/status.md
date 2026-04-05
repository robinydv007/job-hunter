# Project Status
**Last Updated**: 2026-04-05  
**Current Phase**: Phase 1 — MVP Core Pipeline (`complete`)  
**Latest Release**: v0.1.0  
**Health**: On Track ✅

## Summary

Job Hunter AI Agent is a local Python CLI tool that automates job hunting on Indian platforms. Given a user resume and config file, it independently discovers jobs on Naukri, scores them against the user's profile using a 6-factor weighted rubric, and exports a ranked shortlist to CSV. Phases 0 (Foundation) and 1 (MVP Pipeline) are complete. The agent is fully functional for the MVP use case. Phase 2 (Auto-Apply & Enrichment) is the next planned phase.

## Completed Phases
| Phase | Name | Status | Release |
|-------|------|--------|---------|
| 0 | Foundation & Infrastructure | ✅ Complete | v0.0.1 |
| 1 | MVP Core Pipeline | ✅ Complete | v0.1.0 |

## Active Phase
*(No active phase — Phase 1 is complete. Phase 2 not yet started.)*

## Upcoming Phases
| Phase | Name | Status | Key Deliverables |
|-------|------|--------|-----------------|
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
| BUG-001 | Bug | Missing interactive config prompts on `run` command |

## Next Actions
1. Fix BUG-001 (interactive config prompts) before starting Phase 2
2. Write Phase 2 plan: `specs/phases/phase-2-auto-apply/overview.md`
3. Run `/start-phase` to begin Phase 2

## Key Decisions Made
- **UV** chosen as Python package manager (speed + native lockfile)
- **LangGraph StateGraph** for pipeline orchestration (extensible for Phase 2 nodes)
- **Non-headless Playwright** as default (headless triggers Naukri bot detection)
- **Groq primary / OpenAI fallback** for LLM calls
- **Location weight = 0.0** in scoring engine (intentional — remote/hybrid listings unreliable)

## Recent Changes
- 2026-04-05: Phase 1 MVP pipeline completed — all 6 LangGraph nodes implemented and validated
- 2026-04-05: Architecture overview (`specs/architecture/overview.md`) written
- 2026-04-05: BUG-001 discovered and logged to backlog
- 2026-04-04: Phase 0 Foundation completed — project skeleton, SDD setup, CLI, LLM provider, browser manager
