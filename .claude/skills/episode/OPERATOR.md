# Operator: the live-run and repair protocol

This page is the one home of what you may do to a live, parked or delivered episode (deadline retro
2026-10-20, item 14). Read this page before any act on a run. It names commands and links
numbers. The numbers live in GATES.md's generated tables. SKILL.md is the chain, and this page is the
hand on it.

## Your job: watch and report, never a hand

You do not launch `drive.py`, you do not run a step script, and you do not edit anything under
`library/`. You read:

    uv run --no-sync python scripts/episode/autopilot.py status --book <codex>
    library/<book>/autopilot/{status.json,events.jsonl,parked.jsonl}
    library/<book>/episodes/epNN/{drive.jsonl,drive_runNN.log,drive_launchNN.log,brain/attempt_NN.json}

When a parked row names a CODE fault, fix it the way the fixer does: the failing test first, the fix,
the suite, one commit by explicit path, then `autopilot.py retry N --book <codex>` (and `resume` if
the series paused). The owner's optional acts are `pause`, `resume`, `retry N` and `park N --why`.

To rehearse, never on the real run: `uv run --no-sync python scripts/proof/rehearse.py <scenario|all>` (a fenced C: sandbox, fake engines, never `library/`), then `scripts/proof/confidence.py`; do not run the board during a rehearsal.

## Before any act (all read-only)

1. `autopilot.py status`: the state, the pause lease and the drive.
2. `git status --short`. Dirty means runtime code. Edits to tests/, docs/, architecture/, library/,
   logs/, `*.md` and `.claude/skills/` never hold a launch.
3. Before committing runtime code during a series: `autopilot.py may-commit`. Exit 3 means a drive is
   RUNNING on that code: land it at a boundary (below).
4. A delivered episode (`manifest.json`): every `drive.py` launch runs `repair_dry_check.preflight`
   itself. To read its table first: `uv run --no-sync python scripts/episode/repair_dry_check.py <book> <n>`
   (exit 1 on a launch it would refuse).
5. A change to prompt words, `take_currency`, the ladder or the deciders: `uv run --no-sync python
   scripts/episode/regress_delivered.py --touched` (the default test run replays it too). A moved
   cell is a delivered take that would move. Name it in an owner order, or do not merge (V6).
   Re-baseline only in its own commit: `--rebaseline ep01 "<why>"`.

## Operating a live run

| you want | do | never |
|---|---|---|
| land a fix | the failing test, `may-commit`; on exit 3 `autopilot.py pause --at-boundary --by <you> --why "..." --book <codex>`, wait for `paused_at_boundary` in the drive log (one unit: a take ~4 min, a grid ~5 min, a plan rung 4-10 min), apply the patch file, run the touched tests NOW (the drive is paused), commit by explicit path, `autopilot.py resume` | edit a file a running drive will load (every subprocess it starts loads it); run pytest or a plan_check beside a Qwen edit; kill a drive (22 of 23 kills over ep19-27 were this, 527 waste-minutes) |
| a plan row is wrong | `plan_repair` (records the cure in `plan.cures.jsonl`); an owner order is a recorded plan edit named `owner_order_<shots>`, judged first as a scratch plan by `plan_check.py <book> <n> --plan=<scratch>.json`; the next entry re-signs over carried rows, no writer round | patch `plan.json` unrecorded; touch a timestamp |
| a gate accuses correct work | read the MEASURE against the WALL; a wall calibrated on another form is a ruler fault: fix the ruler test-first (cheque/check, packs at 8 s, the 240-word floor), then `retry N` | re-roll a render; raise a wall without its replay |
| the owner changes an order mid-run | state the pictures it stales ("inputs: 2 of 28 takes stale"), redraw by the registry route only | a tagged one-off redraw the next step 07 supersedes |

- Code holds still under a live drive (V4). If HEAD moves, the supervisor keeps its code until the
  drive ends (event `code_moved_during_run`). This is normal, so do not kill it. A runtime edit during
  a run is logged (`code_dirty_during_run`), never paused for.
- A relaunch on moved code prints `RELAUNCH on moved code <a>..<b>: judge code changed; ...: <checks>`
  at the top of `drive_launchNN.log`. The verdicts those checks left on disk were signed by the old code.
- A park at an older HEAD or on a dirty tree is never the brain's. A `brain:` park clears itself when
  runtime code lands (2 per episode).
