# SDD Project Bootstrap

**Page • Resources**

**Purpose**: Feed this document to an agent at the start of any new repository. The agent will scaffold the full spec-driven project structure — folders, rules, workflows, tracking system, and `CLAUDE.md` — so that humans and agents can develop together from day one.

**Version**: 2.0 — Includes phase history, impact maps, doc-sync discipline, and Claude Code hooks.

---

## What This Sets Up
A **spec-driven development system** where:
*   Every phase of work is planned before coding starts
*   Agents and developers share the same source of truth (`specs/`)
*   The backlog, changelog, decisions, and status are always up to date
*   Phase history captures decisions and discoveries as they happen — docs are synced at phase completion
*   Git discipline is automatic and consistent
*   Claude Code (via `CLAUDE.md`), slash commands (via `.claude/commands/`), and agent rules (via `.agent/rules/`) know the system without being told

## The Core Insight
During implementation, decisions change, scope shifts, and new things are discovered. Without a system, these changes drift — docs reference stale information, future phases plan against outdated assumptions. The solution: **Phase History**. This keeps the agent focused on implementation while ensuring nothing is lost.

---

## Step 1: Create the Directory Structure
```
/
├── CLAUDE.md # Claude Code configuration (Rules 1-9)
├── README.md # Project overview
├── docs/
│   ├── .md # Vision / master plan document
│   ├── developer-guide.md # How this system works
│   └── naming-conventions.md # File & folder naming standard
├── specs/
│   ├── README.md # Specs index
│   ├── status.md # Current phase, blockers, P0 items
│   ├── backlog/
│   │   ├── backlog.md # All bugs, features, tech debt, enhancements
│   │   └── details/ # Detail files for complex items
│   │       └── .gitkeep
│   ├── changelog/
│   │   └── YYYY-MM.md # Monthly changelog (create for current month)
│   ├── decisions/
│   │   ├── README.md # ADR index
│   │   ├── 0000-template.md # ADR template
│   │   └── impact-map.json # Topic → doc files map (used by /sync-docs)
│   ├── phases/
│   │   ├── README.md # Phase index
│   │   └── index.json # Phase → topics map (used by /sync-docs)
│   ├── roadmap/
│   │   └── roadmap.md # Timeline and phase dependencies
│   └── vision/
│       ├── principles.md # Engineering principles
│       ├── project-charter.md # Why this project exists
│       └── success-criteria.md # How we know we've succeeded
├── scripts/
│   └── check-history-reminder.sh # PostToolUse hook (read-only reminder)
├── .claude/
│   ├── settings.json # Shared hook config (committed)
│   └── commands/ # Slash command definitions
│       ├── start-phase.md # /start-phase
│       ├── complete-phase.md # /complete-phase
│       ├── sync-docs.md # /sync-docs
│       ├── log.md # /log
│       ├── track.md # /track
│       └── review.md # /review
└── .agent/
    └── rules/
        └── project.md # Agent operational rules (always-on behaviors)
```

**Create all directories:**
```bash
mkdir -p docs \
specs/backlog/details \
specs/changelog \
specs/decisions \
specs/phases \
specs/roadmap \
specs/vision \
scripts \
.claude/commands \
.agent/rules
touch specs/backlog/details/.gitkeep
```

---

## Step 2: Create `CLAUDE.md`
This is the Claude Code configuration file. It loads automatically on every session.

