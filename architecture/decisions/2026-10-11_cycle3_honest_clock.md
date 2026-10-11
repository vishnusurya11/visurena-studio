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

## Why (measured)
- `episode_clock.timed` stamps its row in `finally` (`studio/episode_clock.py:67`); TerminateProcess runs none.
- C3_T's ledger: honest P50 5.88 h / P90 7.55 h, 4/9 over 6 h, against 5.0 / 6.9 h on the step clock.
- Replay (scratchpad `c3b/clock_replay.py`, CPU): the run-span union over ep19-27 is 3,540 min against
  C3_T's 3,499 machine-min (+1.2 % in total; per episode −5.8 % to +3.7 %: the union also counts the
  between-step overhead no step row held).

## Watch
- The heartbeat is a daemon thread inside the runner; a hung (not killed) runner keeps beating. The
  autopilot's engine-hang rescue still owns that case.
