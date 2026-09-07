---
name: trailer-story
description: Derive a trailer's dramatic structure from a screenplay - lead, opposition, turn, and what must stay unanswered.
---

# Story structure

`studio/trailer_story.py` is pure functions of `screenplay.json`, testable against
fixtures; `step_01_story.py` adds ONE model call for the four judged fields.

## The unit is the ELEMENT, not the scene

A scene is ninety seconds of story, a trailer shot two. Selecting scenes gave **11
candidates for 33 shots**, so every setup appeared three times; the scarcity then moved
down into the movement bounds (see the SPINE). Each scene holds 12-15 action lines: **241
candidates for A Study in Scarlet, 630 for Jekyll and Hyde.** `action_elements()` returns
`(scene, index, text, location, cast)`; rank with `element_value()`, which rewards
concreteness — "A wedding ring strikes the floor" beats a state of mind.

## The four derived entities

| | rule | verified |
|---|---|---|
| **LEAD** | present in the most scenes | Holmes; Utterson |
| **FIGURE** | owns the most scenes where the lead is ABSENT | Hope; Hyde |
| **TURN** | first scene of the longest lead-absent run | Scarlet Part II; *Henry Jekyll's Full Statement* |
| **RESOLUTION** | final 15% + the LAST lead/figure meeting | sc 20-22; sc 32, 44-50 |

**Three of the four are maxima over the lead's ABSENCE, and the corpus has almost none.**
`figure_of` (:98), `turn_of` (:101) and through it `movement_bounds`' m2 edge all iterate
`lead not in people_in(sc)`. MEASURED over the 27 screenplays that set holds a MEDIAN
**5 scenes, 5.4 % of the book**, **13 of 27 hold ≤ 3** and 5 hold ZERO — so `figure is
None`, `turn is None` and `turn_scene` falling back to 1 are not three faults but ONE, on
the identical five books (*Alice*, *Oz*, *Crusoe*, *Turn of the Screw*, *Metamorphosis*).
Both books in the `verified` column are the outliers that make the table look right:
Scarlet is **41 % lead-absent, 26th of 27**; Jekyll **32 %, 23rd**. RULE: an entity
derived from a COMPLEMENT is worth only what the complement is big — verify it on the
corpus's MEDIAN book, never on its widest.

TURN is not a plot reveal but **the moment the narration changes hands**, and the RUN is
what degenerates: the longest stretch the lead misses is 1 scene in 5 books, 0 in 5 more.
Fall back to the longest lead-absent run *by location*, inside `turn_of` — never in
story.json — but repair `figure` FIRST: `StorySpec.figure` raises before `turn_scene` is
serialised, so `derive`'s `else 1` (:49) is dead code and a unit test for that fallback
goes green while step 01 still cannot finish. The recorded `turn_scene` moves nothing: its
one consumer is `climax_scenes` (step_04_lines.py:154), a union with `identity_scenes`,
and over the 22 books that can build a spec it adds a scene in **2** (*Jekyll* 39, *Black
Beauty* 88), the figure speaks in neither, so `confrontation` reserves **zero** lines from
it. Step 06 recomputes the turn from `movement_bounds` (:83, :353) and never reads the
field. RULE: a field is alive only where a consumer's OUTPUT moves when it moves.

FIGURE returns **None** wherever the lead is in every scene — the same **5 of 27** — while
`StorySpec.figure` is `Field(min_length=1)` (trailer_stage_spec.py:51), and both roads out
of this step build that spec: the gate (`to_spec`, :90) and the terminal `fallback`
(:126). All three rungs burn quoting `Input should be a valid string` at a field the model
cannot write, then `fallback` raises it uncaught — **step 01 cannot finish on 19 % of the
corpus**, and no test covers `figure=None`. RULE: never quote a DERIVED field to the model
as its violation; a fallback that builds the same contract as the gate is not a fallback.

**And where it does return a name, 10 of the 22 are a spelling tie.** `figure_of` is
`max(shadow, key=(count, name))`, so the alphabetically LAST id takes it: *Wuthering
Heights* **lockwood over heathcliff** (17-17), *Tom Sawyer* **welshman over injun_joe**
(6-6-6), the *Hound*'s withheld figure is **sherlock_holmes** (3-3); where the run is one
scene the tie is that scene's whole cast — *Treasure Island* takes **tom_morgan** over
five including long_john_silver, *A Christmas Carol* **young_cratchits** over four
including jacob_marley. Only **5 of 22** win outright by more than one scene (*Moby-Dick*
19, *War of the Worlds* 9, *Frankenstein* 8, *Prince and the Pauper* 4, *Scarlet* 3).
Unlike `turn_scene` this one MOVES, measured by recomputing both branches:
`restricted_scenes` — Carol **[13,28-31]** vs **[23,28-31]**, Dorian Gray adds sc 28, the
field proved below to cut the picture; `identity_scenes`, which is `select_by_movement`'s
`reveal` (:1138) — Treasure Island **14 scenes of 107 vs 63**, Carol **2 vs 10**; and
`confrontation`'s `speaker == figure` reservation (step_04_lines.py:169) — tom_morgan has
**30** screenplay lines against Silver's **794**, young_cratchits **3** against Marley's
**13**. RULE: gate the MARGIN of every derived field a consumer reads, not only the
lead's.

