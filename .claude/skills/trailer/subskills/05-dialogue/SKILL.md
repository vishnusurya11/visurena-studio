---
name: trailer-dialogue
description: Find the lines a culture kept, grade the finder on a held-out corpus, order them hook → answer → threat → title → button, and choose each line for the measured slot it will occupy.
---

# Dialogue — iconic lines and iconic moments

`studio/trailer_dialogue.py`, `studio/trailer_story.py`, `studio/iconicity.py`
(to build). Evidence: `docs/analysis/research/trailer-iconic-lines-and-moments.md`,
`trailer-debate-verdicts.md`. Speaking the lines is `09-voice`.

## The brick — a trailer line needs no scene and takes a side

Length, syntax, position, what to speak and what to set in type all derive
from that sentence. The iconic *moment* is the same thing in pictures: an
image that needs no scene and changes the story.

Neither is a property of the text alone. Both are **what a culture kept**, so
external evidence outranks every text feature, and the text features exist
for the book nobody kept. That makes this stage an *oracle interface*, not a
generator: every candidate arrives as `(text, speaker, kept: bool, function)`.

## Why the previous scorer was inverted (MEASURED)

Against 38 real trailer lines, `line_value` scored 26 negative (median −1.5).
"This is Sparta!" −7.6; every question −6.6; meanwhile an errand from the
Ferrier subplot ("I guess you are the daughter of John Ferrier…") scored 3.1,
above all 38. Two terms did it:

- `< 5 words → −3.0` deleted half the corpus. The median iconic line is
  **4.5 words**; 28 of 38 are ≤ 7. Short is the *format*.
- `? → −4.0` deleted the hook. 18% of iconic lines are questions, all as hook
  or threat, and Lieu's whole technique is a question a later line answers.

Keep what it got right: replies −3.0 (meaning lives in the previous line),
unbound "the X" −2.0, leading pronouns −1.8, numerals −2.5, causal
connectives −1.0. The Cornell memorability study confirms the pronoun and
generality findings independently.

## The finder reads FOUR pools, not the screenplay

Wikiquote lists 19 quotations for *A Study in Scarlet*. **Four** survived
into `screenplay.json`, ranked 39 / 51 / 104 / 158 of 271. The title sentence
("the scarlet thread of murder…") is in `source/chapters/ch_04` and nowhere
in the screenplay. A finder that reads only the screenplay is structurally
blind to most of what readers quote.

1. screenplay dialogue
2. `analysis/characters/*.quotes` (already extracted; `studio/quotes.py`
   cleans it; capped at 12 per character — holds none of the thesis lines)
3. quoted speech in `source/chapters/`
4. narration sentences, for a book whose narrator is a character
   (`01-story` must emit `narrator: <character_id | omniscient>`; it is
   recorded nowhere today)

Dedupe (near-duplicate drafts cut 673 → 370), split on sentence boundaries
(the famous clause is often the child of a dull parent), then score.

**Attribution** for pool 3 (MEASURED on 617 quoted paragraphs): a speech tag
naming exactly one alias covers 18%; paragraph-sibling matching against the
screenplay and character quotes (token-set ratio ≥ 0.85) adds to **40%**;
where both fire they agree 20/31. The rest have no speaker and can only be
**cards**. The sibling rule is what gives "scarlet thread" to Holmes — its
paragraph also holds "I shall have him, Doctor", which the screenplay gives
him. A line the two rules split on is refused.

## External iconicity — Wikiquote, revid-keyed

`studio/iconicity.py::fetch_wikiquote(title, author)` → `analysis/iconicity.json`
with `{source, revid, n, kept: [{text, bold, page}]}`. MediaWiki API,
CC BY-SA, no key, User-Agent set. Resolver: the book's own page, else the
author page section, else the character page; film and disambiguation pages
refused. Editors **bold** the famous clause inside a long quotation — a
human-curated "compress to ≤ 12 words" — on 19 of 30 pages.

**Cache keyed on the page revid, never the title.** Network only in the
build step; tests use recorded fixtures (`test_iconicity_cache_invalidates_on_new_revid`).

