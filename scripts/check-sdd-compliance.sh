#!/usr/bin/env bash

# SDD Compliance Checker
# Returns exit code 0 (pass) or 1 (fail) with specific error messages.
# Used by both the pre-commit hook and the opencode plugin.
#
# Usage:
#   ./scripts/check-sdd-compliance.sh          # Check staged changes (pre-commit)
#   ./scripts/check-sdd-compliance.sh --cached # Check staged changes explicitly
#   ./scripts/check-sdd-compliance.sh --diff   # Check working tree changes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

ERRORS=()
WARNINGS=()

# Determine which diff to check
DIFF_FLAG="--cached"
if [[ "${1:-}" == "--diff" ]]; then
  DIFF_FLAG=""
fi

# ─── Check 1: No secrets in staged changes ───────────────────────────────────
check_secrets() {
  local secret_patterns=(
    'AKIA[0-9A-Z]{16}'                          # AWS access key
    '(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36}'  # GitHub token
    'sk-[A-Za-z0-9]{20,}'                        # OpenAI/Anthropic API key
    'xox[baprs]-[A-Za-z0-9-]+'                   # Slack token
    'password\s*[:=]\s*["\x27][^\s]{4,}'         # Hardcoded password
    'api_key\s*[:=]\s*["\x27][A-Za-z0-9]{16,}'   # Hardcoded API key
    'BEGIN (RSA |EC |DSA )?PRIVATE KEY'          # Private key
  )

  local staged_files
  staged_files=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)

  if [ -z "$staged_files" ]; then
    return 0
  fi

  for pattern in "${secret_patterns[@]}"; do
    local matches
    matches=$(echo "$staged_files" | xargs grep -lE "$pattern" 2>/dev/null || true)
    if [ -n "$matches" ]; then
      ERRORS+=("SECRET DETECTED in: $matches (pattern: $pattern)")
    fi
  done
}

# ─── Check 2: Code changes require changelog entry ───────────────────────────
check_changelog() {
  local code_files
  code_files=$(git diff $DIFF_FLAG --name-only --diff-filter=ACM 2>/dev/null | {
    grep -v '^specs/' || true
  } | {
    grep -v '^docs/' || true
  } | {
    grep -v '^\.agent/' || true
  } | {
    grep -v '^\.opencode/' || true
  } | {
    grep -v '^scripts/' || true
  } | {
    grep -v '^opencode\.json' || true
  } | {
    grep -v '^CLAUDE\.md' || true
  } | {
    grep -v '^README\.md' || true
  } || true)

  if [ -z "$code_files" ]; then
    return 0
  fi

  # Check if changelog has today's entry
  local today
  today=$(date +%Y-%m-%d)
  local changelog_file="specs/changelog/${today:0:7}.md"

  if [ ! -f "$changelog_file" ]; then
    ERRORS+=("CHANGELOG MISSING: No changelog file for $today. Create $changelog_file with an entry for today's changes.")
    return 0
  fi

  if ! grep -q "$today" "$changelog_file"; then
    ERRORS+=("CHANGELOG MISSING: No entry for $today in $changelog_file. Add a line describing today's code changes.")
  fi
}

# ─── Check 3: Spec changes require history.md entry ──────────────────────────
check_history() {
  # Check if any phase tasks.md was modified
  local task_files
  task_files=$(git diff $DIFF_FLAG --name-only --diff-filter=ACM 2>/dev/null | {
    grep -E 'specs/phases/phase-[^/]+/tasks\.md' || true
  } || true)

  if [ -z "$task_files" ]; then
    return 0
  fi

  # For each modified tasks.md, check if the corresponding history.md was also modified
  for task_file in $task_files; do
    local phase_dir
    phase_dir=$(dirname "$task_file")
    local history_file="$phase_dir/history.md"

    if [ ! -f "$history_file" ]; then
      ERRORS+=("HISTORY MISSING: $task_file was modified but $history_file does not exist. Create it and log this change.")
      continue
    fi

    local history_modified
    history_modified=$(git diff $DIFF_FLAG --name-only --diff-filter=ACM 2>/dev/null | {
      grep -F "$history_file" || true
    } || true)

    if [ -z "$history_modified" ]; then
      local phase_name
      phase_name=$(basename "$phase_dir")
      ERRORS+=("HISTORY NOT UPDATED: $task_file was modified but $history_file was not updated in this commit. Append a history entry.")
    fi
  done
}

