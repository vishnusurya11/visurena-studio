# 2026-10-21 -- The drive names every park at t=0 (craft ruling A23)

Status: **BUILT 2026-10-21 (craft and process ruling, wave 3, row A23; the owner accepted the craft defaults
2026-10-21).** The ruling: `docs/audit/2026-10-21_craft_process/RULING.md` section 2, wave 3 (outside git).

## Why

Jekyll ep01's run charged 6.69 h of machine time before step 13 refused a `source/book.json` with no `series`
(drive_run08.log). The proof harness already had an audit of what a chapter needs that the book lacks
(`scripts/proof/preconditions.py` over `studio/rehearsal/preconditions.py`), but no launch read it.

## What changed in the org (architecture)

- **The runner `scripts/episode/drive.py`** runs a preflight after the dry check and before the title cards:
  `preflight(book, n)` = the proof harness's chapter audit (imported, never moved: the harness owns the file),
  the owner's standing hand (`publish/standing.json` lists the episode, G-STANDING) and the YouTube token's age
  (`.env` stamp; a Testing consent dies at 7 days, and the run's 6 h budget is added).
- Each finding is one line: `refuse now: ...` or `will park at step N: ...`. Only a gap no step runs past
  refuses (no chapter text: no plan); the launch then writes a refused run (`refused: preflight`). Every other
  finding is printed and sent once, and the run goes on to its first park. A publish-only gap always parks.
- A book whose records cannot be read is said (`preflight: book records not read ...`), never a crash.

## What did not change

The dry check, the dirty-tree rule, the title-card bake and every step are untouched. Nothing is written by the
preflight. Test: `tests/test_the_drive_names_its_parks_at_t0.py` (a sandbox book with no `series` prints "will
park at step 13" at t=0).