```markdown
# Project Rules
Claude Code configuration. Agent rules live in `.agent/rules/project.md` — do not modify.

## Navigation (Where to Find Things)
| Question | File |
|----------|------|
| Current state / what phase? | `specs/status.md` |
| What's in the backlog? | `specs/backlog/backlog.md` |
| Phase tasks/progress? | `specs/phases/phase-N-*/tasks.md` |
| Why was X chosen? | `specs/decisions/NNNN-*.md` |
| Overall timeline? | `specs/roadmap/roadmap.md` |
| How this system works? | `docs/developer-guide.md` |

**First file to read: ALWAYS `specs/status.md`.**

## Autonomous Behaviors (Always-On Rules)
### Rule 1: Always Orient First
Before ANY work, read `specs/status.md`. This tells you:
* What phase is active
* What's blocking progress
* What P0 items need attention

### Rule 2: Auto-Update Tracking After Changes
After completing ANY meaningful work, automatically update:
1. **Active phase `tasks.md`** — mark completed `[x]`, in-progress `[/]`
2. **`specs/status.md`** — if phase progress, blockers, or P0 items changed
3. **`specs/changelog/YYYY-MM.md`** — log what changed (one line per change)
Use the built-in **TodoWrite** tool to track in-session task progress. Do NOT wait for the user to ask you to update tracking.

### Rule 3: Auto-Track Discoveries
When you discover a bug, tech debt, or enhancement during work:
* Add it to `specs/backlog/backlog.md` immediately with appropriate priority
* Mention it to the user: "I found [issue] and added it as [ID] to backlog"

### Rule 4: Pre-Phase Bug Check
Before starting work on a new phase:
* Scan `specs/backlog/backlog.md` for P0/P1 bugs
* If any exist, recommend addressing them first
* Present: "N open bugs (X critical), recommend fixing before proceeding"

### Rule 5: Phase Boundary Awareness
When completing the last task in a phase:
* Prompt the user: "All tasks in Phase N are complete. Run `/complete_phase` to verify and release?"
* Do NOT auto-complete a phase without user confirmation

### Rule 6: Git Lifecycle (Automatic)
#### Starting Work
* **Before ANY code change**, check current branch.
* Branch naming:
    * Bug fix: `fix/BUG-NNN-short-desc`
    * Feature: `feat/short-desc`
    * Tech debt: `refactor/TD-NNN-short-desc`

#### During Work
* **Auto-commit** after each logical unit with conventional commits:
    * `feat(scope):` | `fix(scope):` | `infra(scope):` | `docs:` | `refactor(scope):` | `chore:`
* Keep commits atomic — one logical change per commit
* Push to remote after significant milestones

#### Completing Work
* Commit all remaining changes, push branch
* **ASK the user** before merging to `staging` or `main` — never auto-merge to protected branches

| Action | Auto? | Requires Approval? |
|--------|-------|--------------------|
| Create feature branch | Yes | No |
| Commit to feature branch | Yes | No |
| Push feature branch | Yes | No |
| Merge to `staging` | No | **Yes** |
| Merge to `main` | No | **Yes** |
| Tag a release | No | **Yes** |
| Delete branch after merge | Yes | No |

### Rule 7: Plan Before Implementing
For any non-trivial implementation (new module, phase start, architectural change):
* Use built-in plan mode to design the approach first
* Present the plan for user approval before writing code

### Rule 8: Record Phase History
During any active phase, after making a meaningful change, append an entry to the phase's history file (`specs/phases/history.md`).

**What counts as meaningful:**
* An ADR was created or its status/decision changed → `[DECISION]`
* Phase scope was added to or reduced → `[SCOPE_CHANGE]`
* A bug, tech debt, or enhancement was added to backlog → `[DISCOVERY]`
* A new feature was added to the phase plan → `[FEATURE]`
* An architectural pattern or integration approach changed → `[ARCH_CHANGE]`

**Entry format (APPEND ONLY — never edit existing entries):**
```
[TYPE] YYYY-MM-DD — Short title
Topics: topic-1, topic-2
Affects-phases: phase-N-name (or "none")
Affects-docs: path/to/doc.md#section (or "none")
Detail: One to three sentences describing what changed and why.
```
**After writing the entry**, check `specs/decisions/impact-map.json` — if the entry's topics aren't there, add them.
The hook (`scripts/check-history-reminder.sh`) will also remind you if you forget.

### Rule 9: Doc Sync Protocol — Never Mid-Phase, Always at Completion
* **During a phase**: Do NOT update other docs to reflect changes. Just record to history. Stay focused on implementation.
* **Exception**: Direct doc-only tasks (user explicitly asked to update a doc) are fine.
* **At phase completion**: Run `/sync-docs` BEFORE running `/complete-phase`. This propagates all history-recorded changes to relevant docs in a single targeted pass.
```

---

## Step 3: Create `.agent/rules/project.md`
Agent-specific rules (more detailed than `CLAUDE.md`, loaded by Claude Code agents).

