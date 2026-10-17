# 2026-10-17 -- the wide-shot face refine (step 09_07, pasted at master scale in step 10)

Status: BUILT 2026-10-17 (owner approval, same day). Tracker: `architecture/plan/2026-10-17_face_refine.md`.
Evidence: `docs/audit/2026-10-16_model_research/01_face_blur.md`, `docs/audit/2026-10-16_model_tests/PART1_SUMMARY.md`
and `faces/results.json` (test F2), calibration `docs/calibration/face_refine.md`.

## The ruling (owner, 2026-10-17)

> "I like face improvements a lot in wide shots, go ahead"

## The problem, measured

A square take renders at 768x768 (H3's fixed short edge). A wide or full shot puts a face at
25-40 px of that (Jekyll ep01 T00 30 px, T22 25-36 px), a factor 3-5 under the readable line
(`identity_gate.READABLE` 0.15). Close-ups from the same graph read fine, so the stack is not the
cause: the pixels are not there. RTX VSR cannot add them (F0: it sharpens the mush into blotches),
more steps do not (F5), SeedVR2 on the crop draws scratchy noise and no features (F3).

## The brick

**A face gets the pixels it lacks by being rendered again at the size the model draws faces well,
with only its own person's sheet, and is put back where the delivered pixels are -- after the
upscale, never into the 768 take.**

F2 is that rule: a tracked crop of the face (2.4x the face, >= 96 px), scaled to 768, pushed into
H3's video latent (`H3InjectVideoLatent`) and re-rendered at denoise 0.45 with the person's sheet
as the only picture, then feather-pasted into the 3072 master. On T00 the 30 px mush became
Utterson's face (eyes, brows, nose, mouth in the book's line), with no seam and no new flicker
(face-region frame diff 6.52 vs 6.66). Pasted into the 768 take instead, the gain averaged away.

## What runs

| where | what |
|---|---|
| selection (`studio/face_refine.selected`) | a take whose plan size is `wide` or `full`, or whose take_dq face-at-end is under 60 render px (never an insert), with a planned face and a PASSED dq |
| tracking (`studio/face_track.py`) | MTCNN loosened for small faces every 4th frame; detections linked by nearness, missed stretches stitched (<= 48 frames), a face already >= 60 px left alone; one window size per track; the crop span on H3's 17n+5 grid |
| matching (`scripts/episode/face_refine.match`) | every track scored against every staged person: half facenet cosine to the sheet, half a Lab colour histogram of the head and hat (black wideawake vs light-brown top hat), plus the plan's "at the LEFT/CENTRE/RIGHT" when the take prompt says it of one subject; the one-to-one map with the best total |
| render (workflow `video_minimax_h3_r2v_turbo_ref8_crf_visurena_ckattn_comfyorg_facecrop_v2v_mickmumpitz`, F2's own graph, never edited; a new manifest beside it) | the person's crop at denoise 0.45, ONLY their current sheet, the take's own seed + subject number, a silent guide |
| gate (`studio/face_gate.py` measures, `face_refine.decide`) | kept only if: identity to the sheet does not drop by more than 0.05; seam (feather-band level difference at window scale) <= 18; face-region flicker pasted <= 1.10 x the take's + 0.5; faces counted on the 768 crops unchanged (one missed detection allowed). Otherwise the unrefined take. Every decision per take in `takes/r2v/refine.json` |
| paste (`studio/face_paste.py`, `assemble.face_paste_wrap`) | inside the master's one RTX VSR pass (`master_upscale.master(wrap=)`): each upscaled frame gets every kept, CURRENT crop (the take's sha8) through the cut's own geometry -- head trim, G-DEAD slow-down, gutter guard crop -- feathered (8 % of the side) and faded in/out over 4 frames at the track's life. No refine.json, or nothing kept: the upscale untouched. The Lanczos fallback has no frame loop: nothing pasted, said on stderr |

## Scheduling (the GPU never waits on a check)

The refine is a fourth job kind on step 09's GPU queue (`studio/take_schedule.REFINE`): behind
every first render and retake, ahead of the GPU checks; refines ordered while one waits join it.
The CPU lane orders it the moment a take's dq lands PASSED (a take with a dq cure is retaken, not
refined). After the ladder, `step_09_shoot.refine_rest` refines whatever is still owed (a retake,
a swapped attempt) in one GPU run. Inside the script the work is pipelined: a take's crops are
queued on ComfyUI the moment it is tracked; the CPU gates each take while later crops render.

## The clock

Priced at 110 s of GPU per face per 192 frames (F2 on the 4090). Counted on the episode clock:
the refine stamps its own `face_refine` row (`within: takes` inside the lanes). **The refine is the
first thing cut for time:** it runs only while the reserve holds its price AND a full measuring
pass after it (`face_refine.cut`: `leaves_reserve(step, price + 550 s)`); a cut is logged
(`REFINE CUT`) and recorded in refine.json (`status: cut`), and the take ships unrefined. A
measuring check is never cut for a refine.

## Proof (Jekyll ep01, 2026-10-17)

See the tracker for the per-take decisions and the minutes; the master is
`library/<jekyll>/episodes/ep01/cut/master_iter8.mp4`.

## Publishable

A standalone ComfyUI node pack, "face-track region refine for ref2v video" (track, crop, H3 v2v
re-render with the person's sheet, gate, feather-paste at upscale scale), plus the measurement
(face height share vs readable detail on H3). Temporal Face Detailer covers SDXL only; nothing
public does this for H3/ref2v video.
