---
name: trailer-story
description: Derive a trailer's dramatic structure from a screenplay - lead, opposition, turn, and what must stay unanswered.
---

# Story structure

`studio/trailer_story.py`. All pure functions of `screenplay.json`. No model,
no spend, testable against fixtures.

## The unit is the ELEMENT, not the scene

This is the single most important rule here, and getting it wrong produced
every repetition complaint we have had.

A scene is ninety seconds of story. A trailer shot is two. Selecting scenes
gave **11 candidates for 33 shots**, so every setup appeared three times.
Each scene holds 12-15 discrete action lines — **241 usable candidates for
A Study in Scarlet, 630 for Jekyll and Hyde.** Select from those.

`action_elements()` returns `(scene, index, text, location, cast)` per line.
Rank with `element_value()`, which rewards concreteness: a line naming
something a camera can point at ("A wedding ring strikes the floor") beats one
describing a state of mind ("Holmes considers the problem").

## The four derived entities

| | rule | verified |
|---|---|---|
| **LEAD** | present in the most scenes | Holmes; Utterson |
| **FIGURE** | owns the most scenes where the lead is ABSENT | Hope; Hyde |
| **TURN** | first scene of the longest lead-absent run | Scarlet Part II; *Henry Jekyll's Full Statement* |
| **RESOLUTION** | final 15% + the LAST lead/figure meeting | sc 20-22; sc 32, 44-50 |

FIGURE is not "the second most present character" — that returns the
companion. The antagonist is the one the protagonist keeps missing.

TURN is not a plot reveal. For an adaptation it is **the moment the narration
changes hands**, and the rule lands exactly on both books' structural breaks
without knowing anything about them.

## Spoilers are structural, not lexical

Matching logline words against scene text **does not work** and we tried it: a
logline is abstract ("whose solution exposes a decades-old revenge") and action
lines are concrete ("Hope releases the bridle"), so the words never meet. It
banned 0 scenes in one book and 39 of 50 in the other — the latter because
"jekyll" is in the logline and appears everywhere.

What identifies the payoff is structure: the story's last stretch, plus the
last time lead and figure stand together.

**You may show the image. You may not caption it.** Restricted material is
allowed as a shot of ≤0.6s carrying no dialogue. That is what lets the trailer
use the book's best images without answering its own question.

## Gates

- the lead must appear in ≥25% of beats — a *Study in Scarlet* plan once
  contained no Sherlock Holmes and every mechanical gate passed it
- every register (quiet/build/hit) must be present, or nothing peaks
- arc position comes from the BEAT index, never the scene index: 11 beats over
  22 scenes caps position at 0.48 and no beat ever reaches the hit band
