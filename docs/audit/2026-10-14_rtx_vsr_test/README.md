# RTX Video Super Resolution on real episode takes (2026-10-14)

Question: do NVIDIA's RTX Video nodes ([Comfy blog](https://blog.comfy.org/p/nvidia-vfx-nodes-for-video-upscaling))
beat today's Lanczos 2x in `scripts/episode/assemble.py`, and do they fit the 6 h per-episode budget?
$0, local, no uploads. The live Jekyll ep01 render (step 09) was not touched: every GPU job ran only
when the ComfyUI queue was empty, GPU util was under 15 % and at least 2.5 GB VRAM was free (`tools/run_arms.sh`).

**Verdict: adopt RTX VSR standard `ULTRA` 2x, run once on the assembled 768 cut in place of the Lanczos
scale (arm U2 below). It adds about 0.4 min per episode, sharpens line art 1.9-2.7x on the Laplacian
with no ringing, and needs no ComfyUI restart because the installed pack already has it.
No arm moved banding.**

## Takes (Jekyll ep01, gothic-anime look, 768², 24 fps)

Copied from `library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01/takes/r2v/`
into `src/` (not committed; `src/` and `arms/` are 614 MB):

| take | why | frames |
|---|---|---|
| T17 | face close-up (Utterson), ink lines on face and background figures | 175 |
| T03 | wide night street, lamp glow into a dark gradient | 192 |
| T06 | the trampling (Hyde over the child, lamp pool) | 175 |

## What the node pack can do

- **Installed:** `Nvidia_RTX_Nodes_ComfyUI` 0.1.3 (892515e) on `nvidia-vfx` 0.1.0.1. It has only `LOW/MEDIUM/HIGH/ULTRA`, scale 1-4x.
- **Upstream:** 0.2.1 (168d35e) requires `nvidia-vfx>=0.2`. `nvidia-vfx` 0.2.0.0 (NVIDIA index) has the article's 19 modes:
  `BICUBIC, LOW, MEDIUM, HIGH, ULTRA, DENOISE_{LOW..ULTRA}, DEBLUR_{LOW..ULTRA}, HIGHBITRATE_{LOW..ULTRA}, STREAMING_{MEDIUM,ULTRA}`,
  plus `strength` and a 10-bit `image_encoding`. The pack also gains RTX Video HDR and frame generation.
- **Not updated.** The running ComfyUI has `nvvfx` 0.1 imported in-process, and its DLLs are locked, so the
  update (`git pull` the pack, then `pip install nvidia-vfx==0.2.0.0 --extra-index-url https://pypi.nvidia.com`)
  **needs a ComfyUI restart after the episode**. The modes here were tested by running the 0.2.0.0 wheel,
  extracted to a scratch folder, in a separate process (`tools/vsr_arm.py`). That is the same SDK the
  0.2.1 node calls.
- New workflow for after the restart:
  `D:\Projects\KingdomOfViSuReNa\alpha\comfy_studio\workflows\video\video_seedvr2_upscale_rtxvsr020_nvidia.json` (+ `.manifest.json`).
- **The effect is stateless:** frame X processed fresh and after 10 unrelated frames gives max |diff| 0.0
  in both ULTRA and HIGHBITRATE_ULTRA. Running it across a hard cut is therefore safe, and round 0's
  "per take only, never on an assembled cut" caveat does not apply.

## Arms

| arm | what |
|---|---|
| A | today's assemble: `scale=1536:1536:flags=lanczos`, x264 slow CRF 14 |
| B | RTX VSR 2x `HIGHBITRATE_ULTRA` (the clean-source mode) |
| C | `DEBLUR_ULTRA` at 1x, then B |
| D | RTX VSR 4x `ULTRA`, delivered at 3072 |
| D↓ | D's 4x, area-resized to 1536 on the GPU before the one encode (how D would actually ship at 1536) |
| U2 | RTX VSR 2x standard `ULTRA` (the installed node's mode; round 0's arm) |

Every arm is encoded like the master: libx264 slow CRF 14 yuv420p.

## Results

Timing: RTX 4090. **wall** = decode + VSR + download + encode for the whole job. **GPU** = the effect
calls only (CUDA-synced), excluding a ~0.65 s model load per job.
**Episode** = the measured 2:35.7 cut of all 23 ep01 takes (3,736 frames), scaled to a 2:55 master
(4,200 frames, x1.124).

Rulers (`scripts/bench/rulers.py`), all at 1536 (D area-downsampled):
- **lap** = Laplacian variance. It is reported only, because it failed calibration in phase 0, and it rewards ringing and noise.
- **band** = banding comb index, lower is better.
- **crisp** = 95th-percentile Sobel on the 320 px ink-line crop.

Whole-frame values are medians of 8 frames.