## What reaches the screen is the SPINE

`introduction_end` and `turn_of` give `movement_bounds`; `QUOTA_SHARES`
(trailer_story.py:869) spends 25/45/30 % of the setups on M1/M2/M3 in that order
(`select_by_movement`). But that quota is a SHARE spent on three different units — shots
(`select_by_movement`), bars (`CueAsk.for_bars`), sections BY COUNT
(`cue_spans.movements_of`) — and `step_06_plan.restamped` (:476) then overwrites every
beat's movement, and its arc, with its CUE SPAN's, so the last unit wins. MEASURED on run
19's plan.json: 22 spans over six sections, so M1 is section 0 alone —
**0.73 s of a 99.2 s cut, 0.7 % against the 25 % asked** (M2 61 %, M3 38 %), shipped arc
quiet 1 / build 15 / hit 5 / aftermath 1, nothing quiet for the hit to be loud against.
RULE: a share survives only where the units it is spent on are equal, so verify the quota
in SECONDS on the artifact that ships, never in counts.

**And a quota is two numbers: the SHARE and the SUPPLY it is drawn from.**
`movement_bounds` = (`introduction_end`, `turn_of`) (trailer_story.py:912). Over the 27
screenplays M1 holds a MEDIAN **2.7 % of the scenes**, 25 of 27 under 10 % (Scarlet
9.1 %; only *Metamorphosis* 30 % and *Alice* 14.7 % reach the 25 % asked), and on
Moby-Dick M1 and M2 are ONE SCENE EACH — 70 % of the setups from 2 of 323 scenes.
Recomputing `movement_of(scene, bounds=(2, 11))` over run 19's beats gives M1 5 / M2 14 /
M3 3, and those five M1 beats are scenes [1, 1, 2, 2, 1] — the only two `m1_end=2`
allows. All 22 stand on **11 distinct scenes, 9 of them (41 %) in 221B Baker Street
against `PLACE_SHARE = 0.30`**. A thin movement does not under-fill: `_fill` spends its
whole quota inside the one scene it has. RULE: write `(m1_end, m2_end)` and each
movement's scene count into story.json beside the quota; a movement holding fewer scenes
than its share of the setups means the BOUNDS are wrong and not the story — widen them
before spending, never after.

## Four judged fields, and who opens story.json

A field is wired only where a later step OPENS `trailer/story.json`, reads it by name,
AND its own artifact changes when the field changes. The same nine-row table in another
module is not a link, and neither is a read that only widens a pool.

| field | value | who opens story.json and reads it |
|---|---|---|
| `narrator` | `<character_id>` or `omniscient` | `05-dialogue` only — `line_pools(narrator=)`, `voiced()` (step_04_lines.py:126, :400) — and it moves nothing, below. **`09-voice` never opens story.json**: step_05_voice reads `lines.json` and nothing else |
| `register` | one of `elegy / gothic / romance / coming-of-age / tragedy / procedural / detective / comedy / adventure` | `02-refs` only — `palette_for(story.register, story.setting)`, nine registers, **eight** grade lines — `PALETTES["detective"]` == `PALETTES["procedural"]` (trailer_refs.py:342-343; `len(set(PALETTES.values())) == 8`), so run 19's judged `detective` shipped the exact line the terminal fallback's `procedural` writes ("gaslight amber" 20× in plan.json): on a detective book the model call buys zero pixels. Measure a judged field at its consumer's OUTPUT, never at its enum. Give `detective` its own grade or drop it from the enum. **`03-music` never opens story.json** (grep "story" in step_03_music.py: 0 hits) and the register never reaches the CUE: `cue_ask.form_for` takes a `Tone`, keyword-matches the hand-written `trailer/music/tone.json` and defaults to `detective` |
| `thesis` | one sentence, present tense, ≤ 7 syllables, names nothing, not an event ("nobody is who they say") | `05-dialogue` — `thesis_card` (step_04_lines.py:232), the only producer of the title card |
| `setting` | period and place, ≤ 80 chars, e.g. `1881 London` | `02-refs` appends it to every ref prompt (trailer_refs.py:358); `05-dialogue` opens the dialogue ask with it (step_04_lines.py:281) |

