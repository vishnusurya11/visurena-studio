# Expert B: the people-class gates on Jekyll ep07 (read-only, 2026-11-10)

`E` = library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/episodes/ep07. `drive_runNN.log` and
`learnings.jsonl` are under `E`. What I could not see is said so.

## 0. Answer in six lines
- G-DEAD at step 10 refused 8 runs. 4 (runs 02-05) were the G-WHO `who:` rule firing on correct Utterson+Enfield
  two-shots: false. 3 (runs 06-08) were the facenet clone check on T10/T17: unproven, plausibly true (a look-alike
  sheet, cured by the sheet redraw). 1 (run 16, T11) was a warp row, not a people gate.
- G-WHO precision on ep07: 0 of 7 takes true. Two are eye-confirmed false (T06, T17); five more flipped from FAIL to ok
  on byte-identical takes when only the gate changed (commit 35b7e603).
- The shot_07 G-PEOPLE block (runs 10, 13, 14, 15, 17) is one frame deciding a ship-block. The refusal text never prints
  the fault line, frame time or count, so five runs and a brain-retire were spent on a line nobody could read.
- Root cause (one rule): "a people line must be confirmed by more than one frame" is coded per detector, not at the
  block. The take `who:` rule has it (CONFIRM=2); the master per-frame fault, `busiest()` and the panel reads do not.
- The panel keep_best "doubles" at shot_00/05/18 were a third background figure, not copies. No double reached the master.
- Fix: `ship_block.master_blocks` (section 5), test written and run. Unproven parts in section 6.

## 1. What the gates are (so the table is checkable)
- G-DEAD: `scripts/episode/assemble.py:758-784` `dead_plan`. `wrong = people_wrong(take_dir)` marks a take "failed"
  whatever the ladder kept (:774-775); `raise SystemExit("G-DEAD refuses the master...")` at :782-784.
- People class: `studio/people_faults.py:14-28`: kind `twin`/`clones`, a line starting `who:`/`who (head):`/`twin`, or
  `N figure(s) for M declared` (EXTRA regex).
- Block list: `studio/ship_block.py:42-47` `blocks()` = `people_faults.wrong` or long leak or scaffold or a line ending
  `where the row says otherwise` (HAIR_LINE, :17).
- Master terminal: `studio/master_ladder.py:145-152` `flag()` raises `REFUSED: G-PEOPLE` when any `v.faults` entry blocks.
- The `who:` rule: `studio/figure_who.py:112-124` `fault()`. Before 35b7e603 two figures that each resolved to Utterson
  were a double. The reader folds black and grey coats (`COAT_FAMILY`, figure_who.py:42) and at dusk calls both men's
  hair white and both hats top hats (35b7e603 message).
- Clone check: `studio/measure/faces.py:59-71` `clone_pairs`: two faces in one frame with facenet cosine >= `DRIFT` 0.75
  (`studio/identity_gate.py:58`). Sheet-time G-CAST measured Utterson-Enfield 0.712 (`studio/cast_faces.py:17`), under
  the wall; in a frame it reads 0.778-0.854 (below).

## 2. Timeline of the 8 G-DEAD runs (`E/drive.jsonl` for shas)
| run | sha | take verdicts that failed | detector |
|---|---|---|---|
| 02 | 2c04b61d | T06 (2 frames), T08, T10, T19, T22 (`drive_run02.log:166-180`, `:594`) | who |
| 03 | 2c04b61d | T08 (3), T10 (3), T12 (2), T19 (2) (`drive_run03.log:684-694`) | who |
| 04 | 2c04b61d | T06 (3), T08 (2), T17 (2), T19 (2) (`drive_run04.log:390-396`) | who |
| 05 | 348c7390 | T06 (3), T08 (2), T17 (4), T19 (2); T10 clones .788/.801 (`drive_run05.log:561-581`; `learnings.jsonl` 2026-10-31T05:52) | who + clones |
| 06-08 | 35b7e603 | content `ok T06 ... ok T10 ... ok T17` (`drive_run06.log:64-84`); G-DEAD T10, T17 (`:133-135`) | clones only |
| 16 | 1029749f | T11 (`drive_run16.log:735-736`); the 08:34Z eye lists only a T11 warp row | warp, not people |

