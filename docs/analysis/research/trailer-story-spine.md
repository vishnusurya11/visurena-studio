# The trailer's story spine

Run 10 (A Study in Scarlet) was watched by its owner, who said: *"this looks
more like a song than a trailer."* The story-side reading agreed and named the
cause in one line — **there was no spine.** What shipped was a score-ranked
list of setups scattered on the music grid, played twice, with one spoken line
laid over the wrong man's face.

This document says what the spine is, what rules enforce it, and what run 10
would have looked like under them. Everything here is derived from
`screenplay.json` and `story.json` by code; no model is asked which moment
matters.

---

## 1. The brick

A trailer is not a playlist of good frames. It is **three movements in order**:

| | | what the viewer now knows |
|---|---|---|
| **M1** | world & hook | there is a person, and a place |
| **M2** | problem & turn | something has gone wrong |
| **M3** | threat & climax | somebody is doing it, and has not been caught |

Everything else in this document is a consequence. The order is the product:
`trailer_order.one_each` plays the beats **in the order it is handed them**, so
the list order of `TrailerBeat`s *is* the trailer's order. Run 10 handed that
function a score ranking and asked `best_scatter` to space it out — and
`best_scatter`'s only objective is "do not bring an image back soon". It has no
notion of before and after, so the trailer had none either.

### Where the two cut points come from

Both are read off the screenplay, both are arithmetic:

* **M2 → M3 is the story's own break.** `turn_of` finds the first scene of the
  longest run in which the lead is absent. On Scarlet that is scene 11 — the
  point where the narration changes hands and the book becomes Jefferson
  Hope's. On Jekyll it lands on *Henry Jekyll's Full Statement*.
* **M1 → M2 is the end of the lead's introduction** (`introduction_end`): the
  prefix of the screenplay that holds nobody the first scene did not already
  have. On Scarlet that is scenes 1–2, the Criterion bar and Bart's — Watson,
  Holmes and Stamford. Scene 3 brings Lestrade, and Lestrade is the problem
  arriving.

Where the two marks would collide they are pulled apart, because a movement
with no scene in it cannot be ordered and its quota has nowhere to spend.

### Quotas, not counts

`movement_quota(n)` splits `n` shots **25 % / 45 % / 30 %** and always sums to
`n`, with every movement guaranteed at least one shot once `n >= 3`. Shares
rather than constants, because the trailer's length is not a constant: step 06
fits the walk to the takes the render budget affords, so twelve shots today and
forty-one shots after the render cycle is shortened get the same shape.

`arc` (`quiet` / `build` / `hit` / `aftermath`) is now derived from the
movement (`trailer_plan.arc_of`), not from a beat's index in a score-sorted
list. Run 10's `arc` was stamped from list position, so B00–B05 were "quiet"
because they *scored highest*, and the gate that refuses a trailer which "never
reaches a climax" passed by construction. An arc that cannot fail is not a
gate.

---

## 2. Withholding the answer (R4)

A whodunit trailer sells one question. Run 10 answered it twice before
seventeen seconds: the killer's face writing RACHE at 8.75 s, the killer
handcuffed at 17 s. The spoiler filter it had (`resolution_scenes`) is
*structural* — the last 15 % of the book plus the last lead/figure meeting — so
it banned scenes 20–22 and never noticed scenes 10, 11, 18 or 19.

The replacement is a semantic fact that is still fully derivable:

> **`identity_scenes`** — the answer is the FIGURE standing where the LEAD
> stands: the same room, or the same company.

Both halves are already in the screenplay. On Scarlet it names

* **scene 11** — the police-station chamber (Hope in custody, with the two
  detectives who were at Lauriston Gardens),
* **scene 18** — 3 Lauriston Gardens by night (the room Holmes searched),
* **scene 19** — Halliday's Private Hotel (ditto),
* **scene 20** — 221B (already restricted),

and leaves Utah entirely alone. Utah is the figure *before anyone is looking
for him*; it gives nothing away, and it is most of the second half of the book.

Two rules follow:

1. **Late only.** An identity-revealing setup may occupy only a shot index at
   or after `late_floor(n) = int(0.75 n)`. Selection reserves exactly that many
   slots for them and places them last inside M3, so the arithmetic cannot be
   violated by a later reorder.
2. **Never a full face.** `choose_sizes` caps any shot carrying a character
   reference at `BOUND_FLOOR`, so `medium` is the **widest** a bound shot may
   be. `build_plan.hold_wide` takes exactly that for a reveal — the man in the
   room, not his eyes — unless the cut is too short to read a medium, in which
   case the grammar's own size stands (an unreadable frame gives nothing away
   either).

