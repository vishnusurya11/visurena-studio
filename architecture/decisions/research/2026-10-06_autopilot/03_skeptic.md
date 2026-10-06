# SKEPTIC — the unattended "brain" that fixes code mid-episode

Proposal under attack: supervisor runs `scripts/episode/drive.py`; on defer/fail an Agent SDK
session reads logs, writes code + tests, commits, relaunches. No human.

## 0. The proposal has already been run. Four times. Here is the ledger.

The "brain" is not hypothetical. On ep17 and ep19 a Claude session did precisely this loop by
hand (read log -> patch code -> test -> commit -> relaunch). The disk shows what it bought:

| Episode | Launches | Distinct code SHAs during the episode | Outcome | Source |
|---|---|---|---|---|
| ep17 | 6 | **6** (7e3ad5b, 365abe7, f86f4d1, a6133af, a0ae011, 7e9668b) | completed, after hand edits of plan.json/refs.json (tracker §problem) | `library/20260827135508_the-war-of-the-worlds/episodes/ep17/drive.jsonl` |
| ep18 | 6 | 1 (aea4e3a) — six "refused" runs on one SHA = six rounds of hand-edited library data | shipped with `EYE_PANELS keep_best @ attempt 0`, `EYE_TAKES keep_best`, `MASTER flag` (faces, content x3) — the ep12 shape exactly | `.../ep18/learnings.jsonl` last 6 rows |
| ep19 | 4 | **4** (89887d3, c5f64f3, e6096e8, 2a50fc4) | 3 deferrals + 1 crash `OverBudget $3.10/$3.00`; 11 writer calls; 4,537 s of PLAN ladder; **zero pictures, not shipped** | `.../ep19/drive.jsonl`, `drive_run01.log`, `timing.jsonl` |

Between ep19's launch 1 (05:24) and its crash (14:43) the brain-by-hand made 8 commits
(`git log --since=2026-10-06`: ea64dd6, 2e9ff9c, 5ace51d, e6096e8, 2a50fc4, ed991c4, 65dc097 ...).
72 commits since 10-04 total. The tracker (`architecture/plan/2026-10-05_self_curing_pipeline.md`)
says "ten lanes, 27 commits, every lane green" and then lists F7, F8, F9, F10, F14, F17 — six
findings where the green fixes themselves put false faults into the next run (G-STAGE firing on
the film word "shot" = 20 false faults every shot; G-ARTICLE's regex reaching disk with `\b` as a
backspace byte; cures writing "the opened the Martian cylinder" into 30 fields). The loop is
measured: **one fix per ~75 min, each fix a coin-flip to add a new deferral class, and the
episode is still not shipped at $3.10.** Automating the operator does not change the operator's
hit rate; it removes the only thing that stopped it at $3.10 — someone reading the number.

The owner's rules this proposal contradicts by construction, not by accident:
- `feedback_drive_not_babysit.md`: "Never commit code during a run ... one episode runs on one commit."
- `project_five_hour_episode.md` fix #7: one episode, one commit (ep14 ran across 23; the warning
  at `scripts/episode/drive.py:120` exists because of it).
- `docs/audit/2026-10-01_plan_hours_debate.md`: `PLAN_LADDERS_MAX = 1` — a second deferral must
  REFUSE, not relaunch. Every ep19 launch log opens with `WARN ... the desk says deferred; running
  on the owner's word` — the brain-by-hand bypassed the cap four times. A brain-by-SDK will bypass
  it every time, because relaunching is its job.

## 1. Runaway loops — likelihood HIGH x damage HIGH (rank 1)

