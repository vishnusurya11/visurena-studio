# E — Why the War of the Worlds episodes look low quality (measured)

Investigator E, 2026-10-10. Read-only: no code, workflow or library file changed, nothing rendered.
Scratch evidence (frames, contact sheets, scripts):
`D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\quality\`
(`contact_early.png`, `contact_late.png`, `crop_pair.png`, `ep24_panel_vs_take.png`,
`early_ref_vs_late_panel.png`, `graphs.py`, `sharp.py`, `sharp.json`).

## Headline

**The pixel pipeline did not get worse. The picture SOURCE changed.** Every take graph, encode
and master from ep04 to ep27 has the same resolution, steps, sampler, shift, fps, CRF chain and
bitrate, and the measured sharpness of late takes is *higher*, not lower. What changed between the
owner's "good" ep01-03 and the late episodes is (1) what the take is told to look like — a
Krea2-Cinematic 3072x2048 reference set in ep01-03, a Qwen-Image 2.1 storyboard panel from ep05
on, which the take reproduces almost frame for frame — and (2) the take model (stock ref2va to
the Singularity int8 fine-tune with the same turbo LoRA loaded twice, from ep04). On top of that
sits a fixed 768x768 ceiling that every episode shares.

## 1. Measured settings, early vs late

Source: every `takes/r2v/T*.graph.json` (the graph that actually ran), `ffmpeg -i` on takes and
masters, `scripts/episode/assemble.py`, `scripts/episode/grids.py`, `scripts/episode/panels.py`.

| Setting | ep01-03 (owner: good) | ep04 | ep05-19 | ep20-27 (late) |
|---|---|---|---|---|
| Take model (UNET) | `minimax_h3_ref2va_pruned_fp8_scaled` | **Singularity_ref2va v1.3 int8** | Singularity int8 | Singularity int8 |
| Turbo LoRA | ref2v_turbo_8step @1.0 (once) | **same file @1.0 + again @0.7** | same, x2 | same, x2 |
| Steps / sampler / scheduler | 8 / euler / beta | same | same | same |
| CFG | 1 (BasicGuider) | same | same | same |
| Sigma shift (video/audio) | 12 / 3 | same | same | same |
| Take resolution | 768x768 | 768x768 | 768x768 | 768x768 |
| fps | 24 | 24 | 24 | 24 |
| Frames per take (median) | 158-175 | 158 | 141-209 | 124-175 (ep20 124) |
| Seeds | fixed per take (e.g. 82000+) | same scheme | same | same |
| Upscale / interpolation in graph | none | none | none | none |
| **What the take is shown** | Krea2 `wide_establishing`/`wide_space` + `sheet`, all **3072x2048** | same | **Qwen-Image panel 768x768** (+ wide on ep05; wides dropped from ep06-08, commit 5243d48) | **Qwen-Image panel 768x768** + `sheet_front` crops **659-952 x 2048** |
| Panel source | — | — | Qwen-Image 2.1 int8_convrot, 1024 px per cell, 25 steps, cfg 1.0, euler/simple (`grids.py` l.321-323) | same |
| Panel path | — | — | cell 1024 → seam crop → centre square → LANCZOS **down** to 768 (`panels.py` l.124-125) — never upscaled | same |
| Grid layouts actually drawn | — | — | 1x1, 2x1, 3x1, 2x2 (1024/cell) — not 3x3 | same |
| Take file (ComfyUI SaveVideo, codec auto, **no crf → libx264 default CRF 23**) | 1.27-1.46 Mb/s median | 1.60 | 0.86-1.82 | 1.19-1.77 |
| Segment extract | x264 fast CRF 17 | same | same | same |
| Picture join / audio mux | stream copy | same | same | same |
| Final pass (`assemble.tail`) | lanczos **2x → 1536x1536**, x264 slow CRF 14 | same | same | same |
| Loudness trim | `-c:v copy` | same | same | same |
| Master | h264 High 1536x1536 24p, 8.8-11.0 Mb/s, 181-224 MB | — | ep10 9.7 Mb/s | 9.2-12.9 Mb/s, 169-241 MB |
| Still substitutes (panel + zoompan instead of a take) | 0 | 0 | 0-2 (from ep12) | **ep20: 7 of 28 shots**, ep21: 4, others 1-2 |
| Lossy video generations per frame | 3 x264 (CRF23 → CRF17 → CRF14) + YouTube | same | same | same |

Uploaded file = the master (same file as `cut/master_r2v.mp4`), 1536x1536 h264 ~10-13 Mb/s.

## 2. Measured picture, early vs late

`sharp.py` (median over all takes per episode; Laplacian variance on grey 768; motion = mean abs
diff of consecutive frames; change = mean abs diff first vs last frame at 192 px):

| ep | takes | lap first/mid/last | panel lap | consecutive motion | first-vs-last change |
|---|---|---|---|---|---|
| 01 | 23 | 70 / 64 / 65 | — | 3.61 | 39.6 |
| 02 | 23 | 86 / 90 / 84 | — | 4.82 | 36.3 |
| 03 | 23 | 92 / 91 / 91 | — | 4.79 | 36.5 |
| 04 | 24 | 128 / 126 / 137 | — | 3.88 | 25.0 |
| 05 | 30 | 103 / 99 / 101 | 227 | 1.83 | 17.7 |
| 06-11 | | 37-159 mid | 97-492 | **0.97-1.9** (stillest stretch of the series) | |
| 20 | 28 | 111 / 108 / 111 | 306 | 2.20 | 34.5 |
| 22 | 22 | 109 / 106 / 98 | 486 | 3.93 | 31.4 |
| 24 | 22 | 167 / 145 / 135 | 477 | 2.98 | 31.5 |
| 26 | 27 | 206 / 159 / 157 | 980 | 4.28 | 38.9 |
| 27 | 24 | 96 / 143 / 124 | 355 | 3.10 | 27.6 |

Read:
- **Late takes are not blurrier than early ones by this measure** (mid lap 106-145 vs 64-91). The
  "sharpness 615 → 1222" gain claimed in commit 8847c34 for Singularity shows here as a real rise.
- **H3 throws away ~2/3 of the panel's high-frequency detail**: ep24 panel 477 → take 145, ep22
  486 → 106, ep25 673 → 150. The panel is the ceiling; the take lands well under it.
- Detail also decays through a take (first > last on most late episodes, e.g. ep16 225 → 121,
  ep19 171 → 100): the longer the take, the softer its tail.
- Mid-series (ep05-11) is the near-frozen era; late motion has recovered toward ep01-03 levels.
- Master brightness: ep01 luma 40 (63% of pixels < 40), ep02-03 69-73; ep20-27 46-69 (40-59% dark).
  Not a clean early/late split — darkness is chapter-driven, but dark frames do expose the
  CRF-23 take encode (posterised gradients in the night/interior shots).

Frames looked at (`contact_early.png`, `contact_late.png`, 4 frames per master at 20/50/80/110 s):
- **Early**: wide, deep, textured environments (heath, pit, observatory, crowds), Krea2's painted
  cinematic texture on every surface, faces smooth and modelled.
- **Late**: frequent medium-close faces rendered as **flat faceted planes** (ep24's red-lit face,
  ep20's curate and artilleryman), plain walls, dark interiors, flatter light. At 1:1 crop
  (`crop_pair.png`) both eras are equally soft — that is the shared 768 ceiling — but the late face is
  built from hard polygonal colour patches the early one does not have.
- `ep24_panel_vs_take.png`: take frame 0 ≈ the panel and frame 60 is the same picture with small
  movement — **the late look IS the Qwen panel's look**, animated.
- `early_ref_vs_late_panel.png`: the ep03 Krea2 wide (rich gravel, heather, smoke, light) vs ep27/
  ep20 Qwen panels (flat shading, empty walls) — and **ep20 shot_05's panel already contains the
  same moustached man twice**; the take inherits the panel's fault.

## 3. Ranked causes

1. **The look is now drawn by Qwen-Image 2.1 panels, not by Krea2-Cinematic references (from ep05;
   panel-only from ep06-08).** Evidence: the take reproduces the panel (ep24 panel vs frame 0/60);
   the reference set changed from 3072x2048 Krea2 pictures (ep01-04, every LoadImage) to 768 Qwen
   panels (every late LoadImage); the faceted/flat style is visible in the panels themselves before
   H3 touches them; panel content faults (duplicate man, ep20 shot 05) pass straight through. The
   panels are drawn with the int8_convrot Qwen-Image, cfg 1.0, 25 steps, prompts carrying the whole
   cast and setup in one grid; the style anchor is whatever wide/room picture is staged, not the
   Krea2 Cinematic LoRA. This is the change the owner is seeing.
2. **Take model swap at ep04: Singularity int8 + the SAME turbo LoRA applied twice (1.0 + 0.7 =
   1.7 effective)** (commit 8847c34, `video_minimax_h3_r2v_turbo_ref8.json` vs its
   `.pre-singularity.bak`). It fixed duplicates and raised Laplacian sharpness, but a distillation
   LoRA at 1.7x on an int8 checkpoint is the textbook source of over-contrasted, plasticky,
   flat-shaded skin — consistent with the faceted faces. ep01-03 (owner's "good") are the only
   episodes on the stock fp8 model with the LoRA once. Untested which of the two (int8 vs 1.7x
   LoRA) carries the flattening; an A/B on one ep03 graph would split it.
3. **Hard ceiling shared by every episode: 768x768 generation, saved at libx264 default CRF 23
   (~1.3 Mb/s, ~0.09 bit/pixel), then lanczos 2x to 1536.** The 2x adds no detail (the code says so
   itself, `assemble.py` l.775-781); the CRF-23 save is the lossiest step in the chain and the only
   one before any grade/upscale, so dark gradients band there. Not a regression — it is why even the
   good episodes are soft at 1:1 on a big screen.
4. **H3 drops ~65-75% of the panel's detail and decays over the take** (panel lap 300-700 → take
   100-150; first → last frame down 20-45% on ep16/19/23/25). Longer takes end softer.
5. **Still substitutes**: ep20 shipped 7 of 28 shots as a zoompan on a 768 panel (stills.json),
   ep21 4. A slow push on a still picture reads as a slideshow and is the most "cheap" looking
   segment in a cut.
6. **Character refs shrank to one-figure crops** (`sheet_front`, 659-952 px wide, from ep16,
   commit 0d05b1c) vs full 3072x2048 sheets early — fewer face pixels for identity/detail per ref.
   Plausible contributor to face mush on medium-wide figures; not separately measured.

Not causes (ruled out by measurement): steps, sampler, scheduler, CFG, shift, fps, take
resolution, master resolution/codec/bitrate, gutter-guard crops (`gutter.json` empty on ep01/03/
20/24/27), extra re-encodes (mux and loudness are stream copy), panel upscaling (panels are
downscaled 1024 → 768, never up).

## 4. Speed baseline

From `timing.jsonl` and take mp4 mtime gaps (one take after another, 768x768, 8 steps):

| ep | per-take render (median gap) | takes stage total | grids stage total | whole episode clock |
|---|---|---|---|---|
| 05 | 201 s | 6179 s | — (no grids) | 2.35 h |
| 20 | 115 s | 6416 s | 2810 s | 7.05 h |
| 21 | 148 s | 6042 s | 1521 s | 9.22 h |
| 22 | 216 s | 4838 s | 1258 s | 5.57 h |
| 23 | 193 s | 2142 s | 1316 s | 3.14 h |
| 24 | 156 s | 4231 s | 1265 s | 4.50 h |
| 25 | 139 s | 4096 s | 1139 s | 3.81 h |
| 26 | 147 s | 4842 s | 913 s | 5.68 h |
| 27 | 128 s | 3614 s | 5193 s | 5.94 h |

Baseline: **~2-3.5 min per H3 take at 768 (124-175 frames)**, ~22-28 takes + retakes ≈ 1-1.8 h of
takes per episode; Qwen grids 15-90 min. ep01-03 predate timing.jsonl (no per-stage record).
Any quality fix that raises resolution must be priced against this: 2x pixels on H3 is roughly 2x+
per take.

## 5. What would test the causes cheaply ($0, local)

- Replay one late take graph (e.g. ep24 T12) four ways, same seed: {stock fp8, Singularity int8} x
  {LoRA once @1.0, LoRA x2}. Splits cause 2.
- Replay the same take with the Krea2-Cinematic picture of the place (3072x2048) in place of the Qwen
  panel. Splits cause 1 from cause 2.
- Set `crf` on the take's SaveVideo (e.g. 12-14) — one-line change, removes the CRF-23 generation.