```markdown
# Project Rules

## Navigation (Where to Find Things)
| Question | File | Lines |
|----------|------|-------|
| Current state / what phase? | `specs/status.md` | ~50 |
| What's in the backlog? | `specs/backlog/backlog.md` | ~100 |
| Phase tasks/progress? | `specs/phases/phase-N-*/tasks.md` | ~150 |
| Why was X chosen? | `specs/decisions/NNNN-*.md` | ~50 |
| Overall timeline? | `specs/roadmap/roadmap.md` | ~60 |
| How this system works? | `docs/developer-guide.md` | ~200 |

**First file to read: ALWAYS `specs/status.md`.**

## Autonomous Behaviors (Always-On Rules)
These rules are AUTOMATIC — the agent follows them without being asked.

### Rule 1: Always Orient First
Before ANY work, read `specs/status.md`. This tells you:
* What phase is active
* What's blocking progress
* What P0 items need attention

### Rule 2: Auto-Update Tracking After Changes
After completing ANY meaningful work (code change, fix, new feature), automatically update:
1. **Active phase `tasks.md`** — mark completed items `[x]`, in-progress `[/]`
2. **`specs/status.md`** — if phase progress, blockers, or P0 items changed
3. **`specs/changelog/YYYY-MM.md`** — log what changed (one line per change)
Do NOT wait for the user to ask you to update tracking. Just do it.

### Rule 3: Auto-Track Discoveries
When you discover a bug, tech debt, or enhancement opportunity during work:
* Add it to `specs/backlog/backlog.md` immediately with appropriate priority
* Mention it to the user: "I found [issue] and added it as [ID] to backlog"

### Rule 4: Pre-Phase Bug Check
Before starting work on a new phase:
* Scan `specs/backlog/backlog.md` for P0/P1 bugs
* If any exist, recommend addressing them first
* Present a summary: "N open bugs (X critical), recommend fixing before proceeding"

### Rule 5: Phase Boundary Awareness
When completing the last task in a phase:
* Prompt the user: "All tasks in Phase N are complete. Run `/complete_phase` to verify and release?"
* Do NOT auto-complete a phase without user confirmation

### Rule 6: Git Lifecycle (Automatic)
The agent handles the FULL git workflow automatically:
#### Starting Work
* **Before ANY code change**, check the current branch.
* If on `main` or `staging`, **auto-create a feature branch** before making changes:
    * Bug fix: `fix/BUG-NNN-short-desc` (e.g., `fix/BUG-001-state-lock`)
    * Feature: `feat/short-desc` (e.g., `feat/vpc-module`)
    * Tech debt: `refactor/TD-NNN-short-desc` (e.g., `refactor/TD-001-cleanup`)

#### During Work
* **Auto-commit** after each logical unit of work with conventional commits:
    * `feat(scope): description` — new functionality
    * `fix(scope): description` — bug fix
    * `infra(scope): description` — infrastructure changes
    * `docs: description` — documentation only
    * `refactor(scope): description` — code restructuring
    * `chore: description` — build/tooling
* Keep commits atomic — one logical change per commit
* Push to remote after significant milestones

#### Completing Work
When the work unit is done (bug fixed, feature complete, phase tasks done):
* Commit all remaining changes
* Push the branch to remote
* **ASK the user** before merging to `staging` or `main` — never auto-merge to protected branches
* If user approves merge: merge with `--no-ff`, push, then delete the feature branch

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
* Use plan mode to design the approach first
* Present the plan for user approval before writing code

### Rule 8: Record Phase History
During any active phase, after making a meaningful change, append an entry to the phase's history file (`specs/phases//history.md`).

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
* **During a phase**: Do NOT update other docs to reflect changes. Record to history.
* **At phase completion**: Run `/sync-docs` BEFORE `/complete-phase`.
```

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

---

## Step 4: Create the Claude Code Slash Commands
These go in `.claude/commands/` and define the `/slash` commands available to the agent.

### `.claude/commands/start-phase.md`
```markdown
Begin a new implementation phase.

## Steps
1. Read current state:
   * Read `specs/status.md`
2. Check for blocking bugs (Rule 4 — pre-phase bug check):
   * Scan `specs/backlog/backlog.md` for P0/P1 items
   * If P0 bugs exist → report to user, recommend fixing first
   * If only P1 → continue but note them
3. Create the phase directory if it doesn't exist:
   `specs/phases/phase-N-shortname/`
   ├── overview.md ← Scope, goals, deliverables, acceptance criteria
   ├── plan.md ← Implementation approach, steps, risks
   └── tasks.md ← Detailed checklist

Use existing phase directories as reference (e.g., `phase-0-bootstrap/`).

4. Build phase topic index:
   * Read the phase's `overview.md` and `tasks.md`
   * Extract key topics: technology names, services, architectural concepts
   * Add/update the phase entry in `specs/phases/index.json`:
   ```json
   "phase-N-name": {
     "status": "in-progress",
     "topics": ["topic-1", "topic-2", ...]
   }
   ```
5. Create the phase history file: `specs/phases/phase-N-name/history.md` from the template (see Step 10)
6. Update `specs/phases/README.md`:
   * Change phase status: `Not Started` → `In Progress`
   * Add link to the phase directory
7. Update `specs/status.md`:
   * Set "Current Phase" to the new phase
   * Update "Active Phase" table
   * Clear/update blockers
8. Create git branch and initial commit:
   ```bash
   git checkout main && git pull origin main
   git checkout -b phase-N-shortname
   git add specs/
   git commit -m "docs: start Phase N - {phase name}"
   git push -u origin phase-N-shortname
   ```
9. Update `specs/changelog/YYYY-MM.md` with phase start entry.
```

### `.claude/commands/complete-phase.md`
```markdown
Verify, finalize, and release a completed phase.

## Steps
### Verify
1. Read the phase's acceptance criteria:
   * Read `specs/phases/phase-N-*/overview.md`
