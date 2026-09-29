# The place behind the character changes from panel to panel — five-agent debate and the plan

Date: 2026-09-28. Trigger: the owner on ep14's grids: "the background keeps on changing for the
character … you were getting them properly in the previous 20 episodes." Five agents, one angle
each, read-only: the Sherlock archivist, WotW ep01-11 forensics, the grid code historian, the
skill/process auditor, the stager/measurer. Their reports are condensed here; the debate is §3.

## 1. What is on disk (measured, ep14)

- Within one render the place holds; between renders of the same setup it does not.
  Panel pairs from the SAME render score 0.56 / 0.47 (light profile / wings structure);
  pairs from DIFFERENT renders 0.31 / 0.27. ep06's few renders: 0.18 / 0.31 vs 0.07 / 0.22.
- `biology_class` (5 shots, 2 renders): both renders keep the plate's orientation (blackboard
  LEFT, sash windows RIGHT) but grid b dresses a tall glass cabinet and a hanging lamp the plate
  has not. `waterloo_station` (5 shots, 2 renders): a true MIRROR — plate rails bottom-left;
  s05, s08 rails RIGHT; 3x1_a is a small kiosk platform, 2x1_b a columned hall with a gun train.
  `attic_room` (12 shots, 6 renders): attic / street from the dormer / a ground-floor doorway /
  the street, on one NIGHT establishing picture under prose asking for dawn.
- Staging is clean (doll check reproduced every `inputs` hash and read every grid PNG's embedded
  graph): one place file per setup, the setup's own view, no `example.png`, the place in the last
  slot, the same slot doubling as the style anchor.
- The grid code's place mechanics did not change between ep11 (held) and ep12-14: same v2 prompt
  (`fd7fc75`), same seed rule (`40500 + Σ shot index + bump`, per grid), same last-slot place, all
  90 grids ep09-14.
- Prose idiom: capitalised frame-position tokens per shot (LEFT/RIGHT/CENTRE/TOP third) — ep09
  7.7, ep10 6.1, ep11 4.2, ep12 5.7, ep13 5.0, **ep14 0.0**; "edge" tokens 2.83/shot in ep14.
  No ep14 wide carries the setup geometry; ep09 5/5 did. ep14's `geometry`, `landmark` and
  `route` fields ARE filled but `grids.py` never reads them (`SETUP_FIELDS = location, view,
  described`).
- `brief_place()` assumes `described` has the shape "name: …; the light is …". ep14's writer wrote
  inventories with no colon and no light clause, so every 1x1 close received the whole attic +
  street list as its place line (`ep14_grid_attic_room_1x1_s22.txt`).
- Ladder volume: superseded grids ep09 2, ep10 0, ep11 0, ep12 0, **ep13 33, ep14 16**. Each
  redraw is a fresh seed for ONE grid of a setup; its siblings keep theirs.

## 2. How the earlier episodes held it (three different mechanisms, all now absent)

| era | mechanism | evidence |
|---|---|---|
| Sherlock ep01-14 | ONE empty plate per setup at that hour, drawn first, staged as **Image 1** with "Image 1 is the empty location: every panel is set in this exact place, with its architecture, furniture, windows and light"; ONE sequence sheet per setup (≤9 panels, faces and wides together, story order); a GEOMETRY block pinning every fixed thing to a frame edge at a size + the 180° line sentence; a landmark ladder measured on the cut cells (`route_gate.door_height`, >25 % regression refused) and NO-TWO-PANELS-ALIKE (0.70) | `frames.py`, `episode_seq_board.py:1083,1118`, `seq_boards.py:120-160`, `ep14/boards/sheets/seq_sitting_room_evening_0.prompt.txt` |
| WotW ep05-08 | one or two renders per setup; the place picture the ONLY reference in 3 of 7 grids and the style anchor; v1 clause "the location is identical in every panel and never changes -- the same ground, the same horizon, the same weather and the same hour" | ep06 grid PNG graphs; `storyboard_grid.py:72-78` |
| WotW ep09-11 | many 1x1 renders per setup, BUT every cell's prose pinned the same landmarks to the same frame positions ("the white gate behind her at the RIGHT third, black smoke TOP third"), written BY HAND AFTER the place was drawn; hand layouts grouped by content (`lawn_3x1_wides` / `lawn_3x1_faces`) | `ep09/storyboard/grids/ep09_grid_lawn_3x1_*.txt`, LESSONS.md ep09 entry |

ep14 had none of the three: 2-6 renders per setup on independent seeds, no constancy sentence,
geometry unread, cells written by an LLM that had no picture (step 02 plan → step 03 places),
and the ladder re-sampling one grid at a time.

## 3. The debate

**Is the 2026-09-28 grid cap (9 → 4 cells) the cause?** Historian and stager: no — the superseded
one-render attic 4x2 already showed attic / street / doorway; the split multiplied the drift.
Forensics: ep11 held with SIX 1x1 renders per setup. Verdict: not the cause; keep the cap
(blur is measured: 8 cells → 88 % of panels under 0.5 sharpness).

**Is it the writer's prose or the fragmentation?** Forensics: the prose (0.0 position tokens).
Stager: constancy is per RENDER — the drawer re-dresses the room once per render whatever the
prose says (biology: same edges, different cabinet). Both are right and they are the two
independent levers the old episodes used: ep06 held on one render with weak prose; ep09-11 held on
many renders with pinning prose. ep14 pulled neither. A rule that depends on the writer producing
pinning prose is a rule that fails on the next writer draft; a rule built from pixels does not.

