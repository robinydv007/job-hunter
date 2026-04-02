/**
 * SDD Enforcement Plugin
 * 
 * Hard-blocks git commit if SDD compliance checks fail.
 * Also tracks spec file edits and reminds at session idle.
 * 
 * Enforcement checks (via scripts/check-sdd-compliance.sh):
 * 1. No secrets in staged changes
 * 2. Code changes require changelog entry for today
 * 3. Phase task changes require history.md entry
 * 4. Status.md must reflect active phase progress
 */

const { $ } = await import('bun');

const SIGNIFICANT_PATTERNS = [
  'specs/decisions/',
  'specs/phases/',
  'specs/backlog/backlog.md',
  'specs/status.md',
];

export const SddEnforcementPlugin = async ({ client, directory }) => {
  const significantEdits = new Set();

  /**
   * Run the SDD compliance checker.
   * Returns { pass: true } or { pass: false, errors: string[] }
   */
  async function runComplianceCheck() {
    try {
      const result = await $`bash scripts/check-sdd-compliance.sh --diff`.quiet();
      return { pass: true };
    } catch (error) {
      // The script outputs errors to stdout/stderr on failure
      const output = error.stdout?.toString() || error.stderr?.toString() || '';
      const errors = output
        .split('\n')
        .filter(line => line.includes('✗'))
        .map(line => line.replace('✗', '').trim());
      return { pass: false, errors };
    }
  }

  return {
    /**
     * Intercept bash commands — block git commit if compliance fails
     */
    'tool.execute.before': async (input, output) => {
      if (input.tool !== 'bash') return;

      const command = output.args?.command || '';

      // Only intercept git commit (not git add, git push, etc.)
      if (!command.includes('git commit')) return;

      // Allow --no-verify bypass for emergencies (logged as warning)
      if (command.includes('--no-verify')) {
        await client.app.log({
          body: {
            service: 'sdd-enforcement',
            level: 'warn',
            message: 'Commit used --no-verify to bypass SDD checks. This should only be used in emergencies.',
          },
        });
        return;
      }

      // Run compliance check
      const result = await runComplianceCheck();

      if (!result.pass) {
        const errorDetail = result.errors.join('\n');
        throw new Error(
          `SDD COMPLIANCE CHECK FAILED — commit blocked.\n\n${errorDetail}\n\n` +
          `Fix the issues above, stage the fixes, then try git commit again.`
        );
      }
    },

    /**
     * Track edits to significant spec files
     */
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

    /**
     * Remind about unlogged history at session end
     */
    'session.idle': async () => {
      if (significantEdits.size === 0) return;

      const files = Array.from(significantEdits).join(', ');
      
      await client.app.log({
        body: {
          service: 'sdd-enforcement',
          level: 'warn',
          message: `Significant spec files were edited this session: ${files}. If any decisions, scope changes, or discoveries were made, remember to append entries to the active phase history file (specs/phases/phase-N-*/history.md).`,
        },
      });

      significantEdits.clear();
    },
  };
};
