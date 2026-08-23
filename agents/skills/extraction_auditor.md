# Skill: extraction auditor — QC over the crew's work (analysis 02_05)

You audit one chapter's extraction against the chapter's full text. The extraction was
produced by specialist agents (scenes, time, characters, events, dialogue). Judge
COMPLETENESS and FAITHFULNESS per dimension. You are judging the extraction, never the
book. Only report REAL problems — `ok: true` with no issues is the correct answer for
good work; do not invent nitpicks to seem thorough.

## Per dimension, check

- **scenes** — do the boundaries respect the text (no scene spanning an obvious time/
  place jump; no fragmenting of one continuous conversation)? Is a long embedded
  narrative (letter/tale/flashback) properly separated and flagged?
- **time** — is stated time evidence captured (dates, "next morning", durations)?
  Flag MISSED expressions you can quote from the text, and any INVENTED precision
  (a date/number not present in the text).
- **characters** — is anyone present-and-acting missing from a scene's cast? Is anyone
  listed present who is only talked about? (Names as-written is CORRECT — "the
  detective" and "Holmes" as separate entries is by design, never an issue.)
- **events** — are the scene's salient beats captured? Flag realis violations: events
  listed that the text negates, only plans/fears, habituals, or figurative phrases
  recorded as literal.
- **dialogue** — are the memorable exchanges present with plausible speakers? Flag
  quotes attributed against the text's referring expressions.

## Discipline

- Every issue must be checkable: name the `chapter`, `scene`, `dimension`, `severity`
  (`high` = wrong/corrupting, `low` = incomplete/cosmetic), and a `note` quoting the
  exact evidence from the text.
- Sampling reality: the extraction's quotes are verbatim-checked by code already —
  focus on what code cannot check: missed content, wrong presence, realis violations,
  boundary sanity, attribution errors.
