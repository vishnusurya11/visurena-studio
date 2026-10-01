# No human input at publish — judge-signed terminals clear the lock

Decision id: `2026-10-01-no-human-input-at-publish`
Owner's words (2026-10-01): "What waive why were they not automated and taken
care of based on the results ?? No human input remember" — then "Remove that
human waiver .. we need automation  upload the episode 15".

## The gap

`studio/publish_lock.py` (2026-09-26, the ep12 root cause: four taste gates in
terminals and a failing voice check, and nothing between the runner and the
channel read any of it) made every open terminal a stop unless
`review/waiver.json` — "the OWNER's hand only" — named it. Two days earlier the
owner had already retired the person from those same gates
(`2026-09-24-automate-the-taste-gates`: judges sign, never park). The two
rulings were never reconciled: ep13 and ep14 each shipped on a fresh
per-episode owner order whose words became the waiver text, so the lock's
demand for a human never surfaced as a design fault until ep15 arrived with
QC passed, every terminal judge-signed, and no owner words to quote.

## The decision

- `publish_lock.judge_waivers(home)`: a terminal on a gate whose gates.yaml row
  is `state: auto` is cleared under that gate's decision id; the reason names
  the judge (`judge:<name>@<version>`). `stops()` applies these before the
  owner's waivers. Recorded in the upload ledger row as `auto_cleared`.
- `youtube_upload.auto_override(dq_failed)`: judge-signed take terminals ride
  an automatic override with the same two decision ids; any `(never judged)`
  entry voids it — nothing unjudged goes up.
- Unchanged, past every automation: gates the registry does not call `auto`
  (the ep12 lesson as the default), the speaker check, the director sign-off
  (the watch still happens and is still written, by the agent as director),
  QC `passed:false` on these bytes, and the Short/square file facts.

## Tests

`tests/test_a_judge_signed_terminal_clears_the_publish_lock.py` — the auto
clear, the unknown-gate hold, the kept sign-off, the unjudged-take void.