Why 06-08 still refused: the take eye at 2026-10-31T12:36Z names `clones at T10 ... facenet 0.788 / 0.801` and
`clones at T17 ... 0.783 / 0.854 / 0.778` (`learnings.jsonl`). `people_wrong` (assemble.py:732-737) blocks `kind=clones`
via `people_faults.KINDS` (:15). 35b7e603 only touched `who:`.
Brain mis-reads: `autopilot/events.jsonl` 2026-10-31T03:38 and 05:57 park on "who: 2 figures ... shot form is the defect,
redo step 06". The sheets were the cause (commit 348c7390, 35b7e603), not the prompts.

## 3. Per-take true/false table (G-DEAD people lines)
Evidence key: EYE = frame labelled eye-passed in `tests/fixtures/who_reads_jekyll_ep07.json` (commit 35b7e603; images
`E/review/who_frames/T06_2.5s.png`, `T17_2.5s.png`; I did not re-view them). FLIP = same take bytes (`shot_NN_hash` in
the `staged` lines, `drive_run05.log` vs `drive_run06.log`) read FAIL then ok when only the gate changed.
All seven takes stage both sheets (c367d8b2 Enfield, 5fbca766 Utterson) and cast two men.

| take | who: runs | frames | who: verdict | clones (facenet) | clones verdict |
|---|---|---|---|---|---|
| T06 | 02, 04, 05 | 2, 3, 3 | FALSE (EYE; FLIP) | none | n/a |
| T08 | 03, 04, 05 | 3, 2, 2 | FALSE (FLIP) | none | n/a |
| T10 | 03 | 3 | FALSE (FLIP) | .788, .801 | UNPROVEN, plausibly true |
| T12 | 03 | 2 | FALSE (FLIP) | none | n/a |
| T17 | 04, 05 | 2, 4 | FALSE (EYE; FLIP) | .781 .854 .778 .783 | UNPROVEN, plausibly true |
| T19 | 02-05 | 2 | FALSE (FLIP) | none | n/a |
| T22 | 02, 03 | 2 | FALSE (FLIP) | none | n/a |
| T11 (run 16) | - | - | not a people gate | - | warp S 3.78 Se 4.01 HARD |

Owner's note, `E/review/eye_c032c727.json` "notes": "Enfield (beard, grey topper) and Utterson (grey hair, bowler) are two
people in every frame, no doubles" over a 30-frame contact sheet (one frame per 5 s, `FRAMES=30`,
`studio/judges/master_eye.py:46`). That covers the shipped retakes, not the pre-redraw bytes, so the five FLIP-only
rows are inference; the two EYE rows are label-backed.

Why FALSE: the fixture reads for T06 are `[top_hat, brown hair, grey coat]` vs `[bowler, white hair, black coat]`: two
coats, two hats. The coat-family fold (`figure_who.py:42`, black and grey both "dark") plus both men read white-haired
made both resolve to Utterson, hence "2 figures read as Utterson".

## 4. Precision
- G-WHO `who:` on ep07: 7 takes flagged, 0 true: precision 0/7. Every one had >= 2 confirming frames, so the take
  rule's frame agreement (`take_content_check.py:150-163`) could not have saved them; the reader is wrong the same way on
  every dusk frame.
- Facenet clones: 2 takes (T10, T17), truth unproven. Best case 2/2, worst 0/2.
- G-DEAD people-class, per take: 7 distinct takes; upper bound 2/7 = 29 %, verified 0/7.
- G-DEAD people-class, per run: 4 of 8 refusals false for certain, 3 unproven, 1 not people-class.
- Same rule, second hit: ep06 T23/T24 was a documented false twin (`docs/audit/2026-10-30_jekyll_series_retro/skeptic.md:155`;
  RETRO.md:89 "People-gate false positives cost G-DEAD launches: open; calibrate before widening any block").

## 5. G-PEOPLE at step 11, shot_07 (runs 10, 13, 14, 15, 17)
Mechanism (verified in code):
1. The master eye reads ~30 frames, one per 5 s, plus 3 extra frames only inside shots that shipped flagged
   (`master_eye.py:46`, `:153-170`). `read_faults` (`master_eye.py:597-606`) emits ONE `Fault(kind="content",
   where="shot_NN", evidence={"at": t, "faults": [...]})` per frame that disagrees.
2. `ship_block.blocks(fault)` (ship_block.py:42-47) tests one fault alone: no frame count, no duration, no look at the
   take's own verdict.
3. `master_ladder.flag` (:145-152) refuses on any one blocking fault, after retakes that did not move the take
   (`drive_run10.log:395-423`).
