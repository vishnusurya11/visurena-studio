# D: where ep07's 7.08 h went, and what brings a typical episode under 6 h

Paths are repo-relative. EP = library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep07.
M = MEASURED (read off ep07 files or code). D = DERIVED (arithmetic or an estimate; the assumption is named).
I used throwaway Python over EP/timing.jsonl, clock.jsonl, drive.jsonl and a streamed filter of library/vlm_calls.jsonl.

## 0. Headline

- take_dq's 179.6 min is NOT 3 h on the critical path. 124.9 min of it ran under a GPU render, in the CPU lane (M).
  Only 54.7 min stood exposed, with the GPU idle (M). Making take_dq free would save at most 54.7 min.
- The 2026-11-09 efficiency fixes #1 (frame-3 skip) and #3 (model kept) do not apply to production take_dq.
  Production take_dq reads no VL model. The anime POC file of the same name is the VL content judge (section 2).
  Production's VL step, take_content, already holds `comfy.model_kept()` and a bytes-keyed cache (section 3).
- The biggest avoidable block is the refusal relaunch loop: runs 13-17 (G-PEOPLE false refusal at shot_07) cost 84.2 min of drive clock (M).
- Four fixes, about 100 min together (D), project ep07 to about 5.3 h (section 6).

## 1. Breakdown table (minutes, M unless marked)

Source: EP/manifest.json timing.by_stage, EP/timing.jsonl, EP/clock.jsonl. Rows are net of nested rows (studio/episode_clock.py:110-122, `timed`).
The sum is 424.7 min = 7.08 h. The 20 drive runs sum to 453.2 min (clock.jsonl): kills and gaps are counted there.

| item | min | critical path? | note |
|---|---|---|---|
| take_render span (GPU) | 150.5 | yes | 14 `take_render` detail rows in EP/timing.jsonl; about 107 take renders |
| take_dq, hidden under a render | 124.9 | no | CPU lane beside the GPU (studio/take_overlap.py:1-26) |
| take_dq, exposed | 54.7 | yes, GPU idle | 36 min of it is six `--attempts` passes of 2-10 min each |
| takes (net of nested rows) | 26.6 | yes | remainder of the step-09 render wall |
| take_content (VL) | 48.2 | yes | 517 reads inside its stage windows |
| take_eye | 11.0 | yes | 14 passes of 38-65 s |
| grids | 45.3 | yes | 72 rows; run 9 lost 18.7 min to EngineLost (EVIDENCE.md:26) |
| plan | 23.7 | yes | one 1420 s row in run 1 |
| panel_eye + panel_content | 34.8 | yes | |
| master_eye | 16.4 | yes | 5 passes: 575, 35, 51, 265, 57 s |
| bed | 7.6 | yes | 5 acestep builds, ~80 s each (one 123 s) |
| rest | ~46 | | lines, places, qc, upscale, assemble and the like |

How the 125 / 55 split was measured: for each of the 97 take_dq rows I subtracted its overlap with the `take_render` spans
(those rows carry start and end times).

Step 09 in total was 268 min of exclusive time over the 20 runs. attempts.json `wall.09` = 15766 s = 262.8 min is that same step, entered 12 times.
It is not a refusal loop. It is step 09 itself: 150.5 min of render span plus the checks after the renders.
The refusals sit at steps 10 and 11 (drive.jsonl `step` field).

## 2. Why take_dq costs what it costs (question 1)

Production take DQ is `scripts/episode/take_dq.py` plus `studio/take_verdict.py`. It has no VL call:
- `measure_attempt` (take_dq.py:628-654) does one ffmpeg decode (`take_lock.frames`), then `tv.measure`, audio, mouth, gait (yolo on CPU), warp (face detector) and a coherence decode.
- The judges load once per process, on the first cache miss (`Judges.get`, take_dq.py:371-393). They are capped to 2 threads
  (`cap_threads(lane_threads())`, lane_threads at take_dq.py:743-750). The cap is applied even when the pass is NOT `--cpu-only`, i.e. when no render runs.
- The cache is keyed on the take's bytes and the gate version (`cached`, take_dq.py:718-734). It works: 16 cache-hit rows cost 22.9 s in all (M).

