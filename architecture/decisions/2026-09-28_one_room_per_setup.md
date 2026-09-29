# 2026-09-28 — One room per setup: chained grid renders, cells from the picture

Status: DECIDED (owner, 2026-09-28: "fix all that") and BUILT the same day — tracker
`architecture/plan/2026-09-28_one_room_per_setup.md`; ruling in `docs/DECISIONS.md`.
Debate and evidence: `docs/audit/2026-09-28_grid_place_constancy_plan.md`. As built, item 2
below is the second half of step 03 (`03_03 cells`) rather than a split of 02: the writer still
drafts the whole plan; 03 rewrites `geometry` and every `at_rest` from the pictures it drew.

## The finding
ep12-14's storyboard grids draw a different room per render of one setup. The grid code did not
change between ep11 (held) and ep12 (broke); what changed is that a setup is now split into 2-12
independently seeded renders by rule, redrawn one at a time by the panel ladder, from cells an LLM
wrote before any picture of the place existed. Sherlock held the room with one empty plate per
setup as Image 1 and one sheet per setup; ep06 with one render per setup; ep09-11 with cells
written by hand from the drawn picture.

## The rule proposed
A place is held by pixels: every panel of a setup is conditioned on the same picture of the place —
one render, or later renders staged on the first render's own cut panel as Image 1. Words pin only
what the picture leaves free.

## Org-chart changes
1. **step 07 (board)**: layout orders a setup's grids by size (widest first); grids after the first
   stage the setup's first-drawn loose panel as the place reference. No new step.
2. **step 02 (plan) splits into 02a draft / 02b cells-from-picture**, with 03 (places) between
   them; 02b reads each place picture and writes `at_rest` from what it shows. New unit of work:
   the picture read. (Future tab.)
3. **EYE_PANELS** gains a cross-panel rung `panel_place` (advisory until calibrated) — needs the
   owner's D4.
4. The panel ladder's `copy` / `repeat` cures are retired (they push a panel off the plate).

## Owner rulings requested
D4 (cross-panel gate), pin-vs-never-pin (recommend PIN; corrects the 2026-09-24 decision text),
D3 closed as moot, the cure change.
