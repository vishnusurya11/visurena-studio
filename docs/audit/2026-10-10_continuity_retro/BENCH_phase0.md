# BENCH phase 0: quality + speed arms (2026-10-10)

Bench builder, run under `S_skeptic_verdict.md` §4/§6 phase 0 (owner-approved pause, local GPU, $0).
The autopilot was paused 20:1x and resumed at the end (WotW 27/27 complete; the loop was idle).
**Nothing in production was switched.** No existing workflow was edited; every arm is a new file.

## 0. What ran, what did not

| Block (S §4) | Status | GPU |
|---|---|---|
| CPU prework: content-matched ruler calibration; ep04 split | **done** | 0 |
| CPU prework: R0c grid layouts; P1 plan-gate replay; G-LOOK-PANEL marker check | **not run**. The plan gates do not exist yet (P1 commits 6-7, built by the continuity builder). R0c was dropped for time. | 0 |
| B-0 post: Lanczos vs RTX VSR ULTRA, 3 shipped takes | **done** | ~1 min |
| B-1 take model: A1/A2/A3 x S2,S3,S4,S6 + 2nd seed A2/A3 + 2 dialogue A1 vs A3 (24 renders) | **done** | 57 min |
| B-1 A4 stock fp8 (conditional: "only if A2 does not recover the look") | **not run**. A2 did not recover it, so A4 is now due (+10 min). | - |
| B-2 picture source: B1 Krea2 restyle | **cut at the panel** after 12 restyle passes (3 settings); 2 B1 takes rendered as evidence | ~8 min |
| B-3 continuity (P1 looks / villa) | **not run**. Needs P1's look definitions (continuity builder, phase 1). | - |
| B-4 CK attention flag | **not run, see §6**. The relaunch was issued, then ComfyUI access was refused by the auto-mode permission classifier ("interfere with workloads": the engine is shared with the Scarlet session). | - |
| Sage cu130 wheel | **not run**. Same block. The package state is recorded for whoever runs it (`bench_evidence/pip_before_sage.txt`). | - |

GPU used: about 1 h 20 min (20:14-21:32).

## 1. Ruler calibration (content-matched, CPU)

Owner-good: the villa front and the study in ep01-03 (ep01 T03 T18 T19-22, ep02 T00 T01 T20-22, ep03 T11; 12 takes, refs-only Krea2).
Owner-bad: the same places in ep26-27 (ep26 T15-17, ep27 the study and writing-table takes; 16 takes, Qwen panels).
8 frames per take, medians. A ruler votes at AUC >= 0.75 (`scripts/bench/calibrate.py`, `bench_evidence/calibration.json`).

| Ruler | AUC | Votes | good median | bad median |
|---|---|---|---|---|
| **banding** (comb index, dark smooth luma) | **0.849** | **yes** | 0.248 | 0.292 |
| texture (DoG 1-4, off faces) | 0.708 | no (close) | 5.70 | 4.55 |
| flat (16x16 std < 2.5) | 0.693 | no | 0.067 | 0.080 |
| face_flat (8x8 inside faces >= 64 px) | 0.447 | no (inverted) | 0.147 | 0.104 |
| tail (texture last/first) | 0.385 | no | 1.02 | 1.06 |
| Laplacian (reported only) | 0.177 | no (**inverted**, as E found) | 95 | 167 |

**Only ONE ruler calibrates.** S's quality rule ("wins on >= 2 calibrated rulers") therefore cannot pass any
quality arm in this bench: quality arms default to the status quo plus the owner's eye. Note also that `banding`
calibrated even though the encode (CRF 23) is the same in both eras, so it reads the SOURCE's smooth gradients, not the
encode. It does not reward the CRF-10 save (A1 is not better than A0 on it, §2).
**Texture would have voted FOR the mosaic restyle** (B1 texture +20-24 %), which is the "a ruler that rewards
crunch" trap. It must not be promoted to a vote by lowering the bar.

