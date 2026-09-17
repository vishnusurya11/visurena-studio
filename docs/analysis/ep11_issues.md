# Episode 11 — what the build found (2026-09-17)

*A Flight for Life*, published as https://youtu.be/ZC7AWsoTrlo — `master_iter1.mp4`,
163.95 s, −14.3 LUFS, QC PASS, sha8 `395b8b9a`, 25/25 takes, $1.42 of images.
Built under every gate the ep10 analysis produced, the day after they landed.

## The clock

| stage | seconds | share | runs | note |
|---|---:|---:|---:|---|
| lines | 3549 | 19 % | 13 | seven of the runs were re-listens after line edits |
| frames | 248 | 1 % | 3 | two plates set aside by hand (letterbox, mirror) |
| sheets | 323 | 2 % | 1 | six sheets, seven panel redraws |
| takes | 11630 | 63 % | 4 | 25 first takes 7021 s; 11 + 2 + 2 retakes |
| take_dq | 1311 | 7 % | 6 | |
| title | 428 | 2 % | 1 | overlapped the DQ on the GPU |
| assemble | 588 | 3 % | 5 | four refusals before the one that cut |
| qc | 470 | 3 % | 1 | |
| **total** | **18561** | | | **5.2 h of stages, 5.9 h wall** |

Against ep10 (5.0 h): the takes stage was the same length, the retakes were
fewer minutes (2960 + 536 + 536 s against 3808) and the time went instead into
the plan loop — thirteen line runs — and four assemble refusals.

## What the new gates did
- **G-SIZE, G-STORY, G-LIGHT-SIDE, the take lints**: the plan went through
  nine contract/gate refusals before its first render, every one free and
  every one a fault ep10 paid the GPU to find (sizes drawn a class off,
  reported speech over a face, a wordless tail, a dialogue line second on its
  shot, a projection over the wall at the narrator's real rate).
- **face-at-end, look, wide churn, zoom per segment**: 9 of 25 first takes
  failed, 6 on off-board — and 5 of those 6 were PANS (a pan reveals picture
  beyond the cell by design; T08 read 0.06 as a push and 0.48 as a pan of
  the same shot). The wall is pan-aware now (`OFFBOARD_HARD_PAN` 0.60).
- **the plate gate**: two letterboxed rolls refused, the third filled the frame.
- **the short-take gate**: two lines edited after the render made two shots
  longer than their takes; the join filled 88 frames with duplicates and only
  the frame count at the end noticed — `assemble` now names the takes first.
- **the DQ window**: the DQ judged the render record's placed seconds, not
  the timeline's; a shot shortened to end before its take's fault was judged
  on the old length three times. Fixed; and best-of-N now ignores an attempt
  too short for its shot.

## The faults that reached the reviewer
1. **The zoom word overruns in BOTH directions.** Three pull-backs on closes
   ran 0.43–0.71× off their panels; a push clipped a crown. Every retaken
   close took a PAN with an edge object kept and passed. Rule in the skill.
2. **Re-stagings**: the turn (T13) turned its starry night into a lit garden
   twice; the exit (T06) dissolved and cut at 3.3 s three times. The turn was
   fixed by a shorter line (less time for churn); the exit in the cut — the
   shot placed ahead of the fault.
3. **The bed generator** returned 8–11 s of music for a 26 s ask on six
   seeds; the new short-tone refusal was too strict now that loops are
   crossfaded (`LIVE_SHARE` 0.30).
4. **The sentinel's voice** was designed before the design-time gates (self
   0.54) and his button line sat at 0.58; the recast reads 0.71.
5. **The drawer's steel-pipe gate** on three seeds and two wordings — kept,
   as a five-second wide.

## Open
- The plan loop cost 19 % of the day: thirteen line runs because each edit
  (dialogue dial, turn ratio, projection, sync, take length) was found by the
  next gate. A single `plan_check` that runs the contract, the gates, the
  G-RATE projection, the sync rule and the per-shot take length together —
  before any render — would have made it two.
- `identity_gate.observe` and the wardrobe measurer (from ep10's list) are
  still unwritten; identity held again by the sheet reviewer alone.
- The take-length check at retake time: a re-render's placed seconds must be
  the timeline's at that moment; the builder reads placed.json, so it is,
  but nothing prints it.
