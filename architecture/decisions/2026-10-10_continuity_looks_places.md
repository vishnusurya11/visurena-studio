# 2026-10-10 — Continuity: character looks on a story timeline, places as masters

**Status:** RULED (owner, 2026-10-10). Phase 1 (the minimal slice, 9 commits) BUILT 2026-10-10 —
tracker [../plan/2026-10-10_continuity_build.md](../plan/2026-10-10_continuity_build.md).
Phases 2-4 PROPOSED.

The debate: `docs/audit/2026-10-10_continuity_retro/` — investigations A (character
timeline), B (house refs), E (quality); research C (character state), D (location), F
(H3 workflows), G (image post); plans P1 (continuity) and P2 (quality + speed); and the
BINDING verdict S (`S_skeptic_verdict.md`), which this file follows.

## The two complaints (WotW, 27/27 shipped)

1. **The narrator looks like episode 1 in episode 27.** The book greys his hair and grows
   a beard in ch22; ep26-27 show grey hair in 0-1 of about 24 panels. Cause: one sheet
   per character, drawn in the first look, staged everywhere; the story-time look was
   words only, and a staged picture beats words on the face. The row text also carried
   two heads ("dark brown hair … shaven" + "ash-grey … beard"), so no gate could fire,
   and the take's retention line ordered H3 to keep "the clothes of <Picture k>" while
   k showed another look (costume changes mid-take: ep18 T0, ep24 T0, ep25 T0).
2. **The house is a different house.** Every new view of a recurring place was a fresh
   text-to-image draw from that episode's words (`places.py`, since 2026-09-22): the
   dining room is three rooms under two ids, the study six. The 2026-09-28 ruling
   "per-episode views are drawn FROM the pinned picture" was never built.

WotW is finished; nothing shipped is re-rendered. The fix prevents the next book.

## Owner rulings, 2026-10-10 (settled)

- **Per-state character looks on a story timeline.** This reverses the 2026-09-18
  "one picture per entity" rule *for story-time looks only*; places and props keep it.