**ep04 split of cause 2** (ep04 = Singularity int8 + LoRA 1.0+0.7 on the refs-only recipe; its takes that staged the
SAME place picture bytes as ep01-03: `wide_establishing_0a441b5d` crater, `9b71d848`; 34 ep01-03 takes vs 24 ep04):
banding 0.244 (ep01-03) -> **0.266 (ep04)** -> 0.292 (late); texture 4.82 -> 4.76 (unchanged). The take-model change at
ep04 accounts for about **half the banding gap and none of the texture gap**. The panel source carries the rest. Cause 2 is real
but secondary. A2 (LoRA once) does not recover it (§2), so if cause 2 is to be pinned, it is the int8
Singularity weights (arm A4), not the 1.7x LoRA.

## 2. Per-arm table (B-1 take model + B1 takes)

Arms (new files in `comfy_studio/workflows/video/`, each with a manifest whose optional defaults match its own graph):
A1 `video_minimax_h3_r2v_turbo_ref8_crf_visurena` (today's graph, CRF 10 save) · A2 `..._single_lightx2v` (8-step LoRA once
@1.0) · A3 `..._ref4_singularity` (4-step v0.1 LoRA once @1.0, steps 4, **no `steps` inject**). A0 = the shipped take.
Every job replays the shipped ran `T*.graph.json` (same prompt, refs, voice guide, frames, seed) with the arm file's
model/LoRA/attention/steps/save nodes laid over it (`scripts/bench/h3_arms.py`). **Knobs verified on the graph
actually submitted** (UNET Singularity int8; LoRA chain [8step 1.0, 8step 0.7] / [8step 1.0] / [4step 1.0]; steps 8/8/4;
attention `disabled`; crf 10; seed) for all 26 jobs, and asserted before submit (`bench_evidence/ran_graphs/`).
CRF acceptance: every bench take reads **7.9-21 Mb/s** (> 5 Mb/s) against 0.9-2.5 Mb/s shipped.

Shots: S2 ep03 T11 (narrator at gate, Krea refs) · S3 ep24 T05 (frogs wide) · S4 ep24 T12 (two men MCU, dialogue 107 f) ·
S6 ep27 T03 (dialogue 141 f) · D1 ep25 T21 (dialogue 90 f) · D2 ep27 T25 (dialogue 175 f). Seconds come from ComfyUI's
history (prompt) and its own sampler bar (`scripts/bench/timing.py`). **S2_A1 and S3_A1 timings are contaminated** by my
own CPU calibration running beside them (13-14 s/it vs 8.5 elsewhere on similar frames); S2_A3 paid the 4-step LoRA's
first load from the HDD. No foreign (Scarlet) prompt ran inside the B-1 window (history checked); they ran after 21:11.

