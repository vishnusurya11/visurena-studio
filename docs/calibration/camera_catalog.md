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
| locked | "The camera holds a locked-off frame; <actor verb>." | dialogue, a reaction, a still moment where the actor moves | a frozen start if the actor has no verb | works (ep02: 8/8 held; a low-angle 'locked' close still crept 1.4-1.9x) |
| push_slow | "The camera pushes in slowly toward <subject>." | realisation, a close on a face or insert | overrun on wides (ep13 T08 1.94x): mediums and inserts only | mixed (ep02: works on a medium close; overran 3.5x on an insert and 1.9-3.3x on closes, twice into invention) |
| pull_reveal | "The camera pulls back from <detail>, widening to show <the room / what surrounds it>." | reveal, aftermath, scale | invents what lies past the frame: reveal only what the wide contains | works (ep02 T10 three renders out of three) |
| pan_to | "The camera pans from <A> across to <B>." | carry the eye between two things in the room | turns into an orbit if A or B is told to keep its place | mixed (ep02: works on the study and villa wides; letterboxed once, arced once, a walker walked into the lens once) |
| tilt_up | "The camera tilts up from <ground detail> to <what stands above it>." | scale, a figure rising, sky, a dome | overran to the skyline and invented a terrace (Scarlet ep14): stop at something in the wide | works (ep02 T15) |
| tilt_down | "The camera tilts down from <sky / face> to <hands / ground>." | from the sky to the earth, from a face to what it holds | — | fails (ep02: read as a pull-back on a close; opened on the plate on an insert) |
| track_lateral | "The camera tracks sideways to the <left/right>, past <foreground object>, with <subject> behind it." | depth, parallax, a sense of place | may read as an orbit if a subject is centred and named as held | works (ep02: palings, gate top, and the rim insert; parallax on a foreground post) |
| follow | "The camera tracks behind / beside <figure> as <he/she> walks toward <place>." | walks, arrivals, the porch | a small figure in a wide never left the gate (G-MOTION ep01 advisory) | works (ep02: 5/5 incl. T11 once its first 0.5 s is trimmed) |
| crane_up | "The camera rises slowly above <subject>, looking down over <the place>." | endings, the heath, scale | invents the roofscape: point it at what the wide shows | works (ep02 T19 twice: seam to the whole hull) |
| crane_down | "The camera descends from <sky / treetops> to <figure at ground level>." | openings, arrivals | — | fails (ep02 T02: no descent; became a lateral follow) |
| low_angle | camera line: "a low angle from knee height looking up at <subject>" + one move | authority, menace, the machines | angle words were ignored at Scarlet ("amounts, angles"): trial it | mixed (ep02: held on T17 and T09; T07 twice came back at eye level) |
| high_angle | camera line: "a high angle looking down on <subject>" + one move | smallness, the pit, the crowd | as above | works (ep02 T04 three renders) |
| over_shoulder | "Over <A>'s shoulder toward <B>; the camera holds; <B> speaks." | two-hander dialogue | the face ends up on the wrong subject; bind the faces clearly | works (ep02 T12) |
| handheld | "The camera is handheld, drifting gently with <figure>." | panic, the flight chapters | may churn; keep it for the panic chapters | untested |
| rack_focus | "Focus shifts from <foreground object> to <figure behind it>." | two planes of meaning | may be ignored entirely | fails (ep02 T17: no focus change; a locked medium-wide) |
| orbit | "The camera circles slowly around <subject>, keeping <subject> in the centre." | a rare hero beat only: at most one per episode | THIS is what ep01 did 18 times by accident | works (ep01, involuntarily) |

## Smoothness: blur and warp, measured (ep02, 2026-09-19)

`scripts/episode/motion_quality.py <book> <n>` measures every take on grey
frames at 6 fps: sharpness (Laplacian variance) per frame, and the optical-flow
incoherence between consecutive frames. Flags, calibrated on ep02 and checked
against the strips: `BLUR` = 3+ frames under half the take's own sharpness, or
a minimum under 0.5; `REFRAME` = flow incoherence max >= 1.4, which is a take
that jumps to a NEW FRAMING (not a melt). The mean incoherence on a locked
shot is the actor's own motion and means nothing; read the max.