2. Verify all tasks are done:
   * Read `specs/phases/phase-N-*/tasks.md`
   * If any `[ ]` unchecked items remain → report to user, do NOT proceed
3. Run project-specific validation (tests, linting, infra checks).
4. Check for new bugs discovered during the phase:
   * Grep `specs/backlog/backlog.md` for items tagged to this phase

### Finalize
**Step F0: Sync docs from phase history (run BEFORE other finalize steps)**
* Run `/sync-docs` to propagate all history-recorded changes to relevant documents
* This must complete before creating the retrospective, as the retrospective references updated docs
* If /sync-docs finds nothing to update, proceed directly

1. Create retrospective in the phase directory:
   * `specs/phases/phase-N-*/retrospective.md`
   * What went well, what didn't, lessons learned
2. Update all tracking:
   * `specs/phases/README.md` → mark `Complete`
   * `specs/status.md` → update current phase to next, add release version
   * `specs/roadmap/roadmap.md` → update phase status
   * `specs/changelog/YYYY-MM.md` → add release entry

### Release
**Git flow: `phase-N-shortname → staging → main → tag + GitHub Release`**
Never tag or release directly from a phase branch.
1. Commit all remaining changes on phase branch and push:
   ```bash
   git add -A
   git commit -m "docs: complete Phase N - {phase name}"
   git push origin phase-N-shortname
   ```
2. Merge phase branch → staging (ask user for approval first):
   ```bash
   git checkout staging
   git merge --no-ff phase-N-shortname -m "merge: phase-N-shortname → staging (vX.Y.Z)"
   git push origin staging
   ```
3. Merge staging → main (ask user for approval first):
   ```bash
   git checkout main
   git merge --no-ff staging -m "merge: staging → main (vX.Y.Z — Phase N: {phase name})"
   git push origin main
   ```
4. Tag on main + create GitHub Release (ask user for approval first):
   ```bash
   git checkout main
   git tag -a vX.Y.Z -m "Phase N: {phase name}"
   git push origin vX.Y.Z
   gh release create vX.Y.Z \
     --title "vX.Y.Z — Phase N: {phase name}" \
     --notes "## Phase N: {phase name}
     
Next: Phase N+1 — {next phase name}
{key deliverables of next phase}" \
     --target main
   ```
5. Report summary to user:
   * What was delivered this phase
   * GitHub Release URL (returned by `gh release create`)
   * What's next (phase name + key deliverables)
   * Remind to delete phase branch after merge: `git push origin --delete phase-N-shortname`
```

### `.claude/commands/sync-docs.md`
```markdown
Sync all relevant documents based on the active phase's history log.
Token-efficient: reads history + 2 tiny indexes first, then only targeted files.

## Steps
### Step 1: Load history and indexes (cheap reads)
* Read `specs/status.md` → identify active phase
* Read `specs/phases//history.md` → extract all entries
* Read `specs/phases/index.json` (~2KB)
* Read `specs/decisions/impact-map.json` (~3KB)

### Step 2: Build targeted file list
For each history entry:
* Extract Topics list
* Look up each topic in `index.json` → collect affected phase `tasks.md` files
* Look up each topic in `impact-map.json` → collect affected doc files/sections

### Step 3: Show sync plan (ALWAYS show before touching anything)
Present to user:
"Based on phase history, I will check and potentially update:
* [list of files]
Proceed? (yes/no)"
If user says no → stop.

### Step 4: Read and assess (targeted reads only)
For each file in the list:
* Read only the relevant section (not the whole file if section is specified)
* Assess: does it need updating based on history entries?
* If yes: note what change is needed

### Step 5: Make updates (one at a time, fully visible)
For each file that needs updating:
* Show the user what will change: "Updating [file]: [description of change]"
* Use the Edit tool to make the change
* The user sees every Edit call

### Step 6: Update phase index if scope changed
If any `[SCOPE_CHANGE]` entries exist:
* Update `specs/phases/index.json` for the active phase's topic list

### Step 7: Commit all changes
```bash
git add all modified doc files
git commit -m "docs(phase-N): sync docs from phase history"
```

### Step 8: Confirm completion
"Doc sync complete. Updated N files:
* [list of updated files]

### Safeguards
* NEVER update files not in the targeted list
* ALWAYS show the plan (Step 3) before making any edits
* History entries are NEVER modified — only read
* If unsure whether a doc needs updating, skip it and mention it to the user
```

### `.claude/commands/log.md`
```markdown
Record a manual entry in the active phase history file.

