# Jekyll ep07 retro: final (2026-11-10)

Owner: "do a retro on episode 7 and please fix the skills and framework". Medium scope: lead + 4 Sonnet experts + 1 Opus skeptic. Fixes built now; GPU proofs after the PCIe fix.

## What went wrong on ep07
- 20 drive runs over 11 days; 7.08 h machine clock against a 6 h budget.
- It shipped public on 2026-11-10 (https://youtu.be/ZSbWJVFDeGE) with 4 flagged takes.

| # | Fault | Cost | Root rule |
|---|---|---|---|
| 1 | G-WHO / clone refusals on Utterson+Enfield two-shots, runs 02-08 | 8 runs | G-WHO was 0/7 on ep07; the two men's sheets read alike (out/B) |
| 2 | One master frame (0.5 s) refused shot_07 for runs 10, 13-15, 17 | 84 min, 5 runs | the block had no second look, and the refusal never printed the line (brick 17) |
| 3 | "Shuffle 4.0 steps/s" on T00/T19/T21; 6 re-rolls each; shipped flagged | rolls; a false flag | stride-2 aliasing of H3's 8 Hz render pulse (brick 18) |
| 4 | Retakes were seed re-rolls with identical prompts (T05 warp, T21 lettering) | rolls | warp has no plan rung; lettering on a clean panel has no cure; the writer invited signs |
| 5 | The expired token parked as `clock_loop`; the finished episode sat 6 days | 6 days wall | `clock_loop` was tested before the table; "told" proved no delivery |
| 6 | `redo 09` placed 3 times, every take cached | 3 relaunches | cure orders had no memory of the refusal they left |
| 7 | A hand edit ("slowly") crashed step 01 after launch | 2 runs | no plan check at preflight |
| 8 | take_dq serial passes on 2 of 32 cores | ~27-41 min | the lane cap also applied when the GPU was idle |

## Built (test-first, CPU only)
| Spec | Change | Files |
|---|---|---|
| S1 | The master blocks a per-frame people line only on 2+ frames. A lone frame gets 3 more reads in the same pass; under 3 frames read fails closed. The REFUSED line prints line, time and k of n. | studio/ship_block.py, studio/master_ladder.py, studio/judges/master_eye.py |
| S2 | `named_park` outranks `clock_loop`; the park reads `clock_loop: <reason>`. | studio/autopilot.py |
| S3 | `nudge_parked`: FINISHED, NOT PUBLISHED every 6 h. `notify` returns whether it sent; token sends are logged with `sent`. | scripts/episode/autopilot.py, scripts/episode/drive.py, studio/autopilot.py |
| S4 | `refusal_sig` + `cure_spent` park `cure_no_change`. | studio/autopilot.py, scripts/episode/autopilot.py |
| S5 | `plan_lines` at preflight; the TABLE parks `plan_contract`. | scripts/episode/drive.py, studio/autopilot.py |
| S6 | `judge_threads`: a serial pass uses half the cores. | scripts/episode/take_dq.py |
| S7 | `gait.alias` + `frame_rows`; take_dq gate v2. Replayed on the shipped T00/T19/T21: 3 of 3 come back alias (replay/s7_gait_alias_ep07.jsonl). | studio/gait.py |
| S8 | `gait_verb` is idempotent. | studio/gait.py |

Tests:
- New files:
  - tests/test_master_people_block_needs_a_second_frame.py
  - test_master_eye_takes_a_second_look.py
  - test_a_named_park_outranks_clock_loop.py
  - test_a_finished_unpublished_episode_is_told_until_acted_on.py
  - test_the_tick_tells_a_finished_parked_episode.py
  - test_drive_notify_says_whether_it_sent.py
  - test_a_cure_that_changed_nothing_is_not_placed_twice.py
  - test_a_launch_reads_the_plan_before_a_second_is_spent.py
  - test_take_dq_serial_pass_uses_half_the_cores.py
  - test_gait_alias_is_confirmed_at_the_native_rate.py
- One test added to test_gait_is_a_verb.py.
- Fixture tests/fixtures/jekyll_ep07_plan.json.

Skill:
- LESSONS.md: bricks 17 and 18, plus appendices to bricks 2 and 8.
- LESSONS_ARCHIVE.md: section "Jekyll ep07 retro".
- GATES.md: the G-GAIT row, a new G-PEOPLE-at-master row, and the clock backstop paragraph.
- OPERATOR.md: 5 symptom rows.

docs/DECISIONS.md: one line, for veto.

## Not built (skeptic: rejected or deferred), reasons in out/E_skeptic.md
- **Rejected:**
  - counting clock_loop stops since a retry;
  - a plan-sha refusal;
  - 24 fps gait with today's walls;
  - a crowd ceiling taken from the plan alone (needs a CPU replay first);
  - lifting CONFIRM to the take hair line;
  - `same_refusal`.
- **Built in a second commit:**
  - S9: take_eye clone pairs cached on take bytes + clone-code hash (`T<NN>.clones.json`);
  - S10: the who-read stops once CONFIRM frames agree (re-pin only: pass/fail unchanged);
  - S11: lettering on a clean panel earns one seed, with a (0, 0) rate row.
  - 3926 affected tests pass.

## GPU proofs owed (after the PCIe fix; queue in this order)
1. **S1 master-eye replay.** No render: judge-only through `master_eye.measures` + `verdict_of` + `ship_block.master_blocks`.
   - ep07's pre-ship cut must flag, not refuse.
   - ep05's deleted master a2d09fc0 (if its bytes exist) must still refuse at shot_18 and s03/s15.
   - ep04 403e67cf shot_18 must still refuse.
   - Any miss rejects S1.
2. **T05 warp plan rung.** `takes_r2v.py --retake=5` with the head turn removed. Pass: S <= 2.5 and Se < 3.
3. **T21 retake** with "blank fascias, no signs". Pass: text false.
4. **Co-cast sheet distinguishability.**
   - Must refuse: ep03's pair, the pre-redraw ep07 Enfield/Utterson, ep05 Jekyll/Utterson.
   - Must pass: 5 WotW/Scarlet pairs.

## Publishable (flagged for the paper list)
The gait alias is a short note or benchmark on measuring motion in generated video. Its subject: stride-2 optical-flow cadence against the 3-frame render pulses of video diffusion VAEs. The 5-take table is in out/E_skeptic.md section 0.