- After a prompt-builder change, before any re-render: a no-write take-build replay (rebuild the dry
  prompts, diff against `takes/r2v/shots.json`, list the changed takes).
- On a plan park, read `plan.cures.jsonl` and the learnings `draft` row first. After a panel rewind,
  read the `panel_eye` row in timing.jsonl (`reads=N cache_hits=M unread=K`) or `books` in the signed eye file.
- A slow face refine: read refine.json's `gpu_wait_s` / `gpu_busy_s` per take (a `span_s` is overlapped wall,
  not a cost) and `readable_clause`; a slow QC ear: `review/work/qc_whisper.err` and the `poll() =` line.
- After each run, read `library/.device/gpu_util.jsonl` (`gpu_ledger.minutes_per_step`: busy /
  claimed / idle) and `scripts/audit/doc_sync.py` (fix commits with no doc line).
- A spent clock ships the episode flagged (C3_verdict #5). Read the audit sheet, and never `retry` to
  buy hours: a retry never resets the clock.

## Pause leases (V7)

- Pause with a lease: `uv run --no-sync python scripts/episode/autopilot.py pause --by retro --why "<what you build>" [--hours H]`.
  A retro pause is said again by Telegram at 2 h, and nothing resumes it but `autopilot.py resume`.
- An owner pause (`--by owner`, the default) is never lifted by code. The autopilot resumes only its
  own two-parks brake, once its lease has run out and a commit has landed.
- Never set a pause without an end: the 23:11 retro pause on ep01 had none and sat under a dead session.

## An owner redo of a delivered episode (the repair)

- **The order.** An owner redo is a recorded `work_orders` row `by` owner. A note naming `T<nn>` orders
  that take, and a redo of a step before 09 orders every take. Do not write a second order while the
  first is owed. Plan any re-shoot of a repaired episode as an owner order.
- **The clock.** It runs on `studio/repair_clock`: its own cap (GATES.md clock table, `repair cap`),
  `repair` rows, never the 6 h. The finish line shows each window against its own cap.
- **The freeze.** A redo of 09 or later freezes the delivered takes at every place that renders, past
  its drive, until an owner redo of 01-08 governs (`take_currency.governing`). The sites are listed by
  `tests/test_every_take_writer_holds_the_freeze.py`, and a new writer of `T<nn>.mp4` fails it. A
  ladder round counts only on bytes its own run landed. A leftover window closes at drive start unless
  its orders are still backed.
- **The launch.** Read the dry check's table, write the order, `retry N`, `resume`, then pause at its
  end. The drive asks the deciders itself (render pass, early round, batched rung, terminal swap,
  freeze). An unordered delivered take in any of them writes `REFUSED to start: the dry check ...`,
  exits 2, and leaves the window open. A check that raises refuses too.

## Guards

A guard you run beside a live drive (a log watcher, a kill on a pattern) is a rule like any other.
Derive it from the code's print order, never from a guess. Key a guard on bytes written to `takes/`, or on the decider's own answer, never on a
log line. Run it once against a dry run of what it guards before you trust it. Never kill a process
holding a long draw without a reason line the owner can read. A killed draw's booked round is given back
with `step_attempts.refund`.

## Resuming

1. Read `episodes/epNN/drive.jsonl` and the last `drive_runNN.log` (one log per launch), and say back
   where the episode is.
2. Resume through the autopilot only: `autopilot.py retry N --book <codex>` for a parked episode,
   `autopilot.py resume --book <codex>` for a paused series. Never launch drive.py.
3. The autopilot restarts a dead ComfyUI after 2 missed ticks. If a job ignores `/interrupt`, see memory
   `project_comfy_restart`. Never kill a drive (memory `project_kill_run_tree` is for a run already lost).

## OAuth (the YouTube token)

The refresh token dies every 7 days while the OAuth app is in Testing. At launch and at render start, a
token 5 days old (or one whose refresh fails) sends the consent link once per drive. The owner opens it,
approves, and pastes the failed `http://localhost:8765/?state=...&code=...` address. Then run
`uv run python scripts/publish/youtube_auth.py --paste=<address>`, which also stamps
`YOUTUBE_REFRESH_TOKEN_AT`. Check that the token is The Keeper's Lantern's before anything uploads. The
durable fix is the owner's click (V1: consent screen to Production). Do not call it fixed until a token
minted after the switch has lived 8 days. Nothing uploads unless the owner asks.

## Symptoms

| symptom | cause | do |
|---|---|---|
| every delivered take reads stale ("not current to its card") after a commit | prompt words changed (P03 at 11:18) | `regress_delivered.py` names the takes; under a repair of 09+ the freeze keeps them; never launch a pass that writes them unordered |
| the ladder queues a frozen take for a retake (`queueing 1 takes ... T01`) | a decider that skips the freeze (P08's early round, 12:29) | `pause --at-boundary`; the writer lint names the site; fix it test-first |
| a guard killed a legal draw | the guard waited on a line the code prints later | "Guards" above; refund the round |
| `REFUSED to start: the dry check lists N delivered take(s)` | a delivered take would be written with no owner order | name it `T<nn>` in an owner order, or fix the decider, then `retry N`; a bare relaunch changes nothing |
| every unchanged take re-measured on a resume | `GATE_VERSION` bumped, or a record from before 2026-10-20 (no `gate_version`) | owed once; a hash move alone no longer re-measures |
| the pin test is red after a MEASURES edit, or after an edit to look_table.py, panel_dq.py or people_count.py | they judge take content (the import closure of take_content.py) | bump that check's `GATE_VERSION` if a verdict changes, else re-pin `gate_pins.json` |
| Telegram: "autopilot supervisor silent for N min" | the PC restarted (Windows Update) or the loop died | log on, or `schtasks /run /tn visurena-autopilot`; then `status` |
| Telegram: "YouTube token ... open <link>" | the 7-day token | "OAuth" above |
| state `HELD_PUBLISH` | the master is finished; step 13 waits until `publish/standing.json` lists this episode in `episodes` (2026-10-20), which only the owner writes | nothing: the series moves on; never write that file, never `retry` a held episode |
| step 13 prints `G-INORDER: in order on <playlist url>` | after the public flip (2026-10-21) the episode joined its book playlist at its episode-order place, its description got the "— Watch in order —" block and the previous episode a Next line; each act is an `uploads.jsonl` row (`playlist`, `playlist_item`, `watch_block`, `next_line`, `in_order`), the id read from the book video's `compilation/youtube.json` or the previous episode's live block; a playlist is made only when the book has none | nothing; a failed upkeep stops step 13 before the /shorts/ poll and a re-run skips every recorded act |
| event `code_moved_during_run` | HEAD moved under a live drive | normal; the supervisor keeps its code until the drive ends |
| finish line `repair X h of a Y h cap` | each repair window against its own cap (the line once summed both against the second cap) | read each window alone |
| finish line `killed X h in N runs` | a share of the charge and the repair the line already holds | never add it as a third part |
| state `WAIT_TREE` | uncommitted runtime code | commit your own paths the moment a run stops |
| step 03 records `stalled` in `storyboard/cells_from_picture.json` | a vision read stalled twice | a resume before the grids reads again; it is not an unreadable picture |
| ComfyUI will not come up | run `nvidia-smi` first; "GPU is lost" needs the owner's reboot | keep the series paused, then `retry` + `resume` |

## Fixing an owner-reported defect (the agent process; the orchestrator reads this before any fleet)

- Read `docs/audit/` for an existing plan or research on the question before launching research.
- **round 0** counts the defect on the real takes (CPU, minutes) and predicts a number ("moves N of
  28"). The bench is judged against that number. In ep01's round 1, two of three builds moved nothing:
  the framing floor moved 0 of 12 plans.
- The reviewer runs the change on the real ep01 files (the deciders, the gate verdicts, the face
  crops), not only the package tests. Diff-reading reviewers passed 23 of 24, and measuring reviewers
  sent 6 of 8 back. A minor that names an unproven half gives the command that proves it, or it becomes
  one bench or a dated open item: at most one block per package.
- **at most 2 fix rounds** per package. A third goes to the main session with the skeptic's repro.
  The cap is on rounds, not minutes: a 45 min cap would have killed the 151 min round that worked.
- **The budget per defect:** one research fleet, 2 build rounds and about 3 h of agent wall (V5). Then
  the repaired master ships, or the owner gets a one-line stop (what is left, what it costs).
- A change to prompt words, the ladder or the freeze merges only with an empty (or named) replay diff
  on delivered ep01 (`regress_delivered.py`).
- One concern per builder, disjoint files, the one checkout. Commit your own paths, never `-A` or `stash`.

## The report line

The master's full path first, then QC's "inputs: all N takes current", every `CAP` line of the run, the
flagged takes with their seconds, then the time left in Seattle time.
