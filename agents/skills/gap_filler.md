# Skill: gap filler — every scene gets a place and a time (analysis 04)

A scene reached you without a canonical location or without a time of day. You get the
scene, a window of the scenes before and after it WITH their resolved locations and
times, and the canonical location list for this book.

**You must always answer.** Every scene happens somewhere and at some hour, even when
the prose does not say so — the pipeline needs a place and a time for every scene, and
"unknown" is not available to you. Choose the best-supported answer and say what it
rests on.

## Choosing the location

Work down this list; the first that applies wins:

1. **The scene names it.** The raw `location_text` or the summary often contains the
   place even when the matcher failed — "the small chamber at the police-station" IS
   the police station; "answers a summons to 221B Baker Street" IS Baker Street.
2. **The neighbours agree.** If the scenes on both sides are at the same place and
   nothing says the characters left, the scene is at that place. People do not silently
   leave and return.
3. **A journey.** If the scene sits between two different places and describes
   travelling, pick the endpoint the scene emphasises — where they are arriving, or
   where they have just left.
4. **The characters anchor it.** A scene about a character's life, growth, or state of
   mind belongs where that character lives or spends the passage — Lucy Ferrier's girlhood
   belongs at the Ferrier farm.
5. **A summary sweep across many places** ("India, Afghanistan, Peshawar, England, and
   London" covering years of backstory): choose **the single most consequential place in
   that span** — where the passage's decisive event happens. For a soldier's war service
   ending in a wound, that is the battlefield, not the places he passed through.
6. **A reflection or an address to the reader**: place it where the narrator physically
   is while telling it — normally the same place as the surrounding scenes.

Return an `id` from the canonical list. If the right place is genuinely missing from
that list, pick the closest one available and say so in `reasoning` — do not invent an id.

## Choosing the time of day

Return DAY or NIGHT — never UNKNOWN. Use, in order: any time signal in the scene
itself (meals, lamplight, sunlight, sleep, deserted or busy streets); the time of the
neighbouring scenes (a scene continuing an evening conversation is NIGHT); and the
ordinary rhythm of the events described (investigations and travel by day, break-ins and
long confessions by night).

## Answer

- `location_id`: a canonical id. Always.
- `time_of_day`: DAY or NIGHT. Always.
- `confidence`: `high` (the scene or a neighbour states it) | `medium` (a solid reading
  from context) | `low` (a judgement call between plausible options).
- `reasoning`: one sentence naming the evidence, quoting the deciding phrase where you
  can. If your confidence is low, say what the alternative was.

---

## Granularity — the error that produced most of the wrong answers

Three books were audited by independent judges, 25 scenes each. Of every location they
overturned, **almost all were the right area at the wrong SIZE**, in both directions:

| the pipeline said | the judges said | which way it was wrong |
|---|---|---|
| `ingolstadt` (a town) | the vaults and charnel-houses | too big |
| `orkney_island` | Victor's laboratory | too big |
| `geneva` | a barn | too big |
| `darling_house_nursery` | `darling_house` | too small — the scene leaves the nursery |
| `utah_mountains` | Eagle Cañon | too big |
| `evian` | `geneva` | the wrong town entirely |

**The rule: name the smallest place that contains the WHOLE scene.**

Two tests, and a place must pass both:

1. **Does everything in this scene happen there?** If characters move from the nursery
   to the stairs to the street, the nursery is too small — the house, or the street, is
   the answer.
2. **Could a camera be set up there?** If the answer names a town, an island, a county
   or a country, it is too big — you cannot set up in Ingolstadt. Name the building, the
   room, the road, the clearing.

A settlement is a legitimate location **only for a scene that genuinely plays across it**
— a chase through streets, an arrival seen from outside. Not for a scene that happens in
one room inside it.

---

## A scene happens where the CHARACTERS ARE, not where the text points

The single clearest wrong answer in the audit: Frankenstein's opening was placed in
**England**. It is a letter written **from St Petersburg** *to* England. The pipeline
followed where the text pointed instead of where the writer sat.

- A **letter** happens where it is WRITTEN, not where it is sent or read.
- A **memory** or a told story happens where the TELLING happens.
- A **destination** not yet reached is not the location. They are still on the road.
- A place named in dialogue is not the location. A man in a London room recalling
  Afghanistan is in **London**.

## A journey is a place

*"In a cab returning to Holmes's"* came back as a registry gap, because a vehicle in
motion had no entry. It is a real location and a camera can be inside it.

When a scene plays in transit, the location is **the vehicle or the road**, not the
destination. If the scene both travels and arrives, give the place where most of it
plays and say so.
