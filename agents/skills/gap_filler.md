# Skill: gap filler — place a scene the pipeline could not resolve (analysis 04)

A scene has no canonical location (and sometimes no time of day). You get that scene,
the scenes immediately before and after WITH their resolved locations and times, and
the list of canonical locations for this book. Decide where and when it happens.

You are inferring, and the result is labelled as inference — so reason from evidence
and say plainly when there is nothing to reason from.

## How to decide the location

1. **Read the scene's own words first.** The raw `location_text` and the summary often
   name the place even when the matcher failed ("the small chamber at the
   police-station" IS the police station; "answers a summons to 221B Baker Street"
   IS Baker Street).
2. **Then use the neighbours.** If the scene before and the scene after are both at
   the same place and nothing in the scene says otherwise, the scene is at that place —
   people do not silently leave and return.
3. **Movement between neighbours**: if the scene sits between two different places and
   describes travelling, choose the place the scene is *arriving at* or *departing
   from*, whichever the text emphasises.
4. **Pick from the canonical list** — return the `id` of an existing location. Only if
   the scene is clearly at a real place that is genuinely absent from the list should
   you say so in `note` and return `location_id: null`.

## When the answer is NO LOCATION

Return `location_id: null` — this is a correct, expected answer — when the passage is:

- **A summary sweep** across many places ("India, Afghanistan, Peshawar, England, and
  London" covering years of backstory) — no single place holds it.
- **A narratorial reflection** ("the life of Lucy Ferrier", musings on time passing)
  that happens nowhere in particular.
- **An address to the reader**, or an editorial aside.

A scene that spans many places or no place is not a scene with a *missing* location —
it is a scene with *no* location. Do not force one.

## Time of day

If the scene has no time, infer DAY or NIGHT from the same evidence the neighbours give
(a scene continuing an evening conversation is NIGHT) plus any implied signals in the
scene itself — meals, lamplight, sleep, traffic. Return `UNKNOWN` if genuinely nothing
supports a choice.

## Answer

- `location_id`: canonical id, or null.
- `time_of_day`: DAY | NIGHT | UNKNOWN.
- `confidence`: `high` (the scene or a neighbour states it) | `low` (a reasonable
  reading, but the text does not settle it).
- `reasoning`: one sentence naming the evidence you used. Quote the phrase that decided
  it where you can.
