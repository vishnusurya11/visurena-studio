# TRANSITIONS — why a pinned cut shows a foreign picture or ping-pongs, and how to make it land

Episode root: `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\library\20260822113400_a-study-in-scarlet\episodes\ep01\`
Work: `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\transitions\`
(`cutscan.py` / `cutscan.md` / `cutscan.json` = every frame of every iteration-4 take at 24 fps matched to its own cells, all other cells and the plates; `cutscan3.py` / `cutscan3.md` = the same for iteration 3; `dense_*.png` = labelled frame strips; `cut_landing.py` + `test_cut_landing.py` = THE CHECK; `calibrate.py` / `calibrate.txt` = the gate run on every take on disk.)

Method: 24 fps, not 4 fps — a cut is a one-frame event and 4 fps cannot tell "on the pin" from "three frames early". Each frame's closest cell by `studio/frame_match` cosine; "foreign" = a cell of another take or a plate beating every own cell by 0.05. Nothing spent, nothing edited in the repo.

## DIAGNOSIS

### D1. The mechanism of a pin (from the node source, not from the docstring)

`ComfyUI\comfy_extras\nodes_minimax_h3.py` `MiniMaxH3AddGuide` + `comfy\ldm\minimax\model.py` `PackedLayout`: an anchored image is VAE-encoded to one latent frame and appended as a **conditioning row block** with time position `cursor + FRAME_RESCALE(5/3) * frame_idx`, "re-injected every step (never denoised)". It is **not** a replacement of the video latent. A pin is a soft attention target at a time — it competes with the text and the references, and the model can ignore it (T09, T13, T01 below prove it does).

Consequences measured on 24 internal cuts of iteration 4 and 16 of iteration 3 (`cutscan.md`, `cutscan3.md`):

| pins around the cut | cuts | landed in [-3, +1] frames | early by 5-24 f | late / ignored | picture at the cut |
|---|---|---|---|---|---|
| iteration 3: start pin B@f only | 16 | 6 | **10** (-5 … -24) | 0 | 2 foreign (T03 plate_gateway 21 f before the wheel insert; T13 Q12_0 14 f) |
| iteration 4: A@f-4 + B@f (END or hold pin then start pin) | 24 | **20** | 0 | 4 (T09 +34, T13 +51, T01 +37 / +54 both attempts) | 3 foreign (T01 ×2 plate_criterion 40 / 51 f; T17_fail1 plate_bench 30 f) |

- Every honoured cut is a **hard one-frame change** (score 1.00 → 1.00 on the other cell between consecutive frames): no smear, no dissolve, in either iteration and with either wording. The cut lands **exactly on the pin frame** (T02 97, T03 89, T04 77, T06 73, T07 49, T11 69, T14 69, T17 121) or **on the frame after the previous pin** (pin-3: T05 74, T10 74, T12 66, T14 142, T17 210, T18 106/186, T20 110, T07 118). With two pins four frames apart the cut floats inside the gap; nothing else.
- **The token grid is not what `on_grid()` says.** `FRAME_PER_TOKEN = (1, 4, 4, 4, 4)`: a cycle of 17 frames, token starts at `17c + {0, 1, 5, 9, 13}`. "1 mod 4" hits a token start only in cycles 0, 4, 8 (frames 0-16, 68-84, 136-152); pins 49, 89, 97, 109, 113, 121, 189 all sat mid-token. It made no difference: 97 (last frame of token 94-97) landed at 97; 49 landed at 49. A pin's time position is continuous (5/3 per frame); the grid is irrelevant to landing. (The 4-frame gap between A@f-4 and B@f is the only reason the "-3" cases exist.)
- **The bracket lands the cut but freezes the segment.** The A@f-4 pin is why iteration 4 has 0 early cuts against 10 in iteration 3. But `motion_iter4.json` per segment: the bracketed segments freeze whether the pre-cut pin is the same cell (hold) or a drawn END cell — T02 Q02_0→Q02_0E 93 % frozen, T07 Q07_0→Q07_0E 68 %, Q08_0→Q08_0E 83 %, T12 57 %, T13 hold 100 %; only the moving cab T03 Q03_0→Q03_0E is 0 %. The model reaches the pinned end picture in ~1 s and waits there. So MOTION's removal of the pre-cut pin (`episode_takes.end_pins`, `takes_r2v.card` "every cell pinned ONCE") is right for motion and will bring back iteration 3's early cuts (0.2-1.0 s) unless the cause of the early cut is removed (D4) and the residue is measured (THE CHECK) and absorbed (THE FIX, F4).

### D2. The foreign picture at T01's cut is the location PLATE, not a strip neighbour

`dense_T01_plate.png`, `dense_T01r_plate.png`, `criterion_cells.png` (the plate and the six Criterion cells side by side): the interloper is the bar seen from the far end with a street window behind the counter and drinkers at the near end. None of the six cells of `seq_criterion_0` is that picture; `plate_criterion.png` is exactly that picture without the drinkers. Frame-by-frame (`cutscan.json`): T01.mp4 frames 74-113 (40 f = 1.67 s) and T01_retake1.mp4 frames 74-130 (57 f = 2.38 s) best-match `plate_criterion.png`; the hand insert Q01_1 arrives at 114 / 131 (+37 / +54 frames after its pin at 77). The DQ called it "Q21_0 foreign 0.444" only because the plates were not in its foreign set.

Same class, other takes: T17_fail1 frames 139-176 = `plate_bench.png` for 1.58 s right after the cut to the extreme close-up of the finger over the vessel (Q17_1 pinned 121, shown 118-138, then the plate, then Q17_1 again); iteration 3 T03 frames 68-88 = `plate_gateway.png` before the wheel insert. **Every plate intrusion is at a cut to an insert / extreme close-up.**

Why the plate: the prompt promises it. `episode_ref_official.retention()` writes for every take `<Subject 2> (appears in [Shot 1], [Shot 2]): fully_preserved - the room, its furniture, walls, windows and light.` and the subject line describes the whole bar ("drinkers two deep at the near end by the doors … the mirror behind the counter"). For a hand on a knob at the foot-rail there is no room, furniture, walls or windows to preserve; the model satisfies the retention claim by showing the room — the plate, with the promised drinkers painted in — and only then the hand. Two more sentences push the same way in T01: `[Shot 2] … The people are seen from behind, in profile or far off.` (the `hidden` boilerplate, fired by "hand"/"insert" in the frame text: a wide with far-off drinkers satisfies it, a hand does not), and the narration event written into [Shot 1] `From 00:00.250 to 00:05.020 nobody on screen speaks while John Watson's lips remain completely closed` — it spans across the cut at 03.208 and tells the model Watson's face is on screen until 05.02. The retake with a new seed (T01_retake1) reproduced the failure to the frame (plate from 74 in both) — the cause is the prompt, not the seed.

