D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\identity.md

# IDENTITY — do the three faces stay the same person, and what catches a slip

Task force member: IDENTITY. Episode `library\20260822113400_a-study-in-scarlet\episodes\ep01`,
iteration 4 (`shots_r2v\`, 19 takes + 3 retake/fail files) against iteration 3 (`shots_r2v_v5\`, 18 + 4).
Measured with a real face embedder (facenet-pytorch: MTCNN detector + InceptionResnetV1/VGGFace2), CPU,
free, in a scratch venv that does not touch the repo. 5 frames per take (2/25/50/75/98 %), 190 frames,
77 s. Prototypes, frames, sheets and JSON under
`D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\identity\`.

## Short answer

- **Iteration 4: yes.** Every readable face in every take is the cast sheet's man: Watson 0.81–0.94,
  Holmes 0.73–0.77, Stamford 0.74–0.90 cosine to his sheet (cast-vs-cast is 0.20 / 0.08 / −0.15, so
  these are unambiguous). No stranger, no within-take drift (all in-segment first→last ≥ 0.81, most ≥ 0.94).
- **Iteration 3 had one real slip and one invented man**, and the gate catches both and nothing else:
  T09's Watson turns into a different man inside one pinned segment (in-segment drift 0.72; review6's
  "pomaded flat, narrower face"), and T21_fail1 grows a stranger at frame 3 (best match 0.43).
  Review6's other call, the S15 push-in "widening" Watson, is the same man (drift 0.94): a framing slip,
  not an identity slip, and iteration 4's T16 (static) holds it at 0.98.
- **But iteration 4 held identity by luck, not by reference.** 6 of 19 takes put a full-face Watson or
  Stamford on screen with NO cast sheet among the refs (T02, T06, T07, T10, T12, and the failed T17):
  the face is copied second-hand from the drawn cell pinned at the segment start, and is unanchored
  after it. Iteration 3's real slip (T09) is exactly this class: the plan's cut says
  `faces: ["john_watson"]`, and `faces_of()` never reads cut faces, so no `char-john_watson.png` went in.
  The same hole is open in iteration 4 (shots 6, 10, 12, 21) and did not bite this time.

## DIAGNOSIS

### 1. The mechanism (the brick)

A take's refs are `[cast sheet per face] + plate + strip`, and the faces come from
`scripts\episode\takes_r2v.py:64`:

```python
def faces_of(shots: list) -> list[str]:
    seen: list[str] = []
    for shot in shots:
        for who in shot.faces:          # <- shot-level only; shot.cuts[*].faces never read
            ...
    return seen[:MAX_FACES]
```

Two layers of omission feed it:

| layer | shots (iteration 4 plan.json) | what is on screen |
|---|---|---|
| cut `faces` set, ignored by `faces_of` | 6, 10, 12, 21 (cut = "Close on Watson" / "Medium close-up of Watson") | Watson full face, no Watson sheet in refs |
| `faces: []` at both levels although the text puts a face in frame | 2 (cut "Close on Stamford… over the rim of his raised glass"), 5 ("Watson in profile"), 6 ("Stamford in strict profile"), 8 (cut "Close on Stamford"), 9 (cut "Stamford in strict profile"), 12 (cut "…Watson and Stamford"), 14 ("edge of the thin moustache"), 21 ("Stamford… strict profile") | Stamford close-ups and profiles, no Stamford sheet in refs |

Iteration 3's plan_v4.json has the same first layer at shots 5, 9, 11 — T09 is shot 9.

The prompt builder (`studio\episode_ref_official.py`) already knows about cut faces: `retention()`
walks `c.faces`, and `description()` writes `On camera: John Watson` (bare name, because
`subject_of()` finds no `<Subject k>` for him) in T06, T10, T12. So the prompt names a man the
picture set does not define. The storyboard cells DO carry the right face (the drawer worked from the
cast sheets: `identity\cells_unreferenced.png`), which is why the pins hold identity at segment starts.

### 2. The cast sheet "variants" are one file

`refs\characters\`: `char-john_watson_{bench,corridor,criterion,lab}.png` are byte-identical
(md5 6021ad83…), a full-body bareheaded Watson whose face is 22 % of frame height against 42 % on the
base sheet; `char-sherlock_holmes_{bench,lab}.png` are identical (hatless). This did not hurt in
practice (Watson referenced through the lab copy scores 0.81–0.92) — recorded so nobody expects
per-setup wardrobe from them.

### 3. Per-take table, iteration 4 (readable = face ≥ 12 % of frame height and yaw ≤ 0.5; cosine to the best of that character's sheets; drift = first vs last readable frame of the same character inside one pinned segment)

| take | plan faces | refs (cast) | readable faces seen (frames) | min cos | drift (in-segment) | flags |
|---|---|---|---|---|---|---|
| T00 | Stamford | Stamford | Stamford (5) | Stamford 0.82 | Stamford 0.94 | ok |
| T01 | Watson | john_watson_criterion | Watson (2) | Watson 0.92 | Watson 0.97 | ok |
| T01_retake1 | Watson | john_watson_criterion | Watson (2) | Watson 0.92 | Watson 0.96 | ok |
| T02 | [] | - | Watson (2), Stamford (5) | Watson 0.69, Stamford 0.74 | Watson 0.92, Stamford 0.97 | UNCAST Watson; UNCAST Stamford; UNREFERENCED Watson; UNREFERENCED Stamford |
| T03 | [] | - | none | - | - | ok |
| T04 | Watson | Watson | Watson (2) | Watson 0.86 | Watson 0.93 | ok |
| T05 | [] | - | none (Watson in strict profile, yaw 0.67–0.80, cos 0.62–0.66) | - | - | ok |
| T06 | [] | - | Watson (3) | Watson 0.86 | Watson 0.98 | UNREFERENCED Watson |
| T07 | [] | - | Stamford (2) | Stamford 0.89 | - | UNCAST Stamford; UNREFERENCED Stamford |
| T09 | [] | - | none (Stamford profile, yaw 0.77–0.88, cos 0.68–0.72) | - | - | ok |
| T10 | [] | - | Watson (3) | Watson 0.85 | Watson 0.97 | UNREFERENCED Watson |
| T11 | [] | - | none | - | - | ok |
| T12 | [] | - | Watson (3), Stamford (3) | Watson 0.87, Stamford 0.81 | Watson 0.96, Stamford 0.98 | UNCAST Stamford; UNREFERENCED Watson; UNREFERENCED Stamford |
| T13 | [] | - | none (three-shot, faces 8–10 % of frame) | - | - | ok |
| T14 | Holmes | sherlock_holmes_lab | Holmes (2) | Holmes 0.76 | - | ok |
| T16 | Watson | john_watson_lab | Watson (5) | Watson 0.81 | Watson 0.98 | ok |
| T17 | [] | - | none | - | - | ok |
| T17_fail1 | [] | - | Holmes (1) | Holmes 0.71 | - | UNCAST Holmes; UNREFERENCED Holmes |
| T18_fail1 | Holmes | sherlock_holmes_bench | Holmes (2) | Holmes 0.73 | Holmes 0.81 | ok |
| T20 | Watson | Watson | Watson (5) | Watson 0.81 | Watson 0.94 | ok |
| T22 | Stamford | Stamford | Stamford (5) | Stamford 0.77 | Stamford 0.96 | ok |

Iteration 4: 0 STRANGER, 0 DRIFT, 0 WEAK; 8 UNREFERENCED faces across 6 takes, 5 UNCAST.
(Aside, not identity: `shots_r2v\` holds `T18_fail1.mp4` but no `T18.mp4`, while `T18.dq.json` says
`passed: true` with `picture_ok: false`; and `.dq.json` stores an absolute `strip` path.)

### 4. Per-take table, iteration 3

| take | plan faces | refs (cast) | readable faces seen (frames) | min cos | drift (in-segment) | flags |
|---|---|---|---|---|---|---|
| T00 | Stamford | Stamford | Stamford (5) | Stamford 0.72 | Stamford 0.91 | ok |
| T01 | Watson | john_watson_criterion | Watson (2) | Watson 0.83 | Watson 0.92 | ok |
| T02 | [] | - | Stamford (3) | Stamford 0.77 | Stamford 0.90 | UNCAST Stamford; UNREFERENCED Stamford |
| T03 | [] | - | none | - | - | ok |
| T04 | Watson | Watson | Watson (1) | Watson 0.87 | - | ok |
| T05 | [] | - | Watson (2) | Watson 0.83 | Watson 0.95 | UNREFERENCED Watson |
| T06 | [] | - | none | - | - | ok |
| T08 | [] | - | none (Stamford profile 0.71→0.51) | - | - | ok |
| T09 | [] | - | Watson (2) | Watson 0.74 | **Watson 0.72** | UNREFERENCED Watson; **DRIFT** 0.72 < 0.75 |
| T10 | [] | - | none | - | - | ok |
| T11 | [] | - | Watson (1), Stamford (1) | Watson 0.70, Stamford 0.75 | - | UNCAST Stamford; UNREFERENCED Watson; UNREFERENCED Stamford |
| T13 | Holmes | sherlock_holmes_lab | Holmes (3) | Holmes 0.61 (mid-word, mouth open) | Holmes 0.81 | ok |
| T13_retake1 | Holmes | sherlock_holmes_lab | Holmes (2) | Holmes 0.69 | Holmes 0.85 | ok |
| T15 | Watson | john_watson_lab | Watson (5), Stamford (2) | Watson 0.71, Stamford 0.82 | Watson 0.94, Stamford 0.94 | UNCAST Stamford; UNREFERENCED Stamford |
| T15_fail1 | Watson | john_watson_lab | Watson (5), Stamford (2) | Watson 0.68, Stamford 0.86 | Watson 0.94, Stamford 0.97 | UNCAST Stamford; UNREFERENCED Stamford |
| T16 | [] | - | none | - | - | ok |
| T17 | Holmes | sherlock_holmes_bench | Holmes (5) | Holmes 0.63 | Holmes 0.94 | ok |
| T18 | [] | - | none | - | - | ok |
| T19 | Watson | Watson | Watson (2) | Watson 0.82 | Watson 0.91 | ok |
| T19_fail1 | Watson | Watson | Watson (3) | Watson 0.69 | Watson 0.94 | ok |
| T21 | Stamford | Stamford | Stamford (4) | Stamford 0.72 | Stamford 0.97 | ok |
| T21_fail1 | Stamford | Stamford | Stamford (3) | Stamford 0.67 | Stamford 0.93 | **STRANGER** frame 3, best Holmes 0.43 |

Iteration 3 → 4: the two real defects are gone (T09 was replaced by a static corridor MCU, T10, drift
0.97; T21_fail1 was retaken). Referenced faces score higher in iteration 4 (Watson min 0.81 vs 0.68–0.74,
Stamford 0.77–0.82 vs 0.67–0.72) — the END pins that froze motion (motion_scan) also froze faces.

### 5. The flagged frames, looked at (`identity\drift_pairs.png`, `identity\evidence_eye.png`)

| flag | frames | real? |
|---|---|---|
| iter3 T09 DRIFT 0.72 | `identity\frames3\T09_2.png` (Watson, full hair, moustache) vs `T09_4.png` (hair slicked flat, longer face, thinner moustache) | **Real.** A different man for the last 2 s. Same finding as review6 §4. |
| iter3 T21_fail1 STRANGER 0.43 | `identity\frames3\T21_fail1_4.png` | **Real** — an invented man walks in at the tail; the take already failed DQ. |
| iter3 T15 "widened" (review6) | `identity\frames3\T15_2.png` vs `T15_4.png`, drift 0.94 | **Not identity.** Same man, closer; the push-in is the defect and iteration 4 removed it. |
| iter4 T02 Stamford, two-shot → close (across-cut cosine 0.68) | `identity\frames4\T02_1.png` vs `T02_4.png` | **Not a slip.** Same round face; the drop is the framing change at the cut, which is why drift is measured inside a segment. |
| iter4 T05 / T09 / iter3 T08 profiles at 0.51–0.72 | strict profiles, yaw ≥ 0.67 | **Not judged.** The embedder is unreliable on profiles and a viewer reads little identity there; excluded by the yaw rule, counted but not scored. |
| iter4 T13 / iter3 T11 three-shots at 0.46–0.72 | faces 8–10 % of frame | **Not judged.** Far off; below the readable size. |

### 6. The crude fallback does not work — recorded so nobody re-tries it

`identity\identity_crude.py`: fixed head window + `studio\frame_match.signature` against head crops of
the sheets. Cast-vs-cast on the sheets themselves: Watson–Holmes 0.63. On frames: T00 (plainly Stamford)
scores best as Holmes 0.24; T16 (plainly Watson) best as Stamford 0.32. It measures layout and light,
not faces. Without cv2 there is no detector either. An embedder is required.

## THE CHECK

### Install (one line, repo venv, free; ~110 MB of weights fetched once)

`facenet-pytorch==2.6.0` pins `torch<2.3`, `numpy<2`, `Pillow<10.3` — all three collide with the
repo's pins, so it cannot go through `uv add`. Dry-run verified against the repo venv:

```
uv add torchvision==0.29.0                       # resolves cleanly against torch==2.14.0 (1 package)
uv pip install --no-deps facenet-pytorch==2.6.0  # its code needs only torch, torchvision, PIL, numpy
uv sync --all-groups                             # uv add strips the music/voice groups (memory note)
```

Weights: `%USERPROFILE%\.cache\torch\checkpoints\20180402-114759-vggface2.pt` (already cached on this
machine by this review). The MTCNN weights ship inside the package. First `import torch` on a cold disk
took 55 s under today's load; warm, 1.8 s. The embedder handles a 768×1344 frame in ~0.4 s on CPU.

Proven today in `identity\.venv` (torch 2.2.2+cpu): cast × cast on the sheets

```
                 watson  holmes  stamford
john_watson        1.00    0.20     0.08      (base vs _lab copy: 0.83)
sherlock_holmes    0.20    1.00    -0.15      (base vs _lab copy: 0.87)
stamford           0.08   -0.15     1.00
```

### Gate 1 — `studio\identity_gate.py` (prototype: `identity\identity_gate.py`, tests `identity\test_identity_gate.py`, 12 passing, no model, no file, no credit)

```python
READABLE = 0.12   # face box height / frame height; smaller = far off, not judged
FRONTAL  = 0.50   # yaw = |nose_x - eye_mid_x| / eye_distance from MTCNN landmarks; larger = profile, not judged
MATCH    = 0.60   # cosine to the character's best sheet: at/above = that character
STRANGER = 0.45   # below = nobody from the cast; between STRANGER and MATCH = WEAK (advisory)
DRIFT    = 0.75   # cosine first vs last readable frame of one character WITHIN ONE PINNED SEGMENT

@dataclass
class Face: k: int; h: float; scores: dict[str, float]; vec: np.ndarray | None; yaw: float; seg: int

def readable(faces) -> list[Face]                   # h >= READABLE and yaw <= FRONTAL
def identify(face) -> str | None                    # best character, or None below STRANGER
def unreferenced(faces, refs) -> list[str]          # on screen, cast sheet not among the take's refs
def uncast(faces, expected) -> list[str]            # on screen, not in the plan's faces (shot + cuts)
def drift(faces) -> dict[str, float]                # per character, min over segments of cos(first, last)
def judge(faces, expected, refs) -> Verdict         # .present {who: frames}, .flags [...], .ok
```

Calibration (all takes on disk, both iterations): readable faces of the right man never score below
0.61 (iter3 T13 f3, Holmes mid-word) and referenced ones sit 0.72–0.94; the strangers score 0.43,
0.21, 0.03, −0.04; the same man in strict profile scores 0.51–0.69 (hence FRONTAL); the same man at
8–10 % of frame scores 0.46–0.72 (hence READABLE). In-segment drift of the right man is ≥ 0.81 in every
real take; the one real slip is 0.72; across a cut the same man can read 0.68 (iter4 T02), which is why
drift is per segment. With these numbers the gate flags exactly iter3 T09 (DRIFT) and iter3 T21_fail1
(STRANGER) and nothing in iteration 4 except the structural UNREFERENCED/UNCAST flags.

Verdicts: STRANGER or DRIFT → the take fails (retake). WEAK → advisory, strip it for the eye.
UNREFERENCED / UNCAST → not a render fault: a plan/refs fault, and Gate 2 raises it before the render.

### Gate 2 — plan lint, before any render (free, no model)

`faces_of()` must return every face of the take's shots AND their cuts (F1 below), and the plan's
`faces` must name every character whose face the frame text puts on screen:

```python
FACE_WORDS = r"(close(-up)? (on|of)|medium close(-up)? of|in (strict )?profile|his (round |gaunt )?face|eyes|mouth|moustache)"

def faces_named(text: str, cast: list[str]) -> list[str]:
    """Characters whose face the frame text puts on screen: named within a FACE_WORDS clause,
    and not 'seen from behind' / 'back' / 'shoulder' in that clause."""

def lint_faces(shot) -> list[str]:
    """faces_named(shot.frame) - shot.faces, plus the same for each cut: what the plan forgot."""
```

Tests: `"Close on Stamford ... over the rim of his raised glass"` → `["stamford"]`;
`"Medium shot from behind: Stamford a pace ahead, Watson bareheaded"` → `[]`;
`"Watson in profile, brown bowler on ... Stamford's black shoulder and round clean-shaven face, soft"` →
`["john_watson", "stamford"]`; `"the edge of the thin moustache at the top of frame"` → `["john_watson"]`
(the only moustache in the cast). On the current plan.json this lint lists exactly the second-layer
omissions in §1: shots 2, 5, 6, 8, 9, 12, 14, 21.

### Gate 3 — `studio\identity_faces.py` (the only file that imports the library)

```python
def faces_in(image: Image.Image) -> list[Face]      # MTCNN(keep_all, landmarks) + resnet, unit vectors, yaw
def cast_bank(book: Path, cast: list[str]) -> dict[str, list[np.ndarray]]   # every char-<who>*.png, largest face
def score(vec, bank) -> dict[str, float]            # max cosine per character over his sheets
```

Wiring in `scripts\episode\take_dq.py`: `picture_dq()` already extracts `SAMPLES = 8` frames per take
to `work_r2v\dq\take_T??_k.png` and knows each frame's expected anchor (`expected_anchor`, the
segment). Add `identity_dq(frames, anchors, expected, refs, bank) -> dict` that runs `faces_in` on
those same 8 PNGs (seg = `segment_of(expected_anchor)`), calls `judge`, and writes
`dq["identity"] = {"present": ..., "min_cos": ..., "drift": ..., "flags": [...], "identity_ok": bool}`;
`passed` requires `identity_ok`. Cost per take: 8 × 0.4 s ≈ 3 s, no extra ffmpeg. Local Ollama-style
nondeterminism does not apply — the embedder is deterministic — so its tests run with a recorded
`identity_scan.json` fixture (`identity\identity_scan.json`, 190 frames with vectors) and never load the
model: mark the one model-loading test `@pytest.mark.local`.

## THE FIX

### F1 — `scripts\episode\takes_r2v.py` `faces_of()`: read the cuts (the T09 class of slip)

```python
def faces_of(shots: list) -> list[str]:
    seen: list[str] = []
    for shot in shots:
        for who in list(shot.faces) + [w for c in shot.cuts for w in c.faces]:
            if who not in seen:
                seen.append(who)
    return seen[:MAX_FACES]
```

With this alone, iteration 4's T06, T10, T12 and T20 (shot 21's cut) get `char-john_watson_<setup>.png`
in refs, `<Subject 1> is John Watson in <Picture 1>` in the prompt, and `On camera: <Subject 1>` instead
of the bare name — no other prompt code changes, `subjects()` / `retention()` / `subject_of()` already
key off this list. `MAX_FACES = 2` stays: no take exceeds Watson + Stamford; refs go to at most
2 + plate + strip = 4 of the workflow's 8 slots.

### F2 — `plan.json` `faces` (the second layer), per shot

| shot | add to `faces` | why (frame / cut text) |
|---|---|---|
| 2 (cut) | `stamford` | "Close on Stamford … over the rim of his raised glass" |
| 5 | `john_watson` | "Watson in profile, brown bowler on" (profile: the sheet still binds the hair, brow, moustache) |
| 6 | `stamford` (Watson already on the cut) | "Stamford in strict profile" |
| 8 (cut) | `stamford` | "Close on Stamford at the top of the worn stone steps" |
| 9 (cut) | `stamford` | "Close on Stamford in strict profile walking" |
| 12 (cut) | `stamford` (Watson already on the cut) | "Medium close-up of Watson and Stamford" |
| 14 | `john_watson` | "the edge of the thin moustache at the top of frame" — an ECU of his face |
| 21 | `stamford` (Watson already on the cut) | "Stamford nearer the camera in strict profile" |

Shot 13 (three-shot, faces 8–10 % of frame) stays `[]`: below readable size, and three sheets would
exceed MAX_FACES. Gate 2 enforces this table automatically from the text.

### F3 — references per take, iteration 5 (after F1 + F2)

| take | refs today | refs after | prompt subject lines gained |
|---|---|---|---|
| T02 criterion | plate, strip | + `char-stamford.png` | `<Subject 1> is Stamford in <Picture 1>`; "On camera: <Subject 1>" on the close |
| T05 cab | plate, strip | + `char-john_watson.png` | Watson defined for the profile |
| T06 cab | plate, strip | + `char-stamford.png`, `char-john_watson.png` | both defined; cut close "On camera: <Subject 2>" |
| T07 gateway (shots 7, 8) | plate, strip | + `char-stamford.png` | the steps close-up |
| T09 corridor | plate, strip | + `char-stamford.png` | the walking profile |
| T10 corridor | plate, strip | + `char-john_watson_corridor.png` | the dissecting-room MCU |
| T12 lab | plate, strip | + `char-john_watson_lab.png`, `char-stamford.png` | the doorway MCU |
| T14 lab (shots 14, 15) | holmes_lab, plate, strip | + `char-john_watson_lab.png` | the moustache ECU is Watson's |
| T20 gateway (shots 20, 21) | watson, plate, strip | + `char-stamford.png` | shot 21's profile |

The other 10 takes are unchanged. The strip (`ref_take_NN.png`, the take's own cells + END frames) stays
exactly as it is: it is what carried identity in iteration 4 and it already holds the drawer's faces.

### F4 — cast sheet variants (optional, ~$0.20 each, owner's call — no measured need)

The four Watson variants are one full-body image with the face at 22 % of frame height. A
head-and-shoulders variant like the base sheet (face at 42 %) would give the reference more face
pixels; measured today, Watson referenced through the copy still scores 0.81–0.92, so this is a
nice-to-have, not a fix. If done: one gpt-image call per real variant
(`scripts\episode\cast_variants.py <codex_id> john_watson lab "bareheaded, bowler in hand, medium
close-up"`), then delete the three identical copies and let `cast_sheet()` fall back to the base sheet
for bench/corridor/criterion (it already does when the variant file is absent).

### F5 — on a DRIFT or STRANGER verdict

Retake with the same seed + 1 and the (now complete) refs; the failing frame index names the segment,
so if it recurs, split that segment with one more pinned cell (the cell_scale rule) — an unpinned
tail is where both of iteration 3's slips lived (T09 tail 63.2–65.2 s, T21_fail1 tail).

## Files produced (all under `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\8a764c01-76e4-437c-b43b-8b6a5e4a5481\scratchpad\review8\identity\`)

- `identity_gate.py` — the gate (prototype for `studio\identity_gate.py`), calibrated thresholds
- `test_identity_gate.py` — 12 tests, pass in 0.07 s in the repo venv, no model
- `identity_scan.py` — the scanner (detector + embedder + yaw), run in `.venv\` (scratch, facenet-pytorch)
- `identity_scan.json` — 190 frames: boxes, size, yaw, per-character cosines, 512-d vectors (fixture for the gate tests)
- `apply_gate.py`, `identity_verdicts.json`, `verdicts.txt`, `tables.md` — the gate applied to both iterations
- `identity_crude.py`, `identity_crude.json` — the crop-and-compare fallback and its failure
- `frames4\T??_k.png`, `frames3\T??_k.png` — the 5 sampled frames per take, both iterations
- `sheet_frames4_0.png`, `sheet_frames4_1.png`, `sheet_frames3_0.png`, `sheet_frames3_1.png` — contact sheets, every take
- `cells_unreferenced.png` — the storyboard cells behind the unreferenced faces
- `evidence_eye.png`, `drift_pairs.png` — the flagged/suspect faces beside their cast sheets at full resolution
- `durations.json`, `smoke.py`, `conv.py`, `scan.log` — support


---

# Episode 10 populations and the recalibration (2026-09-16)

Source: dq10 analyst A (`scratchpad\dq10\A.md`, `scan.log`, `scan2.log`, `identity_scan_ep10.json`):
the 30 kept ep10 takes at 6 frames each, facenet-pytorch (MTCNN + InceptionResnetV1/VGGFace2) on
CPU in a scratch venv, scored against the nine cast pictures `char-{brigham_young,john_ferrier,
lucy_ferrier}{,_indoor,_outdoor}.png`.  Cast x cast: Young x Ferrier -0.01, Young x Lucy -0.01,
Ferrier x Lucy 0.15 -- and Ferrier x Stangerson 0.62-0.66, which is the next episode's problem.

## The populations, readable frames against the character's best sheet

| character | takes | cosine | notes |
|---|---|---|---|
| Brigham Young | 11 (T04, T05, T07, T10, T13, T15, T16 + hands) | 0.67-0.89 | never below MATCH; T04 at h 0.19 is the low end |
| John Ferrier | 15 | 0.56-0.85 | 0.56-0.60 only at h 0.12-0.13 (T06); T12 f3 WEAK 0.59 at h 0.15 |
| Lucy Ferrier | 5 (T21, T22, T27, T29, T31) | 0.58-0.79 | 0.49 with a hand over the eye (T27 f1); 0.47 in profile (T29 f5) |
| strangers | none | -- | no STRANGER, no UNCAST but the S29 insert intrusion |

## What the ep01 constants did on ep10

| verdict | takes | by eye |
|---|---|---|
| STRANGER (hard) | none | correct |
| DRIFT (hard), first-vs-last | T06 Ferrier 0.60; T21 Lucy 0.69; T29 Lucy 0.43; T33 Ferrier 0.67 | all four the same person: T29 f5 a full profile passed by yaw 0.44 < 0.50; T33 f4 at yaw 0.43 (frontal-only pair 0.91); T21 head bowed (pitch); T06 faces at the 0.12 floor with the coat changing |
| WEAK (advisory) | T06 f1/f3, T12 f3, T21 f0, T27 f1, T29 f5 | small, occluded or turned |

Four good takes (~11 min of 4090 each) refused, no swap caught, because there was none.  The
ep01 sentence "real pairs >= 0.81" does not survive a pitched or turned head: same-person
first-vs-last pairs measure 0.60-0.71 whenever the face is <= 0.14 of frame, bowed, or past
yaw 0.4.

## The recalibration (studio/identity_gate.py)

| constant | was | now | why |
|---|---|---|---|
| `READABLE` | 0.12 | 0.15 | T06's 0.12-0.13 faces are the only frontal faces under 0.60 for the right man |
| `FRONTAL` | 0.50 | 0.35 | T29 f5 (0.44) and T33 f4 (0.43) are profiles by eye; removes T29 (n < 2) and lifts T33 0.67 -> 0.91, T27 0.55 -> 0.87 |
| `drift()` | first vs last | min cosine of each readable frame to the run's MEDIAN embedding when n >= 3; the pair when n = 2 | same-person minimum-to-median 0.82-0.98 in every take (T06 0.84, T21 Lucy 0.88, T33 0.82); the pair is the statistic most sensitive to pose.  n = 2 keeps ep01's one true slip (T09, two frames, 0.72) |
| `ARMED` | -- | False | the row stays ADVISORY for one episode: findings go to `flags` and `note`, `hard` is empty |

With the three changes the gate flags nothing on ep10 and still flags ep01's T09 (two frames,
0.72 < 0.75) and T21_fail1 (stranger, 0.43 < 0.45).

## What is and is not in the venv

`opencv-python-headless==5.0.0.93` is in the lock with YuNet (`studio/models/yunet.onnx`) for the
face-at-end row (`studio/face_end.py`): boxes and five landmarks, no embedding.  facenet-pytorch
is not, so `identity_gate.observe` is still the placeholder and the row still says "not
measured"; the measurer, when written, is the forty lines of `dq10\A\scan.py` (`embed`, `yaw`,
`bank_of`, per-segment sampling) on the recipe in the module docstring.

## Seen and not measured

Grooming is where ep10 actually drifts -- T31's beard short and black, T33's trimmed and grey by
3.9 s, T21's hair sandy at 4.9 s, T06's coat check -> plain -- and the embedder scores them 0.79 /
0.67 / 0.76 / 0.60 because it is built to ignore hair and beard.  That is a WARDROBE-row problem
(analyst A's first improvement), not an identity-row problem.
