# Build tracker — the autopilot and the brain (decision 2026-10-06, approved)

**Status:** BUILT 2026-10-06, LIVE on WotW — four lanes (7fcf13d, 7d2b630+9f9f767, 2fbbdc3,
a4e9e7e), wired (3f3c171, 49d5fa0), task `visurena-autopilot` registered; the first live
hours exposed six faults, all fixed in code (3124c78, e3e2fd3, d3f7037, 49d5fa0, b1d0d25).
Proof run continues: ep20 and ep21 re-queued on b1d0d25.
Decision: [../decisions/2026-10-06_autopilot_and_brain.md](../decisions/2026-10-06_autopilot_and_brain.md).

Rules every lane keeps: test first; one function 10–20 lines with its own test; no test
spends (fake drive, fake transport, fake procs); no absolute path stored; Strands keeps
every department call; the SDK sits above `drive.py`; nothing under `library/` is edited
by hand; commit by explicit path; never touch `studio/command_center/**`.

- [x] Lane A — supervisor core: `studio/autopilot.py` (`derive`, `classify`, `next_unit`, `status`, `stale_lock`) + 3 test files, 66 tests (7fcf13d)
- [x] Lane B — engine + money terminals: `studio/engine_ops.py`; `OverBudget` → ladder terminal; `overbudget`/`escalated` outcomes + `error` ledger field; `DRIVE_QUIET`; `publish_reserve_usd`; 114 tests (7d2b630, 9f9f767)
- [x] Lane C — brain + ratchet: `studio/brain.py`, `studio/ratchet.py`; `claude-agent-sdk==0.2.159` in the `brain` group (bundled claude.exe); `tiers.brain` + rates; fake-transport tests, 56 (2fbbdc3)
- [x] Lane D — CLI + install + workflow: `scripts/episode/autopilot.py`, `.claude/workflows/fix-parked.js`, 46 tests (a4e9e7e)
- [x] Integration: brain brief/Verdict wired (3f3c171); ledger + clamp + retry retires attempts (49d5fa0); grammar fallback, HEAD-move restart, two-parks brake (b1d0d25); org chart slot built
- [x] First live turn: tick 1 → ep19 PARKED(over_budget); tick 2 → ep20 launched by the supervisor; the scheduled loop's own ticks ran the brain's first triage turns on the subscription login (25 s, ~$0.28 list-equivalent each, correct diagnosis)
- [x] `autopilot.py install` → task `visurena-autopilot` registered (Interactive logon, AtLogOn + every 5 min; S4U/AtStartup need elevation)
- [ ] ep20 published by the loop with zero hands (the proof); then ep21+
- [x] SKILL.md "THE RUN" table rewritten: the agent's job is WATCH + report; non-negotiables 3 and 4 name the autopilot (F5 of the self-curing tracker)
- [ ] `Workflow(fix-parked)` confirmed under the Python SDK on the first fixer turn
- [ ] Owner-elevated one-time: re-register with AtStartup (survives a reboot without a logon) — optional

## Log
- 2026-10-06 17:26Z — first tick: ep19 parked (over_budget). 17:27Z ep20 launched. 17:31Z task live; its tick found the stale lock, ran the brain, parked ep20 (400: strict grammar too large). 17:36Z ep21 launched, same 400, parked 17:40Z. Loop paused by hand; six fixes; re-queued.
- 2026-10-06 — approved; tracker opened; lanes launched; all four landed within 15 min.

## Findings (one row per thing that cost time or a hand)

| # | Seen | Cost | Change | State |
|---|------|------|--------|-------|
| A1 | The writer's strict structured call died with a 400 from every provider: "compiled grammar is too large" — the Episode schema compiled as a grammar is over the provider's limit (new today; ep19's 11 calls passed hours earlier) | ep20 + ep21 parked, 4 brain turns | `_parse` falls back once: no `response_format` at all (OpenRouter makes ANY json_schema a strict tool, `strict:false` included), the schema goes in the prompt, the JSON reply is validated here (`schema_prompt`, `json_body`) | fixed + tested (3124c78, b1d0d25) |
| A2 | `Register-ScheduledTask` with an S4U principal or an AtStartup trigger is refused (0x80070005) from a limited shell; PowerShell still exited 0 | first install reported success and registered nothing | `install` ladder S4U+AtStartup → Interactive+AtLogOn; `-ErrorAction Stop` + `exit 5` so a refusal is a non-zero exit | fixed + tested (e3e2fd3) |
| A3 | The task's first start failed 0x80070002: Task Scheduler has no user PATH, the action named `uv` bare | one dead start | `install` resolves `uv.exe` by `shutil.which` into the action | fixed + tested (d3f7037) |
| A4 | The brain's turns left no `usage` row and no order clamp — the CLI called `turn` but not lane C's `ledger`/`allowed` | spend invisible | `run_brain` ledgers each turn as `stage='brain'` for the unit and clamps the order to the desk | fixed + tested (49d5fa0) |
| A5 | `retry N` cleared the parked row but the next tick re-read the old `attempt_01.json` (park) and the old `end` row as today's state → a second brain turn, parked again | 1 brain turn | `retry` retires the episode's brain attempts to `brain_retired_NN/`; a retry newer than the last `end` row reads as a fresh launch (`retried_since`) | fixed + tested (49d5fa0) |
| A6 | The long-lived loop never reloads code: the 17:31Z instance ticked on stale code through four fix commits and paid the brain to re-judge a bug already fixed; `Stop-ScheduledTask` left its python children alive | 2 brain turns, ep21 launched on old code | `run_loop` exits 0 when HEAD moves (`code_moved`) and the 5-min trigger starts a fresh one; stale children killed by pid | fixed + tested (b1d0d25) |
| A7 | The approved design's drift brake (two consecutive parks → pause) was in no lane's file list; ep20 and ep21 parked back to back with ep22 next | the series would have parked itself chapter by chapter | `brake_two_parks` in `park()`: the series pauses itself, one Telegram, `retry N` + `resume` lifts it | fixed + tested (b1d0d25) |
| A8 | Skill: a build fanned into lanes needs an integrator's checklist read FROM THE DESIGN (every noun in the design → a lane or the integrator), not from the lanes' own reports | A7 | the lane prompt template gains "the design's full feature list; mark which are yours; name the rest as NOT MINE" so an orphan feature is visible before launch | proposed (skill) |
