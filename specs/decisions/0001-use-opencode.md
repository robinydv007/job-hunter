---
id: "0001"
title: "Use OpenCode as Primary AI Agent"
status: accepted
date: "2026-04-02"
---

# ADR-0001: Use OpenCode as Primary AI Agent

## Status
`accepted`

## Context
The project bootstrap guide (`project-bootstrap-guide.md`) was originally written for Claude Code, with `.claude/commands/` for slash commands and `.claude/settings.json` for PostToolUse hooks. The team uses OpenCode as the primary AI coding agent. OpenCode has a different configuration model:
- Commands use `.opencode/commands/*.md` with YAML frontmatter
- Hooks use JavaScript/TypeScript plugins with event listeners (`.opencode/plugins/`)
- Project config via `opencode.json`
- Reads `CLAUDE.md` as a fallback for rules (Claude Code compatibility)

## Decision
Migrate all Claude Code-specific configuration to OpenCode format and use OpenCode as the primary AI agent for this project.

Specifically:
1. Move all commands from `.claude/commands/` to `.opencode/commands/` with YAML frontmatter
2. Replace `.claude/settings.json` PostToolUse hook with a JavaScript plugin at `.opencode/plugins/history-reminder.js`
3. Create `opencode.json` project config with command definitions and instruction references
4. Delete the `.claude/` directory entirely
5. Keep `CLAUDE.md` for rules (OpenCode reads it as fallback, and it works for team members using Claude Code)

## Alternatives Considered
| Option | Pros | Cons |
|--------|------|------|
| Keep Claude Code format | Original guide works as-is | Won't work with OpenCode; commands and hooks silently ignored |
| Maintain both formats | Works for both agents | Duplication, maintenance burden, confusion |
| Migrate to OpenCode only | Single source of truth, native support | Requires migration effort; guide needs updates |
| Use AGENTS.md instead of CLAUDE.md | OpenCode's preferred format | Loses Claude Code compatibility for team members |

## Consequences
- **Positive**: All slash commands and hooks work natively with OpenCode; no silent failures
- **Positive**: Plugin architecture is more flexible than JSON hooks (can use Bun shell API, npm packages)
- **Positive**: `opencode.json` provides centralized project config with schema validation
- **Positive**: CLAUDE.md retained for Claude Code compatibility
- **Negative**: Original bootstrap guide references need updating for future use
- **Negative**: Team members using Claude Code will need to create their own `.claude/commands/` if they want slash commands

## References
- [OpenCode Commands Documentation](https://opencode.ai/docs/commands/)
- [OpenCode Plugins Documentation](https://opencode.ai/docs/plugins/)
- [OpenCode Rules Documentation](https://opencode.ai/docs/rules/)
- [OpenCode Config Documentation](https://opencode.ai/docs/config/)
- Phase 0 history entry: `specs/phases/phase-0-bootstrap/history.md`
