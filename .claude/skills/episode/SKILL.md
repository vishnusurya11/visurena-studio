---
name: episode
description: Turn one book chapter into a 2-3 minute vertical (9:16) or square (1:1) microdrama episode — first-person narration laid over pictures cut to the measured voice, the chapter's own locations, one storyboard sequence per setup drawn by gpt-image-2.5, every take rendered on local MiniMax-H3 ref2va from the storyboard's cells with dialogue lips driven by the line's own wav, DQ-gated, iterated with five reviewers. Use when writing, building, fixing or reviewing an episode under library/<book>/episodes/.
---

# Episode

An episode is ONE WHOLE CHAPTER (owner, 2026-09-10), 2 minutes as the
target, 2-3 minutes when the chapter is big. Every iteration ends with the
master's full path first, kept as `master_iterN.mp4` (never overwrite the
only copy). Every paid image is logged in `library/<book>/spend.jsonl`
(`studio/spend.py`, calibrated 2026-09-10: a 2048x3072 sheet ~$0.20, a
2048x2048 sheet ~$0.13, a 1024x1536 still ~$0.08, a 1024x1024 still ~$0.05;
the OpenAI usage page is the truth).

```
uv run python scripts/episode/say_lines.py   <codex_id> <n> [--redo=20,32]  # 1. AUDIO FIRST: every line, IndexTTS2, measured
uv run python scripts/episode/respot.py      <codex_id> <n>   # 2. sub-shot cuts scaled to the measured lines
uv run python scripts/episode/timeline.py    <codex_id> <n>   # 3. placed.json: shot times FROM the audio
uv run python scripts/episode/frames.py      <codex_id> <n>   # 4. one empty plate per setup, at the PLAN's aspect (local, free)
uv run python scripts/episode/cast_bust.py    <codex_id> <who>       # 4a. FREE, LOCAL: the identity BUST of a character nobody has drawn
uv run python scripts/episode/cast_cards.py   <codex_id> --check     # 4b. FREE: gates every cast sheet (studio/cast_agree.py)
uv run python scripts/episode/cast_cards.py   <codex_id> --prompts   # FREE: writes each picture's prompt for the owner to read
uv run python scripts/episode/cast_cards.py   <codex_id> --draw <who> <bust|indoor|outdoor> --approved  # ESCALATE: $0.08 a picture
uv run python scripts/episode/seq_boards.py  <codex_id> <n>   # 5. ONE storyboard sequence per setup (PAID ~$0.20 a sheet)
uv run python scripts/episode/takes_r2v.py   <codex_id> <n>   # 6. every take on H3 ref2va from the board's cells
uv run python scripts/episode/take_dq.py     <codex_id> <n> <take...>          # 7. DQ per take; --retake=1,6 re-renders
uv run python scripts/episode/assemble.py    <codex_id> <n> --engine=r2v  # 8. cut, quiet bed, title card -> master_r2v.mp4
uv run python scripts/episode/qc.py          <codex_id> <n> --engine=r2v  # 9. measure the delivered file
uv run python scripts/episode/runcards.py    <codex_id> <n>   # every input of every shot, both engines, for the owner
uv run python scripts/episode/title.py       <codex_id> <n>   # per episode: SHERLOCK HOLMES / book / EPISODE n card (PAID still)
uv run python scripts/publish/youtube_upload.py  <codex_id> <n> --dry-run   # 10. every gate's verdict, no network
uv run python scripts/publish/youtube_retitle.py <codex_id> --dry-run       # carry the title format back over what is already live
```

## The YouTube title

**The serial and the position come FIRST; the chapter is what gets cut.**
`studio/youtube_publish.series_title` builds it -- never type one into
`episodes/epNN/youtube.json` by hand:

```
Sherlock Holmes: A Study in Scarlet — Ep 04/14 — "What John Rance Had to Tell"
```

A search result, a sidebar and a phone show 40-70 characters. The first five
episodes led with the chapter title, so a viewer saw the one thing that cannot
tell them what this is or where it sits, and the series and the number were the
part truncated away. `04/14` and not `Ep.4` because a viewer deciding whether to
start a serial wants to know how long it is.

