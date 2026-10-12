D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c2\b\

# C2-B: speed, tests and the 6 h budget (cycle 2, researcher B)

2026-10-11. Read-only: CPU, the repo, the library's run records and the bench scratch. No GPU job, no code
or workflow edit, no ComfyUI touch. The bar is the CYCLES one: **95 % = measured on the artefact, in at
least 2 independent cases**. Anything weaker is marked as a hypothesis with a number.

**Scratch** (every number below comes from one of these scripts; rerun any with `python <script>`):
`D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c2\b\`
- `phases_all.py` → `phases_all.json`: the per-take phases of all 51 bench renders (r2 + c1 `runs.jsonl`)
- `timing_eps.py` → `timing_eps.json`: stage minutes per episode, WotW ep17-27 (`timing.jsonl`)
- `plan_ladders.py`, `plan_climbs.py` → `plan_climbs.json`, `plan_policies.py`, `kept_rung.py`, `gate_tally.py`, `lowcure.py`: the plan stage, from each episode's `learnings.jsonl` PLAN rows
- `projection.py`, `projection2.py`, `projection3.py`: the P50/P90 projection
- `door_check.py`: which shipped timelines `episode_home.load_placed` accepts

| # | Question | Answer | Confidence |
|---|---|---|---|
| 1 | CK int8 for dialogue | The written rule needs **3 renders** (CK8 D1 s2, CK8 D2 s2, A1 D1 s2; ≈ 7 GPU min). But S4/D2 are silent-tail shots at 8 steps, so that test has **no power** to see CK raise invented speech. Add **2 shipped sounding-tail dialogue takes** (ep10/T21 "Moving!", ep15/T21 −19.8 dB) × {A1, CK8}: **7 renders, ≈ 15 GPU min**. Gain −5 to −7 min per episode. | rule gap: 99 %; outcome open |
| 2 | 6 h budget | Measured baseline (ep19-27): **P50 5.68 h, P90 7.49 h**, 3/9 over. Cycle 1 as built: **P50 5.5-5.6 h, P90 7.2-7.3 h**. Renders no longer set the tail: the **plan stage is 90 % ladder rungs**, and **40 of 48 climbs ran to the terminal**. With the plan fixes below: **P50 ≈ 4.2 h, P90 ≈ 6.5 h**; adding a QC memo: P90 ≈ 6.05 h. | baseline measured; fixes are replays of the record |
| 3 | Untested speed levers | A take's non-sampling, non-decode time is **11-15 s when the TE runs and 2.3-2.9 s when it is cached** (n = 10 vs n = 4). No ComfyUI flag can keep TE + DiT resident (14.6 + 19.5 GB > 22 GB). Merged LoRA + an "encode-all" prewarm share a ceiling of **≈ 5 min per episode**. VAE decode is bimodal (16.5 vs 24.5 s per 100 frames): ≈ 3.7 min per episode in the slow mode. **All three together are smaller than any one plan fix.** | phases measured; gains are ceilings |
| 4 | 2 red tests | (a) `book_title.py` reads `placed.json` raw (3b38559). **Switching to `load_placed` would break it:** the door refuses 6/27 shipped WotW and **14/14 Scarlet** timelines. The fix is a shipped-history door in `episode_home`. (b) ep11 regen: **c300c4f** ("a row never carries two heads") drops the artilleryman's body hair clause that ep11's `plan.py` quotes. `cast_refs.tag` is called only by legacy plan scripts, so the fix is to validate against the card's own words too. | 100 % (both reproduced) |

---

## 1. CK int8 attention for DIALOGUE: what reaching 95 % takes

### 1.1 Where it stands (`bench_evidence\c1\judge_c1.json`, `tails_c1.json`, `measures_c1.json`)

The rule is GATES.md §Speed arms (`rulers.judge_arm`): (a) same draw, (b) identity ≥ −2σ_seed per shot and the dialogue mean ≥ −0.02, (c) banding, (d) clones, (e) invented speech against the control's own state on that seed.

**Arm rule:** "a speed arm passes the INVENTED-SPEECH check on **S4, D1 and D2 × 2 seeds**, or it is adopted for narration takes only".

| shot | seed 1: CK8 vs A1 | seed 2: CK8 | seed 2: A1 (control) | rule state |
|---|---|---|---|---|
| S4 | tail −55.6 dB, no word / A1 −57.6, no word; id .738 vs .768 | −91.0 dB, no word, id .745 | −92.2, no word, id .776 | **done** |
| D1 | laugh "hahaha" both (prompt-asked, exempt); id .853 vs .837; clones 0 vs 2 | **missing** | **missing** (no 8-step D1 s2 exists, so `judge_c1` D1 `seed2` = 0.0 and the same-draw guard is unread) | **2 renders** |
| D2 | −94.4 dB silent / A1 silent; id .869 vs .875 | **missing** | −95.0 silent, id .899 (exists) | **1 render** |

So the rule as written needs **3 renders**: CK8 D1 s2, A1 D1 s2 and CK8 D2 s2. At the measured prompt times (D1 CK8 54 s, A1 ≈ 75 s, D2 CK8 110 s) plus loads, that is **≈ 7 GPU min**.

### 1.2 Why those 3 renders are not enough for 95 %

- **The 8-step S4 and D2 tails are silent on both seeds** (−55 to −95 dB). D1's tail sounds, but by the prompt's own laugh, so the check exempts it.
- So none of the six rule renders has a sounding tail that is not exempt. Rule (e) can therefore only come back "no new word" whatever CK does: the test has no power.
- The one measured CK fault is exactly this case. On the 4-step S4 seed 1, the **control's tail already sounded** (−30.2 dB); CK pushed it to −24.7 dB and Whisper heard "Indeed." (BENCH_r2 §5).
- Production has such tails. 15 of 204 shipped dialogue takes are louder than −45 dB in the tail (`C1_A_evidence\shipped_fixed.rows.json`). Two of them run on today's exact BASE graph (Singularity int8 + 8-step LoRA 1.0/0.7, 8 × beta):

| take | tail dB | words | frames | why it is the right probe |
|---|---|---|---|---|
| **wotw/ep10/T21** | −14.9 | "moving" (the G-TAIL failure) | 124 | the one shipped take that invents; G-TAIL's own positive |
| **wotw/ep15/T21** | −19.8 | none | 158 | loud tail with no word: the S4-seed-1 shape |
| (spare) wotw/ep22/T12 | −30.1 | none | 175 | prompt-asked "mouth forms the soft call", so exempt; use only if one of the two above fails to replay |

Both have `T21.graph.json` on disk under `library\20260827135508_the-war-of-the-worlds\episodes\ep10\takes\r2v\` and `...\ep15\takes\r2v\`. The overlay builds an arm from the ran graph, swapping only the attention node (`h3_arms`). One condition before rendering: the staged guide's hash must equal `placed.json` (C1 LESSONS: "a guide overwritten in ComfyUI/input makes the speech check lie"). A guide that does not match is skipped, never "measured".

### 1.3 The minimal GPU arm (one window, ≈ 15 GPU min, queue empty, no relaunch)

| # | render | arm | seed | ≈ s |
|---|---|---|---|---|
| 1 | D1 | A1 `video_minimax_h3_r2v_turbo_ref8_crf_visurena` | 2 | 75 |
| 2 | D1 | CK8 `..._crf_visurena_ckattn_comfyorg` | 2 | 55 |
| 3 | D2 | CK8 | 2 | 110 |
| 4 | ep10/T21 | A1 (control re-render, shipped seed) | shipped | 120 |
| 5 | ep10/T21 | CK8 | shipped | 85 |
| 6 | ep15/T21 | A1 | shipped | 145 |
| 7 | ep15/T21 | CK8 | shipped | 100 |

- **Why render the controls at all:** a re-rendered A1 is not the shipped A0. D1 A0 carries 1 clone frame and A1 carries 2, so the two differ. CK is judged against A1 at the same seed.
- **Total:** about 11.5 min of render, plus loads ≈ 15 min.

**Adopt CK for dialogue (one line: `takes_r2v` returns `NARRATION_BASE` for both lanes) only if all of these hold:**
1. Rules (a)-(e) pass on D1 s2 and D2 s2. σ_seed is recomputed with the new D1 seed pair.
2. On **both** sounding-tail takes, CK8's tail words are a subset of A1's words at the same seed. The tail dB is within ±6 dB of A1, and the lower-face tail ratio is within A1's own range.
3. `measure/mouth.lag` stays within ±1 frame of A1 on all four dialogue renders.

**Otherwise:** dialogue stays on BASE, and the result is logged as a measured "no".

**Also read:** the identity sign. CK's Δid is negative on 2 of 4 shots at 8 steps and 4 of 4 at 4 steps (6/8, sign test p ≈ .14). The two seed-2 renders add 2 more pairs. If 8/10 come back negative, record "CK costs ≈ .01 facenet" as measured.

**Gain if adopted:**
- Measured c1 sampling on dialogue: D2 121 → 67 s (−45 %), S4 66 → 40 s, S6 88 → 51 s.
- Over the dialogue share of renders (≈ 22-25 %; 154 WotW dialogue takes out of ≈ 690), that is **−5 to −7 min per episode** (projection: median −5.8).

---

## 2. The 6 h budget, rebuilt from the run records

### 2.1 The measured baseline (sum of `timing.jsonl` stage seconds; the machine clock, not the wall)

| ep | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 |
|---|---|---|---|---|---|---|---|---|---|
| total, min | 407 | 423 | **553** | 334 | 188 | 270 | 229 | 341 | 357 |
| plan | 162 | 64 | **206** | 128 | 47 | 40 | 64 | 142 | 37 |
| takes | 103 | 107 | 101 | 81 | 36 | 71 | 68 | 81 | 60 |
| qc (all runs) | 26 | 59 | **83** | 24 | 8 | 47 | 8 | 26 | 15 |
| reruns of downstream checks* | 55 | 114 | **129** | 42 | 12 | 73 | 6 | 40 | 33 |

\* The 2nd and later runs of qc + assemble + take_dq + take_content + take_eye + master_eye in one episode. ep20 ran qc 7 times (8.2-8.7 min each), and so did ep21 (11.6-12.2) and ep24 (6.6-6.8).

- **P50 5.68 h, P90 7.49 h** (linear interpolation over 9 episodes), with 3 of 9 over 6 h. This matches S_skeptic §3 (median 5.68, mean 5.74).
- The ep17-27 stage medians: plan 76, takes 74, grids 22, take_dq 23, qc 24, panel_eye 15 min (`timing_eps.py`).

### 2.2 Cycle 1, priced on measured parts

| change | Δ per episode | basis |
|---|---|---|
| CK8 on narration (06d8ade) | **−8 to −23 min** (median −17) | takes stage × 0.72 sampling share (c1 A1 rows: 66/87, 88/127, 121/159 s) × 0.40 CK cut (39-45 % measured) × 0.75 narration share |
| No strips (a51ecef), +4.4 grid calls | +2 to +4 | warm 1x1 15.4-20.8 s, 2x2 66-102 s; first-of-model 46-172 s (`bench.log` block 2) |
| G-TAIL (2aeb777) | +1 | Whisper only on tails > −45 dB (≈ 12 % of dialogue takes), one reseed on ≈ 1 % |
| Seam rung (0f6c92d) | 0 | 0 seams in the 25 replayed panels |
| LOOK draws and LOOK-STATE reads | +3 to +8 | Krea2 ≈ 60 s per draw, VL read ≈ 20 s (`bench.log` b1); 2-4 looks per episode, cap 2 redraws on the tail |

**Cycle 1 as built: P50 5.49-5.60 h, P90 7.21-7.32 h, still 3/9 over 6 h.**
- The P50 holds under 6 h.
- **The P90 does not, and no render-side change can move it**: the over-budget episodes are over by 1.0-3.2 h, while all of CK is about 0.3 h.

### 2.3 The plan stage: where its time goes (`learnings.jsonl` PLAN rows, ep17-27)

- **Plan-stage minutes: 1,077. Of those, 966 (90 %) are inside ladder rungs.** Brief, first draft, critic and battery outside the rungs come to 8-43 min per episode.
- **48 climbs. 40 ran every rung to `keep_best`.** The other 8 have no terminal row: all were cut off mid-climb by a relaunch or an LLM error. **Not one climb in the record ended clean by a rung.**
- The mean full climb is 20 min: improve 297 s × 2, fresh_brief 558 s, model_tier 172 s.

**Cause 1: the `fresh_brief` rung buys almost nothing.**
- It ran 41 times for **381 min**: 34.6 min per episode mean, 19 median, **44-51 min on ep19, ep21 and ep26**.
- It produced the kept draft in **1 of 40** terminal climbs (`kept_rung.py`). By design it throws the history away and redrafts from a fresh brief.
- **64 % of terminal-climb rung time (547 of 849 min) was spent after the draft that was finally kept already existed.**
- The other late rung earns its place:
  - `model_tier` turned a battery-refused draft into a battery-passing one twice (ep21 10-08 06:39: 50 → 13; ep27: 49 → 13).
  - In 3 more climbs it produced a parseable draft after a contract refusal (ep18, ep23, ep26).
- **Fix 1:** remove `fresh_brief` from `plan_ladder.ladder()`, so the ladder is improve × 2 then model_tier, then the terminal. Test first: a FakeModel ladder test shows that 4 rungs become 3 and a converged draft is still edited, never discarded.
- **Saves 19 min per episode (median), 35 (mean), 44-51 on the P90 episodes.** It also saves paid calls under the $3 wall.
- Measured on 41 runs across 11 episodes.

**Cause 2: the same plan is climbed again on the same faults.**
- 27 of 37 battery-fault climbs end still refused. That means a defer, then `plan_repair`, then a second `clear()` in the same run, then `Deferred`, then the next autopilot launch climbs again.
- **9 climbs started on exactly the fault count the episode's previous climb ended on (182 min)**: ep22 five times on 61, ep26 on 39, ep19, ep21, ep25.
- Another **8 climbs were abandoned mid-way (116 min)**, plus 41 min of plan rows with `ok: false`. These came from LLM errors (`openai.BadRequestError`, `_parse_loose` failures) and from "code moved mid-episode" relaunches. ep21 alone shows 22 launches.
- **Fix 2:** a fault-set memory. `plan.deferred.json` already holds the best draft's faults, so store the sha of its sorted refusal lines. A new climb whose first battery verdict has the same sha goes straight to the terminal (defer or flag), with no rung.
- Free cures still run first (`cure_aside_first`), so a plan that a code change actually cures still re-judges and passes.
- Test first: two climbs over a FakeModel with identical refusals pay for one climb.
- **Saves 17 min per episode (median), 0-55 per episode.**

**Cause 3: fault classes the writer rarely cures keep climbs alive.**

Per-rung cure rate = the fault is present before a rung and absent after it (`plan_policies.py`). It is an upper bound, because a redrafted plan can drop a fault by changing the shot.

| class | rung verdicts | writer cure rate | episodes |
|---|---|---|---|
| G-TWICE | 71 | 30 % | 9 of 11 |
| G-STORY | 50 | 30 % | 9 |
| critic `invented` (e.g. "count 'extras=200' has no chapter span") | 40 | 28 % | 10 |
| G-TAKELINT | 45 | 36 % | 6 |
| critic `story` (turn shot moved) | 19 | 21 % | 5 |
| G-CROWD-CLOSE / G-STAGE / G-ROWTEXT | 16 / 8 / 7 | 19 / 12 / 0 % | 3 / 2 / 1 |
| for contrast: G-VARIETY, G-MOVES, G-LAID, G-MOVE | 46 / 13 / 40 / 5 | 67 / 62 / 60 / 100 % | |

- **354 of 966 rung minutes went to rungs whose every refusal was in a class with a cure rate ≤ 38 %.**
- **Fix 3:** route by measured cure rate, the way the batched take ladder already does ("router by measured cure rates", 2026-09-30).
  - A class under 35 % over at least 20 rung verdicts goes to its code cure: G-TWICE has `plan_cures.one_position` and `plan_llm_cures`.
  - The critic's `invented` count or prop has a deterministic cure: drop the uncited count or prop. If the code cure leaves it standing, the class goes to the terminal. It never goes back to the writer.
- **Saves:** overlaps fixes 1-2; the remainder is estimated at 10-20 min per episode. **Hypothesis, 80 %:** the cure rates are an upper-bound measure. Replay the rule on the 48 climbs before building it.

**Downstream stops (not the plan stage, but the rest of the P90):**
- QC reran 4-7 times on ep19, ep20, ep21 and ep24, because each code fix relaunched the episode and every check ran again.
- **Fix 4 (QC memo):** key each QC sub-check (the Whisper "lines heard", cuts, loudness) on its input hashes, so a relaunch with an unchanged master reads the cached result. Assumed to recover half of the QC reruns.
- The rest is discipline that the house already ruled (memory `drive-not-babysit`: no mid-run commits). It is the largest single lever left: removing every rerun puts the P90 at 5.1 h.

### 2.4 The projection (`projection3.py`; P50/P90 by linear interpolation over ep19-27)

| scenario | P50 | P90 | over 6 h |
|---|---|---|---|
| baseline, measured (8-step, pre-cycle-1) | 5.68 h | 7.49 h | 3/9 |
| cycle 1 as built (CK narration, adds high) | 5.60 h | 7.32 h | 3/9 |
| + fix 1 (no fresh_brief) | 5.04 h | 6.92 h | 2/9 |
| + fix 2 (fault-set memory) | 4.26 h | 6.63 h | 2/9 |
| + CK dialogue (if §1 passes) | 4.18 h | 6.50 h | 2/9 |
| + fix 4 (QC memo, half the QC reruns) | 4.01 h | **6.05 h** | 1/9 (ep21) |
| reference: no mid-episode relaunch at all | 3.39 h | 5.09 h | 0/9 |

**Caveats:**
- Fixes 1-2 are counterfactual replays of the record. They hold only where the kept draft is unchanged.
- Fix 1 keeps model_tier, so the two measured model_tier rescues survive. The 1/40 fresh_brief keep may come back as one extra climb.
- What remains over 6 h is **ep21**: 22 launches, 7 QC runs, 4 failed plan runs. That is a discipline fault, not a pipeline cost.

---

## 3. Speed levers not yet benched

### 3.1 What a take's seconds are made of (51 bench renders, `phases_all.py`)

| phase | 8-step (n = 13) | 4-step (n = 32) | note |
|---|---|---|---|
| whole prompt, median | 104 s | 91 s | |
| sampling, median | 66 s (CK8: 29-67 s) | 32 s | |
| decode + save, median | 24.7 s | 25.9 s | **18.2 s per 100 frames**; range 12.9-79.7 s |
| the rest (TE encode, DiT re-upload, LoRA patch, step-1 warm) | **11.3-15.2 s when the TE ran (n = 10)** | 23-47 s right after an arm switch | **2.3-2.9 s when the prompt text was cached** (S4_A1_s2 after S4_CK8_s2; S4_A3_s4_zero, s1_room, s4_room; n = 4) |

The cached-TE runs are a natural experiment that holds the graph fixed. **The TE swap tax is about 9-12 s per render, measured at n = 10 against n = 4.** At ≈ 30 renders per episode, that is ≈ 5 min per episode. This is the ceiling for every lever in §3.2 and §3.3 together.

### 3.2 Keeping the text encoder from evicting H3: there is no flag

- **Sizes on disk:** the DiT `Minimax-h3_Singularity_ref2va_Pruned_v1.3_int8` is 19.53 GB. The TE `qwen3vl_32b_minimax_h3_nvfp4_awq` is 14.61 GB. The video VAE is 4.85 GB and the audio VAE 0.56 GB.
- The engine runs `--reserve-vram 2` on 24 GB. **DiT + TE = 34 GB, and even DiT + VAE = 24.4 GB, does not fit**, so the VAE decode also partly offloads the DiT on every take. That is part of the 2.3-2.9 s floor.
- **ComfyUI 0.36 flags** (`comfy/cli_args.py`):

| flag | what it does here | verdict |
|---|---|---|
| `--highvram` / `--gpu-only` | They pin weights on the GPU and turn off dynamic VRAM (`cli_args.py:321`). The models cannot co-reside, so the result is OOM or thrash. | Reject |
| `--cache-ram` (default) / `--cache-lru N` / `--cache-classic` | These govern node *outputs*, not weights. | No direct gain |
| `--disable-smart-memory` | Offloads more aggressively. | The wrong direction |

- **The one real lever is the output cache.** The TE runs inside `MiniMaxH3ReferenceToVideo` (node 8 takes `clip`, `vae`, ref images and the prompt; read in ep27 `T05.graph.json`).
  - A **prewarm prompt** per take would carry only nodes 5/6/7/18/8 plus a cheap output node, queued for all takes before the renders.
  - It would leave node 8's outputs in the RAM-pressure cache (conditioning plus guide latents, each a few MB).
  - Each take's node 8 would then be a cache hit: no TE load, so no DiT eviction, so the ≈ 2.5 s floor.
  - That is R2_S's "encode-all" without a custom node. The numerics are unchanged (same node, same inputs), so the frames should be bit-identical.
  - The TE encode compute (≈ 5 s per take) is still paid, in the batch. **The net gain is the re-upload and re-patch, ≈ 6-9 s per render, so ≈ 3-4.5 min per episode.**
- **Hypothesis, 70 %:** the RAM-pressure cache keeps 30 node-8 outputs. R2_S saw `UNETLoader` re-run on 5/9 takes after foreign prompts, so the cache does evict.
- **Test (≈ 6 GPU min):** 3 prewarms, then 3 takes. Each take's overhead should be ≤ 4 s and its frames bit-identical to the same take without a prewarm.
- This is an architecture change to the take step (a queue phase), so it goes through the architecture page if it is ever built.

### 3.3 Merged-LoRA UNET (R2_S #3)

- Production BASE has **two** LoRA nodes, the 8-step LoRA at 1.0 and again at 0.7 (`T05.graph.json` node 2 and `lora_second`). That is 208 patches, recomputed on every re-upload.
- The patch time sits inside the 11-15 s measured above. It cannot be separated without the engine log, which `phases.jsonl` (f5316b1) does not split out.
- **Ceiling: −1 to −3 min per episode**, and it overlaps §3.2: once the DiT is not evicted, there are no patches to recompute.
- **Risk:** a 21 GB file baked at a net 1.7 strength, with requant stochastic rounding. It needs a PSNR ≥ 45 dB same-seed check.
- **Rank it below §3.2. Bench it only if §3.2 fails.**

### 3.4 VAE decode

- Decode + save is ≈ 25 s per take. **It is bimodal:** 30/45 renders at 13-20 s per 100 frames (median 16.5), and 15/45 at 20-46 (median 24.5).
- The same S4 shot of 107 frames ran from 15.3 to 31.3 s.
- **Hypothesis, 60 %:** the slow mode is the VAE re-loading or decoding alongside a partly resident DiT.
- **Ceiling if the slow mode is removed:** 1/3 of renders × ≈ 11 s × 30 = **≈ 3.7 min per episode**.
- The TRT VAE (R2_S #4) claims 1.7x, which would be ≈ −4.5 min per episode. That is a vendor claim with a 5 h build and a CUDA 13 TensorRT requirement, so it stays deferred.
- **First step at 0 GPU:** extend `phases.jsonl` to log `VAEDecode` alone from the engine log and correlate the slow mode with the previous node. This is R2_S #5, which was half-built.

**Section verdict:** §3.2, §3.3 and §3.4 together are worth **≈ 5-10 min per episode**, about a third of fix 1 alone. **Do the plan fixes first.**

---

## 4. The two red tests on master

### 4.1 `tests/test_only_reports_read_the_timeline_raw.py`: `book_title.py`

- **Reproduced:** `uv run pytest tests/test_only_reports_read_the_timeline_raw.py` gives 1 failed, `['book_title.py']`.
- **Cause:** 3b38559 (2026-10-10 18:23, the main-title/cold-open work, a peer session). `scripts/episode/book_title.py:194-196` `cold_candidates` reads `ep / "placed.json"` raw to choose cold-open shots from each chapter's shipped `compilation/chapters/epNN_main.mp4`.
- **The obvious fix is wrong.** `door_check.py` ran `episode_home.load_placed` on every shipped timeline:
  - it accepts WotW ep01 and ep08-27;
  - it **refuses WotW ep02-07 and all 14 Scarlet chapters** ("timeline is older than the plan").
  - Routing `book_title` through the door would remove every Scarlet cold-open candidate.
  - The door is right before a render: a plan touched later must not cut. It is wrong for history, because a shipped chapter *was* cut from that file.
- **Minimal correct fix** (the owner of the book-title work lands it; test first):
  1. `studio/episode_home.py` (the one file the lint exempts) gains:
     ```python
     def shipped_timeline(book: Path, number: int) -> dict | None:
         """The timeline a SHIPPED chapter was cut from, read as it stands: history for a
         report or a compilation, never fed to a render of this episode. load_placed refuses
         it once the plan moved after the ship (WotW ep02-07, every Scarlet chapter)."""
         path = home(book, number) / "placed.json"
         return read_json(path) if path.exists() else None
     ```
  2. `book_title.cold_candidates` calls `episode_home.has_timeline` and `episode_home.shipped_timeline` and no longer names the file.
  3. **Test:** a fixture whose plan is newer than its timeline still yields cold candidates through `shipped_timeline`, and the lint file passes.
- Adding `book_title.py` to `REPORTS` instead would be wrong: the file acts (it renders a video), and the lint's allow-list is for printers.

### 4.2 `test_the_plan_script_regenerates_its_plan[20260827135508-ep11]`: the artilleryman

- **Reproduced:** `uv run pytest -k "regenerates_its_plan and ep11"` raises `ValueError: artilleryman: the row does not say ['Thick straight black hair cut short at the sides and falling forward over the brow and eyes']`. The raise comes from `studio/cast_refs.py:290`, and the call is ep11 `plan.py:60` `GUNNER = cast_refs.tag(..., chapter=11)`.
- **Cause: c300c4f** (2026-10-10 21:13, "A row never carries two heads").
  - `pack_refs.character_row` now builds `physical` through `look_table.row_text`. That drops the body's head clauses whenever the chapter's look restates them.
  - The ch11 look `rha_hatless` says "Hatless, his thick black hair falling forward over his brow", so the dossier body's hair clause is dropped.
  - The row today reads "His thick black hair falling forward over his brow. Man of 31, …". The clause is still in `analysis\characters\artilleryman.json` `profile.physical`.
  - The test predates cycle 1 and is not from G-TAIL or the look table: WotW has no look table (`look_timeline.load` returns None), so the legacy path ran.
- **Why not edit ep11:**
  - `tag()` writes the fragments into the plan text, so changing the fragment changes `plan.json`.
  - Regenerating `plan.json` overwrites a shipped file and lapses its signature.
  - `PATCHED_BY_HAND` would be a false record: the plan was not patched by hand.
- **Minimal correct fix:**
  - `cast_refs.tag` has **no caller in `studio/`, `scripts/` or `agents/`**. Only the 20 legacy plan scripts call it (WotW ep01-14, Scarlet ep09-14), and new plans come from `episode_writer`.
  - So widen what it checks a quote against: the current row **or** the card's own words for that chapter (`profile.physical` + `profile.wardrobe[<chapter's look>]`, which is exactly the pre-c300c4f row).
  - The guard's purpose ("refuses any fragment the row does not say … typed descriptions contradicted their rows") stands: a typed fragment is still refused. The two-heads rule governs the row that is staged and judged, and the tag is never staged.
  - **Test first:**
    - a fragment that `row_text` drops but the card says is accepted;
    - a fragment the card does not say is still refused;
    - the ep11 case goes green.
  - **CPU replay:** all 20 plan scripts regenerate byte-identically.

---

## 5. Recommendations for the cycle 2 debate, ranked by minutes per episode per hour of work

| # | item | Δ per episode (median / P90 episodes) | evidence | cost |
|---|---|---|---|---|
| 1 | Fix 1: drop `fresh_brief` | −19 / −44 to −51 min | 41 runs, kept 1/40 | CPU, test-first, 1 commit [arch: ladder rung] |
| 2 | Fix 2: fault-set memory across climbs | −17 / −31 to −55 min | 9 re-climbs, 182 min | CPU, 1 commit |
| 3 | Fix 4: QC sub-checks memoised on input hashes | −0 / −20 to −35 min | QC reruns 4-7× on 4 of 9 episodes | CPU, 1 commit |
| 4 | CK for dialogue (§1) | −6 / −7 min | 3 + 4 renders | ≈ 15 GPU min |
| 5 | Fix 3: cure-rate router | −10 to −20 (hypothesis 80 %) | 354 rung-min on low-cure classes | CPU replay first |
| 6 | Prewarm encode (§3.2) | −3 to −4.5 | n = 10 vs n = 4 phases | ≈ 6 GPU min, then a take-step change |
| 7 | Both red tests (§4) | 0 | reproduced | CPU, 2 commits (4.1 belongs to the book-title owner) |
| 8 | VAE slow-mode logging, then a merged LoRA only if §3.2 fails | −1 to −4 | bimodal decode measured | CPU first |

**Owner ruling needed?** No. Fixes 1-4 hold the P50 near 4 h and bring the P90 to ≈ 6.05 h without loosening any gate; every fault still reaches the same terminal. The remaining P90 episode (ep21) is the mid-episode-relaunch fault that `drive-not-babysit` already rules out.

**Publishable (flag):**
- "Most of an agentic plan loop's wall time is spent after its final answer already exists." 40/48 climbs exhausted the ladder, and 64 % of rung time came after the kept draft. This is a general finding about LLM self-repair ladders, and it is measurable on any judged-generation loop.
- The cached-TE natural experiment (a 9-12 s TE swap tax per ref2va render on a 24 GB card) belongs in the public ref2va bench's phase column.
