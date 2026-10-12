# C2 verdict: the cycle-2 skeptic on C2_J, C2_F and C2_B

2026-10-11. Read-only, CPU only. Nothing rendered, no code or workflow edited, nothing committed. This file is the only thing written.

**Bar (CYCLES.md):** build only at 95 % = measured on the artefact, in at least 2 independent cases, and surviving this review. Anything weaker is a hypothesis or a bench arm.

**Inputs:** `C2_J_looks_judges.md`, `C2_F_framing_quality.md`, `C2_B_speed_budget.md`, `CYCLE_1.md`, `C1_verdict.md`, `CYCLES.md`, `.claude/skills/episode/LESSONS.md`, and the scratch folder:
`D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c2\` (`b\`, `F\`, `ghost_eye\`, the contact sheets).

---

## 0. What I re-checked myself

| Claim | My check | Result |
|---|---|---|
| J 1a: LOOK-STATE has no headwear family | Read `studio/look_table.py:177` `family()` and `studio/judges/look_state.py` `marker_faults`; `panel_content.py:262` uses the same compare | **CONFIRMED.** `family()` groups hair colour only; headwear is exact string equality. |
| J 1b: the writer regex mis-maps hats | Read `HEADWEAR` (`look_table.py:126`) | **CONFIRMED by reading.** "silk top hat" misses `top-?hat` and `silk hat`, falls to `other_hat`; "straw hat" → `boater`; "pork-pie" and "billycock" are absent. Note: `panel_content` runs the **reader's** words through the same table (`first_of`), so a regex change moves both sides. |
| J 2: back views in the regrid bar | Read `scripts/refs/look_replay.py:61-75` | **CONFIRMED.** `tally` divides by every read panel. It is a bench tool, not a production gate. |
| J 3: USDU paints faces from the full prompt | Read the graph **embedded in** `library\20260827135508_the-war-of-the-worlds\refs\characters\unnamed_first_person_narrator\sheet.png` (PNG `prompt` chunk) and opened `narrator_sheet_ghost.jpg` | **CONFIRMED, and better than J said.** Node 12 `UltimateSDUpscale.positive = ['5',0]` (full subject prompt), 1024 tiles, denoise 0.2, seed 0. By eye: a large translucent moustached face in the backdrop between the front and ¾ figures, and a second one at the right edge behind the last figure. The sheet's whole graph (KSampler seed **4165438081**, er_sde, 8 steps, 1536x1024) is on disk, so case 2 can be **replayed exactly** with a 1x save: the USDU attribution for the narrator moves from "by mechanism" to a measured A/B in the bench. |
| J 4: `dossier_text` crashes on every real dossier | Read `studio/look_timeline.py:46`; loaded three Scarlet dossiers | **CONFIRMED.** `appearances` is `int` in each; `min(int)` raises. Only caller: `scripts/refs/looks_table.py:34`. The test fixture hand-writes a list (fixture drift). |
| J 5a: Hope and Brigham Young are two men each | Opened `lineage_scarlet.jpg` | **CONFIRMED by eye.** Brigham c9192677 is a lean, dark-haired, clean-shaven younger man; the ep10 sheets are a heavy grey jowled man. Hope 8826eb07 has long hair and a long full beard against short hair and a short beard. Ferrier ep08 → ep09-12 is a deliberate age-up redraw. |
| F 1: tight sizes drawn a size wide | Recounted `F\shipped_faces2.json`; opened `mcu_1x1_vs_2x2.jpg` | **CONFIRMED.** 85 MCU panels, 16 episodes, median face_h **0.207**, 66/85 (78 %) under 0.26. By eye, ep16 s13, ep17 s11, ep23 s2 and ep24 s8 are waist-up or seated full. **Correction:** F says the advisory floors "sit below today's medians on purpose". That holds for close (0.32 < 0.35) but **not for MCU** (0.22 > 0.207). An MCU floor of 0.22 flags more than half of today's panels. That is acceptable for an advisory, but it must be called what it is. |
| F 1b: geometry is appended to a tight 1x1 | Read `studio/storyboard_grid.py:353-357` | **CONFIRMED in code.** `brief_place` drops the description when every shot is TIGHT, but `geometry` is appended unconditionally. That it causes the drift is still 70 % (era-confounded). |
| F 1b: a 1x1 draws wider than a 2x2 | LESSONS line 182 | **CONTRADICTED by an earlier house finding.** "A mixed 2x2 drew a medium close as a full figure." The two measures disagree, so this stays a hypothesis. Arm (d) settles it. |
| F 1c-3: crop-to-plan drops planned props | Opened `crop_to_plan_demo.jpg` | **CONFIRMED.** The ep17 s11 coins and the ep17 s8 bag leave the frame, and the ep14 s24 newspaper is halved. **Not a production cure.** It goes on the owner sheet only as a strip. |
| B 1: CK dialogue test has no power | Read `C2_B` §1.2 against the C1 tails | **CONFIRMED.** All six rule renders have a silent or exempt tail. Rule (e) cannot fail on them. The two sounding-tail takes are on disk: `library\20260827135508_the-war-of-the-worlds\episodes\ep10\takes\r2v\T21.graph.json` and `...\ep15\takes\r2v\T21.graph.json`. |
| B 2.3 fix 1: `fresh_brief` buys almost nothing | Read `studio/plan_ladder.py` (`ladder`, `take`, `remember`); ran `b\kept_rung.py`; listed all 40 terminal climbs | **CONFIRMED, with one caveat.** The kept draft came from draft 15, improve1 7, improve2 12, **fresh_brief 1**, model_tier 5. The single fresh_brief "keep" is ep18 14:21 `[3,3,1,58 → 58]`, an anomaly rather than a rescue. **Caveat:** the 5 model_tier keeps (for example ep21 61→13, ep27 42→13) **edited the fresh_brief draft**, because `refused_plan()` is the last draft on disk. Without fresh_brief, model_tier edits improve2's draft instead, and that cannot be replayed. **Why it still clears 95 %:** a plan ships only through a battery pass. Battery-refused drafts are deferred, never shipped. On critic climbs, model_tier never writes (`not self.drafts`), and fresh_brief produced the kept draft in **0 of 13 critic climbs**. Dropping the rung can cost a later climb's time. It cannot ship a worse plan. |
| B 2.3 fix 2: fault-set memory saves 182 min | Listed every climb that started on the previous climb's end count (my script, the same `plan_climbs.json`) | **REFUTED as specified.** Of 10 such re-climbs, **5 made real progress**: ep19 35→20, ep22 46→35, ep23 40→17, ep25 36→13, ep26 39→35. The writer is stochastic, so the same faults do not mean the same outcome. Jumping straight to the terminal would have deferred those episodes, and a deferral parks the autopilot. That breaks memory `do-not-stop-until-done` and the "walls follow the chapter" lesson. **Not built.** |
| B 2.4: P50 4.2 h / P90 6.5 h | Re-ran `b\projection3.py` without fix 2 | **Overstated.** The honest numbers are below (§2, budget). |
| B 4.1: the `book_title` red test | `uv run pytest tests/test_only_reports_read_the_timeline_raw.py` | **1 failed, reproduced.** Only `scripts/episode/book_title.py:194,196` names `"placed.json"`. **`studio/book_title.py` does not, and is not touched.** |
| B 4.2: the ep11 regen | `uv run pytest -k "regenerates_its_plan and ep11"` | **1 failed, reproduced.** `cast_refs.tag` (`studio/cast_refs.py:283-291`) checks fragments against `pack_refs.character_row`, which since c300c4f drops the body's hair clause. |

---

## 1. BUILD list, in commit order (CPU, test-first, $0, no GPU or paid call in any test)

Each commit carries its skill lines (§5). **[arch]** commits update `architecture/index.html` and `architecture/README.md` in the same commit. Commit explicit paths only. Never stash, checkout or reset.

| # | Commit | Conf. | Acceptance test (written first, must fail first) |
|---|---|---|---|
| 1 | **The ep11 regen goes green: `cast_refs.tag` checks a quote against the row OR the card's own chapter words.** `body` also takes `profile.physical` plus `profile.wardrobe[<the chapter's look>]` from `analysis/characters/<who>.json`. Nothing else changes, and the tag is never staged. | 100 % | (a) A fragment that `row_text` drops but the card says is accepted. (b) A fragment neither says is still refused with the same `ValueError`. (c) `test_the_plan_script_regenerates_its_plan[20260827135508-ep11]` passes. (d) **Every** parametrized regen case (WotW ep01-14, Scarlet ep09-14) stays byte-identical. No `plan.json` is rewritten. |
| 2 | **The `book_title` lint goes green without changing the book video.** (i) `studio/episode_home.py` gains `shipped_timeline(book, number) -> dict \| None`. It reads `placed.json` as it stands and is documented as history for a report or compilation, never fed to a render. (ii) `scripts/episode/book_title.py` `cold_candidates` swaps `(ep / "placed.json").exists()` for `episode_home.has_timeline(book, n)` and `read_json(ep / "placed.json")` for `episode_home.shipped_timeline(book, n)`. **No other line of either `book_title` file changes, and `studio/book_title.py` is not touched.** This is the peer session's file: check `git status` on it first, and if it carries uncommitted peer edits, stop and log rather than edit. Do **not** route it through `load_placed` (that refuses WotW ep02-07 and all 14 Scarlet chapters), and do **not** add it to `REPORTS`. | 100 % | (a) The lint test passes. (b) A fixture whose plan is newer than its timeline still yields candidates. (c) **Output-equivalence replay (CPU):** with `sharpness` monkeypatched to a constant, `cold_candidates(book, N)` for WotW and Scarlet returns a list equal to the pre-change function's (captured in the test from a frozen copy of the old body). No render, no upload, and no file under `compilation/` is written. |
| 3 | **[arch] Drop the `fresh_brief` rung.** `plan_ladder.ladder()` becomes improve × 2 → model_tier → terminal. The `FRESH_BRIEF` branch in `take()` and the module docstring go. `scripts/episode/step_02_plan.py` docstring follows. The `CONVERGED` rule and `remember()` are unchanged. | 95 % (§0) | (a) A FakeModel ladder test: the rung names are `[improve, improve, model_tier]`, and `brief_(fresh=True)` is never called. (b) A converged draft is still edited, never discarded. (c) On a battery climb, model_tier is handed the full merged refusals (they are no longer reset by a fresh brief). (d) A CPU replay over `b\plan_climbs.json` reports which climbs' kept count would change if the fresh_brief output were removed from the candidates (expected: ep18 14:21 only), and that is recorded in the commit message. (e) A watch line in LESSONS: log model_tier's input fault count on the next 3 episodes. |
| 4 | **LOOK-STATE headwear family, narrow.** `look_table.family("headwear", m)` maps `{felt_hat, other_hat} → "brimmed"`. Every other marker is its own family. **`bowler` stays distinct.** J's case for joining it has 0 VLM reads (§0); bench block 1d reads it. LOOK-STATE and G-LOOK-PANEL share the one function. | 95 % (7/8 reads) | Re-judging `bench_evidence\c1\looks_judge.json`: fresh_s0, s1 and s2 pass on headwear; ghost_2x still fails on `beard`; the `regrid_ep25_report.json` shipped reads still fail on `boater`. A boater-for-felt read still refuses. |
| 5 | **The writer's hat words.** `HEADWEAR`: `top_hat` gets `top[- ]?hat\|silk hat\|stovepipe`; `bowler` gets `bowler\|derby\|billycock`; `felt_hat` gets `felt\b[\w\s-]{0,20}\bhat\|pork-?pie\|slouch hat\|wide-?awake`; `boater` gets `boater` only. The order stays most-specific first. | 95 % on the writer side (8/61 by replay). The reader side moves too, because `panel_content` parses reader text with the same table. | (a) Re-deriving all 61 WotW looks changes **exactly** J's 8 rows. (b) A verb guard: "he felt for his hat" must **not** read `felt_hat`. Tighten to `\bfelt hat\|\bfelt\s+[\w-]+\s+hat` if that test fails. (c) Every plan-regen case stays byte-identical. (d) The full suite is no redder than after commit 2. |
| 6 | **Look-table writer: `first_chapter`, and the head from the bound row.** (a) `dossier_text` reads `card['first_chapter']`, and the fixture is rebuilt from a real dossier's keys. (b) `with_head` / `markers_from` take `fallback=row['physical']`, used per layer only where the dossier's physical has none. (c) A row with no dossier is built from its refs.json cards (indoor/outdoor) via `dossier_look`. **A Scarlet table is written only to scratch for replay. It is never written under `library\20260822113400_a-study-in-scarlet\`**: a `looks.json` there would switch Scarlet's `character_row` onto the table path and change shipped behaviour. | 100 % | (a) `dossier_text(jefferson_hope.json)` no longer raises. (b) The Scarlet replay builds 26/26 rows with 0 refused. (c) WotW tables are byte-identical. (d) Jekyll and Hyde are **still** refused ("head unauthored"). (e) No file under `library/` changes (a `git status` assertion in the replay script). |
| 7 | **The regrid bar counts face-visible panels** (`look_replay.tally`). Exempt a cast panel only when its `frame` matches `from behind\|seen from behind\|back to (the )?camera\|walking away`, or its size is wide, extreme_wide or establishing. **Over-the-shoulder is NOT exempt**: an OTS panel faces one of its two people, and the panel rule cannot tell which (0 measured cases). A denominator of 0 reads **unmeasurable**, never passed. | 95 % | ep25 c1 regrid: 2/2 PASS. ep25 round 0: 0/1 FAIL. ep27 study_table: 3/3 PASS. A face-visible panel with no face read counts as a miss. |
| 8 | **[arch] G-FRAME, a measurement only (advisory).** `panel_dq` already computes YuNet face heights (`PRESENT_SCORE`). For every faced, non-back panel it writes `face_h` and `planned_size` into `panel_dq.json`, plus `frame_advisory: true` when an MCU is < 0.22 or a close is < 0.32. The record says these floors are **uncalibrated and above today's MCU median**. There is no cure, no wall, and no ladder effect. | Issue 95 % (85 MCU, 16 episodes, by eye). Floors 0 % calibrated, hence advisory. | (a) A replay over the 396 shipped panels reproduces F's table within ±0.005. (b) The panel verdict, ladder and terminal are unchanged on a fixture (an advisory cannot climb). (c) The GATES line says "advisory until calibrated on the owner-judged episodes". |
| 9 | **G-LINEAGE, advisory.** In the refs step, on every new sheet version of a cast row: head-crop (top 35 %) MTCNN at p > 0.95, then the VGGFace2 cosine against every earlier staged version of the same row. A pair < 0.60 on a row with no `_young` / age-up marker writes an advisory into `audit/`. **It is not a refusal**: the 0.60 line is calibrated on Scarlet's photoreal sheets only, and the WotW stylized faces are unmeasured. | Issue 95 % (Hope, Brigham, by eye). Threshold 95 % on Scarlet only. | (a) The Scarlet replay flags exactly Hope 8826eb07 and Brigham c9192677, notes Ferrier as an age-up, and passes Holmes, Watson, Lucy, Drebber and Lestrade. (b) **A WotW calibration in the commit:** each WotW look picture against its own base sheet (same man by construction) is scored and its distribution recorded. Hard promotion is a cycle-3 decision on that distribution. |
| 10 | **QC memo on input hashes.** A QC sub-check reads its cached result only when the master sha256, the lines text, the thresholds file **and the sha of the sub-check's own module source** are all unchanged. Any change re-runs it. | Issue 95 % (QC reran 4-7× on 4/9 episodes). The saving is a hypothesis: B assumed half. | (a) A relaunch with unchanged inputs and code hits the cache and writes the identical verdict. (b) Editing the checker's source invalidates the cache (the guard against a stale pass, memory `a-fix-that-changes-nothing`). (c) A new master invalidates it. (d) Before building, the builder reads the qc sub-check split from the run logs. If no sub-check is ≥ 1 min, this commit is dropped as a fix that saves nothing. |
| post-bench A | **[arch] CK int8 attention for dialogue**, only if bench block 2 passes: `takes_r2v` returns the CK workflow for both lanes. | from the bench | A test that the dialogue lane names `..._ckattn_comfyorg`, and `knobs()` reads it back. GATES' arm-rule line notes the sounding-tail pair. |
| post-bench B | **The tight-grid words**, only if bench block 3 adopts arm (b) or (c) by its rule: drop `geometry` when every shot in the grid is TIGHT (b), and/or the one-notch-tighter wording (c), in `grid_prompt_v2`. | from the bench | The prompt-text test for a TIGHT-only grid; a mixed grid is byte-identical; every plan-regen case is unchanged. |

**Not built (and why):**
- **Fault-set memory (B fix 2).** Refuted: 5/10 same-count re-climbs made progress (§0). A narrower form goes to cycle 3 (H1).
- **The cure-rate router (B fix 3).** It is an upper-bound measure (80 %), and its code cures (`plan_cures.one_position`, the invented-count drop) have never been replayed on the real drafts under the whole battery. Lesson `a-cure-is-judged-by-every-gate` (trim_style) applies (H2).
- **Crop-to-plan.** It cuts planned props on 3 of 6 demo panels.
- **The track-aware `look_id_at` (J 5b).** The mechanism is certain, but there is no live consumer (Scarlet has shipped, Jekyll is unstarted) and ch13 needs scene granularity (H4).
- **Prewarm, merged LoRA, VAE.** Bench or hypothesis (§2, §3).
- **The neutral-tile workflow in production, P-WORDS, 992.** Owner eye (§4).

---

## 2. ONE GPU bench, ≤ 90 min

**Preconditions:**
- Commits 1-10 have landed. ComfyUI is up and the queue is empty. **Never relaunch it.** If it is down, stop and tell the owner.
- Every arm's `knobs()` reads back its scheduler, attention, canvas and prompt version. ffprobe reads every take's size.
- No output goes under `library/`. Every render goes to `scratchpad\c2b\`, and the evidence to `docs\audit\2026-10-10_continuity_retro\bench_evidence\c2\`.
- New workflows are new files only, in `comfy_studio\workflows\image\`: `image_krea2_cinematic_2x_presave_neutraltile_visurena.json` plus its manifest, copied from `_presave`. The one change is that a new node 14 `CLIPTextEncode` with the house style words only (no subject) feeds `UltimateSDUpscale.positive`, and its `ConditioningZeroOut` feeds `negative`. Denoise 0.2, 1024 tiles and seed 0 are unchanged. The existing files are never edited.

**Blocks run in this order.** Each block is independent; a stopped block is logged, never retried. **Hard stop at 90 min.**

| Block | What | Renders | min | Pass / stop rule |
|---|---|---|---|---|
| 0 | Engine and queue check. Determinism: re-draw 1 grid from the block-3 list (ep16 s13) at its shipped seed through today's v2 | 1 grid | 2 | Not bit-identical to the shipped grid → **stop block 3** (framing has no control). Other blocks go on. |
| 1 | **Neutral-tile A/B (ghosts).** (a) The narrator base sheet, re-run from the graph embedded in `sheet.png`, through `_presave` (saves 1x + 2x), then through `_neutraltile`. (b) ragged_greyed old prompt at seed 4165438081 through `_neutraltile` (the C1 `_presave` render is the control). (c) 2 new look seeds × {today, neutraltile}. (d) **CPU/VL, ~1 min:** LOOK-STATE reads of 2 existing WotW bowler/billycock look pictures, if on disk, for the commit-4 bowler question | 2 + 1 + 4 Krea2 2x | 11 | (a) The `_presave` 2x must match the shipped `sheet.png` (PSNR ≥ 40 dB). If it does not, the replay is not the shipped draw: log it and judge only 1x against 2x. Ghost attribution: 1x clean and today's 2x ghosted makes case 2 **measured** USDU. **Neutral pass:** 0 faces outside heads by eye on every draw; trouser-crop Laplacian variance ≥ 90 % of today's; head-crop facenet against the 1x ≥ today's 2x against the 1x. **Production adoption is an owner ruling** (§4), whatever the result. |
| 2 | **CK8 for dialogue (B §1.3).** D1 s2 × {A1, CK8}; D2 s2 CK8; ep10/T21 × {A1, CK8}; ep15/T21 × {A1, CK8}, both at the shipped seed, built from the ran graph swapping only the attention node. **Precondition:** each staged guide's hash equals `placed.json`, or that take is skipped (spare: ep22/T12, exempt-prompt, tail dB only) | 7 | 15 | **Adopt only if all hold:** (1) rules (a)-(e) pass on D1 s2 and D2 s2, with σ_seed recomputed with the new D1 pair; (2) on both sounding-tail takes, CK8's tail words ⊆ A1's at the same seed, tail dB within ±6 of A1, and the lower-face tail ratio within A1's range; (3) `measure/mouth.lag` within ±1 frame of A1 on all four dialogue renders. Otherwise a measured "no". Record the identity sign tally (8/10 negative → "CK costs ≈ .01 facenet", measured). |
| 3 | **Framing arm (F §1c-2), reduced.** 8 shipped 1x1 MCU shots at shipped seeds (ep14 s22, ep14 s24, ep16 s13, ep17 s8, ep17 s11, ep19 s19, ep23 s2, ep24 s8). Control = the shipped panel (block 0 proves the redraw is exact). Arms: (b) no geometry for TIGHT-only grids; (c) (b) plus one notch tighter words; (d) v2 words at **2048² 1x1**, downscaled to 1024, on **4 shots** (ep14 s24, ep16 s13, ep17 s11, ep24 s8) | 8 + 8 + 4 | 14 | **Adopt (b) or (c) only if:** median face_h ≥ 0.25 over 8; **`panel_content` finds every named object on 8/8** (coins, bag, newspaper by name); people_check passes; 0 seams; and **G-SETUP / the eye read the same room as the shipped anchor** (geometry words drop, the one-room ruling holds by pixels). (d) is data for H3 (canvas against grid shape) and its +5-8 min per episode cost. **Not adopted in this cycle**: it adds minutes and needs P90 headroom. A (b) miss on content → (b) is out, whatever face_h does. |
| 4 | **The owner-eye sheet (§4).** (i) P-WORDS v3 grids at shipped seeds for the grids owning S6 (ep27 study_table), S4 (ep24 s12), S3 (ep24 s5), D1 (ep25 s21), D2 (ep27 study_reverse s25), plus the ep25 fulham_road night exterior: 6 grids. (ii) 768 takes on the v3 panels for S4 and S6 (production 8-step BASE, narration on CK8, as production): 2. (iii) **992** takes on production 8-step BASE for S6, D1, D2, panels cut by `panels.cut` and resized to 992 (no centre re-cut), with the overlay asserting 992 and ffprobe reading 992x992: 3 | 6 grids + 5 takes | 26 | Gather, judge nothing for adoption. Under each row: face px, facenet against the sheet, banding, clones, G-TAIL, whole-take seconds. **If the clock passes 80 min at the start of (iii), render 992 for D2 and S6 only.** |
| 5 | **Prompt-prewarm test (B §3.2).** Re-render the 3 block-2 A1 controls (D1 s2, ep10/T21, ep15/T21) with 3 prewarm prompts (nodes 5/6/7/18/8 plus a cheap output) queued first, then the 3 takes back to back | 3 + 3 prewarms | 7 | **Pass:** each take's non-sampling, non-decode time ≤ 4 s (against the 11-15 s measured) **and** frames bit-identical to the block-2 render (decoded-frame PSNR 99). **Skip the block if the clock is past 78 min.** A pass goes to cycle 3 as an [arch] proposal (a take-step queue phase), not a build. |
| — | Slack, model loads, ffprobe | | ≈ 11 | |
| | **Total** | | **≈ 86** | |

**Not in this bench:** 992 on S4 (row dropped for time; r2 already has a 4-step S4 at 992), G2 (speed only, ≈ −8 min, needs `ManualSigmas` first), room tone (C1 inconclusive, needs a `speech_end` that ignores a bed), Veda (needs ComfyUI ≥ 0.38, an owner install window), Qwen-Image-2.1-Turbo (cycle 3 with its own eye sheet), and a merged LoRA (only if prewarm fails).

**Budget, stated honestly** (`b\projection3.py` re-run without fault-set memory, P50/P90 over ep19-27, linear interpolation):

| Scenario | P50 | P90 | over 6 h |
|---|---|---|---|
| Baseline, measured | 5.68 h | 7.49 h | 3/9 |
| Cycle 1 as built | 5.60 h | 7.32 h | 3/9 |
| + commit 3 (no fresh_brief) | 5.04 h | 6.92 h | 2/9 |
| + commit 10 (QC memo, if half the reruns are saved; a hypothesis) | 4.91 h | 6.47 h | 2/9 |
| + CK dialogue (if block 2 passes) | **4.81 h** | **6.34 h** | 2/9 |
| (B's figure with fault-set memory, refuted) | (4.01 h) | (6.05 h) | — |
| + 992 everywhere (owner option) | ≈ 5.6-5.9 h | ≈ 7.3-7.4 h | ≥ 3/9 |
| + 992 on face-led tight shots only | ≈ 5.1-5.2 h | ≈ 6.6-6.7 h | 2/9 |

**The P50 sits under 6 h. The P90 does not, and has not since before cycle 1.** The episodes over the line are ep21 (22 launches, 7 QC runs) and one more relaunch-heavy episode. That is the mid-run relaunch fault that `drive-not-babysit` and `autopilot` already rule on, not a render cost. See owner ruling 4.4.

---

## 3. Hypotheses carried to cycle 3 (logged, not built)

1. **H1: a narrow fault-set memory.** Skip to the terminal only after **two consecutive** climbs ended on the identical sorted-refusal sha with no progress (ep22 08:30 → 09:08 at 61, ep20 04:15). Replay it on `plan_climbs.json` first. It must cut 0 of the 5 progressing re-climbs.
2. **H2: the cure-rate router.** Replay `plan_cures.one_position` and the invented-count drop on the real refused drafts of the 48 climbs under the **whole** battery and the critic, before any routing. The cure rates are an upper bound.
3. **H3: canvas vs grid shape for framing.** 1x1 against 2x2 conflicts with LESSONS ("a mixed 2x2 drew a medium close as a full figure"). Block 3(d) gives the first same-words canvas data.
4. **H4: the track-aware `look_id_at`** from `analysis/timeline.json`. It needs scene granularity for Scarlet ch13. Design it with the Jekyll ruling.
5. **H5: the narrator backdrop ghost reached shipped takes** (ep18-27). The cheap check is an eye pass on the frame-0 backgrounds of narrator takes, or a VLM list on the 2x. Run it before any ghost gate.
6. **H6: a ghost gate.** MTCNN misses both ghosts and fires on heather. Only a VLM list or a 1x-vs-2x difference can work. Block 1 gives the 1x/2x pairs to design it on.
7. **H7: `bowler` in the brimmed family.** It needs ≥ 2 VLM reads of real bowler looks (block 1d).
8. **H8: G-LINEAGE goes hard** once the WotW look-vs-base distribution (commit 9) shows the 0.60 line holds on stylized faces.
9. **H9: prose naming hands or lap pulls a close wider** (p = .03, n = 8/15).
10. **H10: prewarm, merged LoRA, VAE slow mode.** Prewarm comes from block 5. The VAE first needs `phases.jsonl` to log VAEDecode alone (CPU).
11. **H11: Qwen-Image-2.1-Turbo** funds 992 or the 2048 1x1 in grid minutes. A picture change, so it needs its own eye sheet.
12. **H12: G2** (8-step at 6 calls). Speed only; worth it only if a quality lever needs the minutes.
13. **Carried from C1:** room tone (needs a bed-proof `speech_end`), the Scarlet dq `lag` blindness on WotW, WotW 14/15 vs Scarlet 2 sounding tails, and the APPEARANCE regex precision ("suitors" → `suit\w*`, J 5b).

---

## 4. Owner rulings (only the ones CYCLES.md reserves for him)

The builder produces **one sheet**, shows it to the owner, and adopts **none** of its three items.

**The sheet:** `docs\audit\2026-10-10_continuity_retro\bench_evidence\c2\C2_owner_sheet.jpg`. A `review\` folder beside it holds the takes muxed with their recorded line. Every tile is the same display size. Face tiles are 1:1 crops of the readable face box at 50 % of the take, scaled so the face box is the same height in every column (`contact.py faces`). Three bands, each headed by its price:

| Band | Header | Rows | Columns |
|---|---|---|---|
| **A: P-WORDS** | "v3 material words: +0 min per episode. A LOOK change." | S6 study, S4 two men + smoke, S3 frogs, D1 bearded look, D2 the wife, the ep25 night exterior | shipped v2 panel / v3 panel, same seed / (S4 and S6 only) take face on v2 (the existing A1 render) / take face on v3 |
| **B: 992** | "992 canvas: +45-65 min per episode → P50 ≈ 5.6-5.9 h, P90 ≈ 7.3-7.4 h (over 6 h). Face-led tight shots only: ≈ +15-22 min → P90 ≈ 6.6-6.7 h." | S6, D1, D2 (two if block 4 ran short) | 768 take face (existing) / 992 take face (new) / the same panel's crop-to-plan face (CPU, labelled "props lost: …" where `panel_content` loses one) |
| **C: neutral tile** | "Style-only tile prompt: +0 min. Adopting it means new draws only; re-drawing the narrator base sheet re-stages a new reference for every future WotW narrator shot (shipped files untouched)." | narrator base sheet; ragged_greyed | shipped 2x (ghosts circled) / today's 2x re-run / neutraltile 2x. Three crops each: the backdrop between figures, the face inset, and the trouser crop at 1:1 |

**The rulings:**
1. **P-WORDS v3:** adopt the material words, or keep v2.
2. **992:** everywhere, on face-led tight shots only, or not at all. This is a budget trade over 6 h at P90.
3. **Neutral tile:** (a) for new look and sheet draws, and (b) whether to re-draw the narrator base sheet (a reference change for ep28+). It is his call even if block 1 passes.
4. **Is the 6 h a P50 or a P90 ceiling?** The P50 meets it (≈ 4.8-5.0 h). The P90 (≈ 6.3-6.5 h) is set by relaunch-heavy episodes, not renders.
5. **Carried, unchanged:** stubble wording, the Jekyll/Hyde base sheets (Jekyll and Hyde stay refused by commit 9's wall), and the shipped faults ep10/T21 and ep26/T25. The Hope and Brigham Young redraws on Scarlet are also logged for him: shipped, never overwritten.

---

## 5. Skill text lines (each lands with its commit)

**LESSONS.md:**
- **A rung that throws history away rarely wins (commit 3).** Over 40 terminal plan climbs (ep17-27), fresh_brief produced the kept draft once, and that one was an anomaly. 547 of 849 rung minutes ran after the kept draft already existed. A rung is kept only while it is the source of kept drafts.
- **The same faults are not the same outcome (refuted fix).** 5 of 10 re-climbs that started on the previous climb's fault count made progress (ep23 40→17, ep25 36→13). A memory that skips them parks the series. Remember only "no progress twice".
- **One prompt per tile paints faces (commit-free, block 1).** USDU hands every 1024 tile the full subject prompt. A trouser or backdrop tile paints the subject's face: the ragged_greyed thighs and the narrator base sheet's backdrop, staged in ep18-27. A sheet's own PNG carries its graph, so replay it from there.
- **A reader's hat is a family, a writer's hat is a word (commits 4-5).** The VL reads a felt hat as `other_hat` 7/8 times. The judge compares families. The writer's table maps the book's words exactly (top hat, billycock, pork-pie, straw hat).
- **A tight size is drawn a size wide (commit 8).** 85 planned MCU panels over 16 episodes have a median face_h of 0.207, against about 0.30 that the cut words ask for. 78 % are under 0.26. A crop to plan buys the pixels but cuts planned props (coins, bag, newspaper), so it is not a cure.
- **A fixture typed by hand drifts from the contract (commit 6).** `appearances` is a count in every real dossier. The test's list hid a crash on the only writer path a new book takes.
- **A same-man redraw on one row is a different man (commit 9).** Brigham Young ep08 against ep10 has a head cosine of 0.16-0.24, near the cross-person median. A separate `_young` row holds about 0.6.
- **A test with no case that can fail it proves nothing (block 2).** The CK dialogue rule ran only on silent or exempt tails. A speed arm on dialogue is judged on a take whose control tail already sounds.

**GATES.md:**
- **LOOK-STATE / G-LOOK-PANEL:** headwear compares by family. Brimmed = {felt_hat, other_hat}. Every other marker, bowler included, is its own family.
- **G-FRAME (advisory, uncalibrated):** `face_h` against the planned size, written to `panel_dq.json`. Flag an MCU < 0.22 or a close < 0.32. No cure, no wall, until calibrated on the owner-judged episodes.
- **G-LINEAGE (refs, advisory):** a head-crop cosine < 0.60 between versions of one cast row, outside an age-up, writes an audit line. Hard only after the WotW calibration.
- **Plan ladder:** improve × 2 → model_tier → terminal.
- **Regrid bar (bench):** the denominator is face-visible cast panels. An empty denominator is unmeasurable.
- **BENCH arm rule (amend):** a speed arm on dialogue must also pass on ≥ 2 shipped takes whose control tail sounds above −45 dB.

**SKILL.md:**
- In the plan step: "improve × 2, then model_tier, then the terminal".
- In refs/looks: "a row with no dossier, or a silent dossier head, takes its head from the bound row's `physical`".
- In the grid step: "panel_dq records face_h against the planned size (G-FRAME, advisory)".

---

**Publishable (flag):**
- **"The answer already existed":** 64 % of an LLM self-repair ladder's time came after its kept draft, plus the refutation that the same faults mean the same outcome. A general finding about judged-generation loops.
- **One prompt per tile:** USDU ghost faces, with the embedded-graph replay and the MTCNN failure on stylized ghosts.
- **Planned shot size against drawn face height** across 396 storyboard panels, a measured instruction-following undershoot for Qwen-Image 2.1 (with the block-3 arms).
- **The head-crop lineage check**, calibrated same-man 0.80-0.96 against cross-person p95 0.45.

All four fit the planned public ref2va/storyboard bench.