Cost per call, fitted on 81 non-cache rows (M): seconds = -41 + 139 x takes. So there is no fixed per-call cost; the cost is per take.
- Plain `--cpu-only` rows: 86.9 s per take (72 rows, 86 takes).
- `--attempts` rows: 218.7 s per take (9 rows, 15 takes), about 2.5 attempt files per take.
- Takes measured: 103 take-measures on 26 takes against about 107 renders. That is one measure per new render, not a re-judge of unchanged bytes.
- Per roll: one decode plus about 5 measures. I did not profile the split (it needs a run).

The exposed 54.7 min: the lane has 2 threads on a 32-logical-CPU machine (os.cpu_count() = 32). That is right while the GPU renders.
But the six `--attempts` passes and the serial window also run at 2 threads while the GPU waits.
Examples (M): `0 19 --cpu-only --attempts` 9.8 min exposed; `12 19 22` 10.0; `0` 7.5; `2 11 16 17` 7.6 of 9.8.

Do the POC fixes port?
- #1, frame-3 skip (docs/audit/2026-10-31_anime_model_poc/take_dq.py:115-134, `decided`): that file is the CONFIRM=2-of-3 who-fault judge.
  Production's equivalent is `take_content_check.who_faults_for` and `confirmed` (take_content_check.py:114-165, CONFIRM = 2).
  It reads all 3 who frames unconditionally. The main and twin reads cannot skip (their rows are not confirm-gated).
  production take_dq has no third frame to skip.
- #3, `model_kept` around re-judges: production already has it. take_content_check.py:316 wraps the miss batch,
  studio/judges/panel_eye.py:621 wraps about 30 reads, and `model_kept` is studio/comfy.py:491. take_dq holds no VL model, so it needs none.
- On ep07's counts they save: #1 at most 3 min (fix 4 below), #3 nothing new.

## 3. Group-by-model: does the chain reload the VL model? (question 3)

library/vlm_calls.jsonl has no episode field and mixes sessions: 5244 rows from 10-30 to 11-09, 1160 VL min in all.
I attributed rows to ep07 by intersecting their timestamps with EP/timing.jsonl stage windows (M, 913 rows):

| stage | reads | VL min | median read | reads over 15 s (a load) |
|---|---|---|---|---|
| take_content | 517 | 44.8 | 5.4 s | 11 |
| master_eye | 112 | 14.9 | 7.6 s | 4 |
| panel_eye | 150 | 13.3 | 7.6 s | 0 |
| panel_content | 130 | 12.6 | 5.9 s | 4 |

Load excess (read time over 6 s) is about 3.8 min in all (M). Group-by-model is already done inside each VL stage.
What remains is re-entry on every relaunch, not a reload per read.
take_content full passes cost 546-689 s four times (runs 2, 4, 10, 15); unchanged reruns cost 0.6 s (cache hit, EP/timing.jsonl).
take_eye does NOT cache: unchanged reruns still cost 38-43 s each (11-03 to 11-04 rows).

## 4. wall.09 and the relaunch loop (question 2)

Per drive run: clock.jsonl minutes, the stages that ran in the run window (timing.jsonl), the refusal (drive.jsonl).

| runs | clock min | what ran | verdict |
|---|---|---|---|
| 2 | 139.2 | first 26 renders, take_dq 87.6, content 13.7, grids, eyes; refused at 10 (G-DEAD) | real work |
| 3, 5, 6, 7, 8 | 14.4 | cached re-entry, then the same G-DEAD refusal | loop (cause fixed: 35b7e603, 348c7390) |
| 4 | 72.6 | retake rounds, render span 34.8, dq 34.5; refused at 10 | mostly real |
| 9 | 19.4 | grids 18.7, EngineLost | crash |
| 10 | 60.8 | master ladder, dq 21.4; refused at 11 (G-PEOPLE) | real, then the false refusal starts |
| 13, 14, 16, 17 | 38.8 | cached re-entry, one re-render, bed, mix, qc, master_eye; same refusal | loop, no input changed |
| 15 | 45.4 | render span 24.1, dq 22.9, content 9.3 | one more retake round, same refusal |
| 18-20 | 19.2 | upload, token refresh | not a refusal loop |

