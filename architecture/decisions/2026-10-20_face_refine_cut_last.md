# The face refine is cut last, a face list closes step 09, and an unread paste measure refuses (2026-10-20)

**Status:** BUILT 2026-10-20 by retro package C, on the defaults of the owner's veto list (V2 "cut last and
park", V3 "120 px stays a refine-eligibility constant, log only"). The owner was shown the list and vetoed
none of V1-V11. The ruling is "do the retro one ... made all changes" (2026-10-20).

**Evidence:** `docs/audit/2026-10-20_deadline_retro/RETRO.md` sections 3 (ranks 2, 3 and 5), 5 (V2, V3) and 6
(package C). The skeptics are `quality_in_first_pass_skeptic.md`, `gates_that_see_skeptic.md` and
`deadline_budget_skeptic.md` in the same folder.

## What changed

1. **An unread outside measure is a refusal** (`studio/face_refine.outside_refusal`). The wall at
   `paste_refusals` refused `outside > OUTSIDE_MAX = 1.0`, but only when the measure was read, so a None passed.
   Now a paste is never made unmeasured. The regate treats a row with no `outside` as stale. A row the regate
   cannot read (no take or crop window) falls back to the take instead of keeping its old `kept`.
   Regression: ep01's iter3 paste record (`tests/fixtures/ep01_face_list/refine_iter3.json`, 16 rows, all
   read `outside` 0.0) re-decides to every stored decision unchanged.
2. **The face list** (`studio/face_refine.face_list`, `scripts/episode/face_refine.face_list`,
   `step_09_shoot.face_list_note`). Step 09 ends by writing one row per take into `takes/r2v/refine.json`
   under `face_list`. Each row holds the take's smallest tracked face in render px, which is cut scale (the
   paste is made on the cut before the one upscale), and whether a paste was accepted. The refine's own
   tracker decides wherever it decided on these bytes, and the warp gate's tracks decide elsewhere. A take
   with a face under `LIST_PX = SMALL_FACE_PX = 120` and no accepted paste is listed and logged as a
   `FACE LIST` line. It is routed to the refine (`refine` while the refine still owes it, `logged` once it
   decided). It never fails the master, and inserts and takes with no planned face are never listed. The
   list is written only when it changed, because refine.json is an input of step 10.
   Replayed on ep01's records:
   - At the first master (the iter1-era refine.json, where only T08 and T18 were pasted), it lists 10 of the
     12 takes the repair later refined. The other two are T00 (166 px) and T19 (120.3 px), which the repair's
     own tracker also read as readable.
   - At iter3 it lists T01, T08, T09 and T26. In those four the walls refused a paste, so they shipped soft.
3. **The refine is cut last** (`studio/face_refine.cut_last`, `reserve`, `REFINE_TAKE_S = 81.0`).
   - From its start, step 09 holds N takes x 81 s, where N is the takes the refine can reach that have no
     standing decision and are not already read at 120 px. 81 s is measured: ep01's repair refine took 972 s
     over 12 takes.
   - `dq_flags` cuts a re-measure of unchanged bytes before that reserve.
   - After the ladder, `refine_rest` cuts the refine only when its own price leaves no reserve. No check is
     owed after it, because a refine changes no take bytes.
   - A take still cut ships flagged, and step 09 writes a `FACE_REFINE` terminal to `learnings.jsonl`. The
     publish lock holds that terminal: it has no gates.yaml row, so no judge clears it. The episode is not
     upload-ready: the upload's lock stops refuse it (`scripts/publish/youtube_upload.lock_stops`) until a
     later pass refines the take (that pass writes a `pass` row) or the owner waives `FACE_REFINE` in
     `review/waiver.json`. Nothing auto-ships.
   - The lanes' early refine and the tiny-face draw keep the old cut-first rule (`face_refine.cut`). A lane
     cut is owed again after the ladder, and a draw re-renders bytes that need their checks.

## What it does not do

- The take ladder's retake rounds (`studio/take_ladder.py`, not this package) price themselves against the
  budget's own reserve. They do not see the refine's reserve, so a retake can still spend the time the refine
  was held. When that happens, the refine is cut and the episode parks: the loss is visible, not silent.
- Step 11 QC does not read the list yet. `scripts/episode/face_refine.read_face_list` and `face_list_line`
  are the reader, and wiring them into `step_11_qc.py` / master_eye is package D's (wave 2).
- `scripts/episode/repair_dry_check.priced` (package A) still prices the refine with the 550 s check
  reserve. That is conservative: it may print CUT where the drive now runs the refine.

## Rollback

Revert the package C commits. `face_refine.cut` is unchanged, so restoring `refine_rest`'s call to it
restores the cut-first order.
