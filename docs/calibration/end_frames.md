# END-FRAMES — which segments need a drawn END cell, what it shows, and whether the renders reach it

Task force member END-FRAMES, iteration 4 evidence, for the final iteration 5.
Prototypes and evidence: `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\end_frames\`
(`scan.py` / `scan_iter4.json`, `traj.py` / `traj_iter4.json` + `traj_iter4_T??_Q??_?.png` strips, `calib_cells.py`,
`end_gate.py` = the gates, `pairs_start_end.png` = the five START/END pairs, `cab_iter3_vs_iter4.png`).

## DIAGNOSIS

### 1. Five END cells were drawn; four are the same picture as their start cell

`frames\Q02_0E Q03_0E Q07_0E Q08_0E Q12_0E` (sheet prompts `frames\seq_*_0.prompt.txt`). `frame_match.similarity`
(48x84 grey cosine) START vs END, and what the eye sees in `end_frames\pairs_start_end.png`:

| END cell | sim(START, END) | what changed | verdict |
|---|---|---|---|
| Q02_0E | 0.951 | nothing: Stamford's glass at his mouth in both, Watson's eyes down in both | copy |
| Q07_0E | 0.890 | framing a hair wider; Watson still on the cab step, Stamford still on the pavement | copy |
| Q08_0E | 0.821 | Watson one step higher, hand still at the brim, BOWLER STILL ON | copy (the named change, hat off, is absent) |
| Q12_0E | 0.620 | same pose (Holmes upright, tube raised) — the score is redraw noise in the bottles | same state |
| Q03_0E | 0.339 | the LOCATION changed (Piccadilly street -> the hospital gate); the cab is still centred, same pose | different for the wrong reason |

Calibration of the metric (`calib_cells.py`): two genuinely different pictures never score above 0.58
(99 pairs of different shots in one setup: max 0.58, p90 0.38; 18 pairs of the same shot's sub-cells: max 0.47;
30 same-text panels redrawn between iterations 3 and 4: max 0.53). Copies score 0.82-0.95. Q12_0E (0.62) is the
one same-state cell that sits in the gap.

Why they are copies: the packer's panel text (`studio\episode_seq_board.py` `end_panels`) asks for
"the last frame of panel N, identical place, light and framing: <motion text> has just finished." — it describes the
start panel and a verb phrase, never the end STATE as a picture. gpt-image draws what is described: the panel again.
Two start cells were also drawn past their own state (Q02_0 glass already raised; Q12_0 Holmes already sprung up),
so there was nothing left for the segment to do.

Which cells got an END frame was an accident of the grid: `end_panels` fills only the SPARE cells of the smallest
grid, picking by `size in GEO_SIZES` first. criterion 5 segments -> 1 spare, cab 8 -> 1, gateway 7 -> 2, lab 8 -> 1,
corridor 6 -> 0, bench 6 -> 0. So the corridor walks (Q09_0, Q11_0, Q11_1), the blood test (Q17_1, Q17_2) and the walk
to the door (Q19_1) — the segments that most need a destination — got none, while Q02_0 (a static two-shot) got one
because "medium" counts as geography.

### 2. What an END pin does to the render (measured on `shots_r2v\T??.mp4`, `traj_iter4.json`)

The pinned frame is a near-copy of the cell by construction: full-res mean |diff| frame-at-pin vs cell = 4.7 (VAE
round trip) while neighbouring frames differ from the pin frame by < 1 (T02@93, T12@65, T03@85, T17@209). So
"the render reaches the END cell at the pin" is always true and is not a gate. What matters is WHEN it arrives and
what it does until then:

| segment | END pin | sim(S,E) | arrival (first frame >= 0.90 to END) | frozen before the pin | strip |
|---|---|---|---|---|---|
| T02 Q02_0 f0-93 | Q02_0E | 0.95 | frame 11 (12 % of the segment) | 3.88 s | `traj_iter4_T02_Q02_0.png` |
| T07 Q07_0 f0-45 | Q07_0E | 0.89 | frame 13 (29 %) | 1.33 s | `traj_iter4_T07_Q07_0.png` |
| T07 Q08_0 f49-117 | Q08_0E | 0.82 | 44 (65 %) | 1.00 s | `traj_iter4_T07_Q08_0.png` (Watson's back frozen on the steps for 2.8 s) |
| T12 Q12_0 f0-65 | Q12_0E | 0.62 | 12 (18 %) | 1.54 s | `traj_iter4_T12_Q12_0.png` (silhouette frozen 2.7 s; "springs up" never happens) |
| T03 Q03_0 f0-85 | Q03_0E | 0.34 | 78 (92 %) | 0.00 s | `cab_iter3_vs_iter4.png` row 2 |

Rule the model follows: it moves to the END picture as fast as the distance allows, then holds it until the pin.
A near-copy END (distance ~0) = a freeze for the whole segment. A far END (Q03_0E) = a glide over the whole
segment — but the glide is whatever separates the two pictures, and for Q03_0E that was the background (the street
dissolves into the gate under a centred cab, energy 13.8 falling to 3.5, the treadmill the owner saw). Iteration 3's
T03 with no pin (`cab_iter3_vs_iter4.png` row 1) is the pure treadmill: the cab centred in every frame, the wheels
turning. Neither version has an END picture with the cab anywhere else in the frame, so the cab never travels.

Hold pins (the start cell pinned again, 24 segments): frozen before the pin 0.9-6.0 s in 22 of 24 (T17 Q17_2 6.0 s,
T12 Q12_1 5.7 s, T17 Q17_0 4.9 s); only the tracking walks T09 and T20 Q21_1 keep moving (they move because the
prompt tracks, and T09's walk is then pulled back to its own start frame — frame 72 ~ frame 0 at sim 1.00).

Side finding for the cuts member: three mid-take START pins were not honoured — Q01_1@77 (arrives at 114, 37 frames
late), Q09_1@77 (126, 49 late), Q13_1@69 (120, 51 late); the other 16 land on their frame. All three follow a hold
pin 4 frames earlier; T04/T05/T06/T10/T11/T12/T14 have the same structure and comply, so it is not deterministic.
(`end_frames\` run log, "mid-take start pins".)

### 3. The take reference strip and prompt make END panels into extra shots

`ref_take_02.png` = [Q02_0][Q02_1][Q02_0E], `ref_take_07.png` = [Q07_0][Q08_0][Q08_1][Q07_0E][Q08_0E], and the prompt
says "the panel after them shows how [Shot 1] ends" (`studio\episode_ref_official.py` `ends_sentence`). Review 7
already measured the result: T02 and T07 cut BACK to the wide after their close (the strip read as shot order).
An END panel must sit next to its own start panel in the strip, and the sentence must say it is not a shot.

## THE CHECK

Two gates, calibrated on the cells and takes on disk (`end_frames\end_gate.py`, run output in the task log).
A third idea — "is the END cell still in its own location" by similarity to the setup plates — was tried and
does not work (28 of 40 START cells fail it; a close-up does not resemble its plate), so location stays a
human contact-sheet check plus the "Unchanged:" clause in the prompt.

### Gate A — END-cell distinctness (sheet DQ, `seq_boards.py` after the cells are cut)

```python
COPY = 0.60   # frame_match similarity; different pictures max 0.58 on disk, copies 0.82-0.95, same-state redraw 0.62

