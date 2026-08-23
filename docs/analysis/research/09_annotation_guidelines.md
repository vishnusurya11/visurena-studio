# Research 9 — Annotation guidelines distilled (for the 4 specialist skills)

*Subagent report, 2026-08-23. Distilled; the DO/DON'T blocks live nearly verbatim in
`agents/skills/*.md`. Primary docs (TimeML guide, PDNC guidelines, LitBank papers)
extracted to session scratchpad.*

## The shared brick across ALL four schemes

> **Annotate assertions, not inferences** — TimeML anchors only to stated times; THYME
> forbids inferable relations; LitBank events demand asserted realis; LitBank coref
> demands asserted identity; PDNC demands a literal referring expression.
> And every scheme ships an explicit **"unknown" escape hatch** — the agreement data
> shows *forced guessing*, not hard cases, is what destroys consistency.

## 1. TIME (TimeML/TIMEX3 · THYME · NarrativeTime · script-supervisor practice)

- Four TIMEX types: **DATE, TIME (time-of-day), DURATION, SET (recurring)**. Type is
  decided by the expression's FORM, never the event's extent.
- Extent verbatim incl. modifiers, but STOP before event clauses: in "five days after
  he came back" the timex is "five days"; the event is the ANCHOR. Signals (at/after/
  from) split expressions ("two weeks from next Tuesday" = 2 timexes).
- **Keep vague vague**: "some days later"→PXD-style; "recently"→past-reference;
  "evening"→part-of-day token. Hedges go in a separate `mod` (APPROX/MORE_THAN/START…).
- **Every relative expression records its anchor** ("later than WHAT") or anchor=unknown.
- THYME: narrative containers, assert-only relations, derive the rest by closure.
- NarrativeTime: vagueness is legitimate (~92% of "disagreement" wasn't error);
  hypothetical/negated/remembered times go on side tracks, never the main timeline.
- Script supervisor: per-scene continuity ledger — story day/night, elapsed-since-prior
  (or "unstated"), state deltas (injuries, props, wardrobe).
- Top errors: typing by context not form · over-precision on vague expressions ·
  annotating inferred relations.

## 2. CHARACTERS (LitBank entities/coref · ACE · PDNC · social-event work)

- Mention types NAM/NOM/PRO; PER includes groups ("her daughters") and **anything that
  speaks or has inner monologue** regardless of species.
- **Generic never corefers with specific** ("a man of small income", impersonal "you").
- Merge nominal→named only on ASSERTED identity (present-tense copula, apposition,
  direct address, unambiguous context). Masked figures stay provisional entities,
  merged on reveal — never pre-merged on suspicion. Two characters sharing a
  description ("the duchess" ×2) never merge.
- **PRESENT vs MENTIONED** (the interaction/observation test): present = evidence of
  perceiving/being perceivable in the scene's space-time (acts, speaks, is addressed,
  described there). Mentioned-only = exists only inside speech/thought/memory/letters.
  Silence ≠ absence; being talked about ≠ presence.
- Top errors: presence-by-contamination · premature or missed merges · generic/specific
  confusion.

## 3. EVENTS (LitBank events · ACE/Light ERE · THYME)

- **Asserted realis only**: positive polarity, past/present tense, SPECIFIC occurrence,
  asserted modality. "He did not understand" = no event. Futures/plans/wishes/fears =
  no. Habituals/generics ("he generally arrived…") = no. Hypotheticals/dreams/beliefs =
  no (attribute to the believer, off the list).
- Trigger = single word (verb / event noun / acute adjective). Even "said" is an event
  only 89% of occurrences; "thought" 32% — context prunes.
- States count only when the CHANGE happens in-scene (or inherently acute: "stunned").
- High-value state-change checklist: possession transfer, movement, injure/die,
  meet/communicate, knowledge gain (saw/heard/learned/realized).
- Figurative actions ("broke the ice") = no literal event. Pre-scene events recalled
  in-scene = BACKSTORY, not scene events.
- Top errors: realis leakage · habitual promotion · figurative/frame-broken triggers.

## 4. DIALOGUE (PDNC · Muzny sieve · LitBank quotes)

- **Direct discourse only** (spoken or verbatim thought). Indirect/free-indirect = not
  a quote (it IS a speech event — the Events layer catches "replied"; layers join).
- Quote types by the referring expression's grammatical SUBJECT: proper name →
  EXPLICIT; pronoun/common noun → ANAPHORIC; none → IMPLICIT. Nearby names don't count
  — only the speech verb's subject.
- Referring expression = speech verb + subject (+addressee phrase); drop trailing
  adverbials; narration of gesture ("He broke off.") attributes NOTHING.
- Quotes-within-quotes (read-aloud letters, quoted speech): outermost speaker holds
  the mic; don't annotate the inner.
- **Addressee = everyone the speaker BELIEVES can hear** — not everyone in the room
  (eavesdroppers/distracted excluded; self-talk → self or none).
- Honesty valves: `_group` (joint speech), `_unknowable` — never guess a name.
- Top errors: attribution drift in implicit runs · wrong referring expression/type ·
  addressee = everyone present.

## Cross-cutting for the pipeline

Layer hand-offs mirror the corpora: speech verbs are events while quote content is
dialogue; timexes anchor to events; mentioned-only characters surface via dialogue
mentions while present ones surface via events/addressees. The join keys exist by
design — our assemble step merges on the 1st AD's scene numbers.
