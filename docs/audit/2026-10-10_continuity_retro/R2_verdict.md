# R2 verdict: round-2 skeptic on R2_Q (faces/texture), R2_S (speed), R2_P (panel)

Skeptic, round 2, 2026-10-10. Read-only. Nothing was rendered, installed or switched. I edited nothing except this file.

**Inputs:**
- `R2_Q_faces_texture.md`, `R2_S_speed.md` and `R2_P_panel.md` (the three round-2 reports)
- `S_skeptic_verdict.md` and `BENCH_phase0.md` (round 1)
- `.claude/skills/episode/LESSONS.md`

**Code read:**
- `studio/h3.py`
- `scripts/episode/{takes_r2v,panels,grids}.py`
- `studio/{storyboard_grid,refs_pack,episode_gutter}.py`
- `scripts/bench/h3_arms.py`
- ComfyUI 0.36 `comfy_extras/nodes_minimax_h3.py`, `nodes_model_advanced.py`, `comfy/ldm/modules/attention.py`, `comfy/model_patcher.py`, `comfy/samplers.py`
- KJNodes `PathchSageAttentionKJ`

**Scratch scripts** (both CPU only):
- `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\r2v\sig2.py` recomputes the sigmas.
- `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\r2v\seam.py` scans the panels for seams.

---

## 0. The claims, checked against the code

| # | Claim | Verdict | What I found |
|---|---|---|---|
| 1 | R2_Q §0a: the 768² canvas is our own ceiling. The R2V node honours width/height, and `studio/h3.py` misapplies the reference-video rule. | **TRUE in source. The probe must confirm it.** | `MiniMaxH3ReferenceToVideo.execute` calls `_empty_av_latent(width, height, length)` verbatim (line 291). `adapt_canvas` is called only in the `ref_videos` branch (line 320). That has been so since the first commit, 57500fc5b (2026-08-02): line 241 there is also the ref-video branch. `studio/h3.check_canvas` refuses any output canvas that is not a fixed point of `adapt_canvas`, so `canvas.size()` can only return 768² for 1:1. The house template's own default, 1280x736, is not a fixed point either, which fits "honoured verbatim". **Not explained:** commit ba7eb9c's evidence ("640x384 … rendered 1280x768"). Something in the trailer graph of that day rewrote the canvas. It was probably a ref video, or the H3-Turbo custom node, but that is unproven. A 1-minute probe settles it. Until the probe reads 992x992 on ffprobe, `studio/h3.py` is not touched. |
| 2 | R2_Q §0b: the sigma table, and the claim that beta@12 is off the distillation grid | **TRUE (recomputed exactly)**. The direction of the effect is speculation. | My recompute matches the 8-step rows to the third decimal. The report left out the rows that matter, because **production is moving to 4 steps**: **4-step today (shift 12, beta): 1, .983, .923, .721.** shift 12 simple: 1, .973, .923, .800. shift 6 beta: 1, .966, .858, .563. shift 6 simple: 1, .947, .857, .667. A3's last model call is at σ 0.72, so the final Euler step jumps from 0.72 to 0. That is a plausible mechanism for phase 0's finding that A3 lost texture on 4/6 shots, decayed faster at the tail, and dropped the S3 frogs. Two things are unknown: the 4-step v0.1 LoRA's own schedule contract (R2_Q researched only the 8-step one), and whether "beta" reads as the facets. `simple@12` moves the last call **up**, to 0.80. That is softer and is the old house note "simple = softer". It is the wrong direction for 4-step and is cut (§1). |
| 3 | R2_Q §0b / risk: a shift change touches audio | **TRUE, and stronger than stated** | `ModelSamplingAV.audio_scale = shift / audio_shift`, so 12/3 = 4 and 6/3 = 2. The DiT derives the audio schedule from the video shift (`MiniMaxH3SigmaShift`). A shift arm is therefore also an **audio arm**, and lip lag on all 4 dialogue takes is a hard gate for it. |
| 4 | R2_P §0.2: at cfg 1.0 the grid negative does nothing | **TRUE, but not new** | `LESSONS.md:175` already records it: "The grid negative prompt is inert at CFG 1.0". The house's anti-duplicate wording already lives in the **positive** (`storyboard_grid.no_duplicates`). P-GUIDE's selling point ("the only lever that attacks duplicates, through the live negative") is therefore stale. |
| 5 | R2_P §0.3: ep27 shipped a seam into H3 | **TRUE, and wider than reported** | I scanned all 572 WotW `storyboard/h3/shot_*.png`. **18 panels in 9 episodes** have a full-length line at ≥250 luma over ≥95 % of its length: ep07 12/13/14, ep14 07, ep19 17/18, ep20 09/15, ep21 22/23/24, ep22 05/09, ep25 09/20/22, ep27 10/16. I opened two. **Both are cells drawn as two pictures:** ep19 shot 17 is the pit scene stacked twice (two handling-machines, two pairs of men), and ep27 shot 10 is the narrator at the desk next to a second copy of the desk. **This is a duplicate-figure source as well as a seam.** `episode_gutter` searches only the outer 8 % of each edge (`MAX_FRAC`), so an interior split passes. |
| 6 | R2_S #1: core `ModelAttentionBackend` scopes CK int8 attention to one graph | **TRUE** | The node is at `nodes_model_advanced.py:374` (experimental). The "comfy kitchen attention" option is offered only when `COMFY_KITCHEN_INT8_ATTENTION_IS_AVAILABLE`. It sets `transformer_options["optimized_attention_override"]` on a clone. Every core attention function is `@wrap_attn` and honours that override. H3 calls `optimized_attention(..., transformer_options=...)` (`ldm/minimax/model.py:199`). Node 4 copies `transformer_options`, so the key survives. KJ node 3 at `disabled` returns the model untouched (`if sage_attention == "disabled": return model,`), so it does **not** clobber the override. The engine today is PID 43272 with `--windows-standalone-build --reserve-vram 2`, with no CK flag (read just now). **No relaunch and no install. Scarlet's jobs are untouched.** That removes the blocker that killed B-4 in phase 0. |
| 7 | **(new) The bench overlay would silently drop half of these arms** | **BLOCKER, fix before any GPU** | `scripts/bench/h3_arms.arm_graph` copies only `MODEL_NODES = ("1","2","lora_second","3","4")`, plus `steps` from node 9 and the save keys. It does **not** copy node 9's `scheduler`, node 11's `sampler_name`, node 8's `width/height/ref_image_size`, or any new node id such as the attention node. `knobs()` asserts none of them. A `simple` arm would run `beta`, a 992 arm would run 768, and a CK arm would be missing its node. All three would come back as "no difference": memory `a-fix-that-changes-nothing`, in the instrument itself. |

