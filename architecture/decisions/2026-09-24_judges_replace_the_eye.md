# Judges replace the eye — every taste gate in the refs and episode lines is automated

Decision id: `2026-09-24-automate-the-taste-gates`
Status: **DECIDED** by the owner's instruction, 2026-09-24 ("It says there are human
eye checks, DQ checks, gates — remove them. We should automate them all, using agents
or existing ComfyUI models. Fix all of them."), with the design decisions delegated.
Build plan: [../plan/2026-09-24_judges_replace_the_eye_build.md](../plan/2026-09-24_judges_replace_the_eye_build.md).
Amends §3 of [2026-09-24_future_departments.md](2026-09-24_future_departments.md):
LOOK, PLAN, EYE (board, takes) and MASTER are judged, not signed; the owner audits
after the fact; PUBLISH, MONEY, OVERRIDE, the synthetic declaration and RENDER_HOLD stand.

How it was made: five research reports (the picture eye; video take QC; plan and
LOOK judges; the calibration set; integration and ladders) and a chair's ruling on
every disagreement. Book-neutral in its rules; §1.4, §2 and §6 cite artefact ids
(`epNN TNN`) as the measurement record they are — the casebook's keys — never as story.

Chair's ruling, 2026-09-24, over reports A (picture eye), B (take QC), C (plan/look
judges), D (calibration), E (integration). Read-only against `master` at `4c0f5ec`.
Every path below is relative to `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio`.

## 0. The instruction, and the honest reconciliation

The owner's words: "It says there are human eye checks, DQ checks, gates — remove
them. We should automate them all, using agents or existing ComfyUI models. Fix all
of them." He delegated every decision. So the rule of this design is:

> **No step of the refs or episode line may park on a human.** The only signatures
> left in the studio are going PUBLIC (Distribution, not these lines) and paid credits
> (repo invariant; these lines spend none). GPU time is a ceiling, not an approval.

Four of five reports found the evidence base thin and said "shadow first, flip by a
count rule". Their finding is true and it does not change the ruling; it changes what
we *claim*. The reconciliation:

1. **Where the human sits moves; what the machine can promise does not grow.** The
   line runs unattended with machine judges, cause-directed ladders and terminal
   actions that need nobody. The owner's role moves AFTER the fact and OFF the
   critical path: an **audit sheet** per unit (flags, contact sheet, strips, master
   link, a random sample of passes) that he may open whenever he likes. His findings
   go into the casebook and re-calibrate the judges. No step reads the audit sheet;
   it is never a gate.
2. **A judge never signs silently.** Every terminal rung writes a verdict file with
   `verdict: flagged`, the faults listed, `signed_by: judge:<name>@<version>`, and an
   audit-sheet row. The next step proceeds on `pass` or `flagged`; it still refuses a
   `fault` (only a human could write one now, and none will).
3. **"Shadow" is redefined.** It no longer means "a judge beside a human". It means a
   NEW judge version running beside the CURRENT judge version on the same artefacts,
   writing a sidecar and a bench row, promoted by the bench, never by feel.