The strip neighbour removal (already in `takes_r2v.reference_strip`) is fine but does not touch this: the plate is reference `<Picture 2>` in every take.

### D3. Ping-pong = the model returns to the picture it was shown LAST, when the new segment has nothing to do

Run-length sequences (`cutscan.json`, closest cell per frame):

- **T07 (the owner's hospital steps)** `dense_T07_steps.png`: Q07_0 0-12 → Q07_0E 13-48 (the wide, frozen) → Q08_0 49-92 (steps, Watson's back, 1.8 s, frozen 83 %) → Q08_0E 93-117 (steps END: hand at the brim) → **Q08_1 118-131 Stamford close for 0.58 s** → **Q08_0E again 132-223 = 3.83 s, and THIS is where he climbs** → Q08_1 224-259 (pulled back by Q08_1's last-frame pin at 253). The viewer sees: Watson still on the steps ~3 s, a flash of Stamford, back to the steps where Watson walks up, Stamford again. The cut itself landed at 118 (pin 121); the picture then left the target after 14 frames. It went back to **its own earlier cell (Q08_0E, the END cell of the previous segment)** — the strip at that time held the neighbour cells too, but the return was to the take's own END frame, which had been pinned 4 frames before the cut and sits as a trailing panel in the strip.
- **T02**: Q02_0E 11-96 → Q02_1 97-106 (0.42 s) → **Q02_0E 107-142 (1.5 s)** → Q02_1 143-208. Same shape: the close lands on the pin, holds under half a second, returns to the previous END cell, comes back for the final pin.
- Iteration 3 (no END pins, neighbour strips): T02 close at 69 → two-shot Q02_0 again 96-152 (2.3 s) → close; T04 profile at 145 → hand insert Q04_1 again 177-310 (5.6 s). The return target is always **the take's own previous cell**, never the neighbour (iteration 3's invented pictures, T09/T16, were foreign compositions, D2's class).

What the four ping-pong segments share, against the 20 that held: the segment after the cut is a **static close-up whose motion text is a stillness** (T02 "an odd measuring look, mouth closed"; T07 "the half smile goes; his eyes drop"; iteration 3 T02 the same close, T04 "his left arm held stiff") and is scheduled for **> 4 s** (T02 4.35 s, T07 5.5 s, T04 5.5 s). Segments after a cut that held: inserts with a named action (fingers loosen/close, wheel turning, a drop falling), walks, the handshake, and every close-up under 3 s. This is review6 item 1 confirmed at frame level: the model's own ~2-2.5 s rhythm; a still close-up with nothing to do is abandoned for the most recently shown picture, and the END pin at the take's last frame brings it back.

The prompt also invites the return: `<Picture 3> … each shot begins from its own panel; the panels after them show how [Shot 1] and [Shot 2] end` with the END cells appended **after the last start panel** — the strip reads left-to-right as a shot order in which the END frames come after the close-up.

### D4. Early cuts (iteration 3, and what iteration 5 will get back without the bracket)

Iteration 3 deltas: -11, -24, 0, -11, -24, -5, 0, -2, -14, -3, 0, -10, -12, -24, 0, -12. The six on-time cuts are the segments with continuous action up to the cut (T03 cab moving, T06 arrival, T08 walk, T11 three-shot with the hand, T18 handshake); the ten early ones are all stills (Watson close, two-shot, frontal, slab insert, Holmes bent, vessel). Same root as D3: a still segment is left early for the picture the model knows is coming.

### D5. Wording and the pre-roll pin, evaluated

- `[Shot k] At MM:SS.mmm, the shot cuts to` vs `cuts directly to`: no data separates them and none is needed — 100 % of landed cuts are one-frame hard cuts already. "Directly" would be a no-op. Keep the stamp; it is positive wording.
- The text stamp vs the pin frame: iteration 4 stamps equal `pin/24` exactly (03.208 = 77/24); iteration 3 stamps were the placed time (03.160) while the pin was on the grid (77) — 0.05 s apart, invisible. With a pre-cut pin the cut lands at -3..0 frames of the stamp (0.125 s), invisible. Without one it lands 0-24 frames early on a still segment (D4) — that is the visible error, and it is a picture problem, not a stamp problem.
- Pre-roll pin (target pinned at cut-4 AND cut): it is a bracket made of the target, so it cannot stop an early float (nothing holds the previous picture) and it doubles a soft row that the model rejected in T01 for a reason that lives in the prompt. It would move the landing to cut-7..cut-4 against the stamp. Not as a default. It is the right **retake escalation** for the "pin ignored" class (T09 +34, T13 +51): the same prompt with a new seed did not fix T01, and a heavier pin is the only lever left that costs nothing.

## THE CHECK — cut-landing gate

`transitions\cut_landing.py` (prototype for `studio/cut_landing.py`, called from `scripts/episode/take_dq.py` after `picture_dq`), tests in `transitions\test_cut_landing.py` (10 tests, synthetic signatures, no ffmpeg, no money).

```python
def cut_landing(video: Path, anchors: list, frames_dir: Path) -> dict
    # -> {"passed": bool, "reason": str, "cuts": [row per internal cut], "measured_cuts": [frame | None]}
    # row = {cut, target, pin, landed, delta, foreign_run, foreign_cell, pingpong, pingpong_to}

def classify(sig, own, other) -> list[dict]        # per frame: closest own cell, closest other/plate, foreign flag
def start_pins(anchors) -> list[(cell, frame)]      # first pin per cell, END cells excluded (internal cuts = [1:])
def landing(per_frame, anchors) -> list[dict]       # landed / delta / foreign run / ping-pong per cut
def verdict(rows) -> {"passed", "reason"}           # the gate
def token_start(frame) -> bool                      # 17c + {0,1,5,9,13}: replaces on_grid()'s "1 mod 4"
```

Measures, per internal cut: every frame at 24 fps (`ffmpeg -vf scale=192:336 -pix_fmt gray`, the same signature as `frame_match`), matched to the take's own cells (start + END) and to **every other Q cell and every `plate_*.png`** (the DQ's foreign set lacked the plates, which is why T01 read as "Q21_0").

