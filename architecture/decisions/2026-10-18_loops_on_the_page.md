# 2026-10-18 -- A run that loops, shown as it is (and three pipeline moves)

Status: APPROVED (owner, 2026-10-18: go on D1, D2, D3, P1, P2, P3).
Evidence: `docs/audit/2026-10-18_timeline_debate/` -- ten experts, two rounds; `PROPOSAL.md` is the
ruling, `FACTS_R1.md` the settled facts. Tracker: `architecture/plan/2026-10-18_loops_on_the_page.md`.

## Why

The owner: "the linear timeline might not make sense as qc checks sometime go to board or panels."
Measured: inside one run the runner never goes backward (0 regressions in 3,253 events). The loops are
(a) a later step re-running an earlier step's scripts inside its own wall (08 redraws 07's grids;
11 calls 09's retakes and 10's assemble) and (b) relaunches that re-enter an earlier step -- 6.2 per
published WotW episode, 11 -> 09 / 11 -> 06 in about half. Rework is a median +15 % (0-65 %).

## Decision

Display (board code only):
- D1 Round marks that name who did the work ("08: regrid x2 of 07's grids") and an attempts strip
  for relaunches; loop time billed by timing.jsonl `clock=` name. No arrows.
- D2 The ETA: p50 = the median chain x (1 + measured rework share); p80 from past episodes' actual
  rework; the remaining caps as the ceiling under the 6 h clock; firm / rough; a real-finish line only
  while a park is open.
- D3 A work-item x stage grid (grid/shot x board/panel/take) for 07-09, clean rows collapsed; the main
  body once it matches 3 replayed episodes. 07 and 08 shown as one board lane.

Pipeline (each replayed on WotW ep01-03 + a Jekyll episode before wiring; tests first; $0):
- P1 The free cell/grid/camera lints run in step 06, before any grid is drawn.
- P2 The panel eye caches its verdict by panel bytes; unchanged panels are not re-judged.
- P3 QC records its failing rows by kind; a replay then decides the 768 cut gate as its own go/no-go.

Not done: a runner merge of 07+08 (ids, redo orders and judge signatures depend on them), arrows,
Monte Carlo (9 finished episodes), new retake-in-first-pass work (already built,
step_09_shoot.py:236).