- **One hop, never a chain, never a composite.** A look or a place state may be a ONE-step
  edit of the base sheet or the place master. An edit is never made from another edit,
  and nothing is pasted from one picture into another (so P1's `keep_head` is cut).
- **Budget:** at most 6 h of machine time per 2-3 min episode.
- **No re-render** of shipped episodes.
- **Workflows:** never edit an existing ComfyUI workflow; a new one is a new file
  `<base>_<source>.json` with its manifest.

## The brick

A recurring entity is ONE base picture (a character's sheet, a place's master). Every
story-time state is ONE derivation from that base, recorded in a table keyed by story
time (`refs/looks.json`, `refs/places.json`). Each take stages the picture of the state it
is in, and the words describe that picture. One look table plus one place table resolves
the picture for every (setup, person) and every setup's place; nothing is chosen by hand.

## Phase 1 — the minimal slice (9 commits, test-first, all fakes)

1. These docs.
2. `studio/continuity_spec.py`: `Look` (interval chapter[/scene], layers, closed-vocabulary
   markers, parent = the base sheet's sha8), `Place` (members, masters, optional states).
   Star topology validated.
3. Body/layers split: a row never carries two heads (the body holds no hair, facial hair
   or hat); `panel_content.contradictions` and `take_content.drifted` compare **markers**.
4. A look-timeline producer every book has: an agent over the script supervisor's
   `state_changes` (+ `physical_evolution` where present), quotes verified at 0.85 (the
   G-SOURCE matcher). `looks_from_dossier` reads WotW's `wardrobe_by_chapter` format.
5. Staging: `look_sheet`, `grids.sheet_of`, the `cast_sheet` look rung, `reference_list`;
   the retention line true by construction; the step-06 lint (subject look = staged look).
6. `scripts/refs/looks.py` at step 03: the one-hop route per delta kind (no head paste),
   and LOOK-STATE (headwear, hair colour, facial hair HARD; the rest and identity advisory).
7. Places: membership by aliases + fuzzy match; G-LOOK and G-PLACE with **code cures**
   (rewrite to the default look or the member/master, recorded); the brief lists drawn
   views and history and drops undrawn ids.
8. `places.py`: a state variant is a one-hop 2511 edit of the master (existing workflow);
   a new side is drawn once and frozen; a DINO same-place band flags.
9. Step 03 wiring, `stages.yaml`, SKILL/GATES/LESSONS, the *Current* tab.

### Gates and levels (verdict S)

| gate | where | level | cure |
|---|---|---|---|
| G-LOOK | plan battery | HARD, code cure | an unresolvable look id → the chapter's default look, recorded |
| G-PLACE | plan battery | HARD, code cure | a new location id that fuzzy-matches a Place member, or a view that is neither drawn nor derivable → the member / master, recorded |
| G-LOOK-WORDS | plan battery | ADVISORY (refuses nothing until replayed on all 27 WotW plans) | strip the contradicting marker word from the person's own clause |
| LOOK-STATE | step 03, each new look picture | HARD on headwear, hair_colour, facial_hair; advisory on top, dirt | redraw seed+1 with the faulted layer first; cap 2; terminal keeps the best, flagged |
| relative identity | inside LOOK-STATE | ADVISORY until the bench measures it | — |
| same-place band (DINO) | step 03, each derived variant | FLAG | — |
| G-LOOK-PANEL | step 08 | ADVISORY in the slice; HARD only at recall ≥ 0.8 and false refusals ≤ 0.1 over all ep01-27 narrator panels | a panel redraw |
| G-LOOK-TAKE | step 09 | LOG ONLY (never HARD: its only cure is a re-render, 3/21) | — |

### What the slice cuts or defers, and why

- **`keep_head` (paste the base's head back): CUT.** It is a composite.
- **Production designer agent: phase 2.** Code groups places by aliases + a 0.85 fuzzy match.
- **New workflows (relight, multi-angle, 2.1 Consistency): phase 2.** The existing
  `image_qwen_image_edit_2511_single_image.json` covers the one-hop state edit.
- **`derive:` inside `view`: CHANGED** to a separate resolution (A73: every value the
  contract can sign, every consumer can say).
- **GeomCons G-PLACE-FIXED, G-PLACE-STATE, the "panel IS the sheet" advisory: phase 2.**
- **Routes per delta kind** default to *edit* for garment-only looks and *fresh* (the
  base row's own prompt and seed, the look's layers first) for face changes, until bench
  B-3 picks; flipping a route is one table row.

### Acceptance (artefact, not tests) — needs the GPU, prepared, not run here

CPU half, run 2026-10-10 (`uv run python scripts/refs/continuity_replay.py 20260827135508`):
G-LOOK 0 rewrites; G-PLACE 0-2 a plan over all 27 WotW plans (8 in all, each read:
ep26 `narrators_dining_room` -> `narrators_home/dining_room_unlit_night`, ep27 `reverse`
-> the study master, six framing/state views -> their masters with the state kept);
G-LOOK-WORDS 7 advisories. GPU half, prepared (outputs only under the retro folder):

    uv run python scripts/refs/look_replay.py 20260827135508 25 fulham_road 2 2 --shots=0,2,3,4 --out=docs/audit/2026-10-10_continuity_retro/replay
    uv run python scripts/refs/look_replay.py 20260827135508 27 study_table 2 2 --shots=2,3,12,13 --out=docs/audit/2026-10-10_continuity_retro/replay
    uv run python scripts/refs/place_replay.py 20260827135508 --out=docs/audit/2026-10-10_continuity_retro/replay/house


A bench replay of one ep25 grid and one ep27 grid with the look pictures: the narrator
shows grey hair and beard in ≥ 80 % of his panels (VLM list plus a contact sheet looked
at), against 0-1 of about 24 shipped. The ep26/ep27 plans replayed: `narrators_dining_room`
and a fresh `reverse` are rewritten to the member/master, not drawn. The villa
`abandoned` variant shows the forced door and sits inside the same-place band. The plan
gates replayed on all 27 WotW plans give ≤ 1 false refusal per plan, each read by hand.

## Phase 2 — judges armed, continuity widened (after the next book's first episodes)

G-LOOK-PANEL HARD at its calibration; the "panel is the sheet" advisory (DINO/SSIM of the
panel against the staged sheet); GeomCons G-PLACE-FIXED fitted on our pictures;
G-PLACE-STATE; the production-designer agent; relight and multi-angle workflows (new
files only); G-LOOK-TAKE as a logged measure. *Acceptance:* the next book's first three
episodes show zero wrong-look and zero new-room faults on the owner's audit sheet, and
add ≤ 1 stop per episode against the ep22-27 average.

## Phase 3 — bench winners in production (P2), Phase 4 — deferred

See S §6. Not part of this build.

## Time

Median today 5.68 h (ep19-27). The slice adds +5 to +12 min (looks drawn once and reused,
derived variants replace fresh place draws, plan gates whose cures are code). P1's claimed
payer (grid turbo) is counted at zero. The P90 stays over 6 h until the plan stage and
stops are debated on their own; it is never "solved" by loosening these gates.

## Publishable (flag)

The continuity bible — typed look and place tables (a script supervisor's breakdown as a
contract), the star-topology derivation rule, the list-then-judge verifiers — generalizes
beyond this repo. It ships after the next book's first episodes prove it.
