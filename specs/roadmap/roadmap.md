# Roadmap
**Start Date**: 2026-04-04  
**Phase 0 Complete**: 2026-04-04  
**Phase 1 Complete**: 2026-04-05  
**Phase 2a Complete**: 2026-04-07  
**Phase 2 Target**: TBD

## Timeline
| Phase | Name | Status | Start | End | Effort |
|-------|------|--------|-------|-----|--------|
| 0 | Foundation & Infrastructure | ✅ Complete | 2026-04-04 | 2026-04-04 | ~2 days |
| 1 | MVP Core Pipeline | ✅ Complete | 2026-04-04 | 2026-04-05 | ~3 days |
| 2a | Detailed Profile & Config Restructure | ✅ Complete | 2026-04-07 | 2026-04-07 | ~1 day |
| 2b | Auto-Apply & Batch Screening | 🔲 Not Started | TBD | TBD | ~4 days (est.) |
| 3.0 | Async Architecture Foundation | 🔲 Not Started | TBD | TBD | ~3 days (est.) |
| 3.1 | Multi-Platform Search | 🔲 Not Started | TBD | TBD | ~5 days (est.) | |

## Phase Dependencies
```
Phase 0 (Foundation) → Phase 1 (MVP Pipeline) → Phase 2a (Detailed Profile) → Phase 2b (Auto-Apply) → Phase 3.0 (Async Foundation) → Phase 3.1 (Multi-Platform)
```

## Milestones
| Milestone | Phase | Target Date | Status |
|-----------|-------|-------------|--------|
| Project skeleton + SDD framework | 0 | 2026-04-04 | ✅ Done |
| Resume parsing + profile caching | 1 | 2026-04-05 | ✅ Done |
| Naukri scraper + deduplication | 1 | 2026-04-05 | ✅ Done |
| Scoring engine + CSV export | 1 | 2026-04-05 | ✅ Done |
| End-to-end MVP pipeline working | 1 | 2026-04-05 | ✅ Done |
| Detailed profile + config restructure | 2a | 2026-04-07 | ✅ Done |
| Auto-apply to Naukri jobs | 2b | TBD | 🔲 Planned |
| Async architecture foundation | 3.0 | TBD | 🔲 Planned |
| Multi-platform search | 3.1 | TBD | 🔲 Planned |

## Phase 2 Planned Scope (High-Level)
- Fix BUG-001 (interactive config prompts)
- Auto-apply pipeline node(s) in LangGraph StateGraph
- Smart QA node (uses `screening_answers` from config + LLM fallback)
- CSV write-back for apply status (`Applied` / `Failed` / `Already Applied`)
- Location match weighting enabled
- Resume change detection for cache invalidation
- Unit tests (scoring engine, parser, scraper)

## Phase 3.0 Planned Scope (High-Level)
- Async Architecture Foundation
- Convert entire pipeline from sync+nest_asyncio to pure async
- Add login node to LangGraph workflow (ENH-017)
- Reorder pipeline: parse_resume → login_platforms → search_jobs
- Remove nest-asyncio dependency
- Enable multi-platform login support

## Phase 3.1 Planned Scope (High-Level)
- Multi-platform search: LinkedIn, Hirist, Instahyre, Foundit
- Company intelligence columns: `company_size`, `glassdoor_rating`, `core_business`
- Apply to LinkedIn / Indeed (if feasible)
