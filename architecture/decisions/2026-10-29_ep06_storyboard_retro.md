# 2026-10-29 — ep06 storyboard retro: one man drawn twice, caught nowhere

Status: BUILT 2026-10-29 (owner: "We need to fix the storyboard .. and make sure this doesn't happen in the
future"; "Build all").

## What happened

Jekyll ep06 shot 25's panel drew Utterson twice and no Poole: the over-the-shoulder staged the near man's face
sheet beside the far man's and the drawer copied it. The people count (2 for 2), G-TWIN (same face AND dress)
and every eye passed it; G-WHO ran on takes only, and its fair-vs-grey fix had hidden this exact case. The take
opened on the panel and morphed Utterson into Poole inside half a second, before the 1 s head the take check
skips; warp was flagged, the retake cap spent, it shipped flagged. Repairing it then hit four walls: the panel
rung priced at 1900 s never fit a repair's reserve; the redraw rounds had gone to earlier fixes; the failed panels
put shots 24/25 on refs_only.json for good, so their takes opened on the bare place picture; and an owner order
naming T24/T25 still found them frozen.

## What changed

- A `studio/back_view.py`, `grids.back_turned`: a man seen only from behind in every cell of a grid is drawn
  from words, no face sheet staged.
- B `scripts/audit/who_fixture.py` + `tests/test_g_who_replays_its_calibration_set.py`: every G-WHO rule replays
  real, eye-judged reads.
- C `panel_ladder.RUNG_SECONDS` 600 s; `panel_ladder.reopen` under an owner redo of 08.
- D+E `refs_only.lift_passing` after step 08's ladder.
- F `repair_clock.named_takes`, `take_currency.frozen_in`: a take an owner order names is not frozen.
- G G-WHO on panels (`panel_content_check.who_check`) and on each take's 0.25 s head (`who (head):`); hat as a
  one-way key.
- H the lesson in the episode skill (LESSONS_ARCHIVE "Jekyll ep06 storyboard retro").
