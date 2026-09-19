# Camera catalog — MiniMax-H3 ref2va, refs-only

Started 2026-09-19 after the owner watched WotW ep01: "almost every other shot
is a circle around the object or an arc… not good visually".

## Why ep01 orbited

It wasn't H3's taste; it was our words.
- 18 of 23 ep01 shots were pans.
- Every pan named something that "keeps the left third" (or the centre, or an edge).
- A camera that rotates while its subject holds still in the frame has to
  travel AROUND the subject. So each "pan … X keeps the left third" was an orbit request.

The habit came from a Scarlet rule (SKILL.md, "A WIDE GIVEN A PUSH OVERRUNS
TOO", ep13): "a push is for an insert; everything else pans, and the pan
clause names what keeps an edge". That rule was tuned to pass DQ rows
(zoom overrun, off-board). It passed them, and it made the picture monotonous.
Gates are not quality.

## The rules for choosing moves (from ep02 on)

1. **Variety.** No move on more than ~25% of an episode's shots, and never the
   same move on two consecutive shots.
2. **Only an ORBIT asks for its subject to stay put.** A pan names where the
   frame ARRIVES ("sweeps from the door to the window"). A track names what it
   passes. A tilt names what it reveals. Never write "keeps the …" on a pan or a track.
3. **Direction, not distance.** H3 obeys a move's direction and ignores its
   amount (handoff §4). Point every move at something the location wide
   already contains.
4. **A locked-off shot is a move.** When the actor carries the action, lock
   the camera and give the ACTOR the verb. Scarlet's frozen starts came from
   stillness words in the whole prompt; a locked camera plus a body verb is different.
5. **Motivate the move.** Follow a walk, reveal what the line names, push on
   the realisation, pull back on the aftermath.

## The moves

Status starts at `untested`. Each trial records the take, the measured result
(DQ zoom, churn, off-board where measured) and the eye verdict: `works`,
`drifts` (did a different move), `frozen` or `invents` (made up content).

| id | H3 phrasing (affirmative, direction only) | use for | risk from history | status |
|---|---|---|---|---|
| locked | "The camera holds a locked-off frame; <actor verb>." | dialogue, a reaction, a still moment where the actor moves | a frozen start if the actor has no verb | untested |
| push_slow | "The camera pushes in slowly toward <subject>." | realisation, a close on a face or insert | overrun on wides (ep13 T08 1.94x): mediums and inserts only | untested |
| pull_reveal | "The camera pulls back from <detail>, widening to show <the room / what surrounds it>." | reveal, aftermath, scale | invents what lies past the frame: reveal only what the wide contains | untested |
| pan_to | "The camera pans from <A> across to <B>." | carry the eye between two things in the room | turns into an orbit if A or B is told to keep its place | untested |
| tilt_up | "The camera tilts up from <ground detail> to <what stands above it>." | scale, a figure rising, sky, a dome | overran to the skyline and invented a terrace (Scarlet ep14): stop at something in the wide | untested |
| tilt_down | "The camera tilts down from <sky / face> to <hands / ground>." | from the sky to the earth, from a face to what it holds | — | untested |
| track_lateral | "The camera tracks sideways to the <left/right>, past <foreground object>, with <subject> behind it." | depth, parallax, a sense of place | may read as an orbit if a subject is centred and named as held | untested |
| follow | "The camera tracks behind / beside <figure> as <he/she> walks toward <place>." | walks, arrivals, the porch | a small figure in a wide never left the gate (G-MOTION ep01 advisory) | untested |
| crane_up | "The camera rises slowly above <subject>, looking down over <the place>." | endings, the heath, scale | invents the roofscape: point it at what the wide shows | untested |
| crane_down | "The camera descends from <sky / treetops> to <figure at ground level>." | openings, arrivals | — | untested |
| low_angle | camera line: "a low angle from knee height looking up at <subject>" + one move | authority, menace, the machines | angle words were ignored at Scarlet ("amounts, angles"): trial it | untested |
| high_angle | camera line: "a high angle looking down on <subject>" + one move | smallness, the pit, the crowd | as above | untested |
| over_shoulder | "Over <A>'s shoulder toward <B>; the camera holds; <B> speaks." | two-hander dialogue | the face ends up on the wrong subject; bind the faces clearly | untested |
| handheld | "The camera is handheld, drifting gently with <figure>." | panic, the flight chapters | may churn; keep it for the panic chapters | untested |
| rack_focus | "Focus shifts from <foreground object> to <figure behind it>." | two planes of meaning | may be ignored entirely | untested |
| orbit | "The camera circles slowly around <subject>, keeping <subject> in the centre." | a rare hero beat only: at most one per episode | THIS is what ep01 did 18 times by accident | works (ep01, involuntarily) |

## Trial log

One row per trial take: `episode | take | move id | size | result | eye verdict | note`.

| ep | take | move | size | measured | eye | note |
|---|---|---|---|---|---|---|
| ep02 iter1 | T00 | pan_to | wide | zoom 0.98x, churn 2.9 | works | panned lamp to windows; the streak crossed the glass right to left |
| ep02 iter1 | T01 | locked | medium_close | zoom 1.02x, churn 1.2 | works | pen writes, a green wash crosses the window behind him |
| ep02 iter1 | T02 | crane_down | wide | zoom 0.92x, churn 2.0 | drifts | no descent at all: it became a lateral track following the walking figure (a good shot, the wrong move) |
| ep02 iter1 | T03 | follow | medium | zoom 1.12x, churn 9.6 | works | tracked beside him through the heather to the smoke |
| ep02 iter1 | T04 | high_angle | wide | zoom 0.99x, churn 2.9 | works | the high angle held; the tilt-down read as a slight push; the figure crouched at the rim |
| ep02 iter1 | T05 | locked | medium_close | zoom 0.96x, churn 3.3, lip mux 0.000 | works | spoke on the locked frame |
| ep02 iter1 | T06 | push_slow | insert | zoom 3.52x, churn 6.7 | invents | overran 3.5x into the rim and split the lid open on a black cavity (asked: a slab of crust falls) |
| ep02 iter1 | T07 | low_angle | medium | zoom 0.96x, churn 6.3 | mixed | the low angle held; "slides on his heels" became a man lounging in the sand, in the sheet's cape |
| ep02 iter1 | T08 | locked | insert | zoom 1.00x, churn 0.9 | works | the lid rim held and the mark crept left; the turn is faint |
| ep02 iter1 | T09 | push_slow | close | zoom 1.91x, cut 40.6 HARD, DQ 19.7 FAIL | invents | overran from a close into a face-filling extreme close, then a hard cut to a POV of the lid with a hand ("his hand rises toward the lid") |
| ep02 iter1 | T10 | pull_reveal | medium | zoom 0.27x, churn 7.0 | works | pulled back from his hands on the lid to the whole end of the cylinder |
| ep02 iter1 | T11 | pan_to | wide | zoom 1.00x, churn 1.9, black share 0.54 | invents | letterboxed a 3:2 picture inside the square with black bars; the running figure lost in the heather |
| ep02 iter1 | T12 | over_shoulder | medium_close | zoom 1.00x, churn 2.6 | works | Ogilvy's shoulder foreground, the waggoner facing him, then up on his cart |
| ep02 iter1 | T13 | track_lateral | medium | zoom 1.02x, churn 10.4 | works | tracked along the palings; the gas lamp passed in front (parallax) |
| ep02 iter1 | T14 | locked | medium_close | zoom 1.03x, churn 1.6, lip mux -0.010 | works | camera obeyed; staging put him inside the garden with the house behind him |
| ep02 iter1 | T15 | tilt_up | medium_close | zoom 0.99x, churn 3.9 | works | tilted up the spade to his face as he straightened |
| ep02 iter1 | T16 | push_slow | medium_close | zoom 1.86x, churn 6.2 | works | a medium close pushed to a close; no overrun into invention |
| ep02 iter1 | T17 | rack_focus | medium_close | zoom 1.00x, churn 0.7, face 0.05 | drifts | no focus change at all; a locked medium-wide with his face a twentieth of the frame for a spoken line |
| ep02 iter1 | T18 | follow | medium | zoom 1.61x, churn 6.0 | works | tracked behind the two men down to the cylinder |
| ep02 iter1 | T19 | crane_up | insert | zoom 0.58x, churn 5.3 | works | rose from the seam to a top-down view of the whole lid |
| ep02 iter1 | T20 | pan_to | wide | zoom 1.75x, churn 7.8 HARD, DQ 82.5 FAIL | mixed | panned to the house as asked but turned into a 1.75x push while two figures moved (boy running, man walking) |
| ep02 iter1 | T21 | track_lateral | insert | zoom 0.85x, churn 9.3 | works | the move worked; the prop failed: a legible gibberish masthead ("Daily Chrciples") |
| ep02 iter1 | T22 | tilt_down | medium_close | zoom 0.71x, churn 6.0 | drifts | read as a pull-back from his face to a full figure at the gate |
