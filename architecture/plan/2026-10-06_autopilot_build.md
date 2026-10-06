# Build tracker — the autopilot and the brain (decision 2026-10-06, approved)

**Status:** IN PROGRESS 2026-10-06 — four lanes building in parallel on disjoint files,
each lane commits its own files by explicit path; integration + the first live turn after.
Decision: [../decisions/2026-10-06_autopilot_and_brain.md](../decisions/2026-10-06_autopilot_and_brain.md).

Rules every lane keeps: test first; one function 10–20 lines with its own test; no test
spends (fake drive, fake transport, fake procs); no absolute path stored; Strands keeps
every department call; the SDK sits above `drive.py`; nothing under `library/` is edited
by hand; commit by explicit path; never touch `studio/command_center/**`.

- [ ] Lane A — supervisor core: `studio/autopilot.py` (`derive`, `decide`, `classify`, `next_unit`, `status`, lock/heartbeat helpers) + `tests/test_autopilot_*.py` incl. `test_no_silent_stop`
- [ ] Lane B — engine + money terminals: `studio/engine_ops.py`; `plan_ladder.Desk.write` catches `OverBudget` → terminal; `episode_drive.outcome` learns `overbudget`/`escalated`; `DRIVE_QUIET`; `publish_reserve_usd` in `guard_spend`; tests
- [ ] Lane C — brain + ratchet: `studio/brain.py` (brief, options, turn, ledger, allowed), `studio/ratchet.py`; `pyproject` `brain` group pinned `claude-agent-sdk==0.2.159`; `models.yaml` `tiers.brain` + rates; tests with a fake transport
- [ ] Lane D — CLI + install + workflow: `scripts/episode/autopilot.py` (`run|tick|status|install|uninstall|pause|resume|retry|park`), Task Scheduler registration, `.claude/workflows/fix-parked.js`, the brain's allow/deny rule set; tests
- [ ] Integration: wire A–D, full free suite green, `uv sync --all-groups`, SKILL.md "THE RUN" table rewritten (F5), org chart slot flips to built, republish
- [ ] First live turn: `autopilot.py tick` on WotW → ep19 PARKED(over_budget), ep20 launched by the supervisor; one triage turn confirmed on the subscription login; `Workflow` availability under the Python SDK confirmed
- [ ] `autopilot.py install` → task `visurena-autopilot` registered; survives a supervisor kill and a logoff/logon

## Log
- 2026-10-06 — approved; tracker opened; lanes launched.

## Findings (one row per thing that cost time or a hand)

| # | Seen | Cost | Change | State |
|---|------|------|--------|-------|
