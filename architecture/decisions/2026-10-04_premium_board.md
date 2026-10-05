# The board, premium — one table, many zooms, one voice

**Status: DECIDED 2026-10-04 — owner: "looks good go".** The full ruling is
`research/2026-10-04_board_design/SPEC.md` (ten reports 01–10 and seven mockups in the same folder);
the tracker is `architecture/plan/2026-10-04_premium_board_build.md`.

**The brick:** every studio tracker is one table (entity × step → state, with versions and notes)
shown at several zooms. The board has the table; the redesign gives it one voice — one component set,
one token set, one state vocabulary — at five zooms: studio (Now) → book → department → unit → shot.

**Palette (owner): dark by default** — "Studio": page #0f1012, raised #18191c, ink #ededef / #b4b6bc / #8e9199, rules #26282d / #34373d, media stage #000. The warm beige is retired; Graphite (#f4f5f7) is the optional light theme.

**The identity rule:** paper is the office, the stage is the screening room, ink is the voice,
colour means state and nothing else.

**Decided with it:** Now as the landing page with an inbox that counts flagged-not-acknowledged
units (a new `acknowledge` order kind — the owner's hand, no judge change); no approve button
(judges sign); hand-drawn SVG charts, no chart library; pulse + morph polling, no SSE; the web
process stays read-only and never decodes video. The pipeline asks (posters, sprites, per-iteration
cut lists, step on timing rows) are separate architecture decisions, not part of this one.
