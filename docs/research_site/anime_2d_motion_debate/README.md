# Why AI-built "2D animation" came out as a slideshow, and what six research agents agreed would fix it

*A two-round debate between six AI research agents, judged by a lead agent. November 9, 2026. Desk research only:
the fixes below are ranked and costed, not yet rendered.*

## The complaint

The night before, an AI agent built five 2D book scenes in Blender: one generated anime drawing per shot, split
into layers, stacked as planes, with a slow camera, drawn rain, and narration. The owner's reaction:

> "all images seem static ... 2d animation?? ... no consistency in the world space ... this looked like basic
> image in 2d ... 2d animation like in the anime, not static images"

Every automated check had passed.

## The method

Six agents, one lane each: diagnosis, world and cast, the anime look, generative motion, anime-style 3D
characters, and motion inside flat drawings. Round one: a position paper with sources and a costed top five.
Round two: each agent reads the other five, writes the strongest objection to each, says what it now concedes,
ranks the best five actions across all lanes, and names the first experiment and the result that would kill it.
Every claim is graded MEASURED, SHOWN, CLAIMED or OPINION.

## What the diagnosis measured

- **The drawings were fine.** Several keyframes pass as TV anime frames.
- **The picture almost never changed.** 36 drawings in 233 seconds: 0.15 drawings per second, one per narrated
  sentence, each held 6.7 seconds. The diagnosis paper puts 1963 television anime near 1.0 and a current show at
  2.3 to 3.4.
- **Nothing deformed.** In 35 shots, every layer was a rigid card. The character drawing changed inside the shot
  in one shot of 35.
- **The motion check measured the wrong thing.** It scored movement in the whole frame, so a drifting camera
  passed all 35 shots a human called static.
- **There was no world.** Every background was drawn from words alone. One scene has five different bridge
  constructions in seven shots.

## What changed minds in round two

| Agent | Opened with | After reading the others |
|---|---|---|
| Anime look | A compositing pass as the first action | Withdrew it: compositing is the last stage, and only needed once character and background come from different sources |
| Flat-drawing motion | Key-pose swaps made by image edits | Conceded they are unproven (the one swap already made had doubled a character's eyes) and put video takes first wherever a body moves |
| World and cast | A 3D box set with depth control | Demoted it: a master picture per place first; a consistent world alone is "a consistent slideshow" |
| Generative motion | A masked take that repaints only the character | Dropped it as untested, and argued the Blender 2D route should not be a separate pipeline at all |
| Anime 3D characters | A rigged anime puppet per character | Parked its own route: a 3D render is not the 2D result that was asked for |
| Diagnosis | Cadence first | Conceded that more cuts drawn from words multiply the world drift, so the place master ships with the cut plan |

## Where it converged

1. **A cut per action**, two to three and a half seconds, instead of a cut per sentence. Free.
2. **One master picture per place**, drawn empty and wider than the frame. Every cut is a crop or a one-step edit
   of it. A place is held by pixels, never by words.
3. **Motion by shot type.** Quiet cuts: small drawn changes (eyes, a hand, hair) on a timing sheet. Cuts where a
   body moves: a short take from a local video model. Never an in-between from drawing A to drawing B, never
   bone-rigged paper limbs.
4. **Blender as a station, not the animator.** It holds the cut, the camera on held shots, the timing sheet
   (camera on ones, cast on twos or threes) and the final character-over-background composite.
5. **Compositing last and light.**

Five agents independently priced such a pipeline at 37 to 38.5 machine minutes for a 48-second scene on one
RTX 4090, from unit prices measured earlier. None of it has been run.

## What stayed open

- How much acting can be drawn swaps before a viewer calls it a slideshow with blinks.
- Whether a figure drawn apart and laid over the place reads as pasted.
- Whether a video take should start from the drawing or from reference pictures only.

One experiment was designed to settle all three: one scene, three versions (as shipped, limited animation, video
takes), ranked blind by the owner, with a stated result that kills each arm.

## Lessons that travel

- **A check that passes everything a human rejects is measuring the wrong thing.** Motion in the frame is not
  motion in the subject.
- **Count how often the picture changes.** It is the cheapest number that separates animation from a slideshow.
- **A debate works when agents must name what kills their own proposal.** Four of six withdrew or parked their
  opening position.
- **"Used the tool" is not "did the craft".** A 3D package used as a multiplane camera is not 2D animation.
