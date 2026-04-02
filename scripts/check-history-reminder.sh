#!/usr/bin/env bash

# Read-only hook: reminds the agent to log history when significant files change.
# Receives PostToolUse context as JSON on stdin.
# Output goes to agent — it sees the reminder and appends to phase history.

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
