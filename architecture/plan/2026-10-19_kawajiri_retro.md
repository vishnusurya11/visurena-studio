# 2026-10-19 -- The Jekyll Kawajiri ep01 retro (tracker)

Status: **BUILT 2026-10-19** (16 packages; 15 code commits, then this docs commit). Decision:
`architecture/decisions/2026-10-19_kawajiri_retro.md` (D1-D22, for veto). Plan:
`docs/audit/2026-10-19_kawajiri_retro/BUILD_PLAN.md` (outside git). Open items at the bottom.

## Packages, in rank order (one checkbox per commit)

- [x] P07 warp gate truth + face-refine selection -- 41fba62
- [x] P05 panel eye: proven cache, deadline, orphan limb -- cc5a631
- [x] P04 storyboard: solid figures under haze, a repaired anchor keeps its siblings -- c152d1b
- [x] P08 take ladder: a round is a change of bytes, cure rates, settled marks -- 79b8049
- [x] P03 prompt builder: crowd channels, night light, first-render wall across launches -- b83eac4
- [x] P01 plan ladder: real rows, honest climbs, re-sign over carried rows -- 2f1ef00
- [x] P11 voice: lines wall, phoneme-equal ear, short-line register -- 37eefbb
- [x] P06 content DQ: panel-bound crowd, K9 shape keys, the E1 eval set -- 5616782
- [x] P13 autopilot: no false parks, own logs, handover, engine health, GPU ledger -- 9dd9ffb, 17b7ae9, 222be3b
- [x] P14 device: VRAM-first router, claim liveness, family free, step 03 -- dd1e163
- [x] P02 plan cures + rulers: lock_two_shot, grammar holds, G-CROWD-ORPHAN, G-LIMB, downstream replay -- b2782b4
- [x] P12 clock ledger: heartbeat, locked attempts, owner-order allowance, family free in the runner -- 6a81488
- [x] P09 ship + assemble: per-take settled, flagged_takes.json, encoder record -- f2460f2
- [x] P10 master + QC: no-op recut, frame invariant, av3 pace, eye cache -- eb35ea6, 311bf8e, 20cfd0d, 8d9366d, 1d6f5f8, a47f81f
- [x] P15 tracking card: history kept, owed units, debt line -- fdf836d, 231bed2
- [x] P16 skill, agents, decisions, architecture page, generated tables, LESSONS split, doc_sync -- this commit

## Owed

- [ ] GPU-window evals: P04 solid-figure A/B; P06 local E1 VL replay (then flip BODY_REFUSES by hand);
      P07 T18 refine A/B; P10 NVENC vs x264 QC agreement; P14 step-03 54 s vs 285 s replay.
- [ ] Owner labels for T07, T10, T16, T20, T21, T24 eye patches (re-arms hard Se only at >= 80 %).
- [ ] Wiring: the per-draw best-draw runner (P08); clone evidence `t` seconds in take_eye (P08);
      `heard_on_master` caller in qc.py (P11/P10); 'charged | wall | dead' finish line (P12/P13);
      the dark-budget caller (P12); `comfy.row_deadline` around runner rows (P14/P12);
      `master_ladder` returning `RungResult` (P10); the PANEL_AHEAD argument (P03).
- [ ] Late findings: the QC edit gate reads av3 hqdn3d x4 pixels as off/held (7/28); the GPU whisper
      worker `[Errno 22]`.
- [ ] Future: the facenet / EasyOCR torch worker; the one event stream (C1, C2, C5) -- D21.

## Log

- 2026-10-18 23:12 PDT: ep01 master delivered; autopilot paused at 23:11; the retro's 18 areas debated.
- 2026-10-19 (overnight): 15 code packages built in parallel in the one checkout, each test-first,
  each committed by explicit path.
- 2026-10-19: P16 docs commit -- retired sentences rewritten, generated cap / algorithm / clock
  tables, "Operating a live run", LESSONS index + archive with the 13 failures, doc_sync, the page,
  this tracker, DECISIONS D1-D22. The autopilot stays paused until the owner resumes it.
