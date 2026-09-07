---
name: trailer-dialogue
description: Find the lines a culture kept, grade the finder on a held-out corpus, order them hook → answer → threat → title → button, and choose each line for the measured LEVEL of the window it will occupy.
---

# Dialogue — iconic lines and iconic moments

`scripts/trailer/step_04_lines.py`, `studio/trailer_dialogue.py`, `studio/quotes.py`,
`studio/iconicity.py`, `studio/line_windows.py`. Speaking the lines is `09-voice`.

## The brick — a trailer line needs no scene and takes a side

Length, syntax, position, what to speak and what to set in type all derive from
that sentence. It is not a property of the text alone: it is **what a culture
kept**, so this stage is an *oracle interface*, not a generator, and every
candidate arrives as `(text, speaker, kept: bool, function)`. External evidence
does not OUTRANK the text features, though — run 10 proved that weighting it
that way makes it the only feature. It reserves a seat (`quota_fill`); the text
features rank whoever else gets one, and they exist for the book nobody kept.

## Why the previous scorer was inverted (MEASURED)

Against 38 real trailer lines, `line_value` scored 26 negative (median −1.5).
"This is Sparta!" −7.6; every question −6.6; a Ferrier-subplot errand scored
3.1, above all 38. Two terms did it:

- `< 5 words → −3.0` deleted half the corpus. The median iconic line is
  **4.5 words**; 28 of 38 are ≤ 7. Short is the *format*.
- `? → −4.0` deleted the hook. 18% of iconic lines are questions, all as hook
  or threat, and Lieu's whole technique is a question a later line answers.

What it got right survives as `context_debt` (weights in the block below); the
Cornell memorability study confirms the pronoun and generality findings.

## The finder reads FOUR pools, not the screenplay