`restricted_scenes` from `story.json` are now passed into selection and never
photographed at all. They were not before: run 10's B04 and B11 are both scene
21, which its own `story.json` had already listed as restricted.

---

## 3. The line on the speaker's face (R3)

Run 10 spoke one line in a hundred seconds, and laid it over the wrong man:
Holmes's *"You have been in Afghanistan, I perceive"* at 29.755 s, over B23 —
John Ferrier lowering Lucy onto the Alkali Plain.

The mechanism: `assign_lines` has always required the speaker to be in the shot
the line starts on, but that path is bypassed once `lines.json` and `voice.json`
exist. The window path (`step_06_plan.windows`) placed lines by **time** and
never asked the shot who was in it.

`step_06_plan.speak_on_face` closes it:

* the line does **not** move — it was chosen for that window's music;
* the **picture** moves: the shot under the window is swapped with the nearest
  shot *of the same movement* whose frame holds the speaker;
* if the speaker has no face anywhere in that movement, the line is not laid at
  all, and `plan.json` records `lines_refused` with the reason.

Narration plays over any picture; a swap never crosses a movement, so R3 can
never buy a line at the cost of the spine.

---

## 4. The ranker by function (R12)

Seventeen of run 10's twenty-four candidates were brain-attic aphorisms. The
cause was arithmetic, not judgement:

* `KEPT_BONUS` / `BOLD_BONUS` were **6.0 / 2.0** on a line value spanning about
  −10 … +4. The Wikiquote flag *was* the ranking.
* `analysis/iconicity.json` had resolved `where: "character"` — the Wikiquote
  page for the **character** Sherlock Holmes, a century of Holmes across every
  adaptation, rather than this book.
* `TOP_N = 24` and `RELABEL = 10`, so the labeller never saw past rank ~44.

Offline re-rank of the shipped pool: *"Rache, revenge."* #30, Hope's *"You dog!
I have hunted you…"* #178, *"Now, Enoch Drebber, who am I?"* #663, *"Choose and
eat."* #664. **The model did not choose wrong; it was never offered the right
lines.**

Four changes, all in `step_04_lines.py`:

1. **The bonus becomes a modifier**: 2.0 / 1.0, multiplied by `WHERE_WEIGHT`
   — book 1.0, author 0.5, character 0.25.
2. **The bonus also becomes a quota**: `kept_seeds` reserves four seats for
   kept lines, editor-bolded first. Wikiquote is real evidence; it is not a
   ranking. As a quota it keeps the signal and hands the rest of the window
   back to the book.
