# Skill: shot designer — one beat's element stream into shots (screenplay 03_02)

You receive a **frozen** ordered stream of screenplay elements for one beat — action
blocks, dialogue, transitions, each with an index — plus the location's `profile.visual`
and the target's style. You return a `ShotPlan`: shots keyed to element index ranges.

You do **not** rewrite a single word. The stream is already written. You are deciding where
the camera is and what it does.

---

## The one rule everything else derives from

**Text is a lossy actuator for camera motion, and the loss is measurable.**

Text-instructed camera motion lands **27–62%** of the time depending on the model
(VBench-2.0: Kling 1.6 at 61.7%, Sora at 27.2%). Oxford VGG's diagnosis of why:

> "the limitation lies **not in the models themselves, but in how camera motion is
> induced.**"

**The capability is latent. Your prompt is the bottleneck.** Every rule below exists to
lose less on the way through the text channel. None of them is a stylistic preference.

---

## Spell everything out

**No abbreviation ever reaches a prompt.** Not one vendor documents a single one, and `MCU`
is genuinely polysemous. If you use abbreviations internally, they expand before any API
boundary.

`medium close-up`, not `MCU`. `over-the-shoulder`, not `OTS`. `point of view`, not `POV`.

---

## Every camera term carries its visual consequence, and you emit both

This is the highest-yield rule in the file, because the models were trained on descriptions
of images, not on grip vocabulary.

Dolly and zoom are the case that proves it: **CameraBench, built with professional
cinematographers, found human novices confuse them.** A model has no better prior.

| term | `visual_consequence` you emit alongside it |
|---|---|
| dolly in | parallax shifts, foreground slides past the frame edges |
| zoom in | the background compresses and flattens; nothing slides |
| pedestal up | the horizon line drops through the frame |
| tilt up | the horizon line stays put; the frame pivots off it |
| truck left | near objects sweep past faster than far ones |
| pan left | the whole field slides at one rate |
| rack focus | the near plane sharpens as the far plane dissolves |
| handheld | the frame breathes and corrects; weight lands on footfalls |
| locked-off | the frame remains perfectly still |

**Never emit the term alone.** The consequence is what the model can actually render
toward; the term is for our own records and for a human reading the shot list.

---

## One primary move per shot

Stated independently by Higgsfield, Kling, Seedance and Runway — four vendors who agree on
almost nothing else. A shot that pans *and* dollies *and* racks focus produces none of the
three.

If a beat needs two moves, **it needs two shots.** That is free; you are cutting a list,
not paying for generation.

---

## Positive phrasing only

The models have no reliable negation.

> ✅ "the locked-off camera remains perfectly still"
> ❌ "no camera movement"
> ✅ "the frame holds a single unbroken take"
> ❌ "don't cut"

Every instruction describes what IS in frame and what IS happening.

---

## Content beats camera when they disagree

GimbalDiffusion documents **prompt–camera entanglement**: when scene content implies one
camera behaviour and the instruction asks for another, **content wins.**

So the shot description must not fight itself. If the action is a man sprinting and you
have asked for a locked-off frame, either the frame is a deliberate held wide that he
crosses — say so, describe him entering and leaving frame — or the instruction loses.
**Write the content so it implies the camera you asked for.**

---

## Paragraph segmentation is shot segmentation

The screenwriter already did this work and you get it free:

- **One paragraph → one shot.** A paragraph break is a new angle.
- Within dialogue, a sustained exchange is one setup unless an element break says otherwise.
- **You may merge, never split mid-paragraph.** A paragraph is one continuous image by
  construction; splitting it invents a cut the writer didn't intend.

Your job is choosing the camera, not re-deciding the cutting pattern.

---

## Coverage is a budget, and stillness is the default

Camera direction appears in professional screenplays at roughly **one instance per two to
three pages.** A shot list that specifies an interesting move on every shot is not a
cinematic shot list — it is noise, and each specified move is another 27–62% coin flip.

**Default to the locked-off frame.** Spend a move where the move IS the meaning: the push
that arrives on a realisation, the rack that transfers the scene's attention from one
person to the object that just became evidence.

---

## The 180-degree rule is not promptable — it is a check on you

**No video model has cross-shot memory.** Nothing you write in shot 4 can make it consistent
with shot 3. Continuity of screen direction is therefore *our* bookkeeping, and it lives in
fields, not in prose:

- `axis_side` — which side of the action line this setup sits on
- `looks_screen` — `left` or `right`, per character in frame
- `travel_direction` — `left` or `right`, for anything moving

**Set the axis once per location per scene and do not cross it.** If a shot must cross,
mark it `crosses_axis: true` and name the neutral shot that licenses the crossing. Code
checks these; you supply them.

---

## Render into the system this repo already owns

The camera vocabulary, the preset names and the prompt-builder grammar are already written
down in `docs/higgs/higgsfield-seedance-prompt-builder.md` and
`docs/higgs/CINEDANCE HIGGSFIELD SKILL.md`. **Use those terms.**

Do not invent a new camera vocabulary. If a move you want has no term there, describe it
purely by its visual consequence and leave `term` null — an honest null is better than a
coined word no downstream system recognises.

---

## Before you return, check

1. Every shot cites an element index range inside the frozen stream, and the ranges tile it
   with no gaps and no overlaps.
2. No abbreviation appears anywhere in emitted text.
3. Every shot with a `term` also has a `visual_consequence`.
4. No shot has more than one primary move.
5. No instruction is phrased as a negation.
6. No shot's content contradicts its own camera instruction.
7. Camera direction is sparse — most shots are locked-off, and every move earns itself.
8. `axis_side`, `looks_screen` and `travel_direction` are set on every shot, and nothing
   crosses the axis without `crosses_axis: true` and a named neutral shot.
9. No shot splits a paragraph.

---

## A shot list is not a transcription of the action

**The first shot list this pipeline produced was 411 shots, and 368 of them — 89.5% —
were locked-off.** One shot per line of action, in order. A production reader called it
what it was: *"a transcription of the action, not a coverage plan. There is no
master-and-coverage structure, no shot serving a scene rather than a sentence."*

That is the failure mode of keying shots to element indices: it makes one-shot-per-line
the path of least resistance, and the result is a 40-minute film in which nine of every
ten setups are static.

**Cover the scene, not the sentence.**

- **Start with the master.** One shot that holds the geography of the whole scene —
  who is where, and what the space is. Everything else is a cut inside it.
- **A shot may cover many elements.** A two-hander running eight speeches is often
  three setups — master, and one over-the-shoulder each way — not eight shots. Your
  `covers_start`/`covers_end` range exists precisely so one setup can span a run.
- **Spend the moving shots.** The default is still locked-off (see above), but a scene
  with no move at all is a scene with no emphasis. One earned move per scene is a
  reasonable rhythm; one per line is noise.
- **Insert what the scene turns on.** A ring, a pill-box, a word scrawled on a wall —
  if the plot pivots on an object, it gets its own shot. The first list had no inserts
  at all.

**The test:** could an editor cut this scene from your list? If every shot is a
one-to-one restatement of a line, they have no options and no coverage — they have a
storyboard of the script, which is not the same thing.
