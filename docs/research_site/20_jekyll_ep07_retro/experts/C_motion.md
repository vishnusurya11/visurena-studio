# Expert C: motion and picture flaws that shipped (Jekyll ep07)

EP = library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep07. Read-only; CPU only (24 fps
frame-difference spectra of 8 takes; no GPU, no paid call). Evidence: EP/takes/r2v/T??.dq.json, attempts/*.graph.json (prompt
and seed of every roll), EP/takes/r2v/ladder.json, EP/attempts.json, EP/plan.json, EP/review/director_signoff.md.

## 1. The finding that matters: "4.0 steps/s" is an alias, not a gait

`studio/gait.py:184-202` reads every 2nd frame (`stride=2`, `FPS=12`, gait.py:39). `cadence` (gait.py:88-98) takes the peak of
the legs' motion spectrum inside BAND 0.7-4.5 Hz (gait.py:45). A render rhythm of one beat per 3 frames at 24 fps is 8 Hz;
sampled at 12 fps it folds to |12-8| = 4.0 Hz, inside the band. take_dq already records that rhythm as the `pulse` row
("3f x4 r 0.78" on T00, "3f x12 r 0.93" on T19, in their T*.dq.json gates); it is advisory, so nobody joined the two rows.

My check (frame-difference spectrum at 24 fps): peak at 8.0 Hz on T00 (9.4x the spectrum mean), T19 (14.7x), weaker on T21
(4.8x) and T05 (4.8x); controls T01, T02 (no pulse row failing) 2.7x. Measured gait (T*.dq.json `measures.gait`):

| take | freq | frames | travel (heights/s) | step (heights) | wall |
|---|---|---|---|---|---|
| T00 | 4.00 | 84 | 0.010 | 0.002 | 0.045 (gait.py:49) |
| T19 | 3.95 | 73 | 0.160 | 0.040 | 0.045 |
| T21 | 4.04 | 89 | 0.088 | 0.022 | 0.045 |

The same 3.9-4.1 shows in every earlier shuffle: ep01 T03 3.94 (gait.py:24), WotW ep06 T23 4.04 (gait.py:25), ep01 T01 4.1
(LESSONS_ARCHIVE.md:2212). A person walks 1.6-2.2 steps/s (LESSONS_ARCHIVE.md:1139). At 2 steps/s T19 steps 0.16/2 = 0.08
heights (above the liked floor 0.055, gait.py:50) and T21 0.044 (borderline): the gate calls a walk a shuffle because the
alias doubles the cadence and halves the step. The calibration "20 measurable, ONE fires" (gait.py:22-29) was fitted on the same
alias. Status: spectrum evidence is direct; the end-to-end re-measure at 24 fps (needs yolov10m.onnx under ComfyUI root,
CPU only) is the proof in section 7, not yet run.

T00 is a different fault under the same label: travel 0.01 heights/s, the pair does not walk (frozen-whole "82% static, run 2.75s
ADVISORY (locked on the grammar)" in T00.dq.json). Its 4.0 is the same alias over a standing pair.

## 2. Per-take table

| take | fault shipped | plan ask (EP/plan.json) | rolls and what changed (attempts/*.graph.json) | cause |
|---|---|---|---|---|
| T00 | gait 4.0, 0.002 h/step; frozen-whole 82 % advisory | shot 0: "locked-off frame; walk in over the cobbles and halt before the steps"; wide, 8 s, locked grammar; verb already in the plan now | 6 rolls, seeds 88000, 88101, 88202, 88303, 88404, 88505. fail1->2: camera head tracked->locked, and "At 00:05 the walker goes in profile, a long stride, feet in the picture" appended (gait_verb) after "halt" at 00:03. fail3->4: prompt rebuilt with place-sheet block (+1100 chars). fail4->5: identical prompt. final: only Enfield's beard line differs. | Walkers do not move on a locked wide (travel 0.01); gate reads the 8 Hz pulse as 4 Hz. The appended verb contradicts the plan's own "halt". |
| T19 | gait 3.95, 0.040 h/step | shot 19: "camera tracks beside; walk past the door toward the RIGHT"; medium | 6 rolls, seeds 88019, 88120, 88221, 88322, 88423, 88524. fail1,2 same prompt, no verb (pure seed). fail3: verb added at 00:04. fail4: place-sheet block swapped for panel first-frame. fail5 = fail4 prompt. final +41 chars. | One verb try, then seeds and re-staging. Step 0.040 is under the wall only because the cadence is doubled (section 1). |
| T21 | gait 4.04, 0.022; lettering; crowd 12 vs 11 | shot 21: "camera rises above the kerb; the two walk out along the pavement; four strollers in pairs far down the street"; full; extras 4; NO gait verb | 5 rolls, seeds 88021, 88223, 88122, 88324, 88425; all prompts 3607 chars, byte-same, none has the verb. Pure seeds. | gait never reached the router for T21 (ladder.json round 4 lists only `content`); its row came only in the final verdict, after the retake cap (section 4). |
| T05 | warp S 2.98 Se 4.61 | shot 5: medium_close over Enfield's shoulder; "Utterson speaks and turns his head toward the court entry"; 4.67 s; face 104 px (T05.dq.json tracks) | 4 rolls, seeds 88005, 88106, 88207, 88308. All four prompts identical (4828 chars). S per verdict: 3.47 (10-31), 2.76 (11-04), 2.98 (final); wall 2.5. | Seed only, three times; Jekyll ep01 seeds cured 0 of 4 on warp (take_ladder.py:92-97). Cause is the speaking head turn on a large face; the plan never changed. |

"Rolls" = archived draws in takes/r2v/attempts plus the kept take. Not every roll was a cure: ladder.json holds 4 rounds,
attempts.json counts `retakes rounds 2`, run 04 prints `CAP retakes: 2/2 rounds, 171:01, kept best`. The Nov 3 20:44-21:02 file
times of all four takes fall in run 09/10 after `regrid` (attempts.json): refreshed-panel re-renders (inference from file times
and logs; no ladder round names them).

## 3. T21: lettering and the crowd

- Crowd: `take_content.crowd_fault` (take_content.py:115-128): base = max(panel_people, declared). declared = 2 faces + 4 extras
  (+ shoulder) = 6 (take_content.py:142), but storyboard/panel_content.json shot 21 says the panel drew 10 people and PASSED. base
  becomes 10, allowance 11, the VLM counts 12 on distant strollers. The off-by-one is real arithmetic against a ratchet that is
  itself +4 over the plan; the 12-vs-10 jitter is a VLM count of far figures, the 10-vs-6 is the real fault (a panel gate hole).
- Lettering: panel `text: false` (panel_content.json), take `text: true` (T21.content.json): render-borne. But `panel_clean`
  only converts `{content, clones}` to a seed (take_ladder.py:159-160); `lettering` is INPUT_BORNE (take_ladder.py:67) and routes to ""
  (take_ladder.py:172). A render-borne lettering fault gets no cure. Plan invitation: "shuttered shop fronts" on a full-width thoroughfare;
  the plan battery printed "EXPECTS TEXT: no shot stages printed matter", so the writer was never warned that shop fronts draw signs.

## 4. The router: do the cures match the fault class?

`route` -> `cure_of` (take_ladder.py:152-176, 202-219):
1. gait -> `gait_cure` (take_ladder.py:134-140) -> "gait_verb" -> `gait_edit` (take_ladder.py:514-518) -> `gait.gait_verb`
   (gait.py:70-79). With no pace phrase it appends the clause (as at T00, 00:05); a plan that already carries the verb gets nothing
   new, so the re-render is a pure seed. SKILL.md:550 says "a gait shuffle is cured by the plan's verb, never a seed": here the verb
   was in by roll 3 and the later rolls were seeds anyway.
2. The verb is "in profile, a long stride, feet in the picture" (gait.py:65-66). "Feet in the picture" guarantees the gate can read
   the feet (gait.py:155 marks feet False when the box touches the bottom). The cure makes the take MORE measurable; it does not lengthen
   a step, and it is wrong for a locked wide whose walkers do not move.
3. Caps: ROUNDS_CAP 2 across resumes (take_ladder.py:845), REPEAT_CAP 2 per (take, kind) (take_ladder.py:229-231), MAX_TAKE_ATTEMPTS 3
   archived draws (take_ladder.py:845-847). T21's gait appeared after the cap and never routed. T05's warp had its one allowed seed
   (`warp_cure`, take_ladder.py:122-131), then the terminal. EP has no cures_owed.jsonl: the "plan cure owed" row
   (take_ladder.py:264-277) never fired, though T05/T19/T00 each took repeated draws.
5. Frozen: a `frozen-whole` on a locked-grammar shot is never pushed (take_ladder.py:507-508) and is ADVISORY there, so T00's real fault
   (standing walkers) had no move cure.
Verdict: gait = verb once then seed; warp = seed only (3 identical prompts); lettering/crowd = terminal. The ladder mostly rerolls
seeds for classes whose measured seed rate is ~0 (CURE_RATES, take_ladder.py:92-97), and the one class with a real plan cure
(gait) is fed a mis-measured fault.

## 5. Root causes

1. A signal sampled below twice its frequency: stride 2 folds the 8 Hz render pulse to 4.0 Hz inside BAND.
2. A cure whose success criterion is the failing gate's own readability ("feet in the picture"), not the picture.
3. A take that does not move (T00) carries a gait label; frozen walkers need a changed ask, not a stride phrase appended after "halt".
4. No plan rung for warp: seed then terminal. Same shape as repo memory (lag wants a shorter take, freeze wants a new move TYPE): a
   warp wants a changed ask (no head turn, shorter, wider), never a seed.
5. The crowd ceiling is anchored on the panel's own count, so an over-drawn panel loosens the take gate.
6. `panel_clean` ignores `lettering`.

## 6. Proposed fixes, with failing tests (pytest shape)

F1. `studio/gait.py`: measure at the native rate (`FPS = 24`, `measure(..., stride=1)`), or reject an alias in `judge(rows,
pulse_hz=None)` when `abs(freq - (FPS - pulse_hz)) < 0.3` (pass `measures.pulse` from take_dq). Recalibrate the 0.045 wall on
docs/audit/2026-10-14_jekyll_ep01_hel/gait_replay.jsonl at 24 fps before keeping it.
```python
# tests/test_gait_alias.py
import numpy as np
from studio import gait

def rows(freq_hz, fps, travel_hps, n=96):
    t = np.arange(n) / fps
    return [{"art": 1.0 + 0.4 * np.sin(2 * np.pi * freq_hz * x), "h": 1.0, "travel": travel_hps / fps,
             "feet": True, "grow": 0.0} for x in t]

def test_an_8hz_render_pulse_seen_at_12fps_is_not_a_gait():
    assert gait.judge(rows(8.0, 12, 0.16))["state"].startswith("unmeasured")   # today: shuffle 4.0

def test_a_two_step_walk_crossing_0_16_heights_a_second_is_a_walk():
    gait.FPS = 24
    assert gait.judge(rows(2.0, 24, 0.16))["state"] == "walk"                   # step 0.08
```
F2. `take_ladder.gait_cure` / `gait.gait_verb`: idempotent, and re-cure by move when the verb is already in.
```python
def test_gait_verb_is_idempotent():
    m = "The camera tracks beside them; they walk; the walker goes " + gait.VERB + "."
    assert gait.gait_verb(m) == m

def test_gait_with_the_verb_already_present_is_a_move_cure_not_a_seed():
    f = Fault(where="T19", kind="gait", severity="high", note="shuffle: 4.0 steps/s HARD", evidence={})
    assert take_ladder.cure_of([f], verb_present=True) == "move_type"    # new arg; today there is none
```
(`route` passes `gait.VERB in shot motion`; add a `"gait"` cause to CAUSE_OF/SUBSTITUTE, take_ladder.py:296-316, `{"*": "follow"}`.)

F3. `gait.row` (gait.py:129-139): travel under 0.02 heights/s is not a walker: not a HARD shuffle; `frozen-whole` owns it, and
`take_ladder.move_type` (take_ladder.py:507-508) no longer exempts a locked shot whose motion has a walk verb.
```python
def test_a_standing_pair_is_not_a_shuffle():
    m = {"state": "shuffle", "freq": 4.0, "step_h": 0.002, "travel_hps": 0.01}
    assert gait.row(m, "walk in and halt").ok                              # today: HARD
```
F4. `take_ladder.warp_cure` (take_ladder.py:122-131): after one seed with S still over the wall return "plan_warp"; `plan_cure`
(take_ladder.py:521-525) drops a head-turn clause, halves beat/coda (`shorten`) or widens size. Writer rule (SKILL.md shot form;
plan battery row): no "speaks and turns his head" on medium_close or closer.
```python
def test_a_second_warp_fail_is_a_plan_cure_not_a_seed():
    f = Fault(where="T05", kind="warp", severity="high", note="Se 4.61",
              evidence={"value": 2.98, "repeated": True})
    assert take_ladder.cure_of([f], taken=1) == "plan_warp"                # today ""; 3 identical prompts shipped
```
F5. `take_content.crowd_fault` (take_content.py:115-128): ceiling = declared + CROWD_FAR slack, never the panel's count; and
panel_content fails a panel whose people exceed declared + 2.
```python
def test_the_ceiling_follows_the_plan_not_an_overdrawn_panel():
    assert take_content.crowd_fault(reads_of(12), declared=6, panel_people=10)   # fires (also fires today: 12>11)
    assert take_content.crowd_fault(reads_of(8), declared=6, panel_people=10)    # today None: panel excess excused
```
F6. `take_ladder.cure_of` (take_ladder.py:159-160): with `panel_clean`, treat `lettering` like `content` (one seed). Writer rule:
a shopfront street states "blank fascias, no signs"; the EXPECTS TEXT check lists shop fronts.
```python
def test_lettering_on_a_clean_panel_is_render_borne():
    f = Fault(where="T21", kind="lettering", severity="high", note="text or lettering in the picture", evidence={})
    assert take_ladder.cure_of([f], panel_clean=True) == "seed"            # today ""
```
(`reads_of`, `Fault` fixtures derive from the contract in tests/conftest; no model call.)

## 7. What needs a GPU proof

No GPU, queue now (CPU, YOLO over OpenCV DNN): F1 re-measure at 24 fps of T00, T19, T21 plus the 20 calibration takes in
gait_replay.jsonl; accept if T19 reads walk, T00 reads unmeasured/frozen, and no calibration verdict flips except the ep01
T03/T01 alias cases. F2, F3, F5, F6 are pure unit tests.

GPU proof, HELD until the PCIe/BIOS fix (memory: project_gpu_lost_needs_reboot): one batch of 3 takes (~14 min,
cost model take_ladder.py:34): T00 (plan "the two men cross to the door", no appended stride), T05 (head turn removed), T21
(blank fascias + verb), then measure:
`uv run python scripts/episode/takes_r2v.py --retake=0,5,21 --why="plan_warp: warp, gait, lettering" --last`, then
`scripts/episode/take_dq.py 0 5 21` and `scripts/episode/take_content_check.py 0 5 21`.
Pass: T05 S <= 2.5 and Se < 3; T00 travel >= 0.1 heights/s; T21 text false and people <= 8; no take adds a hard row.
