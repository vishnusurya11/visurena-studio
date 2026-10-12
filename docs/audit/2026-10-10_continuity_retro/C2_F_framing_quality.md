# C2-F: framing drift and the picture-quality levers still open

Cycle 2, researcher F. 2026-10-11. The work was read-only, done online and on the CPU. No GPU was used, no code or workflow was edited, and nothing was committed.

**Scratch folder:** `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c2\F\`
- Scripts:
  - `measure_shipped.py`: YuNet face height on every shipped ep12-27 panel, with planned size and grid shape
  - `ana.py`, `geo.py`, `hands.py`: the splits and permutation tests
  - `copy.py`, `anchor.py`: does the panel copy its staged place or room picture?
  - `paired.py`: c1 replay against shipped, same shot
  - `crop_demo.py`, `sheet.py`
- Data: `shipped_faces.json`, `shipped_faces2.json`, `copy.json`, `anchor.json`, `paired.json`, `crop_to_plan_demo.json`
- Pictures:
  - `mcu_1x1_vs_2x2.jpg`: 1x1 MCU panels beside their staged picture, and 2x2 MCU cells
  - `crop_to_plan_demo.jpg`: six 1x1 MCU panels, shipped against a crop to plan

**Instrument:** `studio.face_end.faces` (OpenCV YuNet, `studio/models/yunet.onnx`). A face counts at a score of 0.7 or more, which is `panel_dq.PRESENT_SCORE`. `face_h` is the face box height divided by the frame height, so a 1024 cell and a 768 panel read the same. Back views are excluded with `panel_dq.back_view`.

---

## 1. Framing drift: a tight shot is drawn about one size wider than planned

### 1a. What was measured

**The population:** 396 shipped WotW panels from ep12-27, every episode that has `storyboard/layout.json`. Each was read with its plan size and with its grid's shape, taken from `storyboard/grids/*.json`. Only shots with a planned face and no back view are counted.

| planned size | 1x1: n, median face_h (q1-q3) | 2x2: n, median | strip cells (2x1/3x1): n, median |
|---|---|---|---|
| close | 16, **0.350** (.31-.37) | 3, 0.404 | 4, 0.321 |
| medium_close | 55, **0.202** (.17-.25) | 9, **0.263** | 21, 0.21 |
| medium | 8, 0.094 | 31, 0.118 | 55, 0.124 |
| full | 4, 0.070 | 1, 0.101 | 3, 0.101 |
| wide | – | 6, 0.088 | 16, 0.07 |

**What the cut words ask for.** `storyboard_grid.PEOPLED_CUT["medium_close"]` reads "cuts the figure at the middle of the chest; head and shoulders fill the centre". Top of head to mid-chest is about 2 head-heights. Allowing for headroom, the head is about 0.40-0.45 of the frame and the YuNet box (brow to chin, about 0.75 of the head) is **about 0.30**. "close" ("the face fills the panel") implies 0.45 or more.

| planned size | below its floor (floor) | 1x1 below its floor |
|---|---|---|
| medium_close | **65 of 84 (77 %)** (0.26) | 46/55 |
| close | 19/23 (0.40) | 14/16 |

The drawer reads a planned MEDIUM CLOSE as a medium, chest to waist. You can see it in `mcu_1x1_vs_2x2.jpg`: ep16 s13, ep17 s11 and ep24 s8 are waist-up or seated full, while the ep20 2x2 cells are true chest-up shots.

**Paired, same planned shot (c1 replay against shipped)** (`paired.json`):

| shot | shipped | c1 replay | Δ |
|---|---|---|---|
| Scarlet ep14 T04 (MCU, same panel words) | 3x3 sheet cell **0.443** | 1x1 **0.252** | **−43 %** |
| Scarlet ep14 T05 (MCU, same panel words) | 3x3 sheet cell **0.305** | 1x1 **0.171** | **−44 %** |
| WotW ep20 s9 (MCU) | strip 0.19 | 2x2 0.26 | +36 % |
| WotW ep20 s15 (MCU) | strip 0.18 | 2x2 0.27 | +50 % |
| ep20 s16, s17 | strip | 2x2 | ±2 % |
| ep20 s18 | strip | 2x2 | +14 % |
| WotW 1x1 replays (ep21 s24, ep22 s5, ep27 s22, ep26 s15) | | | medium and wide only: mixed (+87 %, −10 %, −55 %, −14 %). They cannot speak for MCU. |

The WotW c1 1x1 seam replays were mediums, inserts and wides. **None of them planned an MCU**, so the drift CYCLE_1 saw on Scarlet has no WotW 1x1 MCU replay to confirm or clear it. The population above stands in for one.

### 1b. What it is, and what it is not

| Candidate cause | Test | Result | Grade |
|---|---|---|---|
| **The drawer undershoots every tight size, whatever the grid shape** | face_h against the size's cut words, 84 MCU and 23 close panels over 16 episodes | 77 % of MCU under 0.26 and 83 % of close under 0.40, in 1x1, 2x2 and strips alike | **95 %**: measured on the artefact, many episodes, and the paired Scarlet cells |
| **A 1x1 draws wider than a 2x2 for the same size** | Scarlet paired, same words: −43 % and −44 %. WotW MCU 1x1 against 2x2: 0.202 vs 0.263, permutation p = 0.005 (n = 42 vs 9; 5 of the 9 2x2 cells are ep20). Against all multi-cell shapes: −7 %, p = 0.24. Episode-matched: the multi-cell is tighter in 5 of 8 episodes. | Real on 2 independent sets, but the WotW 2x2 sample is small and clustered | **about 85 %**: below the bar on its own. The commit-3 world is only 1x1 or 2x2, so this matters. |
| The staged room or anchor picture is copied (the chain) | `anchor.py`: 1x1 face_h against the face size of its staged anchor | Chained MCU 0.203 vs unchained 0.188. Rank correlation with the anchor's face size is −0.07. | **Refuted.** The layout correlation with the staged picture is high for 1x1 tight panels (0.56-0.60 vs 0.14-0.25 for cells, `copy.py`). The background repeats, but face size does not follow. |
| The setup's wide GEOMETRY is appended to a tight 1x1 prompt | `grids.prompt_for` passes `place_words(here)` for every grid. `grid_prompt_v2` adds it even when every shot is TIGHT, although `brief_place` already drops the description for TIGHT. That is the G-SCALE fault, carried into the grid prompt. | 1x1 MCU with geometry in the prompt 0.201 (n = 42) vs without 0.250 (n = 13), p = 0.02. **But** the 13 without geometry are all ep12-14, from before `place_words` existed, so other changes are confounded. | **Hypothesis (70 %)**. It is in the code and plausible. It needs the arm in 1c. |
| Prose that names hands, lap, seated or held objects pulls the frame down | `hands.py` | MCU: no effect (0.207 vs 0.209). Close: 0.307 vs 0.367, p = 0.03 (n = 8/15). | Hypothesis for close only. Logged. |
| The canvas: 1x1 is 1 MP (1024²) while a 2x2 is 4 MP, which is Qwen-Image 2.1's native 2048² | Not separable on CPU | The only remaining difference in the Scarlet pair, where the words were identical | **Hypothesis**. It is the arm in 1c (2048² 1x1). |

**Why this is a quality issue and not only a framing one.**
- H3 copies the panel's framing; memory `h3-obeys-direction` and the Scarlet T04/T05 takes in `contact_T04_T05.jpg` show it.
- A planned MCU face box today is a median of 0.20 × 768 = **155 px** in the take.
- At the planned framing (0.26-0.30) it would be **200-230 px**. That is a 1.3-1.5x linear gain in face pixels.
- That is **the same gain the 992 canvas buys (992/768 = 1.29x), at zero minutes.**
- The owner's "low quality" is judged mostly on faces. Faces drawn one size too small throw away the very pixels 992 was meant to buy.

### 1c. Proposed fix (test-first, in this order)

1. **G-FRAME, a measurement first (CPU, advisory).**
   - Write the planned size's `face_h` into `panel_dq.json` for every faced, non-back panel.
   - Flag an MCU under 0.22 or a close under 0.32. Those floors sit below today's medians on purpose; they are a first wall. Calibrate them on the owner-judged episodes before anything goes hard (memory `constants-outlive-their-world`).
   - Architecture: one more check in an existing panel gate. Update GATES.md and the page.
2. **A tight-size words arm on Qwen (GPU, about 12 min).**
   - Take eight shipped 1x1 MCU shots at their shipped seeds: ep14 s22, ep14 s24, ep16 s13, ep17 s8, ep17 s11, ep19 s19, ep23 s2, ep24 s8. Draw four arms:
     - (a) v2 control: a re-draw, checked bit-exact
     - (b) no geometry: `place_words` dropped when every shot in the grid is TIGHT, the G-SCALE rule extended to the grid prompt
     - (c) (b) plus the size said one notch tighter in a single picture ("CLOSE-UP ... cuts at the collarbone")
     - (d) v2 words on a **2048² 1x1** canvas, downscaled to 1024, which tests the canvas hypothesis
   - That is 32 draws: about 20 s each warm at 1024 and about 70 s at 2048.
   - **Adopt** the arm whose median face_h is 0.25 or more with no content loss. Content is checked with `panel_content` on the plan's named objects, the seam check, and people_check.
   - Per episode: (b) and (c) cost +0. (d) costs about +1 min per 1x1 tight shot, about +5-8 min per episode.
3. **Crop to plan (CPU fallback, needs the owner's eye).**
   - When a single-face tight panel is still under its floor, crop the 1024 cell around the face by at most 1024/768 = 1.33x, so the 768 H3 panel is still a downsample, and re-run `panel_content`.
   - `crop_to_plan_demo.jpg`: on six shipped MCU panels the face rises from 0.17-0.20 to 0.23-0.26 (132-157 px → 177-199 px at 768) at no GPU cost.
   - **But it drops planned business at the lower edge:** the ep17 s11 coins in hand, the ep17 s8 bag, and half the ep14 s24 newspaper.
   - So it is a cure only where `panel_content` still finds every named object after the crop. It is a crop, not a composite.

---

## 2. Quality levers left open: evidence, cheapest arm, and minutes per episode

The baseline is 5.7 h per episode (CYCLE_1 projection: 8-step BASE, CK8 on narration). The ceiling is 6 h.

| Lever | Measured evidence so far | Cheapest GPU arm | Per-episode time | Call |
|---|---|---|---|---|
| **Framing to plan (new, §1)** | 77 % of MCU under floor. Face px 155 → 200+ at plan, the same gain as 992. | §1c-2: 32 Qwen draws, about 12 min | +0 for words; +5-8 min for 2048 1x1 | **First.** The cheapest face-pixel lever found so far. |
| **P-WORDS** (grid v3: keep the `<imageN>` style citation and "angular stylised 3D"; replace "flat high-chroma colour" with per-surface material + wear + named light) | **None measured.** BENCH_r2 block 7 was cut. R2_P had only reasoning: Qwen obeys "flat" literally. The texture ruler votes for mosaics and does not count. | Redraw the 5 grids that own S3/S4/S6/D1/D2 plus one night exterior (ep25 fulham_road, for memory `walls-follow-the-chapter`) at the shipped seeds with v3 words: about 9-10 min. Add two 768 takes (S4, S6) on the v3 panels: about 5 min. | **+0** (same graph) | **A LOOK change: owner's eye only** (R2_verdict). It goes on the sheet in §3. |
| **992 canvas** | BENCH_r2 block 5, **on 4-step shift6-beta, not production**: whole prompt 1.59x, s/it 2.2-2.5x (partial offload on S3 and D2), identity −0.025 (S4) and −0.038 (S6), mean banding 0.311 vs 0.285. The S3 frogs were kept. By eye (`faces_B5_canvas.jpg`), D2 came back **framed wider** and not visibly sharper. Never measured on the 8-step production base. | S4, S6, D1, D2 on BASE 8-step at 992 with 992 panels cut by `panels.cut`, not a centre re-cut: 4 renders, about 20 min | **+45 to +65 min** (projection: r2's 2.2-2.5x s/it applied to c1's 8-step sampling of 66-121 s, plus decode +8-12 s, over 30-36 renders). That gives **≈ 6.5-6.8 h, over the ceiling**. | **An owner budget ruling** (CYCLES: a trade over 6 h). It goes on the same sheet. A 992 only for face-led tight shots would cost about a third of that. |
| **G2** (8-step LoRA ×2 at 6 calls on its own grid: `ManualSigmas 1, .9730, .9231, .8780, .8000, .6316, 0`) | **None.** Deferred in C1 (`C1_G` estimates about 70 % content kept). | First a CPU commit: `h3_arms` lays `ManualSigmas`, and `knobs()` reads the sigma string, or the arm runs beta-8 and reports "no change". Then 7 renders (the six + S3 seed 2), about 20 min, judged against A1 under the calibrated rule plus G-TAIL. | **≈ −8 min** (C1_G's −12 min is against pre-CK8; CK8 already removed about 40 % of narration sampling) | A **speed** lever, not a quality one. Worth it only to fund a quality lever (992 or the 2048 1x1). Any schedule change has made invented tail speech before (BENCH_r2 §5), so G-TAIL must pass. |
| **Subject noun first** (`fresh_prompt` "A man of 34 with …") | One bearded ghost face (C1_L, 55 %). Since then: the beard was cured by marker words (3/3), and the ghost face was traced to the USDU tile pass (CYCLE_1 block 1b). | 3 Krea draws × 2 arms, about 4 min | +0 | **Drop to a log line.** The fault it targeted has a measured cause elsewhere, and it is not a lever on the owner's complaint. |

**One time trade worth naming.** Qwen-Image-2.1-Turbo is an official Alibaba 8-step checkpoint, 2026-10-09 (§4).
- Today's grids run 25 steps. The checkpoint could return a large share of the grid minutes (E's grid median is about 70 s per draw, about 14 draws per episode).
- That time could **fund** 992 or the 2048 1x1. It is a picture change, though, so it needs its own eye sheet.
- It is not bundled here.

---

## 3. The owner-eye sheet: P-WORDS and 992 in one look

**File:** `bench_evidence\c2\C2_owner_words_992.jpg`, with a `review\` folder of the takes carrying the recorded line.

**GPU:** about 35 min. Grids about 10, 992 takes about 20, v3 takes about 5.

**Rows:** five shots, all in the replay set, so the controls already exist.

| row | shot | panel source (owning grid, shipped seed) | why |
|---|---|---|---|
| 1 | S6 = WotW ep27 T03 | ep27 `study_table` 2x2 | the owner-bad study; narrator MCU dialogue |
| 2 | S4 = ep24 T12 | ep24 grid owning shot 12 | two men, MCU, the smoke column |
| 3 | D2 = ep27 T25 | ep27 `study_reverse` 1x1 s25 | the wife, longest take; the worst VRAM case at 992 |
| 4 | D1 = ep25 T21 | ep25 grid owning shot 21 | the bearded look (cycle 1's beard) |
| 5 | S3 = ep24 T05 | ep24 grid owning shot 5 | frogs, a wide: content and texture on ground and water |
| (6) | ep25 `fulham_road` night exterior | its grid | panel only: does material wording over-texture a night sky? |

**Columns:** every tile is the same display size. Face tiles are 1:1 crops of the readable face box at 50 % of the take, scaled so the face box is the same height in every column, which is how `contact.py faces` lays them out.

| A | B | C | D | E |
|---|---|---|---|---|
| shipped panel, v2 words (768) | **P-WORDS v3** panel, same seed (768) | take face at 768, production 8-step (the existing A1 render) | take face at **992**, production 8-step (new) | take face at 768 on the **v3 panel** (rows 1-2 only, new) |

**Under each row, measured:**
- face px in the take
- identity against the sheet (median)
- banding
- clones
- G-TAIL
- whole-take seconds

**The header states each choice's price:**
- P-WORDS: +0 min per episode, a LOOK change.
- 992: about +45 to +65 min per episode, which puts the episode at 6.5-6.8 h.

**How the owner reads it:**
- **A | B** (and C | E) is the P-WORDS ruling: does the material wording read as better painting, or as a different style?
- **C | D** is the 992 ruling: is the face visibly better, and is it worth about an hour per episode?
- A strip beside row 1 shows the same panel's crop-to-plan (§1c-3). Tighter framing gives the face the same 1.3x more pixels as 992 at 0 min. Without it the owner would be judging 992 against a face that is too small for a reason that has nothing to do with the canvas.

**Bench preconditions** (memory `a-fix-that-changes-nothing`):
- The overlay asserts width/height 992, and ffprobe reads 992x992.
- The 992 panels are cut by `panels.cut` from `storyboard/shot_NN.png` and resized to 992, not centre-cropped as in r2.
- The v3 grids record `prompt: v3` in their json.
- Dialogue stays on BASE, not CK8.

---

## 4. Online, 2026: anything new on H3 ref2va quality since round 2 (dates verified on the page)

| Date | Item | What it means for us | Call |
|---|---|---|---|
| **2026-10-03/05** | **Veda sparse attention** for H3, an official ComfyUI node (veda-sparse/Veda-on-ComfyUI). It skips about 90 % of attention tiles. Measured 2.9x end-to-end on an RTX 5070. The predictor repo reports **1.77x on an RTX 4090** (5 s clip) and 2.4-2.8x on longer clips. **Not yet verified on 40-series.** Its R2VA example uses a **T2VA-trained predictor**; an R2VA fine-tune is "announced". Needs **ComfyUI ≥ 0.38** (we run 0.36). It must not be combined with core sparse attention. | The first speed lever large enough to pay for 992 (the 992 penalty is about 2.3x s/it; Veda claims 1.8-2.8x back). It needs an engine upgrade, which is an owner install window, and a quality bench, because sparse attention on reference frames is unproven. | **Watch.** Bench it once the R2VA predictor ships, in its own window. |
| **2026-10-09** | **Qwen-Image-2.1-Turbo**, official Alibaba 8-step at CFG 1, repackaged by Comfy-Org. Multi-reference edits are said to "work the same way as the base". No quality numbers. | Grid time, not take quality (§2). It is the lever that could fund the 2048 1x1 or 992. | Cycle 3 arm, with an eye sheet. |
| 2026-10-07 | Qwen-Image-2.1 **Next-Scene LoRA** (akhaliq, rank 64, "Next Scene:" + camera direction, trained at 512 px, grain builds up over hops). | A chained "camera pushes in to a medium close" from the setup's anchor is a framing lever in principle. It is trained at 512, its licence is not stated, and portraits are "out of scope by design". | Log only. |
| 2026-10-02 | **DMAD** 4-step H3 audio-video LoRAs (Texas A&M / ByteDance). Claims 79 % preference over DMD2. **T2AV only, no ref2va**; Kijai's rank-reduced conversion; licence not stated. | Not for ref2va. | Cut. |
| 2026-10-06 | **FastH3 Trim** (pruned FastH3 V2). T2V only, quality loss admitted. | Not ref2va (FastH3 was rejected on 2026-09-16). | Cut. |
| 2026-09-30 | **H3 X2 Detail VAE** (5.2 GB, experimental). A 2x decode via PixelShuffle, plus a detail node that sits **before** R2V on the reference image. Its own note: the detail gain "cannot be reproduced from the standard generated H3 latent alone". No licence, no 4090 timings. | A 2x decode could replace the 768→1536 Lanczos/RTX VSR delivery step. The detail node edits the reference picture, which is a look change. | Low evidence. A cycle-3 candidate for delivery only, A/B against RTX VSR. |
| 2026-08-11 (not in any repo doc until now) | **H3 FL2VA/Ref2VA hybrid merge** (ANe5s, GPL-3.0 loader). The FL2VA base with Ref2VA `adaln_proj` overlaid on later blocks. Author's screenshots only; "small risk of fitting extra objects". | It replaces Singularity, the house's duplicate fix, with an untested base. Extra objects are our worst fault class. Needs another 21 GB checkpoint. | Cut. |
| ~2026-09-18 | Singularity **v1.3 w4a8** (11.8 GB). There is no version newer than v1.3. The newest commit was 23 days ago. | A memory or speed variant only, and w4a8 on Ada is unproven. | No change. |
| ~Sept | lightx2v: the Ref2V **8-step 768p v1.0** (already production), FL2V 4-step v1.2 (FL2V only). There is no new Ref2V LoRA in the last month. Community reports on Ref2V 8-step quality are mixed (#49, #51). | Nothing new for ref2va. | No change. |

**Bottom line:** no new ref2va **quality** lever has been released since round 2. The new items are speed (Veda, Qwen Turbo) and delivery (X2 VAE). Their value is in funding 992 or the 2048 1x1, not in replacing them.

---

## 5. What I would act on at 95 %, and what stays a hypothesis

| Claim | Grade |
|---|---|
| Tight sizes are drawn about one size wide in every grid shape (77 % of MCU under 0.26; median 0.20 against about 0.30 asked) | **95 %**: 16 episodes plus the Scarlet pair |
| A 1x1 is wider than the same words in a multi-cell grid | 85 %: Scarlet −43 %/−44 % paired; WotW against 2x2 p = .005, small n. The §1c-2 arm (d) settles it. |
| The room or anchor chain causes it | **Refuted** (rank corr −0.07) |
| Wide geometry in a tight 1x1 prompt causes it | 70 %: in the code, but confounded by era. Arm (b). |
| Framing to plan is worth what 992 is worth in face pixels, at 0 min | arithmetic plus the crop demo. The owner's eye on the sheet strip decides. |
| P-WORDS, 992 | **owner rulings** (look and budget). One sheet, about 35 GPU min. |
| G2 | speed only, about −8 min. Bench only if a quality lever needs the minutes. |
| Subject noun first | dropped to the log |

**Publishable (flag):**
- "Planned shot size against drawn face height" across 396 storyboard panels is a measured framing undershoot for an instruction-following image model. Add the arm (b)/(c)/(d) results and it becomes a benchmark of how Qwen-Image 2.1 obeys shot-size words by canvas and grid shape.
- It sits with the public ref2va bench already planned.

**Sources** (checked 2026-10-11):
- https://comfyui-wiki.com/en/news (index)
- https://comfyui-wiki.com/en/news/2026-10-05-veda-sparse-attention
- https://comfyui-wiki.com/en/news/2026-10-09-qwen-image-2-1-turbo
- https://comfyui-wiki.com/en/news/2026-10-07-qwen-image-2-1-next-scene-lora
- https://comfyui-wiki.com/en/news/2026-10-02-dmad-h3-4step
- https://comfyui-wiki.com/en/news/2026-10-06-fastvideo-fasth3-trim
- https://comfyui-wiki.com/en/news/2026-09-30-h3-x2-detail-vae
- https://comfyui-wiki.com/en/news/2026-08-11-minimax-h3-fl2va-ref2va-hybrid
- https://github.com/ANe5s/ComfyUI-MiniMax-H3-Hybrid
- https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity/tree/main
- https://huggingface.co/lightx2v/Minimax-h3-Turbo/discussions