Coverage (MEASURED 2026-09-03 across all 30 analysed books): **30/30
resolve**, median 18.5 quotes, min 4, total 1,024; 25/30 have ≥ 10. The thin
tail (Call of the Wild 4, Eighty Days 4, Hound 6, Metamorphosis 7, Jekyll 7)
yields ~1 kept line after the ~20% survival into the pools. When `kept < 2`
the manifest says `iconicity: thin`, the finder is the text floor plus the
in-repo signals (character quotes, title echo, the book's own repetition),
and — PROPOSED — spoken lines ≤ 2, the rest cards: without external evidence
a spoken line bets on a model's taste, and a card is the cheaper way to be
wrong.

Goodreads API is dead (2020) and Kindle highlights are ToS-locked. Do not
build on either. Wikipedia plot-summary sentences are the moment-level
equivalent, same API.

## The scorer

```
rank_lines(book):
    pool = dedupe(screenplay + character_quotes + source_quotes + narration)
    icon = load_iconicity(book); idf = idf_over(pool)
    for line in pool:
        s  = stance(line) − penalties(line)         # keep: reply, unbound, pronoun-open, numeral, causal
        s += length_band(line)                       # +1.0 for 3–12 words; −1.0 per 4 words past 14
        s += 1.5 * answerable_question(line, pool)   # a "?" a later line can answer; else 0
        s += generality(line)                        # +0.6 "a", −0.8 per 3rd-person pronoun, +0.5 present, −0.6 past
        s += min(2.0, distinctiveness(line, idf))    # rarer words on commoner syntax, per-book IDF
        s += 3.0 * title_echo(line)                  # PROPOSED: keep only if ≥ 40% of 30 titles echo in text
        s += 6.0 * (line in icon.kept) + 2.0 * (line in icon.bold)
    return sorted(pool, by=−score)
```

**Grading the scorer — never on the corpus it was tuned on.** Held-out: the
Cornell *You had me at hello* pairs (~2,200 same-character, length-matched
pairs; features 64.3%, humans 78%). `test_beats_chance_on_cornell_pairs`
asserts pairwise accuracy ≥ 0.55 with iconicity OFF — length-matched pairs
make the length band inert, so it grades exactly the other terms. Within-
book gate, iconicity OFF: ≥ 50% of Wikiquote-kept lines in the pools rank in
the top quartile (Scarlet today: 2/4). The 38 lines are a smoke test only
(`test_sparta_outscores_ferrier_errand`, `test_no_data_yet_does_not_top_the_book`).

Ten top lines are also judged "understood without the book" by a FakeModel
contract now and a human panel once (`test_top_lines_are_understood_without_the_book`).

## Function, and the slate that must exist

One Strands call (FakeModel in tests) labels each line
`hook | stakes | threat | promise | button | exposition`. The slate must hold
≥ 1 hook and ≥ 1 threat-or-stakes or the build refuses; the button is
optional. This is a gate on model judgment and says so in the manifest.

## Ordering — the conversation across cuts

```
order_lines(top, slots, figure):
    hook   = first(top, kind in {hook, question})
    answer = first(top, kind in {stakes, exposition}, speaker != hook.speaker,
                   shares_content_word(hook))          # the accent must relate (Lieu)
    threat = first(top, kind == threat, speaker == figure) or first(top, threat)
    button = first(top, kind in {button, joke}, words <= 6)
    seq = [hook, answer, threat]                       # → TITLE → button
    refuse if hook is None or (answer is None and threat is None)
```
Scarlet: "You have been in Afghanistan, I perceive" → "It was easier to know
it than to explain why I know it" → "There is death in one and life in the
other" → title → "No data yet." in type.

## The budget is the SLOTS, and the line is chosen for its slot

`lines = min(slate, measured_slots)`. A slot is a trough ≥ 6 dB under the
median held ≥ 1 bar in 20–80% of the *delivered* cue (`03-music` counts them
and scores them in fitness — the metre-best Scarlet seed had one; the plan
wanted four). Cap 4. Vocal path only with ≥ 2 stem gaps.

- With `bars_in_mode ≥ 0.65` a line occupies **whole beats**, starts on beat
  2 or 3 of the slot's first bar (the cut and the first word are not the
  same event), ends one beat before the return, never crosses an L0 point.
  `assign_lines(max_span=2)` survives only in the rubato fallback, and the
  manifest says which applied.
- The pre-title slot must hold threat + 2 beats; `title_term` scores it.
- **Never `atempo` a line into a slot.** 0.85 buys 15%; a 2.5 s line cannot
  enter a 1.43 s slot. Choose the line for the slot: `09-voice` renders the
  slate and reports `seconds_measured` per file; `order_lines` reads that,
  never a predicted duration. The old `speech_seconds` formula is a
  pre-filter only (skip lines predicted > 2× the longest slot).
- Duck at most twice; `trailer_fitness()` selected the cue for its dynamic
  range and six holes destroy it. A **duck** is a line that ends after its
  trough: on the rubato path a line may overrun by `DUCK_OVERRUN` (1.0 s,
  the ducker's release - the bed's mid band is under one release curve
  either way), and `allowance()` grants that to at most `MAX_DUCKS` (2)
  lines per slate. A line inside its trough is not a duck. On the metre
  grid the return downbeat is an L0 point and is never crossed. Scarlet
  run 6: troughs of 2.6 and 2.0 s, the best hook 3.3 s, music_only three
  runs in a row - `rank` admitted the line at 2x the longest slot and
  `fits` refused it at the trough's edge, while `duck_bed` was built to
  carry exactly that overrun.

## Cards

The over-black line is a **card**, not a voice: at the stopdown every masking
mechanism is absent at once and the audience attends to one synthetic voice
for three seconds. Any line with `synthesis_risk ≥ 2` is a card; a card and a
voice never carry the same sentence. Hold `0.55 × words + 0.5 s`, floor
1.4 s; the Netflix 20 cps reading floor is the lower gate (a 12-word card at
7.1 s is 2× the floor, right for a card that must be felt).

## Moments — what `setup_value` cannot see

`setup_value` sees camera emphasis, verbatim density, proper nouns, ALLCAPS,
entrances, bindability. A trailer set piece is three things it does not see:

- **reversal** +3.0 — a scene whose `state_changes` flips the lead's
  knowledge or allegiance (92 state changes exist in Scarlet's scenes)
- **first sight** +2.5 — the figure's first scene, or the first scene a
  named thing appears (RACHE, the ring, the pills)
- **reaction to the unseen** +2.0 — an action line with face/eyes/stares/
  recoils and no object named; the money shot is withheld (Lieu)
- **withheld reveal** — the last lead/figure meeting ≤ 0.6 s, never with a
  line, AND the line that names the figure's identity is refused everywhere
  (detector to define; `test_line_naming_the_figure_is_refused`)
- **kept moment** +6.0 — a Wikipedia plot-summary sentence or an
  illustration-history plate matches the scene

`iconicity.json` never existed for any book; the 6.0 term was always zero and
selection has only ever run on camera emphasis, density, names and caps.

## The honest alternative

Woollen's *Schindler's List* trailer had no voice-over and two dialogue
snippets. A synthetic voice is the one component whose failure the viewer can
*name*, and naming it reclassifies the whole piece. Ship three lines and A/B
against the music-only cut before widening.
