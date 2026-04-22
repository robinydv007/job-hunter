# Backlog
**Last Updated**: 2026-04-07  
**Convention**: Simple items stay in this table. Complex items get a detail file: `[→](details/ID.md)`

## Priority Levels
| Level | Meaning |
|-------|---------|
| **P0** | Critical — blocks current phase |
| **P1** | High — address in current/next phase |
| **P2** | Medium — address within 2 phases |
| **P3** | Low — nice to have |

**Status**: `open` | `in-progress` | `resolved` | `deferred` | `deprecated`

## Bugs
| ID | Title | Priority | Status | Phase | Detail |
|----|-------|----------|--------|-------|--------|
| BUG-001 | Missing interactive config prompts on `run` | P1 | resolved | 2 | [→](details/BUG-001.md) |

## Features
| ID | Title | Priority | Status | Phase | Detail |
|----|-------|----------|--------|-------|--------|
| FEAT-001 | Auto-apply pipeline (Naukri) | P0 | open | 2 | _(planned)_ |
| FEAT-002 | Smart screening QA node | P1 | open | 2 | _(planned)_ |
| FEAT-003 | Multi-platform search (LinkedIn, Hirist, Instahyre, Foundit) | P1 | open | 2/3 | _(planned)_ |
| FEAT-004 | Apply status CSV write-back | P1 | open | 2 | _(planned)_ |
| FEAT-005 | Company intelligence enrichment columns | P2 | open | 3 | _(planned)_ |
| ENH-018 | Review answers before apply (edit/regenerate) | P1 | open | 2b | [→](details/ENH-018.md) |
| ENH-019 | Export screening Q&A to CSV | P1 | open | 2b | [→](details/ENH-019.md) |

## Tech Debt
| ID | Title | Priority | Status | Phase | Detail |
|----|-------|----------|--------|-------|--------|
| TD-001 | Unit tests: scoring engine, parser, scraper | P1 | open | 2 | _(simple)_ |
| TD-002 | Resume cache invalidation on file change | P2 | resolved | 2a | Implemented in Phase 2a with SHA256 hash detection |
| TD-003 | LLM-based required_skills extraction per job | P3 | open | 3 | _(expensive — phase 3 candidate)_ |
| TD-004 | Prune unused fields from `JobHunterState` | P2 | resolved | 2 | [→](details/TD-004.md) |

## Enhancements
| ID | Title | Priority | Status | Phase | Detail |
|----|-------|----------|--------|-------|--------|
| ENH-001 | Enable location match scoring (LOCATION_WEIGHT > 0) | P2 | open | 2 | _(simple)_ |
| ENH-002 | Work-mode filter (remote/hybrid/on-site) in config | P2 | open | 2 | _(simple)_ |
| ENH-003 | Expand config: search params, auto-apply controls, screening answers | P1 | resolved | 2 | [→](details/ENH-003.md) |
| ENH-004 | Smart job freshness filter with auto-calculation from last run | P1 | resolved | 2 | [→](details/ENH-004.md) |
| ENH-005 | Overhaul search query generation: role-only, remove arbitrary caps, configurable limits | P1 | resolved | 2 | [→](details/ENH-005.md) |
| ENH-010 | Pan-India fallback: add locationless query when locations < max_locations | P1 | open | 2 | [→](details/ENH-010.md) |
| ENH-006 | Anti-blocking: randomize timing (delays, jitter, scroll behavior) | P1 | resolved | 2 | [→](details/ENH-006.md) |
| ENH-007 | Anti-blocking: CAPTCHA detection + session health checks | P1 | open | 2 | [→](details/ENH-007.md) |
| ENH-008 | Anti-blocking: Playwright stealth mode (webdriver masking) | P2 | open | 2 | [→](details/ENH-008.md) |
| ENH-009 | Anti-blocking: exponential backoff on consecutive failures | P2 | open | 2 | [→](details/ENH-009.md) |
| ENH-011 | Improve search_naukri method: add more parameters for flexibility | P2 | open | 2 | _(simple)_ |
| ENH-012 | Refactor nodes.py: extract platform-specific code to separate files | P2 | resolved | 1 | [→](details/ENH-012.md) |
| ENH-013 | Extract static scoring data to config/constants.yaml | P1 | resolved | 1 | [→](details/ENH-013.md) |
| ENH-014 | Refactor CSV export: single source of truth for columns | P2 | resolved | 1 | [→](details/ENH-014.md) |
| ENH-015 | LLM-Based Job Scoring | P1 | resolved | 1 | [→](details/ENH-015.md) |
| ENH-016 | Fix Naukri pagination using UI navigation | P1 | resolved | 2 | [→](details/ENH-016.md) |
| ENH-017 | Reorder pipeline: parse resume before login | P1 | open | 2 | [→](details/ENH-017.md) |
| ENH-020 | Include detailed profile in LLM answer context | P1 | open | 2b | [→](details/ENH-020.md) |

> **Note (2026-04-07)**: Current work-around is login in CLI before workflow. Implementation attempts inside LangGraph workflow have failed due to async/sync conflicts between login node and sync search_naukri function.
