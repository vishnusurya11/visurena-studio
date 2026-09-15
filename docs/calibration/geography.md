# GEOGRAPHY — does the place hold from take to take? (iteration 4, master_iter11; iteration 3 for calibration)

Evidence folder: `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\geography\`
- `frames\it4\`, `frames\it3\` — first frame, last frame, the frame at every pin and the frame just before the next pin, of every take (`meta.json` beside them)
- `tl_it4_<setup>.png`, `tl_it3_<setup>.png` — the timeline per setup: one row per take, those frames in order, labelled with landmark height / luma / pin similarity
- `geo_it4.json`, `geo_it3.json` — the numbers behind the tables below (`geo_scan.py`)
- `T07_strip_4fps.png`, `master11_46-58_4fps.png`, `gateway_cells.png`, `it3_T06_strip_4fps.png` — the hospital steps
- `master11_118-133_4fps.png`, `T18_fail1_strip.png`, `it3_T18_strip.png` — the bench exit
- `it4_T09_walk_8fps.png`, `it4_T20_walk_8fps.png`, `it3_T19_walk_8fps.png` — the walks at 8 fps
- `geo_gate.py` + `test_geo_gate.py` (7 tests, pass) — THE CHECK; `calibrate.py` — its run over every take of both iterations; `slide2.py` — the pace measure

Nothing spent, nothing in the repo edited.

## One line

The pins are obeyed to 0.999 at every pinned frame, so the geography is exactly what was DRAWN — and three drawn things break it: the gateway END cells were drawn as the same instant (the men re-enter the side-door, master 48.9-57.2 s), the lab approach was drawn flat (window 265 px at the door, 260 px mid-room), and the two walks of the second half (railings, bench exit) were drawn with no destination, so they freeze or crawl. The corridor holds (door 46 → 267 px, monotonic) and the cab route holds. An automatic gate on the takes catches every break the humans found in iterations 3 and 4 (calibration below).

## DIAGNOSIS

### Setup-level position timeline, iteration 4 (story order; `path` from plan.json; landmark = `route_gate.door_height` on the RENDERED frame; sim = frame vs its pinned cell)

| setup | take (shots) | segments: cell @ frame, path | landmark px on rendered frames | handoff in → out |
|---|---|---|---|---|
| criterion | T00 (0) | Q00_0 @0/137, 0.1 | no landmark (the mirror is not a bright blob; 39-40 px is a lamp) | — |
| | T01 (1) | Q01_0 @0/73, 0.15; Q01_1 @77/169, 0.15 | — | cut at f77 lands LATE: frame 77 still matches Q01_0 (sim 0.31 vs Q01_1) |
| | T02 (2) | Q02_0 @0, Q02_0E @93, 0.3; Q02_1 @97/205 | — | Q02_0E ≈ Q02_0 (sim 0.95): a face beat, harmless |
| cab | T03 (3) | Q03_0 @0, Q03_0E @85, 0.1; Q03_1 @89/169, 0.15 | — | Q03_0E moved (sim 0.34: the cab has left frame) |
| | T04 (4) | Q04_0 @0/73, 0.4; Q04_1 @77/169, 0.45 | — | interiors, same seat, same light (luma 44 → 37 for the hand insert) |
| | T05 (5) | Q05_0 @0/73, 0.5; Q05_1 @77/169, 0.55 | — | the front-glass insert is bright (67) — legitimate |
| | T06 (6) | Q06_0 @0/69, 0.7; Q06_1 @73/153, 0.75 | — | → gateway: the same two-wheeled hansom with horse in Q07_0 (review6 item 3 fixed) |
| gateway A | T07 (7, 8) | Q07_0 @0, Q07_0E @45, 0.0; Q08_0 @49, Q08_0E @117, 0.1; Q08_1 @121/253, 0.1 | arch = dark stone: door_height None (see CHECK) | **BREAK 1**: Q07_0E ≈ Q07_0 (sim 0.89, Watson still on the cab step), Q08_0E ≈ Q08_0 (sim 0.82, still on the same step, hand at the brim). The take: 0-1.9 s off the cab (frozen 0.5-1.9), 2.0 s hard cut to the steps, **2.1-4.75 s frozen on the steps**, 4.9 s cut to Stamford's close (pin 121), **5.5 s cut BACK to the steps, Watson climbs and both go in (5.5-9.0 s)**, 9.3 s cut to Stamford's close for the END pin. Two walks up the same steps; the doorway is entered twice. In the master: 48.9-51.7 pause, 51.75-52.25 Stamford, 52.5-56.0 the climb, 56.25-57.0 Stamford. DQ saw off_beat 3, scene_events [4.0, 5.5, 9.25], camera_ok False — and passed it (advisory). |
| corridor | T09 (9) | Q09_0 @0/73, 0.1; Q09_1 @77/169, 0.3 | 46, 45, 46 (first 3 s), then the profile close (none) | the cut to Stamford's profile lands at 4.62 s, not 3.21 (frame 77 sim -0.08): 1.4 s late; master S09 shows the corridor 1.4 s longer than placed |
| | T10 (10) | Q10_0 @0/73, 0.7; Q10_1 @77/169, 0.7 | slab insert / doorway MCU: none | fine |
| | T11 (11) | Q11_0 @0/65, 0.95; Q11_1 @69/153, 0.95 | 267, 267, 267 | **door only grows: 46 → 267, never back.** Holds. |
| lab | T12 (12) | Q12_0 @0, Q12_0E @65, 0.0; Q12_1 @69/205, 0.05 | 265 → 240 (Holmes springs up, the camera settles; a hard snap at 0.5 s) | Q12_0E moved (0.62) ✓ |
| | T13 (13) | Q13_0 @0/65, 0.5; Q13_1 @69/153, 0.5 | 260, 260, 260 | **BREAK 2**: from the doorway (0.0, window 265) to mid-room (0.5, window 260) the landmark does not grow. The drawer ignored the ladder ("thumbnail" → "hand"); the sheet DQ only checks SHRINK > 25 %. Iteration 3 had the same: Q11_0 175 → Q12_0 177. The lab door → Holmes's table never reads as an approach. |
| | T14 (14, 15) | Q14_0 @0/65, Q14_1 @69/141, Q15_0 @145/253, all 0.6 | closes: none | fine |
| | T16 (16) | Q16_0 @0/153, 0.6 | none | → bench: luma 51 → 64, chroma jump 7.4 (largest same-room handoff). The bench sheet was drawn with NO previous sheet (refs: plate_bench + 3 cast sheets; `seq_lab_0.png` absent), so "match its light" never applied. |
| bench | T17 (17) | Q17_0 @0/117, 0.2; Q17_1 @121/209, 0.3; Q17_2 @213/357, 0.3 | 279 (bigger than the lab's 260: consistent with standing at the table under it) | fine as geography; frozen 14.75/15 s (MOTION's problem) |
| | T18 (18, 19) | Q18_0 @0/105, 0.5; Q19_0 @109/185, 0.6; Q19_1 @189/289, 0.9 | T18.mp4 absent (re-render pending); T18_fail1 + master 128.75-132.5 | **BREAK 3**: the exit geography is now RIGHT (camera at the door facing them, far window and a bent Holmes behind them — review6 item 3 fixed) but the men never walk: 3.75 s standing two-shot. The 3x2 bench sheet had no spare cell, so Q19_1 has no END frame and the tracking-back walk has no destination. |
| gateway B | T20 (20, 21) | Q20_0 @0/109, 0.3; Q21_0 @113/185, 0.5; Q21_1 @189/289, 0.6 | none | **BREAK 4**: Q21_0 "tracking beside at walking pace" is bracketed by Q21_0 and Q21_0 again (no END drawn: the two spares went to Q07_0/Q08_0 by story order) → frozen 4.6-7.75 s; Q21_1 close "walking along the railings" → the railings crawl (floor slide 12 px/s; real walks 25-49). The second gateway visit is farther along the route on paper (0.3 → 0.6, arch behind → railings) and in the cells; in the take nobody moves along it. |
| | T22 (22) | Q22_0 @0/153, 0.8 | none | fine |

Route positions never go backwards within a setup (`route_ok` holds in both plans); the gateway is used twice at different positions (0.0-0.1 arrival, 0.3-0.8 the walk after) and the two visits do not share a cell. The men re-enter a doorway once (BREAK 1). The corridor door only grows. The cab route is four interiors and one exterior with the same hansom at both ends.

### Iteration 3 against iteration 4

- Gateway: it3 T06 walked off the cab, across the cobbles and up the steps in one continuous 4.4 s (`it3_T06_strip_4fps.png`), one entry, drawn from the wrong instant (review6 item 4). it4 fixed the drawing and broke the walk with the END pins. Net: worse for the viewer.
- Corridor: both iterations monotonic (it3: 50 → 204; it4: 46 → 267).
- Lab: flat in both (175→177; 265→260). Never caught.
- Bench exit: it3 walked the wrong way; it4 faces the right way and does not walk.
- Railings walk: it3 T19 is a real walk (8 fps strip: both men stride, the gas lamp passes behind them, floor slide 27.6 px/s); it4 T20 froze (0 px/s) then crawled (12).

### The owner's 15:35 note: the hospital steps

It is the END-pin freeze AND a ping-pong, in that order, and not a take handoff (T07 is one take; its neighbours T06/T09 hand off cleanly at 1.0 similarity to their own cells). Mechanism: `end_pins()` closes the Q08_0 segment with Q08_0E at frame 117; the drawer drew Q08_0E as the same instant as Q08_0 (sim 0.82; compare `gateway_cells.png` panels 4 and 5: same step, same hand at the brim), so the model must arrive at frame 117 looking like frame 49 — it holds still for 2.7 s. Four frames later (121) it must show Stamford's close; it does, for 0.5 s; then, with 132 frames of "Static shot… his eyes drop" to fill before the next Q08_1 pin at 253, it goes back and performs the climb the segment never got to do. The same instant-END pattern is on Q07_0E (0.89): Watson never leaves the cab step, so the cut to the steps at 2.0 s is a teleport.

### The owner's second note: walking pace

Pace never reads as slow legs; it reads as the world not moving. Measured (floor-band slide, px/s at 192 wide, `slide2.py`; step counts from the 8 fps strips):
- it4 T09 corridor 0-3 s: Watson ≈1.8 steps/s with the stick planting on the right step, Stamford matching — real pace. Stamford's profile walk 3.25-7 s: slide 25.6 — real.
- it3 T08 profile walk 48.8, it3 T19 railings 27.6 — real.
- it4 T07 climb 5.5-9.0 s: 4 steps in 3.5 s on stairs (≈1.2/s) — a limp on stairs is plausible on its own, but it follows 2.7 s of standing on the same step, so the whole reads as a freeze-then-walk.
- it4 T20 Q21_0 4.6-7.75 s: 0 (frozen); Q21_1 7.9-12 s: 12 (a crawl behind a walking man = slow motion). This is the one place the walk reads as slow motion.
- Bench exit (master 128.75-132.5): 0 — no walk.
- Holds for reference: T11 far end 0, it3 T06 climb 0 (a static camera on a climb gives no floor slide; use the landmark for those).

## THE CHECK

Everything is in `geo_gate.py` (tests in `test_geo_gate.py`, 7 pass). Two gates the brief asked for, plus the two sheet-level gates that decide them upstream.

### 1. Take-to-take handoff gate — decided on the SHEET, verified on the TAKE

Measured: the first frame of every take matches its start cell at 0.999-1.0 and the last frame matches its END pin at 0.999-1.0 (all 18 + 17 takes, both iterations, `geo_it4.json` / `geo_it3.json` `pin_sim`). So a handoff between take k and k+1 IS the pair (last cell of k, first cell of k+1). Luminance of those frames is not a usable "same light" test: legitimate insert→close cuts inside one room swing 25-37 luma (T13→T14 +37, T10→T11 +25); I do not propose a luma gate. What is checkable:

```python
def landmark_track(heights, paths, sizes, shrink=0.25, grow=1.3, step=0.3) -> {"shrunk": [...], "flat": [...]}
    # geography sizes only (medium/full/wide); heights from route_gate.door_height on the
    # rendered anchor frames of the setup's takes in story order (and on the cells at sheet time)