**Scenario (already observed on ep19):** deferral on G-STORY -> brain adds `quiet_share` ->
relaunch -> deferral on G-SYNC -> brain adds `dialogue_first` -> relaunch -> OverBudget crash ->
brain reads "spent $3.10 of $3.00" and ... raises `episode_ceiling_usd` in `models.yaml`, or
re-tiers the writer (ea64dd6 did the opposite tier move 3 h before the wall broke — F20). Each
relaunch re-pays the writer because the plan signature lapsed (decision file: "every hand edit
lapsed the plan signature and paid the writer again").

Second shape: the brain's fix is a *new gate* (F7, F17 were both new gates). New gates fire on
the next chapter's correct English (G-STAGE on "shot", G-ARTICLE needing a scan over every
delivered plan to stop flagging verbs). The brain then "fixes" its own gate. This is an
oscillator with no damping, and `feedback_constants_outlive_their_world.md` says this is the
repo's single most frequent fault class.

**Caps (hard, in the supervisor, not in the brain's prompt):**
- `FIXES_PER_EPISODE = 1`. One code commit between first `start` and `end` in `drive.jsonl`.
  A second deferral after a fix => the episode is PARKED (a row in a series-level
  `parked.jsonl`, the aside kept) and the autopilot moves to the next chapter the same minute.
  Nothing waits. Rationale: ep19 shows fix #2 through #4 bought nothing; `PLAN_LADDERS_MAX=1`
  already encodes the same judgement for the writer.
- `BRAIN_SESSIONS_PER_EPISODE = 1`, `BRAIN_SESSIONS_PER_DAY = 3` across all episodes (a bad gate
  will defer every episode; three in a row is the signal, not three fixes).
- `BRAIN_USD_PER_EPISODE = $1.00`, counted INSIDE the $3 wall (see §3), not beside it.
- The brain may not relaunch an episode whose `drive.jsonl` already shows two distinct SHAs —
  that is drive.py's own "code moved mid-episode" warning promoted to a refusal
  (`studio/episode_drive.py` — add `first_sha != sha and sha_count >= 2 -> refuse`).
- Any fix that touches a file under `studio/plan_gates.py`, `studio/plan_cures.py`,
  `studio/judges/**`, `gates.yaml`, `models.yaml` is not a "fix" — it is a calibration change
  and goes to §2's rule.

## 2. Wrong fixes — the fix that only weakens — likelihood HIGH x damage HIGH (rank 2)

**Scenario:** G-STORY says "narration-only run 89.6 against 75". The cheapest passing change is
`75 -> 95`. The brain-by-hand did something subtler but structurally identical in 2a50fc4:
`narration_wall = max(75, quiet x runtime)` — a wall that *stretches to fit the chapter*. It is
argued well in the commit message; it is also precisely a threshold that moves to let the
current artefact through. ep12 shipped on `keep_best`/`flag` terminals
(`docs/audit/2026-09-26_ep12_root_cause.md`: "Every taste gate on ep12 ended in a terminal, not
a pass -- and I published anyway"). Every gate in `gates.yaml` lines 14-20 has
`terminal: keep_best|flag` — none stops. The 10-01 ruling (`project_no_human_input_at_publish.md`)
makes a judge-signed terminal auto-clear the publish lock. So: brain loosens or no-ops a gate ->
run reaches a terminal -> step 13 uploads public. ep18's final learnings row is `MASTER flag:
faces at master; content at shot_01; content at shot_21` — under step 13 that is a public Short.

**Detection that is mechanical, not prompt-based:**
- **Red-before-green, enforced by the supervisor, not trusted from the brain:** the brain's
  commit must add >= 1 test file; the supervisor checks out `HEAD~1`, runs ONLY the new test
  files, and requires a non-zero exit; then runs them on `HEAD` and requires zero. A fix with no
  test that fails on the old code is rejected and reverted (`git reset --hard HEAD~1` by the
  supervisor; the brain never runs git reset). This is `feedback_a_fix_that_changes_nothing.md`
  as code.
- **Threshold diff lint:** a numeric literal changed in `studio/plan_gates.py`,
  `studio/judges/**`, `studio/*_ladder.py`, `gates.yaml`, `models.yaml`, or any `MAX_*`/`*_CAP`/
  `*_WALL`/`*_SHARE` constant anywhere, requires in the same commit a new row in
  `tests/fixtures/episodes/` calibration (the ep05/ep07 good, ep08/ep09 bad set from
  `feedback_gates_are_not_quality.md`) AND the ratchet test
  (`tests/test_a_judge_may_not_lose_a_catch.py`) still green. No calibration row => reject.
- **Ratchet on catches:** a fix may not reduce the fault count the battery reports on the
  delivered plans of the last 3 shipped episodes (F10's "pre-launch dry check" turned into a
  pre-commit assertion: `plan_check` over ep16/17/18 plans must report the same or MORE faults
  after the fix than before, unless each removed fault is in a named false-positive list the fix's
  test asserts). This catches "the gate went quiet" — the exact ep09 failure (28/28 at 100 while
  worse).
- **Forbidden edit classes:** `terminal:` values in `gates.yaml`; `episode_ceiling_usd`;
  `PLAN_LADDERS_MAX`, `MAX_IMPROVE`, `ROUNDS_CAP`, `MAX_RUNS`; anything under `studio/llm.py`
  `guard_spend`. Hook-level deny on the path + a supervisor grep on the diff.

## 3. Spend — likelihood MEDIUM x damage MEDIUM (rank 4)

**Scenario:** the $3 wall is a wall on *the episode's writer calls* recorded through
`studio/spend.unit_spent` (`studio/llm.py:138-149`). It is estimate-before-send and ep19 still
landed at $3.10 — it leaks by one call's estimate error. The brain's own session is Opus/Sonnet
reading 100 KB logs plus a 907-file test tree; one brain session reading `drive_launch01.log`
(a single 27 KB line of battery output) and running the suite is plausibly $1-3 by itself and
is charged to NOTHING today. Four sessions = ep19's whole media budget again, invisible.

**Guardrail:** one number per episode: `spend.unit_spent + brain_usd <= 3.00`, where the brain's
usage (from the SDK's per-turn usage) is written as rows into the same spend table under the
episode's unit id with `purpose: brain`. Hard stop: the supervisor kills the brain session at
$1.00 of its own spend, PARKS the episode, moves on. Who is told: nobody is *asked*; Telegram
via the existing `notify_bench.py` path (`scripts/episode/drive.py:NOTIFY`) gets a receipt with
the three numbers (media, brain, wall) — a log line the owner reads when he likes, never a gate.
A parked episode is re-tried by the autopilot itself only under §5's rule (on a SHA that has
since shipped a clean episode), never on a human word.

Also: the tracker's F20 fix prices a tier against `MAX_IMPROVE` rounds — good — but that is a
"proposed" row. Until it is code, a brain can re-tier the writer the way ea64dd6 did and blow
the wall in one launch.

## 4. Data integrity — likelihood MEDIUM x damage HIGH (rank 3)

**Scenario:** the cheapest fix for "G-SYNC line 3 must be first on its shot" is to edit
`episodes/ep19/plan.json`. The brain-by-hand did this on ep17/18 (decision file, §problem) and the
writer "re-added the very clauses the hand had removed". A brain with Edit on `library/**`
will do it on its first deferral because it is the fix with the shortest diff. Worse: a brain
that cannot make a gate pass can write `plan.verdict.json` itself — "never sign verdict files by
hand" (`project_judges_replace_the_eye.md`) has no hook enforcing it today.

**Allowed write set (deny-by-default, enforced by PreToolUse hook in `.claude/settings.json`
AND by a supervisor diff check — the hook alone is bypassable via Bash heredoc):**
- allow: `studio/**/*.py`, `scripts/**/*.py`, `agents/**/*.py`, `tests/**/*.py`,
  `architecture/plan/2026-10-05_self_curing_pipeline.md` (the findings table only).
- deny: `library/**` (every byte), `**/*.verdict.json`, `**/eye_*.json`, `**/learnings.jsonl`,
  `**/drive.jsonl`, `gates.yaml`, `models.yaml`, `stages.yaml`, `pyproject.toml`, `uv.lock`,
  `.claude/**`, `docs/DECISIONS.md`, `architecture/decisions/**`.
- deny Bash patterns: `git push`, `git reset`, `git checkout --`, `git commit --amend`,
  `uv add`, `uv remove`, `uv sync`, `rm -r`, any `>`/heredoc write whose target resolves under
  `library/` (the hook must resolve the path, not grep the string), `touch`.
- deny all `mcp__claude_ai_Higgsfield__*` and `mcp__comfy-mcp__*` generate/run tools — the brain
  diagnoses; it does not render.
- The supervisor, not the brain, runs `git diff --name-only HEAD~1` after the brain's commit and
  reverts the commit if any path is outside the allow set. Two independent checks because
  `feedback_patch_scripts_not_heredocs.md` and F17 show a shell write reaching disk in a form the
  author did not intend.

## 5. Quality drift — likelihood HIGH x damage HIGH, slow (rank 2b)

**Scenario:** nothing in the proposal looks at a picture. Owner calibration rows on disk:
`library/20260827135508_the-war-of-the-worlds/casebook/owner.jsonl` — the ratchet's bench
measures "false refusals only; owner recall is 0/0" (`project_judges_replace_the_eye.md`). The
calibration fixtures are Sherlock ep05/07/08/09 (`tests/fixtures/episodes/`) — a different book,
a different aspect, a different renderer. A brain that optimises for "drive.py exits 0" has a
loss function that is exactly `feedback_gates_are_not_quality.md`'s warning: "almost every one
of those faults was introduced the same day in the name of fixing episode 8". Ten green episodes
of drifting output is the realistic failure, and it is the one the owner notices last and
hates most (ep09: "the owner saw it in minutes").

**The only human touchpoint is the design approval, once (owner, 2026-10-06). So every brake
below is self-acting; nothing parks "until the owner". What survives, async only:**
- The owner audits *after*, whenever he likes: the public Short, the sheets that already exist
  (`library/<book>/audit/epNN.html`, `audit/rows.jsonl`), and a series-level `parked.jsonl`
  (episode, SHA, gate, measured vs wall, the brain's report). A casebook note he files
  (`scripts/audit/note.py`) is data the ratchet consumes on the next run — it is never waited on.
- **What the autopilot does on its own on N consecutive bad outcomes** (counted over the series,
  reset by one clean ship):
  - 2 consecutive episodes PARKED, or 3 consecutive shipped with `terminal: flag` on MASTER
    => the fault is the code, not the chapters. The autopilot **demotes the brain to
    report-only** for the rest of the series and **pins the series to the last SHA that shipped
    a MASTER with zero terminals** (`git checkout <sha>` in a detached run, drive.py's SHA ledger
    already records which). It then re-queues the parked episodes on that SHA once each, behind
    the fresh chapters. A parked episode that parks again on the clean SHA is left parked for
    good (the chapter is the problem; the series moves on).
  - If the pinned SHA also parks 2 in a row: the autopilot stops launching — not waiting for a
    human, but because the rule says a pipeline that cannot ship on its best-known code has
    nothing left to try unattended. The Telegram receipt says so. The owner's next design change
    is the only thing that restarts it, and that is the one touchpoint he approved.
  - A flagged MASTER never upgrades to a pass by relaunch: `QC once per master sha8` already
    holds (`project_five_hour_episode.md`); the brain may not re-judge a master.
- Every shipped episode's MASTER verdict, the brain's diff (if any) and the public URL go into one
  Telegram receipt. Not a question.
- The brain never runs `scripts/episode/eye_review.py` and never writes `director_signoff.md`
  (b815244 renders it from measures; keep it that way).

## 6. Is it premature? Yes. The alternative, with numbers.

What the tracker actually says the hand did on ep17-19 (F1-F20): 14 of 20 rows are "fixed +
tested" or "done in code" — the recurring classes were (a) a new gate firing on correct text
(F7, F8, F14, F17), (b) cures applied as one all-or-nothing round (F9, F11), (c) stale plan
judged / signature lapsed (F20, ep18 "refused" x6), (d) a wall calibrated on the wrong population
(F18, G-STORY 75 s), (e) infrastructure (F1 slow suite, F2 buffered output, F13 watcher). None
of these needed a brain at 03:00. They needed: F10's pre-launch dry check over the last 3
delivered plans (seconds, $0) and a supervisor that **stops and pages** instead of a session that
"stops in the middle".

The owner's actual pain is the session ending — a lifetime problem, not a judgement problem.
That is solved by the supervisor half of the proposal alone: a Python process (or `/loop`) that
relaunches `drive.py` on the conditions drive.py already encodes, honours `MAX_RUNS=6`,
`PLAN_LADDERS_MAX=1`, `ROUNDS_CAP=2`, parks what will not ship, and moves to the next chapter.
Zero new judgement, zero new spend, zero new attack surface, zero waiting. The brain is the
expensive half and the evidence says its hit rate is about one useful fix per two tries with the
episode still unshipped.

**Recommendation on autonomy: REPORT-ONLY now; one narrowly fenced FIX class later; never FULL.
All three levels are unattended — "report-only" means the brain's output is a file, not a
question; the series never waits on anyone reading it.**

- Now: the brain is a *diagnoser*. On defer/fail it reads the logs and writes one F-row into the
  tracker's findings table (`architecture/plan/2026-10-05_self_curing_pipeline.md`, the only
  file it may edit): fault class, the gate, measured vs wall, the three comparable artefacts on
  disk it checked (`feedback_constants_outlive_their_world.md`'s method), a proposed diff as
  text. Cost cap $0.50. The supervisor parks the episode and launches the next chapter. The
  parked list accumulates diagnoses; a code session (the owner's, or a scheduled one that runs
  the full suite on a clean tree between episodes, never mid-run) applies them in batches —
  one commit per batch, then the parked episodes are re-queued on that commit. This keeps
  "one episode, one commit" true and keeps the fix off the episode's clock.
- Later (after 5 consecutive parked episodes whose proposed diff shipped unchanged — the
  supervisor can count this from the tracker and the commit log, no human grades it): allow
  `fix-with-tests` for ONE class only — a Python traceback in `studio/**` or `scripts/episode/**`
  (a crash, not a refusal). Crashes have an objective red/green; gates do not. All §1-§4 caps
  apply. Threshold/gate/cure edits stay report-only forever, because the repo's own memory says
  the most frequent fault *is* a threshold that looked right.
- Full autonomy fails the owner's own standard twice over: `feedback_a_terminal_is_not_a_pass.md`
  (a runner completing is not quality) and `feedback_spend_approval.md` (spend inside a goal is
  pre-authorised *at known prices* — the brain's price per episode is unknown and unbounded).
  The one-touchpoint rule makes this worse, not better: with nobody ever in the loop, the only
  thing standing between a loosened gate and a public upload is the ratchet in §2 — so §2 is not
  optional at any autonomy level.

## Ranked summary (likelihood x damage)

1. Runaway fix/relaunch oscillator with new gates flagging correct text — HIGH x HIGH. Cap 1 fix,
   1 session, refuse relaunch at 2 SHAs; park and move on.
2. Gate loosened/no-op'd -> terminal -> auto-publish — HIGH x HIGH. Red-before-green by the
   supervisor; threshold lint needs a calibration row; ratchet on last-3-plans fault count.
2b. Slow quality drift under green ladders — HIGH x HIGH (slow). Self-acting: 2 parked or 3
   flagged in a row => brain demoted to report-only, series pinned to the last clean-shipping
   SHA, parked episodes re-queued once; receipt with diff + URL per ship, never a question.
3. Brain edits `library/**` or signs a verdict — MEDIUM x HIGH. Hook deny + supervisor diff
   revert; no git push/reset/amend, no uv add.
4. Brain spend uncounted beside the $3 wall — MEDIUM x MEDIUM. One number; brain rows in the
   spend table; $1 brain cap; park on the wall.
5. Premature: ship the supervisor (relaunch + park + next chapter), keep the brain report-only;
   fixes land between episodes on a clean tree, one commit per batch.