What ep02's 23 takes showed:
- **Zoom-type moves soften.** The one visibly soft take was the push-in (T16:
  6 blur dips, min 0.45, and the face distorted as it filled the frame). The
  pull-back (T10, min 0.65) and the wide pan that became a push (T20, 0.56)
  softened next. Lateral moves, tilts and locked shots stayed sharp (min 0.8-0.98).
  Reason: a magnified region of a 768 px render has less detail to upscale.
- **Late reframes come from the last clause.** T12 ("...the horse pulls the cart
  on along the road") jumped in its final second to the waggoner up on the cart;
  T21 ("...fingers point away down the road") jumped to the brick wall. H3 follows
  a departing subject to wherever the words send it. RULE: the final clause of
  `motion` stays inside the opening frame -- a gesture, a look, a hand settling --
  never an exit, an "away", or an "on along".
- **Over-the-shoulder: the foreground face slice warps.** T12's foreground
  Ogilvy was a distorted ear-and-cheek. Put the SHOULDER and the back of the
  head in the foreground, never a sliver of face.
- **Locked-off shots are the sharpest and the most stable** (no dips, no
  reframes) and carry dialogue best: prefer them for every spoken line.

## Where the remaining blur comes from (ep03, 2026-09-19)

Three takes still flag BLUR after two iterations, and the cause is the same in
all three: **an extreme magnification of the one location wide**.
- T03, an insert on the cylinder's crust: sharpness min 0.19 of its own median.
- T10, a pull-back that STARTS on a hand against the crust: min 0.35, 20 dips.
- T11, a wide pan that became a 1.4x push: min 0.48.
The prop sheet IS staged on these takes, but the location wide is Picture 1 and
a take opens at its first picture's framing, so the insert is a crop of the
wide, not of the sheet. Two ways out, neither tried yet:
1. stage the PROP sheet first on a prop insert with no faces (needs the picture
   numbering in `episode_ref_official.subjects` to move with it); or
2. write the insert as a medium (blocked on its own: G-VARIETY wants 4 inserts).
A pull-back that ENDS wide is sharp where it lands; only its first second is soft.

## Clones: one description, many copies (ep03, 2026-09-19)

The owner saw duplicated characters. Measured on ep03's takes: the LEADS never
cloned (`people_check.py`: 0 clone frames in 23 takes of ep01, ep02 and ep03),
the CROWDS did.
- T19 "three workmen in collarless shirts and moleskin trousers digging" -> three
  identical men, same face, same pose, side by side.
- T12 "a stream of people in straw hats and light summer dresses" and T14's
  "crowded rim" -> rows of the same woman in white and the same boater.
A group described once is a single figure to the model, repeated. Every figure
at a readable size needs its own dress and posture; a crowd is heads and
shoulders above an edge, or small distant figures, never a countable group of
identical roles.

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
| ep02 iter2 | T04 | high_angle | wide | zoom 0.99x, churn 4.3 | works | same as iter1; "the hull towers many times his height" did not enlarge the drum: the pit picture sets its size |
| ep02 iter2 | T06 | tilt_down | insert | cut 60.5 HARD, DQ 60 FAIL (twice) | invents | opened on the pit's own wide for half a second, then cut to the rim insert; the clinker shower and the grey drift that followed were right |
| ep02 iter2 | T07 | low_angle | medium | zoom 1.00x, churn 4.5 | drifts | no low angle: an eye-level follow of him walking past the drum, upright, in his suit |
| ep02 iter2 | T09 | push_slow | medium_close | zoom 1.97x, churn 7.0, DQ 64.9 | invents | began on a full-length front-on sheet pose, then pushed to a face-filling close: the overrun again, from further out |
| ep02 iter2 | T09 (2) | low_angle | medium_close | zoom ~1.9x, DQ 85 | mixed | crouched at the drum, spoke with good lips; the "locked-off" camera still pushed in from medium to close |
| ep02 iter2 | T10 | pull_reveal | medium | zoom 0.32x, churn 6.6 | works | again; with "towering" in the words the drum now reads three times his height |
| ep02 iter2 | T11 | pan_to | medium | zoom 0.68x, churn 10.9, DQ 36 | drifts | no letterbox this time; the pan became an arc around him to the cart (an orbit by the back door), and the sheet's cape came back |
| ep02 iter2 | T14 | locked | medium_close | zoom 1.07x, churn 2.0 | works | the camera held; "on the pavement" did not move him out of the garden: the location picture has the house behind the palings, so he stands in front of it |
| ep02 iter2 | T16 | push_slow | medium_close | zoom 3.29x, churn 8.4, DQ 71 | mixed | began medium-wide and pushed to a close (3.3x); readable and emotional, but the overrun is real |
| ep02 iter2 | T17 | low_angle | medium_close | zoom 0.98x, churn 1.5, face 0.18 | works | the low angle held: he cups his ear looking down at the lens, face readable for the line |
| ep02 iter2 | T18 | follow | medium | zoom 1.21x, churn 4.8 | works | again |
| ep02 iter2 | T20 | pan_to | wide | churn 6.5 HARD, DQ 95.5 FAIL | invents | the Narrator waiting at the gate walked into the lens and filled the frame |
| ep02 iter2 | T20 (2) | pan_to | wide | DQ 85 PASS | works | with the Narrator far off in the doorway the pan landed on the house as asked |
| ep02 iter2 | T21 | track_lateral | insert | churn 7.3, DQ 76.6 | works | the paper folded edge-on: no masthead |
| ep02 iter2 | T22 | locked | medium_close | zoom 1.04x, churn 2.6, face 0.24 | works | the boy points and speaks, face readable to the end |
| ep02 iter3 | T04 | high_angle | wide | zoom 1.01x, churn 3.9, DQ 90 | works | on the redrawn pit (one long hull): the high angle and the tilt down to the end both read; the figure crouched at the rim, in the sheet's cape |
| ep02 iter3 | T06 | track_lateral | insert | zoom 1.00x, churn 2.7, DQ 100 | works | on the new pit picture it no longer opened on the plate: the rim cracks and the clinker drifts down (the head trim was dropped) |
| ep02 iter3 | T07 | low_angle | medium | zoom 0.99x, churn 1.9, DQ 100 | drifts | eye level again: a follow of him walking to the hull and laying a hand on it |
| ep02 iter3 | T08 | locked | insert | zoom 1.02x, churn 1.5, DQ 100 | works | the camera held and a black mark appeared on the rim; the lid was drawn as a flat disc lying on the sand, unlike its neighbours |
| ep02 iter3 | T09 | low_angle | medium_close | zoom 1.44x, churn 3.7, DQ 95 | mixed | crouched, looked up into the lens, spoke; "locked" still crept in 1.4x |
| ep02 iter3 | T10 | pull_reveal | medium | zoom 0.11x, churn 5.9, DQ 80 | works | the third time: from his hands on the seam out to the whole hull, the best reveal in the episode |
| ep02 iter3 | T18 | follow | medium | zoom 1.16x, churn 3.6, DQ 95 | works | again |
| ep02 iter3 | T19 | crane_up | insert | zoom 0.48x, churn 2.1, DQ 90 | works | again: from the stick on the seam up to the length of the hull |
| ep02 iter4 | T08 | locked | insert | DQ 100 | invents | the lid again a flat disc, now with a black drip down its edge; iter3's render kept |
| ep02 iter4 | T11 | follow | medium | zoom 1.42x, churn 8.2, DQ 82.6 (was 36) | works | opened for 0.3 s on the sheet's front-on face, then followed him from behind waving at the cart; the cut enters at 0.5 s (heads.json) |

## What ep02 taught (49 renders of 23 shots)

- **Variety is achievable and it reads.** 14 move ids over 23 shots, none on more than
  five, no orbit on purpose; the coordinator's contact-sheet review called the variety
  a clear success. The one accidental orbit (T11 iter2) came from a pan whose subject
  was a running man in the middle of the frame.
- **The location picture outranks the words on size and shape.** "The hull towers many
  times his height" changed nothing while the pit picture drew a coin two men tall;
  redrawing that one picture changed every pit take at once.
- **A take can open on a reference picture and cut away from it** (0.3-0.6 s): the plate
  on an insert with no person in it (T06, three renders on the old pit picture) and the
  sheet's front-on face on a figure seen from behind (T11 iter4). On a shot with no
  dialogue, `heads.json` enters the take after it; with dialogue it would break lip-sync,
  so re-render instead.
- **A push has no brake on a close.** Asking for a push from a medium close is safer
  than from a close; a "locked" low-angle close still crept 1.4-1.9x.
- **Moves H3 ignores:** crane_down (became a follow), rack_focus (nothing), tilt_down
  (became a pull-back). Use crane_up, pull_reveal and track_lateral instead.