| take | prompt s | sample s (s/it) | banding (votes) | texture | flat | tail | clone frames | id median | lag s | still | Mb/s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S2_A0 | - | - | 0.223 | 6.27 | 0.060 | 0.833 | 0/12 | 0.613 | - | 0.0 | 2.4 |
| S2_A1 | 149.7* | 106 (13.31)* | 0.244 | 6.94 | 0.132 | 0.987 | 0/12 | 0.306 | - | 0.0 | 15.7 |
| S2_A2 | 152.3 | 110 (13.8) | 0.260 | 6.76 | 0.130 | 0.957 | 0/12 | - | - | 0.0 | 13.3 |
| S2_A2_s2 | 145.7 | 108 (13.52) | 0.250 | 7.13 | 0.122 | 0.934 | 0/12 | - | - | 0.077 | 17.8 |
| S2_A3 | 180.1† | 51 (12.98) | 0.235 | 6.42 | 0.143 | 0.999 | 0/12 | - | - | 0.0 | 16.5 |
| S2_A3_s2 | 133.4 | 52 (13.18) | 0.241 | 6.82 | 0.142 | 0.929 | 0/12 | - | - | 0.0 | 21.0 |
| S3_A0 | - | - | 0.284 | 5.63 | 0.043 | 0.873 | 0/12 | - | - | 0.0 | 2.5 |
| S3_A1 | 343.8* | 114 (14.3)* | 0.281 | 5.70 | 0.039 | 0.883 | 0/12 | - | - | 0.0 | 16.8 |
| S3_A2 | 171.1 | 115 (14.44) | 0.281 | 6.07 | 0.040 | 0.932 | 0/12 | - | - | 0.0 | 15.9 |
| S3_A2_s2 | 159.2 | 117 (14.69) | 0.290 | 6.54 | 0.034 | 1.002 | 0/12 | - | - | 0.0 | 18.1 |
| S3_A3 | 166.4 | 57 (14.38) | 0.281 | 5.19 | 0.112 | 0.763 | 0/12 | - | - | 0.0 | 16.7 |
| S3_A3_s2 | 125.4 | 53 (13.5) | 0.280 | 4.89 | 0.074 | 0.654 | 0/12 | - | - | 0.0 | 17.1 |
| S4_A0 | - | - | 0.216 | 7.29 | 0.030 | 0.998 | 0/12 | 0.748 | 0.0 | 0.0 | 1.9 |
| S4_A1 | 117.1 | 68 (8.55) | 0.223 | 7.31 | 0.026 | 0.994 | 0/12 | 0.768 | 0.0 | 0.0 | 12.3 |
| S4_A2 | 135.1 | 67 (8.47) | 0.229 | 7.37 | 0.026 | 0.992 | 0/12 | 0.766 | 0.0 | 0.0 | 12.2 |
| S4_A2_s2 | 104.0 | 68 (8.62) | 0.233 | 7.33 | 0.028 | 1.004 | 0/12 | 0.796 | 0.0 | 0.056 | 12.1 |
| S4_A3 | 98.4 | 33 (8.28) | 0.270 | 7.87 | 0.024 | 1.0 | 0/12 | 0.800 | 0.0 | 0.0 | 12.6 |
| S4_A3_s2 | 91.2 | 32 (8.13) | 0.253 | 6.91 | 0.031 | 1.076 | 0/12 | 0.798 | 0.0 | 0.0 | 13.7 |
| S4_A1_B1v3 | 120.4 | - | 0.232 | 8.75 | 0.007 | 0.99 | 0/12 | **0.683** | 0.0 | 0.056 | 13.3 |
| S6_A0 | - | - | 0.392 | 3.68 | 0.047 | 0.817 | 0/12 | 0.738 | 0.0 | 0.0 | 1.3 |
| S6_A1 | 130.7 | 90 (11.27) | 0.413 | 3.76 | 0.035 | 0.814 | 0/12 | 0.730 | 0.0 | 0.0 | 12.0 |
| S6_A2 | 132.4 | 89 (11.24) | 0.445 | 4.16 | 0.029 | 0.875 | 0/12 | **0.521** | 0.0 | 0.0 | 12.4 |
| S6_A2_s2 | 149.5 | 90 (11.25) | 0.447 | 4.29 | 0.033 | 0.82 | 0/12 | 0.746 | 0.0 | 0.0 | 10.1 |
| S6_A3 | 114.2 | 43 (10.87) | 0.419 | 3.15 | 0.059 | 0.672 | 0/12 | 0.762 | 0.0 | 0.0 | 12.1 |
| S6_A3_s2 | 106.2 | 42 (10.73) | 0.446 | 3.49 | 0.053 | 0.765 | 0/12 | 0.756 | 0.0 | 0.0 | 11.7 |
| S6_A1_B1v3 | 352.3‡ | - | 0.326 | 4.56 | 0.015 | 0.81 | 0/12 | **0.655** | 0.0 | 0.0 | 13.1 |
| D1_A0 | - | - | 0.293 | 5.10 | 0.132 | 1.151 | 1/12 | 0.845 | 0.0 | 0.0 | 1.7 |
| D1_A1 | 82.0 | 47 (5.94) | 0.303 | 5.14 | 0.123 | 1.122 | 2/12 | 0.837 | 0.0 | 0.0 | 11.1 |
| D1_A3 | 95.0 | 22 (5.57) | 0.279 | 4.24 | 0.176 | 0.96 | **0/12** | 0.834 | 0.0 | 0.0 | 12.4 |
| D2_A0 | - | - | 0.306 | 5.31 | 0.212 | 0.822 | 0/12 | 0.871 | -0.01 | 0.241 | 0.9 |
| D2_A1 | 171.0 | 126 (15.83) | 0.318 | 5.37 | 0.198 | 0.814 | 0/12 | 0.875 | -0.01 | 0.241 | 7.9 |
| D2_A3 | 131.0 | 60 (15.11) | 0.286 | 5.46 | 0.219 | 0.989 | 0/12 | 0.879 | -0.01 | 0.069 | 8.4 |