Thresholds (calibrated on the 40 cuts on disk, `calibrate.txt`):

| measure | pass | honoured cuts | failures |
|---|---|---|---|
| `delta` = first frame on the target − pin | −4 … +6 frames | −3 … +1 | +34, +51, +37, +54; −5 … −24 (iteration 3) |
| `foreign_run` in [pin−24, pin+48] | ≤ 12 frames (0.5 s) | 0 … 7 (a 7-frame flicker of the cab against Q17_0: matcher noise) | 25, 30, 40, 51 |
| `pingpong` frames back on an earlier cell before the next start pin | ≤ 12 frames | 0 | 36, 56, 92, 134 |

Verdict order: foreign first (it also delays the landing), then landing, then ping-pong; the reason names the cut, the cell and the count.

Result on disk (`calibrate.txt`, 10/10 tests green): iteration 4 — PASS T03 T04 T05 T06 T10 T11 T12 T14 T17 T18 (the re-render that arrived during this review: -3, 0) T18_fail1 T20; FAIL T01 and T01_retake1 (40 / 51 frames of plate_criterion at cut 1), T02 (36 frames back on Q02_0E), T07 (92 frames back on Q08_0E at cut 2), T09 (landed +34), T13 (landed +51), T17_fail1 (30 frames of plate_bench). Iteration 3 — PASS T03 T06 T08 T11 T18 T19_fail1; FAIL the ten early cuts (-5 … -24), T02/T04 ping-pong (56 / 134 frames), T13 (14 frames of Q12_0) and T13_retake1 (25 frames of Q16_0). Every FAIL is a take a reviewer or the owner flagged; every PASS held on screen. The DQ on disk passed all of T02, T07, T09, T13 and T17_fail1.

