# Phase 0 — Bootstrap Retrospective

## What Went Well
- Full spec-driven development structure bootstrapped in one session
- OpenCode migration completed cleanly — all commands converted to frontmatter format, hooks replaced with JavaScript plugin
- Directory structure and file organization matches the bootstrap guide exactly
- Agent rules (CLAUDE.md + .agent/rules/project.md) are comprehensive and tool-agnostic
- Git workflow set up with proper commit messages and pushed to remote

## What Didn't Go Well
- **SDD discipline not followed during implementation**: Rule 2 (auto-update tracking) and Rule 8 (record phase history) were not followed during the initial work. This meant:
  - `specs/status.md` showed "Not Started" while all tasks were actually complete
  - `specs/changelog/2026-04.md` was missing entries for the migration work
  - No `history.md` existed to record decisions and discoveries
  - `overview.md` had stale references to `.claude/commands/`
- This required a separate compliance pass to fix, which could have been avoided

## Root Cause
The bootstrap was treated as "setup" rather than "implementation work." The SDD rules apply to all work, including bootstrapping the system itself. The agent should have been following Rule 2 and Rule 8 from the first commit.

## Lessons Learned
1. **SDD rules apply from commit #1** — Even bootstrapping the system counts as work that needs tracking
2. **History.md should be created at phase start** — Not at completion. The `/start-phase` command creates it, but we didn't use `/start-phase` for Phase 0
3. **Status.md should be updated after each commit** — Not just at phase completion
4. **Doc references need review** — When migrating formats, check all docs for stale references

## Actions for Phase 1
- [ ] Ensure `/start-phase` is used to kick off Phase 1 (creates history.md automatically)
- [ ] Verify status.md is updated after each meaningful change
- [ ] Check changelog entries match git commits
- [ ] Review all doc references before marking tasks complete

## Metrics
| Metric | Value |
|--------|-------|
| Planned tasks | 14 |
| Completed tasks | 14 |
| Completion rate | 100% |
| SDD compliance violations found | 6 |
| Commits made | 3 |
| ADRs created | 1 (ADR-0001) |