# ─── Check 4: Status.md must reflect active phase progress ───────────────────
check_status_sync() {
  # If tasks.md is marked complete, status.md should reflect that
  local complete_tasks
  complete_tasks=$(git diff $DIFF_FLAG --name-only --diff-filter=ACM 2>/dev/null | {
    grep -E 'specs/phases/phase-[^/]+/tasks\.md' || true
  } || true)

  if [ -z "$complete_tasks" ]; then
    return 0
  fi

  for task_file in $complete_tasks; do
    # Check if the task file contains "Complete" status
    if git show ":$task_file" 2>/dev/null | grep -q '\*\*Status\*\*: Complete'; then
      # Verify status.md was also updated
      local status_modified
      status_modified=$(git diff $DIFF_FLAG --name-only --diff-filter=ACM 2>/dev/null | {
        grep -F 'specs/status.md' || true
      } || true)

      if [ -z "$status_modified" ]; then
        ERRORS+=("STATUS NOT SYNCED: $task_file marked as Complete but specs/status.md was not updated in this commit.")
      fi
    fi
  done
}

# ─── Check 5: Overview.md acceptance criteria must be checked when phase is complete ──────────────────────────
check_overview_criteria() {
  # Check if any overview.md was modified
  local overview_files
  overview_files=$(git diff $DIFF_FLAG --name-only --diff-filter=ACM 2>/dev/null | {
    grep -E 'specs/phases/phase-[^/]+/overview\.md' || true
  } || true)

  if [ -z "$overview_files" ]; then
    return 0
  fi

  for overview_file in $overview_files; do
    # If overview status is "Complete", check that acceptance criteria are checked
    if git show ":$overview_file" 2>/dev/null | grep -q '\*\*Status\*\*: Complete'; then
      # Check for any unchecked acceptance criteria
      local unchecked
      unchecked=$(git show ":$overview_file" 2>/dev/null | {
        grep '\* \[ \]' || true
      } || true)

      if [ -n "$unchecked" ]; then
        local phase_name
        phase_name=$(basename "$(dirname "$overview_file")")
        ERRORS+=("OVERVIEW INCOMPLETE: $overview_file is marked Complete but has unchecked acceptance criteria. Mark all criteria as [x].")
      fi
    fi
  done
}

# ─── Check 6: Last Updated dates must be current ─────────────────────────────
check_dates() {
  local today
  today=$(date +%Y-%m-%d)

  # Check status.md Last Updated date
  if [ -f "specs/status.md" ]; then
    local status_date
    status_date=$(grep '\*\*Last Updated\*\*:' specs/status.md | head -1 | sed 's/.*: //' || echo "")
    if [ -n "$status_date" ] && [ "$status_date" != "$today" ]; then
      # Only error if there are staged code changes (not just spec changes)
      local code_files
      code_files=$(git diff $DIFF_FLAG --name-only --diff-filter=ACM 2>/dev/null | {
        grep -v '^specs/' || true
      } | {
        grep -v '^docs/' || true
      } || true)

      if [ -n "$code_files" ]; then
        WARNINGS+=("STALE DATE: specs/status.md Last Updated is $status_date but today is $today. Consider updating.")
      fi
    fi
  fi
}

# ─── Run all checks ──────────────────────────────────────────────────────────
check_secrets
check_changelog
check_history
check_status_sync
check_overview_criteria
check_dates

# ─── Report results ──────────────────────────────────────────────────────────
if [ ${#ERRORS[@]} -gt 0 ]; then
  echo ""
  echo "╔══════════════════════════════════════════════════════════╗"
  echo "║  SDD COMPLIANCE CHECK FAILED                            ║"
  echo "╚══════════════════════════════════════════════════════════╝"
  echo ""
  echo "Commit blocked. Fix the following issues:"
  echo ""
  for i in "${!ERRORS[@]}"; do
    echo "  ✗ ${ERRORS[$i]}"
  done
  echo ""
  echo "Run 'bash scripts/check-sdd-compliance.sh' to re-check after fixing."
  echo ""
  exit 1
fi

if [ ${#WARNINGS[@]} -gt 0 ]; then
  echo ""
  echo "⚠ SDD Warnings:"
  for i in "${!WARNINGS[@]}"; do
    echo "  ⚠ ${WARNINGS[$i]}"
  done
  echo ""
fi

exit 0