`measured_cuts` is written for the assembler (F4): the frame the cut actually landed on, or None.

Tests (`test_cut_landing.py`): classify names the closest own cell and flags a plate; start_pins drops END cells and repeats; on-pin passes; −3 passes and +34 fails naming "landed 34"; −11 fails; 40 frames of a plate fails naming the plate; 36 frames back fails naming the earlier cell; a 6-frame flicker passes; never landing fails; `token_start` follows the (1,4,4,4,4) cycle.

## THE FIX

Ranked by what the viewer sees; F1-F3 are prompt/strip/plan changes with no render cost beyond iteration 5's re-render, F4 is a no-render change.

**F1. Scope the location subject to the shots that show the room; give inserts a positive frame sentence** (`studio/episode_ref_official.py`). Removes the plate intrusion (T01 both attempts, T17_fail1, iteration-3 T03).

- `retention()`: the location line lists only segments whose frame text is not an insert / extreme close-up:
  ```python
  INSERT = ("insert", "extreme close", "close on the hand", "hand on", "boot on", "the vessel")
  room = [f"[Shot {i}]" for i, seg in enumerate(segs, 1) if not any(w in seg.frame.lower() for w in INSERT)]
  f"<Subject {plate}> (appears in {', '.join(room)}): fully_preserved - the room, its furniture, walls, windows and light."
  ```
  and add one line for the inserts: `<Subject {plate}> ([Shot 2]): the room is present only as the mahogany counter-top and the brass rail under the hand.` (built from the frame text's first noun phrase after the colon).
- `description()`: for `hidden` segments replace `The people are seen from behind, in profile or far off.` by `The frame holds only what the panel shows, filling it edge to edge.` — true for an insert and for a from-behind shot alike, and it names no people for the model to go looking for.
- `voice_events()`: clip every narration span to its segment: `t1 = min(t0 + dur, segment_end)`; a line that crosses the cut gets a second event in the next segment. T01's "lips closed until 05.020" then ends at 03.208 in [Shot 1] and the insert says "From 03.208 to 05.020 the hand is the only thing in frame; the action keeps moving at normal speed."

**F2. Strip in time order, with the panel order said the same way** (`takes_r2v.reference_strip`, `ro.subjects`). Removes the "END frames are later shots" reading behind the T02 / T07 returns.

- Order: `[Q07_0, Q07_0E, Q08_0, Q08_0E, Q08_1]` (each segment's START then its END, in time order), never START panels followed by all the ENDs.
- Sentence: `<Picture 3> shows the take's panels in time order, left to right: each shot begins on its first panel; a shot with two panels ends on its second, and the next shot begins on the panel after that.` (positive, no "never"/"no").

**F3. No still segment longer than 2.5 s after an internal cut** (plan lint in `scripts/episode/shots.py` or the episode skill's plan gate). Removes the ping-pong (D3) and most of the early cut (D4) at the source, and it is the owner's 15:25 note in a measurable form: a segment whose `motion` has no visible-action verb (`walk, step, turn, lift, raise, lower, push, open, set, take, climb, plant, pass, fall, drop, pour, shake, grip, wipe`) and whose duration to the next cut or take end is > 2.5 s FAILS the plan. Today that fails S02.1 (4.35 s "an odd measuring look"), S08.1 (5.5 s "the half smile goes"), S12.1, S17.2 — exactly the takes that ping-ponged or froze. Fix each by a named action lasting to the cut, or a second cell.

**F4. Absorb the residue in the cut, not in a retake** (`scripts/episode/assemble.py`, `take_dq.py`). With the pre-cut pin gone (MOTION), an honoured cut may land a few frames off; write `measured_cuts` from THE CHECK into `shots.json` and have `assemble.py` place the shot boundary and any word-tied line at the measured frame when `|delta| <= 6`; a larger delta is already a FAIL and goes to retake. This is review6 item 8, now with the measurement in hand.

**F5. Retake escalation for a pin the model ignored** (`takes_r2v.main --retake`): on a FAIL with reason "landed +N" (T09, T13 class), the retake pins the target at `cut-4` **and** `cut` (the pre-roll) and moves the stamp to `(cut-4)/24`; on a FAIL with a plate reason, the retake is pointless until F1 is in (both T01 attempts landed the plate at frame 74).

**Not changed:** the `cuts to` wording (D5); `on_grid` may stay (harmless) but its docstring should say the truth: `FRAME_PER_TOKEN = (1,4,4,4,4)`, token starts at `17c + {0,1,5,9,13}`, and a pin is a conditioning row at `5/3 * frame`, not a latent — `token_start()` in `cut_landing.py` is the correct predicate if anyone wants pins on token starts.

## Files

- `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\transitions\cutscan.md` — the 24 fps landing table, iteration 4 (every pin incl. END pins; the real cuts are the rows whose target is a new cell)
- `...\transitions\cutscan3.md` — the same for iteration 3
- `...\transitions\cutscan.json`, `cutscan3.json` — per-frame closest cell / foreign match for every take
- `...\transitions\dense_T07_steps.png`, `dense_T01_plate.png`, `dense_T01r_plate.png`, `dense_T02_pingpong.png`, `dense_T09_late.png`, `dense_T13_late.png`, `dense_T05_minus3.png` — labelled frame strips (pins in yellow)
- `...\transitions\criterion_cells.png` — plate_criterion and the six Criterion cells
- `...\transitions\cut_landing.py`, `test_cut_landing.py` — THE CHECK and its tests
- `...\transitions\calibrate.py`, `calibrate.txt` — the gate on every multi-cut take of iterations 3 and 4
