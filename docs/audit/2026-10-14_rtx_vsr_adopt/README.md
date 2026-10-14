# RTX VSR adopted in assemble (2026-10-14)

Owner decision: RTX Video Super Resolution at the highest quality that costs under 10 min per episode.
Built: 4x standard `ULTRA` to a 3072 master, in process (`studio/master_upscale.py`, nvidia-vfx 0.2.0.0 + cupy).
`VISURENA_MASTER_UPSCALE=rtx2x` gives 1536. `lanczos` is the old path and the fallback when the GPU or nvidia-vfx
is missing; a fallback is printed (`UPSCALE FALLBACK:`) and named on the clock row. Bench: `../2026-10-14_rtx_vsr_test/`.

## Jekyll ep01, measured end to end (no takes re-rendered)

| | iter1 (Lanczos 2x, 1536) | iter2 (RTX 4x ULTRA, 3072) | added |
|---|---|---|---|
| master join + upscale + encode | 37.7-40.4 s (same cut, re-timed) | 252.3 s (`upscale` row, timing.jsonl) | **+3.6 min** |
| qc.py | 403.3 s | 497.6 s (passing run; the first run read 629.6 s) | +1.6 to +3.8 min |
| **total** | | | **+5.1 to +7.3 min, under the 10 min ceiling** |
| master size | 210 MB | 1,535 MB | |

QC on iter2: **PASS**. 145.08 s, -14.1 LUFS / -1.9 dBTP, cuts 22/22, lines heard 21/21, segments 23/23,
pts holes 0, tail 3482/3482, takes 23/23.

The first QC run failed 7/23 segments. QC's segment cap (mean grey difference from the take, 1.0) had been
calibrated on Lanczos masters. RTX sharpening puts every correct segment at 0.97-1.48 (it was 0.35-0.55),
with no frame over 1.56 and offset 0 the best shift on all 23. Assemble now records each master's upscale
by sha8 in `cut/master_layout.json`, and an RTX master is judged at 2.0 (`edit_gate.SEGMENT_MEAN_RTX`).

Note: assemble re-made 4 bed tones on this run, so iter2's bed is not byte-identical to iter1's.
The picture came from the same takes and the same placed.json.

## Files

- `crop_iter1_vs_iter2.jpg`: the same region at 100 % in each master (face, ink lines, night street, trampling)
- `master_iter2_preview720.mp4`: 720p preview of master_iter2 (21.9 MB)
- the master: `library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep01/cut/master_iter2.mp4`