3. **The confrontation enters whole**: `confrontation` takes the figure's last
   `CONFRONTATION = 14` lines of the climax scenes (`climax_scenes` — the
   identity scenes plus the story's turn, less the resolution), **in the order
   he speaks them**. A confrontation is a sequence — ranking its sentences against each
   other by lexical value is exactly what buried *"Choose and eat."* Its tail
   rather than its head, because a trailer's threat and last word come from
   where the scene lands.
4. **Every role gets candidates**: `role_seeds` reserves two per role by the
   marks a role leaves in the text (a question for the hook, second person for
   the threat, risk vocabulary for stakes, `will`/`shall` for the promise, six
   words or fewer for the button). A labeller cannot label a threat it was
   never shown.

`TOP_N` is 30. On the run-10 pool the window is now **19 / 30 screenplay** (was
7 / 24) and holds *"Now, Enoch Drebber, who am I?"*, *"Choose and eat."*, *"You
dog!"*, *"I have hunted you from Salt Lake City to St. Petersburg…"* and
*"You have been in Afghanistan, I perceive."*

---

## 5. How much is said (R1, R2, R8, R9, R11)

**`music_only` is a refusal, not an outcome.** The ladder is now
`relabel_next_10` ×2 → `drop_story_rules` ×1 → `music_only`. The first two
rungs gate on the *story* rules and quote the violation back to the labeller;
the third drops those rules rather than ship a silent trailer. Only a slate
that cannot satisfy the **contract** ends in silence.

The story rules, each phrased as something a LABEL can fix:

| rule | test | refusal handed to the labeller |
|---|---|---|
| R1 | `wanted_speech(runtime, MAX_LINES)` — `ceil(5 × runtime / 100 s)`, floor 3, capped by the contract | "the slate speaks 1 line and this trailer needs 4; label more spoken lines…" |
| R2 | the hook's window opens by `HOOK_BY = 12 s` | "the hook opens at 38.9 s…; label a shorter line as hook" |
| R8 | the last spoken line is a question or a threat | "the last spoken line 'No data yet.' closes the trailer…" |

R2 was *unreachable* before, for a reason nothing had noticed: `WINDOW_BAND`
started at **0.2**, so on a hundred-second bed no line could be laid before
twenty seconds. It is now `(0.0, 0.8)` — the upper edge stays, because a line
laid over the title card is a caption.

The runtime is read from the plan's own end where a plan exists, and from the
cue otherwise. It is never a constant: step 06 fits the walk to the takes the
budget affords, so a 25 s cut and a 100 s cut are different films and are asked
for different amounts of speech.

**Cards (R9).** A card is *read*, and eight words is what a viewer reads in a
shot: `CARD_WORDS = 8`, and never two cards in a row. Run 10's two cards were
eighteen and eleven words, back to back at 48.66 s and 68.3 s. Both now fail
`playable`, and the adjacency rule is enforced in `fill_roles`.

**The narrator may speak.** `narration_pool` marks its sentences speakerless,
which made every one a card — so the framing the narrator exists for could only
ever ship as prose on screen. `voiced` gives the top `VO_LINES = 3` narration
candidates the narrator's voice. He never plays the hook or the last word:
those belong to the people the story happens to.

**Thesis never null (R11).** `step_01_story.fallback` used to write `None` when
the model's refrain broke the contract. It now cuts the refused answer back to
the shortest clause the contract accepts (`thesis_from`), and the contract does
the accepting so the rules live in one place — length is fixed by cutting, a
name is not. The thesis then joins the labeller's window as a reserved
candidate, so it reaches the screen as a card or in a voice.

---

## 6. Nobody owns the trailer (R10, R6)

Run 10 gave Holmes **26 of 51 shots**, and nine of his twelve setups were the
same three-quarter deerstalker face with an orange lamp behind it. 221B took
**39 % of the seconds**. Lucy, Drebber and Stangerson had reference sheets and
were never cast at all.

`_cap_faces` holds `PRINCIPAL_SHARE = 0.45` and `PLACE_SHARE = 0.30`. The
**earliest** appearances of a face are kept — they are the ones that introduce
him — and appearances past the ceiling are swapped for a setup of the same
movement, on the same side of the reveal line, showing somebody else. A quota
may never reorder the story or move the answer earlier. Where the book offers
no other face inside the place ceiling, the place ceiling gives by one: half a
trailer of one man is the louder fault.

---

## 7. What run 10 would have looked like

Twelve takes at the measured render cycle is a ~25 s trailer. Replayed on the
run-10 screenplay (`tests/fixtures/scarlet_scenes.json`), with movement bounds
`(2, 11)` and quotas M1 3 / M2 5 / M3 4:

```
 #  mv  arc        scene  location                     bound to
 0  M1  quiet      sc01   criterion_bar                sherlock_holmes
 1  M1  quiet      sc02   st_bartholomews_hospital     sherlock_holmes
 2  M2  build      sc03   221b_baker_street            sherlock_holmes
 3  M2  build      sc05   number_3_lauriston_gardens   sherlock_holmes
 4  M2  build      sc06   number_46_audley_court       (plate)
 5  M2  build      sc07   221b_baker_street            john_watson
 6  M2  build      sc08   221b_baker_street            sherlock_holmes
 7  M2  build      sc10   221b_baker_street            (plate)
 8  M3  hit        sc13   utah                         john_ferrier
 9  M3  hit        sc17   scotland_yard                jefferson_hope
10  M3  hit        sc18   number_3_lauriston_gardens   jefferson_hope   <- answer
11  M3  aftermath  sc19   hallidays_private_hotel      jefferson_hope   <- answer
```

Watson meets Holmes; the body, the constable, the pill-box; then Utah, the cab
outside Scotland Yard, and Hope over Drebber. Eight locations, Holmes in 5 of
12 (41 %), the answer at indices 10 and 11 — both at or past `late_floor(12) = 9`.

With a slate of four lines against a 120 BPM cue, the picture (23.0 s) reaches
three windows, and `speak_on_face` brings a face to each of them:

```
 #   start   mv  scene  bound to           line
 0    0.00s  M1  sc01   sherlock_holmes    "You have been in Afghanistan, I perceive."  (0.5s)
 1    3.88s  M1  sc02   sherlock_holmes
 2    5.12s  M2  sc07   john_watson        "There is a scarlet thread of murder."       (8.5s, VO)
 3    9.12s  M2  sc05   sherlock_holmes
 4   11.62s  M2  sc06   (plate)
 5   12.25s  M2  sc03   sherlock_holmes
 6   14.62s  M2  sc08   sherlock_holmes
 7   16.00s  M2  sc10   (plate)
 8   16.50s  M3  sc17   jefferson_hope     "Now, Enoch Drebber, who am I?"             (16.5s)
 9   17.50s  M3  sc13   john_ferrier
10   18.00s  M3  sc18   jefferson_hope
11   20.00s  M3  sc19   jefferson_hope
```

Three spoken lines, none refused, the hook at 0.5 s, and every line on the face
that says it — against run 10's single line at 29.755 s over John Ferrier.
Shots 2 and 8 were swapped up from 5 and 9 by `speak_on_face`, each inside its
own movement.

One ordering fact makes this work: `reachable` gives the orderer only the
windows the picture actually reaches. Step 04 orders against the CUE (88 s) and
step 06 cuts a picture as long as the takes afford (23 s); without the filter
the slate spread its four lines over 0 / 24 / 56 / 80 s and three of them fell
off the end — one line in a 23 s trailer, run 10's disease at a shorter length.

Compare what shipped: sick man examined (sc11) at 0 s, **Hope writing RACHE at
8.75 s**, first sight of Holmes at 11 s, **Hope handcuffed at 17 s**, then Utah
one shot at a time between 221B, and the same twenty-five images again from
50 s.

---

## 8. Where the rules live

| rule | code | test |
|---|---|---|
| movement bounds, quotas | `studio/trailer_story.py` `movement_bounds`, `movement_quota` | `tests/test_trailer_story.py` |
| movement ordering | `studio/trailer_story.py` `select_by_movement`, `_regroup` | `tests/test_trailer_story.py`, `tests/test_step_06_plan.py::TestTheSpine` |
| arc from movement | `studio/trailer_plan.py` `arc_of` | `tests/test_trailer_plan.py` |
| delivered order, Kendall tau >= 0.4 (R7) | the whole step | `tests/test_step_06_plan.py::TestTheDeliveredOrder` |
| identity late-only (R4) | `studio/trailer_story.py` `identity_scenes`, `late_floor`, `_third_movement` | `tests/test_trailer_story.py::TestIdentityScenes` |
| reveal never a close-up | `scripts/trailer/build_plan.py` `hold_wide` | `tests/test_step_06_plan.py::TestTheAnswerIsNeverACloseUp` |
| line on the speaker (R3) | `scripts/trailer/step_06_plan.py` `speak_on_face` | `tests/test_step_06_plan.py::TestSpeakOnFace` |
| lines aimed at the picture, not the cue | `scripts/trailer/step_06_plan.py` `reachable` | `tests/test_step_06_plan.py::TestWindowsThePictureReaches` |
| ranker by function (R12) | `scripts/trailer/step_04_lines.py` `quota_fill`, `confrontation`, `kept_seeds`, `role_seeds` | `tests/test_step_04_lines.py::TestRun10Regression` |
| speech minimum (R1/R2/R8) | `studio/trailer_dialogue.py` `wanted_speech`, `story_refusal` | `tests/test_trailer_dialogue.py::TestHowMuchIsSaid` |
| cards (R9) | `studio/trailer_dialogue.py` `playable`, `no_second_card` | `tests/test_trailer_dialogue.py::TestCards` |
| narrator VO | `scripts/trailer/step_04_lines.py` `voiced`; `trailer_dialogue.VOICELESS_ROLES` | `tests/test_trailer_dialogue.py::TestNarratorVoice` |
| thesis never null (R11) | `scripts/trailer/step_01_story.py` `thesis_from` | `tests/test_step_01_story.py::TestThesisIsNeverDroppedForLength` |
| face and place share (R10/R6) | `studio/trailer_story.py` `_cap_faces` | `tests/test_trailer_story.py::TestNoOneOwnsTheTrailer` |

Fixtures: `tests/fixtures/scarlet_scenes.json` (run 10's screenplay, trimmed to
three authored setups a scene) and `tests/fixtures/scarlet_line_pool.json` (228
candidate lines drawn from the four pools). Nothing under `tests/` reads
`library/`, and nothing here spends a credit.

## 9. Not implemented

* **R5** (zero duplicate `image_prompt`s) and R7's second half (no repeated
  25-shot window) are properties of the *cut*, not of selection; the one-take-
  one-shot invariant in `TrailerPlan` already makes them unreachable.
* **R1's "≥ 5 spoken lines per 100 s"** cannot be reached while
  `LineSlate.MAX_LINES` is 4. `wanted_speech` computes the true figure and then
  caps it at the contract; raising the contract is a change to
  `trailer_stage_spec.py`.
* **R2's "threat ≤ 55 % of runtime"** and **R9's "≤ 5 cards"** are satisfied by
  construction (`targets` aims the threat at its share of the span; the slate
  holds at most four lines) rather than by a rule of their own.