def end_cell_distinct(start_cell: Path, end_cell: Path) -> tuple[bool, float]:
    """The END cell is a different picture from its start cell: similarity <= COPY."""
    s = fm.similarity(fm.load(start_cell), fm.load(end_cell))
    return s <= COPY, round(s, 3)
```
Verdicts on disk: Q02_0E 0.951 FAIL, Q07_0E 0.890 FAIL, Q08_0E 0.821 FAIL, Q12_0E 0.620 FAIL, Q03_0E 0.339 pass —
all five agree with the eye. A failing END cell sends the sheet to the STRICT redraw (already in `draw_setup`) with
the sentence "STRICT: every END panel must differ from its start panel at a glance: <the named change>"; a second
failure drops the END cell (the segment renders without an end pin) and is reported, never silently kept.
Margin note: the same-framing-subject-moved case an END frame is for (cab at the right edge, Watson at the door)
lands around 0.2-0.5 on this metric (T03 cab frame 0 vs frame 40, cab entered -> centred: 0.17), so 0.60 does not
reject good END frames; warn-band 0.50-0.60 goes to the contact sheet.

Tests (synthetic, no repo assets):
```python
def test_an_end_cell_that_repeats_its_start_fails():        # same image -> sim 1.0 -> (False, 1.0)
def test_an_end_cell_with_the_subject_moved_passes():       # dark 30%-wide block at x=10% vs x=65% on the same gradient -> sim < 0.6
def test_the_known_iteration_4_scores_are_reproduced():     # if the ep01 frames exist: Q02_0E 0.951 fails, Q03_0E 0.339 passes (skip otherwise)
```

### Gate B — render reaches the END late, not early-and-frozen (take DQ, per END-pinned segment)

```python
ARRIVE, FROZEN, FROZEN_MAX_S, FPS = 0.90, 1.5, 0.75, 24   # FROZEN as motion_scan.py (96x168 grey, per frame)

