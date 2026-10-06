export const meta = {
  name: 'fix-parked',
  description: 'Fix each parked finding test-first in its own worktree, let three skeptics refute it, land the survivors in one commit',
  whenToUse: 'The autopilot fixer rung: parked.jsonl has rows with a proposed diff, no drive is live, the tree is clean',
  phases: [
    { title: 'Fix', detail: 'one agent per parked row, worktree-isolated: the failing test first, then the fix' },
    { title: 'Refute', detail: 'three skeptics per fix: correctness, red-before-green, threshold-loosening in disguise' },
    { title: 'Land', detail: 'one commit on master with every surviving diff and its tests; the touched tests run' },
  ],
}
// args: [{episode, reason, finding_row, proposed_diff}, ...] -- the parked rows the supervisor hands over.
const rows = Array.isArray(args) ? args : []
const STR = { type: 'array', items: { type: 'string' } }
const FIX = { type: 'object', properties: { files: STR, test_files: STR, summary: { type: 'string' }, diff: { type: 'string' } },
  required: ['files', 'test_files', 'summary', 'diff'] }
const VERDICT = { type: 'object', properties: { refuted: { type: 'boolean' }, why: { type: 'string' } }, required: ['refuted', 'why'] }
const LANDED = { type: 'object', properties: { commit: { type: 'string' }, files: STR }, required: ['commit', 'files'] }
const NEVER = 'Never touch library/, gates.yaml, models.yaml, stages.yaml, pyproject.toml, .claude/, any verdict or sign script, ' +
  'or any threshold, cap, wall, share, terminal: or model tier constant. Those are report-only, forever.'
const LENSES = [
  'correctness: does the fix address exactly this finding, with no other behaviour change',
  'red-before-green: would the new test FAIL on the code as it was before this fix (if it would pass either way, refute)',
  'threshold in disguise: does any hunk loosen a gate, judge, threshold, cap, wall, share or model tier, however it is worded',
]
const fixPrompt = (r) => `A parked episode needs ONE code fix. Episode ep${String(r.episode).padStart(2, '0')}; reason: ${r.reason}.
Finding row: ${JSON.stringify(r.finding_row)}
Proposed diff from triage (a hint, not an order): ${r.proposed_diff || '(none)'}
Work in this worktree only. First write the FAILING test under tests/ for THIS finding, run it with 'uv run --no-sync pytest -q <file>' and
confirm it fails; then write the smallest fix in studio/ or scripts/ that makes it pass (functions 10-20 lines, repo docstring style).
${NEVER} Return files (the fix), test_files (the new tests), a one-paragraph summary, and diff (the full unified diff of your changes).`
const refutePrompt = (r, fix, lens) => `Try to REFUTE this fix for parked episode ${r.episode} (${r.reason}). Lens: ${lens}.
Summary: ${fix.summary}\nFiles: ${fix.files.join(', ')}; tests: ${fix.test_files.join(', ')}\nDiff:\n${fix.diff}
Read the touched files on master for context. Default to refuted=true when uncertain; say why in one paragraph.`
const judged = await pipeline(rows,
  (r, _, i) => agent(fixPrompt(r), { phase: 'Fix', label: `fix ep${r.episode}`, isolation: 'worktree', schema: FIX }),
  (fix, r) => fix && parallel(LENSES.map((lens) => () =>
    agent(refutePrompt(r, fix, lens), { phase: 'Refute', label: `refute ep${r.episode}: ${lens.split(':')[0]}`, schema: VERDICT })))
    .then((votes) => ({ row: r, fix, refuted: votes.filter(Boolean).filter((v) => v.refuted) })))
const kept = judged.filter(Boolean).filter((j) => j.refuted.length <= 1)
const dropped = rows.filter((r) => !kept.some((j) => j.row === r))
  .map((r) => ({ episode: r.episode, why: (judged.find((j) => j && j.row === r) || { refuted: [{ why: 'no fix returned' }] }).refuted.map((v) => v.why) }))
log(`${kept.length} fix(es) survive, ${dropped.length} dropped`)
if (!kept.length) return { landed: null, dropped }
phase('Land')
const landed = await agent(`Apply these ${kept.length} surviving diff(s) on master in ONE commit, with every new test file included.
${kept.map((j, i) => `--- fix ${i + 1}: ep${j.row.episode} (${j.row.reason}) ---\n${j.fix.summary}\n${j.fix.diff}`).join('\n\n')}
Apply each diff with 'git apply' (resolve a context drift by hand, never by widening the change). Then run
'uv run --no-sync pytest -q ${kept.flatMap((j) => j.fix.test_files).join(' ')}' and commit ONLY the touched files by explicit path
with a subject that states the behaviour, ending 'Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>'. ${NEVER}
Return the commit sha and the files committed.`, { phase: 'Land', schema: LANDED })
return { landed, dropped }
