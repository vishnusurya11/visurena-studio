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