| arm | wall s/take | GPU s/take | per take x27 (min) | on the master (s) | **added vs A (min/ep)** | lap T17 / T03 / T06 | band T03 / T06 (night) | face crop lap / crisp | ink crop lap / crisp | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 2.56 | 0 (CPU) | 1.15 | 44.1 | 0 | 27.6 / 22.0 / 16.9 | 0.229 / 0.223 | 98 / 224 | 55 / 179 | soft baseline |
| B | 4.43 | 0.30 | 1.99 | 64.1 | **+0.33** | 45.6 / 49.4 / 30.9 | 0.218 / 0.215 | 176 / 240 | 101 / 182 | clean, but barely above A: HIGHBITRATE holds back on soft H3 renders |
| C | 4.79 | 0.53 | 2.15 | 74.3 | **+0.50** | 166.7 / 70.6 / 52.3 | 0.223 / 0.205 | 505 / 293 | 339 / 222 | **reject**: crispest, but rings (white rims on the ear, hats and outlines) and amplifies grain in the flats |
| D (3072) | 13.63 | 0.34 | 6.13 | 270.8 | **+3.78** | 62.9 / 29.1 / 23.1 | 0.105 / 0.086 * | 301 / 259 | 100 / 178 | no visible gain at 1536; the cost is a 3072 encode |
| D↓ | 4.49 | 0.65 | 2.02 | 65.8 | **+0.36** | 61.3 / 30.5 / 25.3 | 0.208 / 0.203 | 299 / 259 | 103 / 178 | clean supersample, about level with U2 |
| **U2** | 4.61 | 0.22 | 2.08 | 69.6 | **+0.43** | **75.9 / 41.7 / 33.2** | 0.210 / 0.202 | 383 / 267 | 125 / 182 | **recommended**: firmest clean lines, no halo, installed today |

\* D's low banding is an artefact of the measurement, not a property of D: it comes from decoding a 3072 x264
encode and then averaging 4x4 pixels, which turns codec noise into dither. D↓, the same 4x output resized
before quantisation, bands like every other arm. Native-3072 banding is 0.197 / 0.192.
**Banding is flat across every arm that would ship (0.20-0.23 at night).** Round 0's narrow banding
win did not reproduce.

ComfyUI node path (installed pack, `video_seedvr2_upscale_rtxvsr_nvidia` with its declared inject slots,
queued between the episode's jobs, T17): **2x ULTRA 25.1 s, 4x ULTRA 49.4 s**, which matches round 0's
15-22 s/take. Most of that is the node's whole-clip float tensors plus PyAV's CRF 10 save, not VSR.
Per take x27 that is +11.3 min (2x) or +22.2 min (4x).

Raw: `timings.jsonl` (per take), `rulers.json` (every ruler, every arm, every crop).

## Budget (per-episode clock ~5.5 h median, ceiling 6 h)

| path | added | episode clock |
|---|---|---|
| U2 on the master, in-process (recommended) | +0.4 min | ~5.51 h, fits |
| B / D↓ on the master | +0.3-0.4 min | fits |
| C on the master | +0.5 min | fits, but rejected on quality |
| D delivered at 3072 | +3.8 min | fits |
| U2 per take through the ComfyUI node | +11.3 min | ~5.69 h, fits |
| D per take through the ComfyUI node | +22.2 min | ~5.87 h, fits, but uses 2/3 of the headroom |

Every arm fits. Cost does not decide this; the picture does.

## Recommendation

Replace the Lanczos `scale` in `assemble.py` with **RTX VSR `ULTRA` 2x over the assembled 768 cut**
(U2), followed by the same x264 slow CRF 14 encode.
- The effect is stateless, so one pass over the cut is equivalent to per take and avoids 27 job loads.
- It runs on the installed `nvidia-vfx` 0.1.0.1, so no restart is needed.
- In-process it is ~0.4 min per episode.
- Running the whole master through the ComfyUI node is not an option: 4,200 frames as float tensors is
  ~30 GB in and ~119 GB out. It is either the in-process call (`tools/vsr_arm.py` is the shape) or per
  take through the node (+11 min).
- D↓ is the close second (same cost, a hair softer). HIGHBITRATE (B) is too conservative for these
  sources. DEBLUR (C) rings on ink line art and should not ship.
- The 0.2 pack is still worth installing at the next restart (HDR and frame-generation nodes, 10-bit
  encoding), but its new SR modes did not beat standard ULTRA here.

## Files

- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-14_rtx_vsr_test\compare.jpg`: 100 % crops (face, ink lines, night gradient, trampling) for A, B, C, D↓, plus D native 3072 at 100 %
- `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-14_rtx_vsr_test\compare_preview.mp4`: 2x2 A/B/C/D↓ on T17, 100 % 768 crops (15.5 MB)
- `tools/vsr_arm.py`: one arm, standalone nvvfx 0.2. `tools/run_arms.sh`: the gap-gated runner. `tools/measure.py`: rulers and the sheet.
- Not committed: `src/` (the 3 takes) and `arms/` (18 arm outputs, 581 MB).
