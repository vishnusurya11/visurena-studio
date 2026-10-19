# 2026-10-18 -- A run that loops, shown as it is (tracker)

Status: **IN PROGRESS**. Decision: `architecture/decisions/2026-10-18_loops_on_the_page.md`.
Board items build now (the running episode never imports board code); pipeline items wait for the
running Jekyll ep01 to finish (they edit runner files); commits land after ep01 (owner's rule: no
commit restarts a live run).

## Display
- [x] D2 loop-aware ETA: `eta.finished_units` (last 9 delivered), `rework_shares` (each step's longest
      pair is the pass), `rework_band`, `with_rework`, `firmness`; the range reads "firm|rough · rework +11 %
      (9 episodes)". Measured live: ep01 "finish 8:45 pm, firm, +11 %". Park line: not built (the stop
      sentence already says it).
- [x] D1 `studio/command_center/loops.py`: `borrowed` (an earlier step's work inside a later step's
      span, by timing.jsonl names), `attempts` (runs of this make), one loops line under the rail.
      Live ep01: "run 10 of 10 · entered at 01 after run 9 stopped after 08 · 08 re-ran 07's grids x1".
- [x] D3 `studio/command_center/workgrid.py` (one reader, pure cells, clean rows folded), shot order;
      replayed on WotW ep19-21 (regrids r3/r5, takes r2-r4 with their causes; a renamed grid read
      'waiting' until a cut panel counted as drawn).

## Pipeline (built when ep01's run stopped on an assemble refusal and the autopilot waited on the tree)
- [x] P1 (replayed: grids.py --prompts clean on WotW ep01-03 + Jekyll ep01, also with the plan-only
      layout step 06 sees; ~1 s each) step 06 launches `grids.py --prompts` (the same lint as step 07's wall, dry, no GPU) and logs
      `camera_lint` faults on the writer's heads as advisories (uncalibrated there; never a wall). The
      cell gates already run in plan_check at 02/03/05 -- no change. Tests: test_episode_steps_run_alone.
- [x] P2 (unreadable reads never kept; refs keyed by size+mtime, the panel by bytes) `panel_eye.read_panel` cached by (panel bytes, shot size/faces/frame/at_rest, setup words, ref
      bytes, VERSION, SCORED_BOXES) in storyboard/eye_cache/; stored rows, repeats, place stay live.
      Tests: test_the_panel_eye_reads_a_panel_once.
- [x] P3 (the autopilot's qc_fail patterns match on the unchanged prefix) the step 11 refusal names `qc.failed_rows` (step_11_qc.py is outside QC_MEASURES: no stored
      report is re-measured). Tests: test_a_qc_refusal_names_its_rows. Then the cut-gate replay.

## Log
- 2026-10-18 PDT: debate (10 experts, 2 rounds), owner go on all six.