**The terminal rung discards the judged `setting` to repair `thesis`.** `fallback`
(step_01_story.py:126) builds the spec with no `setting` — it defaults to `""` — and the
gate keeps `exc.errors()[0]["msg"]` while dropping `["loc"]` (:142), so nothing knows
WHICH field failed. Cost, MEASURED on run 19: all 20 ref prompts carry `; 1881 London`
from `palette_for` (trailer_refs.py:358), and detective and procedural share a grade, so
that clause is the ONLY thing this rung changes on 20 plates. Never fired; two of the six
rows below are attempt 2 of 3. RULE: fall back per FIELD — quote the `loc`, keep what the
refused answer got right, replace only the field the gate named.

**`narrator` is read twice and changes nothing.** Both consumers only ADD to a pool:
`line_pools` appends `narration_pool` for a character narrator (trailer_story.py:857) and
`voiced` stamps his name on at most `VO_LINES = 3` of them (step_04_lines.py:214) — *after*
`rank` has scored them (:400). Nothing scores them up: `line_value` pays +0.8 only for a lead
speaker, −0.4 for a missing emotion and subtracts `context_debt` for pronouns
(trailer_dialogue.py:161-169), while `narration_pool` emits speaker/emotion/scene all `None`
(trailer_story.py:823); `quota_fill` reserves thesis / confrontation / kept / role, no
narration (step_04_lines.py:204). MEASURED on run 19, narrator `john_watson`: the labeller's
whole sheet is `TOP_N = 30`, work/labels-0.json holds exactly 30, pools screenplay 19 / source
9 / quotes 2 — **narration 0**, and all five shipped lines come from pools `omniscient` builds
too. RULE: a judged field that only WIDENS a candidate pool cannot move a cut
decided by a ranker scoring what that pool lacks — wire it to a RESERVATION or a threshold.

**`null` passes on the first try, and the ask asks for it.** `Judgement.thesis` defaults to
`None`, `_thesis_is_a_refrain` returns early on None, and `ladder.settle` writes a Learning
only when a gate FAILS: run 19 shipped `"thesis": null` with no step-01 row at all and
`thesis_card` returned `[]` — no card. All six step-01 rows ever written measure a syllable
overrun, none an absence; the `clauses`/`thesis_from` cut-back (R11) runs only on the terminal
rung. And the prompt discourages the answer it is missing: `prompt_for` ends the thesis
sentence with `A sung refrain only fits {sorted(VOCAL_REGISTERS)}` (step_01_story.py:85) —
elegy, gothic, romance, coming-of-age, tragedy — so on `detective`, `comedy`, `adventure` and
on the fallback's own hardcoded `procedural` (:126) the model is told its refrain does not fit.
The consumer that clause protects is unbuilt: `vocal_eligible()` (trailer_stage_spec.py:79) has
zero call sites outside tests, nothing writes `story.thesis` into `Tone.refrain` (run 19's
music/tone.json: `lyrics_mode: instrumental`, `refrain: null`), BUILD row 13 is `[ ]` — while
the thesis's real consumer, `thesis_card`, never reads the register. RULES: a gate that only
refuses BAD answers cannot make a field required — refuse silence on the retry rungs like an
over-long refrain; and every clause of an ask must name the consumer it protects, since a
clause whose consumer is unbuilt suppresses the field for free. Ask for the refrain
unconditionally; restore the register test the day BUILD 13 is ticked.

## Spoilers are structural, not lexical

Matching logline words against scene text **does not work** and we tried it: the logline
is abstract and action lines concrete, so the words never meet — it banned 0 scenes in one
book, 39 of 50 in the other; structure identifies the payoff (the RESOLUTION row above).
`restricted_scenes` is DERIVED, not judged, and `resolution_scenes` is the DEAD half of
the copy: `derive` returns one list under both names (step_01_story.py:50), nothing in
`scripts/` or `studio/` reads `story.resolution_scenes`, and step_06's own
`resolution_scenes(...)` default (:82) never runs — the production call passes
`banned=story.restricted_scenes` (:599). It provably cuts the PICTURE:
`select_by_movement` on run 19's screenplay with `banned=[20,21,22]` ends
[...,16,18,18,18,19,19,19]; with `banned=[]` scene 20 — the arrest — takes the last slot
and scene 17 enters.

