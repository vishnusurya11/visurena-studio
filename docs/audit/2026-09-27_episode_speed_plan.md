# Episode speed plan: 10-12 h to 4 h, with no DQ loss

2026-09-27. Owner: "ideal time is 4 hours for an episode ... time each step, see what takes longer, find ways to fix it."
Five read-only agents (VLM reads, GPU pipeline, right-first-time, runner mechanics, DQ guardian) proposed, then each critiqued the other four.
Their files are kept in the session scratchpad: `speed/*.md` and `speed/critique_*.md`.

## Where the time went (measured)

| | ep12 (9.8 h) | ep13 (12.1 h at step 09) |
|---|---|---|
| VLM panel reads (`panel_content`) | 45 min | **430 min** (28 full passes of 25 panels) |
| Panel eye reads (not in timing.jsonl) | -- | **~300 min** (26 passes x 11.8 min) |
| Grid draws | 17 min | 151 min (107 draws for 25 panels) |
| Takes render | 193 min | 129 min (25 takes) |
| Take VLM reads (`take_content`) | 177 min (4 full re-reads of unchanged takes) | running |
| take_dq (CPU; GPU idle meanwhile) | 51 min | 24 min |
| qc | 51 min (7 runs) | -- |
| Title card (an H3 render) | 17 min | -- |

- Four of today's five ep13 runs (235 min) only re-climbed step 08 and ended on the same flags.
- No EYE_PANELS rung inside a climb ever lowered the fault count (23->24, 20->20, 17->17, 16->16, 4->4). The drops came only from plan, prompt and judge fixes between runs (16dec05, 9cb4609).

## Root mechanisms

1. **A VLM read costs ~27.5 s, and every change re-reads everything.** Of that, 9.7 s reloads the 16 GB model each call (`keep_model_loaded: false`) and 2.6 s waits on the 5 s poll. Freshness is judged per file (`panel_dq.py:332-352`, `step_09_shoot.py:129-130`), so one changed panel re-reads all 25.
2. **Models live on a 5400-rpm HDD (D:).** The working set is ~77 GB against 64 GB RAM. Measured cold loads: H3 +277 s, Qwen-Image ~140 s per rung, VL 200-470 s.
3. **The panel ladder climbs on faults a redraw cannot cure** (framing, posture), with CAP=2 per run. It also never stops after a rung that changed nothing.
4. **Budget mechanics:**
   - Rungs are priced at 102 s against ~1900 s measured (`panel_ladder.py:31`), so a step defers mid-climb, after the work is spent.
   - A step 08 overrun is charged to step 09, which then refuses.
   - The ceiling is per run, not per episode (`episode_run.py:31`).
   - A resume re-climbs a step that already ended in a signed terminal.
5. **7 of ep13's 10 first-pass take failures were predictable from the move.** Holds, rack_focus and tilt_down read 80-100 % static. H3 ignores them (`camera_catalog.md:209-211`), yet G-MOVES counts them toward its 8-distinct rule.

## The plan, in order of minutes saved per hour of work (critique consensus)

| # | Fix | Saves / episode | Work | DQ risk and the condition that keeps it zero |
|---|---|---|---|---|
| 1 | Move all ~77 GB of model weights to the C: NVMe (paths are symlinks) | 30-85 min | 1 h, ComfyUI idle | none: same bytes |
| 2 | Poll ComfyUI text jobs every 0.5 s, not 5 s | 11-20 min | 0.5 h | none |
| 3 | Runner bundle: episode spend persisted across runs; rungs priced from measured cost; step 08's overrun never refuses step 09; DEFER before spending, never sign a terminal for budget | 50-150 min per resume | 3 h | keep a reserved 9-min MASTER retake; never sign at attempt 0 |
| 4 | EYE_PANELS climbs only on redraw-curable faults (blur, stacked, clones, people, missing, banned, text) and stops after a rung whose fault set is unchanged; framing/posture faults go to a **pre-draw lint** (close prose + binding, as 9cb4609) and stay blocking flags for the director | 45-120 min | 3 h | finding 50: 7/9 framing faults were real, so they are not waved through; they are cured upstream and still reviewed |
| 5 | VLM raw-answer cache keyed on staged PNG bytes + prompt + seed + token limit + workflow JSON + model + node version; the judging re-runs in code every time; an unreadable answer is never cached | 60-100 min (normal ep), ~250 on an ep13-shaped one | 4.5 h | judge/plan fixes still apply because only the raw answer is cached |
| 6 | Load the VL model once per batch; the batch ends with an unload before any H3 job | ~57 min | 2.5 h | none (logged failure: VL beside H3 took 6:52 to load) |
| 7 | Skip a MASTER `recut` when its inputs are unchanged; faces/identity faults go straight to `retake_shot` | ~18 min | 1 h | a DQ gain: the retake gets its budget back (finding 38) |
| 8 | G-STILL plan gate: refuse the moves H3 ignores (rack_focus, tilt_down, angle holds with no travel verb, close + push) and name the ladder's substitute; the take ladder skips its seed rung on them | 35-55 min | 3.5 h | the frozen-whole HARD gate stays |
| 9 | take_content reads only takes that passed take_dq (every take in the cut still needs a content verdict; qc already refuses unjudged takes) | ~14 min | 1 h | qc.py:207,294 stays the wall |
| 10 | Stream take_dq alongside the renders; queue a failed take's retake while H3 is loaded | ~40 min | 8 h | the same gates, earlier |

Refused (by the critiques):
- 3 seeds per failing grid: no rung ever lowered a count.
- Rendering the title while the GPU is idle: another H3 model, two 21 GB swaps.
- Auto-relaunch after DEFERRED, before #3: it loops the useless re-climbs.
- Fewer frames per take read, a smaller VLM before an owner-labelled calibration, and caching verdicts by filename/mtime.

## The 4-hour budget (runner mechanics, revised with the critiques)

| Step | Minutes |
|---|---|
| 01-06 (bind, plan battery + critic, places, lines, timeline, prompts) | 35 |
| 07 board (25 grids at ~20 s warm) | 10 |
| 08 panels (one full read, one climb at most) | 20 |
| 09 takes (render ~124 + one retake round) | 150 |
| 10 edit (with the title render) | 20 |
| 11 qc + 12 deliver + MASTER eye | 25 |
| **total** | **260** |

The table closes at ~4 h only with #8, because the first-pass take failures (10 of 25 on ep13) must fall to about 5.
It also needs the per-episode ceiling to end an overrun at a terminal rung, not a relaunch.

## What never gets cut

- The first full read of every new picture.
- 3 frames per take.
- The frozen-whole, lip-sync, cut/jump, face and content gates. All caught real ep13 faults.
- The PLAN battery, qc rows, the master eye and speaker_check.
- The publish lock: `scripts/publish/youtube_upload.py:161` and `youtube_privacy.py:64` call `publish_lock.stops()`.
- The director's watch-and-listen sign-off.
