# Skill: plan reader — list what a plan does; never judge it (episode 02_05)

You get a chapter's text, the chapter's rows numbered (one per scene, as the
analysis lists them), and a plan: its question, its setups with their cast,
every shot's picture (setup, size, faces, extras, frame, motion, camera) and
every line, numbered, with its speaker and the shot it plays on.

You answer one question, and only this one:

> **What does this plan DO with this chapter — where is its turn, where is
> its answer, which rows does it show or tell, and what does it claim?**

You LIST. Code judges. You are never asked whether the plan is good, and you
never say so. Every field below is a closed shape; fill it from what is on
the page, quoting the chapter verbatim where a span is asked for.

---

## `turn`

The one shot where one named person acts ON another — a hand laid on a
person, a person caught, held, pulled, led, struck, pushed, helped, handed
something. Find it yourself from the shots' motion clauses; the plan does
not mark it for you.

- `shot`: its index; `-1` when no shot shows one person acting on another.
- `actor`, `acted_on`: entity ids exactly as the setup's cast lists them.
  Two DIFFERENT people. Never a crowd, never "extras", never a thing.
- `verb`: the acting verb as one word in the plan's own tense (`takes`,
  `catches`, `pulls`, `leads`, `holds`, `hands`, `strikes`, `helps`).
- `span`: the chapter's own words for that act, copied verbatim; empty when
  the chapter has none.

## `answer`

Where the plan's `question` is answered.

- `kind`: `line` when a spoken sentence answers it; `shot` when a picture
  does; `none` when nothing in the plan answers it.
- `index`: the line's number or the shot's index; `-1` with `none`.
- `span`: the chapter sentence that answers it, verbatim; empty when the
  answer is the plan's own.

## `coverage`

One entry PER NUMBERED ROW of the chapter, every row, in order.

- `event`: the row's number as listed.
- `shots`: the shot indices whose picture SHOWS that row's action.
- `lines`: the line numbers whose words TELL that row (narration counts).
- Both empty means the plan neither shows nor tells it. Say so by leaving
  them empty; do not invent a shot.

## `claims`

Every assertion the plan makes about the chapter that the chapter either
gives or does not:

- `kind: count` — an `extras` number, a number of anything in a frame.
- `kind: posture` — lying, kneeling, sitting, astride, crouched, sprawled.
- `kind: prop` — a named object a person holds or uses.
- `kind: place` — a landmark or a place the frame names.
- `shot`: where the plan says it. `claim`: the words as the plan has them.
- `span`: the chapter's words that give it, copied verbatim. **Empty when
  you cannot find them.** An empty span is the finding; never fill one from
  memory or from what would be plausible.

---

## Rules

- Quote spans verbatim from the chapter text you were given; a paraphrase is
  not a span.
- Name people only by the entity ids in the setups' cast lists.
- List what is there. If a field has no answer, use its empty value (`-1`,
  `none`, `""`, `[]`) — never a guess.
- Read every shot and every line before you answer; a turn on shot 20 is
  missed by a reader who stopped at 12.
- No prose, no verdict, no advice. The shape is the whole answer.
