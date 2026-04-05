# Roadmap
**Start Date**: 2026-04-04  
**Phase 0 Complete**: 2026-04-04  
**Phase 1 Complete**: 2026-04-05  
**Phase 2 Target**: TBD

## Timeline
| Phase | Name | Status | Start | End | Effort |
|-------|------|--------|-------|-----|--------|
| 0 | Foundation & Infrastructure | ✅ Complete | 2026-04-04 | 2026-04-04 | ~2 days |
| 1 | MVP Core Pipeline | ✅ Complete | 2026-04-04 | 2026-04-05 | ~3 days |
| 2 | Auto-Apply & Enrichment | 🔲 Not Started | TBD | TBD | ~5 days (est.) |
| 3 | Multi-Platform & Intelligence | 🔲 Not Started | TBD | TBD | TBD |

## Phase Dependencies
```
Phase 0 (Foundation) → Phase 1 (MVP Pipeline) → Phase 2 (Auto-Apply) → Phase 3 (Multi-Platform)
```

## Milestones
| Milestone | Phase | Target Date | Status |
|-----------|-------|-------------|--------|
| Project skeleton + SDD framework | 0 | 2026-04-04 | ✅ Done |
| Resume parsing + profile caching | 1 | 2026-04-05 | ✅ Done |
| Naukri scraper + deduplication | 1 | 2026-04-05 | ✅ Done |
| Scoring engine + CSV export | 1 | 2026-04-05 | ✅ Done |
| End-to-end MVP pipeline working | 1 | 2026-04-05 | ✅ Done |
| Auto-apply to Naukri jobs | 2 | TBD | 🔲 Planned |
| Multi-platform search | 2/3 | TBD | 🔲 Planned |

## Phase 2 Planned Scope (High-Level)
- Fix BUG-001 (interactive config prompts)
- Auto-apply pipeline node(s) in LangGraph StateGraph
- Smart QA node (uses `screening_answers` from config + LLM fallback)
- CSV write-back for apply status (`Applied` / `Failed` / `Already Applied`)
- Location match weighting enabled
- Resume change detection for cache invalidation
- Unit tests (scoring engine, parser, scraper)

## Phase 3 Planned Scope (High-Level)
- Multi-platform search: LinkedIn, Hirist, Instahyre, Foundit
- Company intelligence columns: `company_size`, `glassdoor_rating`, `core_business`
- Apply to LinkedIn / Indeed (if feasible)
