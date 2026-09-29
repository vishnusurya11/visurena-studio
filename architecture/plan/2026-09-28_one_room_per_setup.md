# One room per setup — build tracker

**Status: BUILT 2026-09-28 — owner ruled "fix all that" 2026-09-28; P1-P4 built the same day; the calibration and the first episode under it are open.**
Decision: `architecture/decisions/2026-09-28_one_room_per_setup.md`; the debate:
`docs/audit/2026-09-28_grid_place_constancy_plan.md`. Nothing here touches what episode
steps 10-12 load, so a live run (ep14 was shooting) is not changed under it.

## Progress

- [x] P1 chained renders — `studio/grid_room.py` (anchor = the setup's widest shot; its cell cut to `storyboard/anchors/<setup>.png`; siblings stage it); `grids.py` stages the room last, the plate beside it only for a wide/full, the style on the last picture, the geometry fields in `SETUP_FIELDS` and the prompt; `storyboard_grid` v2 says "this exact room", v1's "identical in every panel and never changes" is back, `brief_place` takes a place's first clause and `Setup.light`; step 07 draws the anchor first and cuts the room; the ladder's `copy`/`repeat` cures name the same room; a redrawn anchor re-cuts the room and redraws its siblings — 7 test files
- [x] P3 `panel_place` — `studio/measure/place.py` (profile, wings, light side vs the staged room and its mirror); `panel_eye.place_faults` ADVISORY (never fails the verdict, no rung); calibration note `docs/calibration/panel_place.md`
- [x] P4 G-SETUP — `MAX_SETUP_SECONDS = 50` (measured: held plans peak 33-50 s; ep13 hedge 89, ep14 attic 52); a battery wall, advisory on a rendered plan; the writer's brief carries it
- [x] P2 cells from the picture — a new registry step `03b cells` after 03 (no split of 02: the writer still drafts the whole plan; 03b rewrites `geometry` and every `at_rest` FROM the picture): `studio/picture_read.py` (the VLM lists fixed things by third and band, closed vocabulary, behind `comfy.cached_text`), `studio/cells_from_picture.py` (the ep09-13 idiom, the writer's subject sentence kept), `scripts/episode/step_03b_cells.py` (battery re-judges, verdict re-signed, a refusal keeps the writer's cells, never parks); the drift guard covers it — 5 tests
- [ ] calibrate `panel_place` over ep06, ep09-13 (CPU) and promote it to a wall or retire it — a dated row in `docs/calibration/panel_place.md`
- [ ] the first episode drawn under P1 (ep15, or an ep14 iteration): read every setup's panels against its room; log the measured constancy in `docs/audit/`

## Rules for every commit

- Test first; a function does one thing in 10-20 lines; no test touches the GPU, a model or a
  paid API; nothing book-specific in the code tree; every path book-relative.
- A rendered plan is never refused by a wall raised after its render (report mode).
