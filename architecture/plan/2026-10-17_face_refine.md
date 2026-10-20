# 2026-10-17 — the wide-shot face refine (step 09_07; paste in 10_05)

Status: **BUILT 2026-10-17** — code, tests, scheduler hook, docs. Proof scope cut by the owner the
same morning to 2-3 wide takes (side-by-side clips at master scale, no new master).
Decision: `architecture/decisions/2026-10-17_face_refine.md`. Owner: "I like face improvements a lot
in wide shots, go ahead".

## Commits

- [x] the parts: `studio/face_refine.py` (selection, price, cut rule, cast, positions, match, prompt,
      gate), `studio/face_track.py`, `studio/face_gate.py`, `studio/face_paste.py`,
      `scripts/episode/face_refine.py` (track, match, render via F2's workflow, gate, refine.json)
- [x] matching on ep01's real takes: stitched tracks, readable faces left alone, Lab colour, loose
      sheet detector, positions only from "at the SIDE"
- [x] wiring + docs: `take_schedule.REFINE`, `take_overlap.Refines` + `Shop.order_refine`,
      `step_09_shoot.refine_rest`, `master_upscale.master(wrap=)`, `assemble` layout.json +
      `face_paste_wrap`; the F2 manifest in comfy_studio; page, README, stages.yaml, skill, DECISIONS
- [x] face-blur round 2 (2026-10-19, `docs/audit/2026-10-19_face_blur/PLAN_FINAL.md` 1a-3): tracker ports
      (lost-subject guard, weak faces, body far figures, hysteresis span, frozen side, 17k+5 grid inside the
      shot), the soft paste and its seam, CCIP + clip_vision_h identity (`studio/anime_id*.py`), drift, the
      drawn-eye score (`studio/face_eye.py`)
- [ ] proof clips: T00, T22 (T06) shipped vs refined at master scale under
      `docs/audit/2026-10-16_model_tests/faces/step_proof/` (waits on the shared ComfyUI queue)

## Log

- 2026-10-17 09:00-10:30 PDT: built test-first; calibrated the gate on F2/F3
  (`docs/calibration/face_refine.md`); dry-ran selection/tracking/matching on ep01 (T00 2 faces, T03 none
  small, T06 2, T07 3, T18 2, T22 2); queued the 11 crop renders on the shared queue behind a 32-take bench.
- 2026-10-19 PDT, face-blur round 2: round 1's 15 refined crops re-measured through the new gate with the
  real CCIP / clip worker: all 15 kept (round 1 refused T01 x2 and T07's child on the seam); the walls and
  their evidence in `docs/calibration/face_refine.md`; the GPU arm of round 2 is still owed.
- 2026-10-19 PM, fix round (skeptic): the seam is read where the paste mask falls (the whole-window mean
  diluted a small face's to nothing); wall 18 again; round 1's three stay refused with either paste. The
  tracker links by least cost and holds every head to its own track's reading less 0.15; the stitch no
  longer counts the piece as its own rival. Bench replay: identical tracks.
- 2026-10-19 PM, face-warp fix round 2 (skeptic): the paste is brow to chin and cheek to cheek (round 1's
  outline was 1.1 x 1.3 face heights and crossed the brim, hair, ears and jaw); each redraw frame is re-seated
  on the take's head (H3 jitters 2-3 px at 384); the gate reads the paste the Paster makes: band warp <= 0.9,
  turn (MTCNN eye line) <= 4 deg; older rows regated before the cut. ep01 replay at $0: brim flow 0.70-5.38
  (iter2) -> 0.09-0.45, jaw 1.40-5.30 -> 0.07-0.20; T08, T09, T26 Enfield refused on the turn
  (`docs/calibration/face_refine.md`).
