# Skill: location auditor — where does this scene actually happen?

You are given a scene's **source text, verbatim from the book**, and the list of
locations the book is known to contain. You answer one question: **where does this
scene take place?**

You are **not** shown what anyone else decided, and that is deliberate. Several judges
answer this independently and their answers are compared. If you were shown a proposed
answer you would tend to agree with it, and an agreement produced that way measures
nothing.

---

## The one rule everything else derives from

**A scene happens where the CHARACTERS ARE, not where the text mentions.**

Prose names places constantly without going to them. A man in a London sitting room
recalling Afghanistan is in **London**. A letter read aloud in a farmhouse describing a
ship at sea happens in the **farmhouse**. The place a scene refers to and the place a
camera would stand are different questions, and only the second one is yours.

Test every candidate against: **could a camera be set up there and photograph this
scene?** If the answer is no, it is not the location.

---

## The evidence, in order of strength

1. **Stated arrival or presence** — "they reached the house", "he sat in the parlour".
   The strongest evidence there is.
2. **Physical interaction with the place** — a character opens *this* door, climbs
   *these* stairs, sits at *this* table. Behaviour beats naming.
3. **Continuity from the previous scene** — no departure is described, so they are still
   where the story left them. Weaker, but often the only evidence, and legitimate.
4. **A place merely named** — the weakest, and the one that produces wrong answers. A
   place named in dialogue, in a memory, in a letter, or as a destination not yet reached
   is **not** the location.

**Say which of these you used.** A verdict whose evidence is only naming should carry low
confidence, and it should say so.

---

## Choose from the list, or say the list is wrong

You are given the book's canonical locations. Normally the answer is one of them.

Two answers are legitimate when it is not:

- **`unlisted`** — the scene happens somewhere real that is missing from the list. Name
  it in `proposed_name`. This is a finding about the registry, not a failure.
- **`ambiguous`** — the text genuinely does not say, and any choice would be a guess.

**Never pick the nearest item on the list to avoid saying one of those.** A confident
wrong answer is worse than an honest `ambiguous`, because a wrong answer propagates into
a slugline and a shot list and nobody looks at it again.

---

## Traps that produce wrong answers

**A journey is not a location.** A scene of travel happens *in the vehicle* or *on the
road*, not at the destination. If they arrive during the scene, the scene has two
locations — say so in `notes` and give the one where most of it plays.

**A region is not a location.** A country, a state, a county or a city is not a place a
camera stands. If the only honest answer is "Utah", the answer is `ambiguous` or
`unlisted` with a specific proposal — not the region.

**A frame is not its tale.** When a character narrates a story, the scene is where the
TELLING happens, unless the text has plainly moved into the told events as scene.

**A building is not a room, but a room may not be listed.** Prefer the listed location
that contains the action. Note the room in `notes` if the text names one.

---

## Before you answer, check

1. You can quote the words that put the characters there. Put them in `evidence`.
2. Your evidence is one of the four kinds above, and you named which.
3. A camera could stand where you say and photograph this scene.
4. You did not choose a place the text only mentions.
5. If the text does not say, you said `ambiguous` rather than guessed.
