# 2026-10-27 — judge the cut, upscale once; a master retake changes an input

Status: BUILT 2026-10-27 (Jekyll ep03 retro finding #2, coordinator's go; the owner rule it serves
is 2026-10-18 "cut + face paste first, ONE GPU upscale of the finished picture, no picture edits
after"). For the owner's veto.

## What was wrong (ep03, PDT)

upscale (av3 4x, 3.1 min) 11:26 -> qc 11:29 -> master eye 11:32 -> retake T04 for "faces at
master" -> upscale again 11:46 -> qc 11:49 -> master eye 11:52 -> flag. 14 minutes changed nothing:

- the retake drew a new seed (84206, try 2), it scored 81.7 against the old draw's 81.9, and
  `take_dq --attempts` put the old draw back. The render had rewritten shots.json, and the
  master ladder's fingerprint hashed that file, so it read "changed".
- "faces" measures a face too small at a close (T04: 0.093 of the height, wall 0.12). A seed
  cannot change it; T04 is a spoken over-the-shoulder take whose camera never travels.
- the master eye judged the 4x master, so every master round paid the upscale.

## What changed

1. **A master retake changes an input or is refused** (`studio/master_ladder.py`): the fingerprint
   is what the cut reads (take, heads.json, stills.json); board -> the take ladder's move type,
   faces -> a push; a spoken / locked-grammar / already-pushing shot and repeats/shadow have no
   render cure: `NO-OP master` before any render, a "panel cure owed" row, no round, the flag.
2. **Step 10 makes the judged cut** (`assemble.py --at-cut` -> `cut/cut_r2v.mp4`): the face
   paste at 768 (`master_upscale.AT_CUT`, CRF 8), card, chip, loudness; no upscale.
3. **Step 11 judges the cut** (`qc.py --at-cut` -> `qc_r2v_cut.json`; the master eye reads the
   cut; the master ladder recuts at cut scale), **then upscales once** (`assemble.py --upscale`):
   the cut's sound copied, never re-encoded; `cut/master_iterN.mp4`; `cut/upscaled.json` records
   master sha8 -> cut sha8. The QC report and rubric are carried to the master's sha8
   (`qc_r2v.json`, `review/eye_<master>.json`, `judged_on` naming the cut). `done` holds only
   while upscaled.json traces the master on disk to the judged cut on disk: another file at the
   master's name is upscaled again from the judged cut; a new cut is judged first.
4. **The face strip (log only) is cut from the upscaled master**, the one measure that wants
   full resolution (crops as the viewer sees them).
5. **QC's edit gate reads the cut under its own cap** (`edit_gate.SEGMENT_MEAN_CUT` = 1.6).

## Measured

- Face box share at 768 and at 3072 on ep03's master: 0.134 both. MTCNN: 0.13 s a frame at 768,
  1.34 s at 3072 (the eye reads ~36 frames).
- ep03's own work room through the cut pass: 31 s on the CPU, 130 MB, 3444/3444 frames; the edit
  gate 0.50-1.36 over 28 segments (9 pasted), offset 0, cuts 27/27, tail ok. Under the old
  unrecorded cap (1.0) 11 of 28 failed. One episode: refit the cap when a cut fails it.

## Rollback

Step 10 without `--at-cut` and step 11 on a master with no cut beside it run the old path
(a master from before this change is its own judged file).
