# Episode 13 -- A Continuation of the Reminiscences: what the road found (2026-09-17)

## Plan and cast

The plan was written while episode 12's takes rendered (CPU only) and went
clean in four passes. New refusals worth keeping:

- A row NAME with a possessive ("a wife of Drebber's") claimed the token
  "drebber's", so "Enoch Drebber's face" named her in the marks gate. Fixed in
  `name_map`: a possessive is the bare name.
- "silk top hat" (Lestrade's mark) and "sandy hair" (Brigham Young's) cannot
  appear on anyone else's shot; "cabman's hat" belongs to the new cabman row.
- G-FIRSTFRAME wants a median of 60 geometry words per setup; one more measured
  sentence each.
- The Lauriston front room was drawn in ep03 with its mantelpiece on the LEFT;
  ep13's first draft had it on the right.

Hope's `outdoor` wardrobe is the Utah sombrero, so the rain on the cab box got a
second row, `jefferson_hope_cabman` (same physical, bust copied, one card).
London Drebber is young Drebber aged twenty years (no London episode had drawn
his face). The Inspector's voice (141 Hz, self 0.82) sits at 0.85 against the
ep04 constable; accepted, the two never share an episode.

## Lines

The turn line "Now, Enoch Drebber. Who am I?" measured 0.46 and then 0.55
against Hope's voice (floor 0.65), and two `--redo` rounds returned 0.55 again:
six words give the speaker embedding too little. Lengthened to "Now then, Enoch
Drebber. Look at my face, and tell me who I am." it passed; the Inspector's line
lost two words to stay under the 20 % dialogue wall, which then packed shots 1
and 2 into one take until shot 1's hold grew.

## Plates and sheets

Two plates drew the wrong time of day: the cab street as grey dusk and the
Brixton room with a daylit window. "under a black night sky" and "a window black
with night" fixed both. The sheets drew well; Watson's close looked like a
stranger until compared with his card -- it WAS his card. A redraw that was not
needed ($0.08): compare a surprising face with the card before redrawing.

## Dry build

The dry build refused one take at a time and named none ("[Shot 1]" is every
single-shot take). Now it names the take and lists every refusal at once. The
two faults: a setup's CROWD line ("travellers walk along the platform") is in
every take of that setup and needs its own pace; "his head draws back" is not a
body-scale verb to L4 ("pulls back" is).

## Takes

28 takes, 27 passed first time -- the best first-pass DQ of the series. The one
hard failure was T08, the wide of the cab in the rain: asked to PUSH in, it
overran to 1.94x and read 0.46 off-board. Rewritten as a pan it came back
100/100. Three advisories were accepted on sight: T07 (Drebber walking the
platform, background shifts behind him), T21 (the wide of the fallen body, a
push again at 1.74x) and T26 (the Inspector at the bell, a pan that drifts).

The lesson is the ep11 one, again and in a new place: **a wide given a push
overruns**. Closes and MCUs already pan by rule; wides on a moving subject want
a pan too, or a push named at a hand's breadth with something that keeps an
edge.

## The title card, and the credits running out

The paid image API answered `credit_balance_exhausted` with the episode
finished but for its card -- and a 1:1 episode cannot fall back on the generic
9:16 card. `title.py --local` now draws the still on the owner's own model:
same desk, skein, lamp and silhouette, the three lines legible, the word
SCARLET red. The one thing the local drawer will not draw is the scarlet
thread, so the paid card stays the default.

## Publish

QC PASS sha8 f69b1444, 170.04 s, -14.3 LUFS, 28/28 takes, no override needed:
https://youtu.be/OoTLbV3KurU. Spend $0.73.
