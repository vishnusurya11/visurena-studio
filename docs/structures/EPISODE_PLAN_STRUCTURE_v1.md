# EPISODE PLAN STRUCTURE v1 (2026-10-01)

THE HELD STRUCTURE: planning is FILLING THIS, never figuring it out.  Five experts
(empirical-structure, slot-contract, consistency-lookups, compiler-completeness,
money-budget) measured all 29 shipped plans, every gate, and the spend ledger; the
chair's rulings close their disagreements.  The owner's walls: **<= $3 per episode,
plan step <= 30 min, fully automated.**  This file is versioned — v2+ may add
alternative skeletons; the SECTIONS are the contract, their numbers are the knobs.

Sibling verdicts: docs/audit/2026-10-01_plan_hours_debate.md (why free-writing cost
4.5 h / $4.11), docs/audit/2026-09-30_five_hour_plan.md.

---

## 1. THE PIPELINE (what replaces the old writer ladder)

    bind -> LOOKUP CHECKS (22, O(1), $0) -> ONE writer call (creative core only,
    <=15k tokens) -> COMPILER (deterministic, $0, seconds) -> battery ->
    plan_repair cures -> [only CREATIVE faults: ONE micro-call per field] -> judge signs

Cost math: one luna call at ~15k in / ~8k out ≈ **$0.013**; a worst case with three
micro-calls stays under $0.10.  Time: call ~3-6 min + seconds of compiling/checking.
The old failure (169 calls, $4.11, 4.5 h) is structurally impossible: the mechanical
80% is never asked of a model.

## 2. THE SKELETONS (empirical; template the ANCHORS, range the middle)

Measured invariants across 29 plans (full list in the expert report; the binding ones):
- hook = shot 0, wide, narration (29/29); ONE turn at 48-77% (median 63%); ONE button
  at the end: a NON-LEAD's ~5-word dialogue line on medium_close/close (28/29).
- 4-6 setups (6 is the norm), ~4 shots per setup; dialogue ONLY on medium_close/close,
  always the first line of its shot; 19-31 lines; dialogue 3-9 lines, 2-4 voices,
  10-20% of words (the 20% ceiling binds often — keep headroom).
- Sizes: medium 26%, medium_close 25%, insert 19% (1 per ~6 shots, faceless), wide 15%
  (<=25% with full), close 12%; 0-4 silent shots (wides/inserts, never turn/button).
- Beds 3-7, first at shot 0, tones from the five; beat vocabulary {0, .5, .6, .8, 1.0,
  1.2, 1.5}; the button's breath >= 1.0 s before it.

**Skeleton A — 23-shot standard** (the WotW default): 0 hook(wide) · 1-3 setup(A, one
dialogue on mcu) · 4 transition(wide, B) · 5-9 friction(B, one dialogue) · 10 spike ·
11 reaction · 12-13 friction · 14 TURN(~61%, mcu) · 15 reaction(close) · 16-17
spike(D) · 18 answer(~80%) · 19-20 runout(E) · 21 BUTTON(non-lead, 1-6 words) · 22
optional silent tail.  ~270 words: ~17 narration @ ~14w, ~5 dialogue @ ~7w.

**Skeleton B — 28-shot extended** (big chapters): A's shape with a 4-shot opening run,
a mid-episode return to A or a new D, answer ~85%, silent wide tail.  ~340 words.

**Skeleton C — 20-22 compact** (thin/aftermath chapters): one shot per section, turn
at 60%, answer 80-85%, button last, no tail.  ~240 words, 3-4 dialogue lines.

**Chair's rulings on the risks:** the MIDDLE (friction/spike/reaction/transition
interleave) is filled from the chapter, never fixed; dialogue slots are a RANGE (3-9);
the turn's speaker is free (not the lead in 13/29); a single-room chapter may hold one
setup for its whole run (no per-setup quota wall); per-slot word budgets derive from
the narrator's MEASURED rate (series_rate), not 3.0.

## 3. THE CREATIVE CORE (all a model is ever asked for)

