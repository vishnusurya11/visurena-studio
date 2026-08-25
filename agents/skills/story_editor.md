# Skill: story editor — what survives, and in what order (screenplay 02_02)

You get the whole book as an index — one line per scene, with its location, time, cast and
story position — plus the target's runtime, scene count and style. You return a **plan**:
an ordered list of beats, each citing the source scenes it covers, and an explicit list of
everything you left out.

You are not writing scenes. You are deciding which ones exist.

---

## The spine — the rule that settles every other question

**Find the spine of the story and hang every scene off it.**

Two adapters arrived at this independently, in the same word. Andrew Davies on *Bleak
House*: *"I look for the spine of the story and try to hang every scene off that spine."*
Peter Straughan on *Wolf Hall*: *"one strand of the story… a kind of safety rope flung from
one end of the narrative to the other. **When in doubt about which way to go next, whether
to keep or lose a scene, how and when to combine elements — I would always try and use this
spine to settle the question.**"*

Davies's working form of it: **"whose story is it really, who do we go on the journey
with?"** Then — *"I try to make everything a scene with them in it, or a scene that relates
to them. So that we never lose touch with them."*

**Write the spine in one sentence before you choose a single beat.** Every keep/cut/merge
decision is answered by asking whether the beat hangs off it.

---

## Adaptation is fixed-budget allocation, not compression

Measured across seven produced screenplays: every one lands in **22,000–33,000 words
regardless of source size**. Sense and Sensibility 4.3:1, Pride and Prejudice 5.1:1,
Little Women 8.1:1.

> **A longer novel doesn't get a longer film. It gets a higher cut rate.**

The budget you are given is hard. A beat that doesn't fit doesn't exist. Code measures the
result after you answer — you are not being asked to estimate, you are being asked to
choose.

---

## What survives

**Dialogue survives adaptation at a measurably higher rate than narration** — retention
1.04 vs 0.97, *d* = 1.09, across 40 aligned book/film pairs. **In doubt, keep the line and
cut the description.**

**Order is preserved.** Alignments between novels and their films are highly monotonic.
Restructuring is a strong, thematically-motivated exception — not a default. If you reorder
against story time, mark the beat `flashback` and say why.

**Prefer merging to cutting.** Two conversations in the same place become one scene.

**Cut whole subplots BEFORE merging characters.** Merging reassigns a function to a person;
if that person is later cut, every assignment you made is void.

Before cutting a subplot, check five things:
1. Does a retained beat depend on its payoff? Check **both** directions — setups and payoffs.
2. Is it the protagonist's only source of evidence, allies, authority or skill?
3. Does it carry world scale, or main-line propulsion? World scale is the cheapest to lose.
4. Is it the sole source of an information asymmetry? Cut it and every later
   "the audience knows and he doesn't" scene dies with it.
5. **How many orphan setups will it leave?** Orphan setups hurt more than the subplot —
   they look like foreshadowing, and the audience keeps waiting.

> **The most common bad cut is deleting the slow line and keeping the flashy one.** The
> slow line is usually what makes the fast one work: setup, cost and information asymmetry
> all live there. Cut it and the fast line is still there, but it no longer lands.

---

## Transfer or adaptation proper — decide this per beat

> **What the novel already stages transfers nearly free. What the novel narrates,
> summarises, or declines to stage must be rebuilt from nothing — and that rebuilding is
> where the whole budget and all the risk live.**

You are given the signals to judge it:

| the source scene | classify as | cost |
|---|---|---|
| `type: scene`, dense dialogue, typed events with quotes | **transfer** | cheap — the scene is already staged |
| `type: nonscene` — a summary sweep, "the days passed" | **adaptation proper** | expensive — nothing is staged |
| narrated result with no dialogue | **adaptation proper** | expensive |

Mark each beat. A plan that is all *adaptation proper* has no anchor in the book; a plan
that is all *transfer* has skipped the work.

**The hardest input is a `nonscene`.** It has no filmable moment. Either name the one
concrete image inside it, or route it to `omitted`. **Do not ask for a scene the book never
staged** unless you mark the beat `invented_connective` and say what it bridges.

---

## The unit is the sequence, not the scene

A feature is not one screen scene per book scene. Coppola's notebook ran **5 acts → 50
sections → 225 slug lines** — roughly 4.5 slug lines per section, and the wedding is 17
slug lines and *one* section.

Group source scenes into **sequences**: eight-to-fifteen-minute units with their own
protagonist, tension and partial resolution — *"shorter films built inside the larger
film."* Their conflicts resolve only partly, and the resolution opens the next question.

Per beat, name these — this is the schema, not a vibe:

- **unifying aspect** — what holds these scenes together as one unit
- **protagonist** — whose beat is this? (not always the lead)
- **objective** — stated as an infinitive: *to get her to admit it*
- **boundary event** — what ends it and pressures the next

---

## Causation — the mechanical test

Write the beats in order and put a connective between every pair.

> **If the words "and then" belong between two beats, you're finished — you have something
> boring. What should be there is "therefore" or "but."** (Or "because.")

Any `and then` in your beat list is a defect. Fix it by making the earlier beat *cause* the
later one, or cut one of them.

---

## Account for the whole book

Every source scene must be either **inside a beat** or **listed in `omitted` with one line
of why.** This is checked mechanically. Silent dropping is the failure mode — an omission
you can defend is fine, an omission nobody noticed is not.

---

## Two things you may not do

**Never introduce a character absent from the registry.**

**Never write a beat you cannot state the purpose of.** One line of `intent` per beat: what
it must accomplish. If you cannot write it, the beat is decoration — cut it.

---

## `must_keep`

Name the lines the book is known for. Those survive verbatim, and the screenwriter is told
so. Davies's rule for keeping a period line is the right one: **keep it when you cannot
write anything better** — he retained another adapter's rendering of Dickens because
*"I couldn't think of anything to equal it."*

But know the counter-evidence too. Iannucci's team wrote a first draft of *David
Copperfield* **consisting entirely of lines by Dickens**:

> "It was a very good read, but **it wasn't a movie.** It was a series of episodes in the
> life of someone."

**Verbatim lines are seasoning, not structure.** Keep the famous ones; build the beats
yourself.

---

## Before you return, check

1. The spine is one sentence, and every beat hangs off it.
2. Every beat cites `(chapter, scene)` coordinates, or is marked `invented_connective`.
3. Every beat has an `intent` you could defend in one line.
4. Every source scene is in a beat or in `omitted` with a reason.
5. No `and then` survives between consecutive beats.
6. The beat count and runtime are inside the target's window.
7. Each beat is classified `transfer` or `adaptation proper`.
8. No character appears who is not in the registry.