4. **What will be approved wrongly at first**, said plainly:
   - Faults of classes nobody has named. The fence (ep09 T02) was one; the next will
     be another. Recall on unnamed classes is 0 by construction. Measured by the
     *owner-finding rate on audited units* (A §5's recall estimator): findings per
     audited unit, per class, from the casebook.
   - Story and taste residue: the plan critic is calibrated on five plans (two bad,
     two good, one with three named faults); the master "story" field checks that the
     plan's turn verb is *visible*, not that it *lands*.
   - Hats, invented landmarks, posture-by-keypoint, framing size, world rotation,
     mouth-envelope lag: 1-3 owner positives each; walls one take wide. They will
     both miss and false-refuse. Their cost is bounded (at most two cheap rungs,
     then a flag), never a block.
   - Style drift across a pack (LOOK): two books of evidence; flag only.
   - Small or profile faces the embedder cannot read: "cannot tell", which is a fault
     on a close and nothing on a wide.
   Measured by three numbers per judge, reported in `docs/calibration/<judge>.md`:
   **recall on owner catches** (must be 1.0 on every casebook row of its classes;
   the ratchet test refuses a commit that loses one), **false-refusal rate** (share of
   owner-pass / default-pass rows refused; today's set is the 27 takes published with
   a failing dq and the 377 kept takes with a soft fail), and the **flag rate per
   unit** (a rising flag rate with a flat finding rate means the walls, not the
   pictures, moved).

## 1. Debate record

### 1.1 Judge architecture

| position | held by | strongest argument |
|---|---|---|
| Detectors for counts and geometry, embeddings for identity, VLM only names, code judges | A; B's substrate (flow, mask, face embedding, patch embedding) | Every owner-caught fault is a count, a position, an identity or a copy; none is a caption. A VLM counts from memory (reliable at 2-4, dips at 5, 7), reads a hat as worn whether held or worn, and read "4 figures, 0 copies" on three identical women. A 97 px gutter and a fence that moved 1055 px while the face moved 0 are numbers a Laplacian and a flow field report exactly |
| VLM list-then-judge everywhere (extend `panel_content.ASK` with framing, action, hats, landmarks) | B row 12; C's plan critic; E's panel_eye size read | It rides the session the step already opens (~6 s a short read), needs no new workflow, and is the house pattern with a calibration doc |

**Verdict: A's split, with B's substrate and C's critic.** The *decision* on any count,
position, identity or copy comes from a detector or an embedding; the VLM keeps what
it does well — naming in a closed vocabulary (hour, landform, posture family, landmark
word, framing size, the main figure's action) — as a second vote. Disagreement between
the detector and the VLM is a refusal on the cheap rungs and a flag at the terminal,
never a pass. Code judges everything; no model is ever asked "is this right"
(`studio/panel_content.py:10-13`).

Primitives, all on disk (A §3, B §3), and where each runs:

| primitive | where | for |
|---|---|---|
| YuNet (`studio/models/yunet.onnx`) | venv, CPU | face boxes, head boxes, clone pre-filter |
| **facenet-pytorch** (VGGFace2 InceptionResnetV1) | venv, CPU 0.4 s/face; `torchvision==0.29.0` + `facenet-pytorch==2.6.0` (no-deps) then `uv sync --all-groups` | identity vs sheet, clones within a frame, sheet-vs-sheet distinctness, cross-take identity |
| DWPose (`comfyui_controlnet_aux`, torchscript files at the models root) | ComfyUI workflow `image_dwpose_keypoints`, < 2 GB beside H3 | posture family, shot size, extra limbs, wrists for a held hat |
| GroundingDINO swin-T (`comfyui_layerstyle`) | ComfyUI workflow `image_groundingdino_boxes` | hats, landmark words from `cell_gates.MAJOR` |
| EasyOCR (`easyocr==1.7.2`, weights cached under the user profile) | venv, CPU 1-2 s/panel | lettering: recognised strings, not boxes |
| pHash + SSIM (numpy; `edit_gate.py:145` comparator) | venv, CPU | a reference handed back unchanged |
| DIS optical flow (`cv2.DISOpticalFlow`) + a 4-parameter similarity fit | venv, CPU | pass-through, rotation, warp residual |
| DINOv3 ViT-L (`models/dinov3`) | ComfyUI workflow `image_embed` | head leak vs staged pictures, refs-only take vs panel, style outlier, repeats |
| PySceneDetect (`scenedetect`, exact version pinned at install) | venv, CPU | second vote on jumps and master cuts |
| MediaPipe FaceMesh (exact version pinned at install) | venv, CPU | mouth-aperture envelope (advisory row) |
| Qwen3-VL-8B (`ComfyUI_Qwen3-VL-Instruct`) | the existing `describe.reader()` session | closed-vocabulary names only; short asks (~6 s), never the 1024-token list twice |
| person mask (YOLOv8-seg / SAM2, ComfyUI python) | v2 only, ComfyUI workflow | pass-through with a mask instead of a face band, when the bench says v1's margin is too thin |
| not used: SFace, insightface, CoTracker3, RAFT, SyncNet, Florence-2 OCR | — | see below; the optional GPU rungs are justified only when the cheap rung fails to separate the calibration set |

**Identity: facenet, not SFace (A wins over B).** The measured numbers decide it.
`docs/calibration/identity.md` (facenet): same person 0.73-0.94 (0.81-0.94 with the
sheet among the refs); cast-vs-cast 0.20 / 0.08 / -0.15; the four real strangers 0.43,
0.21, 0.03, -0.04; the one true drift 0.72 against real pairs >= 0.81; recalibrated on
ep10 to READABLE 0.15, FRONTAL 0.35, MATCH 0.60, STRANGER 0.45, DRIFT 0.75
(`studio/identity_gate.py`). SFace (`studio/cast_card.py:16`): the published
same-person line is 0.363, and two *different* cast members read 0.540 and 0.464 — the
separation is inverted on drawn faces. B's "recalibrate on SFace's scale" would need a
wall above 0.54 with no same-person data on this style; facenet has the data and the
install recipe. SFace is not the pre-filter either: the 64x64 zero-mean cosine
(`frame_match.signature`) is, for faces under READABLE.

### 1.2 Per gate

| gate | position (E) | position (B / C / A) | verdict |
|---|---|---|---|
| LOOK terminal | park (never auto; taste is n=1) | C: auto when five rows pass; an unverifiable card must escalate | **keep-best sheet, flagged**; a lookalike pair is bound flagged, and the take identity judge catches the consequence |
| PLAN terminal | park with `plan.refused.json` | C: never auto-approve after max rounds | **two terminals by cause**: a battery (plan_check) refusal is never signed — a `model_tier` rung, then `defer` (set aside, audit row, the scheduler retries with a fresh seed on at most two later passes); a *critic* fault ends in keep-best-of-drafts, flagged |
| EYE-panels terminal | park after 2 grids | B: never drop; A: redraw | **keep-best panel, flagged**; the panel becomes a take and the take judges see it again |
| EYE-takes terminal | still (<= 2), then park | B: keep-best for advisory/motion; still for narration with HARD content; ESCALATE for dialogue/turn/button | **keep-best flagged** for advisory or motion below severity; **still from the passed panel** for a narration shot with a HARD content or geometry fault (cap 2, never adjacent); **keep-best flagged with `severity: high`** for a dialogue, turn or button shot or a third still — no park |
| MASTER terminal | park | B: the ensemble; E: a judge never waives | **flag, never waive**: `eye_review.refusals` accepts an `n` carrying `flagged_by: judge:...` and evidence; waivers stay the owner's word; flags ride into `uploads.jsonl` so the PUBLISH signature sees them |
| drop a shot | never (silent gap fails QC) | B: never; a drop is a re-plan | agreed, everywhere |
| re-plan a cell after render | E: a "reversal" | B: rung 5, capped | allowed as `replan_cell` x1 for content faults that repeat on a fresh seed; it edits cell prose, extras and motion only — never a timing input, so `placed.json` stays current (GATES: "a reworded frame does not stale it") |

**Why keep-best-flagged and not park.** A parked unit is a human on the critical
path, which the owner removed. A flagged take exists, passed every row but the named
one, and is the cost the owner has accepted by removing the gate; the audit sheet
makes it findable, the casebook makes it fixable, the PUBLISH signature still sees it.
A public fault that is *recorded* is a lesson; a silent one is what ep09 was.

### 1.3 Policy file

| position | held by |
|---|---|
| `gates.yaml` at the repo root, `human|shadow|auto`, read by `studio/gate_policy.py`; `series.json` may lower MASTER/PUBLISH per series | E |
| `library/<book>/series.json` `policy.gates.<gate>` with mode, decision id, K and evidence; an owner refusal auto-un-retires | C |

**Verdict: `gates.yaml` (E), amended.** It is versioned (`library/` is gitignored) and
per format; a test can assert every row. Amendments: (i) every refs/episode row is
`auto` from day one with `decision: 2026-09-24-automate-the-taste-gates` (the owner's
instruction, quoted in `docs/DECISIONS.md`); (ii) `shadow` is a *field*, not a state:
`shadow: <judge>@<version+1>` runs beside `judge:` and writes `<verdict>.shadow.json`;
(iii) `human` remains a legal state only for gates outside these lines (PUBLISH);
(iv) no `series.json` override — the judged episodes remain the calibration set, but
the grain of a *judge version* is the format, and the casebook is per book already.
Decision-id rule: `YYYY-MM-DD-<slug>`, and the slug must exist as a heading in
`docs/DECISIONS.md` (a test reads both files).

```yaml
# gates.yaml — who signs each gate. auto = the judge signs pass|flagged and never parks;
# shadow = a newer judge version runs beside it, signs nothing, benches everything.
gates:
  refs:
    LOOK:        { state: auto, judge: look@1,       decision: 2026-09-24-automate-the-taste-gates, terminal: keep_best }
  episode:
    PLAN:        { state: auto, judge: plan@1,       decision: 2026-09-24-automate-the-taste-gates, terminal: keep_best, battery_terminal: defer }
    LAYOUT:      { state: auto, judge: grid_layout@1, decision: 2026-09-24-automate-the-taste-gates }   # a rule, no ladder
    EYE_PANELS:  { state: auto, judge: panel_eye@1,  decision: 2026-09-24-automate-the-taste-gates, terminal: keep_best, max_grids: 2 }
    EYE_TAKES:   { state: auto, judge: take_eye@1,   decision: 2026-09-24-automate-the-taste-gates, terminal: keep_best, still_max: 2 }
    MASTER:      { state: auto, judge: master_eye@1, decision: 2026-09-24-automate-the-taste-gates, terminal: flag }
    RENDER:      { state: auto, decision: 2026-09-24-episode-department, ceiling_seconds: 18000 }
promotion:
  units: 3          # a shadow version is promoted after this many units where its bench is not worse
```

### 1.4 Calibration

| position | held by |
|---|---|
| Labels JSONL per codex under `docs/calibration/labels/` + owner overlay; `judge_bench` with Wilson intervals and weights; a ratchet test; synthetic negatives in their own column | D |
| `docs/calibration/eye_labels.jsonl` with a region box per owner remark | A |
| `library/<book>/casebook.jsonl`, one row per (sha8, class, who, date); walls cite rows | B |
| `docs/calibration/owner_verdicts.jsonl` back-filled from prose; a fixture lock (fail the known-bad, pass the known-good) | C |

**Verdict: one design, D's schema, B's location, A's field, C's lock.**

- **Rows** (D §2 shape, plus A's optional `region: [x, y, w, h]`) live per book:
  `library/<book>/casebook/labels.jsonl` (harvested, regenerable by
  `scripts/calibration/harvest_labels.py`) and `library/<book>/casebook/owner.jsonl`
  (the casebook proper: append-only, the only file a person edits, every owner remark
  from now on — including audit-sheet findings — goes here through
  `scripts/audit/note.py`). `docs/ARCHITECTURE.md` already puts casebooks under the
  book; the code tree stays book-neutral.
- **Bench baseline** committed at `docs/calibration/bench/<judge>.json` (codex ids and
  sha8s only — opaque, the way `docs/calibration/*.md` already carry their tables),
  and the report appended to `docs/calibration/<judge>.md`.
- **Metrics**: recall on owner rows (Wilson, per class), all-fault recall, false-refusal
  rate with weights owner 1 / agent 0.75 / default 0.5 / synthetic in its own column,
  expected GPU minutes of refusals, flag rate per unit.
- **Ratchet** `tests/test_a_judge_may_not_lose_a_catch.py`: every judge with shipped
  constants, over the library's rows (globbed, skipped when no library is present, as
  `test_a_plan_script_regenerates_its_plan.py` already does), must still catch every
  owner row it caught in its committed baseline; a wall may move only with a new
  baseline in the same commit.
- **Fixture lock** (C) for the plan critic: fail ep09 and ep10 fixtures, pass ep05 and
  ep07, or it ships with its findings advisory (flag only, never refuse).

What is calibrated now, with margins; what synthetic covers; what stays uncalibrated
and therefore errs by design:

| judge row | calibration today | margin | errs toward |
|---|---|---|---|
| stacked / gutter-in | 1.000 on 3 positives vs worst clean 0.020 over 124 panels (`panel_dq`) | wide | refuse |
| jump | 0.08, 0.16 vs every accepted take >= 0.83 | wide | refuse |
| frozen | 63 files (`motion_gate`) | stated in the doc | refuse |
| zoom overrun, face-at-end, look | 14 / 13 / 30 agent-labelled rows, 1 known false alarm each | one take wide | refuse; agent labels, not owner's — the bench says so |
| content counts (people, extras) | ep09 panels 4 TP / 19 clean; ep08 takes 3 TP, 1 FN, 16 clean | stated | refuse |
| identity (MATCH / STRANGER / DRIFT) | 2 true positives, 4 strangers, recalibrated on ep10 after 4 false alarms | 0.72 vs >= 0.81 | refuse on a close, "cannot tell" on a wide |
| clones (pairwise >= DRIFT in one frame) | positives ep09 panel 4, 21; ep08 T07; **synthetic legitimate** (duplicate a face crop) | cast-vs-cast <= 0.20 vs same render >= 0.75 | refuse |
| lettering (recognised string) | ep08 T06 (leaked label), T10-T12; **synthetic legitimate** (paste text) | needs the bench | refuse; a cast id or plan word in an insert is a certain fail |
| copy of a staged reference | ep09 insert; `sheet_gate.py:471` 0.951 / 0.890 / 0.821; **synthetic legitimate** (re-save, crop) | needs the bench | refuse |
| held / pass-through | 2 fires vs 3 passes ("thin, said so"); G-ANCHOR upstream 7 fires / 5 faults | one take wide | refuse on the cheap rungs, flag at terminal |
| hats worn+held | ep09 panels 11, 20; `wardrobe_eye_labels.json` 22 rows (hat_on / hat_in_hand) | thin | refuse on the cheap rungs, flag at terminal |
| landmark invented | ep09 retakes 14 / 15 / 18 and their fresh-seed repeats | thin | same |
| posture by keypoint | ep10 T18 / shot 18; ep11 shot 9 (the walker exception) | one | same; VLM posture is the second vote |
| framing size | 0 owner rows; 16 medium panels of ep06-09 as negatives | none | flag only until the bench has a positive |
| rotation | ep10 T18 | one | refuse on the cheap rungs, flag at terminal |
| mouth-envelope lag | ep06 T28, ep08 T05 vs ep10's seven | two | advisory -> flag; the cure is the shorter take |
| style outlier (LOOK) | two books (refused 3D sheets vs approved Krea2 pack) | one book wide | flag only |
| plan critic (turn, answer, coverage, claims) | 5 plans; the fixture lock | n=5 | pass (flag) — a false refusal costs writer rounds, and its recall is on two story faults |
| G-MOVES, G-SOURCE | ep01 fails (18/23 orbit), ep02 passes; spans are deterministic | wide | refuse (deterministic) |
| master: shadow, faces, board, repeats | ep05-07 vs ep09 (one bad episode) | one episode wide | refuse -> recut; flag at terminal |
| master: story (action listed on the turn shot) | ep09 | one | flag |
| anchored slide, dead body moves, identity drift, wardrobe | no synthetic possible (render behaviour) | — | shadow-benched only through real units; refuse where a row exists |

### 1.5 Cost

| item | E | A / B | verdict |
|---|---|---|---|
| judges per episode | ~11 GPU min (panel short read 2.5, VLM trait cards on takes 5, master 30-frame read 3.5) | detectors in CPU seconds; a master pass on a 30-frame grid; B's 1 fps master pass (68-81 min) | **~7 GPU min + ~5 CPU min**: identity moves to facenet on CPU (the 5 min VLM take read is gone); DWPose + GroundingDINO on 23 panels and 69 take frames ~1.5 min beside H3; the panel size/board read 2.5 min; the master 30-frame short read 3 min; OCR, pHash, flow, facenet on CPU. Never 1 fps |
| ladders | panels <= 2 grids x 2 rungs x 1.7 = 7 min; takes 15-50 min at the observed retake rate (4-11 of 25) plus one 5-min cold load a round | B adds re-plan | **budget**: judges capped at 15 GPU min; ladders at 60 min (panels 10, takes 40 incl. <= 2 `replan_cell` at ~12 each, master retake 10) |
| ceiling | `EPISODE_CEILING_SECONDS` via `run_budget.Budget` shares | — | **18 000 s (5 h)** against today's 3.5-4 h; shares keyed by step id like `TRAILER_SHARES` |
| when exceeded | terminal rungs | — | cut in this order: `replan_cell` -> `move_type`/`shorter_take` retakes -> master `retake_shot` -> the master read drops to 15 frames (every 10 s). Never cut: dq, content, identity, OCR (CPU), the audit row. A run over the ceiling takes terminals and flags; `RENDER_HOLD` stays the brake |

### 1.6 Organisation

| position | strongest argument |
|---|---|
| A Quality unit inside each line: the substeps exist (02_05, 08_05, 09_04, 11_03, refs/04) and now run a judge | The decision doc's rule: "a measure returns a number; a gate (department-owned) returns a verdict". The ladder is the step's; the verdict file is the line's contract |
| A Platform "Measures & Judges" service with the bench and the audit sheet as its deliverables | The primitives (flow, embeddings, keypoints, OCR) serve every line, trailer and shorts included; the bench and the casebook must be one across formats; `studio/measure/` is already a Platform row in the doc |

**Verdict: both, split at the doc's own seam.** *Measures, the calibration bench, the
ratchet, the audit-sheet builder* are Platform (`studio/measure/*`, `studio/judge_bench.py`,
`scripts/calibration/*`, `scripts/audit/*`) — no verdict of their own. *Judges* (verdict
writers with a ladder) sit in the line's existing substeps as `qc` agents named
`judge:<name>@<version>` — they own the file the next step refuses without. The
Studio office gains the **Audit sheet** beside Decisions and the Brake: the owner's
after-the-fact look, feeding the casebook. The `eye` agent of the decision doc ("would a
viewer see a fault no measurement names?") is retired: it was the human.

### 1.7 The rest, one line each

- Master read at 1 fps (B) vs the 30-frame grid (E): **E**; short ask, ~3 min.
- CoTracker3 / RAFT / SyncNet (B): **not in v1**; the bench must show the cheap rung fails to separate.
- Person mask (SAM2 / YOLO-seg) vs face band: **v1 face band + DIS** (zero install); **v2 mask** through a ComfyUI workflow when the bench says the held margin is too thin — it is, so v2 is the first shadow.
- EasyOCR in the venv vs Florence-2 in ComfyUI: **EasyOCR** (weights cached; keeps the GPU for H3).
- `Verdict.confidence` as a count of readable reads (E): **adopted**; unread on a close is a fault, on a wide it is nothing.
- Pairwise "vs the last approved plan" (C, shadow only): **dropped** — no decision value under auto; the bench is the evidence channel.
- The `--approved=render` flag hard-coded in `step_09_shoot.py:52` (E): **registered** as `RENDER: auto` with the build decision id; the ceiling replaces the flag.
- **A sixth human park no report listed**: `scripts/episode/step_07_board.py:56` raises `Escalation("PLAN", "storyboard/layout.json", "choose cols x rows per setup")`. Replaced by a rule, `studio/grid_layout.py`: per setup, shots in plan order, chunked greedily into grids whose cell count is in {9, 6, 4, 3, 2, 1} (cols, rows <= 3), `cols x rows == shots` exactly, at most three reference slots as `grids.py` demands.
- Trait cards stay the LOOK *verbal* distinctness check; identity across takes is facenet, not trait cards (E's 5 GPU min are gone).
- Terminal names across ladders are the trailer's (`studio/ladder.Ladder.terminal`): `keep_best`, `still`, `flag`, `defer`; `park` no longer exists in refs/episode.

## 2. The final design: judges per gate

| gate (substep) | detectors / models | judge module | ladder (rung x tries, GPU min) | terminal | errs toward | calibration |
|---|---|---|---|---|---|---|
| LOOK (refs/04) | trait card (built); facenet sheet-vs-sheet < STRANGER; `look_back` MUST nouns (built, HARD for MUST); EasyOCR zero words; DWPose limb count; DINOv3 style outlier vs the pack's own place pictures; voice ECAPA 0.55 (built) | `studio/judges/look.py` | `redraw_seed` x1 (2.5) -> `defining_state_first` x1 (2.5) | keep_best, flagged; lookalike pair bound flagged | refuse on MUST noun / OCR / identity; flag on style | trait card calibrated; nouns 4 recorded misses; OCR synthetic; style 2 books |
| LAYOUT (episode/07_01) | none | `studio/grid_layout.py` | none | — | — | deterministic |
| PLAN (episode/02_05) | `plan_check` battery (built) + G-MOVES + G-SOURCE (new, deterministic); `plan_reader` critic (Strands, different family from the writer, plain-text plan with `why`/`turn`/`section` stripped, k=3 on turn and claims, temperature 0) | `studio/judges/plan.py` + `agents/plan_reader.py` | `improve` x2 (0) -> `fresh_brief` x1 (0) -> [battery still refusing] `model_tier` x1 (0) | critic faults: keep_best draft, flagged; battery refusal: **defer** (set aside, audit row, retried by the scheduler <= 2 passes) | deterministic rows refuse; the critic flags | n=5 + the fixture lock |
| EYE-panels (episode/08_05) | `panel_dq` incl. stacked-by-thirds; `panel_content` (built); hats (GroundingDINO + YuNet + DWPose); copy (pHash <= 10 or SSIM >= 0.6 with pHash <= 14 vs every staged input); posture + framing (DWPose); clones (facenet pairwise >= 0.75; 64x64 cosine >= 0.9 under READABLE); lettering (EasyOCR); landmark (GroundingDINO over `MAJOR` not in setup words + pack); repeats (subjects equal + DINOv3 within one setup); one short VLM read for size/board as the second vote | `studio/judges/panel_eye.py` | `redraw_grid_seed` x1 (1.7) -> `reprose` x1 (1.7, cure table; cell prose only) ; cap 2 grids per episode | keep_best panel, flagged | refuse on calibrated rows; cheap-rung refuse / terminal flag on thin rows | see §1.4 |
| EYE-takes (episode/09_04) | `take_dq` rows (built); `take_content` (built) + FRAMING and ACTION names; identity (facenet MATCH/STRANGER/DRIFT, `identity_gate` armed); clones per frame; pass-through (DIS flow, face band v1 / mask v2); rotation (4-parameter fit, cumulative theta); head leak measured vs every staged picture (DINOv3) -> `heads.json` automated; `last_vs_cell` on the panel for refs-only takes; scenedetect second vote; mouth-envelope lag (advisory) | `studio/judges/take_eye.py` | `seed` x1 (3.8 + 5 cold; stochastic rows only, and only if the row did not fail on the previous attempt) -> `move_type` x1 (3.8; cause -> substitute move from the camera catalog, through `write_plan`) -> `shorter_take` x1 (3.8; lag rows; restore a length just changed first) -> `head_cut` (0; leak measured, take still covers the shot) -> `replan_cell` x1 (~12; content faults that repeat on a fresh seed) | keep_best flagged (advisory / motion below severity); `still` from the passed panel with a slow push (narration shot, HARD content or geometry, cap 2, never adjacent); keep_best flagged `severity: high` (dialogue, turn, button, third still) | refuse where calibrated; identity "cannot tell" on wides | see §1.4 |
| MASTER (episode/11_03) | `qc.py` hard rows (built); `judged` (built); five rubric measures: shadow = `take_look` p5 luma / near-black over master frames; faces = YuNet box height at closes vs plan; board = `frame_match` last-vs-cell, DINOv3 first-vs-panel for refs-only; repeats = count of near-duplicate representative-frame pairs not explained by a shared setup; story = the plan's turn verb among the actions the VLM lists on the turn shot +-1; plus the 30-frame short read (people, copies, lettering, hour, posture, framing, action, judged against `placed.json`) and a cross-take facenet pass (each character within DRIFT of his own median; no two collapse) | `studio/judges/master_eye.py` | `recut` x2 (0) -> `retake_shot` x1 (4-9, through the take ladder) | flag: the rubric filled, `n` fields carry `flagged_by` + evidence, `waived_because` never written by a judge | refuse -> recut on the four measured fields; flag on story | ep05-07 vs ep09 |

Every judge: takes `reader=` / `run=` / `model=` callables (the `look_back.read` /
`describe(run=)` pattern), rides the session its step already opens, and writes one
`Learning` per rung to the unit's `learnings.jsonl`. A test conftest monkeypatches
`comfy.run_text` to raise, so a judge constructed without injection is a failing test.

## 3. The shared contract

```python
# studio/judges/verdict.py
class Fault(BaseModel):
    kind: str            # "clones" | "lettering" | "hat" | "identity" | "pass_through" | "story" | "unread" | ...
    where: str           # "shot_07" | "T07" | "00:45.0" | "refs/sheets/x.png"
    evidence: dict = {}  # {"cosine": 0.81, "wall": 0.75, "frames": [12, 40]}
    severity: str = "normal"   # "high" on a dialogue / turn / button shot at a terminal rung
    note: str = ""

class Verdict(BaseModel):
    judge: str; version: str
    passed: bool
    faults: list[Fault] = []
    confidence: float    # share of reads that were readable; a count, not a feeling
    reads: int = 0
    terminal: str = ""   # "" | "keep_best" | "still" | "flag" | "defer"
    signed_at: str = ""
    @property
    def signer(self): return f"judge:{self.judge}@{self.version}"
```

Verdict files (additive, the owner path unchanged):

- `eye_verdict.VERDICTS = ("pass", "flagged", "fault")`; `passed()` is true for pass or
  flagged; `require()` refuses only `fault`; `sign(..., signed_by=, faults=, terminal=)`.
- `plan_verdict.sign(plan, note, signed_by=, faults=, flagged=)` — `verdict` stays APPROVE
  (the file's contract), `flagged: true` when the terminal signed.
- `refs_verdict.sign(book_dir, note, signed_by=, faults=)` — a stale pack re-judges the
  new rows only and re-signs.
- `eye_review.refusals` accepts an `n` that carries `flagged_by` and `evidence`;
  `waivers()` is unchanged; a new `flags()` rides into `uploads.jsonl` beside the waivers.

## 4. The audit sheet

`scripts/audit/sheet.py <codex> [<unit>]` writes `library/<book>/audit/<unit>.html`
(and an index) from `library/<book>/audit/rows.jsonl`, which every terminal rung
appends to: `{unit, gate, judge, sha8, artefact rel_path, faults[], terminal, ts}`.
The page shows every flagged artefact (panel, take strip, master frame) with the
judge's numbers next to the wall, the contact sheet, the strips, the master link, and
a random sample of three *passed* artefacts per gate (seeded by the unit sha8, so the
sample is reproducible). The owner may open it whenever he likes and write a finding
with `scripts/audit/note.py <codex> <unit> <artefact> <class> "<words>"`, which appends
to `library/<book>/casebook/owner.jsonl`. The bench re-runs on the next commit; the
ratchet enforces the new row. **No step reads the audit sheet or its rows**; a test
greps the step modules for the path.

## 5. What is removed, and what replaces it

| removed (file:line) | replaced by |
|---|---|
| `scripts/refs/step_04_verdict.py:36-37` — `Escalation("LOOK", ...)` twice (stale pack; sign every sheet) | `judges.look` over the pack (new rows only when stale) -> `refs_verdict.sign(signed_by="judge:look@1")`; ladder; keep_best flagged |
| `scripts/episode/step_02_plan.py:123` — the writer failed `plan_check` after 2 rounds | `model_tier` rung, then `defer`: `set_aside`, audit row, `plan.deferred.json`, the scheduler retries on at most two later passes with a fresh seed |
| `scripts/episode/step_02_plan.py:137` — "read the plan and sign" | `judges.plan` -> `plan_verdict.sign(signed_by="judge:plan@1")`, flagged at the terminal |
| `scripts/episode/step_07_board.py:56` — `Escalation("PLAN", "storyboard/layout.json", ...)` | `studio/grid_layout.py` writes `layout.json` by rule |
| `scripts/episode/step_08_panels.py:68` — `eye_verdict.require(... "EYE" ...)` | `judged_gate.clear` with `judges.panel_eye` and `panel_ladder`; keep_best flagged |
| `scripts/episode/step_09_shoot.py:60` — `eye_verdict.require(... "EYE" ...)` | `judged_gate.clear` with `judges.take_eye` and `take_ladder`; still / keep_best flagged |
| `scripts/episode/step_11_qc.py:74` — `Escalation("MASTER", ...)` | `judges.master_eye` fills the rubric; recut / retake ladder; flagged rubric |
| `scripts/episode/step_09_shoot.py:52` — `--approved=render` typed by code | `gates.yaml` `RENDER: auto` with the build decision id; `run_budget.Budget` ceiling and shares; `can_afford` before every render |
| the `eye` agent (decision doc §2.4) and `eye_review.write_blank` as the path to a verdict | the judges above; `write_blank` remains for the audit sheet's contact grid |

Kept, unchanged: `RENDER_HOLD` (a file, the brake), MONEY for paid credits (the lines
spend none), PUBLISH and OVERRIDE (Distribution), the synthetic declaration, and
`eye_verdict.require`'s refusal of a `fault` file (nobody writes one now; if a person
ever does, it is work to do).

## 6. Risks, plainly

1. **The calibration set is not the owner's** (D §0): zero signed verdicts; ~8 owner
   catches with an id; agent labels transcribed by the agent being evaluated. The judges
   can be built now and validated only as the casebook grows through the audit sheet.
   Until then, every number in `docs/calibration/*.md` is what it says: a wall with a
   stated margin, fitted on one book.
2. **A consistent judge approves slop consistently** (C §5). ep09 was 28/28 at 100.0.
   The mitigation is not a better judge; it is that nothing is silent: flags, the audit
   sheet, the finding rate, and the ratchet.
3. **False refusals cost GPU nights**: a 20 % false-refusal rate on 25 takes is 1-2 GPU
   hours. Bounded by the ceiling and the cap on rungs; a false refusal costs at most
   one rung's minutes, and the terminal costs 0.
4. **Thresholds are one book's** (`take_look`'s night calibration accused daylight).
   Walls carry `fitted_on` and the bench is per codex; the first unit of a new book
   runs every new row advisory (flag only) and the bench re-fits before rows go HARD.
5. **The plan critic's family**: the writer is OpenAI `gpt-5.6-luna` on the `local`
   tier; the critic must be another family through Strands or it grades its own prose.
6. **Two repos**: the DWPose / GroundingDINO / embed workflows live in the sibling
   `comfy_studio` workflows folder that `studio/comfy.py:19` names; the recorded outputs
   are fixtures here. A workflow that drifts there breaks a judge here silently —
   `comfy.validate` on the manifest at step start.
7. **`uv add` strips the music/voice groups** (memory): every dependency commit ends in
   `uv sync --all-groups`, and a test asserts the lock still carries them.

## 7. Publishable

`list-then-judge` (already flagged) grows a second half: **casebook-locked calibration**
— rows per artefact, a bench with Wilson intervals, synthetic negatives in their own
column, a ratchet test that refuses a commit losing a catch, and a flag-not-park
terminal contract. That is a standalone package and a short paper measured on two
books' casebooks. The detector recipes (hat worn/held from boxes + keypoints; copy of a
staged reference; clones by embedding) are its worked examples.