Wikiquote lists 19 quotations for *A Study in Scarlet*. **Four** survived into
`screenplay.json`, ranked 39 / 51 / 104 / 158 of 271; the title sentence ("the
scarlet thread of murder…") is in `source/chapters/ch_04` and nowhere in the
screenplay. A finder that reads only the screenplay is blind to most of what
readers quote.

1. screenplay dialogue
2. `analysis/characters/*.quotes` (already extracted; `studio/quotes.py`
   cleans it; capped at 12 per character — holds none of the thesis lines)
3. quoted speech in `source/chapters/`
4. narration sentences, for a book whose narrator is a character
   (`StorySpec.narrator`, a character id or `omniscient`; `voiced` lets him
   SPEAK at most `VO_LINES` = 3 of them, and he never plays hook or button)

Dedupe (near-duplicate drafts cut 673 → 370), split on sentence boundaries
(the famous clause is often the child of a dull parent), then score.

**Attribution** for pool 3 (MEASURED on 617 quoted paragraphs): a speech tag
naming exactly one alias covers 18%; paragraph-sibling matching against the
screenplay and character quotes (token-set ratio ≥ 0.85) adds to **40%**;
where both fire they agree 20/31. The rest have no speaker and can only be
**cards**. The sibling rule is what gives "scarlet thread" to Holmes: its
paragraph also holds "I shall have him, Doctor", which the screenplay gives
him. A line the two rules split on is refused.

## External iconicity — Wikiquote, revid-keyed

`studio/iconicity.py::fetch_wikiquote(title, author)` → `analysis/iconicity.json`
with `{source, revid, n, kept: [{text, bold, page}]}`. MediaWiki API,
CC BY-SA, no key, User-Agent set. Resolver: the book's own page, else the
author page section, else the character page; film and disambiguation pages
refused. Editors **bold** the famous clause inside a long quotation — a
human-curated "compress to ≤ 12 words" — on 19 of 30 pages.

**Cache keyed on the page revid, never the title.** Network only in the build
step; tests use fixtures (`test_iconicity_cache_invalidates_on_new_revid`).

Coverage (MEASURED 2026-09-03 across all 30 analysed books): **30/30 resolve**,
median 18.5 quotes, min 4, total 1,024; 25/30 have ≥ 10. The thin tail (Call of
the Wild 4, Eighty Days 4, Hound 6, Metamorphosis 7, Jekyll 7) yields ~1 kept
line after the ~20% survival into the pools. When `kept < 2` the manifest says
`iconicity: thin` and the finder is the text floor plus the in-repo signals
(character quotes, title echo, the book's own repetition). A thin book still
SPEAKS: `MIN_SPOKEN` is 3, so the old proposal to cap a thin book at 2 spoken
lines was a guaranteed `speech_refusal` — deleted. Goodreads' API is dead
(2020) and Kindle highlights are ToS-locked; do not build on either.

## The scorer

```
rank_lines(book):
    pool = dedupe(screenplay + character_quotes + source_quotes + narration)
    icon = load_iconicity(book)
    for line in pool:
        s  = stance(line) − context_debt(line)       # reply 3.0, unbound 2.0, pronoun-open 1.8, numeral 2.5, causal 1.0
        s += length_band(line)                       # +1.0 for 3–12 words; −1.0 per 4 words past 14
        s += generality(line)                        # +0.6 "a", −0.8 per 3rd-person pronoun, +0.5 present, −0.6 past
        s += rarity(line)                            # mean word length − 4, clipped [−1, 2]
        s += 1.4 * theme_word(line) + 0.8 * (speaker in leads)
        s −= 2.0 * (speech_seconds(line) > 8.0)      # past this it is a paragraph, not a line
        s += where * (2.0 * kept + 1.0 * bold)       # where: book 1.0, author 0.5, character 0.25
    return sorted(pool, by=−score)
```

`answerable_question`, per-book IDF `distinctiveness` and `title_echo` are
PROPOSED, unbuilt: `stance` only declines to punish a "?", `rarity` stands in
for the IDF term without a pool.

**What the culture kept is a RESERVATION, not a ranking.** At the 6.0/2.0 this
block used to prescribe, over a line value spanning about −10..+4, Wikiquote IS
the sort: 17 of run 10's 24 candidates were aphorisms off the Holmes CHARACTER
page and the book's own threat — "Now, Enoch Drebber, who am I?" — ranked #663
and was never offered. Evidence weighted above the score it is added to stops
being evidence and becomes the sort. So the mechanism left the score:
`quota_fill` decides what the labeller SEES — thesis card, the figure's
confrontation whole and in spoken order (the TAIL; its opening is still setup),
four seats for what the culture kept (bolded first), two per role by
`ROLE_MARKS`, then the best by score. A labeller cannot label a threat it was
never shown, and that is the only reason "Choose and eat." (score **0.60**
against the errand's 3.83) reaches the sheet: ranking a sequence's sentences
against each other destroys the sequence.

**Grading the scorer — never on the corpus it was tuned on.** Held-out: the
Cornell *You had me at hello* pairs (~2,200 same-character, length-matched
pairs; features 64.3%, humans 78%). `test_line_value_beats_chance_on_cornell_pairs`
asserts pairwise accuracy ≥ 0.55 with iconicity OFF — length-matched pairs
make the length band inert, so it grades exactly the other terms. Within-
book gate, iconicity OFF: ≥ 50% of Wikiquote-kept lines in the pools rank in
the top quartile (Scarlet today: 2/4). The 38 lines are a smoke test only
(`test_sparta_outscores_ferrier_errand`, `test_no_data_yet_does_not_top_the_book`).

## Function, and the slate that must exist

One Strands call (FakeModel in tests) labels each line
`hook | stakes | threat | promise | button | exposition`. The slate must hold
≥ 1 hook and ≥ 1 threat-or-stakes or the build refuses; the button is optional.
This is a gate on model judgment and says so in the manifest.

**A speaker who cannot be voiced is not a speaker.** `09-voice` renders only a
speaker with a cast card (`design_refs` opens `analysis/characters/<speaker>.json`
and nothing else) and `step_06_plan` lays the line only where that speaker has a
face in the window's movement (`speak_on_face`). Both card the line AFTER this
stage counted it as speech, so both are selection filters HERE: a speaker that
is not a cast-card **id** enters as a card and never counts toward
`wanted_speech`.
Scarlet run 19: the slate's only `stakes` line is the Police Inspector's, and
`Police Inspector` is no id among the 23 cast cards (`g_lestrade`,
`tobias_gregson`, `unnamed_constable`). It was carded in four consecutive runs
(`gate=speaker_card`, terminal) then refused downstream (`lines_refused: no
shot of Police Inspector in M3`) — while the pool held **four** spare `stakes`
lines, every one a cast-card id, that `next_candidate` exists to reach and
`voice_line` never asks for: it returns the card before the ladder is entered.

**And that seat was not lost on score — it was lost to the ANSWER filter
(MEASURED).** `role_candidates("answer")` drops every line whose speaker equals
the hook's, then sorts on `l.speaker is None` (`trailer_dialogue.py:430-433`);
both predicates test a STRING. Run 19's hook is Holmes, so the filter dropped
three cast-card Holmes lines scoring **3.95, 3.87, 3.10** (`lines.json` `pool`)
and the best non-`None` speaker left was `Police Inspector` at **3.50** — sorted
into the SPOKEN bucket ahead of two real cards at 4.30 and 4.05. The rule that
exists to produce a second VOICE reached a name that is no voice. RULE:
**castability — `analysis/characters/<speaker>.json` exists — is the predicate,
not `speaker is None`**, in `playable`, `no_second_card` and every role sort.
Carded before ordering that line is not merely outranked: 9 words against
`CARD_WORDS` = 8, so `playable` refuses it and the seat goes to Watson's
**2.37**. Four spoken lines becomes five and `lines_refused: no shot of Police
Inspector in M3` never fires. The missing test hands `role_candidates` a pool
whose top non-card speaker has no cast card.

A line carded downstream must also be carded IN `lines.json`. `SlateLine.card`
is a computed property (`speaker is None`), not a field, so no downstream
carding can be written back: step 06 (`if not line.card`) still lays a window
for a line whose `rel_path` is null and `speak_on_face` reorders the picture
around a voice nobody will hear. The mix skips it (`trailer_assemble` requires
`rel_path`), so the cost is picture order spent on silence, not a duck.

## The ladder cannot answer arithmetic — relabel converts 0 of 10 (MEASURED)

Scarlet's `learnings.jsonl` holds **30** `step 04 / gate slate` rows over
**11** climbs: 22 refusals, **8** terminal `music_only`. `relabel_next_10` has
converted **0 of 10** — 8 climbs got the byte-identical refusal back, 2 got a
different contract refusal from the same gate. The only two climbs that shipped
lines AFTER a rung shipped on `drop_story_rules`: "the slate speaks 3 line(s)
and this trailer needs 6" was satisfied by deleting the rule and shipping 3.
Both are the owner's "no dialogues" — one as silence, one as a floor met by not
asking. That rung and `quota_fill` landed 2026-09-05 21:57; of the five climbs
since, two ended `music_only`, two shipped on `drop_story_rules`, and run 19's
logged **no row at all** — it passed at attempt 1. Nothing on this ladder
produced the 0.115 master below, which is the measurement that matters: the
ladder is not where the lines are lost.

The 22 refusals divide by what a LABEL can change:

- **10× "a hook with no threat or stakes after it"** — the one refusal in this
  step that names no action, and it cannot even say whether the role went
  unlabelled or merely unplaced. `refusal()` names both seconds and an action
  ("label shorter lines as hook"); this raised string names neither.
- **8× "no hook fits the first slot"** — arithmetic: `line_seconds` against
  `holds(slot, beat)`. A relabel changes neither number, and the sheet grows by
  ten candidates of LOWER score, never of shorter ones.
- **4× `speech_refusal`** — arithmetic, and invisibly so: `budget` caps the
  slate at one line per window (below), yet `wanted_speech` is compared only to
  the slate, never to the supply. Scarlet's cue makes **5** windows; a wanted of
  6 is unsatisfiable by any labelling of any sheet.

**A rung must change an input the refusal is a function of, or it is not a rung,
it is a delay before the same terminal.** Reconcile the floor with the supply
BEFORE the labeller is asked: a wanted count above the seats the cue affords is
a MUSIC fault (`03` owes more phrase starts) or a PICTURE fault (a shorter cut),
and the step says which instead of asking twice and then dropping its own rule. Grade
every rung by its conversion in `learnings.jsonl`; a rung measured at 0 is
deleted, not re-tuned — and `test_the_last_rung_ships_lines_rather_than_silence`
asserts the actions are exactly `[relabel_next_10, relabel_next_10]`, so the
tests encode the 0/10 as correct.

## Ordering — the conversation across cuts

```
order_lines(top, slots, figure):
    top    = [l for l in top if not names_figure(l, figure)]  # the trailer sells WHO;
                                                   # the answer is never a line (test_line_naming_the_figure_is_refused)
    hook   = first(top, kind in {hook, question})
    answer = best(top, kind in {stakes, exposition}, speaker != hook.speaker)
             sorted by (is_card, NOT shares_content_word(hook))  # a SORT, not a filter
    threat = first(top, kind == threat, speaker == figure) or first(top, threat)
    button = first(top, kind in {button, joke}, words <= 6)
    seq = [hook, answer, threat]                       # → TITLE → button
    refuse if hook is None or (answer is None and threat is None)
```

**A sort key with no match is lexical score.** Lieu's accent is a sort, never a
filter: when nothing shares a content word with the hook every candidate lands
in one bucket and the winner is whatever scored highest. Scarlet run 19
(`lines.json`, MEASURED): the hook is "Rache, revenge." — two content words —
and **0 of 7** answer-eligible candidates share one (checked with the repo's own
`shares_content_word`). So window 2 of 5 went to "I always smoke 'ship's'
myself," at **3.83** and Hope's "There is death in one and life in the other."
(**1.90**, stakes) lost. The second thing the trailer says is an errand, and no
score can catch it: `line_value` grades a line ALONE, and the answer's whole job
is to be second.

RULE (PROPOSED, untested): **a hook with no answer is the wrong hook.** When no
candidate shares a content word with the chosen hook, take the next hook that
has one before taking the best-scoring stranger, and refuse in words when no
hook has one at all. The shorter the hook the fewer answers exist for it, so an
aphorism-length hook is the most dangerous in the pool — iconicity and
answerability pull opposite ways. Both accent tests hand the orderer a pool
where a sharer exists (`test_the_answer_comes_from_another_speaker_and_relates`,
`test_an_auxiliary_is_not_a_content_word`); the missing test is the empty one.

## The budget is the DELIVERED PICTURE, and the line is chosen for its slot

A **window** is a RUN of consecutive spans the music leaves room in
(`CuePlan.line_windows`): troughs, sustains and phrases inside one section,
broken by an accent, a section start or the tail, ending a beat before the run
does. Waiting for troughs alone is what shipped `music_only` eight times —
Scarlet's cue holds **2** found troughs in 116.7 s — and a run admits the
sustains and phrases beside them, which is why all five of run 19's windows read
`made: true`. `made` on this path does not mean made from the grid; it means the
run is not all trough. `made_slots` and its `WINDOW_BAND = (0.0, 0.8)` are the
no-plan fallback (`windows_for` takes the plan whenever step 03 wrote one), so
run 10's 0.2-floor hook at 38.9 s and "a rubato cue keeps only its troughs" are
the fallback's history, not the shipping path's: `beat_for` hands the orderer
`plan.bar / 4` whatever the metre calls the cue, and a run needs no phrase start.

**A window is a duration; the budget counts windows. That is the supply gap.**
`place` searches only windows with `start >= after` and `fill_roles` sets
`after` to the previous **window's** end, never the previous **line's** — so a
window is reserved whole whatever fraction of it is used, and `budget =
min(len(slots), len(pool), MAX_LINES)` counts windows, not seats. Run 19's
second window is 20.95–40.129 (**19.18 s**) and carries a **2.31 s** line; the
other 16.87 s cannot be spoken in and is music-only by construction
(`longest_music_only_s` **21.0** against a target of 15). Under the step's own
fit rule the five windows hold `holds(slot, 0.73)` = 11.68 + 17.52 + 11.68 +
11.68 + 6.57 = **59.13 s** of speech, and **11.39 s** was spoken: 19% of the
room the music already left, on a cue nobody needs to re-render. RULE
(PROPOSED, untested): a window SEATS `n` lines where `n × line + (n − 1) × gap
≤ holds(slot, beat)`, `after` advances to the last line's END, and `budget`
counts seats. The gap is a mixing number, not a musical one — `DUCK_OVERRUN` is
1.0 s, longer than this cue's 0.73 s beat — and even at 2.85 s a line plus a
1.0 s gap those same five windows seat **14**, above `MAX_LINES` = 13; thirteen
lines over run 19's 99 s picture is **0.374** occupancy against the 0.30 target.
`test_chosen_windows_never_overlap` asserts `b.window.start >= a.window.end` and
`TestHowMuchIsSaid`'s docstring says the orderer "cannot lengthen a window" —
both encode one-line-per-window as correct and change with the rule.

**A window is also a LEVEL, and no stage reads it (MEASURED).** `Slot` is
`start, end, made` — no level — so nothing downstream of the plan can choose by
loudness, and `place` takes the window nearest the aim (`by_nearness`, keyed on
`abs(s.start − target)` alone). The plan already knows: `cue_spans.density_in`
writes `level_db` on every span and every section, and the ask makes those a
STAIRCASE (`TEXTURE`: M1 low, M2 mid, M3 high). Run 19's five measured sections
read −29.3, −27.8, −19.6, −17.6, −17.1 dB, and because `fill_roles` only ever
advances `after`, each line sits over a louder bed than the last:
`lines.level.json` measured bed peaks **−22.5, −17.5, −11.8, −7.6** LUFS and
`qc.json` delivered `line_over_bed_lu` **16.11, 14.71, 8.52, 7.32** — monotone
down, 4 of 4. The trailer's last word is by construction its least audible line,
and that is the owner's "all I hear is music" said as a number. It ends in a
CLIFF, not a slope: `duck_depth` is `min(18, max(10, bed + 24))`, so the duck
reaches `BED_UNDER_LINE` only while the bed peaks at or under **−6.0 LUFS**;
run 19's button sat at −7.6, **1.6 dB** inside it, and past that line every extra
dB of bed comes straight off the voice.

**And the line's own level is a target nobody read back (MEASURED).**
`level_lines` (`trailer_assemble.py:632-641`) computes `line_gain(integrated(raw))`,
applies `volume=` through an `alimiter` at `LINE_TP − LIMITER_MARGIN` = **−3.5 dB**
sample peak, writes the file and never measures it. Run 19's four levelled lines
deliver **−17.83, −16.77, −17.03, −16.29** LUFS against `LINE_TARGET_LUFS` =
**−16.0** — every one short — and true-peak at −3.14, −3.39, −3.15, −3.21 dBTP,
all four pinned on that ceiling. A target and a ceiling are ONE constraint: a
line holds both only while its peak-to-loudness is under **12.5 dB**. The raw
takes all measure −20.1 LUFS at −1.39, −3.93, −2.08, −5.33 dBTP — crests of
18.7, 16.1, 18.1, 14.8 dB, every one over budget — so every line MUST be
limited, and the loudness the limiter takes back ranks with the raw peak
**4 of 4** (1.83, 0.77, 1.03, 0.29 LU). The most dramatic read is the quietest
line in the film. Nothing reads it back: `write_level_sheet` writes `duck_db`,
`bed_peak_lufs`, `bed_floor_lufs` and no line level, and `QCReport` carries
`line_tp`, `line_flat_factor`, `line_crest_db`, `bed_under_line_lu` and no field
for a line's loudness — though `line_over_bed` (`qc.py:145-148`) already computes
`integrated(line-N.level.wav)` and throws it away in the subtraction. RULE: **a
level applied is not a level delivered; a stage may claim a level only where it
measures the artifact it wrote.** It costs one field, and it splits a figure
this page today reads as one: of the **0.68** LU by which run 19's button misses
the 8.0 `LINE_OVER_BED` asserts, **0.29** is the line's, not the bed's. Raising
`LINE_TARGET_LUFS` raises the gain, the limiter takes it straight back and the
delivered level does not move — the lever is the READ's crest, which makes the
take a LEVEL decision made in `09-voice`, not a mixing one.

**And a run is not uniform: the line always plays at its opening.** Step 06 lays
every line at `line.window.start + metre.beat` (`step_06_plan.py:246`) — run 19's
four `at`s are 2.92, 21.68, 47.419, 91.168, each exactly one 0.73 s beat after
its window opened. Window 2 runs 20.95–40.129 and ENDS in a trough measured
**−89.7 dB** from 35.02; the 2.31 s line was laid at 21.68, over the −27.8 dB
span the run opens on, and mixed at −17.5. The cue's two real holes
(`metre.slots` 35.05–40.85 and 64.25–70.00, **11.5 s** of measured silence)
carried **none** of the four spoken lines.

RULE (PROPOSED, untested): a window carries its measured `level_db`, and the
offset inside it is a measurement, not a constant. Among the windows that hold
the line the orderer takes the QUIETEST — the aim only breaks ties — and it
writes the line's `at` on the quietest span of the run instead of step 06
deriving it. Run 19's threat had three windows left and took 46.689 (span
−19.8 dB) because its aim was 46.31 s, while 64.178 opens on a **5.84 s trough
measured −87.0 dB** and holds 11.68 s against that line's 5.74 s: 17.9 s of aim
bought at ~30 dB of bed. `level_db` (median event level) is not `bed_peak_lufs`
(momentary LUFS on the rendered bed) — over run 19's four lines the offset is
+7.0, +10.3, +8.0, +7.9 dB and the rank order agrees 4/4 — so an admission
threshold is stated in the mix's unit and calibrated, never in `level_db`
directly. When no window left can hold the last line quietly, the fault is the
CUE's and the step says so: `AskedEvent` has a `hole` kind that `EVENT_ORDER`
never asks for, so no cue this pipeline has ordered has a hole in M3 for the
button to land in.

**A count floor and an occupancy floor are the same rule in two units
(MEASURED).** `wanted_speech` is `max(3, ceil(SPOKEN_PER_100S × runtime / 100))`
with `SPOKEN_PER_100S` = **5** lines per 100 s; `qc.speech_target` is a DURATION
SHARE, 0.30 above 60 s. Neither is derived from the other. At the repo's own
line length (`speech_target`'s docstring: "three lines of the 1.5-4 s the norm
gives them is about 6.6 s" → 2.2 s a line) 0.30 of 100 s needs **13.6** lines
per 100 s — **10.5** at run 19's measured 2.85 s mean — and
`SPEECH_CEILING_PER_100S`'s own docstring puts the norm at **8–12 per 100 s**
and calls `SPOKEN_PER_100S` its floor. The code's floor is 5. Two bounds fall
out of that arithmetic: run 19's **11.39 s** of speech meets the occupancy floor
only under a **~44 s** picture (0.259 against 0.257 at 44 s, 0.253 against 0.260
at 45 s), and the contract ceiling `MAX_LINES` = 13 caps the reachable picture
at **~95 s** at 2.2 s a line or **~124 s** at the measured 2.85 s — the pinned
108 s cue sits between them, so line LENGTH decides whether the ceiling can meet
the floor at all. `wanted_speech` must read the occupancy back —
`ceil(speech_target(runtime) × runtime / mean measured line seconds)` — and when
that exceeds the seats the cue affords, the step names the lever (more line room
from `03`, or a shorter picture) instead of asking the labeller twice and then
dropping its own rule. **A floor stated in a unit the delivered master is not
measured in can be satisfied exactly and still ship silence.**

**The floor BELONGS on the delivered master, not on the slate — and is not
there yet.** `story_refusal` runs once, inside step 04's ladder, and four later refusals spend its count
without re-asking: an uncastable speaker, a speaker with no face
(`speak_on_face`), a window past the picture's end (`inside` / `reachable`), a
re-fit that placed nothing. Re-ask at every artifact that can lose a line —
`voice.json` (rendered), `plan.json` `lines` (laid), `lines.level.json` (mixed),
and the last is the number that matters. QC states it as `speech_occupancy`
(0.22 up to 30 s, rising to 0.30 by 60 s) with `music_only_fraction` ≤ 0.45, and
that pair is the owner's "no dialogues" said as a number — **said, and never
gated on.** `QCReport.floor_pass` is loudness, true peak, unbound / reused /
stale shots, `lines_are_clean`, `hard_out` and `cue_cut.floor_misses()`; speech
appears in `_layer_flags` only, and step 09's `verdict` returns `floor_pass`
alone. Run 19's two `09 / floor / recut` rows were bought by
`line_flat_factor[1]` = **0.869** and `cuts_inside_sustain` = 3; the 0.115
speech bought nothing and the run ended `ship_flagged`. **A number nothing gates
on is a note, not a floor, and a stage may only claim a floor where a rung is a
function of it.** The step-09 ladder's own threshold string confirms it from the
other side — "−15.5..−12.5 LUFS, TP ≤ −1.0, 0 unbound, no clipped line, the bed
stops before the card" names no voice at all.

**And the one line-placement number that IS a floor is a tautology (MEASURED).**
`CueCut.lines_in_troughs` sits in `floor_misses()` at 1.0 — the only placement
number anywhere that gates. It asks whether each line the mix laid falls inside
`plan.line_windows()`; step 06 lays lines only in `cue.line_windows()`
(`step_06_plan.py:611`), `fits` keeps each inside its window, and step 08 writes
that same settled plan back to `music/plan.json`, so on the shipping path both
sides come out of one function. Run 19 read **1.0** with all four lines outside
both of the cue's actual troughs; only a hand-built pool makes it read less
(`test_cue_qc.py:75`). The name is the only part of it that measures a trough.
The numbers that are not tautologies are the mix's own, and they disagree:
`QC_TARGETS["line_over_bed_lu"]` flags below **5.0** while the mix is built to
**8.0** (`LINE_OVER_BED = LINE_TARGET_LUFS − BED_UNDER_LINE`, asserted in
`test_a_quiet_take_still_clears_the_bed_it_ducked`). Run 19's last line delivered
**7.32** — it passes the number QC grades and fails the number the mix's own test
asserts. **When both sides of a floor come from one function it measures nothing,
and when one rule carries two numbers the loose one is the one that ships.**

Run 19's delivered master, 2026-09-06, is the whole chain inside ONE run:
`wanted_speech(99.2)` = **5**, the slate holds **5** (`lines.json`), **4** render
(`voice.json`; the fifth is the uncastable Police Inspector, `rel_path` null),
`lines.level.json` mixes 1.59 + 2.31 + 5.74 + 1.75 = **11.39 s** into a 99 s
picture, and `qc.json` reads `speech_occupancy` **0.115** against **0.30**,
`music_only_fraction` **0.765**, `longest_music_only_s` **21.0**, all three in
`flags` — and it shipped. The step met its own floor exactly, on a slate that
needed no rung, and delivered 38% of the master's.

- With `bars_in_mode ≥ 0.65` a line occupies **whole beats**, starts on beat
  2 of the window's first bar — always, which is the constant the offset rule
  above replaces — ends one beat before the return, never crosses an L0 point.
  `assign_lines(max_span=2)` survives only in the rubato fallback, and the
  manifest says which applied.
- The pre-title slot must hold threat + 2 beats; `title_term` scores it.
- **Never `atempo` a line into a slot.** 0.85 buys 15%; a 2.5 s line cannot
  enter a 1.43 s slot. Choose the line for the slot. `speech_seconds` is a
  pre-filter only (skip lines predicted > 2× the longest slot) — yet step 04
  still ORDERS on it, calling `order_lines` with no `measured`. The order that
  ships is step 06's re-fit against `voice.json`'s `seconds`. Not because the
  prediction drifts — on run 19's four rendered lines it errs +0.04, +0.10,
  −0.43, +0.42 s, inside the 0.73 s beat `fits` rounds to — but the re-fit is the
  only pass that knows which windows the PICTURE reaches.
- The duck budget is INERT on the shipping path (MEASURED). `overruns` spends
  nothing on a `made` window and all five of run 19's are `made`, so `allowance`
  always returns `DUCK_OVERRUN` — and `fits` ignores the overrun whenever there
  is a beat. `MAX_DUCKS` has not been reachable since step 03 began shipping a
  plan. The dynamic range `trailer_fitness()` selected the cue for is defended
  by `duck_depth`'s 18 dB ceiling and by nothing in this step.

## Cards

The over-black line is a **card**, not a voice: at the stopdown every masking
mechanism is absent at once and the audience attends to one synthetic voice for
three seconds. A card and a voice never carry the same sentence. Hold
`0.55 × words + 0.5 s`, floor 1.4 s; the Netflix 20 cps reading floor is the
lower gate. "Any line with `synthesis_risk ≥ 2` is a card" is PROPOSED, not
built: `synthesis_risk` is computed in `dialogue_candidates` and `SlateLine`
has no field to carry it, so today a card is exactly a line with no speaker.

## Moments — not this step's

`setup_value` lives in `studio/trailer_story.py` and sees camera emphasis,
verbatim density, proper nouns, ALLCAPS, entrances, bindability.
`iconicity.json` resolves for all 30 books but carries `kept` QUOTATIONS only —
no plot-summary sentence — so its +6.0 kept-moment term has been zero in every
run. Wikipedia plot summaries are the moment-level equivalent on the same API;
until one is fetched this subskill holds no lever here.