**"You may show it; you may not caption it" (trailer_story.py:198) is a permission no code
grants.** The ban is a POOL FILTER, and a pool filter can only say NEVER:
`setups_for(banned=story.restricted_scenes)` (step_06_plan.py:599) reaches `_ranked_pool`,
which drops those scenes before any ranking (trailer_story.py:987) and `candidates` drops
their SCREENPLAY lines (step_04_lines.py:127) — only those, below; no short-glimpse slot
exists (grep `0.6` in trailer_story.py and step_06_plan.py: 0 hits). Run 19's plan.json:
22 beats, 11 scenes, highest 18, **none of 20-22**. RULE: a permission is a lie until a
consumer implements the exception — either give the glimpse a slot (a beat drawn from
`banned` after the quota fills, `line: null`), or say the true thing: the resolution is
CUT, not glimpsed.

**The ban is written in scene numbers, and one pool of four sets one.** `screenplay_pool`
stamps the scene (trailer_story.py:697); `quote_pool` (:714), `source_pool` (:810) and
`narration_pool` (:823) emit `scene: None`, and `line["scene"] not in restricted`
(step_04_lines.py:127) cannot refuse what carries no key. MEASURED on run 19's book,
`line_pools(narrator="john_watson")` = 2417 candidates — source 1003, narration 989,
screenplay 359, quotes 66 — so **359 (14.8 %) carry a scene**, the ban removes **43**, and
the last 2 of 15 chapters still hand over **101** attributed lines it cannot see, Hope's
confession among them (`pool: source, scene: None`). None has shipped yet — `dedupe_lines`
gives a repeated sentence to the screenplay copy, which HAS the key, so the hole is
paraphrase, not duplication — and all 989 narration lines a character narrator adds arrive
un-bannable. RULE: a decision written in scene numbers reaches exactly the material
carrying one — every setup carries a scene, so the picture is 100 % governed and the line
pool one seventh. Carry `chapter` out of `source_pool` and ban its tail fraction, or the
SCENE ban stops at pictures and screenplay lines. **The withholding does not, because its
second ban is keyed on the NAME**: the same line 127 also drops
`names_figure(line["text"], story.figure)` — any capitalised ≥3-letter token of the
figure's id (trailer_dialogue.py:357) — and `order_lines` re-applies it (:582, BUILD 12).
Text is a key EVERY candidate carries: on run 19 it removes **39** lines, **36** outside
`restricted_scenes`, **33** of those from the source and narration pools the scene ban
cannot see — sc 10's "let me introduce you to Mr. Jefferson Hope, the murderer of Enoch
Drebber", in both its screenplay and its source copy. Checked and null: **0** false
positives in the 2417 candidates; both sentence-initial matches are the real name. RULE: a
ban reaches exactly the candidates carrying its KEY — key it on WHAT is withheld, not on
WHERE it happens.

## Gates

- `LEAD_SHARE_FLOOR` does not measure its own story. The failure was a PLAN with no
  Sherlock Holmes; `lead_share` measures the SCREENPLAY's scenes (:53, :156), which exist
  before any plan does — and it never fires: over 27 screenplays the lead's share runs
  **0.56–1.00, 0 of 27 under 0.25**, so :158 has never written a row. Move it to `06-plan`
- what IS undecided here is the MARGIN. `lead_of` is `max(counts, key=(count, name))`
  (trailer_story.py:81): *Scarlet*'s Watson and Holmes hold **13 scenes each** and the
  lead is Holmes because `s` sorts after `j`; Moby-Dick's is Stubb by 2 of 323 over Ahab;
  *Metamorphosis*'s is Mrs Samsa by 1 over Gregor. MEASURED by flipping *Scarlet*'s tie on
  the real screenplay: lead `john_watson` gives turn **12** not 11, bounds **(2,12)** not
  (2,11) and restricted **[11,20,21,22]** not [20,21,22] — scene 11 goes, and with it run
  19's shipped stakes line — while `select_by_movement(count=22)` returns **4 different
  beats of 22**. And the one call that could break the tie is TOLD: `prompt_for` writes
  `Lead: {derived['lead']}` as a given (step_01_story.py:80). RULE: gate the quantity that
  is CLOSE — write `lead_margin` into story.json (it costs no model call) and put both
  names in the ask as a QUESTION; a fact stated to the model is a question never asked
- so is the FIGURE's margin, and worse: **0 in 10 of the 22** books that have one, ≤ 1 in
  **17**. Write `figure_margin` beside `lead_margin` and put both names in the ask as a
  question — `prompt_for` states `figure: {derived['figure']}` as a given (:81) too
- quiet/build/hit all present AND M1's share of the cut's SECONDS against its 0.25 quota