\* contaminated by my CPU calibration · † first load of the 4-step LoRA from the HDD · ‡ a model reload after foreign prompts.
`lag` = mux lag of the take's soundtrack against the staged voice wav (`studio.av_sync`); `id` = facenet median best cosine of
readable faces to the staged sheets (S2/S3 faces are too small or absent to read); clones = frames with more faces >= 0.12 of the
frame height than staged sheets. **Lip-sync lag on the 3 dialogue takes of different lengths (D1 90 f, S6 141 f, D2 175 f), plus
S4 107 f: A1 0.0 / 0.0 / -0.01 / 0.0, A3 0.0 / 0.0 / -0.01 / 0.0: identical** (within +-0.1 s of A1, S's acceptance).

Looked at (contact sheets, §5): A1 is the same picture as A0 (same seed, deterministic), so the CRF arm isolates the encode.
**A2 seed 1 on S6 turned the narrator grey-haired with a grey moustache** (the id drop to 0.52 is real; a look fault, the
exact class of the owner's complaint). **A3 loses the frogs from the S3 wide by mid-take in both seeds** (A2 seed 2 also
does; A1/A0 keep them), and A3 seed 1 on S6 ends on a much tighter push. B1 dresses everyone in a patchwork mosaic and drops the smoke column.

## 3. B-0: RTX VSR ULTRA 2x vs Lanczos 2x (3 shipped takes, both 1536², CRF 10)

`video_seedvr2_upscale_rtxvsr_nvidia` (new file). Frame counts preserved (175/107/141).

| shot | banding L -> VSR | texture L -> VSR | flat L -> VSR |
|---|---|---|---|
| S3 | 0.275 -> 0.272 | 4.16 -> 4.35 | 0.123 -> 0.090 |
| S4 | 0.210 -> 0.206 | 5.38 -> 5.66 | 0.089 -> 0.067 |
| S6 | 0.374 -> 0.360 | 2.73 -> 2.92 | 0.199 -> 0.133 |

VSR wins 3/3 on the voting ruler (small) and 3/3 on texture/flat, and invents nothing visible (`vsr_crops_lanczos_left_rtx_right.jpg`).
Time: the log brackets each VSR prompt at **about 15-22 s per take** (Scarlet prompts were interleaved, so attribution is approximate),
which is +6-9 min per episode, more than G's 1-3 min. Most of that is the 1536² CRF-10 encode. It is "does it hurt": **no**. It fixes no cause.
(Bench bug, fixed: the first collection copied the LoadVideo input preview, which was byte-identical to the shipped take. The real
outputs were recovered from `ComfyUI/output/bench_S*_A0_rtxvsr_00001_.mp4` and measured.)

## 4. B-2: Krea2 restyle of the Qwen panel (B1)

`image_krea2_cinematic_2x_restyle_visurena` (new file: the house sheet recipe as img2img over the panel, 768 -> 1024 -> 768).
Three settings on 4 panels (S3, S4, S5 ep20 T05, S6): denoise 0.35 / LoRA 1.0 / house lead; 0.25 / 0.7 / house lead;
0.25 / 0.7 / a softer lead without "heavily angular". **Every setting fails at the panel**
(`restyle_d035_top_qwen_bottom_krea.jpg`, `restyle_d025_rows_qwen_v2_v3.jpg`):
- a hard colour **mosaic** on mud, clothes and logs, i.e. the faceting the owner complained of, amplified;
- **content loss**: the frogs (S3) vanish and the smoke column (S4) is gone;
- **faces redrawn**: the B1 takes' identity falls 0.768 -> 0.683 (S4) and 0.730 -> 0.655 (S6).
Warm restyle cost: about 7-8 s per panel (+ one Krea load of about 15 s). Two B1 takes (S4, S6 on A1) carry the mosaic straight
into the motion (`contact_S4.jpg`, `contact_S6.jpg`, last row). H3 copies the panel, as E said.

## 5. Evidence (contact sheets: rows = arms, columns = 8 %, 50 %, 92 % of the take)

Folder: `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\contact_S2.jpg`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\contact_S3.jpg`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\contact_S4.jpg`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\contact_S6.jpg`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\contact_D1.jpg`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\contact_D2.jpg`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\vsr_crops_lanczos_left_rtx_right.jpg`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\restyle_d035_top_qwen_bottom_krea.jpg`
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\restyle_d025_rows_qwen_v2_v3.jpg`
- data: `calibration.json`, `measures_b1_b2.json`, `measures_vsr.json`, `timing_b1.json`, `plan_b1.json`, `pip_before_sage.txt`, `ran_graphs\*.graph.json` (all 26 submitted graphs)

Bench videos (not committed, about 400 MB): `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\bench\runs_b1\`, `...\runs_b2\`, `...\runs_b0b2\`.

## 6. Winners per decision

| Decision | Winner | Why (S's rules: speed arms tie on calibrated rulers; every arm non-inferior on duplicates, identity, lag) |
|---|---|---|
| **CRF 10 take save** | **A1 (adopt in phase 3)** | Its acceptance per S row 106 is met: the ran graph carries `format.codec.encoding.crf: 10`, and the takes read 7.9-21 Mb/s. Same pixels as A0. The banding ruler shows no gain (it reads the source, §1), so this is a lossless-generation fix, not a measured look fix. Disk: about 10-15 MB per take vs 1-2 MB, so about +300 MB per episode. |
| **LoRA once vs twice** | **Twice (status quo)** | A2 is worse on the voting ruler on 4/4 shots (mean banding 0.304/0.305 vs 0.290), and it produced one look fault (S6 seed 1, grey narrator, id 0.52). Texture is slightly higher (non-voting). The 2026-09-19 x2 recipe stands. |
| **4-step vs 8-step** | **4-step (A3) passes, adopt behind the tripwire** | Banding over 6 shots: mean 0.295 vs A1 0.297 (3 better, 2 tie, 1 worse: S4 0.270/0.253 vs 0.223). Clones 0 vs 2 (D1). Identity equal or better (0.80/0.76/0.83/0.88 vs 0.77/0.73/0.84/0.88). Lag identical on all 4 dialogue takes. Sampling halves (median -51 s per take); the whole prompt falls about 20-40 s. **Risks the rulers do not vote on:** texture lower on 4/6 (S3 -9/-14 %, S6 -16/-7 %), a faster tail decay on S3/S6, and **the S3 frogs leave the frame in both seeds**. Hard cuts were not tested (every bench take is one shot). F warns cuts smear at 4 steps, so the `cut`/`jump` judge must read the first production episode. Owner's eye on `contact_S3.jpg` / `contact_S6.jpg` before adoption. |
| **Krea restyle vs Qwen panel** | **Qwen panel (status quo)** | B1 fails at the panel in all 3 settings: mosaic, lost content, redrawn faces (identity -0.08). It is not non-inferior on identity. E's cause 1 needs a different lever (a refine that does not re-paint, e.g. G #3, or a better grid prompt/model), not this restyle. |
| **RTX VSR vs Lanczos** | VSR wins narrowly, **deferred** | It wins 3/3 on the voting ruler, but it fixes no cause and costs +6-9 min. S §3 puts it first in the cut order unless scenario W holds. Scenario W needs 4-step **and** B1; B1 lost. |
| **Sage / CK attention** | **Not measured** | Not run: the ComfyUI relaunch for CK was issued at about 21:33, then my access to the engine was refused by the permission classifier (shared engine). See §8, the engine state is pending. |
| (cause 2 follow-up) A4 stock fp8 | due, not run | A2 did not recover the look and ep04 shows half the banding gap. A4 is the remaining split (+10 min GPU). |

## 7. Projected minutes per episode (vs the 6 h budget)

Baseline: ep19-27 median **5.68 h** (mean 5.74, 3/9 over 6 h).

| Change | Δ min / episode | Basis |
|---|---|---|
| P1 slice | +5 to +12 | S §3 (unchanged) |
| CRF 10 | +1 | encode only |
| A3 4-step | **-10 to -25** | measured: sampling -51 s median, whole prompt -20 to -40 s, x 25-35 renders + retakes |
| B1 restyle | 0 (rejected) | |
| RTX VSR | 0 (deferred; +6 to +9 if adopted) | measured 15-22 s per take |
| CK / Sage | unmeasured | S's estimate -5 to -7 on 4-step |

**Scenario after phase 3 with A3 + CRF and without VSR:** 5.68 h + (8 + 1 - 17) / 60 ≈ **5.55 h median**; with VSR ≈ 5.7 h.
Without A3 (if the owner's eye or the tripwire rejects it): ≈ 5.83 h. The P90 stays above 6 h in every case (plan stage and stops, S §3).

## 8. Adoption and rollback, one line each (phase 3; nothing switched now)

- **CRF 10**: adopt `scripts/episode/takes_r2v.py:52  BASE = "video_minimax_h3_r2v_turbo_ref8_crf_visurena"` · rollback `BASE = "video_minimax_h3_r2v_turbo_ref8"`.
- **4-step**: adopt `BASE = "video_minimax_h3_r2v_turbo_ref8_ref4_singularity"`, plus (test-first) `graph_for` passes `steps` only when the manifest declares it. The manifest deliberately has no `steps` inject, so today `apply_inject` raises `KeyError: 'steps'` (loud, not a silent 8). Also copy `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` to `C:\comfy_models\loras\minimax_h3\` (it is on the HDD). Rollback: `BASE = "video_minimax_h3_r2v_turbo_ref8_crf_visurena"`. Tripwire on the first episode: duplicates, identity, lag, cut judge, clock vs the ep22-27 medians.
- **RTX VSR** (if later adopted): a per-take pass with `video_seedvr2_upscale_rtxvsr_nvidia` before `assemble`, behind a flag that defaults off. Rollback: flag off (the Lanczos 2x in `assemble.tail` stands).
- **CK attention** (once measured): relaunch flag `--use-ck-attention` · rollback: relaunch without it.
- **Sage cu130** (its own window): before = `sageattention 2.2.0+cu128torch2.10.0andhigher.post5`, `torch 2.11.0+cu130`, `triton-windows 3.5.0.post21` (`bench_evidence/pip_before_sage.txt`). Rollback: `python_embeded\python.exe -m pip install --force-reinstall --no-deps <the post5 cu128 wheel>` (download and keep it locally before installing post6).

**ENGINE STATE TO RESTORE.** At about 21:33 I relaunched ComfyUI as
`python_embeded\python.exe -s ComfyUI\main.py --windows-standalone-build --reserve-vram 2 --use-ck-attention`
(the old PID 2344 was killed with the queue empty). Before I could confirm that it came up, every ComfyUI call was refused
by the permission classifier. If it is up, it runs **with CK attention on** for every job, Scarlet's included. Restore the
production launch (the same command without `--use-ck-attention`) unless CK is wanted. Nothing else changed on the
engine (no wheel installed).

## 9. Incidents

- 20:20-20:35: ComfyUI's HTTP stopped answering for about 15 min while jobs kept executing. The likely cause is my full
  `/object_info` request (one huge synchronous call on a busy engine). Use `/object_info/<Node>` only. No job was lost.
- My calibration ran beside the first two renders and slowed their sampling (13-14 s/it); those two timings are excluded.

## 10. Publishable (flag)

`scripts/bench/` (arm overlay with ran-graph knob assertion, content-matched ruler calibration, sampler-bar timing) plus the
26 ran graphs is the core of the first public **ref2va** consumer-4090 bench (S §6, P2 §9). It includes the negative results
(LoRA x1, the Krea restyle) and the finding that only one of six image rulers survives a content-matched human split.