YouTube's wall is 100 characters. Thirteen of this book's fourteen chapter names
fit whole; chapter 13 ("A Continuation of the Reminiscences of John Watson,
M.D.") is elided at a word boundary. The series and the number are never what is
cut.

`youtube_retitle.py` carries a format change back over published videos. It
reads each video's LIVE snippet first, because `videos.update` with
`part=snippet` REPLACES the snippet -- sending a title alone returns 200 and
leaves the video with no description, no tags and no category.

## The brick

ONE EVENT split by a title card: a TURN (the lead's choice, 50-75 % in) and a
BUTTON (the world's answer, the last line, never the lead's). AUDIO FIRST:
the plan carries no seconds; every line is rendered and measured; each
shot's length is derived from the lines it carries; nothing is scheduled
afterwards. THE PANEL IS FRAME ZERO: the storyboard cell is the instant
before the motion, and the render begins on it. THE STORYBOARD IS ONE
SEQUENCE PER SETUP: drawn first, in story order, with a route position in
every cell, so no take can contradict its neighbours; takes are windows on
it. NARRATION IS NEVER IN THE TAKE: only dialogue wavs go into a render (an
anchored narration made the face on screen mouth it, 2026-09-11); narration
is laid on the master.

## THE SYNC RULE (owner-approved, non-negotiable)

`shot.seconds = HANDLE + sum(measured line seconds) + BREATH x (lines - 1) +
HANDLE + beat_s + coda_s`, snapped UP to a whole frame at 24 fps.
`studio/episode_spec.py` owns both numbers -- HANDLE = 0.25, BREATH = 0.70 --
and they are named rather than copied here, because this line said 0.50 for
three episodes while section 2 below said 0.70 and the code meant 0.70. Every line
is laid at its shot's start + 0.25 on the master. A dialogue line's wav is
anchored in its take at that same offset, so mouth and sound are one
recording; measured lag 0.000-0.010 s on every engine
(`studio/av_sync.py`). `episode_timeline.misaligned()` refuses anything else.

## 0. RESUMING: read `story.md` first, and say it back

`episodes/epNN/story.md` is the one file that answers "what is this and where
did it get to". Regenerate the facts with
`uv run python scripts/episode/story.py <book> <ep>`; the judgement half is
kept verbatim through every regeneration.

On picking up an episode: read "Where it got to", "Settled" and "Decisions",
say the project back in three sentences (`story_bible.restate`), then carry on
from that stage. DO NOT re-open a settled decision unless the owner overturns
it. On stopping: make sure the facts are fresh and the last line says what
happens next.

Every choice whose reason a stranger could not reconstruct goes in the decision
log with its date and its WHY — `story.py --decide "<what>" --because "<why>"`.
Without the why the next window reads a rule it cannot evaluate, and either
obeys it superstitiously or quietly reverses it. Armstrong footnotes his
scripts only where the reason for a change is not self-evident and notes that
the distribution of the footnotes is itself information: the episodes that shot
smoothly have none. Where our log is thick is where the pipeline is unsettled.

## The story layer: one question, and a value that turns

Two rules, both optional on the contract and REPORTED rather than refused
(`studio/story_layer.py`), because episode 1 was cut before either existed.

**One question per episode, answered inside it.** `Episode.question`, in
Armstrong's form: "Today, can X do Y?". "Today" is what makes it answerable in
one episode; "can" is what makes the answer yes or no. An episode with no such
question has no reason to stop where it stops.

**No shot without a turn.** `Shot.turn` is the value at stake and how it flips,
written "before -> after" ("alone -> seen", "hope -> refused"). McKee: mark the
value at the open and again at the close, and if they read the same the scene
is there to explain something — and explanation belongs inside another shot's
picture. THIS IS THE STORY-SIDE STATEMENT OF OUR OWN WORST RENDER FAULT. A shot
whose value does not turn has nothing to photograph, and it comes back frozen.
We spent three iterations treating the freeze as an engine problem, then as a
pin problem, then as a prompt-vocabulary problem. It is all three, but upstream
of all three it is a shot that was never about anything.

**`Shot.why`** is the only shot string the drawer never reads: the new thing
this shot tells, and the thing it shows about the protagonist (Hicks: a scene
does both, or it is cut). It is reasoning for the people and agents writing the
episode, so it is absent from `SHEET_TEXT` and free to explain an absence,
which every drawn string is forbidden.

## 1. The plan (`plan.json`) — no seconds anywhere

`Line{index, kind: narration|dialogue, speaker, text, shot}` (<= 18 words,
first person, the narrator's cast voice, fresh prose, no book quote over 8
words). `Shot{index, section, setup, size, faces, frame, motion, take,
beat_s <= 1.5, coda_s <= 4, path 0..1, cuts: [SubShot{at_s, size, faces,
frame, motion, path}]}`. `Setup{described, cast, landmark, route}`.
Validators: 120-180 s projected at 3.0 words/s; one hook, one turn (50-75
%), one button (not the lead's, beat >= 1.0 before it); dialogue on a
readable face (close / medium_close); 5-20 % dialogue words; <= 2 lines a
shot; sub-shots >= 2.5 s apart on narration shots only; route positions
never go backwards within a setup; up to SIX setups.

**`Episode.aspect` IS THE DELIVERY SHAPE, AND THE PLAN IS THE ONLY PLACE IT IS
WRITTEN** (`studio/canvas.py`, added 2026-09-12 when the owner asked for 1:1).
`"9:16"` renders 768x1344 and draws 2048x3072 sheets; `"1:1"` renders 768x768
and draws 2048x2048 sheets, which are CHEAPER ($0.13 against $0.20) because a
square cell wastes no pixels. Every stage derives its canvas from this one
field -- the plate, the sheet grid AND ITS OWN WORDING ("equal square 1:1
panels"), the take, the cut, the title card. It used to be a literal
`W, H = 768, 1344` in seven files, which is six chances to disagree in silence:
a square take cropped by a vertical assemble loses a third of every frame and
nothing raises. H3 forces the short edge to 768 and rewrites any other canvas
without saying so, so `canvas.size()` returns the fixed point of H3's own
transform and the tests assert it by calling `h3.check_canvas`.

Rules the owner made after watching:
- **Locations.** No setup holds more than ~25 s of picture (50 s of one
  corridor was rejected). Take the chapter's own places (Criterion Bar, the
  cab, the hospital gate, the corridor under 20 s, the laboratory, the
  street) and add a setup whenever it buys variety: plates are free.
- **A hold is not a shot, and a sub-shot is not the answer.** An insert
  earns 3 seconds. A stretch longer than the take budget becomes TWO SHOTS
  WITH TWO LINES, split while the lines are being written -- never 2-3
  sub-shots inside one take. A sub-shot is a cut the MODEL has to place,
  and it is placed from a stamp: `episode_ref_official.stamp` rounds to a
  whole second (the engine's own grammar), so the model can be told the
  time only to +-12 frames. Measured over all fifteen of episode 3's
  internal pins, 7 of 15 could not land inside the old [-4, +6] window even
  with perfect obedience. Episode 4 was written with one line per shot: 24
  shots, 24 takes, zero internal cuts, every take 4.5-8.0 s, all inside the
  band that passes 16 of 20 (`episode_takes.BUDGET`). Put the cut in the
  EDIT, where it is frame-exact, and ask the latent for one continuous
  picture.
- **Variety.** No two consecutive shots of the same subject at the same
  size; every third shot an insert or a new axis; a face that must read is
  >= A QUARTER of the frame height. A stated head fraction is honoured at a
  median 0.95 at or above a quarter and at 0.00-0.45 below it (54 drawn cells,
  2026-09-12). The old rule said a fifth, which is under the model's own
  threshold. NOTHING ENFORCES THIS -- `identity_gate.READABLE` is a
  post-render floor on a disabled gate, and `cast_agree.CARD_FACE` judges the
  cast card, not a panel.
- **Wardrobe contract, one state, in every frame text**: Watson bare
  sunburnt hands to the wrist on a black stick with a silver knob; Holmes
  bare-headed, green velvet jacket, plaster on the right forefinger. The
  contract is SPLIT in `refs.json`: `physical` is invariant, positive and
  unconditional, and `wardrobe[state]` carries the hat, chosen by the
  setup's own `state` (`Setup.outdoors` -> indoor / outdoor). Each
  character has TWO pictures -- the bare-headed identity BUST
  `char-<who>.png` and the wardrobe CARD `char-<who>_<state>.png` --
  cited inside one `<Subject>`, as MiniMax's guide's own example does.
  `cast_cards.py --check` refuses a sheet whose caption and picture are
  not the same statement -- including R5, a `wardrobe[state]` line with no
  card drawn for it. That is not pedantry: `cast_sheet` falls through to
  the BUST, which is bare-headed by rule, so an undrawn `_outdoor` card
  means the words promise a hat and the picture passed shows none. Either
  draw the card or delete the line.
- **Narration text**: ~22 lines / <= 260 words / ~90 s of speech for a
  chapter; cut caption-lines (the picture shows it) and repeats.

## 2. Lines and the timeline

IndexTTS2 from `cast/<who>/voice/design.wav` (0.80 similarity vs 0.73 for
the Qwen clone); Whisper WER <= 0.20 AND ECAPA >= 0.70; a line whose text
changed is re-rendered; `--redo` gives a rejected line a fresh seed and
KEEPS THE BEST TRY (a redo once went 0.69 -> 0.64); from the third try the
reference is the speaker's own best passed line (>= 0.75), because a short
line cloned from the design clip drifted toward the narrator's voice
(Stamford's button measured 0.55 against Watson, 2026-09-11); a -3 dBFS
limiter after the gain. BREATH between two lines in one shot is 0.70 s (the
wavs carry no silence of their own). `respot.py` scales every `at_s` to
measured/projected, floors the cap so the tail clears the validator under
BOTH the projected and the measured length, and keeps the 2.5 s grid;
`timeline.py` writes `placed.json` with absolute `cuts`.

## 3. The storyboard: one sequence per setup (`seq_boards.py`)

Per setup, every shot and sub-shot is a PANEL, in STORY ORDER (owner
2026-09-11): panel 1 is the first moment of the scene, each panel is later
than the one before, and each END panel sits straight after the panel it
closes. Story order is also order of distance travelled, because the plan
already refuses a route that goes backwards. The sheet is the smallest grid
that holds the panels (3x1 at 1536x1024, 3x2 at 2048x2048, 3x3 at
2048x3072); a spare cell takes an END panel, walks and moving shots first.

The prompt is built in labelled blocks: SHEET, DIFFERENT PICTURES, ORDER,
REFERENCES, LOCATION, GEOMETRY, WARDROBE, BACKGROUND LIFE, PANELS, STYLE,
CONSTRAINTS. GEOMETRY states every relation as a frame edge and an apparent
size and fixes one side of the 180-degree line, because a relational
preposition ("the horse's legs ahead of the wheel") drew a four-wheeler with
the horse abreast of the axle. WARDROBE is its own block with the hat rule
flattened to one state per sheet. BACKGROUND LIFE names counts and
activities in public setups: the owner asked for ordinary people at their own
work by name. EVERY STRING IS AFFIRMATIVE: a negated noun is still that noun,
and our own board drew CRISTERION from a "no signage" clause.

Each panel carries `frame` (the instant BEFORE its action, never the action
finished), `motion`, `camera` (position and lens, no move words), `at_rest`
(what is still), and where it earns one `end` plus `changed` (ONE sentence of
12-17 words naming what moved, the frame edge it moved to, and its apparent
size). The panel prose is written by one author per setup, then read by three
reviewers together (story and continuity, physical and optical sense, the
rules mechanically) and settled by a fixer, because each author sees only its
own location and the faults live between them.

Cells are cut between the gutters FOUND on the sheet
(`episode_board.cell_boxes(grey, cols, rows)`), soft edges above 170
trimmed, and DQ'd: the right number of gutters per axis, no bright flat line
inside a cell, the landmark growing along the route, and NO TWO PANELS ALIKE
at `ALIKE = 0.70` over EVERY pair, a panel and its own END panel included
(measured: the highest legitimate pair on a sheet is 0.584, the copies the
owner caught were 0.82 to 0.95). A failing sheet is redrawn once with a
STRICT opening naming the offending panels.


### ONE SIMPLE CAMERA MOVE BETWEEN PANELS (owner, 2026-09-12)

The difference between two consecutive panels — a panel and its own END panel
included — is ONE SIMPLE CAMERA MOVE plus ONE SMALL LOCAL ACTION. Nothing
else. The moves are: push in, pull back, pan left or right, tilt up or down, a
small track along the subject. The local action is one limb, one object, one
eyelid: a hand slides a baluster's width, a chin comes up, a page travels a
thumb's width.

The mechanism, and why this is a rule and not a taste: a ref2va segment is
given two pictures and asked to get from one to the other. If the two differ by
a REPOSITION of the subject — the same man standing somewhere else, the same
room from a different corner, a prop that has crossed the frame — the model has
no path between them and dissolves one into the other. THAT IS THE MORPHING.
If the two differ by SCALE or by a shifted frame edge, the path is a camera
move, which is exactly what the model is good at, and the segment comes back
smooth.

So `changed` names a change of apparent SIZE or of FRAME EDGE ("the chin has
risen to the top third, a hand taller"), never a change of place. Write the
move's name into the take prose (`motion`), and keep the panel's own `camera`
a standing position with no move words, as it always was: the panel is where
the camera IS, the move is how it gets to the next panel.

This also cheapens the freeze problem from the other side. A big re-stage was
our instinct for "give the segment something to do"; it is the one thing that
guarantees the segment cannot do it.

### THE END PANEL CANNOT BE ASKED FOR IN WORDS (measured 2026-09-12, ep02)

An END panel is "the same shot one moment later". **This drawer cannot draw
that**, and three attempts on the same 9 cells of episode 2 bound the problem
from both sides:

| What the prompt did | Result | Similarity to its own start cell |
|---|---|---|
| Sheet prose: "a DIFFERENT photograph … a viewer can say what happened in between" | **re-staged** to a new camera | 0.072 – 0.406 |
| Attached the start cell as Image 1: "draw Image 1 again, with one thing changed" | **copy** | 0.984 – 0.997 |
| Same, with the reference demoted in prose to "the angle and the SIDE" | **copy** | 0.981 |

With a dominant reference image it copies; without one it re-stages. Both
prompts asked for a RELATION to another picture ("be different", "be the
same"), and a relation is not a thing that can be drawn.

So: **judge, never argue.** `sq.reaches()` measures the drawn pair and only a
cell inside `END_FLOOR..END_CEILING` (0.45–0.80) is a destination.

- A **re-staged** END cell is dropped. Aiming a take at it is aiming it at a
  cut, and `drift` then fails the take for the sheet's fault — that was all
  seven of episode 2's hard drift failures.
- A **copy** END cell is dropped too, and this one is counter-intuitive: it is
  WORSE than no END cell, because it tells the take to end where it began,
  which is the stillness the owner banned outright.
- With **no** END cell the take follows the motion described in words and
  `drift` has no aimed segment to fail. That is the good default.

`seq_boards.py` already does the right thing: `duplicates()` judges END pairs
in the band, one strict retry names the offender, then `drop_end_copies`
deletes it. Cost is bounded at two draws per sheet. Episode 2's sheets predate
that gate, which is why 9 bad cells reached the render.

**Still open, and free**: derive the END cell mechanically by CROPPING its
start cell. A crop IS a push-in — same axis, same angle, closer — and it lands
in the band by construction (a 25 % crop measures 0.66). Only legitimate for a
segment whose motion is a camera push; a segment whose motion is a subject
action needs different content, which a crop cannot give.

### Craft the storyboard inherits from screenwriting

- **A cut between two setups needs a third element, shared or opposed**: a
  gesture, an object, a line, the quality of the light, a sound, an idea
  (greenhouse -> jungle; dawn shadows -> sunset). Our cut-landing gate measures
  that a cut lands on its pin; it cannot tell you the cut MEANS anything. Name
  the linking element in the second panel's `frame`.
- **Action beats talk, and the camera magnifies small things.** The ring that
  rolls under the table, the French toast made badly then well, wringing out a
  stocking. For a 9:16 microdrama this is the best source of visible action
  that is not a walk — and a walk is what we reach for when we have not thought.
- **Concrete or it is invented for you.** Not "a small midwestern town" but
  "Springfield, Ohio"; not "expensive clothes" but "a double-breasted
  chocolate-brown Armani suit". Our prop-size rule is one case of this law;
  apply it to light, ground, weather and crowd too.
- **Don't show a detail off.** The test of a repeat is whether it advances the
  story: a sack of rice appearing three times is necessary; the same flourish
  seven times is nauseating. This is our twin-panel fault said in craft terms.
- **Enter late, leave early — and leave before the conflict resolves.** The
  unfinished feeling is the tension. Shorten shots approaching the turn to earn
  the right to a pause on it.
- **The last word of a line is the core word.** Put the word that opens the
  next reaction at the END of the line, not the middle; it is also where our cut
  lands.
- **The greatest sin is boredom, and repeated beats are how it arrives** — the
  same tactic in different words. Two panels that argue the same thing twice are
  one panel.

## 4. Takes (`takes_r2v.py`) — ENGINE r2v v6

Base `video_minimax_h3_r2v_turbo_ref8`: ref2va fp8 + the DEDICATED lightx2v
Ref2V 8-step 768p LoRA at 1.0, euler/beta 8 steps, sigma shift 12/3 (the
LoRA's own release post; 6/3 is the FL2VA row, and an FL2VA-lineage LoRA on
ref2va ran iteration 1 with camera-scale pumping: never again). A take is a
run of consecutive shots totalling <= `episode_takes.BUDGET` (**8.0 s**, was
12.0) and holding at most `SEGMENT_CAP` (**2**) segments. Measured on episode
3's 24 takes: the 5.9-8.7 s band passes 16 of 20 at a mean of 82.9, both 12.25 s
takes pass 0 of 2 at a mean of 3.75, and 3-segment takes pass 0 of 2 at 23.5.
`takes_r2v.refuse_long_shots` refuses the whole run before the GPU -- so a plan
written to the old 12 s is refused AFTER its sheets are paid for.

References: the cast sheets for EVERY face the take shows, sub-shot faces
included (reading shot-level faces alone left 6 of 19 takes with a face on
screen and no sheet staged), then the plate, then a strip of the take's own
cells in time order with its END frames. Pins: EVERY CELL ONCE, at its first
token start (H3 packs 17 frames into 5 tokens, so token starts are
17k + {0,1,5,9,13}); the next cell's start pin closes the segment. NO END
PINS of any kind: a pin is a soft conditioning row at its time, not a latent
overwrite, so a second pin on a hold says "nothing changes" and the take
freezes (measured over 71 segments: start + same cell 65 % frozen, start +
drawn END cell 59 %, start only 30 %). END cells live in the strip and the
prompt only. Audio: dialogue wavs at their offsets, silence elsewhere,
anchored at frame 0; narration NEVER (an anchored narration made the face on
screen mouth it).

Prompt (`studio/episode_ref_official.py`), MiniMax's own ref2va grammar with
the owner's rules on top, and a LINT that refuses the prompt rather than
sending a bad one:
- EVERY TIME IS A WHOLE SECOND and every shot is a RANGE, `From MM:SS to
  MM:SS`, ranges touching, the first starting at 00:00 and the last ending at
  the take's length, so the text accounts for every second of the video. A
  point stamp gives a segment nothing to sustain, which is one source of the
  freeze. (The guide's own form is an onset, `[Shot 1]` with no stamp and
  later shots `At MM:SS.mmm`; the owner's range form is what ships, with the
  guide's rule named in a comment so the A/B can flip it in one line.)
- AN ACTION IN EVERY SEGMENT, including a one-second reference beat: "if we
  need a ref shot, just showing the other character, put it for a second and
  define an action, so it is not static."
- AFFIRMATIVE ONLY. MiniMax reads no negation; the builder raises on any.
  `calm()` converts the drawer's stillness vocabulary at the boundary, so the
  panel prose stays right for gpt-image and reaches H3 as position.
- The limp is a gait, never a speed: "limps along on his stick at a normal
  walking pace" while Stamford walks at a normal pace. "Slow" applied to a
  person renders as slow motion, and the turbo LoRA already pulls that way.
- **THE CAMERA MOVE GOES IN THE HEAD CLAUSE, BEFORE THE FIRST SEMICOLON.**
  Owner's rule since 2026-09-12; nothing enforced it, and episodes 4 and 5
  dropped it on 32 of 49 shots. `M2` in `episode_spec.motion_faults` now
  refuses it, in `seq_boards` and `takes_r2v`, before a cent is spent.

  MEASURED over the 92 judged takes of episodes 2–5:

  | episode | head names a camera move | stillness points lost |
  |---------|--------------------------|-----------------------|
  | ep02    | 25/25 (100 %)            | 12.2 over 19 takes    |
  | ep03    | 25/25 (100 %)            | 10.8 over 24 takes    |
  | ep04    | 12/24  (50 %)            | 59.1                  |
  | ep05    |  7/25  (28 %)            | 106.8                 |

  All ten of the stillest takes in episodes 4–5 have a head with no camera
  move; not one of the nineteen takes whose head names one was ever penalised
  (Fisher one-sided, p = 0.0041). Episodes 2 and 3 scored *badly* — means of
  59.6 and 76.6 — but lost it to landing, drift and lip-sync. Their stillness
  loss is ~zero. The convention broke, and all the loss moved to stillness.

  **Why the camera and not the subject.** The camera move is the only element
  of the prompt that is not a property of the reference picture. The pose, the
  wardrobe, the room — H3 can satisfy all of them by rendering the pinned cell
  and holding. A move is the one instruction it cannot satisfy by standing
  still.

  Write it with a measured amount and the span:

      The camera pushes in on the sofa across the whole shot, travelling two
      long strides; <action>; <action>

  A move written AFTER a semicolon is deleted by the builder and never reaches
  the model (ep04 T21). The move in the prose must be the SAME move the cells
  differ by.

- **EVERY MOVING THING HAS A MOVER, AND THE CAMERA IS THE PREFERRED ONE**
  (owner, 2026-09-14: "remove unnatural movement like paper turning on its own
  on table ... and violin getting a red light ... keep the movement simple").
  `M9` refuses a clause whose subject is a thing at rest on a surface — paper,
  ring, coin, a patch of light — with no hand, no finger and no camera in it.

  This is the same fault as the missing camera move, seen from the other end:
  with nothing else moving, the motion got handed to the props. Episode 5's
  shot 6 (the paper sliding itself across the cloth) and shot 24 (a red light
  crossing the violin) are the two the owner picked out by eye, and they are
  the only two the gate finds in that episode.

  Fog, flame, coal, smoke, washing in a draught and a turning cab wheel are
  NOT this fault — the place supplies their cause, and those shots scored 100.
- DESCRIPTIVE: 150-240 words a shot block, at least `min(350, 150 x shots)`
  a take. Ours measured 114 a block before this and 179 after.
- The plate is a DEFINITION, `partially_preserved`, never "appears in" a
  shot: declared as a shot, the model showed the empty room as one.
- One `<Picture N>` per pinned cell; the voice range is clipped to its own
  segment (a span crossing a cut made the model wait for the span's end
  instead of cutting on the pin); `(Sx)` counts dialogue voices only.
`ref_image_size: match`. Takes render at ~3.3 s/frame.


### DRY-BUILD EVERY TAKE PROMPT BEFORE YOU COMMIT THE GPU (2026-09-12)

`takes_r2v.cards(book, episode, number)` builds every prompt and runs the LINT
without touching ComfyUI. Call it FIRST, always:

```python
cards = t.cards(book, episode, number)      # raises on the first bad prompt
print(f"{len(cards)} prompts, {sum(c['frames'] for c in cards)} frames")
```

The lint refuses the whole run on the FIRST bad prompt, so a render launched
without this dies minutes in, and the next fault is only revealed after the next
launch. Episode 2 hit FIVE in a row this way -- L16, L9 (twice, different
causes), L2 and L14 -- and each discovery cost a fresh submit. One dry-build
loop found all of them in minutes.

What they were, because they are the classes that recur:

- **L16 DIALOGUE TAIL.** `beat_sentences` reads `clauses_of(motion)[1][1:]` --
  the camera sentence consumes the FIRST follow-on clause -- so a dialogue shot
  needs **two clauses after the head** (`head; tail; tail.`) for one to reach
  the stamped beat at the line's end. One clause emits no tail beat at all, and
  6 of 8 dialogue segments froze at the second their line ended.
- **L2 STILLNESS on the words you add.** `still, stays, remains, motionless,
  frozen, pauses, waits, unchanged, unmoving, holds, held`. A tail clause is
  exactly where "he holds the salute" wants to be written, and it is banned.
  It also catches a CONTRACT: `refs.json` `physical` is repeated verbatim into
  every prompt, so "shoulders held back" in a character's own description
  refuses every take that character appears in.
- **A MOUTH NOTE is silently dropped.** `clauses_of` filters a clause that only
  says a mouth is closed, so "he waits with his lips closed" leaves you a clause
  short and L16 fires anyway.
- **L9 NO LIMP fires on somebody else's gait.** The lint asks only whether
  Watson's tag and a gait word share a block; it cannot attribute the verb. A
  hansom "at a trot", a woman who "walks the pavement", and the NOUN "steps"
  (stair treads) each refused a take where nobody was walking. Reword the
  background life -- the cabs roll, the woman carries her basket, the stair has
  treads -- rather than loosening the lint or writing a limp into a man who is
  standing at a window.
- **L14 LENGTH, 150-240 words a block.** Every clause you add to fix the rules
  above pushes toward the cap; budget for it.

### THE PLATE IS NOT AN UNCONDITIONAL REFERENCE (measured 2026-09-12, ep02)

Episode 2's top fault by count: **13 of its 14 foreign frames were the take's
OWN attached plate**, matched at 0.988–0.998. T03 opens on Holmes's face and by
1.5 s the frame IS `plate_sofa.png`, chairs and violin and all.

Every one came from a close or insert segment with **no wider cell anywhere in
the take** (Fisher exact p = 0.0072; 0 of 64 wider frame samples). The
mechanism: a take of nothing but tight cells cannot place a room, so the plate
stops being a definition and becomes the only whole picture the model can fall
back on.

So the plate is staged only when `sq.places_the_plate(sizes)` — the take shows
at least one `medium`, `full` or `wide` cell. On episode 2 that dropped it from
12 of 19 takes.

**Dropping it from the reference LIST alone fails loudly, and this is the trap.**
`picture_numbers` fixed the plate at slot `n_faces + 1` and every later picture
counted from it, so the prompt cited a picture the graph never staged —
`L11 PICTURES: 5 pictures defined against 4 staged references`. The numbering
has to close the gap too, and `has_plate` threads through **all five**
emitters: `picture_numbers`, `subjects`, `retention`, `summary` and
`prompt_facts`. Miss `summary` and it cites `<Subject 3>` with no such subject;
miss `prompt_facts` and the two plate lints fire on a plate that isn't there.

### THE HALF AFTER `as` IS NOT A NEW SENTENCE (2026-09-12)

`camera_sentence` joins the camera half to the motion half, and the motion half
arrives from the plan as its own sentence, capital and all:
`…pushes in a hand's breadth as The right forefinger lifts`. **21 of these
across 19 take prompts.** A capital mid-sentence reads to the model as a second
sentence — the same class of fault as the malformed camera clause.

`lower_lead()` lowercases a closed list of words that can only ever open a
subordinate clause (`the a an his her their its one both two three`). It does
NOT touch names: lowercasing `Watson` would cost more than the fault it fixes.
Careful — `"his".rstrip("'s")` is a CHARACTER SET and eats the `s`; use
`removesuffix`.

### ONE GPU, ONE STAGE AT A TIME (owner, 2026-09-12)

Every take of a run is submitted to ComfyUI BEFORE any of them is collected, so
they execute consecutively and the MiniMax weights load once. Then, and only
then, the whole DQ. Then the whole retake batch. Then DQ again. Never a DQ
while takes are in flight: the lip-sync gate reaches Whisper THROUGH ComfyUI,
and every Whisper job evicts the video weights.

A STAGE THAT LOSES WORK STOPS; IT DOES NOT FALL THROUGH. One interrupted take
killed the collector, three more rendered with nobody waiting for them, and the
chain walked on to DQ and then to assemble on an incomplete set. Collect every
take you can, name the ones lost, exit non-zero. The same morning taught the
smaller half of it: a displaced attempt's name is read off disk, never from a
`tries` counter, because a re-run does not know what earlier retakes left there.

MEASURED the morning this rule was written: back to back, takes ran 407, 502,
583 s; with another production's jobs landing between them the same graph took
742 and 998 s. Memory is the other half of it: with the weights of two
productions and Whisper resident, the machine had 6.6 GB of 63.7 free and 1.6 GB
of 24 VRAM, and was paging -- which reads as heavy disk, not as a slow GPU. A
restart put it back to 46.8 and 20.8. Submitting one take and waiting for it leaves a gap after every
take, and the gap is where another job gets in — 19 invitations per episode.
Two of those interleavings were mine, from re-running the DQ to check a gate
while the renders were running.

## THE THIRD REFERENCE: OBJECTS (owner, 2026-09-12)

A book binds its people and its places and used to bind nothing else.
`Setup.props` only ever named ANOTHER SETUP whose plate got reused, so an object
that is not also a location could be described and never shown.

    character   refs/characters/char-<id>.png   build_refs.py / cast_bust.py   free, Krea2
    location    refs/locations/loc-<id>.png     build_refs.py                  free, Krea2
    PROP        refs/props/prop-<id>.png        prop_refs.py                   free, Krea2

    uv run python scripts/episode/prop_refs.py <codex_id> --bind <records.json>  # FREE
    uv run python scripts/episode/prop_refs.py <codex_id> --check                # FREE
    uv run python scripts/episode/prop_refs.py <codex_id> --draw-all             # FREE, LOCAL

MEASURED on episode 2, nine props drawn from WORDS ALONE over six independent
sheets: violin 0.36x (a child's fiddle under a six-foot jaw -- and correct at
63 cm in panel 1 of the SAME sheet), shawl 3.0x, a fingerprint asked "a
thumbnail wide" drawn a palm across, stick shaft 1.95x, pencil 2.6x, coffee pot
0.55x and drifting 1.5x inside one sheet, and in one panel the poker was drawn
AS the walking stick. The controlled comparison is the blue envelope, the one
prop with a picture -- and only by accident, because the commissionaire's bust
happens to show it in his hand against his chest. It came back at 1.25x over
ten panels and three sheets.

THE BRICK: gpt-image copies APPEARANCE and never ABSOLUTE SIZE, and the only
thing in a photograph that carries absolute size is A HUMAN BODY. So:

- **The reference picture always has a hand in it.** Held in a hand where the
  object has an owner, standing beside an open hand where it does not. An
  object photographed alone on a table teaches appearance and nothing else.
- **The contract states THREE measures** (`studio/prop_refs.Prop`): `overall`
  against the body, `cross_section`, and one sized `detail`. The validator
  REFUSES a measure in centimetres -- a model has no ruler -- and refuses a
  negation or a pace word like every other drawn string.
- **Extraction is judgement, the contract is code.** An agent reads the chapter
  and authors the records, the way `analysis/characters/` is authored; `--bind`
  validates them into `refs.json` as `kind: "prop"` rows and refuses a prop
  missing a measure BEFORE anything is drawn.
- **Slots are the constraint at take time.** `ro.MAX_PICTURES` is 9 and the ep02
  takes already use 3-7, so a take attaches its HERO prop only. Sheets have
  room for more.

## What the five prompt auditors measured (2026-09-12)

Read `library/<book>/episodes/epNN/report_final.html` for the full list. The
findings that change how we write, not just what we fixed:

- **OBEDIENCE, per instruction type, over 54 drawn cells.** people count 0.96;
  the instant before 0.93; named face frontal 0.93; frame-edge assertion 0.83;
  wordless surfaces 0.83; shot size 0.80; camera height 0.76; END differs by its
  one named change 0.58; END keeps the same camera 0.33; **landmark size ladder
  0.00**. The ladder is DEAD PROMPT -- zero for seven, failing both too big and
  too small -- while the same fact stated as a frame edge lands. Write sizes as
  frame edges.
- **A stated head fraction is honoured only at or above A QUARTER** (delivered
  vs stated: median 0.95 above that line, 0.00-0.45 below it). The old rule
  said "a fifth", which is under the model's own threshold.
- **Where the size word and the head fraction disagree, the model follows the
  FRACTION.** Size misses run 10-to-1 WIDER, and every panel drawn wider than
  its size word also invented furniture the prompt never named.
- **The prompt is not too long.** OpenAI's cap is 32,000 characters and ours run
  16-22 kB; the block order already matches their documented order. The waste is
  inside it: 19 % of every prompt is an "instant BEFORE" clause re-describing
  the picture the same block just described.
- **`quality="high"` is the MIDDLE rung on gpt-image-2.5**, not the top: `xhigh`
  and `max` sit above it. `input_fidelity` is a dead end -- the docs say omit
  it, GPT Image 2 and later always process inputs at high fidelity.
- **Keep the 3x3 sheet, raise its canvas.** One sheet is $0.0144 a cell against
  $0.053 for singles, and the resolution argument for singles collapses: a
  682 px cell upscales 1.13x to the 768 canvas while a 1024 px single would be
  DOWNSCALED. 2880x2880 is the documented pixel cap and gives 960 px cells with
  no upscale.
- **Four setups of one room drawn four times are not one room.** The room-plan
  clause is BYTE-IDENTICAL (419 characters) in all five sitting-room prompts and
  still produced two different sofas and three door colours -- and the drift is
  in the PLATES, each sheet having copied its own plate faithfully. Words cannot
  substitute for a picture. No gate in `studio/` is cross-sheet.

## 5. The gate ladder: nothing is spent before it is checked

Each rung is free and guards the rung after it.

**G1 PLAN**, before anything: an action in every segment, no negation, no
stillness word, no "slow" on a person, the wardrobe contract named wherever a
hand, hat or Holmes's jacket shows, props named in `motion` present in
`frame`, sub-shot faces named, no location over ~25 s, no still segment over
2.5 s after an internal cut, ranges covering the take. Guards the sheets and
the whole render round.

**G2 SHEET PROMPT**, before the paid draw: every panel a different picture,
each the instant before its action, END panels naming a changed state,
geometry as edges and sizes, crowd life in public setups, panel count
matching the grid. Guards ~$0.20 a sheet.

**G3 CELL**, after the draw and before any GPU: gutters, white lines, the
landmark growing along the route, and `ALIKE = 0.70` over EVERY pair
including a panel and its own END panel. A failing sheet is one STRICT
redraw. Guards hours of render.

**G4 TAKE** (`take_dq.py`, `studio/motion_gate.py`, `cut_landing.py`,
`take_verdict.py`, `identity_gate.py`): frozen-at-start over 1.0 s is a hard
fail (the owner's "some takes start with a static image"); frozen share per
segment kind; no foreign picture; the cut landing within [-4,+6] frames of
its pin with no ping-pong; drift; lip sync and words heard on dialogue takes
only (a narration take carries silence by design); identity against the cast
sheet. One score, `--attempts` keeps the best automatically, budget 2
retakes, and a reseed is never the answer to a freeze.

**G5 MASTER** (`studio/edit_gate.py`, `qc.py`): every segment of the master
is its take frame for frame, no duplicated frame across a cut, cut positions
within half a frame, no pts hole, then -15.5..-12.5 LUFS, TP <= -1.0, every
line heard.

`assemble.py`: one segment per take-run, gutter guard, bed 11 dB down with
-40 LUFS room tone, duck at least 4 dB with 0.15 s attack / 0.25 s pre-delay
/ 1.0 s release, a 2.76 s fade over bed AND tone at the placed end, lines at
their placed `at`, title card at -20 LUFS with fades, 0.25 s of black after
it, final gain + limiter.

## 5b. THE MUSIC BED — every episode has one

**This stage is easy to miss, and it was missed**: the owner asked "are we not
doing background music?" on 2026-09-13, after two episodes had shipped with a
bed under every second of them. It was documented in half a line inside a
sentence about `assemble.py`, so it read as absent. It is not.

**Where it lives.** NEVER in the take. The ref2v prompt ends
`non_diegetic_music: N/A` on purpose — H3 generates the take's diegetic sound
only, and music in a take cannot be ducked, cut or levelled afterwards. The bed
is laid on the MASTER in `assemble.py`, exactly like narration.

**What it is**, measured and tuned across three iterations:

| knob | value | why |
|---|---|---|
| model | **ACE-Step 1.5** (`audio_acestep15_music`), `BED_ENGINE_DEFAULT = "acestep"` | it is the only engine with a real instrumental control. `--bed=yue2` stays reachable |
| ask | **five per-span tones**, `studio/episode_bed.py` | `plain / light / uneasy / grave / thrilling`, each with its own `tags` (acestep), `style` prose (yue2), `bpm`, `key` and `lufs` |
| spans | `Episode.beds`, authored | `[{"from_shot": 0, "tone": "plain"}, ...]`; empty means one `plain` span end to end, which is what episodes 1-5 shipped |
| length | per tone, its longest span + `CROSSFADE_S` | ONE generation per DISTINCT tone, not per span: two rolls of one tone are two different performances |
| level | **per tone**, -31.0 to -27.5 LUFS | set BEFORE composing; `quiet_bed(..., normalise=False)` on that path, because normalising the composite averages five deliberate levels back into one |
| dead | `DEAD_UNDER = 12.0` dB under target, `BED_ROLLS = 3` | episode 6's `grave` came back at -58.0 against -29.0. A warning is not a fix: it re-rolls, keeps each dead roll as `bed_<tone>.emptyN.wav`, and refuses after three |
| sings | `studio/bed_gate.py` | a bed is transcribed and REFUSED if it sings |
| floor | room tone at -40 LUFS | under the bed, so a gap is never digital silence |
| duck | >= 4 dB, 0.15 s attack, 0.25 s pre-delay, 1.0 s release | 10 dB in 20 ms pumped audibly on every line |
| seams | 2.0 s equal-power crossfade | equal-power, not linear: two uncorrelated beds summed with linear fades dip ~3 dB in the middle of the join |
| out | 2.76 s half-sine over bed AND tone | the bed's last hit at 135.0 s fell inside the old 1.5 s fade |

**WHY PER-SPAN.** OWNER 2026-09-14, after episode 5: *"make sure audio is not
too loud the BG ... different types based on the context of background thrilling
.. normal"*. Measured on the shipped ep05 master: speech -13.2 LUFS, the bed in
an un-ducked gap -28.0, the bed inside the voice band -34.9. It was never
objectively loud. What made it READ as loud is that one solo violin in D minor
played for 160 seconds under a breakfast, a joke, a flashback and a murder, and
a constant is a thing the ear gives up filtering. Episode 6's quiet floor
measures -45.0 dB against episode 5's -35.1, with the loud level unchanged.

The tone is AUTHORED, never derived from `section`: "friction" covers both a
comic invasion of six street boys and a man's hand closing on a woman's wrist.

**THE INSTRUMENTAL MARKER IS A DIFFERENT WORD IN EACH MODEL, and getting it
wrong does not fail — it SINGS.** ACE-Step takes **`[inst]`**, a trained control
string in its lyric encoder. **YuE2 takes the EMPTY STRING** — it has no
instrumental token in its vocabulary at all, `encode_ordinary` makes any marker
literal text, and CFG is off, so there is nothing to steer with. `(instrumental)`
belongs to MiniMax Music 3 and to the TRAILER; it was written into this pipeline
as though it had been measured on YuE2, it had not, and episode 3's bed then
sang invented English verse for 101 of its 157.8 seconds (64 %) and reached
YouTube's queue. `BED_INSTRUMENTAL` holds both markers and is tested.

## 6. Writing with agents: authors, reviewers, one fixer

The panel prose and the take prose are judgement work, so agents write them;
the checks are exact, so code runs them. Never the other way round.

WHAT MAY BE SPLIT IS PANEL TEXT, NOTHING ELSE. The chapter, the episode's
question, the shot list and the story stay in one head: they are one thing, and
an agent given a piece of them returns something that contradicts the rest.
Parallel work is for (a) panel prose inside ONE setup, (b) read-only review,
each agent running one checklist over everything, and (c) bulk retrieval that
brings back a conclusion rather than a pile of text.

ONE AUTHOR PER SETUP, in parallel, each reading its peers' patches so the
voice matches and writing only a patch for its own setup, which is merged
centrally. Then THREE REVIEWERS reading all setups together, one for story
and continuity, one for physical and optical sense, one for the rules
mechanically. Then ONE FIXER. Then the lints again, and only then the draw.

This is not ceremony. On the pass that built this section the authors caught
the plaster on the wrong hand and a panel contradicting its own staging; the
reviewers caught the time of day running backwards across four locations
against a chapter set before lunch, a wardrobe block ordering Watson drawn
bareheaded on every sheet, and a cab panel that is geometrically impossible
(a 9:16 frame whose height holds a 9 ft 6 in hansom is 16 ft wide, the
length of the rig, so it cannot stand at one edge and cross to the other).
Where two reviewers disagree, the third supplies the mechanism.

## 7. The iteration loop

After each master: five reviewers in parallel (picture and continuity,
prompts vs the official grammar, storyboards and character consistency,
audio/sync/mix, story/edit/plan), each returning <= 8 ranked changes with
evidence and a measurement; the owner's own notes outrank them. Apply,
re-run the chain unattended, report the path, QC, DQ, wall time and ledger.
Log in `episodes/epNN/iterations.log`, and keep every issue with its
evidence and status in `episodes/epNN/findings.json`, which `runcards.py`
renders at the top of `report_final.html`.

NO AGENT TOUCHES THE GPU WHILE A RENDER RUNS: a vision model loaded during
one turned an 8-minute take into 37.

## The contract: every prop carries a size

A wardrobe and props contract is the list of things the drawer is forbidden to
invent, and anything it leaves out is invented panel by panel. So each prop
states what it IS, how BIG it is against the body, and WHERE it sits: "a black
walking stick that stands hip high and reaches a little over half his own
height, its shaft as thick as one finger and its ferrule on the ground beside
his boot". An adjective ("a walking stick") is not a size, and 23 panels each
guessed a different one, which is how a cane came back the size of a lamp post
(owner, 2026-09-11).

Two traps in the code made that invisible and both are now shut, but check them
in any new book:
- `trailer_refs.visual_description` trims to 220 characters and trims SILENTLY.
  A contract cannot be trimmed, so the episode reads `contract_description`,
  which has no limit; `dropped_by_limit` says when the two disagree.
- A sentence reaches the drawer only if it sounds photographable, and the word
  list was faces and clothes alone. A sentence about a PROP failed it, so every
  fact about the stick was discarded whatever the limit. Props are in the list
  now.

## Known open items


- Word-level spotting from Whisper timestamps (`respot.py` scales by line,
  not by phrase yet).
- Wardrobe and face-count on a cell need a local vision model; identity has
  one behind a flag (`facenet-pytorch`), wardrobe is still the eye.
- There is no free pixel test for "is this cell in the right place": 17 of 40
  cells measure closer to a foreign plate than their own, so a panel drawn in
  the wrong location is caught only by reading the text.
- Room tone per setup is one brown-noise floor; no footsteps.

## Entry paths — where a session actually starts

| What you have | Start at | Watch for |
|---|---|---|
| A chapter of a book already set up (cast voices, refs, plates) | Stage 1, lines | The normal path |
| A book with no cast voices yet | Voice design first; the episode cannot begin | Audio first is not negotiable |
| A chapter that brings a character with no sheet | Author his row in `refs.json`, then `cast_bust.py <who>` (free, local), then `cast_cards.py --draw <who> <state> --approved` | The BUST is free on your own GPU and only the wardrobe CARD costs $0.08. NEVER `build_refs.py` for this: it draws the whole cast and then REWRITES refs.json from what it drew, deleting every hand-authored wardrobe, sheet and cards block. `faces_of` stages the new sheet everywhere the words name him |
| A chapter that brings a character who HAS a bust but no card | Author `wardrobe`, `sheet` and `cards` on his row, then `cast_cards.py --draw <who> indoor --approved` | **A BUST IS NOT A CARD.** Gregson and Lestrade each had a bust and nothing else, so `cast_sheet` fell through to it: a landscape head-and-shoulders wearing a hat, with no body. No body is no scale — the proportion fault of episode 2 — and the hat is baked into every indoor shot. The card is an `images.edit` OF the bust, so **the bust's face and SKIN TONE survive it**: Lestrade's contract says Doyle's "sallow" and his card came back fair, because the template says "the same skin tone". Fix the bust first, or accept and record the deviation |
| A chapter in a location never drawn | One plate, then the sheet for that setup only | `--setup=<name>` keeps the other sheets' money in your pocket |
| An episode half rendered | `takes_r2v.py` with no `--retake`: it renders only what has no record | Check no other run is alive FIRST, by command line, not by `ps -W` |
| A cut that needs re-cutting, no new pictures | `assemble.py` then `qc.py` | Costs nothing; `master_iterN` never overwrites |
| One bad cell in a good sheet | `redraw_panel.py <book> <ep> S14.1 --approved` | $0.08, leaves its neighbours alone |
| A finished episode to review | `runcards.py`, then read `report_final.html` | Every input and output per take, with the issues |

## When a failure sends you back

A fault is almost never owned by the stage that reveals it.

| What you see | Whose fault it is | Go back to |
|---|---|---|
| Take frozen, or still then moving | The panel, or the shot that turns no value | Stage 0 (the turn) and stage 3 (the cell) |
| Subject dissolves or smears between two cells | Two panels that differ by a REPOSITION, not by a camera move | Stage 3, `changed`: make it a size or a frame edge |
| Walk reads as slow motion | The motion text | Stage 1, the plan's words |
| Vehicle moves but goes nowhere | The shot is locked off and the world is still | Stage 1 |
| Face wrong, moustache missing | Whoever the scene's words name had no sheet staged | Stage 1's text, not the cast sheet |
| Prop the wrong size | The contract did not size it | `refs.json`, before any drawing |
| Two panels the same picture | An END whose change cannot read at that size | Stage 5, the sheet prompt |
| A shot cuts to a picture nobody asked for | A reference the model could not place | Stage 7, the take's reference list |
| A line lands late | Seconds written into the plan instead of measured | Stage 2, and never the plan |
| Renders taking half again as long | Something else is on the GPU between takes | The staging rule above |

## What earns its own skill, and how a new one is added

A medium gets its own skill only if it makes us WRITE DIFFERENTLY — different
structure, different format, different language rules. Subject matter (a
detective chapter, a romance chapter), a book, or a visual style do not
qualify; those are entries in a table inside an existing skill. By that rule
`episode`, `trailer` and `shorts-*` are three skills because a trailer is cut
to music, a short is a single scene, and an episode is cut to a measured voice;
a second book is not a fourth.

When a new medium does earn one: ONE new skill, ONE boundary table inside it
saying what transfers from here and what does not, and ONE row in the entry
table above. The existing skills are not edited. A medium that edits the
general layer to fit itself has taken everything else hostage.

## The owner's spec outranks everything in this file

If the owner or the platform gives a length, an aspect, a format or a count,
that is the spec; every convention here is a default for the blanks they left.
Never ship something off-spec in order to fill in a field this skill asks for.
Say which of our defaults you dropped, and why.
