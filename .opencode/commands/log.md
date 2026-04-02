---
description: Record a manual entry in the active phase history file
---
Record a manual entry in the active phase history file. Use $ARGUMENTS for the entry detail.

## Steps:
1. Read `specs/status.md` to identify the active phase (`Current Phase` field)
2. Find the history file: `specs/phases/phase-N-*/history.md`
3. Determine entry type from $ARGUMENTS:
   - Decision about technology/architecture → `[DECISION]`
   - Phase scope added/removed → `[SCOPE_CHANGE]`
   - Bug/tech debt/enhancement found → `[DISCOVERY]`
   - New planned feature → `[FEATURE]`
   - Architecture pattern changed → `[ARCH_CHANGE]`
   - Anything else → `[NOTE]`
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