## Steps:
1. Read `specs/status.md` to identify the active phase (`Current Phase` field)
2. Find the history file: `specs/phases//history.md`
3. Determine entry type from the message:
   * Decision about technology/architecture → `[DECISION]`
   * Phase scope added/removed → `[SCOPE_CHANGE]`
   * Bug/tech debt/enhancement found → `[DISCOVERY]`
   * New planned feature → `[FEATURE]`
   * Architecture pattern changed → `[ARCH_CHANGE]`
   * Anything else → `[NOTE]`
4. Extract or infer topics (2-5 keywords covering what this touches)
5. Identify affects-phases (check `specs/phases/index.json` — which phases have these topics?)
6. Identify affects-docs (check `specs/decisions/impact-map.json` — which docs cover these topics?)
7. Append the formatted entry to `history.md` (APPEND ONLY — never edit existing entries):
   ```
   [TYPE] YYYY-MM-DD — Short title (max 10 words)
   Topics: topic-1, topic-2
   Affects-phases: phase-N-name (or "none")
   Affects-docs: path/to/doc.md#section (or "none")
   Detail: One to three sentences describing what changed and why.
   ```
8. If the entry introduces a topic not yet in `specs/decisions/impact-map.json`, add it
9. Confirm to user: "Logged [TYPE] entry to [phase] history."
```

### `.claude/commands/track.md`
```markdown
Track a backlog item — bug, feature, tech debt, or enhancement.

## Steps
1. Read the backlog to find the next available ID:
   * Read `specs/backlog/backlog.md`
2. Determine the item type from context or `$ARGUMENTS`:
   * Bug → `BUG-NNN` — add to Bugs table
   * Feature → `FEAT-NNN` — add to Features table
   * Tech Debt → `TD-NNN` — add to Tech Debt table
   * Enhancement → `ENH-NNN` — add to Enhancements table
3. Add a row to the appropriate table in `specs/backlog/backlog.md`:
   * `Priority`: Infer from urgency (default `P2`)
   * `Status`: `open`
   * `Phase`: Target phase or `unscheduled`
   * `Detail`: `—` unless complex
4. If the item is complex (needs acceptance criteria, investigation notes):
   * Create `specs/backlog/details/{ID}.md` with YAML frontmatter:
   ```yaml
   id: {ID}
   title: "{title}"
   priority: {P0-P3}
   status: open
   phase: {phase or unscheduled}
   created: {YYYY-MM-DD}
   ```
   * Update the `Detail` column to `[→](details/{ID}.md)`
5. If this is P0, also update the Critical Items table in `specs/status.md`.
6. Commit:
   ```bash
   git add specs/backlog/
   git commit -m "docs(backlog): add {ID} - {short title}"
   ```
```

### `.claude/commands/review.md`
```markdown
Review and groom the backlog between phases.

## Steps
1. Read current state and backlog:
   * Read `specs/status.md`
   * Read `specs/backlog/backlog.md`
2. For each category (Bugs, Features, Tech Debt, Enhancements), assess:
   * Are priorities still accurate given the current phase?
   * Should any items move to the active/next phase?
   * Are any items now `resolved` or `deprecated`?
   * Are there orphaned items (no phase assigned)?
3. Check for dependencies:
   * P0 bugs that should block phase progress
   * Features that depend on unresolved tech debt
4. Update `specs/backlog/backlog.md` with any priority/status/phase changes.
5. Update `specs/status.md` if P0/blocker items changed.
6. Commit:
   ```bash
   git add specs/
   git commit -m "docs(backlog): grooming for Phase N"
   ```
7. Report to user:
   * Total open items by type and priority
   * P0/P1 items requiring immediate attention
   * Recommended actions before next phase
```

---

## Step 5: Create the Claude Code Hook
### `.claude/settings.json`
This fires after every `Edit` or `Write` tool call, reminding the agent to log phase history when significant files change.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/check-history-reminder.sh"
          }
        ]
      }
    ]
  }
}
```

### `scripts/check-history-reminder.sh`
```bash
#!/usr/bin/env bash

# Read-only hook: reminds Claude to log history when significant files change.
# Receives PostToolUse context as JSON on stdin.
# Output goes to Claude — it sees the reminder and appends to phase history.

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input', {}).get('file_path', ''))" 2>/dev/null || echo "")

if [ -z "$FILE_PATH" ]; then exit 0; fi

# Patterns that warrant a history entry
SIGNIFICANT=false
case "$FILE_PATH" in
  specs/decisions/*.md) SIGNIFICANT=true ;;
  specs/phases/*/tasks.md) SIGNIFICANT=true ;;
  specs/backlog/backlog.md) SIGNIFICANT=true ;;
  specs/status.md) SIGNIFICANT=true ;;
esac

if [ "$SIGNIFICANT" = "true" ]; then
  echo "PHASE HISTORY REMINDER: '$FILE_PATH' was modified — if this reflects a decision, scope change, or discovery, append an entry to the active phase history file (specs/phases/phase-N-*/history.md)."
fi

exit 0
```
**Make it executable:**
```bash
chmod +x scripts/check-history-reminder.sh
```