4. The message prints the shot only. The fault line, frame time and confirming-frame count are not logged
   (`drive_run10.log:423`, `:445`; `learnings.jsonl` has no master rows). The owner note "hair read white at 0.5 s" cannot
   be re-checked from disk, and the brain (`autopilot/events.jsonl` 2026-11-04T05:29) invented a "who: Utterson twice at
   shot_07" story from stale take rows; shot_07 casts Jekyll alone.
Same shape one level down: `take_content.busiest()` (take_content.py:29-43) UNIONS every subject over a take's frames,
then `drifted()` (take_content.py:80-96, called at :144) fires on any one hair word in any one frame.
Honest gap: I found no code that emits HAIR_LINE from master reads (`judge_staged` is called with no markers,
`master_eye.py:350-356`), so the shot_07 line may have been a people-count line. Either way the block is per-frame.

Brick: a block may stand only on evidence that survives a second look. Confirmation exists as `CONFIRM = 2` in one
detector (`take_content_check.py:150`, written after ep06 T23: "a copied panel or a morph persists; a misread moment
does not"). It was never lifted to the block, so each new block kind (hair line 10-30, master frame, clones) reopened the
hole. A one-frame read cannot tell "persists" from "misread moment".

### Proposed fix
Add to `studio/ship_block.py`; call it from `master_ladder.flag` with the shots the take eye already names, and add the
line text, frame times and count to the REFUSED message.

```python
CONFIRM_FRAMES = 2
"""Master frames a per-frame people fault must show in, unless the take's own eye names the shot (ep07 shot_07)."""

def master_blocks(faults, take_named=frozenset()) -> list[str]:
    """Shots a master verdict may refuse on: a blocking per-frame fault stands on 2+ distinct frames, or when the
    take's eye names the shot, or when it carries no frame (a measured fault: clones, a leak)."""
    rows: dict[str, list[dict]] = {}
    for f in faults:
        d = f.model_dump() if hasattr(f, "model_dump") else dict(f)
        if blocks(d):
            rows.setdefault(d["where"], []).append(d)
    return [w for w, fs in rows.items()
            if None in {(d.get("evidence") or {}).get("at") for d in fs}
            or len({(d.get("evidence") or {}).get("at") for d in fs}) >= CONFIRM_FRAMES or w in take_named]
```
A dropped fault stays in the signed verdict and ships flagged (the master eye's own terminal is `flag`). A one-frame shot
(5 s cadence) whose lone read would block gets the `EXTRA_FRAMES` re-read flagged shots already get, before it may block.

### Failing test (pytest shape; reads as literals)
File: `tests/test_master_people_block_needs_two_frames.py`
```python
from studio import master_ladder, ship_block
from studio.judges.verdict import Fault, Verdict

HAIR = "white where the row says otherwise"   # ep07 shot_07, eye_c032c727.json notes (line text reconstructed)

def frame_fault(where, at, line):
    return Fault(kind="content", where=where, evidence={"at": at, "faults": [line]})

def master(*faults):
    return Verdict(judge="master_eye", version="1", passed=False, faults=list(faults), confidence=1.0, reads=30)

def test_one_frame_of_shot_07_does_not_refuse_the_master():
    v = master(frame_fault("shot_07", 0.5, HAIR))            # the 0.5 s read of ep07 runs 10/13/14/15/17
    assert ship_block.master_blocks(v.faults) == []
    assert master_ladder.flag(v) is v

def test_the_same_line_on_two_frames_still_refuses():
    v = master(frame_fault("shot_07", 0.5, HAIR), frame_fault("shot_07", 3.0, HAIR))
    assert ship_block.master_blocks(v.faults) == ["shot_07"]

def test_one_frame_the_take_eye_also_names_still_refuses():     # ep05 T07: Jekyll grey in every shot
    v = master(frame_fault("shot_07", 0.5, HAIR))
    assert ship_block.master_blocks(v.faults, take_named={"shot_07"}) == ["shot_07"]

def test_a_measured_fault_with_no_frame_stands_alone():          # ep07 T10, take eye 2026-10-31T12:36
    clone = Fault(kind="clones", where="shot_10", evidence={"cosine": 0.801, "by": "facenet"})
    assert ship_block.master_blocks([clone]) == ["shot_10"]
```
Run (CPU, scratch dir, `master_blocks` injected into `ship_block` by a conftest, `flag` unchanged): test 1 FAILS with
`SystemExit: REFUSED: G-PEOPLE ... stands at shot_07 after the master ladder's rounds` (the five-run refusal reproduced
from the real code path); tests 2-4 pass. Without the function all four fail on the missing attribute. Test 1 passes
once `flag` calls `master_blocks`. Scratch copy:
(scratch)/test_master_people_block_needs_two_frames.py

## 6. Replayed effect and what is unproven
- ep07 G-PEOPLE: all 5 refusals (shot_07) drop to flagged IF the 0.5 s read was the only blocking frame, which is what the
  owner's note says. The reads are not on disk: no master learnings row, no per-frame fault text in the logs;
  `review/work/eye_reads.json` holds only the final master's 113 reads (3 say "white hair", all on the two-man dusk
  walk, none shot_07).
- ep07 G-DEAD: the rule does not touch these. Every `who:` line had >= 2 frames and was still false. N=3 would keep T06
  and T10 and drop T08/T12/T17/T19/T22 in their 2-frame runs, but would also drop real doubles; no ep05-06 true-double
  frame counts exist to bound it, so N=3 is NOT recommended. The ep07 cure was apart-by-coat (35b7e603), already landed;
  the clones on T10/T17 were cured by the sheet redraw.
- True-fault guard (ep01-06; `docs/audit/2026-10-30_jekyll_series_retro/owner_vs_gates.md` rows 8-11, `skeptic.md:46`):
  - ep05 T07 (Jekyll grey in every shot): take-level, every frame, the take eye names it, so `take_named` keeps the block.
  - ep05 T22 (Utterson twice), ep05 s06/s22 (shoulder double), ep03 sheet collapse: caught or missed at take or sheet
    level, not by a lone master frame; unchanged by this fix.
  - ep04 shot_18 "3 figure(s) for 1 declared" (row 10): master content, probably >1 frame in a crowd shot and named by the
    panel eye; likely kept, no per-frame data. UNPROVEN.
  - A real double visible in one frame of a one-frame shot is un-blockable by frame count alone; the re-read and the
    take-eye clause are what cover it. UNPROVEN: the master reads of ep01-06 were not kept.
- Also unproven: the shot_07 fault type; whether Jekyll's hair read white in any other frame; the five FLIP-only take
  verdicts by eye; whether clones T10/T17 were true.

## 7. Panel keep_best doubles at shot_00 / 05 / 18: did a double reach the master? No evidence of one
- Panel lines (`learnings.jsonl` EYE_PANELS 2026-11-04T09:01Z): shot_00, shot_05 "3 figure(s) for 2 declared, 0 of them
  copies of another"; shot_18 clones "3 figure(s) for 2 declared, 2 of them copies"; shot_05 `who: 2 figures read as
  'richard_enfield'`.
- The shipped takes (`E/takes/r2v/T00.content.json`, `T05`, `T18`): `people 2, lookalikes 0, panel_people 3, passed true,
  gate_version 13`. The panel shows a third figure; the take it fed draws two men and no copy.
- Owner contact-sheet check (`eye_c032c727.json`): two people in every frame. Limits: 30 frames at 5 s hold at most one
  frame of T05 (4.7 s) or T18, and the content reader samples 3 frames per take.
- Residual: panel shot_05 `who: Enfield twice` survived v13 (`apart()` needs different raw coats, figure_who.py:105-110);
  the final take reads clean. Treat as a panel-only false positive, unproven by eye on the panel image.
- The other keep_best items (framing, orphan limbs 20/21, mirror at 02) are not people-class.

## 8. Recommendations, in order
1. Add `master_blocks` and print the fault line, frame time and count in the REFUSED message. Hiding the evidence cost a
   brain-retire and five runs; the message fix alone is free.
2. Lift the 2-frame confirmation to the block: also `take_content.drifted` over `busiest()` and the panel `who:` read.
3. Add a pre-render distinguishability check on two co-cast sheets using the who-reader (resolve each sheet's read against
   the staged marks; if two men resolve to one member, refuse at sheet time). It would have caught ep07 before step 09.
   Not built, not measured.
4. Close RETRO.md open item 3 (people-gate false positives) before adding another block kind; ep07 is its second hit.
5. Publishable: the 18-case who replay set (`tests/fixtures/who_reads_*`) plus "confirmation at the block" is a small
   benchmark of VLM-attribute twin detection; flag for the paper list.
