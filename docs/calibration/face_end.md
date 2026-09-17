# face-at-end calibration -- episode 10, 2026-09-16

`studio/face_end.py` reads ONE frame of a take -- the last frame of its first
segment (the frame before the second pin, else the last frame) -- with OpenCV's
YuNet (`studio/models/yunet.onnx`, 232 KB, CPU) and judges the largest face on
it: box height / frame height, and whether the box touches an edge.

Source: every kept take in `library/20260822113400_a-study-in-scarlet/episodes/ep10/takes/r2v/T*.mp4`
and every superseded render in `.../takes/r2v/attempts/`, 768x768, plus the
plan's `size` and `faces` for the take's first shot.  The prototype was DQ
analyst H's `faces_end.py` (`scratchpad/dq10/H/faces_end.json`); the numbers
below are the shipped module's own run (`opencv-python-headless==5.0.0.93`,
YuNet score 0.5, NMS 0.3, edge = 8/768 of the frame), 6 s for 40 files.

Labels: the reviewer's frame strips from the DQ brief -- fault = WATCH or
RETAKE on the render the reviewer saw: T03, T04, T05 (`T05_fail2`), T12, T15,
T16, T20, T25, T28, T29 (`T29_fail1`).  Of those, the face-out-of-frame class
is T05_fail2 (nostrils), T16, T25, T28; T05_fail1 (the first render, ended on
nostrils) is the same class.

## The table

| file | size | planned faces | h | edge | row |
|---|---|---|---|---|---|
| T05_fail2 | close | 1 | 0.85 | left | HARD (fault) |
| T05_fail1 | close | 1 | 0.85 | -- | HARD (fault) |
| T14 | close | 1 | 0.83 | top | HARD -- **the accepted false alarm** (KEEP: a whole close, hair on the edge) |
| T16 | medium_close | 1 | 0.81 | top | HARD (fault) |
| T25 | close | 1 | 0.77 | -- | HARD (fault) |
| T28 | close | 1 | 0.74 | left | HARD (fault: the profile leaving as he turns to the window) |
| T27 | medium_close | 1 | 0.73 | -- | ok |
| T08 | close | 1 | 0.69 | -- | ok |
| T05 | close | 1 | 0.68 | -- | ok (the kept pull-back) |
| T22 | close | 1 | 0.68 | top | ok -- clipped under `CLIPPED_HARD` (KEEP; two-shot take read at its pin) |
| T18 | medium_close | 1 | 0.63 | -- | ok (two-shot take read at its pin) |
| T13 | medium_close | 1 | 0.59 | -- | ok (zoom 2.16x, the zoom row's false alarm) |
| T10 | medium_close | 1 | 0.51 | -- | ok |
| T07 | medium_close | 1 | 0.40 | -- | ok |
| T12 | medium | 1 | 0.38 | -- | ok |
| T29 | insert | 0 | 0.38 | -- | ok (Lucy intrudes on the insert; no planned face, no wall) |
| T01 | medium | 0 | 0.28 | -- | ok |
| T04_fail1 / T04 | medium | 1 | 0.28 / 0.22 | -- | ok |
| T21 | medium | 2 | 0.27 | -- | ok |
| T33 | medium | 1 | 0.26 | -- | ok |
| T31 | medium | 1 | 0.24 | -- | ok (read at its pin; the second segment is hands) |
| T15_fail2 / T15 / T15_fail1 | medium | 2 | 0.23 / 0.17 / 0.13 | -- | ok |
| T06 | medium | 2 | none | -- | advisory: no face found, 2 planned (Young's back to camera, Ferrier under 0.15) |
| T00, T02, T03, T09, T11, T17, T20, T24, T26 and their attempts | wide / insert | 0 | none | -- | ok, none planned |

## The walls

```
FACE_END_HARD = 0.75    h at or over this on a close / medium_close with a planned face
CLIPPED_HARD  = 0.70    a box touching an edge counts only from this height
SIZES         = {close, medium_close}
```

Against the face-out-of-frame class: 5 hits (T05_fail1, T05_fail2, T16, T25,
T28), 1 false alarm (T14), 0 misses.  The zoom wall on the same faults reads
three false alarms (T13 2.16, T17 1.73, T02 1.72).  Margins: above the wall
T25 0.77 (+0.02); below it T27 0.73 (-0.02) -- two hundredths each way, one
take each.  On the clip floor: T28 0.74 (+0.04) against T22 0.68 (-0.02).  This
is a fit to fourteen labelled faces, not a separation; the strong cases
(0.81-0.85) are clear by 0.08.

## Why a size floor on the clip

The interface asked for "0.75 or clipped".  Read at the segment's end frame
instead of the file's last frame, T22 (a two-shot take: Lucy's close, then
Ferrier) reads 0.68 with the hair line on the top edge, and the reviewer kept
it -- the storyboard cell for a `close` is drawn without headroom (dq10/G
§5), so a whole face touching the top is the picture as drawn.  A box at an
edge is composition when it is small and a face leaving when it is large;
T28's 0.74 leaving frame-left is the fault.  Hence `CLIPPED_HARD`.

## What the row cannot see

- A face turned away (T29_fail1, the back of a head where Lucy was staged):
  the advisory fires on "no face found" only; a frontal read from YuNet's five
  landmarks (both eyes present) is the next measure, inside this row.
- T06: Young's back and Ferrier's face under the readable size read as "no
  face found (2 planned)" -- an advisory the plan earned by staging two faces
  in a shot that shows one back.
- A hand that reads as a face (T24 0.80, score 0.53): quiet because the
  insert plans no face.  The score threshold (0.5) is YuNet's default; the
  wrong-object reads sit at 0.53-0.70 and the real faces at 0.75-0.95, so a
  higher threshold would also do it, at the cost of T28 (0.67).

## Not in the repo

`.gitignore` line 78 (`models/`) matches `studio/models/yunet.onnx`; the file
is on disk and in the module's path, and needs `!studio/models/yunet.onnx` (or
a download step) before it can be committed.  Origin: OpenCV zoo,
`face_detection_yunet_2023mar.onnx`, md5 `4ae92eeb150c82ce15ac80738b3b8167`.
