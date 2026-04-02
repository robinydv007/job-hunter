/**
 * History Reminder Plugin
 * 
 * Tracks edits to significant spec files and reminds the agent
 * to log phase history when a session ends without updating history.
 * 
 * This replaces the Claude Code PostToolUse hook pattern.
 */

const SIGNIFICANT_PATTERNS = [
  'specs/decisions/',
  'specs/phases/',
  'specs/backlog/backlog.md',
  'specs/status.md',
];

export const HistoryReminderPlugin = async ({ client, directory }) => {
  const significantEdits = new Set();

  return {
    'file.edited': async ({ event }) => {
      const filePath = event?.path || event?.filePath || '';
      
      if (!filePath) return;
      
      const isSignificant = SIGNIFICANT_PATTERNS.some(pattern => 
        filePath.includes(pattern)
      );

      if (isSignificant) {
        significantEdits.add(filePath);
      }
    },

    'session.idle': async () => {
      if (significantEdits.size === 0) return;

      const files = Array.from(significantEdits).join(', ');
      
      await client.app.log({
        body: {
          service: 'history-reminder',
          level: 'warn',
          message: `Significant spec files were edited this session: ${files}. If any decisions, scope changes, or discoveries were made, remember to append entries to the active phase history file (specs/phases/phase-N-*/history.md).`,
        },
      });

      significantEdits.clear();
    },
  };
};
