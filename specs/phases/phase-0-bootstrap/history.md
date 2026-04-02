# Phase 0 — Bootstrap: Implementation History
Append-only log. Do NOT edit existing entries. Add new entries at the bottom.
Agent appends automatically when significant changes occur.
Use `/log` to add a manual entry at any time.

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

[DECISION] 2026-04-02 — Migrate from Claude Code to OpenCode format
Topics: opencode-config, agent-tooling
Affects-phases: phase-0-bootstrap
Affects-docs: CLAUDE.md, opencode.json, docs/developer-guideline.md
Discovered that .claude/commands/ and .claude/settings.json hooks are Claude Code-specific and don't work with OpenCode. Migrated all commands to .opencode/commands/ with YAML frontmatter format, replaced PostToolUse hook with a JavaScript plugin using file.edited and session.idle events. Created ADR-0001 for full rationale.

[ARCH_CHANGE] 2026-04-02 — Plugin-based hooks replace JSON hook config
Topics: opencode-config, plugin-system
Affects-phases: phase-0-bootstrap
Affects-docs: .opencode/plugins/history-reminder.js
OpenCode uses JavaScript/TypeScript plugins with event hooks instead of Claude Code's .claude/settings.json PostToolUse matcher. Created .opencode/plugins/history-reminder.js that tracks edits to significant spec files and reminds the agent at session idle.

[DISCOVERY] 2026-04-02 — .claude/ directory not needed since OpenCode reads CLAUDE.md
Topics: claude-compatibility, agent-config
Affects-phases: phase-0-bootstrap
Affects-docs: CLAUDE.md
OpenCode supports CLAUDE.md as a fallback for rules (Claude Code compatibility). The .claude/ directory (commands, settings) is not read by OpenCode, so it can be safely deleted after migration.

[DISCOVERY] 2026-04-02 — SDD tracking discipline not followed during bootstrap
Topics: spec-system, process-discipline
Affects-phases: phase-0-bootstrap
Affects-docs: specs/status.md, specs/changelog/2026-04.md
During the initial bootstrap and migration work, Rule 2 (auto-update tracking) and Rule 8 (record phase history) were not followed. status.md showed "Not Started" while tasks were complete, changelog was missing entries, and no history.md existed. This was corrected as part of SDD compliance sync.

[NOTE] 2026-04-02 — Phase 0 complete, all 15 tasks done
Topics: project-setup, phase-completion
Affects-phases: phase-0-bootstrap
Affects-docs: specs/status.md, specs/phases/README.md
All Phase 0 tasks completed: directory structure, agent config, slash commands, plugin, specs, developer guideline, initial git commit and push, OpenCode migration, and SDD enforcement system.

[ARCH_CHANGE] 2026-04-02 — SDD enforcement: hard blocks on non-compliant commits
Topics: spec-system, enforcement, plugin-system
Affects-phases: phase-0-bootstrap
Affects-docs: CLAUDE.md#rule-10, .agent/rules/project.md, .opencode/plugins/history-reminder.js
Added scripts/check-sdd-compliance.sh (4 checks: secrets, changelog, history, status sync), scripts/pre-commit git hook, and upgraded .opencode/plugins/history-reminder.js to intercept git commit and block if compliance fails. Both enforcement layers must pass for a commit to succeed.

[DISCOVERY] 2026-04-02 — 7 bugs found during SDD architecture audit
Topics: spec-system, process-discipline, opencode-config
Affects-phases: phase-0-bootstrap
Affects-docs: specs/roadmap/roadmap.md, specs/phases/phase-0-bootstrap/retrospective.md, specs/vision/success-criteria.md, specs/phases/phase-0-bootstrap/plan.md, CLAUDE.md, docs/developer-guideline.md, opencode.json
Full audit revealed 7 inconsistencies: stale roadmap status, retrospective metrics mismatch, unchecked success criteria, outdated plan risk table, [NOTE] entry type inconsistency, wrong vision doc path reference, and duplicate command definitions in opencode.json. All added to backlog as BUG-001 through BUG-007.