**Words or pictures?** Sherlock and stager: the plate was Image 1 and named as "the empty
location"; in WotW it is the LAST slot and also the style anchor, after 1-2 cast sheets. The
SCARLET_ARCHIVE line the auditor found says it plainly: "Words cannot substitute for a picture. No
gate in studio/ is cross-sheet." The drawer follows prose over the plate whenever the prose speaks
(memory: H3 obeys direction, not amount; the same holds for Qwen-image on grids).

**Is a gate the fix?** Stager: a mirror gate catches waterloo s05/s07 but NOT the biology
re-dressing; a VLM furniture-per-wall list would, later. Auditor: the cross-panel gate was filed
"not to build" pending the owner's D4 and never ruled. Verdict: a gate is the second line; the
first line is construction (one render, or chained renders).

**Does anything now work AGAINST the place?** Yes, two things, both latent: the panel ladder's
only place-related cures push a panel AWAY from the plate ("closer in than the place picture and
turned from it", "composed differently from every other shot of this place"); and the
2026-09-24 decision text says "a recurring place is never pinned to one picture" while the owner's
2026-09-17 ruling (memory `project_no_single_baker_street`) says the opposite: PIN it.

## 4. The brick

**A place is held by pixels, not by words: every panel of a setup is conditioned on the SAME
picture of that place — one render, or later renders conditioned on the first render's own panel —
and a cell's words only pin what that picture leaves free (which edge, what size), never what
the room contains.**

It regenerates the results: Sherlock (plate as Image 1 + one sheet) held; ep06 (one render, plate
the only reference) held; ep09-11 (plate + cells written from the picture) held; ep14 (six
renders, cells written before any picture, plate last) did not. It predicts: a redraw of one grid
without re-chaining its siblings drifts (ep13 33 redraws → hedge LEFT in the 3x2, RIGHT in ten
1x1s).

## 5. The plan (sequenced; nothing touches the ep14 run in progress)

### P1 — chain the renders of a setup (code, ~3 h, test-first) — `scripts/episode/grids.py`, `studio/storyboard_grid.py`
1. The first grid of a setup holds its WIDEST loose shot (layout orders by size, not plan order).
2. Every later grid of that setup stages the setup's first-drawn loose panel (a cut cell) as its
   place reference **in slot 1**, named "Image 1 is this exact room, already drawn: every panel is
   set in it with the same walls, furniture, windows and light"; the plate is staged beside it
   only when the grid holds a wide. Staleness cascades for free: `inputs` hashes the staged bytes,
   so a redraw of the anchor grid re-draws its siblings.
3. Restore v1's constancy sentence in the multi-cell clause ("identical in every panel and never
   changes -- the same ground, horizon, weather and hour").
4. The GEOMETRY block: `Setup.geometry` + `landmark` at `landmark_at`/`landmark_size` pasted into
   the prompt (the fields exist; Sherlock's `geometry_block` is the template).
5. `brief_place` reads a `place_head` (first clause up to the first comma or colon) and the light
   from `Setup.light`; no shape assumption. A contract check refuses a `described` that names a
   second place (street nouns in an attic).
6. Remove the ladder's `copy`/`repeat` cures; the place-related cure becomes "the same room as
   <imageN>, seen closer".

### P2 — cells are written FROM the picture (process, ~1 day) — decision file, Future tab
Split step 02: 02a the writer drafts setups, shots (size, section, motion), lines; 03 draws the
places; 02b a picture-reading pass (VLM) lists what stands at which frame edge in each place
picture and the writer (or a deterministic composer) writes `at_rest` from that list — the SKILL's
own rule "cells from the drawn picture, never before", which the org chart inverted on 2026-09-24.
Until 02b exists, P1's chaining carries the load.

### P3 — the cross-panel gate (needs D4) — `studio/judges/panel_eye.py`
`panel_place`: for every loose panel, light-profile + light-side against the STAGED reference
(read back from the grid PNG graph) and pairwise across the setup's renders. Advisory first;
calibrated on ep06 and ep09-13 before it is a wall (a threshold calibrated on one episode accuses
correct work). Exempt a shot whose prose names a reverse. Re-dressing needs the VLM rung:
"list the furniture on the left wall / right wall" judged in code against the plate's list.

### P4 — setup hygiene (contract)
A setup is one place at one hour from one side; reinstate the retired "no setup over ~25 s"
as MAX_SETUP_SECONDS with MAX_SETUPS raised, so a one-scene chapter under G-COVER splits into
attic / dormer view / doorstep / street (ep11 did exactly this with three views of one location).

### Owner rulings needed (docs/DECISIONS.md)
- D4: build the cross-panel place gate (recommend YES, advisory → wall after calibration).
- Pin vs never-pin: recommend PIN — a recurring location has one book picture; per-episode views
  are drawn FROM it (an edit at the setup's hour), never fresh. The 2026-09-24 decision text
  must be corrected.
- D3 (the 2x2 minimum): moot under the 4-cell cap; close it.
- The ladder's place cures (P1.6): removal is a taste change on a judged gate.

### ep14 now
The takes are rendering on the current panels. Its master gets the full watch; if the place
drift reads on screen, ep14 iterates on P1 (master_iter2) — the owner judges, the ladder does not.

## 6. Time and cost
P1 ≈ 3 h code + one grid stage on ep15 (or an ep14 iteration) to verify: $0, local.
P2 ≈ 1 day. P3 ≈ half a day + calibration run over five episodes' panels (CPU). P4 ≈ 1 h.
