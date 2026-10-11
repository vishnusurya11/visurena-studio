# 2026-10-10 — Continuity build (phase 1, the minimal slice)

**Status:** BUILDING — commit 3 of 9. Decision:
[../decisions/2026-10-10_continuity_looks_places.md](../decisions/2026-10-10_continuity_looks_places.md).
Binding verdict: `docs/audit/2026-10-10_continuity_retro/S_skeptic_verdict.md` §6.

- [x] 1. Docs: decision file, this tracker, the DECISIONS line, README rows, the *Future* tab
- [x] 2. `studio/continuity_spec.py`: Look, Place, star topology, intervals, closed markers
- [x] 3. Body/layers split; `character_row` never carries two heads; contradictions/drifted compare markers
- [ ] 4. Look-timeline producer (agent over `state_changes`, quotes at 0.85) + `looks_from_dossier`
- [ ] 5. Staging: `look_sheet`, `grids.sheet_of`, `cast_sheet` look rung, `reference_list`; step-06 lint
- [ ] 6. `scripts/refs/looks.py` at step 03 + LOOK-STATE
- [ ] 7. Places membership + G-LOOK / G-PLACE with code cures; the brief lists drawn views and history
- [ ] 8. `places.py`: one-hop 2511 state variant of the master; a new side frozen; DINO same-place flag
- [ ] 9. Step 03 wiring, `stages.yaml`, SKILL/GATES/LESSONS, episode_writer continuity, the *Current* tab

Not in this build (GPU): the acceptance replay — the command is written in the log when
commit 6 lands. Republish the claude.ai copy of `architecture/index.html` after commit 9.

## Log
- 2026-10-10: retro (A-G), two plans (P1, P2), skeptic verdict S. Owner rulings: per-state
  looks on a story timeline; one-step edits from the base, never chained, never composited;
  ≤ 6 h per episode; no re-render; new workflow files only. Slice started.
- 2026-10-10: commit 2 — the contract: Look/Span/LookBook (star topology on the base sheet's sha8, closed markers, intervals by chapter and scene, last-start-wins, a look may return), Place/Master/State/Variant/PlaceBook (one place per location, a variant one hop from its master, a derived side never chained); relative paths only.
- 2026-10-10: commit 3 — one head per row: studio/look_table cuts text into clauses by layer (hair, face, headwear), the look's restated head leads and replaces the body's (a look restating none keeps the old bytes); rows carry look + markers; panel contradictions and take hair drift compare the staged look's markers (prose rule kept for rows without); G-LOOK-PANEL as an advisory on panel rows, G-LOOK-TAKE as a log on take rows. Related tests 667 passed; 2 step_05 timeline failures pre-exist at HEAD.