---

## Step 6: Create the Phase History & Doc Sync Infrastructure
### `specs/phases/index.json`
Maps each phase to topic keywords. Used by `/sync-docs` to find affected phases.

```json
{
  "version": 1,
  "generated": "YYYY-MM-DD",
  "description": "Maps each phase to topic keywords. Used by /sync-docs to find affected phases.",
  "phases": {
    "phase-0-": {
      "status": "not-started",
      "topics": ["topic-1", "topic-2"]
    }
  }
}
```

### `specs/decisions/impact-map.json`
Maps topic keywords to specific docs/sections. Used by `/sync-docs` to find affected documents.

```json
{
  "version": 1,
  "description": "Maps topic keywords to specific non-phase docs/sections. Used by /sync-docs to find affected docs.",
  "topics": {
    "example-topic": {
      "files": [
        {"path": "docs/.md", "section": "Section Name"},
        {"path": "specs/status.md", "section": "Key Decisions Made"}
      ]
    }
  }
}
```

**How to populate**: As ADRs are created and topics emerge during phase work, add entries here. The `/log` command also checks this file and adds missing topics automatically. Over time, this map becomes comprehensive and makes `/sync-docs` highly accurate.

---

## Step 7: Create `specs/status.md`
```markdown
# Project Status
**Last Updated**: YYYY-MM-DD
**Current Phase**: Phase 0 — (`not-started`)
**Latest Release**: None
**Health**: On Track

## Summary
<One paragraph describing the project and where it stands.>

## Active Phase
| Phase | Name | Status | Progress |
|-------|------|--------|----------|
| 0 | <Phase 0 Name> | Not Started | 0% |

## Upcoming Phases
| Phase | Name | Status | Key Deliverables |
|-------|------|--------|-----------------|
| 1 | <Phase 1 Name> | Not Started | |

## Blockers
| ID | Description | Severity |
|----|-------------|----------|
| _(none)_ | | |

## Critical Items (P0)
| ID | Type | Description |
|----|------|-------------|
| _(none)_ | | |

## Next Actions
1.
2.

## Key Decisions Made
_(none yet)_

## Recent Changes
* **YYYY-MM-DD**: Project management structure initialized
```

---

## Step 8: Create `specs/backlog/backlog.md`
```markdown
# Backlog
**Last Updated**: YYYY-MM-DD
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
| _(none yet)_ | | | | | |

## Features
| ID | Title | Priority | Status | Phase | Detail |
|----|-------|----------|--------|-------|--------|
| _(none yet)_ | | | | | |

## Tech Debt
| ID | Title | Priority | Status | Phase | Detail |
|----|-------|----------|--------|-------|--------|
| _(none yet)_ | | | | | |

## Enhancements
| ID | Title | Priority | Status | Phase | Detail |
|----|-------|----------|--------|-------|--------|
| _(none yet)_ | | | | | |
```

---

## Step 9: Create `specs/decisions/0000-template.md`
```markdown
---
id: "0000"
title: "ADR Template"
status: template
date: null
---

# ADR-0000: [Title]

## Status
`proposed` | `accepted` | `rejected` | `superseded`

## Context
What is the issue being decided? What forces are at play?

## Decision
What is the decision and why?

## Alternatives Considered
| Option | Pros | Cons |
|--------|------|------|
| Option A | | |
| Option B | | |

## Consequences
## References
* Links to specs, docs, or discussions
```

---

## Step 10: Create `specs/decisions/README.md`
```markdown
# Architecture Decision Records
ADRs capture significant architectural decisions and their rationale.

| ID | Title | Status | Date |
|----|-------|--------|------|
| [0000](0000-template.md) | ADR Template | template | — |

## Creating a New ADR
1. Copy `0000-template.md` to `NNNN-short-title.md` (kebab-case, sequential number)
2. Fill in Context, Decision, Alternatives, Consequences
3. Add a row to the table above
4. Commit: `git commit -m "docs(adr): NNNN — "`
```

---

## Step 11: Create `specs/phases/README.md`
```markdown
# Phases Index
Quick reference for all phases. See [roadmap](../roadmap/roadmap.md) for timeline.

| Phase | Name | Status | Directory |
|-------|------|--------|-----------|
| 0 | <Phase 0 Name> | Not Started | [phase-0-/](phase-0-/) |

Each phase directory contains:
| File | Purpose |
|------|---------|
| `overview.md` | Goal, scope, deliverables, acceptance criteria, exit criteria |
| `plan.md` | Implementation approach, module structure, risks |
| `tasks.md` | Detailed checklist with verification steps |
| `history.md` | Append-only log of decisions, scope changes, discoveries (drives /sync-docs) |
| `retrospective.md` | Post-completion review (created by /complete-phase) |

## Dependencies
```
Phase 0 ()
└── Phase 1 ()
└── Phase 2 ()
```
```

