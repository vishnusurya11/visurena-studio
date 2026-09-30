# Build: the batched ladder (2026-09-30 decision)

**Status: built** — Phases A, B and C landed; follow-ups tracked below.

- [x] Phase A — judge truthfulness: beard per row, crowd waives count, print scoped
  by size, dusk in DAY_WORDS, pass-through advisory · `b5e41e3`
- [x] Phase B — `studio/take_ladder.py`: `BATCH` rung (tries 2), `cure_of` / `route`
  / `renders_of` / `signatures` / `progressed`, `count_round` records signatures,
  `ROUNDS_CAP` 4 → 2, `still_curable` asks the router, `take()` runs free cures
  (head cut, timeline trim) roundless then one batched render · tests:
  `test_the_ladder_batches_every_cure_in_one_round.py`,
  `test_a_frozen_take_is_cured_by_its_cause_in_one_batched_round.py` (renamed from
  the seed-first claim), `test_a_row_that_repeated_on_a_fresh_seed_skips_the_seed.py`
  and `test_the_take_ladder_remembers_its_rounds.py` recalibrated
- [x] Phase C — `plan_gates.crowd_faults` (G-CROWD wall) + `plan_gates.expects_text`,
  wired into `scripts/episode/plan_check.py`; architecture page steps 02 and 09
  updated in the same commit

## Follow-ups (not yet built)
- [ ] Content cure as code: panel redraw then ONE render (`retake_shot`); until then
  content is terminal (still / keep_best flagged) — measured 3/21 by re-render, 1/1
  by panel redraw
- [ ] Wardrobe-prose text-prop lint on the refs side (lettering born in sheets)
- [ ] panel_place calibration over ep06/ep09-13, then promotion from advisory
- [ ] Shadow-bench promotion path for demoted judges: pass-through's PASS_WALL
  benched on WotW owner rows

## Log
- 2026-09-30 — debate ran (5 experts), verdict `docs/audit/2026-09-30_rounds_debate.md`;
  A committed `b5e41e3`; B and C built the same day.
