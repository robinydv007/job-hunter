# Phase 0: Implementation Plan

## Approach
Create all files from the project-bootstrap-guide.md, adapting Claude-specific references to work with opencode. Most of the structure is tool-agnostic and works with any AI coding agent.

## Implementation Steps
* **Step 1:** Create directory structure
* **Step 2:** Write CLAUDE.md (agent config)
* **Step 3:** Write .agent/rules/project.md
* **Step 4:** Create slash commands
* **Step 5:** Create hook script and settings
* **Step 6:** Create phase history & doc sync infrastructure (index.json, impact-map.json)
* **Step 7:** Create specs/status.md
* **Step 8:** Create specs/backlog/backlog.md
* **Step 9:** Create ADR template and README
* **Step 10:** Create phase directory templates
* **Step 11:** Create remaining specs files (roadmap, changelog, vision)
* **Step 12:** Create developer-guideline.md
* **Step 13:** Initial git commit

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Opencode hook system differs from Claude Code | Medium | Medium | Use bash script hook that works with any tool that supports PostToolUse |
| File naming conflicts with existing files | Low | Low | Check for existing files before writing |