def direction_of(text) -> 'away' | 'toward' | 'beside' | 'still'      # from frame + motion text
def direction_breaks(segments) -> [(index, from, to)]                # a change with no "turn" named
```
Thresholds: shrink 25 % (existing `route_gate.REGRESSION`; a static hold moves ≤ 2 %, a camera settle 9 %); grow 1.3× when the route advances ≥ 0.3 (corridor 47 → 267 over 0.85 passes; lab 266 → 261 over 0.5 fails; it3 lab 175 → 177 fails). Direction: a plan-level text gate; the bench exit of plan_v4 ("from behind… leaving for the door") next to a lab route drawn "from behind" was consistent but wrong for the room, which only a human sees — the gate catches the other case, plan_v5's `toward the camera` after an `away` corridor with no turn named (it names none; the fix below adds it).

Verified on the takes: it4 corridor `[46,45,46,267,267,267]` → no shrink, no flat; it4 lab `[265,240,260,260,260]` with paths `[0,0,0.5,0.5,0.5]` → flat at index 2 (BREAK 2); it3 lab `[175,270,269,177]` → the 270 is the doorway MCU (medium_close, excluded), so `[175,177]` over 0.5 → flat.

### 2. Landmark-monotonic gate on rendered frames — and what to do where there is no bright landmark

`route_gate.door_height` finds the corridor's barred window and the lab's arched window (and the criterion's lamp, wrongly: 39-40 px — it should be given a setup allow-list). It finds nothing at the gateway (the arch is dark stone, the sky touches the band edge and is excluded) and nothing on the bench (the flame is small and blue). I tried to extend it and stopped: for the gateway there is no bright compact far landmark to measure; the honest finding is "no automatic brick for the gateway and bench", and the geography there is carried by (a) the route positions in the plan, (b) `end_moved` on the sheet, (c) the cut gate below on the take. A human line on the contact sheet stays for those two setups: "arch behind → railings beside → corner with cab ahead".

### 3. The gate that actually catches every break on disk: unplanned / extra pictures

```python
def energy(frames_24fps_96x168_grey) -> per-frame mean |diff|
def cuts_from_energy(e, cut=20.0, ratio=4.0) -> [seconds]        # a hard cut: >= 20 and >= 4x the surrounding second's median
def unplanned_cuts(cuts, pin_frames, tol=0.3) -> [seconds]       # no pin within 0.3 s
def transitions(anchors) -> int                                   # pins where the cell changes
def extra_pictures(cuts, anchors) -> int                          # hard cuts beyond the plan's cell changes
```
A take FAILS when `unplanned_cuts` is non-empty or `extra_pictures > 0`. Calibration (`calibrate.py`, every take of both iterations; peak energy of a pinned cut 32-76, of a moving wide 14, of a spring-up 8):

| iteration 4 | verdict | why |
|---|---|---|
| T07 gateway | FAIL | cuts 0.54, 2.04, 4.92, 5.5, 9.33 for 2 cell changes: 3 extra pictures = the re-entered doorway |
| T01 criterion | FAIL | extra cut 4.75 s = review7's known strip-neighbour flash |
| T02 criterion | FAIL | extra cuts 4.46, 5.96 (the Stamford close ping-pongs, review6 item 1 class) |
| T09 corridor | FAIL | the planned 3.21 s cut lands at 4.62 (1.4 s late) |
| T12 lab | FAIL | a snap at 0.5 s inside a "static" wide (camera 1.0 → 0.89) |
| T13 lab | FAIL | the insert's cut lands at 5.0, not 2.88 |
| T00 T03 T04 T05 T06 T10 T11 T14 T16 T17 T20 T22 | ok | every hard cut within 0.3 s of a pin, none extra |

| iteration 3 | verdict | matches review6 |
|---|---|---|
| T02, T04, T09, T16 | FAIL | review6 item 1's four ping-pong takes, exactly |
| T13, T19 | FAIL | review6 item 8's early cuts (-0.29 s, -0.46 s; measured -0.42, -0.50) |
| the other 11 | ok | |

No false positives against the human lists on 35 takes. T20's frozen two-shot and crawl are NOT caught by this gate (a freeze makes no cut) — that is MOTION's gate plus `end_moved`/`floor_slide` below.

### 4. Two sheet-level gates (before any render)

```python
def end_moved(start_cell, end_cell, floor=0.75) -> bool     # a WALK's END cell must be a different instant
def floor_slide(frames, band=0.22) -> px/s ; walk_moves(px_s, floor=20.0)   # a tracking walk's world must move
```
`end_moved` calibration (all five END cells drawn in iteration 4): Q07_0E 0.89 FAIL, Q08_0E 0.82 FAIL (the two that froze the steps); Q12_0E 0.62 ok, Q03_0E 0.34 ok (the two that moved); Q02_0E 0.95 exempt (a face beat, not a walk). Four walk samples: thin; the threshold sits between 0.62 and 0.82 and should be re-checked on iteration 5's sheets. `floor_slide` is a take-DQ measure for segments whose motion says "Tracking": T20 Q21_1 12 → FAIL; it4 T09 profile 25.6, it3 T19 27.6, it3 T08 48.8 → ok. (My first attempts — autocorrelation cadence and a top-band slide — were broken instruments: the autocorrelation locks onto the decoder's 8-frame stride at 0.33 s on every take, holds included; do not use it.)

Where it plugs in: `end_moved` and `landmark_track(flat)` into `scripts/episode/seq_boards.py` next to `route_gate.regressions` (a failing walk END or a flat approach redraws the sheet STRICT, as the shrink rule does today); `cuts_from_energy`/`unplanned_cuts`/`extra_pictures`/`floor_slide` into `scripts/episode/take_dq.py` as HARD verdicts (today `picture_ok`/`camera_ok` are advisory: T07 and T20 carry `"passed": true`); `direction_breaks` into the plan validator with `route_ok`.

## THE FIX

Per break, in the order a viewer meets them.

**BREAK 1 — the hospital steps (T07; master 48.9-57.2 s).** Three changes, all on the sheet and the plan; no pin code change needed once the END cells are real.
- `end_panels()` writes an END frame as "the last frame of panel N … {motion} has just finished" and the drawer repeats the panel. Give the plan an explicit `end` text per walk shot and have `end_panels` use it. For iteration 5:
  - Q07_0E: "Watson standing on the wet cobbles beside the empty cab step, the stick planted, his bowler on; Stamford already under the arch turning in; the cab and horse unchanged."
  - Q08_0E: "the worn stone steps EMPTY from the same low angle; the side-door at the top standing open on the dark corridor, nobody in it; a glimpse of a tweed coat-tail going in."
- Plan shot 8: put Stamford's close (the 3.0 s sub-cut, Q08_1) BEFORE the climb, not in its middle — "Close on Stamford at the top of the steps in the open door, turned back down toward camera, the uneasy half smile" as sub 0 at 0 s, then the climb as sub 1 with Q08_0 → Q08_0E. The take then has nothing left to perform after the close, and the doorway is entered once. Frame text for the climb, written as the instant: "Watson's boot is on the third step from the top, his weight on the stick, RISING" (already there) plus motion "he climbs the last three steps without stopping, the bowler comes off at the door, both go in; the steps are empty at the end."
- Sheet prompt (gateway): after the END sentence add "Panel 8 must NOT repeat panel 1: the man has left the cab step and stands on the cobbles. Panel 9 must NOT repeat panel 2: the steps are empty." — and gate it with `end_moved`.

**BREAK 2 — the lab approach (T12 → T13; master 84-90 s).** Sheet prompt for `seq_lab_0`: on the mid-room panel replace the ladder word with a measurable: "the tall arched window now fills the top THIRD of the panel, TWICE the height it has in panel 1"; gate with `landmark_track(flat)` on the cells (266 vs 261 fails today). Plan: give T12's doorway MCU (Q12_1, path 0.05) an END frame that is the walk — "the two men mid-room between the benches from behind, the window larger" — so the 5.75 s frozen MCU becomes the approach the route promises.

**BREAK 3 — the bench exit (T18, shot 19 sub 1; master 128.75-132.5 s).** The 3x2 bench sheet left no spare cell. Rule: a tracking walk always gets an END cell, bumping the grid (3x3) if needed. Q19_1E: "the two men now close to the camera in the doorway, filling the frame, Stamford's shoulder cutting the edge; behind them, small and far, Holmes bent over his table under the window." Add "they turn from the bench" to the shot-19 frame text so `direction_breaks` sees the away→toward change as a named turn. Draw the bench sheet WITH `seq_lab_0.png` as the previous sheet (the light jump 51 → 64 luma, chroma 7.4, is the missing reference).

**BREAK 4 — the railings walk (T20; master 137.2-144.3 s).** `end_panels` orders walk cells by story order, so the two gateway spares went to the arrival (Q07_0, Q08_0) and the tracking walk Q21_0 got none. Order: tracking walks first (motion starts with "Tracking"), then static-camera walks, then the rest. Q21_0E: "the same two-shot a dozen paces further along the railings, the gas-lamp post that was ahead of them now behind, the corner and the waiting cab nearer." Q21_1 frame text: "the railings and the hospital wall sliding past behind him at walking pace, a lamp post passing" and gate the take with `floor_slide ≥ 20`.

**Pins (`studio/episode_takes.py`).** No code change to `end_pins`; the END pin is right when the END cell is right. The one pin rule to add: a hold whose END is its own start cell (`has_end=False`) may only be pinned that way if its motion is a face beat (size close/medium_close/insert); a geography cell without a drawn END gets NO end pin (the iteration-3 behaviour, 25 % frozen) rather than a same-cell pin (55 % frozen). That single rule would have left T20's two-shot and T17's bodkin free to move.

**DQ.** Promote `picture_ok` and `camera_ok` from advisory to verdict, replacing `scene_events` with `cuts_from_energy` + `unplanned_cuts` + `extra_pictures` (calibrated above: zero false positives against both human reviews).

## Not a geography problem, noted for the others

- Late cuts inside takes: T01 f77 (Q01_1) sim 0.31, T09 f77 -0.08, T13 f69 -0.02, T20 f189 -0.01: the picture change lands 0.4-2.1 s after the pin at exactly the pins that follow a same-cell END pin four frames earlier (Q01_0@73→Q01_1@77 etc.). T04, T05, T10, T14 with the same layout land on time, so it is not a clean rule; CUT reviewer's domain.
- Criterion: `door_height` returns 39-40 on a lamp; give the gate a per-setup switch (corridor, lab only).
