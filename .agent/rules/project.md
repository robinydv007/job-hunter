# Project Rules

## Navigation (Where to Find Things)
| Question | File | Lines |
|----------|------|-------|
| Current state / what phase? | `specs/status.md` | ~50 |
| What's in the backlog? | `specs/backlog/backlog.md` | ~100 |
| Phase tasks/progress? | `specs/phases/phase-N-*/tasks.md` | ~150 |
| Why was X chosen? | `specs/decisions/NNNN-*.md` | ~50 |
| Overall timeline? | `specs/roadmap/roadmap.md` | ~60 |
| How this system works? | `docs/developer-guideline.md` | ~200 |

**First file to read: ALWAYS `specs/status.md`.**

## Autonomous Behaviors (Always-On Rules)
These rules are AUTOMATIC — the agent follows them without being asked.

### Rule 1: Always Orient First
Before ANY work, read `specs/status.md`. This tells you:
- What phase is active
- What's blocking progress
- What P0 items need attention

### Rule 2: Auto-Update Tracking After Changes
After completing ANY meaningful work (code change, fix, new feature), automatically update:
1. **Active phase `tasks.md`** — mark completed items `[x]`, in-progress `[/]`
2. **`specs/status.md`** — if phase progress, blockers, or P0 items changed
3. **`specs/changelog/YYYY-MM.md`** — log what changed (one line per change)
Do NOT wait for the user to ask you to update tracking. Just do it.

### Rule 3: Auto-Track Discoveries
When you discover a bug, tech debt, or enhancement opportunity during work:
- Add it to `specs/backlog/backlog.md` immediately with appropriate priority
- Mention it to the user: "I found [issue] and added it as [ID] to backlog"

### Rule 4: Pre-Phase Bug Check
Before starting work on a new phase:
- Scan `specs/backlog/backlog.md` for P0/P1 bugs
- If any exist, recommend addressing them first
- Present a summary: "N open bugs (X critical), recommend fixing before proceeding"

### Rule 5: Phase Boundary Awareness
When completing the last task in a phase:
- Prompt the user: "All tasks in Phase N are complete. Run `/complete-phase` to verify and release?"
- Do NOT auto-complete a phase without user confirmation

### Rule 6: Git Lifecycle (Automatic)
The agent handles the FULL git workflow automatically:

#### Starting Work
- **Before ANY code change**, check the current branch.
- If on `main` or `staging`, **auto-create a feature branch** before making changes:
  - Bug fix: `fix/BUG-NNN-short-desc` (e.g., `fix/BUG-001-state-lock`)
  - Feature: `feat/short-desc` (e.g., `feat/vpc-module`)
  - Tech debt: `refactor/TD-NNN-short-desc` (e.g., `refactor/TD-001-cleanup`)

#### During Work
- **Auto-commit** after each logical unit of work with conventional commits:
  - `feat(scope): description` — new functionality
  - `fix(scope): description` — bug fix
  - `infra(scope): description` — infrastructure changes
  - `docs: description` — documentation only
  - `refactor(scope): description` — code restructuring
  - `chore: description` — build/tooling
- Keep commits atomic — one logical change per commit
- Push to remote after significant milestones

#### Completing Work
When the work unit is done (bug fixed, feature complete, phase tasks done):
- Commit all remaining changes
- Push the branch to remote
- **ASK the user** before merging to `staging` or `main` — never auto-merge to protected branches
- If user approves merge: merge with `--no-ff`, push, then delete the feature branch

### Merge Safety Rules
| Action | Auto? | Requires User Approval? |
|--------|-------|------------------------|
| Create feature branch | Yes | No |
| Commit to feature branch | Yes | No |
| Push feature branch | Yes | No |
| Merge to `staging` | No | **Yes — always ask** |
| Merge to `main` | No | **Yes — always ask** |
| Tag a release | No | **Yes — always ask** |
| Delete feature branch after merge | Yes | No |

### Rule 7: Plan Before Implementing
For any non-trivial implementation (new module, phase start, architectural change):
- Use plan mode to design the approach first
- Present the plan for user approval before writing code

### Rule 8: Record Phase History
During any active phase, after making a meaningful change, append an entry to the phase's history file (`specs/phases/phase-N-*/history.md`).

**Entry types:**
| Type | When to use |
|------|------------|
| [DECISION] | ADR created or updated, technology choice made |
| [SCOPE_CHANGE] | Phase deliverables added, removed, or reprioritized |
| [DISCOVERY] | Bug, tech debt, or enhancement found |
| [FEATURE] | New planned feature added to this phase |
| [ARCH_CHANGE] | Architectural pattern or integration changed |
| [NOTE] | Anything else worth recording |

**Entry format (APPEND ONLY):**
```
[TYPE] YYYY-MM-DD — Short title (max 10 words)
Topics: topic-1, topic-2
Affects-phases: phase-N-name (or "none")
Affects-docs: path/to/doc.md#section (or "none")
Detail: One to three sentences describing what changed and why.
```
After writing an entry, check `specs/decisions/impact-map.json` — if the entry's topics aren't there, add them.

### Rule 9: Doc Sync Protocol — Never Mid-Phase, Always at Completion
- **During a phase**: Do NOT update other docs to reflect changes. Record to history.
- **At phase completion**: Run `/sync-docs` BEFORE `/complete-phase`.

## Naming Conventions (Backlog IDs)
| Type | Prefix | Example |
|------|--------|---------|
| Bug | `BUG-` | `BUG-001` |
| Feature | `FEAT-` | `FEAT-003` |
| Tech Debt | `TD-` | `TD-002` |
| Enhancement | `ENH-` | `ENH-001` |

## Priorities
| Level | Meaning | SLA |
|-------|---------|-----|
| `P0` | Critical — blocks current phase | Address immediately |
| `P1` | High — important | Current/next phase |
| `P2` | Medium | Within 2 phases |
| `P3` | Low — nice to have | When convenient |

## Git Branches
| Type | Pattern | Example |
|------|---------|---------|
| Phase | `phase-N-shortname` | `phase-0-bootstrap` |
| Feature | `feat/description` | `feat/vpc-peering` |
| Bug fix | `fix/description` | `fix/state-lock-timeout` |
| Refactor | `refactor/description` | `refactor/module-cleanup` |

## Git Commits (Conventional)
`feat:` | `fix:` | `docs:` | `refactor:` | `chore:` | `infra:`

## Constraints
1. **No secrets in code** — All credentials via Secrets Manager or env vars
2. **Never commit to main** — Always use feature/phase branches
3. **Plan before implementing** — Use plan mode for non-trivial work
