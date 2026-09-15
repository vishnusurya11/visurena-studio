# THE STANDING GOAL — A Study in Scarlet, chapters 4 to 14

Set by the owner, 2026-09-13. This file is the WATCHDOG, and this is its
TRACKED copy -- `library/` is gitignored, so the copy beside the book survives a
session and this one survives the disk. They say the same thing; the ledger
(`SERIES_PROGRESS.json`) lives only beside the book, because it is book data.

**Read this file first whenever you do not know what to work on.**

## The loop, per episode

For each chapter N from 4 to 14, in order:

1. **GENERATE** episode N end to end.
2. **DQ-ITERATE 2-3 times** — measure, fix what the numbers show, re-cut. Each
   iteration keeps its own `master_iterK.mp4`; never overwrite the only copy.
3. **PUBLISH** to YouTube.
4. **INTROSPECT** — what went wrong that the gates did not catch.
5. **IMPROVE THE SKILLS AND AGENTS** for whatever could NOT be fixed in-episode,
   using 5 subagents.
6. Move to N+1 and repeat, until chapter 14 is published.

## The rules that bind the loop

- **Do not stop in the middle.** Finish the step, then the episode, then the
  next episode. See `feedback-do-not-stop-until-done` in memory.
- **Publishing is the one place to stop and ask.** QC now stamps the sha8 it
  measured and the publish ladder refuses a report about different bytes, so an
  episode may publish unattended ONLY when qc passes on the exact file. If it
  does not pass, stop, say why, and wait for the owner. Episode 3 went out
  against a stale report; that must not happen again.
- **SPEND. DO NOT STOP TO ASK.** This goal IS the authorisation. Sheets are
  ~$0.13-0.20 each, panels $0.08, title cards $0.05, a whole episode about
  $1.00-1.30. Spend it, log it to `spend.jsonl`, report the number in the
  wrap-up. Owner, 2026-09-14, after I halted the entire chain to ask for FIVE
  CENTS: *"i explitlity gave you the fucking goal .. man fucking follow .. spend
  money"*. Ask first ONLY for something outside this goal's scope, an order of
  magnitude past the per-episode norm, or a paid service never used before
  (`feedback-spend-approval`).
- **One GPU, one stage at a time.** Two concurrent H3 runs clobbered a work dir.
- **Every iteration ends with the deliverable's full path, first line.**

## Progress

The ledger is `SERIES_PROGRESS.json` beside this file. It is the source of
truth for where the loop is, and it is updated after every step, not at the end.

| chapter | title | state |
|---|---|---|
| 1 | A Mr. Sherlock Holmes | published `-K2ucdt_mCg` |
| 2 | The Science of Deduction | published `P8i7niWhEWo` |
| 3 | The Lauriston Garden Mystery | published `Pkr4HudmQPo` |
| 4 | What John Rance Had to Tell | published `WN2ktyq8tr0` |
| 5 | Our Advertisement Brings a Visitor | published `g-U-P0ZOoq8` |
| 6 | Tobias Gregson Shows What He Can Do | published `AIX83NAcTGc` |
| 7 | Light in the Darkness | IN PROGRESS -- takes re-rendered, DQ pending |
| 8 | On the Great Alkali Plain | |
| 9 | The Flower of Utah | |
| 10 | John Ferrier Talks with the Prophet | |
| 11 | A Flight for Life | |
| 12 | The Avenging Angels | |
| 13 | A Continuation of the Reminiscences of John Watson, M.D. | |
| 14 | The Conclusion | |

Chapters 8-12 are the Utah flashback: a different cast, a different place, and
no Holmes or Watson. Expect the cast and location work to be as large as an
episode of its own, and do not discover that at render time.

## Known open faults to carry into episode 4

These were measured on episode 3 and are NOT fixed. Each one will bite again.

- **`BUDGET = 12.0` permits the band where takes die.** Measured over ep03's 24
  takes: 5.9-8.7 s takes pass 16/20 at a mean of 82.9; the two takes at 12.25 s
  pass 0/2 at a mean of 3.75, and they are the two worst in the episode. T22 has
  only 2 segments and still scores 3.8, so this is a separate axis from
  `SEGMENT_CAP`. Proposed: `BUDGET = 8.0`.
- **No gate reads text.** A re-roll produced a visiting card reading "Number 3
  Lauriston Gardens." instead of "Enoch J. Drebber", and DQ promoted it over the
  correct take because it scored higher. Any lettered prop needs an OCR check or
  best-of-N will actively choose the misspelt take.
- **Every DQ gate reads one 48x84 grey thumbnail**, 146:1 against the frame. A
  defect smaller than ~1/150 of the frame -- lettering, a face, a sixth finger,
  the wrong hat -- is invisible by construction.
- **Three of six ep03 plates are the wrong place.** `plate_corner_wall` is a
  street exterior for a setup described as "the darkest corner of the front
  room", because `described` opens with the exterior paragraph, and `geometry`
  never reaches the plate prompt at all.
- **No prop reference has ever reached a take.** `reference_list` never calls
  `props_in`; ep03's takes used 1-5 of 9 slots.
- **`wardrobe[state]` reaches no prompt** (`subject_text` has no callers), so
  `hat_line` falls through and every outdoor sheet orders a bareheaded Victorian
  into the street.
- **`identity` and `wardrobe` DQ rows are stubs.** `identity_gate.observe`
  raises `NotImplementedError` and facenet-pytorch is not installed.
- **`geo_gate` is dead code** — zero callers outside its own test.
- **Cut stamps round to a whole second** (+/-12 frames) while `cut_landing`
  allows [-4,+6]. Seven of ep03's 15 internal cuts could not pass even if the
  model obeyed perfectly. Beat stamps and cut stamps share the `At MM:SS` form,
  15 of each, which is a 1:1 prior that any stamp opens a shot.
- **`SKILL.md:136` says a narration stretch becomes "2-3 sub-shots"**, which is a
  3-4 segment SHOT, which `groups()` can never split -- the rule manufactures the
  take `SEGMENT_CAP` forbids.
