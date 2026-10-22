# Plan: agent triggering and the shut usage window (group R, 2026-10-22)

Status: **WAVE 0 PART BUILT 2026-10-22** -- A1, A2, A5 and the A10(b) pin landed; the task runner is
proposed, not built. Decision: [decisions/2026-10-22_agent_task_runner.md](../decisions/2026-10-22_agent_task_runner.md).

## Wave 0 (defect fixes; 0 GPU, $0)

- [x] A5 -- the write fence reads PowerShell (commit 408ab77)
- [x] A2 -- `.env` never loads ANTHROPIC_*; a visible key refuses the spawn (commit 219b0da)
- [x] A1a -- RateLimited is an llm.LimitWait; structured raises it after one call; limit text is the same wait (commit a33e4f5)
- [x] A1b -- the autopilot's WAIT_QUOTA: global quota.json, no brain call, one notice, relaunch past the reset (this commit)
- [x] A10(b) -- `_caller_for` regression pin (this commit)
- [ ] A3 / A7 / A8 / A9 -- with the runner (instrumentation, not defects)
- [ ] A4 -- needs models.yaml rate rows (owner's file)
- [ ] A11 -- measure the scratch cwd and lean MCP flags on the SDK path first

## The runner (proposed; build gate open, default gate closed)

- [ ] fix the prototype's claim race, short heartbeat lease, limit-text park, dead worker's stream
- [ ] `studio/agent_jobs.py` + `scripts/ops/tasks.py`, test-first
- [ ] re-run R-B4 on the lifecycle wall it registered
- [ ] owner yes on the design

## Log

- 2026-10-22 -- group R gavel ruling, nine benches (eight ran, ~125 subscription calls, $0), skeptic
  pass; wave 0 defect fixes landed test-first.