---

## 1. Arm by arm

| Arm (source) | Call | Why |
|---|---|---|
| **R2_S #1: CK int8 attention via `ModelAttentionBackend`** | **BENCH, first** | Free, scoped, reversible by a name, and verified in source (§0.6). Expected −9 to −13 s per take. Its risk is numerical (int8 Q·K), so judge it by non-inferiority plus PSNR against the deterministic A3 control. Watch the compiler's "graph breaks" count in the log. |
| R2_S #2: Sage 2.2 post6 cu130 wheel | **CONDITIONAL (only if CK fails)** | It is an environment change on the shared engine, and it needs the engine stopped. The pv_fp16 kernel needs triton, and triton-windows 3.5 against torch 2.11 is an unproven pair. The gain would be the same as CK's. The owner allows it with a rollback, but only use it if CK fails quality or gains under 15 %. The install happens in its own window, with the post5 wheel kept locally first. |
| R2_S #3: bake the 4-step LoRA into a 21 GB int8 file | **DEFER** | −1 to −3 min per episode, and R2_S calls that "the least certain number". It is a new 21 GB artefact that must be re-baked whenever Singularity or the LoRA changes, and it pins 4-step before 4-step has passed its production tripwire. First let #5's phase table show that the "prepared → first step" gap is ≥ 4 s of patching. |
| R2_S #4: TRT VAE | **DEFER** (agree) | Vendor claim only. A 5 h build, CUDA 13 TensorRT, and a grid bug fixed only on `main`. |
| **R2_S #5: per-phase timing record in the take step** | **ADOPT NOW (CPU, test-first)** | It is the instrument for the production tripwire and for every speed claim. Without it a speed arm is an estimate forever. |
| **R2_Q #2: schedule** | **BENCH, re-scoped to 4-step:** shift 6 beta and shift 6 simple. **CUT** `simple@12` and `er_sde`. | The production take is moving to 4 steps, so an 8-step schedule result would not transfer. `simple@12` raises the last σ (0.72 to 0.80), which is the softer direction and the opposite of the cure being sought. `er_sde`: one tester note on a different LoRA family, and the house's own 2026-08-07 "disco lights" from a non-euler sampler on a distilled LoRA. The house's earlier 6/3 run (`takes_r2v` docstring, iteration 3) was on the FL2VA-row LoRA, so 6/3 on the ref2v LoRAs is **unmeasured**, not refuted. A shift arm is an audio arm (§0.3), so lag is a hard gate. |
| **R2_Q #1: native canvas 992²** | **BENCH, after a 1-minute probe, on the schedule winner.** 896 only as a fallback. | It is the only lever that adds face tokens inside generation, and the mechanism is verified. Three attacks. (a) **Off-distribution risk:** the vendor's own `adapt_canvas` encodes short edge = 768, so 992 short edge may never have been trained. Above-trained resolution is a classic cause of **doubled subjects**, our worst fault, so clones stay at 0 and the production tripwire watches it. (b) **It spends the 4-step saving:** +45 s per take, about **+22 min per episode** (§4). (c) **Adoption is not one line.** It needs `studio/h3.py` (an area rule for the output canvas, `adapt_canvas` kept for ref videos), `canvas.size`, `panels.NATIVE`, assemble's non-integer 992→1536 (or 1984 delivery), and every px-unit threshold. That makes it an architecture-page change. The bench must stage **992 panels re-cut from the 1024 `storyboard/shot_NN.png`**. They exist on disk. A 768 panel under a 992 canvas tests the wrong thing. |
| R2_Q #4: `ref_image_size` max | **CONDITIONAL** | Low evidence, off the LoRA's distribution, and largely subsumed by 992 (`match` already gives refs 1.67x the area). It runs only if the probe says 768 is forced. It is then the only in-generation face-pixel lever left at 768. |
| R2_Q #5: larryvrh v4 EMA-600 | **CUT** | FL2VA/T2V lineage. Its v1 sibling (ckpt850) is the **measured camera-scale pumping** of ep01 (2026-09-10, `takes_r2v` docstring), which is why the house moved to the ref2v LoRA. It deletes `lora_second`, but phase 0 kept x2 over x1 on 4/4 shots and saw a grey-narrator look fault with x1. It runs 8-step, which gives back the 4-step saving. "Complex prompts get ignored" collides with "H3 obeys direction" (camera verbs are our control surface). Evidence: an author claim plus one tier note. |
| R2_Q #3: H3-FaceRefine | **DEFER (phase 4) and owner ruling** | Its stitch-back pastes a second render's face pixels into the take with a feather, which is a composite under the owner's "never composites" ruling (S cut `keep_head` for the same reason). It installs insightface and scenedetect into the shared `python_embeded`, where onnxruntime CPU+GPU are both present and its README warns identity then runs on CPU. It re-renders the mouth at 0.35-0.40 denoise, so lip lag is at risk. It costs +10-25 min per episode, which cannot coexist with 992. Evidence is README frames only. |
| R2_P §0.1 + **P-WORDS** (drop "flat / simplified / poster / angular", add material words) | **OWNER-EYE SHEET ONLY, never auto-adopted** | "Angular stylised 3D with brush-stroke colour texture" is **the house style the owner chose** (WotW refs style, Krea2 + Cinematic, owner pick 2026-09-18; `refs_pack.STYLE_LEAD` "heavily angular"; `storyboard_grid.STYLE_V2`). Changing those words is a **LOOK change**, not a quality fix. R2_P's best point stands, and the owner should hear it: Qwen obeys "angular / flat" literally, while Krea2 paints it. The owner's "faceted faces" complaint may be his own style words reaching a more literal model. Also: memory `walls-follow-the-chapter` (material words written for an interior chapter over-texture a night sky), and v1 → v2 already measured "describing the style in words bought nothing" for slot citation. If anything is drawn, the minimal variant keeps "angular stylised 3D" and the slot citation, replaces only "flat high-chroma colour" with per-surface material words, and is shown side by side. The texture ruler does not vote: it voted for the mosaic. |
| R2_P P-GUIDE: cfg 2.5 + APG + FreSca | **DEFER** | Doubles grid NFE (+12-18 min). The Comfy docs say cfg 2 "over-sharpens edges", which is the facet complaint itself. Its duplicate-negative premise is stale (§0.4). Six panels cannot show a duplicate-rate change (S §2, rare events). |
| R2_P P-RESTORE-MASKED | **DEFER and owner ruling** | Pasting the original face boxes back over a refined panel is a feathered composite with seams at hat brims and collars. It needs a 152 MB LoRA, a new step and a face-box dependency. Its identity safety holds by construction only if the owner accepts the paste. |
| R2_P P-FIX (e-n-v-y) | **CUT** | No licence tag, a single author, users dispute whether the LoRA or the settings does the work, and it may pull photographic. |
| R2_P P-NATIVE (1x1 at 1536 per shot) | **DEFER until R0c** | It touches the 2026-09-28 one-room ruling (25 separate re-imaginings of a room, unmeasured). R0c, the CPU layout check, still has not run. |
| R2_P §0.4: Qwen 2.1 research licence | **FLAG ONLY** | It applies to the grids that already ship. The owner's attorney decides, not this audit. |
| (round 1) A4 stock fp8 | **DROP from this bench** | A reference, not a candidate: Singularity is kept for the duplicate fix. It costs a 19.5 GB HDD load for a diagnostic. |

