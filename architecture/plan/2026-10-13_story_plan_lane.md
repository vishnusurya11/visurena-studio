# 2026-10-13 — Story/plan lane (Jekyll ep01 review)

Status: **BUILT 2026-10-13** — narrator, tale, pacing, plan checks, dialogue camera, the
writer's viewer rules; replayed on all 41 shipped WotW + Scarlet plans.
Decision: `architecture/decisions/2026-10-13_the_book_narrator_and_the_viewer.md`.
Binding: `docs/audit/2026-10-13_jekyll_ep01_review/DIAGNOSIS.md`.

## Commits

- [x] `studio/book_narrator.py` — refs/narrator.json, else the published episodes' shared
      narrator, else unset (85b1720)
- [x] G-SPEAKER reads the book's narrator; brief, alias cure, writer, step 02 stop (6d3d380)
- [x] `tale` line kind (8972e20)
- [x] STUDIO_RATE 2.45, G-PACE, `cut_lines` / `breathe` (12c042b)
- [x] G-ACTION (9e85078)
- [x] the critic lists threat and spike; G-HOOK, G-SPIKE, a nonscene row folds (4234f5a)
- [x] dialogue held: G-MOVES unit, G-STILL, the ladder's actor verb, the builder's
      example, G-TALK (d1925ef)
- [x] the writer's brief: five viewer rules (f9c250c)
- [x] replay fixes: G-TALK counts travel not pans (a3d776a); the move share keeps its
      total (504df6c)
- [x] skill (SKILL/GATES/LESSONS), this page, README, DECISIONS
- [x] Jekyll's `refs/narrator.json` = the dedicated narrator

## Log

- 2026-10-13: built test-first; 41 shipped plans replayed through the new gates; the
  four baseline batteries (WotW ep01/22, Scarlet ep01/09) diffed before/after.
- Open for the other lanes: the VOICE lane casts `cast/narrator/` (speaker id
  `narrator`); Jekyll ep01/ep02 must be re-planned (their plans narrate as
  `henry_jekyll`, now refused).
