# Episode 12 -- The Avenging Angels: what the road found (2026-09-17)

Build notes kept as the episode is made; the DQ and the cut sections are
filled when those stages have run.

## The plan loop

`plan_check` went clean in six passes with no line rendered. Refusals, in
order: absences in prose ("gone", "nobody"); two lines over 18 words; a cap
in `physical` that drew a capped bust; a one-shot setup whose three spare
cells took the same alternate three times (fixed in `alt_panels`, and the
runout folded into the canyon); eight Hope closes against a wall of six; seven
sun-split faces (the brim named as the caster); "looking down" and "going
away" read as facing away; "tilted" read as a camera word; three Cowper MCUs
on one horse read as twins on text.

Found AFTER the plan check, each now moved into it: the quote gate (line 6,
nine of Doyle's words, after lines/respot/timeline/plates); the take packer
grouping shot 21 (1.7 s) into T20; the L8 pace lint on "walks at the CENTRE"
(advisory only, the built prompt is the verdict).

## Casting

Cowper's 125 Hz design did not agree with itself (0.64) and was Drebber's
twin (0.82); the nudge walks toward the rivals. Recast at 185 Hz soft tenor:
177 Hz, self 0.72, nearest the servant 0.76. drebber_wife: 218 Hz, self 0.80.

## Lines

25 lines, one rushed (Cowper's warning, 3.93-3.99 w/s twice); a comma and
"out" gave it 5.12 s and it passed. Runtime 164.0 s, speech 77 %.

## Plates and sheets

The camp_night plate drew under a lit twilight sky because the setup named no
sky; "a black sky full of stars" in `described` and a fresh seed fixed it.
The dawn sheet was blocked by the image model's safety filter (violence, on
the output) with a rifle aimed and "a bloody haunch"; softened, it drew.
Sheet gate: two false positives (hash dupe Q00/Q07; a rock crack as a white
line); day cells on the canyon have no black floor (p5 23-31, black 0.02-0.06)
-- the take look gate will say the same of their takes.

## Takes

27 takes queued, 4-9 min each (2.4 h). Shot 21 (a 1.7 s silent reaction) had
packed into T20; lengthened to 2.7 s and rendered as its own take, T20
re-rendered at its own length -- 28 takes, one shot each.

First DQ: 21/28. The seven, read by eye on 4-frame strips:

| take | row | what the picture did |
|---|---|---|
| T01 | off-board 0.89 | a pan on Hope walking the horse; the two riders pass behind the horse |
| T09 | off-board 0.75, last-vs-cell 0.19 | the cupped-hands halloo holds; the background shifts from cliffs to forest in the last third |
| T13 (turn) | invented cut 32.6 | opens on its MCU cell, jumps at frame 15 to shot 12's kneeling picture |
| T16 | no floor p5 22 | a correct sunlit wide with haze |
| T24 | off-board 0.76 | asked to PUSH in on the doorway; cut to shot 23's bier wide instead |
| T27 | churn wide 6.8, no floor p5 30 | a correct sunlit runout, walking figure |

One batched round of six (`--why=` written). T24's push rewritten as a pan:
it now holds the doorway -- the ep11 rule (a medium on a doorway takes a pan
too). T13's retake jumped again at frame 15; cut from 0.67 s in instead.
T01, T09, T27 retakes scored LOWER than the originals and `--attempts` kept
the originals. Final 24/28.

## What was built

- **A head trim** (`heads.json`, assemble + edit gate through one reader,
  refused on dialogue shots): a take whose first frames are the invented jump
  is cut after it, when the render is long enough. The edit gate compared from
  frame 0 and reported all 191 frames off until it read the same file.
- **Two plan_check gates** (ONE PER TAKE, L8 pace) and the quote gate moved in.
- **alt_panels** kind follows the cell; **name_map** possessive fix.

## What the gates got wrong

The look gate's black floor (p5 <= 20, black >= 0.08) refuses sunlit wides on
every day setup: ep11 T00 at 19 moved the constant, ep12 T16/T27 at 22/30 need
it again. A day setup is not a night setup; the floor wants to be read per
setup light (sun vs lamp), not per episode -- open item.

## Publish

QC PASS sha8 3834c9c5, 169.70 s, -14.3 LUFS. Published with a recorded
override for the four accepted takes, on the owner's standing instruction:
https://youtu.be/s7_uJ-VSDHk. Spend $1.07. Clock 3.6 h of stages, takes 70 %.