---

## Step 12: Create the First Phase Directory
For every phase, create these files. When the phase starts, `/start-phase` also creates `history.md`.

### `specs/phases/phase-0-/overview.md`
```markdown
# Phase 0:
**Status**: Not Started
**Depends On**: Nothing — this is the foundation
**Estimated Effort**: X days

## Summary
<One paragraph goal.>

## Scope
### In Scope
* Item 1
* Item 2

### Out of Scope
* Item 1

## Key Deliverables
| # | Deliverable | Description |
|---|-------------|-------------|
| 1 | Name | Description |

## Acceptance Criteria
* [ ] Criterion 1
* [ ] Criterion 2

## Exit Criteria
All acceptance criteria met AND:
* No P0 bugs remain open
* Documentation updated
```

### `specs/phases/phase-0-/plan.md`
```markdown
# Phase 0: Implementation Plan

## Approach
<Describe the implementation approach.>

## Implementation Steps
* **Step 1:**
* **Step 2:**

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Risk 1 | Low/Med/High | Low/Med/High | Mitigation strategy |
```

### `specs/phases/phase-0-/tasks.md`
```markdown
# Phase 0 Tasks
**Status**: Not Started | **Progress**: 0/N tasks

* [ ] **Task title**
    * Detail or sub-step
    * Verification: how to confirm this is done
* [ ] **Task title**
    * Detail or sub-step
    * Verification: how to confirm this is done
```

### `specs/phases/phase-0-/history.md` (created by `/start-phase`)
```markdown
# Phase 0 — : Implementation History
Append-only log. Do NOT edit existing entries. Add new entries at the bottom.
Claude appends automatically when significant changes occur.
Use `/log ` to add a manual entry at any time.

## Entry Types
| Type | When to use |
|------|------------|
| [DECISION] | ADR created or updated, technology choice made |
| [SCOPE_CHANGE] | Phase deliverables added, removed, or reprioritized |
| [DISCOVERY] | Bug, tech debt, or enhancement found |
| [FEATURE] | New planned feature added to this phase |
| [ARCH_CHANGE] | Architectural pattern or integration changed |
| [NOTE] | Anything else worth recording |

## Entry Format
```
[TYPE] YYYY-MM-DD — Short title (max 10 words)
Topics: topic-1, topic-2
Affects-phases: phase-N-name (or "none")
Affects-docs: path/to/doc.md#section (or "none")
Detail: What changed and why.
```

## Entries
```

---

## Step 13: Create Remaining Specs Files
### `specs/roadmap/roadmap.md`
```markdown
# Roadmap
**Start Date**: YYYY-MM-DD
**Target Completion**: YYYY-MM-DD

## Timeline
| Phase | Name | Status | Start | End | Effort |
|-------|------|--------|-------|-----|--------|
| 0 | | Not Started | YYYY-MM-DD | YYYY-MM-DD | X days |

## Phase Dependencies
```
Phase 0 → Phase 1 → Phase 2 → ...
```

## Milestones
| Milestone | Phase | Target Date |
|-----------|-------|-------------|
| | 0 | YYYY-MM-DD |
```

### `specs/changelog/YYYY-MM.md`
```markdown
# Changelog — YYYY-MM

## YYYY-MM-DD
* Project management structure initialized
* All spec files, slash commands, and agent rules created
```

### `specs/vision/project-charter.md`
```markdown
# Project Charter
## Problem Statement
<What problem does this project solve?>

## Goals
1. Goal 1
2. Goal 2

## Non-Goals
* Not this
* Not that

## Stakeholders
| Role | Name/Team |
|------|-----------|
| Owner | |
```

### `specs/vision/principles.md`
```markdown
# Engineering Principles
1. **Principle name** — Explanation
2. **Principle name** — Explanation
```

### `specs/vision/success-criteria.md`
```markdown
# Success Criteria
## Phase 0 Complete When...
* [ ] Criterion
```

### `specs/README.md`
```markdown
# Specs
Project management for . The single source of truth for all work.

## Structure
| Directory | Purpose |
|-----------|---------|
| `status.md` | Current phase, blockers, P0 items — **read this first** |
| `backlog/` | All bugs, features, tech debt, enhancements |
| `changelog/` | Monthly changelogs |
| `decisions/` | Architecture Decision Records (ADRs) + impact-map.json |
| `phases/` | Per-phase plans, task checklists, history logs + index.json |
| `roadmap/` | Timeline and milestones |
| `vision/` | Charter, principles, success criteria |
```

---

