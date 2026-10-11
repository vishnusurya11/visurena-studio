# 2026-10-11 — Cycle 3: the honest clock, the ceiling that never parks, the boundary stop

**Status:** BUILT under the cycle-3 skeptic verdict (`docs/audit/2026-10-10_continuity_retro/C3_verdict.md`,
CYCLES.md's 95 % bar). The owner ordered on 2026-10-11 "don't ask me any more, design it the best way and
implement it", so every call here is made on the evidence and recorded in the verdict's §4 (D1-D12) for
veto. Nothing here spends money.
**Reports:** `C3_T_p90_tail.md`, `C3_R_judges_leftovers.md`, `CYCLE_3.md`.

## What changes in the org chart

| slot | before | after | commit |
|---|---|---|---|
| episode runner (`episode.py run_unit`), shared service `studio/run_clock.py` | the ceiling was charged with `timing.jsonl`: a row per step, stamped in a `finally`; a Stop-Process kill left no row (398 unlogged machine-min over ep19-27, 23 kills) | **the clock is the process (D1):** each run opens a row in `clock.jsonl`, a daemon thread beats `clock.open.json` every 60 s, a clean exit closes the row, the next run closes an orphan as `killed` at its last beat. `run_budget.spent_before` = the UNION of run spans (overlaps once) + legacy timing rows before the first run row. `timing.jsonl` stays for the per-stage report; the command-center progress card reads the new figure | #3 |
| autopilot `retry` (scripts/episode/autopilot.py) | `run_budget.reset_clock`: every retry opened a fresh 5 h (67 retries, all 4 over_budget parks) | **a retry stamps `attempt_at` and never resets the ceiling (D2)**; the ladders' own round counters still read the stamp | #4 |
| the ceiling (step 09, step 02, step 11, `studio/autopilot.derive`, `episode_drive`) | step 09 refused a half-rendered round 0 at a spent clock (it could never finish); the autopilot parked `clock_spent`; the driver stopped resuming | **at the 5 h ceiling (D3):** the takes missing on disk always render; every ladder signs its best flagged; the plan battery's lines are tagged BUILDER (a downstream script repeats the refusal: CONTRACT, G-LIGHT, PLAN GATES, TAKE LENGTH, TAKE BUILDER, MOTION hard, G-TAKELINT, CAST BOUND, ACTOR -- read from the code, `studio/plan_tags.py`) or JUDGED; JUDGED-only signs keep_best flagged, a BUILDER line buys one climb (<= 3 rungs) then a SAFETY stop; QC fails outside the SAFETY list ship flagged with an audit row; nothing parks on the clock; a third spent-clock stop in a row parks `clock_loop`. **SAFETY (closed, `gate_policy.SAFETY`):** short length, title card, line unheard, unjudged takes, stale takes, loudness after the leveller, plan BUILDER line, money, publish auth, GPU lost | #5 |
| the stop path (`studio/boundary.py`; `step_runner`, `judged_gate.climbed`, step 07's grid loop, `takes_r2v.collect_all`; `autopilot pause --at-boundary`) | a session landing a fix killed the drive mid-step (22 of 23 kills, 527 waste-min) | **stop at a boundary (D4):** the flag is read between steps, rungs, grids and takes (the take in hand and the running one finish, the queued ones leave the engine's queue); the run exits `paused_at_boundary` with its clock closed; the drive's end row says so, the autopilot reads it as PAUSED (a resumed series relaunches; it is never a stop or a crash); the next run consumes the flag | #7 |

## Why (measured)
- `episode_clock.timed` stamps its row in `finally` (`studio/episode_clock.py:67`); TerminateProcess runs none.
- C3_T's ledger: honest P50 5.88 h / P90 7.55 h, 4/9 over 6 h, against 5.0 / 6.9 h on the step clock.
- Replay (scratchpad `c3b/clock_replay.py`, CPU): the run-span union over ep19-27 is 3,540 min against
  C3_T's 3,499 machine-min (+1.2 % in total; per episode −5.8 % to +3.7 %: the union also counts the
  between-step overhead no step row held).

## Watch
- ONE PER TAKE was listed BUILDER in the verdict's draft; no downstream script refuses a packed run (`episode_takes.groups` packs it), so it is JUDGED. G-LIGHT and PLAN GATES were called judgement in the draft; `takes_r2v.opened` repeats both, so they are BUILDER.
- The heartbeat is a daemon thread inside the runner; a hung (not killed) runner keeps beating. The
  autopilot's engine-hang rescue still owns that case.

## Addendum 2026-10-11: the downstream reserve (decided on the owner's behalf, for veto)
- **Rule:** the owner's 6 h holds for EVERY episode with zero input. A rescue rung runs only if
  spent + its price + the as-built shares of the firsts after its step fit under 6 h
  (`run_budget.OWNER_LIMIT_SECONDS`, `Budget.leaves_reserve`, checked first in
  `judged_gate.affordable`); a refusal closes the run's rungs (`rungs_closed`) with D3's terminal:
  a ladder signs its best flagged, the plan follows its BUILDER/JUDGED tags; nothing parks.
- **Companion:** past the ceiling a verdict on the same bytes stands under moved code (take_dq's
  report; a passing QC report). A re-judge there is a repeat that can only move a flag.
- **Why:** the 5 h ceiling bounds rungs, not firsts. ep21 crossed 20 min into round 0 (floor 6.3 h).
  Replay (scratchpad c3cpu/replay_3a.py): ep19-27 P90 6.45 -> 5.64 h, 1/9 over (ep21 371 min);
  0/9 with ep21's door refusal cured at step 04 (434213e). Second case (c3cpu/second_case.py):
  it binds on WotW ep12-15 (all > 6 h); a false cut on ep17 (297 min, 2 panel rungs); Scarlet
  ep10-14 none (no plan/grid/panel clock; their retakes leave 32 min owed).

