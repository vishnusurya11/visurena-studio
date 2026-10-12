# C1-G: gates and speed remainders (cycle 1, researcher G)

2026-10-11. Read-only, plus online sources and CPU. No GPU was used, no code was edited and nothing was rendered.

**Scratch** (CPU scripts and outputs) is in `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c1\`:
- `sig3.py`: the sigma each schedule makes the DiT see, mapped back to the distillation grid
- `psnr_pairs.py` → `psnr_pairs.json`: arm-vs-control distance compared with seed-to-seed distance
- `seam_ladder.py` → `seam_ladder.json`: why each of the 18 seam panels shipped, read from the episode records
- `seam_by_shape.py` → `seam_by_shape.json`: seam rate by grid shape over all 572 WotW panels
- `dl\`: the author sources, fetched read-only:
  - `mt_readme.md.txt`
  - `mt_comfy.md.txt`
  - `mt_ref2v_wf.json`
  - `lx_h3_scheduler.py.txt`

| # | Issue | Verdict | Confidence |
|---|---|---|---|
| 1 | The 4-step loses content | **A3 runs off its own distillation grid.** The authors publish the 4-step ref2v grid as σ [1, .9730, .9231, .8000] → 0, which is `simple` at shift 12. We run `beta`, which hits base-t 824 and 177 where the student was trained at 750 and 250. The R2 verdict cut the one arm that is on the contract. | Off-grid: **99 %**. That the grid cures the frogs: ~60 %, so it needs one bench arm. |
| 2 | The CK PSNR wall | **The 28 dB wall is miscalibrated.** It would refuse today's shipped 8-step on every shot (16-27 dB against A3). Re-judged with seed-calibrated rules, **CK passes**. The S4 word is a property of the 4-step seed-1 tail, not of CK. | Wall miscalibrated: 99 %. CK passes: 95 %. Word by chance: ~90 % (5 renders take it to 95 %). |
| 3 | Seam panels shipped on keep_best | **The seam comes from the layout.** The strip grids are drawn by Qwen as a different grid: 15/201 strip panels against 0/198 square-ish ones (p = 4.7e-5). The seed-bump cure in 3ea5461 is measured not to cure it. **keep_best keeps the LAST draw, not the best.** | Cause: 99 %. Seed bump fails: ~90 %. keep-last: 95 %. |
| 4 | The red test | **The test is stale.** d8d47ea made `extreme_close` a real size. The fix is two lines in the test. | 100 % |

---

## 1. The 4-step LoRA: content loss and the sigma grid

### 1.1 What the authors use (online, primary sources)

**The ModelTC/Minimax-H3-Turbo README**, "Note on shift" (`dl\mt_readme.md.txt`):
- Model table: "Ref2VA Turbo 4-step v0.1 | 544p mixed aspect ratio | 12 / 3 | 4 | 4". Those are the training shifts (video / audio), the distillation NFE and the recommended NFE.
- Verbatim: "with `NFE = 4`, `video shift = 12`, and `audio shift = 3`, the shared grid is `q = [1, 0.75, 0.5, 0.25]`, giving video sigma `[1, 0.9730, 0.9231, 0.8000] -> 0` and audio sigma `[1, 0.9000, 0.7500, 0.5000] -> 0`."

**The authors' own ComfyUI ref2v graph** (`example_workflows/video_minimax_h3_ref2v_lightx2v_turbo.json`, read in `dl\mt_ref2v_wf.json`):
- **`BasicScheduler ['simple', 4, 1]`**
- `MiniMaxH3SigmaShift [12, 3]`
- `KSamplerSelect ['euler']`
- `LoraLoaderModelOnly [..ref2v_turbo_4step_v0.1.., 1]`
- `ref_image_size 'match'`

**LightX2V's reference scheduler** (`lightx2v/models/schedulers/minimax_h3/scheduler.py`, in `dl\lx_h3_scheduler.py.txt`):
- `base = linspace(1, 0, steps+1)`
- `sigmas = shift*base/(1+(shift-1)*base)`
- `training_euler` step: `x + (σ − σ_next)·v`
- `configs/minimax_h3/dmd/minimax_h3_ref2av_4step.json` sets `video_flow_shift 12.0`, `audio_flow_shift 3.0`, `infer_steps 4` and `reference_image_resize_mode match`.

**The Kijai / H3-Turbo node README** (larryvrh, FL2VA lineage) also says "keep the scheduler on `simple`". It is a different LoRA family and is quoted only as corroboration.

**ComfyUI 0.36:**
- `simple` at 4 steps over the 1000-entry shifted table picks t = 1000/750/500/250, which is exactly the grid (`sig3.py`).
- The audio sigma is derived from the video sigma (`ldm/minimax/model.py:563`, `time_shift_sigma(σv, 12, 3)`), so the video grid also puts the audio exactly on the authors' audio grid.

### 1.2 What production runs (`sig3.py`)

| schedule | σ the DiT sees | base-t (trained: 1000/750/500/250) | worst off-grid |
|---|---|---|---|
| **A3 today: 4 × beta @12** | 1, .9825, .9234, .7207 | 1000, **824**, 501, **177** | **74** |
| **4 × simple @12 (authors)** | 1, .9730, .9231, .8000 | 1000, 750, 500, 250 | **0** |
| 5 × simple @12 (4-step LoRA) | 1, .980, .947, .889, .750 | 1000, 800, 600, 400, 200 | 100 |
| 6 × simple @12 (4-step LoRA) | 1, .984, .960, .923, .858, .706 | 1000, 834, 667, 500, 334, 167 | 84 |
| A1 today: 8 × beta @12 (8-step LoRA ×2) | 1, .995, .983, .961, .923, .855, .721, .425 | 1000, 943, 824, 671, 501, 330, 177, 58 | 67 (vs the 8-grid) |
| 8-step grid, 8 × simple @12 | 1, .988, .973, .952, .923, .878, .800, .632 | 1000, 875, …, 125 | 0 |
| **6-of-8 subset** (drop 875, 625) | 1, .973, .923, .878, .800, .632 | 1000, 750, 500, 375, 250, 125 | 0 |

**Corrections to R2_verdict §0.2 and §1:**
- Beta's last call (.72) is *lower* than the authors' (.80). "The final Euler step jumps from 0.72 to 0" is therefore not the defect, because the authors' own grid jumps from 0.80.
- **The defect is that two of the four calls are off the trained timesteps.** Step 2 sees *more* noise than it was trained for (824 against 750), and that is where layout and objects are committed. Step 4 sees less (177 against 250). The audio is off the same way: its last call is at σa .39 against the trained .50.
- The verdict cut `simple@12` as "the softer direction". That cut removed the **only arm on the published contract**.
- The house note "simple = softer" was measured on the ckpt850 FL2VA LoRA (R2_Q §0b), not on this LoRA.

### 1.3 The D1 "clone frame" is not a 4-step fault

`measures_r2.json` D1 `clone_frames`:

| Take | Clone frames |
|---|---|
| A0 (shipped 8-step) | **1** |
| A1 (8-step) | **2** |
| A3 seed 1 | 0 |
| A3 seed 2 | 1 |
| CK | 0 |

The production take fails the "D1 held to 0" rule itself. D1's prompt asks for "his head tips back as a laugh shakes through his shoulders", so the clone is a property of the shot. **The rule should read "clones ≤ the production take's count on the same shot".** The 4-step's case therefore rests on S3 content alone, plus the tail.

### 1.4 Which option keeps the content at about half the time

- **5-step or 6-step on the 4-step LoRA: rejected by the arithmetic.** Every call is off the grid (worst 84-100). That is the opposite of the cure.
- **G1: the 4-step on the authors' grid** (`BasicScheduler simple`, 4, shift 12/3). It is the **only option at true half time**: the same NFE as A3, so 0 min per episode against the 5.55 h projection. Likelihood that it keeps the S3 frogs: about 60 %.
  - For: it is the trained grid; DMD students are evaluated only at their trained t.
  - Against: the 8-step is also off its grid by up to 67 and keeps content, so off-grid is not the whole story. Also, the 4-step v0.1 was trained at 544p, against our 768² short edge.
- **G2: the 8-step LoRA ×2 at 6 calls on its own grid subset** (`ManualSigmas "1, 0.9730, 0.9231, 0.8780, 0.8000, 0.6316, 0"`). Every call is on the 8-grid, so it is the likeliest to keep content (about 70 %). It saves only about 25 % of sampling: roughly −12 min per episode against today's 8-step, and +15 min against A3.
  - It drops the two smallest σ gaps (.012 and .021).
  - Caveat: the ref2v 8-step 768p row is not in the ModelTC table. Its 12/3 is from the release post, per the `takes_r2v` docstring.

### 1.5 The arms (new files only, `<base>_<source>.json`; A3 is never edited)

| Arm | Graph change | Shots | Renders | GPU min |
|---|---|---|---|---|
| **G1 `video_minimax_h3_r2v_turbo_ref8_ref4_singularity_simple12_modeltc`** | node 9 `scheduler` beta → **simple**. Nothing else. | the six, seed 1; plus seed 2 on S3, S4, D1 | 9 | ≈ 20 |
| **G2 `video_minimax_h3_r2v_turbo_ref8_crf_visurena_sub6_modeltc`** | a new node `ManualSigmas` with the string above, feeding node 13 `sigmas` in place of node 9 | the six, seed 1; plus S3 seed 2 | 7 | ≈ 20 |
| Loads, ffprobe, slack | | | | 5 |

**Prerequisites (CPU, test-first):**
- `scripts/bench/h3_arms.py` must lay an arm-only `ManualSigmas` node and rewire node 13. `knobs()` must read the sigma string. Otherwise G2 runs `beta` 8 and reports "no change" (memory `a-fix-that-changes-nothing`).
- G1 needs nothing: bcb8312 already asserts `scheduler`.

**Judged against:** A3 for G1 and A0 for G2.
- S3 frogs at 50 % on the contact sheet (both seeds).
- Clones ≤ the production take's count.
- id ≥ the calibrated rule in §2.3.
- The speech tail: dB, words and lower-face motion.
- **Adopt G1** if the frogs hold on both seeds. **Otherwise adopt G2 as the speed step.**
- G1 is also the cleanest test of root-cause candidate 2 for the invented speech, because the audio returns to its trained grid.

---

## 2. CK int8 attention: re-calibrating the PSNR wall and re-judging from existing renders

### 2.1 Measured on CPU (`psnr_pairs.json`)

The figures are ffmpeg `psnr` YUV average and SSIM over the whole take. Absolute PSNR runs about 1-2 dB above BENCH_r2's numbers (a different averaging), but the ranking is identical.

| shot | A3 seed 2 vs A3 | **CK vs A3** | shift6 beta | shift6 simple | A1 (8-step) vs A3 | **CK margin over seed** |
|---|---|---|---|---|---|---|
| S2 | 17.1 / .50 | **24.5 / .70** | 18.2 | 19.5 | 18.3 | +7.4 dB |
| S3 | 20.4 / .61 | **28.1 / .81** | 23.5 | 23.5 | 22.1 | +7.8 |
| S4 | 16.0 / .50 | **30.7 / .93** | 27.8 | 29.2 | 26.8 | +14.8 |
| S6 | 20.1 / .72 | **28.3 / .87** | 27.6 | 28.6 | 20.9 | +8.2 |
| D1 | 15.3 / .65 | **30.3 / .91** | 23.6 | 24.8 | 16.0 | +15.0 |
| D2 | 18.4 / .68 | **27.8 / .87** | 23.0 | 24.0 | 17.6 | +9.4 |

- CK is the closest arm to the control on **all six shots**, and 7-15 dB above seed-to-seed.
- **A fixed 28 dB floor would refuse A1, the 8-step that ships today, on all six shots.** It measures how far an int8 rounding error travels through a chaotic sampler, not quality.

### 2.2 Rulers: CK against the control's own seed spread (`measures_r2.json`)

| ruler | seed spread \|A3 s2 − A3\| | CK − A3 |
|---|---|---|
| id S4 / S6 / D1 / D2 | .002 / .006 / .015 / **.033** | −.010 / −.018 / −.001 / **−.022** |
| banding (6 shots) | .001-.028 (mean \|Δ\| .018) | mean +.001, worst +.006 (S6) |
| clones / lag | 0 / 0 (D1 s2: 1 clone) | 0 / 0 |

- D2's −.022 sits **inside** that shot's own seed spread (.033).
- An honest caveat: CK's identity delta is negative on 4/4 dialogue shots, with a mean of −.013. A one-sided sign test gives p = .06, so CK may cost about 0.01 of facenet identity. That is smaller than the A3 → A1 gap (−.032 on S4 and S6), and A1 is what ships today.

### 2.3 The proposed calibrated non-inferiority rule (replaces the 28 dB wall and the flat −0.02)

1. **Same-draw guard** (a pixel test, used only for this):
   - PSNR(arm, ctl) − PSNR(ctl seed 2, ctl) ≥ **3 dB** on every shot. This shows the arm changed the numerics, not the draw.
   - An arm under this guard (a schedule or LoRA change) is judged as a *new draw*, by rulers and the owner's eye only.
2. **Identity:**
   - Per shot, Δid ≥ −2·σ_seed, where σ_seed is the pooled RMS of the seed differences = .018, so **≥ −0.037**.
   - **The mean Δid over the dialogue shots must be ≥ −0.02.**
   - Recompute σ_seed whenever a seed-2 control is added.
3. **Banding** is unchanged: the mean must be ≤ ctl + .005 and no shot worse by more than .03. It is already seed-scale.
4. **Clones:** ≤ the production take's count on the same shot (§1.3).
5. **Invented speech:** compare the words and the lower-face tail ratio against **the control's own sounding/silent state on that seed** (§2.4). Exempt words the shot's prompt asks for (D1).

**CK re-judged under this rule: PASS.**

| Check | CK result |
|---|---|
| Same-draw margin | +7.4 to +15 dB |
| id | worst −.022 (≥ −.037), mean −.013 (≥ −.02) |
| banding | +.001 |
| clones | 0 |
| lag | 0 |

The face sheet `bench_evidence\r2\faces_B3_ck.jpg` was already read as indistinguishable. As a speed arm, it is adopted on rules 1-3 (R2_verdict §3.4).

**Where CK goes:**
- **CK is not tied to the 4-step.** A3 is not wired, so CK on today's 8-step BASE is its own arm: `video_minimax_h3_r2v_turbo_ref8_crf_visurena_ckattn_comfyorg`, 6 renders, ≈ 15 GPU min.
- It is judged by the same rule, against A0.
- At 8 steps CK saves about twice the 4-step's −9 min per episode, so about **−15 to −18 min per episode** (an estimate; the sampling share doubles).

### 2.4 Is the S4 "Indeed." chance?

Most likely yes, at about 90 %. The evidence is in `speech_tail.json`.

**At seed 1 the S4 control tail is already sounding:** −30.2 dB, mouth ratio .325. At seed 2 it is silent (−92.4).

**Four unrelated perturbations of seed 1:**

| Arm | Tail level | Words heard | Mouth ratio |
|---|---|---|---|
| CK (attention numerics) | −24.7 dB | **"Indeed."** | .34 |
| shift6 beta | −24.0 dB | **"Heed."** | .43 |
| shift6 simple | −22.3 dB | none | .43 |
| 992 | −17.4 dB (the loudest) | none | .58 |

- A word does not track loudness, and both words echo the line's last word ("…a man indeed").
- The model mumbles an echo whenever the seed-1 tail sounds, and Whisper resolves some of those mumbles into a word.
- **CK did not change the shipping risk.** Masters strip take audio, and CK's mouth ratio (.34) equals the control's (.325).

**To reach 95 %:** render A3 on S4 at seeds 3 and 4, and CK on S4 at seeds 2, 3 and 4. That is 5 renders, ≈ 8 GPU min. CK is cleared if the word rate per sounding tail is the same in both arms.

The real fault is that the **4-step itself** lifts the tail: mouth .12-.15 → .31-.33 against the 8-step. That belongs to the invented-speech issue, not to CK.

---

## 3. Seam panels: why 16 shipped, and a cure that cannot loop

### 3.1 How each of the 18 shipped (`seam_ladder.json`, read from each episode's `storyboard\ladder.json`, `eye_*.json`, `layout.json`, `panel_dq.json` and `superseded\`)

| Path to ship | Panels |
|---|---|
| **Cap exhausted:** two other grids took the `max_grids` 2 first. Fault `climbed: false`. | ep19 17/18, ep21 22/23/24, ep25 20/22 (**7**) |
| **Climbed and still stacked** (redraw then reprose, all draws stacked .98-.99) | ep22 5/9 (**2**) |
| **A clean grid re-rolled into a fault by sibling redraws:** `copper_2x1_b` v1 and v4 read stacked 0.0, the shipped draw 1.0. It was redrawn 4× as the anchor's kin. | ep20 9/15 (**2**) |
| Grid in the climbed list, fault still `climbed: false` (layout changed by an isolate) | ep27 10/16 (**2**) |
| Pre-ladder era (no layout, no eye) | ep07 12/13/14 (**3**) |
| Seam only, `stacked` silent (ep14 s07 is an edge remnant at col 22-28) | ep14 7, ep25 9 (**2**) |

### 3.2 The cause is the layout, not the seed (`seam_by_shape.py`, all 572 WotW h3 panels)

| grid shape (cells are 1024² in every shape) | panels | seam | stacked flag |
|---|---|---|---|
| 1x1 | 92 | **0** | 0 |
| 2x2 | 100 | **0** | 0 |
| 3x2 | 6 | 0 | 0 |
| **2x1** (2048×1024) | 60 | **8 (13.3 %)** | 8 |
| **3x1** (3072×1024) | 141 | **7 (5.0 %)** | 8 |
| pre-layout | 173 | 3 | 3 |

- Strips against square-ish grids: 15/201 against 0/198. **Fisher p = 4.7e-5.**
- **The mechanism is read from the seam positions.**
  - Every 2x1 seam is a **row at 381-383 of 768** (50 %). Qwen drew a **2x2** on the 2:1 canvas.
  - The 3x1 seams fall at **cols 577 / 382 / 191** in cells 0 / 1 / 2. Those are 75 / 50 / 25 %, which is exactly where the gutters of a **4-column** grid (768 px apart) land in 1024-px cells.
- Qwen draws its own preferred grid count, not ours. `grid_layout.GOOD`'s own docstring says "without … a long strip", yet `shape(2)` and `shape(3)` *are* strips.
- **A seed bump does not cure it:**
  - ep22 `pantry_empty_3x1_b` read stacked .99 / .98 / .98 on all three draws.
  - ep14 Waterloo was redrawn 9 times.
  - ep20 alternated clean and stacked, and shipped stacked.
  - The cure named in 3ea5461's message ("the ladder's seed-bump grid redraw") is therefore measured **not** to cure.
- **keep_best keeps the last draw.** The terminal leaves "the panels stand as drawn", and `supersede()` moves every earlier draw away, including clean ones (ep20 v1 and v4).

### 3.3 The cure (test-first; bounded, so it cannot loop the autopilot)

1. **Prevention: no strips** (`grid_layout.shape`).
   - 2 shots → two 1x1 grids. Same pixels (2 × 1 MP against 2 MP), and the room is held by the anchor chain as faces already are.
   - 3 shots → one 2x2 whose 4th cell is the setup's empty place, at the room-anchor wording. It is not staged, and it doubles as a room reference. The alternative is three 1x1s.
   - Cost: +33 % pixels on a 3-shot grid, about +0.6 GPU min, and about 2-4 per episode, so **≈ +2 GPU min per episode**.
   - **Acceptance:** replay the 9 seam grids' setups at their shipped seeds. 0 seams, and G-SETUP still passes.
   - This is an architecture change (the grid rule), so `architecture/index.html` and `GATES.md` change in the same commit.
2. **Rung for `seam`/`stacked`: isolate, not seed** (`panel_ladder`).
   - It reuses `Climb.isolate` (G-TWIN rung 2), which puts the faulted shot in its own 1x1 (0/92 seams).
   - `isolate` returns False for a shot already alone, so **every shot can take this rung at most once. It is finite by construction.**
   - It is priced at one 1x1 render plus the scoped rebuild. It is **outside the 2-grid cap**, which exists for open-ended seed and reprose climbs, so it cannot starve.
   - Drop the `stacked`/`seam` entries from `CURES` for reprose. It ran on ep22 and moved nothing.
3. **keep_best becomes best-of-draws.**
   - The terminal restores, per grid, the draw (current or `superseded/<name>_vK.png`) with the fewest machine flags on its own shots (`panel_dq.verdict`, already a pure function). It re-cuts the panels from that draw.
   - A sibling redraw may never replace a grid whose panels were machine-clean. That is the rule `machine_clean` already states for rungs ("a rung may not undo a clean board"), extended to `Climb.redraw`'s kin loop.
4. **Terminal for a panel still seamed after isolate (owner ruling needed):** that shot's take renders **refs-only**. Its doubled panel is never staged, because a staged doubled cell is a duplicate-figure source (R2_verdict §0.5). The take gets the sheets, the place picture and the words, and is flagged in `audit/`.
   - Today `FROM_REFS` is episode-wide (`takes_r2v.py:269`). A per-shot version is a small new mode and an architecture-page change.
   - Rejected alternatives:
     - **Crop the clean half.** A 2x1-as-2x2 half is 1024×512, so a square crop is 512 px upscaled 1.5x and soft, and which half is "the shot" is a guess.
     - **Fall to a still.** It breaks the audio-first cut, and the owner has never ruled that a still may ship.

**What the owner must rule** (memory `a-terminal-is-not-a-pass`):
- (a) Whether a seam/stacked panel that survives its isolate ships **unattended as a refs-only take, flagged in the audit sheet**, or parks the episode. The 2026-10-01 ruling ("judge-signed terminals auto-clear") would otherwise ship it silently.
- (b) Informational: the 2 → two 1x1 and 3 → 2x2 layout change. It sits under the 2026-09-28 one-room ruling: the room is held by the anchor chain, not by the strip.

---

## 4. The red test: `tests/test_an_empty_panel_is_not_framed_on_a_person.py::test_an_unknown_size_is_refused`

**Cause:** d8d47ea (2026-10-08) "Every size the contract can sign is a size the grid can say".
- It added `full` and `extreme_close` to `PEOPLED_CUT` and `EMPTY_CUT`, after ep21 launch16 died on KeyError 'full'.
- This test (8f38506, 2026-09-20) used `extreme_close` as its example of an *unknown* size, so `cut_clause` no longer raises.
- The code is right, and the test is stale.
- Confirmed with `uv run pytest`: 1 failed, 16 passed.
- I also checked that the two new empty-panel clauses carry no body word and no fence word ("no"/"never"), and that each has ≥ 8 words (21 and 29).

**Minimal fix (test only):**

```python
from typing import get_args
from studio.episode_spec import Size

