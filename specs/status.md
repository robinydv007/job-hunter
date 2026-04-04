# Project Status
**Last Updated**: 2026-04-02
**Current Phase**: Phase 1 — Vectorless RAG (`in-progress`)
**Latest Release**: None
**Health**: On Track

## Summary
Phase 1 (Vectorless RAG Chatbot) in progress. Building a document-based Q&A application using BM25 keyword retrieval instead of vector embeddings.

## Active Phase
| Phase | Name | Status | Progress |
|-------|------|--------|----------|
| 1 | Vectorless RAG | In Progress | 0% |

## Upcoming Phases
| Phase | Name | Status | Key Deliverables |
|-------|------|--------|-----------------|
| 2 | TBD | Not Started | |

## Blockers
| ID | Description | Severity |
|----|-------------|----------|
| _(none)_ | | |

## Critical Items (P0)
| ID | Type | Description |
|----|------|-------------|
| _(none)_ | | |

## Next Actions
1. Implement Phase 1: Vectorless RAG chatbot
2. Fix BUG-007 (duplicate command definitions) as part of this phase

## Key Decisions Made
- **2026-04-02**: OpenCode selected as primary AI agent over Claude Code — full migration of commands and hooks to OpenCode format (see [ADR-0001](decisions/0001-use-opencode.md))
- **2026-04-02**: Spec-driven development system adopted for project management
- **2026-04-02**: Phase history + doc sync pattern chosen over mid-phase doc updates

## Recent Changes
* **2026-04-02**: Phase 1 started — Vectorless RAG Chatbot
* **2026-04-02**: 7 bugs added to backlog from SDD architecture audit
* **2026-04-02**: SDD enforcement system added — hard blocks on non-compliant commits
* **2026-04-02**: Phase 0 marked complete — all tracking docs synced
* **2026-04-02**: Migrated from Claude Code to OpenCode format (commands, plugins, config)
* **2026-04-02**: Project management structure initialized
