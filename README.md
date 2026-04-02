# Spec-Driven Development Project

A project management system for spec-driven development with AI agents.

## Overview

This repository implements a **spec-driven development (SDD)** workflow where:
- Every phase of work is planned before coding starts
- AI agents and developers share the same source of truth (`specs/`)
- Tracking is automatic — agents update status, changelog, and tasks as they work
- Phase history captures decisions and discoveries as they happen
- Git discipline is built in — automatic branching, atomic commits, safe merges

## Quick Start

1. Read `specs/status.md` to understand the current state
2. Read `docs/developer-guideline.md` for how to work with this system
3. Write your vision document in `docs/<project-name>.md`
4. Run `/start-phase` to begin Phase 0

## Structure

| Path | Purpose |
|------|---------|
| `specs/` | Single source of truth — status, backlog, phases, decisions, roadmap |
| `docs/` | Developer documentation and vision |
| `.claude/commands/` | Slash commands for phase workflows |
| `.agent/rules/` | Agent operational rules |
| `scripts/` | Automation hooks |

## Key Commands

| Command | Purpose |
|---------|---------|
| `/start-phase` | Begin a new implementation phase |
| `/complete-phase` | Verify and release a completed phase |
| `/sync-docs` | Propagate phase history to docs |
| `/log` | Record a manual history entry |
| `/track` | Add a backlog item |
| `/review` | Groom the backlog between phases |

## Development Cycle

```
DISCOVER → PLAN → IMPLEMENT → VERIFY → SYNC → RELEASE
```

See `docs/developer-guideline.md` for the complete guide.