SIZES = get_args(Size)          # was a hand list of 5; full and extreme_close now covered too

def test_an_unknown_size_is_refused():
    assert "establishing" not in SIZES
    with pytest.raises(KeyError):
        cut_clause("establishing", peopled=False)
```

---

## 5. GPU minutes (cycle 1 window, if the owner's budget allows)

| Item | Renders | GPU min | Decides |
|---|---|---|---|
| G1 4-step on the authors' grid | 9 | 20 | the 4-step at half time, and audio back on its trained grid |
| G2 8-step ×2 on a 6-of-8 subset (only if G1 loses the frogs) | 7 | 20 | the fallback speed step, −12 min per episode |
| CK on the 8-step BASE | 6 | 15 | adopt CK now, −15 to −18 min per episode (estimate) |
| S4 seed sweep, A3 against CK | 5 | 8 | the S4 word is chance (to 95 %) |
| Seam prevention replay (Qwen grids, 9 setups) | 9 grids | 15 | 0 seams under the no-strip rule |
| Loads and slack | | 10 | |
| **Total** | | **≈ 70-90** | |

**Publishable (flag):**
- ComfyUI's common `beta` setting puts the ref2v 4-step LoRA off its published grid. The audio follows the same grid.
- The calibrated non-inferiority rule for numerical speed arms in chaotic samplers: same-draw margin plus seed-spread tolerance.
- Qwen-Image draws its own grid count on 2:1 and 3:1 multi-panel canvases (0/198 against 15/201).

All three belong in the planned public ref2va / storyboard bench.

Sources:
- [ModelTC/Minimax-H3-Turbo README (model table, "Note on shift")](https://github.com/ModelTC/Minimax-H3-Turbo)
- [ModelTC ref2v ComfyUI workflow](https://github.com/ModelTC/Minimax-H3-Turbo/tree/main/example_workflows)
- [LightX2V MiniMax-H3 scheduler and DMD configs](https://github.com/ModelTC/LightX2V/tree/main/configs/minimax_h3/dmd)
- [ComfyUI-Wiki: MiniMax H3 Turbo Ref2V v0.1](https://comfyui-wiki.com/en/news/2026-08-13-minimax-h3-turbo-ref2v)
- [LightX2V step distillation docs](https://lightx2v-en.readthedocs.io/en/latest/method_tutorials/step_distill.html)
- [lightx2v/Minimax-h3-Turbo on Hugging Face](https://huggingface.co/lightx2v/Minimax-h3-Turbo)
