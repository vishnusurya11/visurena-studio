# Jekyll HEL ep01 — DQ coverage audit (2026-10-14)

Episode: `library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01`,
master `cut/master_iter1.mp4`. Owner: *"I think you skipped DQ checks. The little walk is weird."*

Sources read: `takes/r2v/T??.dq.json`, `T??.content.json`, `eye_*.json`, `ladder.json`, `stills.json`,
`storyboard/panel_dq.json`, `panel_content.json`, `eye_884024ad.json`, `timing.jsonl`, `clock.jsonl`,
`drive.jsonl`, `drive_run01.log`, `learnings.jsonl`, `takes/work/dead_cuts.json`, `qc_r2v.json`,
`audit/rows.jsonl` of the book.

## The clock

Run spans (`clock.jsonl`, union): 1.37 h by 02:59 (plan + 13 record relaunches), 3.22 h after round 0
(04:55), 4.98 h after the third take ladder (07:14), **5.46 h** at the end (07:58). The 5 h ceiling
crossed about one minute into the last run (07:30). In that run take_dq re-measured all 23 takes
(548 s), take_content was a cache hit (11 s), take_eye ran, QC ran with `--ceiling-spent` (403 s, it
measured), master eye ran (470 s).

**There's no learning row with `action: reserve`, and no budget `terminal`.** The downstream reserve
never refused a rung, and no check was cut for time in this episode. The terminals came from ladders
that ran out of rungs, from the repeated-fault rule, and from relaxations built into the code.

The rule was still wrong, and it would have cut checks one run later. Past 5 h, `step_09.dq_flags`
passed `--ceiling-spent`, and `take_dq.cached(any_code=True)` then served the old verdict under any
measuring code. `step_11.qc_report` also kept a passing QC under older QC code. At 5.15 h ep01 still
had 51 min under 6 h, with 32 min owed downstream. A new check (G-GAIT below) would never have read
the takes. **Fixed** (`Budget.checks_cut`, below).

## Coverage by check

| check | ran on | outcome | skipped / downgraded, and why |
|---|---|---|---|
| panel DQ (`panel_dq`) | 23/23 panels | fail shot_10 (1 face for 2 planned) | none skipped |
| panel content (VLM, J-rules) | 23/23, then 3-6 and 10 re-read after each redraw | fail shot_03 (posture), shot_10 (missing) | shot_03's fault was **false**: "a pool of gaslight *lying*" asked the walking man to lie (fixed later in 880f16d). The cached refusal is never re-read. 8 look advisories (hat or top off the staged look) are log-only |
| panel eye (EYE_PANELS) | 3 reads | **keep_best**, 11 faults | the ladder ran out (redraw_grid_seed, reprose). It was not time: both rungs were paid from headroom. Two of its three rounds chased the false shot_03 posture fault on the walk shots 3-6. shot_10 (a cast member missing) shipped. G-FRAME and place-mirror are advisory by design |
| take DQ: freeze / frozen-at-start / jump / foreign / letterbox | 23/23 | pass | none |
| take DQ: frozen-whole (stillness) | 23/23 | pass | **drawn-look relaxation** (9ea1304: HARD only past `DRAWN_RUN` 2.5 s; 85ef81c: a speaking dialogue take is never HARD-still). Under the house rule these fail: T01 82 % static (run 4.08 s, failed 4 rounds, then exempted as speaking), T02 75 %, T19 92 % (2.04 s), T20 74 % (2.25 s) |
| take DQ: zoom / camera-move (G-MOVE) | 22/23 | pass | T09: camera-move and rotation are `not measured` |
| take DQ: cut-landing, coherence off-board | 23/23 | scored advisory | **panel-board advisory** by design (b637bc9). T14 off-board 0.85, T08 0.56, T10 0.58 |
| take DQ: last-vs-cell | 23/23 | advisory | HARD only where an END cell was drawn, and `--no-ends` draws none. So it's advisory on every take (T03 0.39, T10 0.26) |
| take DQ: face-at-end | 23/23 | 9 advisory misses | advisory by design |
| take DQ: **identity** (G4.7) | **0/23** | `not measured` on 17, "0 cast on screen" on 6 | **Skipped by design since 2026-09-25**: `take_verdict.measure` never hands the cast sheets in (3 false fails on ep10-12). Not time |
| take DQ: held / pass-through | 3/23 eligible | pass | "n/a by the plan" or "not measured" unless the plan keeps the subject in place |
| take DQ: last-vs-panel | 0/23 | `not measured` | only a cell-less board reads it, and every take has a panel board |
| take DQ: lip-sync lag | 1/4 dialogue | T02 +0 f | T01 and T14: no readable face. T17: no correlation |
| G-TAIL | 4/4 dialogue | pass | none (T14 failed once at -23.5 dB, cured by a reseed) |
| take content (VLM) | 23/23 | fail T14 "text or lettering" | the last pass was a cache hit on the same bytes. T14 ended **keep_best** (a repeated fault) |
| take eye (EYE_TAKES) | 5 rounds | keep_best, flagged | the batched ladder ran out, so it was not time |
| **gait / walk** | **did not exist** | — | nothing read a walker against his ground (below) |
| G-DEAD | master | `dead_cuts.json` cut [] | T19 (2.04 s) is under the 2.5 s wall |
| LOOK-STATE / refs LOOK verdict | — | **no verdict on disk** | `refs/verdict.json` is absent. The drive log opens "the desk says failed on refs/04; running on the owner's word" |
| QC | master | PASS | ran in full (with `--ceiling-spent`, which only governs flagging) |
| master eye (MASTER) | master | **flag**: story + identity drift (Enfield, Utterson) | spent clock: flagged, no rung |
| plan battery | 4 drafts | keep_best, 7 JUDGED faults (G-HOOK, invented counts) | ladder ran out |