## Step 14: Initial Git Commit
```bash
git add .
git commit -m "feat: initialize spec-driven project structure

- CLAUDE.md with agent rules (Rules 1-9) and autonomous behaviors
- .agent/rules/project.md with detailed operational rules
- .claude/commands/ with start-phase, complete-phase, sync-docs, log, track, review
- .claude/settings.json with PostToolUse history reminder hook
- specs/ with status, backlog, decisions (+ impact-map), phases (+ index), roadmap, vision, changelog
- Phase history system: append-only history.md + index.json + impact-map.json → /sync-docs

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## What Comes Next (After Bootstrap)
Once the scaffold is in place, the workflow is:
1. **Write your vision document** — put it in `docs/.md`. This is the master plan the agent reads to understand the full scope of what needs to be built.
2. **Run a gap analysis** — give the agent your vision doc and the empty phases. Ask it to compare and populate all phases with tasks derived from the vision.
3. **Start Phase 0** — use `/start-phase` to kick off the first phase. The agent creates the branch, populates the tasks and history file, builds the topic index, and begins implementation.
4. **Iterate** — during each phase:
    * Agent auto-appends to `history.md` as decisions, scope changes, and discoveries occur
    * Use `/log ` to manually record anything the agent missed
    * Use `/track` to add backlog items as you discover them
    * The hook in `scripts/check-history-reminder.sh` catches forgotten history entries
5. **Complete a phase** — `/sync-docs` to propagate history to docs, then `/complete-phase` to verify acceptance criteria, write retrospective, tag release, and merge to main.
6. **Groom between phases** — `/review` to re-prioritize backlog items before starting the next phase.

---

## The Development Cycle
```
┌─────────────────────────────────────────────────────────┐
│ THE FULL CYCLE                                            │
│                                                           │
│ 1. DISCOVER "What should I work on?"                        │
│    ↓ Agent reads status.md + backlog.md                   │
│                                                           │
│ 2. PLAN "How should I build this?"                          │
│    ↓ Agent reads/creates phase plan.md                   │
│                                                           │
│ 3. IMPLEMENT "Build the thing"                             │
│    ↓ Agent writes code, auto-updates tasks               │
│      + appends to phase history.md                        │
│                                                           │
│ 4. VERIFY "Does it work?"                                  │
│    ↓ Tests, validation, checks                            │
│                                                           │
│ 5. SYNC "Propagate decisions to docs"                     │
│    ↓ /sync-docs (runs at phase completion)                │
│                                                           │
│ 6. RELEASE "Ship it" (/complete-phase)                     │
│    Tag, retrospective, update roadmap                     │
└─────────────────────────────────────────────────────────┘
```

---

## Migrating an Existing Project
If you already have a repository with code but no spec-driven structure:
1. **Run the bootstrap** — Create all directories and files from Steps 1-13 above.
2. **Backfill status.md** — Set the current phase to wherever the project actually is. If you've already shipped features, you may be at Phase 2 or 3. Create completed phase directories with minimal `retrospective.md` files.
3. **Backfill the backlog** — Any known bugs, features, or tech debt go into `specs/backlog/backlog.md` immediately. Use `/track` for each one.
4. **Backfill ADRs** — For every significant technical choice already made, create a backdated ADR. These don't need to be perfect — just capture the decision and rationale.
5. **Populate the impact map** — As you write ADRs and identify topics, add them to `specs/decisions/impact-map.json` pointing to the relevant docs.
6. **Populate the phase index** — For each phase (past and future), add a topics entry to `specs/phases/index.json`.
7. **Start the next phase** — Use `/start-phase` to begin the next phase of work. From this point forward, the full system is active.

**Tip**: You don't need perfect backfill. The system self-improves — as you work through phases, the impact map and topic index grow organically. Within 1-2 phases, the system will be comprehensive.

---

## File & Folder Naming Convention
| Location | Convention | Examples |
|----------|-----------|---------|
| `specs/` — folders | `kebab-case` | `phase-0-bootstrap/`, `phase-1-networking/` |
| `specs/` — files | `kebab-case` | `0001-state-backend-postgres.md` |
| `docs/` — files | `kebab-case` | `developer-guide.md`, `naming-conventions.md` |
| `.claude/commands/` — files | `kebab-case` | `start-phase.md`, `sync-docs.md` |
| `.agent/` — files | `snake_case` | `project.md` |
| Root config files | `UPPERCASE` or tool default | `README.md`, `CLAUDE.md` |
| ADR files | `NNNN-kebab-title.md` | `0001-state-backend-postgres.md` |
| Phase directories | `phase-N-shortname` | `phase-0-bootstrap` |
| Date/changelog files | `YYYY-MM.md` | `2026-03.md` |
| Scripts | `kebab-case` or `snake_case` | `check-history-reminder.sh` |
