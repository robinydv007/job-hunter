# Phase 0 Bootstrap Tasks
**Status**: Complete | **Progress**: 14/14 tasks

* [x] **Create directory structure**
    * Run mkdir for all required directories
    * Verification: ls shows all directories exist
* [x] **Write CLAUDE.md**
    * Contains Rules 1-9 adapted for opencode
    * Verification: file exists with all 9 rules
* [x] **Write .agent/rules/project.md**
    * Detailed agent operational rules
    * Verification: file exists with naming conventions and priorities
* [x] **Create slash commands**
    * start-phase.md, complete-phase.md, sync-docs.md, log.md, track.md, review.md
    * Verification: all 6 files exist in .opencode/commands/ with proper frontmatter
* [x] **Create opencode plugin**
    * .opencode/plugins/history-reminder.js with file.edited and session.idle hooks
    * Verification: plugin file exists and exports valid hooks
* [x] **Create opencode.json**
    * Project config with commands, instructions, and plugin references
    * Verification: valid JSON with $schema, command, and instructions keys
* [x] **Create phase history infrastructure**
    * specs/phases/index.json and specs/decisions/impact-map.json
    * Verification: both JSON files are valid
* [x] **Create status and backlog**
    * specs/status.md and specs/backlog/backlog.md
    * Verification: files exist with proper templates
* [x] **Create ADR system**
    * specs/decisions/0000-template.md and README.md
    * Verification: template and index exist
* [x] **Create phase directory**
    * specs/phases/phase-0-bootstrap/ with overview.md and plan.md
    * Verification: directory and files exist
* [x] **Create remaining specs**
    * roadmap.md, changelog, vision files, specs/README.md
    * Verification: all files exist
* [x] **Create developer-guideline.md**
    * Comprehensive guide for developers using this system
    * Verification: file exists in docs/ with .opencode/ references
* [x] **Initial git commit and push**
    * git add . && git commit with proper message, push to remote
    * Verification: git log shows commit, remote has code
* [x] **Migrate from Claude Code to OpenCode format**
    * Move .claude/commands/ → .opencode/commands/ with frontmatter format
    * Replace .claude/settings.json hook → .opencode/plugins/history-reminder.js
    * Create opencode.json project config
    * Delete .claude/ directory
    * Update all doc references from .claude/ to .opencode/
    * Verification: no .claude/ directory exists, all docs reference .opencode/
