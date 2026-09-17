# Episode 10 — what the careful build found (2026-09-16)

Episode 10, *John Ferrier Talks with the Prophet*, was built under a per-stage
clock with a reviewer at the plan, the sheets and the takes, and a monitor on
the renders. This is the list of what surfaced, ranked by what it would cost
the next episode if left alone. Each item says what was measured, what was done
today, and what is still open.

Master: `library/…/episodes/ep10/cut/master_iter2.mp4` — 175.8 s, −14.3 LUFS,
QC PASS, sha8 `6fe30f38`, 30/30 takes, seven retakes, $1.29 of images.

## The clock

| stage | seconds | share | runs | norm | |
|---|---:|---:|---:|---:|---|
| lines | 1543 | 10 % | 13 | 900 | Ferrier's l27 needed the book-wide reference |
| frames | 192 | 1 % | 1 | 600 | |
| sheets | 444 | 3 % | 3 | 900 | 8 sheets + 4 panel redraws |
| takes | 9810 | 65 % | 4 | 7200 | 30 takes 7002 s; 7 retakes 2808 s |
| take_dq | 275 | 2 % | 4 | 1200 | |
| title | 388 | 3 % | 1 | 120 | SLOW — animation queued behind takes |
| assemble | 389 | 3 % | 2 | 900 | |
| qc | 2137 | 14 % | 2 | 300 | SLOW — 1935 s while retakes held the GPU; 201 s alone |
| eye_review | 8 | 0 % | 1 | 120 | |
| **total** | **15186** | | | | **4.2 h of stages, 4.1 h wall** |

A first-pass episode with no retakes is ~2.9 h; each retake round is ~4–9 min
per take plus a 90 s re-cut and a 200 s qc.

## Issues, ranked

### 1. The push-in has no brake, and nothing measured it — SYSTEMIC
Seven of thirty takes (T05, T12, T13, T16, T25, T28, T33) ended one or two
sizes tighter than the plan; T05 twice ran "a hand's breadth" to an
eyes-and-nose frame. Every gate passed them: coherence off-board, last-vs-cell
and drift all judge resemblance, none judges scale. Words did not hold it
("comes to rest with the whole face inside the frame" — still nostrils).
- Done: shot 5 is a pull-back (cannot end tighter than it began). A CPU
  measurer `studio/take_zoom.py` (phase-correlated window lattice → RANSAC
  similarity → subject-region scale first→last frame; `docs/calibration/
  take_zoom.md`) separates the reviewer's groups: over-pushed ≥ 1.63, fine
  ≤ 1.50, wall `OVER_PUSH = 1.55` (hand/finger), 2.0 (forearm), 2.5 (any).
  Wired into `take_dq` as the `zoom` row after the coherence rows
  (`tests/test_take_zoom_gate.py`) — a SCORED ADVISORY, not a FAIL: the wall
  at 1.55 failed six takes in the cut on the re-read and four were the
  reviewer's KEEPs (T13 2.16, T16 2.40, T17 1.73, T25 2.12: a size tighter,
  face whole). T05's nostrils at 1.93 read the same as T13's whole face at
  2.16 — scale separates pushed from not pushed, not usable from not. The
  episode skill now says a CLOSE takes a pull-back or a pan, never a push,
  and how to order the clauses.
- Open: the whole-frame read does NOT separate the groups (the room zooms
  1.3× while the man is walked at the lens), so the wall is a fit to 14
  labelled takes — recalibrate on ep11. Stride pushes T12 (1.98) and T33
  (1.52) sit under their 2.0 wall; `REACH_WALLS["stride"]` is the one line
  if a stride is to be held to a hand.

### 2. The coherence gate is blind to a background that re-draws itself
T03's house grew a second chimney, a second window and a wider porch between
frame 60 and 157 while the gate posts vanished — off-board 0.00, churn 10.8
*advisory*. The gate compares to the panel as a whole; a wide with a small
change everywhere scores as the same picture.
- Done: motion names what is kept ("both gate posts keep the frame edges, the
  log villa keeps its one chimney and one window"); the retake held the house.
- Open: a plate check for wides — last frame vs the setup plate on the
  landmark region — or a churn wall for `wide` shots specifically.

### 3. The identity gate has never measured anything
`identity_gate.observe` raises `NotImplementedError`; every take of every
episode prints `identity not measured`. Identity is judged only by the sheet
reviewer before the render and by eyes after it. It held on ep10 (reviewer:
same three faces in all 30 takes) — by the sheets, not by a gate.
- Open: implement the facenet-pytorch backend the module documents, calibrate
  on the ep05–ep10 takes.

### 4. Reposition words in a motion are obeyed literally
"turns toward the door" → the man walked past the lens (T15); "goes out through
the gate" → the camera left the porch instead of the man (T20); "walks up the
path toward it" → he stood at a fence while the camera pushed (T04). The skill
already says a reposition is what the model dissolves on; nothing lints it.
- Done: head turns with "shoulders following a hand's breadth"; the walk named
  with what slides past ("the fence posts behind him sliding to the right").
- Open: an M-lint (advisory) for `turns toward|goes out|walks past|crosses` in
  a motion whose subject is the framed face.

### 5. A blurred foreground body in a cell dissolves in the take
T15's out-of-focus Ferrier shoulder at the right edge vanished ~1.6 s in on
both renders. The model cannot hold a soft foreground mass.
- Open: plan rule — a foreground figure in a cell is sharp and whole, or
  absent; add to the plan reviewer's checklist.

### 6. The hygiene sentences ate the prose budget
Sixteen of thirty take blocks overran the 150–240 band once the required
camera/light/at-rest/arrival sentences were in; `frame` and `at_rest` had
been saying the same thing twice. Three more overran after the reviewer's
motions.
- Done: frame ≤ ~35 words (subject + one place cue), at_rest ≤ ~50 words
  (composition only).
- Open: a plan-level advisory in `plan_gates` on frame/at_rest word counts, so
  the builder hears it before the dry build does.

### 7. The take lints are right but the skill does not say how to satisfy them
Three rounds were needed to place the "kept" clauses: the head must be the
camera move (M2), the last clause must be a movement not a layout (the
"ends on a layout" lint), and beats are read from the third clause (M1).
- Open: one paragraph in the episode skill: *camera move first; kept-clauses
  in the middle; a movement last.*

### 8. QC and the title card contend with the renders
qc ran 1935 s (norm 300) with Whisper sharing the GPU with six retakes; the
title animation waited 388 s (norm 120) behind the take queue.
- Open: `run.py` refuses to start `qc`/`title` while the ComfyUI queue is
  non-empty, or the norms are stated per condition. The clock caught both.

### 9. QC's provenance gate worked
The first master was cut while retakes were landing; qc FAILED it on
`provenance ['T03','T04','T05','T15','T20','T29']`. Keep.

### 10. Ferrier's voice sits at the floor
His ep10 lines pass at 0.71–0.74 against a 0.70 floor; l27 needed the
book-wide best reference (ep08, 0.815) after eight tries. A redesign of his
cast voice from the ep08 line would lift the whole book.

### 11. Small
- A 220 MiB master cannot be sent to the owner's phone (30 MiB limit); a
  900 kbps `preview_iterN.mp4` was made by hand — `assemble` could write it.
- The sheet reviewer's Q20 wide has no black floor (accepted, sunlit wide).
- The parlour act repeats (three Young-in-chair, two Ferrier closes) read as
  distinct on screen per the take reviewer; the owner's call stands.