The writer call fills ONLY (full schema + field audit in the expert report):
- `title`, `question` (Armstrong form), `protagonist`, `answer`, `omit`
- per setup: `described` core (place nouns + the LIGHT SOURCE noun; >=90 words),
  `geometry` (>=60w), `cast`, `crowd` (count + activity), `ambience`, `landmark`,
  `route`, `location`+`view` (picked from the book's tables), `outdoors`, prop candidates
- per shot slot: `section` (from the skeleton), `size`, `faces`, `extras` (the book's
  count), `frame`, `motion` (move + what acts), `camera`, `at_rest` (>=40w), `end`,
  `changed`, `source` (verbatim chapter spans), `turn`, `why`, `sounds` on loud events
- per line: `kind`, `speaker`, `text` (<=18w; narration never lifts >8 book words;
  dialogue lifts freely — prefer the screenplay's pre-adapted lines), `shot`, `delivery`
- `beds` (tones are authored, never derived)

NEVER asked (compiler-owned): numbering/refs, beat_s/coda_s, head fractions, light
DIRECTIONS, pace words, head repairs, prop filtering, look/style/aspect/light/where,
edge casing.  The brief for the one call KEEPS unit/band/scenes/chapter-text/
screenplay/cast-rows/picture-rules/dq-rules and DROPS the 25k camera catalog (a
10-line move digest instead) and the places' visual/design prose (ids only).

## 4. CONSISTENCY = LOOKUPS (the "floating/character" template checks)

Ten tables (cast rows T1, chapter-cast T2, wardrobe-by-chapter T3, places+views T4,
drawn pictures T5, place-state-by-chapter T6, props T7, setup-cast T8, room anchor T9,
cross-episode places T10) -> **22 O(1) checks at the TOP of plan_check**, before
anything else: cast stamp; face bound+sheeted; face IN THE CHAPTER; group-not-a-face;
face in its setup; wardrobe matches the chapter; constants quoted from rows never
retyped; location/view legal and chapter-legal; SHOT view belongs to its setup's
place; picture drawn and in the chapter's state; hour agrees with the scene; a
wide/full anchor per setup; prop in registry + chapter + sheeted-or-words-only +
right state + declared when named; recurring-place advisory; speaker on camera.

Proof of value: run by hand on ep15's SHIPPED plan they catch three faults no gate
sees (the artilleryman absent from ch15; shot 16 wearing another place's picture; the
field gun out of its chapters).  13 data gaps for bind to close are listed in the
expert report (present[] into refs.json, marks, state lists, a places_used index...).

## 5. THE COMPILER (guarantees, and the build list)

GUARANTEED today (plan_cures): numbering, head fractions, light directions, paces,
button beat, prop filter, series pinning, edge casing, the holds algebra (floor,
pairs, setup cap).  BY-CONSTRUCTION via the skeleton: word floors, variety ratios,
dialogue share/placement, one-hook-one-turn-one-button, non-lead button, <=2 lines a
shot, <=6 setups, G-COVER/G-ORDER (the slot walk follows the chapter's paragraphs),
ambience present, source-span-with-claim.  IRREDUCIBLY CREATIVE (micro-call or
author): word-choice rules, G-SCALE prose, span invention, story-shape judgments,
over-MAX_SECONDS word cuts, the answer's content.

**New compiler rules to build (expert 4, algorithms in its report):** 1 camera-move
ROTATION over the full catalog with a frequency table (replaces the 2-move swap — the
biggest gap); 2 travel-amount clamp; 3 ignored-move substitution; 4 hole-patch beats;
5 renumber must remap `omit`; 6 path-monotonic clamp; 7 sub-shot spacing; 8 G-SYNC
line reorder (+renumber after); 9 bed-tone fold; 10 loud-event auto-cue.

**Fixed compile ORDER** (cures were a hash-ordered set — a live bug): renumber ->
pin_series -> legal_props -> text cures -> edge_cases -> path/sub-shot -> head cures
-> G-SYNC(+renumber) -> hole-patch -> holds LAST.  Also fix holds()'s floor-lift vs
setup-shave oscillation (protected minimum on what the floor-lift added).

## 6. THE MONEY WALL (<= $3/episode, enforced, never advisory)

Measured: luna = $0.20/M in, $1.20/M out; 100% of all episode LLM spend ever is step
02; the overspend lived INSIDE rungs (3 unmetered retries) and across unmetered
re-runs.  Build (expert 5's 9-step order, smallest first): `spend.by_step_unit` ->
fill the dead `Cost.usd` -> $ in `--report` -> 50%/80% one-shot alerts -> a
`MoneyBudget` mirroring run_budget (ceiling $3.00, charged from the usage ledger
across resumes) -> the hard pre-call gate in `llm.structured` (raises OverBudget;
the crossing call never fires) -> folded into judged_gate's affordable so a money
wall terminals exactly like a time wall, with a distinct "budget spent, not plan
bad" deferral line.  SHARES (owner to ratify): plan $2.00 / ladders pool $0.50 /
slack $0.50 — note a $0.50 plan share would have refused ep13, the only clean plan
($0.76).  Under this structure a plan costs ~$0.01-0.10, so the wall is a fuse, not
a constraint.

## 7. VERSIONING

This file is the structure of record.  A new skeleton, a changed knob, a new lookup
or cure lands as v2 with a dated changelog line here; the owner picks between
versions per book if they diverge.  Every number above is measured or marked as the
owner's to ratify.

CHANGELOG
- v1 2026-10-01: born from the five-expert debate; chair rulings as stated.
