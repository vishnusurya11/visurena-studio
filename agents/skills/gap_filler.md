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