---

## 2. Adopt now, without a bench (CPU, test-first, $0)

1. **The interior seam / doubled-cell check on panels.** For each `h3/shot_NN.png`, flag any column or row whose pixels are ≥ 250 over ≥ 95 % of its length (the same pale-and-flat family as `episode_gutter`, but searching the whole panel, not the outer 8 %).
   - It is a hard panel fault. The cure is a redraw of that cell with a seed bump; panel redraw is the measured 1/1 cure. That is a code cure, not a writer loop.
   - **Acceptance on the artefact:** it fires on the 18 WotW panels listed in §0.5, and a person reads all 18 to confirm or clear them, with any false positives counted. Two are already confirmed as doubled pictures. Then it runs on the next book's first episode.
   - Architecture: one more check in an existing panel gate. Update `GATES.md` and the page's gate list in the same commit.
2. **The per-phase take record (R2_S #5):** encode, first-step gap, s/it, steps, decode+save, and whether the UNET/TE node re-ran. Write it to `timing.jsonl`. It is the tripwire's clock.
3. **Fix the bench overlay before the GPU window (§0.7).**
   - `arm_graph` lays node 9 `scheduler`, node 11 `sampler_name`, node 8 `width/height/ref_image_size`, and any arm-only node id (the attention node) over the shipped graph. It also rewires node 3's `model` input to it.
   - `knobs()` reads and `assert_knobs` checks `scheduler`, `shift_video`, `shift_audio`, `sampler`, `width`, `height`, `ref_image_size`, the attention backend, and the staged panel's pixel size.
   - After each run, ffprobe the output's dimensions.
   - A test per knob: an arm claiming `simple` must fail the assert on a `beta` graph.
4. **A face-crop sheet tool** (`scripts/bench/contact.py` extension). For each readable face box at 8/50/92 %, put a 1:1 crop of every arm side by side at the same display size. This is the owner's deliverable, not a gate.
5. **No change to `studio/h3.py`** until the probe reads 992x992. The ba7eb9c observation (640x384 → 1280x768) is unexplained, and that is a reason to measure, not to trust the source reading.

---

## 3. The bench: one ordered window of about 1 h 45 min of GPU

**Base for every arm:**
- A3: `video_minimax_h3_r2v_turbo_ref8_ref4_singularity`, which is Singularity v1.3 int8 + 4-step v0.1 @1.0, 4 steps, shift 12/3 beta, euler, CRF 10.
- That is the graph that will ship. Quality arms measured on the 8-step A1 would not transfer.

**Controls:**
- Phase-0's A3 renders are reused, not re-rendered. They are `S2/S3/S4/S6/D1/D2_A3.mp4` and the `_s2` seeds, in `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\bench\runs_b1\`.
- Determinism (A1 equalled A0 byte-for-picture) is re-proven with **one** control re-render.

**Shots:** the phase-0 six, same shipped ran graphs, same seeds.

| Shot | Source | What it tests |
|---|---|---|
| S2 | ep03 T11 | refs-only, narrator at the gate |
| S3 | ep24 T05 | frogs wide: content retention, tail decay |
| S4 | ep24 T12 | two-man MCU, 107 f |
| S6 | ep27 T03 | dialogue, 141 f; the owner-bad study |
| D1 | ep25 T21 | dialogue, 90 f; A1 had 2 clone frames |
| D2 | ep27 T25 | dialogue, 175 f; longest, VRAM worst case |

| Order | Block | Arms × shots | Renders | GPU min | Stop rule (checked before the next block) |
|---|---|---|---|---|---|
| 0 | Engine check | queue empty, no foreign prompt queued, engine flags as above, `/object_info/<Node>` only (phase 0 §9 incident) | 0 | 1 | A foreign job is queued: wait, never kill. |
| 1 | **Canvas probe** | A3 graph, node 8 at 992x992, 22 frames | 1 | 1 | ffprobe ≠ 992x992: block 5 becomes `refmax@768` × 6. |
| 2 | **Determinism** | A3 control re-render on S4 | 1 | 2 | Frames differ from phase-0 S4_A3 (PSNR < 45): controls are void. Re-render all 6 controls (+10 min) before anything else. |
| 3 | **CK attention** | `<A3>_ckattn_comfyorg` × 6 | 6 | 11 | **Out if:** sampling s/it gain < 15 %, or graph breaks rise, or PSNR vs control < 28 dB on any shot, or any hard check fails (below). If out, Sage enters as a separate install window, not inside this one. **If it passes, CK is ON for blocks 4-5**, and block 3's renders become their control. |
| 4 | **Schedule** | `<A3>_shift6beta_vllmomni` (node 4 shift_video 6) and `<A3>_shift6simple_modeltc` (node 4 6 + node 9 simple), × 6 each | 12 | 22 | A cell is **out at the first hard failure**: stop rendering it, and its remaining shots are not owed. If both cells are out, or neither beats control on banding and the owner's eye, the schedule stays 12/beta, and block 5 runs on 12/beta. |
| 5 | **Canvas 992** | schedule winner (+CK) at 992x992 with 992 panels re-cut from `storyboard/shot_NN.png` (S2: refs only, no panel) × 6 | 6 | 18 | **Out if:** OOM, or an s/it cliff (s/it > 2.3x the 768 run, which means partial offload; then one 896 run of D2 decides whether 896 is worth a separate window); or a whole-prompt time > 1.25x the 768 run on the median shot; or any hard failure. |
| 6 | **Second seed on the leader** | the combined leader (CK + schedule + canvas, whichever survived) on S3, S6, D2 with seed 2 | 3 | 8 | Any hard failure on seed 2 demotes the leader back to the last surviving step. |
| 7 | **P-WORDS sheet (droppable)** | one Qwen load; redraw the grids that own S3, S4, S6 and ep27 shots 03/12 at their shipped seeds with v2 vs minimal-v3 words; **panels only, no takes** | 4-5 grids | 10 | Cut first if the window runs long. It produces a sheet for the owner, not an adoption. |
| | Loads, VAE, ffprobe, slack | | | 12 | **Hard stop at 2 h 15 min wall.** Report what finished. |
| | **Total** | | **≈ 30 H3 + 5 grids** | **≈ 1 h 45 min** | |

### How each arm is judged (in this order)

1. **Ran-graph knob assertions** (§2.3). An arm whose ran graph does not carry its knob does not count. Also ffprobe the dimensions and check that the CRF output exceeds 5 Mb/s.
2. **Hard non-inferiority against the block's control.** Any single failure puts the arm out.

   | Check | Pass condition |
   |---|---|
   | Clone frames | 0 on every shot. D1 is held to 0, as A3 measured. |
   | Identity (facenet median vs staged sheets) | ≥ control − 0.02 on S4, S6, D1, D2 |
   | Lip lag | within ±0.1 s of control on S4, S6, D1, D2 (mandatory for every shift arm, §0.3) |
   | Content retained | by eye on the contact sheet: S3 frogs, S4 smoke column, no new figure, no look change (the A2 grey-narrator class) |
   | Cut/jump judge | no dissolve where the shipped take cut |

3. **Banding, the one calibrated ruler (AUC 0.849).**
   - Speed arms must be non-inferior: 6-shot mean ≤ control + 0.005, and no shot worse by > 0.03.
   - A quality arm must not be worse on the mean. It "wins" only together with point 4.
   - Texture, flat, face_flat, tail and Laplacian are **reported, never voting**. Texture voted for the mosaic, and face_flat is inverted.
4. **The owner's eye (the deliverable, not a gate).**
   - One face-crop sheet per block: 1:1 face boxes at 8/50/92 % for S4, S6, D1, D2, with arms side by side.
   - Plus the existing full-frame contact sheets.
   - Plus the P-WORDS panel sheet.
   - Path: `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\r2\` (`faces_B3_ck.jpg`, `faces_B4_schedule.jpg`, `faces_B5_canvas.jpg`, `panels_B7_words.jpg`).
   - A quality arm (schedule, canvas) is adopted **only** with the owner's yes on its face sheet. A speed arm (CK) is adopted on points 1-3 alone.
5. **The production tripwire after adoption** (S §2, unchanged). The first episode on any new name records duplicates, identity, lag, the cut judge and the per-phase clock (§2.2) against the ep22-27 medians. A regression rolls back the one `takes_r2v.BASE` line. Six shots cannot see a rate change in a rare fault, and memory `gates-are-not-quality` applies: a green bench is the absence of gross failure, nothing more.

---

## 4. Per-episode time projection (30 renders per episode)

| Scenario | Δ vs the 5.55 h phase-3 projection (4-step + CRF + P1 slice) | Median |
|---|---|---|
| 4-step alone (already counted) | 0 | **5.55 h** |
| + CK attention | −4.5 to −6.5 min | **≈ 5.45 h** |
| + schedule (any winner) | 0 (same NFE count) | ≈ 5.45 h |
| + canvas 992 at 4-step (sampling ×1.9 ≈ +33 s, decode ×1.6 ≈ +11 s, ref encode ≈ +2 s per take; CK gains slightly more at 992) | +20 to +25 min | **≈ 5.8 h** |
| + canvas 896 instead | +10 to +13 min | ≈ 5.65 h |
| without CK (Sage fails too) and with 992 | | ≈ 5.9 h |
| Speculative alternative if 992 wins on faces but the owner wants the time back: 992 only for shots whose main face is < 160 px | about half of +22 | ≈ 5.6 h |

The speculative alternative is not designed. It mixes canvases inside one cut, and that would need the owner's eye on grain matching.

- **Likely winners:** CK (verified mechanism, measured elsewhere at 1.34-1.79x on a 4090), and probably one shift-6 cell, since the 4-step last σ of 0.72 is the clearest mechanical defect found. Both are free or negative in time, giving **≈ 5.45 h median**.
- **992 is a quality-for-time trade.** It spends the whole 4-step saving and lands around 5.8 h. It is the owner's call from the face sheet.
- **The P90 stays over 6 h in every scenario.** As round 1 said, the tail is the plan stage and the stops, not the renderer.

---

## 5. What round 2 got wrong or left out (short)

- **R2_Q bench order:** it ran the schedule at 8 steps, ahead of a 4-step adoption, so its result would not transfer to what ships. It also kept `simple@12`, which is the softer direction at 4 steps.
- **R2_Q ranking:** it ranked a FL2VA-lineage LoRA (#5) in its top 5 against a recorded, owner-caught failure of that lineage.
- **R2_Q #3 (FaceRefine):** it missed that the stitch-back is a composite.
- **R2_P:** it presented the inert negative as a discovery (it is `LESSONS.md:175`), and sold P-GUIDE on it.
- **R2_P:** it treated "flat angular" as a defect instead of as the owner's chosen house style.
- **R2_P:** it under-reported its own best finding. The seam is 18 panels in 9 episodes, and the two inspected are doubled pictures, which are a duplicate source.
- **All three:** none checked that the bench overlay can carry their knobs. It cannot (§0.7).
- **R2_S:** correct in its claims, and it removed phase 0's blocker. Its merged-LoRA arm is premature.

**Publishable (flag):**
- Verified in source: ComfyUI's R2V node honours any canvas up to the 768x1344 area, so square users run at 57 % of the pixel budget.
- The 4-step ref2v schedule ends its last model call at σ 0.72 under the common 12/beta setting.
- Per-graph CK int8 attention via a core node, measured on ref2va.
- Once the bench measures all three, they belong in the planned public ref2va consumer-4090 bench (BENCH §10), including the arms that lose.