G-PEOPLE loop, runs 13-17: 8.1 + 9.7 + 45.4 + 11.0 + 10.0 = **84.2 min (M)**. With the G-DEAD loops 3-8 added: 98.6 min.
Each relaunch in 13/14/16/17 repeats the same chain (run 14, EP/timing.jsonl): a shot_07 grid (16 s) and panel gates, one take render (116 s),
take_dq 70 s, take_content 30 s, take_eye 41 s, cut 19 s, **bed 77 s (acestep)**, mix 9 s, assemble 13 s, qc 25 s, master_eye 51 s: 8-11 min per run.
The refusal is raised in `master_ladder.flag` (studio/master_ladder.py:145-154), after the whole chain has re-run.
The cause was a one-frame hair read (EVIDENCE.md:24). `ship_block.blocks` (studio/ship_block.py:41-46) blocks on `HAIR_LINE` from one frame,
while the content judge's who-fault already needs CONFIRM = 2 frames (take_content_check.py:150-153).

Are verdicts cached by input hash? Partly.
- Yes: take_dq (take_dq.py:718), take_content (take_content_check.py:273-300), panel_eye (`cache_hits=25` in its timing notes).
- No: take_eye, master_eye, bed, mix, qc, assemble re-run on every launch. take_eye 14 x ~41 s = 11 min; bed 5 x ~80 s = 7.6 min.
- The refusal has no memory. `clock_loop` (studio/autopilot.py:437-445) fires only on a SPENT clock (at or over the 5 h ceiling) after 3 non-zero ends.
  Under the ceiling, a same-reason refusal relaunches without limit. EVIDENCE.md:30 shows the hand retries about 20 min apart.

## 5. Ranked fixes (minutes from ep07's own counts)

| rank | fix and function | saves on ep07 | status |
|---|---|---|---|
| 1 | A same-reason refusal parks instead of relaunching: `studio/autopilot.py::derive` (new `same_refusal`). Hair block needs 2 frames: `studio/ship_block.py::blocks` | 70 min (D) of the 84.2 M; one legit retake cycle (~10 min) is kept | new. The 2-frame rule exists for who (take_content_check.py:150); port it to the hair line |
| 2 | Exposed take_dq passes use the whole machine: `scripts/episode/take_dq.py::Judges.get` (cap only when `cpu_only`), or N takes in parallel | 27 min (D, 50% of the 54.7 exposed) up to 41 (75%) | new. Thread scaling is NOT measured; measure one take at 2 vs 8 threads first |
| 3 | take_eye and master_eye keyed on input bytes + prompt: `studio/judges/take_eye.py` | 4 min net (D: about 8 unchanged take_eye passes x 41 s = 5.5, less 1.5 overlapping fix 1) | new. take_content_check.py:296 `cached` is the pattern |
| 4 | Third who-frame read only when it can change the verdict: `take_content_check.py::who_faults_for` | 3 min at most (D: 517 reads; at most 1 in 9 is a third-frame who read) | built in the POC (take_dq.py:115 `decided`); needs porting only |
| 5 | Cache the bed by plan + length hash: the bed call in `scripts/episode/step_10_edit.py` | 5.6 min (D: 4 of 5 builds x ~84 s), but inside fix 1's runs, so NOT added to the total | new |
| - | G-DEAD clone refusals | 14.4 min of loop | already landed (35b7e603, 1029749f, 348c7390) |
| - | POC #1 and #3 against take_dq | 0 | they do not apply (section 2) |
| - | EngineLost during Qwen grids (run 9) | up to 18.7 min | reliability; no fix designed here |

## 6. Projected ep07 clock

| step | min |
|---|---|
| baseline, manifest total | 424.7 |
| fix 1 | -70 |
| fix 2, conservative | -27 |
| fix 3, net | -4 |
| fix 4 | -3 |
| projected | 320.7 = 5.3 h (D) |

- Fix 1 alone gives 354.7 min = 5.9 h: only just under the 360 min budget. It cures a false refusal, so it is a one-off.
- Fix 2 helps every episode. At 41 min saved the clock is about 307 min (5.1 h). If threads do not scale (0 saved) it is about 348 min (5.8 h).
- An episode with no refusal loop is about 340 min on these stage totals (424.7 - 84.2) and already under 6 h.
  Its floor is the 150 min of GPU renders and the 54.7 min of exposed checks.

## 7. Failing tests (pytest shape; each fails on today's code)

