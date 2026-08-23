# Skill: journey tracer — a span that moves is a route, not a point (analysis 04)

You get a span of prose that appears to cross several places, the scenes around it, and
the canonical location list for this book. Decide whether it is **one place** or **a
route**, and if it is a route, list its legs in order.

## The question

Most scenes happen somewhere. Some passages instead *carry a character across places* —
a backstory summary, a voyage, a pursuit, a chapter that compresses months of travel
into a paragraph. For those, no single location is true. Naming one is not a small
approximation; it deletes the passage's entire subject.

So: **does this span move, or does it merely mention?**

## It is a ROUTE when

- The prose takes characters bodily from place to place — they arrive, they are moved,
  they land, they are sent, they gravitate.
- Different things happen at different places in the span, and the order matters.
- Time passes between the places (days, months, years).

## It is ONE PLACE when

- The other places are **mentioned, remembered, feared, or discussed** — talking about
  Utah in a Baker Street sitting-room is a Baker Street scene. **Mention is not
  presence.**
- The named places are containers of one another ("the sitting-room, 221B Baker
  Street") — that is one place written at two levels of zoom, not two places.
- A character merely passes through en route with nothing happening there. Do not
  invent a leg for scenery glimpsed from a train.

Return `is_journey: false` for these, and the span keeps the placement it already has.

## Writing the legs

One leg per place where something actually happens. In the order the text travels them
— which is the order of the events, not the order the sentences happen to mention them.

- `order`: 1-based, no gaps.
- `location_id`: from the canonical list. If a place the span visits is genuinely
  missing from the list, **skip that leg** — do not invent an id and do not substitute a
  different place.
- `when`: the text's OWN words about the timing ("in the year 1878", "a month later",
  "for months"). Do not compute a date; a later step does that.
- `event`: one line, what happens on this leg. The reason this leg exists.
- `time_of_day`: DAY or NIGHT — the ordinary reading if the text is silent.

Fewer, truer legs beat many thin ones. A leg where nothing happens is noise.

## The primary location

`primary_location_id` is the single place to use where only one is possible — a label on
a map, a one-line index. Choose **where the span's decisive event happens**: the place
the passage exists in order to reach. For a soldier's war service ending in a wound,
that is the battlefield where he was hit, not the country he convalesced in and not the
city he drifted to afterwards.

Give it even when `is_journey` is false — then it is simply the place.