def render_reaches_end(video: Path, start_f: int, pin_f: int, start_cell: Path, end_cell: Path,
                       frames: np.ndarray | None = None) -> dict:
    """arrival_f: first frame in [start_f, pin_f] with sim(frame, END) >= ARRIVE and >= sim(frame, START);
    frozen_before_pin_s: run of frames before the pin with step energy < FROZEN.
    ok = arrival exists and frozen_before_pin_s <= FROZEN_MAX_S."""
```
Calibration on all 34 pinned segments of iteration 4: passes T03 Q03_0 (arrival 92 %, frozen 0), T03 Q03_1,
T09 Q09_0/Q09_1, T20 Q21_1; fails the other 29, every one of them with >= 0.92 s frozen before its pin
(Q02_0 3.88 s, Q07_0 1.33 s, Q08_0 1.00 s, Q12_0 1.54 s; the hold pins 0.92-6.0 s). The verdicts match the strips
and the owner's "static image then video". A failing segment is a retake with the END pin moved earlier
(see FIX 4) or the segment split.

Tests (inject `frames`; verified against `end_gate.py` with a textured plate, START = the plate, END = the plate
panned 100 px, 72 frames — a flat synthetic image has no step energy, so the fixture must be textured):
```python
def test_a_pan_that_runs_over_the_whole_segment_passes():        # frames pan 0->100 px linearly: arrival 0.99, frozen 0.0 -> ok True
def test_a_pan_that_arrives_in_the_first_quarter_and_holds_fails():  # pan done by 25 %, then held: arrival 0.25, frozen 2.21 s -> ok False
def test_a_render_that_sits_on_the_end_picture_from_frame_0_fails():  # END repeated: arrival 0, frozen 2.96 s -> ok False
def test_a_render_that_never_leaves_the_start_fails():          # START repeated: arrival None -> ok False
def test_gate_a_on_the_same_fixture():                           # END = plate panned 100 px: end_cell_distinct -> (True, ~0.0); END = START -> (False, 1.0)
```

## THE FIX

### 1. The plan carries the END state (spec first): `Shot.end` / `Cut.end`

Add `end: str | None = None` to `Shot` and `Cut` in `studio\episode_spec.py`. The END panel is drawn iff `end` is
set. A plan lint (`route_gate` or a new `plan_gate`) fails a segment whose `motion` names travel or a state change
(crosses, exits, climbs, steps, walks, turns, lifts, lowers, sets down, comes off, springs up, falls, spreads,
darkens, closes, drops) but has no `end`. Every `end` is written as a picture: nouns and positions, then
"Changed: ..." and "Unchanged: place, lens, light, framing, wardrobe".

### 2. Per-segment list for `plan.json` (iteration 5)

END = yes: draw it, pin it. no: no END cell and NO end pin (the segment is a hold or a tracking shot; its motion
belongs to the prompt member). rewrite: the motion as written is sub-visible (an eye move, a breath, knuckles) — the
owner's rule fails it; either rewrite the motion to the visible action given and draw that END, or accept no pin.

| seg | size / motion (short) | END | END panel text (the picture after the motion) |
|---|---|---|---|
| 0.0 | MCU Stamford speaks (dialogue) | no | lips carry the motion |
| 1.0 | close Watson, eyes hold, shifts bowler | rewrite -> yes | "Watson turned from the counter to face Stamford, three-quarter to camera, the bowler now held flat against his chest with both hands; Stamford's black shoulder larger at the left edge. Changed: his head and shoulders have turned to Stamford. Unchanged: place, lens, light, drinkers behind." |
| 1.1 | insert hand loosens/closes on the knob | no (sub-visible at insert scale; the gate cannot see it) | — |
| 2.0 | medium two-shot, Stamford lifts his glass, Watson looks down | yes (and redraw the START with the glass ON the counter) | "Stamford's glass at his lips, his eyes on Watson over the rim; Watson's head bowed, looking down into his own glass on the mahogany. Changed: the glass has risen from the counter to his mouth; Watson's face has dropped. Unchanged: place, framing, mirror, light." |
| 2.1 | close Stamford over the glass, sets it down, wipes his lip | yes | "Stamford, the glass gone from frame, set down below; his bare hand at his mouth wiping his lip, his eyes still on Watson. Changed: the glass is down and the hand is at the lip. Unchanged: place, framing, gaslight, mirror." |
| 3.0 | wide cab crosses L->R (the treadmill) | yes, first priority | "The SAME stretch of wet Piccadilly street, the same shopfronts and lit lamps: the hansom now at the right edge of frame leaving it, its rear wheel and the folded hood the only parts still in frame, the horse already gone out of the right edge, the puddle's spray falling behind it, the kerb where it entered on the left now empty. Changed: the cab has travelled the width of the frame. Unchanged: camera, street, shopfronts, sky." |
| 3.1 | insert tracking beside the wheel | no (tracking; the road blurs) | — |
| 4.0 | close Watson in the cab, jolts, eyes flick | rewrite (optional) | "a jolt has thrown his shoulder against the hood's side, his head tilted, the bowler brim knocked askew" |
| 4.1 | insert hand on the knob, knuckles whiten | no | — |
| 5.0 | MCU Watson profile, hand tightens | rewrite (optional) | "his head turned from the side window to Stamford at the right edge" |
| 5.1 | insert front glass, street slides toward camera | no (moving background = the treadmill case; the prompt member owns it) | — |
| 6.0 | MCU Stamford looks out, nod | no | — |
| 6.1 | close Watson watching Stamford, looks away to the glass | yes (warn band: a head turn in close-up) | "Watson's face turned away from Stamford to the small front glass, seen in three-quarter from the other side, the bowler brim toward the camera; Stamford's averted shoulder unchanged at the right edge. Changed: the head has turned from Stamford to the glass. Unchanged: seat, hood, light." |
| 7.0 | wide gateway, Watson down from the cab, Stamford in under the arch | yes, first priority | "The same gateway from across the street: Watson standing on the wet cobbles a pace from the cab, both boots down, the stick planted, his body turned toward the arch; Stamford already under the arch, only his back in its shadow; the cab step empty. Changed: Watson is off the cab and on the cobbles; Stamford is inside the arch. Unchanged: camera, cab, horse, cabman, arch, light." |
| 8.0 | full steps, Watson climbs, the bowler comes off, Stamford steps back | yes, first priority | "The same steps from their foot: Watson on the top step in the open side-door, BAREHEADED, the brown bowler in the hand on the left of frame held against his chest, the stick planted on the top step; Stamford stepped back inside, only his shoulder visible in the doorway. Changed: three steps climbed, the hat is off, Stamford is inside. Unchanged: camera, steps, door, brick, light." |
| 8.1 | close Stamford in the door, eyes drop, away into the door | yes | "Stamford at the top of the steps turned away into the dark doorway, the back of his head and one ear to camera, the half smile gone. Changed: his face has turned from Watson into the door. Unchanged: door, brick, light, framing." |
| 9.0 | medium tracking behind, corridor walk | yes (a walk END = the next route position; the door ladder applies) | "The same two backs from behind, a third of the way down the corridor: the barred window at the far end is the height of a finger, the dissecting-room doorway now at the right frame edge, Stamford's head half turned back, the stick planted. Changed: the far window has grown and the doorway has arrived. Unchanged: lens, height, the two men's places in frame." |
| 9.1 | close Stamford profile tracking | no | — |
| 10.0 | insert slab, a drip | no (the drip is the visible action; 1 s) | — |
| 10.1 | MCU Watson stopped dead, half step back, head to Stamford | yes | "Watson a half-step back from the dissecting-room doorway, the door frame now between him and the camera's left edge, his head turned toward Stamford's shoulder, the bowler brim turned in his hand. Changed: one step back, head turned. Unchanged: corridor, light, framing." |
| 11.0 | full from behind at the far end, Watson takes the first step | yes | "Watson one pace nearer the low arched passage, mid-stride, the stick lifted clear of the flagstones; Stamford inside the passage holding the door, smaller. Changed: Watson has stepped; the stick is off the floor. Unchanged: camera, corridor, door, light." |
| 11.1 | insert boot + ferrule, the first step | yes | "The boot down one flagstone further, on the next bar of window light; the ferrule lifted behind it in the air. Changed: the boot has moved a flagstone; the ferrule is raised. Unchanged: floor, light, threshold ahead." |
| 12.0 | wide lab, the figure springs up, turns to the door | yes, first priority (and redraw the START with Holmes BENT over the table) | "Holmes upright at his table under the window, turned toward the door and the camera, the test-tube raised at arm's length toward the window, the stool tipped on two legs. Changed: he was bent over the table; he is now standing and turned. Unchanged: camera at the door, benches, flames, window." |
| 12.1 | MCU Watson and Stamford in the doorway, Stamford starts forward | yes | "Stamford a step ahead of Watson toward the benches, already past him, seen in profile; Watson turning to follow, his shoulder to camera. Changed: Stamford has moved ahead; Watson has turned. Unchanged: doorway, light, framing." |
| 13.0 | full three-shot, Stamford's hand gestures, Holmes turns to them | yes | "Holmes facing the two men, the test-tube still up, his back to the bench; Stamford's open hand extended toward Watson at the end of its gesture. Changed: Holmes has turned from the bench; the hand is extended. Unchanged: camera, benches, places." |
| 13.1 | insert Stamford's open hand turns and drops | yes | "The same sleeves and hands, Stamford's hand gone from frame, dropped below; Watson's hand on the silver knob and Holmes's plastered hand on the bench edge unchanged. Changed: the open hand is out of frame. Unchanged: everything else." |
| 14.0 | close collar, one breath | no (a deliberate still study, 1.5 s) | — |
| 14.1 | insert hand on the knob, fingers tighten | no | — |
| 15.0 | MCU Holmes speaks | no | — |
| 16.0 | MCU Watson alone, eyes drop and lift | rewrite (optional) | "his head turned to Stamford beside him at the frame edge" |
| 17.0 | medium bench, the bodkin comes down to the fingertip | yes | "The bodkin's point touching the plastered fingertip, the finger still held over the litre vessel of clear water, the flame unchanged. Changed: the bodkin has come down to the finger. Unchanged: camera, bench, vessel, water clear." |
| 17.1 | ECU drop hanging, the drop falls | yes | "The plastered fingertip bare, the drop gone; one thin red thread hanging in water that is otherwise clear; the flame in the glass. Changed: the drop has fallen and become the thread. Unchanged: vessel, framing, light." |
| 17.2 | ECU vessel, the cloud darkens to mahogany | yes, first priority (and redraw the START as the thread-only picture) | "The same vessel: the water dull mahogany through its whole depth, brownish dust settled on the bottom, no thread visible, the flame reflected in the glass. Changed: clear water with a thread has become opaque mahogany with dust. Unchanged: vessel, framing, light." |
| 18.0 | MCU Holmes speaks, sets the pen down | optional | "the pen lying on the open notebook, his hand flat beside it" |
| 19.0 | insert handshake, one pump | no (sub-visible) | — |
| 19.1 | medium tracking back, the two men grow larger | yes | "Watson and Stamford filling the frame waist-up, close to the camera at the door, Stamford's shoulder at the frame edge; Holmes small and bent under the far window behind them. Changed: the men are twice their size in frame; the bench is far. Unchanged: room, window, light." |
| 20.0 | MCU Watson asks (dialogue) | no | — |
| 21.0 | medium tracking beside along the railings | no (tracking) | — |
| 21.1 | close Watson walking, tracking | no | — |
| 22.0 | MCU Stamford, last word, coda hold | no | — |

20 END cells (+5 optional). Sheets: criterion 5+3 = 8 (3x3), cab 8+2 = 10 (3x3 + 3x1), gateway 7+3 = 10,
corridor 6+4 = 10, lab 8+4 = 12 (3x3 + 3x1), bench 6+4 = 10: ten sheets against six now, ~$2.00 plus strict redraws.

### 3. Packer rule (`studio\episode_seq_board.py`)

- `end_panels(segs)` returns one END cell for every segment with `seg["end"]` set; it no longer takes `spare` and
  never invents one. `sheets()` sizes the grid on `len(segs) + len(ends)` (END cells are cells, not padding);
  when the count exceeds 9 the overflow sheet is chained as today.
- Order on the sheet: each END panel IMMEDIATELY AFTER its own start panel. For geography cells the END panel is the
  walk's next position and sits inside the walk strip (its `path` = start path + one ladder step, so `door_size` and
  `route_gate.regressions` apply to it unchanged). For close cells the pair sits together in story order.
- Priority when a chained sheet must be trimmed (never more than 4 END panels on one 3x3 sheet, so the sheet is not
  a copying exercise): 1 travel across the frame (3.0, 7.0, 8.0, 9.0, 11.0, 12.1, 19.1); 2 object state changes
  (17.2, 17.1, 12.0); 3 body/head turns (2.1, 8.1, 10.1, 13.0, 6.1, 1.0); 4 hand/foot actions at insert scale
  (11.1, 13.1, 17.0, 2.0). Optional rewrites last.
- Panel texts: start panel keeps "The instant before: <motion>; the action has not begun" (Q02_0 and Q12_0 were
  drawn past their state). END panel:
  `Panel {k}, the END of panel {j}: {end}. Changed from panel {j}: {changed}. Unchanged: place, lens, light, framing, wardrobe.`
- Sheet sentence (replaces `end_order`):
  "An END panel comes immediately after the panel it ends and shows the same place, lens, light and framing one
  action later: the named change is complete and visible at a glance, everything else is unchanged; a viewer must be
  able to say what happened between the two panels. No END panel is a copy of its panel."
- Gate A runs on every END cell after `conform`; a failure triggers the STRICT redraw with
  "STRICT: panel {k} must differ from panel {j} at a glance: {changed}." Second failure: drop the END cell, report.

### 4. Pins and the take prompt

- `episode_takes.end_pins`: pin only END cells that exist (and passed Gate A); never pin the start cell again
  (the hold bracket froze 22 of 24 holds; iteration 3 without it froze 25 % of take time, iteration 4 with it 55 %).
- Put the END pin EARLIER than the last grid frame for long segments: the model arrives and holds, so the pin sets
  the arrival time. Pin at `grid_frame(start + 0.6 * (next - start))` when the segment is longer than 2.5 s, and
  leave the last 40 % for the prompt's continuing action (T03 shows the glide fills exactly the span to the pin).
- Reference strip (`takes_r2v.reference_strip`): [start][its END][next start][its END]..., and `ends_sentence`:
  "a panel that repeats the place and framing of the panel before it is that SAME shot's last frame, not a new
  shot; the take never returns to an earlier panel."
- Take DQ: Gate B per END-pinned segment, hard fail -> retake with the pin moved earlier (rule above) or the segment
  split at a sub-shot.

### 5. Cab exterior specifically (owner: "horse jumping but not moving anywhere")

START Q03_0 redrawn with the cab ENTERING at the left edge (the current cell has it centred), END 3.0 as in the table
(cab leaving at the right edge, same street). With both pinned the only trajectory that satisfies them is lateral
travel across a fixed street, which is the shot. The motion text: "the cab crosses the whole frame from the left edge
to the right edge at a trot, the shopfronts stay where they are, the wheels throw water" — no "static shot" clause,
which the prompt member is removing anyway.

---

# THE DECISION, 2026-09-16: the ref2v workflow pins no last frame

Everything above is a proposal for making END pins work. It was never adopted: gate A
(`end_cell_distinct`) and gate B (`render_reaches_end`) do not exist in the codebase, and
the owner's experiment of 2026-09-13 (`takes_r2v.NO_ENDS`, "render every take with NO END
picture and the arrival said in words, then compare") was never run. `NO_ENDS` stayed
`False` through eight episodes by default, not by decision.

The owner's standing rule, stated again on 2026-09-16: **no first-frame/last-frame pinning
in the ref2v workflow, because it warps.** Section 2 above is the mechanism, in this
document's own words:

> the model moves to the END picture as fast as the distance allows, then holds it until
> the pin. A near-copy END = a freeze for the whole segment. A far END = a glide over the
> whole segment -- but the glide is whatever separates the two pictures.

So the pin has no good setting. Near freezes; far dissolves the background. Gate B does not
fix that; it only detects it after the render is paid for.

## What episode 8 shipped

Episode 8 carried **15 END pins against 3 in episode 7 and 1 in episode 6** -- not because
anything was decided, but because `sq.reaches` was fixed on 2026-09-15 to drop its 0.45
re-staging floor for a camera told to travel (`The END cell now reaches the take that paid
for it`, 1a31d69). Every one of episode 8's shots travels.

| | ep06 | ep07 | ep08 |
|---|---|---|---|
| takes given an END pin | 1 | 3 | **15** |

Measured on the delivered files (`shots.json` + `T??.mp4`):

- All 15 pins sit on a travelling camera.
- **7 of the 15 have START/END pictures farther apart than the 0.45 floor** -- admitted only
  because the floor was dropped. `Q15_0` scores **0.041**: the two pictures share nothing,
  which is precisely the Q03_0E case (the street dissolving into the gate) that section 2
  named the treadmill.
- 7 of the 15 freeze 0.8-2.1 s before their pin (worst `T04`, 2.08 s), against 3 of the 13
  unpinned takes. The pin roughly doubles the rate; it is not the only cause of a freeze.

## What is enforced now

`scripts/episode/takes_r2v.py`: `NO_ENDS = True`, and `end_cells` returns `[]` whatever is
drawn on disk. `--ends` is the control, kept so the comparison stays reproducible; nothing
in the pipeline asks for it. The destination is carried by
`episode_ref_official.arrival_clause`, verified against the rebuilt artefact rather than the
function: 28 of 28 episode-8 take prompts, 0 staged END pictures, 0 occurrences of
"last frame of [Shot".

Tests: `tests/test_dq_targets_what_was_staged.py::test_the_ref2v_workflow_pins_no_last_frame`
(a drawn, perfectly reachable END cell is still refused) and
`::test_the_arrival_is_said_in_words_when_no_end_is_staged`.

The END panels are still DRAWN on the sequence sheets. They cost nothing extra (they fill
spare cells that would otherwise be alternates) and they remain a useful contact-sheet
check that the plan's motion has a destination at all. They are simply never pinned.
