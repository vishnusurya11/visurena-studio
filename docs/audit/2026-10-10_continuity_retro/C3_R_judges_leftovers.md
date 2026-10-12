# C3-R: judge reliability, the neutral-tile switch, and the leftovers

2026-10-11. Cycle-3 researcher R. Read-only, CPU and online only: no GPU, no code or workflow edit, nothing committed. This file is the only thing written in the repo.

**Scripts and evidence:** `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c3\`
- `R_repeats.py` → `R_hits.json` and `R_repeats.json`: every cached VL read reachable from the WotW and Scarlet panels, grids, take frames and bench folders.
- `R_framepairs.py` → `R_framepairs.json`: reader agreement between near-identical frames.
- `R_streak.py`: the tweed streak index.
- `R_gframe_owner.py` → `R_gframe_owner.json`
- `R_ghost_takes.py` → `R_ghost\contact_50.jpg` and `R_ghost\contact_90.jpg`
- `R_hairparse.py`
- `R_refused.py` → `R_refused_panels.jpg`
- `R_sheet_front.jpg`

**Owner rulings in force (2026-10-11):** P-WORDS no; 992 no; neutral-tile upscale ADOPT for new draws only; 6 h is a P90 limit.

---

## 0. Headline findings (each measured, with n)

| # | Finding | Evidence | Conf. |
|---|---|---|---|
| R1 | **The CYCLE_2 carry #9 premise is wrong.** The S6 "no-op crop" that read "mustache" once and not once was **not identical pixels**: the shipped panel is 1024², and the crop was resized to 768² with LANCZOS (`sheet_c2.py:90`). Qwen's processor tiles 1024² (above `max_pixels` 1 003 520, so it is resized) and 768² (inside the range) into different visual-token grids. | pixel compare: shapes (1024,1024) vs (768,768) | 100 % |
| R2 | **On truly identical pixels the reader has agreed 2/2.** ep14 s22 and ep14 s24: the C2 (b) redraws are pixel-identical to the shipped grids but have different bytes, hence different staged names and a genuine cache miss. Both re-reads returned the identical 21-subject list and people count. The whole scan (5 450 images, 1 603 cache hits) found **no other** identical-pixel pair read twice. | `R_repeats.json` | measured, n = 2 |
| R3 | **The reader is a seeded sampler, so identical inputs are deterministic by construction.** The `Qwen3_VQA` node calls `torch.manual_seed(seed)` and then `generate(temperature=0.1)` with no `do_sample`. That inherits `generation_config.json`: `do_sample: true, top_k 20, top_p 0.8`. Batch size is always 1, so the forward pass is run-to-run deterministic (Thinking Machines: nondeterminism comes from batch-size variance). **Variance enters only through the pixels or the seed.** | node source `ComfyUI_Qwen3-VL-Instruct/nodes.py:108,223` (commit 70cc35e); model `generation_config.json` | 100 % by code |
| R4 | **What is unstable is the answer under a tiny pixel or seed change, and that is large.** These are pairs of a take's own content frames: seeds 11/12/13, adjacent moments, frame PSNR ≥ 25 dB, 63 pairs. People count differs in **8/63 (12.7 %)**, landform 10/63 (16 %), hour 4/63 (6 %), lookalikes 2/63, text 0/63. The free subject list overlaps only **Jaccard 0.57-0.67** even at PSNR ≥ 30. Cases at PSNR ≥ 30: ep14 T19 lookalikes 4 vs 0 (×2), ep15 T05 people 2 vs 3, ep16 T23 people 3 vs 4. | `R_framepairs.json` (373 takes, 1 119 pairs) | measured, ≥ 2 cases per field (except text) |
| R5 | **The production cache makes every read sticky.** `comfy.cached_text` keys on the workflow, the prompt, the seed and the content-addressed staged name, and it keeps any parseable answer, refusals included. A wrong read on given bytes is therefore never re-read. Only a redraw (new pixels) escapes it. The cost of a false refusal is one reseed or climb, never a retry of the read. A false pass ships. | `studio/comfy.py:442-462` | 100 % by code |
| R6 | **LOOK-STATE is the one hard gate that is uncached and single-read.** `look_back.vlm_reader` → `comfy.run_text` (seed 11), and a wrong or unread HARD head marker refuses. The C1 felt-hat misread (7/8) was systematic, not noise. Commit 4's family fixed it. | `studio/look_back.py:144`, `studio/judges/look_state.py:96` | 100 % by code |
| R7 | **Shipped residual refusals are mostly true reads under a too-literal rule, not reader noise.** Of 21 shipped panels refused on mountain/cliff/lettering, by eye the station signs and can labels **have** lettering, and the pits **have** rock walls. The rule (a pit is not a cliff; scenery text is not a caption) is the fault, not the reader. | `R_refused_panels.jpg`; 46/486 shipped takes and 40/468 shipped panels still carry a refusal | by eye, 21 panels |

**Bottom line for item 1:** "different answers on identical pixels" is **refuted as stated** (0 cases; 2/2 agree; deterministic by code). The real reliability fault is that **a gate decides on ONE sample of a reader whose count fields flip on 6-16 % of near-identical inputs**, and the cache then freezes that sample.

---

## 1. Judge reliability

### 1.1 Which gates stand on a single read

| Gate | Reads | Seed | Cached | Decides |
|---|---|---|---|---|
| `panel_content` (G-CONTENT, panel) | 1 per panel (+1 twin ask on 2-face sizes) | 11 (twin 17) | yes | **HARD**: people/lookalikes count, hour, landform/banned noun, text, posture, cast missing |
| `take_content` (G-CONTENT, take) | 3 frames, each read once | 11/12/13 (twin 23+i) | yes | **HARD**, aggregated by **max / any** (`take_content.busiest`). One over-count on any of 3 frames refuses. Under independent noise that roughly triples a per-read over-count rate. |
| LOOK-STATE (refs step 03) | 1 | 11 | **no** (`run_text`) | **HARD** on headwear, hair colour and facial hair; refusal → redraw |
| G-LOOK-PANEL (`panel_content.look_advisories`) | the panel read | 11 | yes | advisory |
| QC step 11 frames | 1 per sampled frame | fixed | yes | QC refusal |
| `describe` (cast distinguish) | 1, +1 on unparsable (seed+1) | 42 | no | refs collision |
| book/series title OCR and people | 1 | node default | no | title plate |

### 1.2 What the flip rate costs
- **False refusals (time).**
  - On a take, the max-of-3 aggregation turns a ~6-7 % per-read count flip (half the 12.7 % pair disagreement) into an upper bound of ~15-20 % of takes showing an over-count on some frame.
  - Each one costs a retake, about 2-4 min of H3 at 768.
  - A refusal that survives the ladder becomes a `keep_best` terminal: 46/486 shipped takes, 40/468 shipped panels.
  - **Hypothesis**: the direction of each flip is unknown, because a pair disagreement says nothing about which read is right.
- **False passes (shipped faults).** A read that misses a third figure or a copy passes, and the cache keeps that pass. The only measured case is ep16 T23 (3 vs 4 people on near-identical frames). The two sides cannot be separated without ground truth.
- **The free subject list** (Jaccard ≈ 0.6 between near-identical frames) drives the `banned:` noun rules ("mountain", "cliff"). A banned-noun rule on that list is a coin flip at its margin. Of the 21 shipped refusals in R7, most are rule faults.

### 1.3 Online: deterministic decoding and its cost
- **The current node cannot decode greedily.** `Qwen3_VQA` exposes `temperature` (min 0) but not `do_sample`. Temperature 0 with the model's `do_sample: true` raises in transformers. Greedy decoding would need an edited custom node, and that is out under the house rules.
- **The other installed node, `ComfyUI-QwenVL` (AILab, 1038lab), has a beam switch.**
  - `num_beams ≥ 2` sets `do_sample=False`, which is deterministic beam search (`AILab_QwenVL.py:816-819`).
  - Its weights are already on disk: `models\LLM\Qwen-VL\Qwen3-VL-8B-Instruct`.
  - **Caveat**: its default `repetition_penalty` is 1.2, which changes answers. Set it to 1.0 for parity.
  - A new workflow file is needed, for example `image_qwen3vl_caption_beam2_visurena.json`.
  - Beam 2 costs about 1.2-1.6× the decode time. This is a vendor claim, unmeasured here.
- **Qwen's own Instruct settings sample** (temp 0.7, top_p 0.8, top_k 20, presence_penalty 1.5). Greedy is the usual choice for reproducible VQA.
- **Determinism is not the cure here.** We are already deterministic per input (R3). Beam or greedy decoding removes only the seed term. The pixel term remains: R4 mixes the seed with adjacent frames, so how much of the 12.7 % is seed alone is **unmeasured**.
- **Majority-of-3 cost.**
  - VL read time: 14-18 s each (C2: 30 panels in 9.0 min, 6 reads in 1.4 min).
  - Shipped state per episode: about 80 reads (1 603 reads over about 20 episodes).
  - Ladder rounds roughly double that, so about 100-160 reads per episode.
  - **Majority-of-3 on every read: +50-95 min per episode.** That breaks the P90 ruling (6.9 h already over).
  - **Confirm-before-refuse** (2 more reads at seeds +100 and +200, only when a read raises a HARD count, boolean or head-marker fault; refuse on 2-of-3) costs about **+5-12 min per episode** at a 10-20 % refusal rate. It also saves the retakes that a false refusal triggers.

### 1.4 Proposed (for the cycle-3 verdict)

| Item | Conf. | What |
|---|---|---|
| J1 | **100 %, CPU** | **Correct carry #9** in LESSONS/CYCLE notes: the S6 case was a 1024→768 resample. Add the lesson: "a reader compared across two reads must be fed the same pixels at the same size". |
| J2 | **95 % (issue), bench to size** | **Seed-only flip bench (GPU ≈ 15 min).** 12 shipped panels (6 with 2+ people, 3 night, 3 with signage) × current settings at seeds 11, 111, 211, 311, + seed 11 again cold. Then the same 12 through a beam-2 workflow ×2. Measure per-field flips (people, lookalikes, hour, text, landform, posture) and subject Jaccard. This separates the seed term from the pixel term in R4. |
| J3 | **issue 95 %, cure pending J2** | **Confirm-before-refuse** for `panel_content`, `take_content` and LOOK-STATE HARD faults. Two extra cached reads at fixed seeds; refuse on 2-of-3. A pass stays one read. **Replay first:** on the owner-judged fixtures (ep05/ep07 good, ep08/ep09 bad), no bad-episode refusal may vanish (memory *a cure is judged by every gate*). |
| J4 | 70 %, hypothesis | **take_content's max-of-3 for counts:** require an over-count on ≥ 2 frames, or on the last frame (a walk-in stays in). This changes a deliberate rule (`busiest` docstring), so it needs owner-judged replays. |
| J5 | 95 % (R7, 21 panels) | **The banned-noun and lettering rules over-refuse on true reads.** Pit walls read "cliff"; station signs and tins read "text". This is a rule calibration, not reader noise. Route it to whoever owns the content rules, with the 21-panel sheet as fixtures. |
| J6 | measured 20/1 492 | **Repetition loops**: 1.3 % of cached panel reads have ≥ 40 items or an item repeated ≥ 4 times (C2 ep14 s22 (c): "lamp cord, lamp switch…" to 1 024 tokens). Each costs a full 1 024-token decode. `Qwen3_VQA` has no repetition penalty. The beam workflow would allow `presence/repetition_penalty`; it must stay at 1.0 unless benched. |

---

## 2. Neutral-tile adoption (owner: ADOPT for new draws; existing sheets untouched)

### 2.1 The file to make
- `image_krea2_cinematic_2x_neutraltile_visurena` **does not exist yet**. Only the bench file `image_krea2_cinematic_2x_presave_neutraltile_visurena` does, and it saves two outputs (13 = 2x, 14 = 1x) with a `bench_` prefix.
- **New file, never an edit:**
  - Copy `comfy_studio\workflows\image\image_krea2_cinematic_2x.json` and keep nodes 1-13.
  - Add node 15 `CLIPTextEncode` (the bench's style-only text, `clip ['2',0]`) and node 16 `ConditioningZeroOut(['15',0])`.
  - Rewire node 12 to `positive ['15',0]`, `negative ['16',0]`.
  - Keep node ids 15/16 so the graph diffs cleanly against the bench.
  - The manifest is the base manifest with the id and template changed. The `inject` map is unchanged (prompt → 5, width/height → 7, seed → 8, lora_strength → 4, filename_prefix → 13), and `outputs.count` is 1.
- **Note:** cfg is 1.0, so node 16 (the negative) is ignored by the sampler. It exists only to satisfy the input.
- **Where it lands:** comfy_studio is checked out on **`poc/2k-video-pipeline`**, the branch the bench file sits on. Add a test that `comfy.load_workflow(refs_pack.T2I)` resolves. If comfy_studio is switched back to master, every refs draw then fails loudly instead of silently.

### 2.2 Every call site of `image_krea2_cinematic_2x` for a NEW draw

| Site | How it names the workflow | Switch? |
|---|---|---|
| `studio/refs_pack.py:20` `T2I` | constant, used by `character_jobs`, `location_jobs`, `prop_jobs` (base sheets, location wides, prop sheets) | **yes**. This one line is the minimal switch. |
| `scripts/refs/looks.py:226` `fresh` (Krea2 T2I route for hair/beard/face looks) | `refs_pack.T2I` | follows the constant |
| `scripts/refs/places.py:261-264` (per-episode place pictures drawn from words) | `refs_pack.T2I` | follows the constant |
| `studio/sheet_ladder.py:163` `Try.workflow` default | `refs_pack.T2I` | follows the constant |
| `studio/sheet_ladder.py:89` `job_from_row` | **`row.get("workflow") or T2I`** | **Decision needed.** A redraw of a row built from the pack (per-episode places) reuses the row's recorded `image_krea2_cinematic_2x`, so a reseed of an old row keeps the ghosting tile pass. Recommend: a new draw maps the old name to the new one (the row records how the old picture was made, not how the next one must be). It is a new picture, which the ruling covers. |
| `studio/book_title.py:79` `plate_request` (stylised title plates) | literal `"image_krea2_cinematic_2x"`; `tests/test_the_book_main_title.py:240` asserts it | **Owner/verdict call.** WotW and Scarlet cards are already baked. A new book's plate is a new draw, so the ruling covers it, but the test must change with it. |
| `scripts/refs/looks.py:221` edit route (`image_krea2_identity_edit`) | — | **no**: that graph has no USDU tile pass (read node by node), so it has no ghost mechanism |

**Untouched by construction:**
- The existing `sheet.png` / `sheet_front.png` and every pack row: rows keep their recorded workflow name, so replays stay exact.
- Fixtures: `tests/look_fixtures.py:61` and `tests/test_refs_pack.py:66` carry literal names and stay valid.
- Tests compare `T2I` by the constant.

### 2.3 The tweed colour-streak side effect: measured, and a cheap mitigation to bench
- **Streak index** (`R_streak.py`): the share of pixels whose Lab a* rises > 8 over the 1x (the 2x downsampled to 1536×1024).

  | Draw | Today's tile | Neutral tile | Ratio |
  |---|---|---|---|
  | narrator | 0.31 % | 1.08 % | 3.5× |
  | fresh_s3 | 0.28 % | 0.40 % | 1.4× |
  | fresh_s4 | 0.29 % | 0.59 % | 2.0× |

  **3/3 draws rise.** By eye (`bench_evidence\c2\narrator_neutraltile_2x.jpg`), red and purple dashes sit on the back-view jackets.
- **Mechanism (80 %):** with the subject removed, the tile prompt is pure style words, "brush stroke colour texture … high contrast". At denoise 0.2 the tile repaints flat cloth as coloured strokes. The subject prompt used to anchor the cloth's colour words.
- **Cheap arms to bench** (tile-only, so no new base draw):
  - A **new** tile-only workflow, `LoadImage → UltimateSDUpscale`, with the bench's nodes, `image_krea2_upscale2x_neutraltile_visurena`.
  - Run it on the four 1x files already on disk in `c2b\looks\*_1x.png` (narr, ragged, fresh_s3, fresh_s4).
  - 4 pictures × 4 arms × about 20 s ≈ **6 min GPU**:
    - (a) today's neutral, the control;
    - (b) tile denoise 0.15;
    - (c) the tile words minus "brush stroke colour texture" and "high contrast";
    - (d) (c) plus a subject-free material clause taken from the look's own wardrobe nouns ("grey herringbone tweed, white collar").
  - **Pass:** 0 ghost faces by eye **and** the streak index ≤ 1.2× today's **and** trouser Laplacian ≥ 90 % **and** head facenet vs 1x ≥ the neutral control.
  - Arm (d) puts words back in the tile, so it must also show 0 faces. A material noun is not a face, but that is a hypothesis.
- **Adopt order:** the switch in §2.2 lands now, on the ruling. The streak arm adopts only if it passes, as a further new file. The streaks are an owner-visible look change, so the bench sheet goes to the owner.

---

## 3. Leftovers

### 3.1 G-FRAME calibration (advisory floors)
- Data:
  - the 396-panel ep12-27 set (`c2\F\shipped_faces2.json`);
  - the owner-judged episodes replayed here (`R_gframe_owner.json`; ep05-08 predate grid JSON, so the panels are measured without shape).

| Set | MCU n | MCU face_h (sorted) | flagged at 0.22 |
|---|---|---|---|
| ep05 (owner good) | 7 | .192 .204 .221 .226 .226 .249 .267 | 2 |
| ep07 (owner good) | 6 | .137 .161 .177 .186 .209 .277 | **5** |
| ep08 (owner bad) | 3 | .149 .176 .214 | 3 |
| ep09 (owner bad) | 3 | .109 .148 .268 | 2 |
| ep12-27 | 84 | median .208 | 48 |

- **The 0.22 MCU floor flags 7/13 MCU panels of the owner-good episodes** (5/6 of ep07). Today's advisory is therefore miscalibrated against the owner's own eye.
- **Floor candidates (MCU):**
  - 0.15 flags 1/13 good, 3/6 bad, 14/84 of ep12-27;
  - 0.16 flags 1/13, 3/6, 16/84;
  - 0.13 flags 0/13, 1/6, 8/84.
- **Close:** ep12-27 n = 23. A 0.25 floor flags 2/23 (today's 0.32 flags 8/23). The owner-judged set has only 2 closes (ep09 .27/.33), which is uncalibratable.
- **Plan:** move the advisory MCU floor to **0.15** and the close floor to **0.25**, still advisory.
  - The owner's bad episodes were bad for other reasons (template copies, synopsis), so G-FRAME can **never** go hard on this set.
  - The cut must be sized against the 0.15 floor from the planned-size words, not the canvas (H3 data: a bigger canvas draws wider).
- **Confidence:** 95 % that 0.22 is wrong (7/13 good-episode MCU panels flagged); about 70 % that 0.15 is the right advisory line (n = 13 good).

### 3.2 Ghost check on the ep18-27 narrator takes (H5)
- **The ghost IS in the staged reference.** Every ep18-27 narrator take stages `sheet_front_28241af7.png` (the crop of the ghosted `sheet.png`, md5 4d5059f4), and its right edge holds the translucent backdrop face at mid-height (`R_sheet_front.jpg`).
- **Takes:** 20 narrator takes, 2 per episode, chosen at random from the takes whose graph stages that crop. Frames at 50 % and 90 % (40 frames), read at 512 px per tile by eye: **0/20 takes show a translucent face or a face in the backdrop.** The extra figures seen are planned cast (curate, artilleryman, wife, crowds).
- **Verdict:** H5 is **not supported at contact-sheet resolution** (0/20, 40 frames). H3 reads the reference for identity, not as a backdrop. **Retire H5. H6 (the ghost gate) is moot** for takes. The neutral tile prevents new ghosts in sheets anyway.
- **Limit:** 512-px tiles could hide a faint ghost under 30 px. A full-resolution pass on the 6 plain-wall frames (ep20 T20, ep22 T03, ep27 T24, ep18 T13, ep21 T16, ep24 T16) is a 10-min eye job if the owner wants it closed harder.

### 3.3 The two look-table parse faults (C2 #8): sized across all 29 books (`R_hairparse.py`, 281 dossier physicals)
- **(a) A negated hair sentence counts as an authored hair layer: 117/281 dossiers (42 %) in 29 books.**
  - Typical wording: "gives no height, build, **hair**, eye colour…".
  - Examples: Scarlet Watson, Lestrade, Gregson, Hope and Stangerson; Dracula's Van Helsing, Harker and Mina; Jekyll's Utterson.
  - Every one yields hair marker `''`, but `layers_in` reports a hair layer. **The commit-6 row fallback is therefore skipped on 42 % of all future books' dossiers.** This is the dominant case, not an edge case.
  - **Fix (95 %):** `layer_of` ignores a clause whose hair word sits inside a negation (`no|not|without|gives no … hair`, within one clause). Test on Watson plus 3 other books.
  - **Acceptance:** the WotW tables stay byte-identical, and the 117 reach the fallback.
- **(b) The colour comes from the first match in the clause, not the word next to "hair".** Cases:
  - Scarlet: "grey eyes under a tangle of **sandy** hair" (Wiggins) reads grey, and so does "pale blue eyes under light sandy…". The other 2 "sandy" rows read `''`, because **"sandy" is not in `HAIR`**.
  - WotW Gregg: "Sandy-ginger hair … bald crown" reads `bald` (adjacent: red).
  - Secret Garden Mary Lennox: "red in her cheeks" reads `red`.
  - **Fix (95 %, ≥ 4 cases):** take the colour from the adjective adjacent to `hair|haired`, the pattern the reader side already uses (`SEEN_HAIR`, `look_table.py:172`). Fall back to first-of only when no adjacent colour exists. Add `sandy` → `fair`.
  - **Judgement rows to leave alone:** "auburn greying" and "brown flecked with grey" read grey (that is the family the look shows).
  - **Acceptance:** WotW tables are byte-identical except Gregg. Check whether Gregg is in a shipped `looks.json` first; if so it is a ruling, not a fix.

### 3.4 Merged LoRA at P90
- The C2_B ceiling is **−1 to −3 min per episode**, and it overlaps the TE-eviction cost.
- The P90 gap is ≈ 0.9 h (6.9 → 6.0), and peer T's ledger puts it in relaunch and kill waste (ep21: 243 min "killed:session", 384 min of waste in all), not in per-take overhead.
- **Verdict: not worth it at P90.** Retire it from the speed list. It is a 21 GB re-bake with a PSNR ≥ 45 dB proof owed, for ≤ 3 min. Revisit only if a quality lever needs minutes and the P90 is under 6 h.

### 3.5 H1 / H2 / H7 / H8: which can reach 95 % cheaply

| H | Verdict | Why |
|---|---|---|
| **H1** narrow fault-set memory ("two identical no-progress climbs → terminal") | **Retire** (measured against it, 2 eps) | `c2\b\plan_climbs.json`, by count: **ep22** ran 61→61, 61→62, 61→62, 61→62, **then 61→44 and later 46→4**, and shipped from there. **ep21** ran 1→1 ×3, **then 50→13**. A skip after two no-progress climbs cuts both rescues and parks the series. A sha-level replay could only narrow it further, and counts already show progress after ≥ 3 stalls. |
| **H2** cure-rate router | **Can reach 95 % on the battery side for ≈ 0 GPU** | `plan_cures.one_position` and the invented-count drop are code. Replay them on the refused drafts under the whole battery: CPU, no paid call. The critic side needs LLM calls, so it is not cheap. Route the battery-only part as a build candidate, and the critic part stays a hypothesis. Peer T owns the plan ladder; hand it over. |
| **H7** bowler joins the brimmed family | **Cheap: ≈ 1-2 min of GPU at the next bench** | It needs ≥ 2 VL reads of real bowler looks. Read each **3× at seeds 11/111/211** (R4 shows single reads flip). Candidates: Scarlet rows whose cards say bowler/billycock (CPU grep of `refs.json` first). If none exist on disk, retire until a book has one. |
| **H8** G-LINEAGE hard | **Retire for WotW; keep advisory** | WotW is finished (27 chapters) and has no per-episode look pictures under `library/`. A cast-wide stylized set will not exist until a new book draws ≥ 2 characters' looks. Revisit at that book's ep02. |

---

## 4. For the cycle-3 verdict, in order
1. **J1** (CPU, 100 %): correct carry #9 and add the reader-size lesson.
2. **§2.1-2.2** (100 % mechanics, owner-ruled): the new `image_krea2_cinematic_2x_neutraltile_visurena` file plus `refs_pack.T2I`, a `load_workflow` test, and the `job_from_row` mapping decision. `book_title` is a separate yes/no.
3. **§3.3 (a)** (95 %, 117 dossiers): negated hair is not authored. **§3.3 (b)** (95 %, ≥ 4 rows): the adjacent colour, plus `sandy`.
4. **§3.1** (95 % the old floor is wrong): G-FRAME advisory floors MCU 0.15, close 0.25.
5. **Bench (≈ 25 min GPU in all):** J2 seed-only flips with the beam-2 arm (≈ 15 min); §2.3 streak arms (≈ 6 min); H7 bowler reads (≈ 2 min).
6. **After J2:** J3 confirm-before-refuse, replayed on the owner-judged fixtures before wiring.
7. **Retire:** H1, H5/H6, H8 (WotW), merged LoRA. **Route to the content-rule owner:** J5 (banned-noun and lettering rules on true reads).

**Publishable (flag):**
- **"Your VLM judge is deterministic but not stable."** A seeded-sampler VL gate agrees with itself on identical pixels (2/2, and by code), yet flips count fields on 6-16 % of near-identical frames, and a content cache freezes whichever sample came first. The sticky-cache effect on judged-generation loops is a general finding.
- **"Dossiers that say what they don't say":** 42 % of LLM-written character dossiers across 29 public-domain books list "hair" inside a negation. A layer parser counts it as authored.

Sources:
- [Thinking Machines: Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference)
- [Unsloth: Qwen3-VL how to run (Qwen's official sampling settings)](https://unsloth.ai/docs/models/tutorials/qwen3-how-to-run-and-fine-tune/qwen3-vl-how-to-run-and-fine-tune)
- [Qwen3-VL generation parameters (mirror)](https://mintlify.wiki/QwenLM/Qwen3-VL/inference/generation-parameters)