```python
# tests/test_autopilot_same_refusal_parks.py   -> studio/autopilot.py::derive / same_refusal (new)
from studio import autopilot
def test_the_same_refusal_on_the_same_inputs_twice_parks():
    row = {"event": "run", "outcome": "refused", "step": "11",
           "error": "REFUSED: G-PEOPLE ... shot_07", "inputs_sha8": "ab12cd34"}
    s = signals(drive_rows=[row, {"event": "end", "code": 1}, row, {"event": "end", "code": 1}],
                clock_spent_s=0)             # under the 5 h ceiling, where clock_loop is blind
    d = autopilot.derive(s, 7)
    assert d.state == autopilot.State.PARKED and "same_refusal" in d.reason
def test_a_refusal_after_the_inputs_changed_does_not_park():
    a = {"event": "run", "outcome": "refused", "step": "11", "error": "REFUSED: G-PEOPLE", "inputs_sha8": "aa"}
    assert not autopilot.same_refusal([a, {**a, "inputs_sha8": "bb"}])

# tests/test_ship_block_hair_needs_two_frames.py   -> studio/ship_block.py::blocks
from studio import ship_block
def test_a_hair_line_in_one_frame_does_not_block():
    fault = {"where": "shot_07", "lines": [f"frame 1 of 3: {ship_block.HAIR_LINE}"]}
    assert ship_block.blocks(fault) is False      # today True: line.endswith(HAIR_LINE)
def test_a_hair_line_in_two_frames_blocks():
    fault = {"where": "shot_07", "lines": [f"frame {i} of 3: {ship_block.HAIR_LINE}" for i in (0, 1)]}
    assert ship_block.blocks(fault) is True

# tests/test_take_dq_serial_pass_is_not_lane_capped.py   -> scripts/episode/take_dq.py::Judges.get
import sys; sys.path.insert(0, "scripts/episode")
import take_dq
def _stub(monkeypatch, seen, deferred):
    monkeypatch.setattr(take_dq, "cap_threads", lambda n: seen.append(n) or n)
    monkeypatch.setattr(take_dq, "judge_embedder", lambda cpu_only: (None, None, deferred))
    monkeypatch.setattr(take_dq, "load_vision_judges", lambda: (None, None))
    monkeypatch.setattr(take_dq, "landmarker", lambda: None)
def test_a_pass_with_no_render_running_is_not_capped_at_two(monkeypatch, tmp_path):
    seen = []; _stub(monkeypatch, seen, [])
    take_dq.Judges(tmp_path, cpu_only=False).get()
    assert seen[0] > take_dq.lane_threads({})     # today 2 == 2
def test_the_cpu_lane_stays_at_two(monkeypatch, tmp_path):
    seen = []; _stub(monkeypatch, seen, ["leak"])
    take_dq.Judges(tmp_path, cpu_only=True).get()
    assert seen == [2]

# tests/test_take_eye_verdict_cached_on_bytes.py   -> studio/judges/take_eye.py (keyed read, new)
def test_unchanged_takes_cost_no_reads(tmp_path, fake_vl):
    take_eye.judge(two_takes(tmp_path), reader=fake_vl); n = fake_vl.calls
    take_eye.judge(two_takes(tmp_path), reader=fake_vl)
    assert fake_vl.calls == n                     # today it doubles: ~41 s a rerun on ep07

# tests/test_take_content_third_who_frame_skipped.py   -> take_content_check.who_faults_for
def test_the_third_who_frame_is_not_read_when_two_agree(fake_vl):
    who_faults_for(shot_two_faces(), three_frames_two_people(), tmp, "T07", staged)  # fake_vl: same fault on frames 0, 1
    assert fake_vl.calls == 2                     # today 3
```
The take_eye and take_content tests use fake readers (CLAUDE.md: no test spends money or touches the GPU).
`signals`, `two_takes`, `fake_vl` and the shot helpers are fixtures to write; the names are placeholders.

## 8. Caveats

- vlm_calls.jsonl is shared across sessions, so section 3 attributes rows by timestamp window; a concurrent session would inflate it.
  Per-stage read minutes agree with the stage minutes (take_content 44.8 vs 48.2), so the leak is small.
- Fix 2 is the least certain number: the 50-75% is an assumption about thread scaling.
  One un-run measurement (one take at 2 vs 8 threads, CPU only) settles it.
- timing.jsonl rows are net of nested rows, so summing `seconds` double-counts nothing. A parent row's t0/t1 span DOES cover its children.
  I used the `take_render` spans for the render overlap.
- Run-window attribution (section 4) uses clock.jsonl start and end epochs. Run 18 was killed, so its time is only partly mapped.