## THE WALK — T03 (shot 3, "the little man stumps along the far pavement at a good walk")

Strips are in `docs/audit/2026-10-14_jekyll_ep01_hel/walk/`:
- `T03_follow_0-4s_12fps.jpg` (12 fps crops that follow the man, brightened). Use this one.
- `T03_strip_6fps.jpg`, `T03_figure_0.5-2.5s_12fps.jpg`, `T03_figure_2.5-4.5s_12fps.jpg`.
- `T04_strip_6fps.jpg`, `T04_legs_8fps.jpg`, `T04_key6.jpg`, `T05_strip_6fps.jpg`,
  `T06_strip_6fps.jpg`, `T15_strip_6fps.jpg`.

**By eye:** Hyde faces the camera, square-on, while he travels sideways to the right along the
pavement. His legs patter in tiny steps, and his torso and hat ride level, as if on a rail. It's a
crab-wise mince: the legs cycle, the body glides, and the feet must slide back over the cobbles on
every step. From about 5.5 s he walks out of frame right, and the last 2.2 s of the 8.0 s shot is an
empty street.

**Measured** (G-GAIT, `studio/gait.py`: CPU person box, Farneback flow, ground from the bands beside
the feet):
- **3.94 steps/s.** A human walk is about 1.6-2.2.
- **0.106 body heights of ground a second.**
- **0.027 heights a step.** A planted foot crosses about the gap between the feet, and the
  owner-liked WotW walkers cross 0.052 or more.

**Why nothing caught it:**
- frozen-whole read 14 % static, because the frame is alive.
- G-MOVE read 1.00x, because the camera did what the plan said.
- `held` and `pass-through` only read a person the plan keeps in place.
- The eyes read 3 still frames, and a still frame can't show a gait.
- The panel gate's posture read on shot_03 was hijacked by the false "lying" fault.
- No row anywhere compared a walker's steps with the ground he crosses.

The drawn-look advisories had nothing to do with it: none of them reads gait.

The other walker takes:
- T05 (girl running) and T06 (the collision) walk: 1.71 steps/s at 0.244 heights, and 1.10 at 0.157.
- T10 walks: 0.75 steps/s.
- T04 (Hyde walking toward the camera) and T15 are unmeasured, because the feet are out of the picture.

## Fixes (test-first)

1. **A check is cut only for the reserve** (`studio/run_budget.py` `Budget.checks_cut`;
   `step_09_shoot.dq_flags` and `step_11_qc.qc_report`).
   - Past the 5 h ceiling, the take DQ re-measure (priced 550 s) and the QC re-measure (420 s) still
     run while `leaves_reserve` holds under the 6 h limit.
   - They are cut only when running them would eat the time the firsts downstream still owe.
   - A check of 60 s or less is never cut.
   - Rungs keep the old rule: the ceiling closes them.
   - Tests: `tests/test_a_check_is_cut_only_for_the_reserve.py`.
2. **G-GAIT** (`studio/gait.py`, wired into `scripts/episode/take_dq.py` as the HARD `gait` row).
   - It runs only when the plan asks a subject to walk or run. "travelling two strides at a walking
     pace" is the camera, not a walker.
   - It FAILs a shuffle: cadence of 3.0 steps/s or more AND a step under 0.045 heights.
   - Unmeasured means one of these: fewer than 2 s with the feet in frame, a walk toward or away from
     the camera, or no step rhythm.
   - It's part of `MEASURES`, so every take is measured again.
   - Tests: `tests/test_gait_shuffle.py`, `tests/test_the_take_gate_reads_the_gait.py`.
   - Replay (`gait_replay.jsonl`, over 91 walker takes):
     - Coverage: 20 measurable, 71 unmeasured (feet out of the picture 37, no rhythm 31, depth 3).
     - **Fires on Jekyll T03 only.**
     - No fires on WotW ep01-27 or Scarlet ep01-14.
     - Nearest shipped non-fire: WotW ep06 T23 at 4.04 steps/s and 0.048 heights.
     - Owner-liked WotW ep03 T07: 3.1 steps/s at 0.052.
     - One positive, so the wall is thin. Read it as a first calibration.
3. **Drawn-look advisories (c):** none of them would have caught the walk, so none is bound here.
   The frozen-whole relaxations are listed above for the owner's ruling (T01, T19, T20).

## The ep01 takes to redo

| take | shot | the check it fails | note |
|---|---|---|---|
| **T03** | 3 | **G-GAIT shuffle** (HARD, new) | the little walk. The retake cure is the plan's gait verb: "stumps along" became a mince. Ask for "walks briskly in profile, left to right, a long stride", and keep the feet in the picture |
| **T14** | 14 | take content: text or lettering (HARD) | shipped keep_best on a repeated fault |
| T01 | 1 | frozen-whole 82 %, run 4.08 s | HARD under the house rule; passed only through the drawn + speaking exemption (85ef81c). Retake if the owner sides with the house rule |
| (panel) shot_10 | 10 | panel content and DQ: one figure for two named | the take T10 inherits it. It shipped through the panel keep_best. Redraw with the cast-continuity shots |
| (master) | — | identity drift: Enfield, Utterson | the cast-continuity agent's scope |
