D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\c2\C2_owner_sheet.jpg

# CYCLE 2: build + bench report

2026-10-11. Builder for `C2_verdict.md`.
- Commits 1-9 landed test-first. Commit 10 (the QC memo) was **dropped by its own precondition (d)**: it would have saved nothing.
- One GPU bench ran on the production ComfyUI. The engine was never relaunched and the queue was empty at the start: **75.3 of 90 minutes, every block run, nothing retried**.
- $0. Nothing under `library/*/episodes/` or `library/*/refs/` was written.
- **Nothing was adopted from the bench.** CK8 for dialogue failed its rule, and the framing arms missed the face bar.
- The three owner-sheet items (P-WORDS v3, 992, the neutral tile) are on the sheet and **not adopted**.

**Evidence folder:** `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\c2\`
- `C2_owner_sheet.jpg`: the deliverable, three bands, each headed by its price.
- `review\`: every new dialogue take muxed with its recorded line (12 mp4s, on disk, not committed). Files:
  - CK8 bench: `D1_A1_s2`, `D1_CK8_s2`, `D2_CK8_s2`, `E10_A1`, `E10_CK8`, `E15_A1`, `E15_CK8`
  - 992 takes: `S6_992_A1`, `D1_992_A1`, `D2_992_A1`
  - v3 panels: `S4_v3_A1`, `S6_v3_A1`
  - each named `<tag>_review.mp4`
- Contact sheets:
  - `framing_arms_contact.jpg`: block 3, eight shots × shipped / (b) / (c) / (d)
  - `pwords_grids_v2_v3.jpg`: the six grids, shipped v2 against v3 words at the same seed
  - `narrator_today_2x_ghost.jpg`, `narrator_neutraltile_2x.jpg`
  - `ragged_legs_1x_presave_neutral.jpg`
  - `fresh_s3_today_vs_neutral.jpg`, `fresh_s4_today_vs_neutral.jpg`
- Numbers:
  - `bench.log`
  - block measures: `b1_measures.json`, `b2_judge.json`, `b3_measures.json`, `b3read.json`, `b5_measures.json`
  - take measures: `measures_c2.json`, `tails_c2.json`, `lag_c2.json`
  - crop-to-plan: `crops.json`, `cropread.json`
  - CPU replays: `replay_fresh_brief.json`, `replay_gframe.json`, `replay_lineage.json`, `scarlet_looks.json`

**Scripts and raw renders:** `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c2b\`
- `bench_c2.py` (the driver), `post_c2.py` (the CPU measures), `sheet_c2.py` (the sheet), `prep_grids.py` (the shipped-grid byte check)
- `replay_fresh_brief.py`, `replay_gframe.py`, `replay_lineage.py`, `replay_scarlet_looks.py`
- render folders: `grids\`, `looks\`, `panels\`, `runs_b2`, `runs_b4`, `runs_b5`

## Commits

| # | sha | title (short) |
|---|---|---|
| 1 | 62f35de | The ep11 regen goes green: a cast tag quotes the row OR the card's own chapter words |
| 2 | 92201a8 | The book_title lint goes green without changing the book video |
| 3 | 314b168 | [arch] Drop the fresh_brief rung: improve x2 → model_tier → terminal |
| 4 | 34f16c1 | LOOK-STATE headwear family, narrow: brimmed = {felt_hat, other_hat} |
| 5 | 6f1dc54 | The writer's hat words: top hat, billycock, pork-pie, straw hat |
| 6 | 4bcd813 | Look-table writer: first_chapter, and the head from the bound row |
| 7 | 07b8f1e | The regrid bar counts face-visible panels |
| 8 | e97bc9a | [arch] G-FRAME, a measurement only (advisory) |
| 9 | bf6b806 | [arch] G-LINEAGE, advisory |
| 10 | — | **Dropped.** Precondition (d) measured a saving of 0. See below. |
| bench | (this commit) | Bench evidence, the skill's bench lines, the GATES arm-rule amend, this report |
| comfy_studio | 1e032e9 | New files only: `image_krea2_cinematic_2x_presave_neutraltile_visurena` (branch `poc/2k-video-pipeline`) |
| post-bench A | — | **Not built.** CK8 for dialogue failed block 2. |
| post-bench B | — | **Not built.** Neither framing arm reached median face_h 0.25. |

### Deviations from the verdict's wording (each one forced by a measure, each in its commit message)
- **#5 felt hat.** The verdict's `felt\b[\w\s-]{0,20}\bhat` failed the verb guard ("he felt for his hat"). It is tightened to the verdict's own fallback, `\bfelt hat|\bfelt\s+[\w-]+\s+hat`.
  - The reader side moved too, as the verdict warned, and two G-LOOK-PANEL tests went red.
  - The reader's straw hat is unmeasured, so `panel_content` reads free text through `READER_HEADWEAR`: the writer's table plus the old `boater|straw hat` row. The reader now moves only on the new words.
- **#6 head fallback.** The bound row lends the head **for hair and face only, never the hat.**
  - With the hat included, acceptance (c) failed: two WotW looks changed.
  - The landlord's `behind_the_bar` gained "Wearing: Hatless".
  - The neighbour's `common_evening` gained another chapter's straw gardening hat.
  - The cause: a row's `physical` carries one chapter's costume. Without the hat, WotW is byte-identical.
- **#9 age-up.** The marker `_young` cannot be a bare suffix test, because `brigham_young` is Brigham Young's name. An age-up is now one of two things:
  - a declared `age_up` on the row, or
  - a `_young`/`_child` row whose display name is not simply the id.
- **#9 Ferrier.** No row on disk marks Ferrier as an age-up, so the replay **declares** it.
- **#9 WotW calibration.** WotW has no look picture under `library/`, so the calibration runs on the 14 readable bench draws of the narrator's looks: one character.
- **Block 1 node ids.** `_presave` already uses node 14 for the 1x save. The neutral tile is nodes **15** (CLIPTextEncode, style words only) and **16** (ConditioningZeroOut).
- **Block 3 control.** Each control is the shipped grid's own `.txt` plus its staged bytes, verified against the record's `inputs` hash. This is not today's `prompt_for`, because refs.json is bound to ch27 and would re-dress old chapters (C1 carry-over #10).
  - ep14's shipped words predate the geometry clause, so arm (b) is the control there.
  - Both ep14 (b) redraws came back bit-identical to the shipped grids: two more determinism proofs.
- **Block 4 N25.** The verdict calls ep25 `fulham_road` a night exterior. Its plan says hard afternoon sunlight, so it was drawn as written.

## Per issue: before → after, measured

| Issue | Before (measured) | After (measured) | Verdict bar | Met? |
|---|---|---|---|---|
| **ep11 regen (#1)** | `test_the_plan_script_regenerates_its_plan[...-ep11]` failed: the artilleryman's hair fragment was refused | passes; every other regen case byte-identical (35 passed, 6 strict xfail) | (a)-(d) | **met** |
| **book_title lint (#2)** | 1 failed (raw `placed.json` read) | passes. `cold_candidates` equals a frozen copy of the old body on WotW (27) and Scarlet (14), with sharpness held constant. `studio/book_title.py` untouched; the peer file had no uncommitted edits | (a)-(c) | **met** |
| **fresh_brief rung (#3)** | ladder improve ×2 → fresh_brief → model_tier | improve ×2 → model_tier. Replay: removing the fresh_brief draft changes **exactly one** climb's kept count (ep18 14:21, [3,3,1,58→58]), as the verdict predicted | (a)-(e) | **met**; watch line in LESSONS |
| **LOOK-STATE headwear (#4)** | fresh_s0/s1/s2 refused (felt_hat vs other_hat) | re-judged from the C1 evidence: s0-s2 pass on headwear; ghost_2x still fails on beard; the ep25 boater reads and a boater-for-felt read still refuse | as stated | **met** |
| **writer hat words (#5)** | 8/61 WotW looks mis-marked | re-deriving the 61 changes **exactly J's 8 rows**; verb guard holds | (a)-(d) | **met** (tightened regex; reader table above) |
| **look-table writer (#6)** | `dossier_text` crashed on every real dossier; Scarlet: 11/26 rows had no dossier and 9/15 dossiers had no head | Scarlet replay (scratch only, worst-case headless writer draft, no paid call): **26/26 rows, 0 refused**. Jekyll and Hyde still refused. WotW byte-identical. library/ size+mtime snapshot unchanged | (a)-(e) | **met** (hat excluded from the fallback; 2 parse-precision faults logged) |
| **regrid bar (#7)** | C1 ep25 regrid 2/4 FAIL (back view + wide counted) | **2/2 PASS**; ep25 round 0 **0/1 FAIL** (still catches the beardless look); ep27 study_table **3/3 PASS**; an empty denominator is unmeasurable | as stated | **met** |
| **G-FRAME (#8)** | no framing measure | `face_h`/`planned_size`/`frame_advisory` in panel_dq.json. The 396-panel replay reproduces F's per-(size, shape) medians in **every cell (0 beyond ±0.005)**. MCU: 84 panels, median 0.208, 48 flagged; close: 23, 8 flagged. Ladder and verdict unchanged | (a)-(c) | **met** |
| **G-LINEAGE (#9)** | redraws staged unchecked | Scarlet flags **exactly** Hope 8826eb07 (0.43-0.46) and Brigham c9192677 (0.16-0.23); Ferrier (0.58-0.59) noted as an age-up; the rest pass. WotW narrator looks vs base: n 14, min 0.70, median 0.81, 0 under 0.60 | (a), (b) | **met** (Ferrier declared; WotW one character) |
| **QC memo (#10)** | QC ran 7× on each of ep20, ep21 and ep24 (6.6-12.2 min a run) | **not built**. timing.jsonl has no sub-check split. 20 of 21 reruns followed an assemble that wrote **new master bytes** (md5 of master_iterN). The one identical pair (ep20) was already re-measured for a code change. Step 11 already reuses a report on identical bytes + code | (d): drop if it saves nothing | **dropped, as specified** |
| **Determinism (block 0)** | — | ep16 s13 redrawn from its shipped text and verified staged bytes at seed 40513: **bit-identical** to the shipped grid | bit-identical, or stop block 3 | **met**; block 3 ran |
| **Ghost faces (block 1)** | narrator base sheet: ghost "by mechanism" | `_presave` replay from the sheet's embedded graph = shipped sheet.png **(PSNR 99)**. The 1x is clean; the 2x has the backdrop face. **Case 2 is now measured USDU.** Neutral tile: **0 ghosts** on narrator, ragged_greyed and 2 new seeds (today: 1 + 1). Trousers at 0.96-1.06 of today's. Head facenet vs 1x **0.001-0.015 lower** than today's (narrator .953 vs .964, s3 .936 vs .937, s4 .891 vs .906). By eye, the tweed gains red/purple streaks | ghosts 0; trousers ≥ 90 %; head ≥ today's | **2 of 3 clauses met; head clause narrowly missed.** Owner ruling regardless |
| **CK8 for dialogue (block 2)** | dialogue on BASE; the C1 rule had no sounding-tail case | rule 1: identity within floor (σ_seed 0.0182 with the new D1 pair, floor −0.036; D1 −0.031, D2 0.000) but **banding mean fault**. Rule 2: ep10/T21 CK8 says **"keep moving" vs A1 "moving"** (not a subset); ep15/T21 mouth tail ratio **1.14 vs A1 0.94-0.97**. Rule 3: D1 A1 lag unmeasurable (corr 0.28); ep10 and ep15 equal. Speed: sampling 30-45 % faster | all of (1)-(3) | **NOT met. Measured "no"**: dialogue stays on BASE. Identity sign tally 4/8 negative, so "CK costs ≈ .01" is not supported |
| **Framing arms (block 3)** | shipped MCU median face_h 0.189 (8 shots) | (b) no geometry: **0.196**. (c) + CLOSE-UP words: **0.226**. (d) 2048: **0.150-0.178** (smaller faces). Seams 0, people 1 everywhere. Coins, bag and newspaper read on every arm (newspaper lost on (d)). (c) changes costume by eye (ep23 suit → torn shirt) and drops the ep14 s22 satchel. Rooms hold in (b)/(c) | median ≥ 0.25 and content 8/8 | **NOT met**: (b) and (c) out. (d) = data for H3: the bigger canvas drew *wider* |
| **Owner sheet (block 4)** | — | 6 v3 grids at shipped seeds; 2 takes on v3 panels; **992 on S6, D1 and D2** (all three ran, 992×992 by ffprobe, no size fault). **S6 at 992 drew a grey-haired, grey-moustached narrator** (identity .489 vs .730 at 768); D1 .823 (vs .837), D2 .891 (vs .875). 992 sampling 2.2-2.4×, whole take 1.8-2.0× (S6 248 vs 131 s, D1 145 vs 82 s, D2 341 vs 171 s) | gather only | **done** |
| **Prewarm (block 5)** | overhead 11-15 s a take | 11.5 / 13.3 / 13.7 s after prewarm (controls 16.4 / 14.1 / 13.5 s); frames bit-identical (PSNR 99) | ≤ 4 s and bit-identical | **NOT met**: no take-step proposal (H10 stays a hypothesis; a merged LoRA is next) |

**The full suite.**
- After commit 2: 4 failed / 10438 passed. The 4 are pre-existing and unrelated: `test_llm` ×2 and `test_canon` (the models.yaml tiers moved to the SDK) and `test_episode_tail`.
- After all commits: **4 failed / 10496 passed** (the same 4). No redder.

## GPU minutes (`bench.log`)
- B0: 3.2 (cold Qwen load 188 s)
- B1: 6.8 (7 Krea2 2x)
- B2: 11.1 (7 takes)
- B3: 14.7 (16 + 4 grids), plus 9.0 for the VL read of 30 panels
- B4: 7.2 (6 v3 grids), plus 16.2 (2 v3 takes + 3 992 takes)
- B5: 5.7 (3 prewarms + 3 takes)
- post: 1.4 (the crop-to-plan VL read)
- **Total: 75.3 min**

## Projection against 6 h, stated honestly
The model is `c2/b/projection3.py` over ep19-27 (C2_verdict §2):

| Scenario | P50 | P90 | over 6 h |
|---|---|---|---|
| Baseline, measured | 5.68 h | 7.49 h | 3/9 |
| Cycle 1 as built | 5.60 h | 7.32 h | 3/9 |
| **Cycle 2 as built (+ commit 3 only)** | **≈ 5.0 h** | **≈ 6.9 h** | 2/9 |

What did not bank, and why:
- **Commit 10** was not built: 0 saving measured.
- **CK dialogue** failed, so the verdict's further −0.1 h P50 / −0.13 h P90 is not banked.
- **The P50 is under 6 h. The P90 is not.** It is set by relaunch-heavy episodes (ep21: 22 launches, 7 QC runs), not by renders.

If the owner adopts 992 from the sheet:
- everywhere: ≈ 5.6-5.9 / 7.3-7.4 h
- face-led tight shots only: ≈ 5.1-5.2 / 6.6-6.7 h
- On today's evidence, 992 must also clear a look check: S6 aged the narrator.

## Owner rulings: the sheet asks for these, nothing adopted
1. **P-WORDS v3 (band A).** Same composition at the same seed. The changes are subtle: warmer lamp, more brass and leather in S6; D1 and D2 near-identical; on N25 one panel's figure is redrawn. Take faces: S6 id .789 on v3 vs .730 on v2, S4 .794 vs .768; S6 banding .453 vs .414.
2. **992 (band B).** A budget trade over 6 h at P90. It is also now a **look risk** (S6 aged by the canvas, n = 1). The crop-to-plan column:
   - S6 is already at plan (no crop).
   - D1 crop loses the machine and the sky.
   - D2 crop loses books, chair, clock, lamp and table.
3. **Neutral tile (band C).** It removes the ghosts. The cost is a slightly lower head facenet and colour streaks on the tweed. It also asks for a ruling on re-drawing the narrator base sheet (a reference change for ep28+).
4. **6 h as P50 or P90.** P50 ≈ 5.0 h meets it; P90 ≈ 6.9 h does not.
5. **Carried, unchanged:** stubble wording, the Jekyll/Hyde sheets, shipped ep10/T21 and ep26/T25, and the Hope/Brigham Scarlet redraws (shipped, never overwritten).

## Architecture
- Changed this cycle, in the same commits:
  - `architecture/index.html`: episode/02 ladder, episode/08 G-FRAME, refs/02 G-LINEAGE
  - `architecture/README.md`
  - `architecture/decisions/2026-10-11_cycle2_ladder_frame_lineage.md`
- The bench adopted nothing, so it changed no stage, step or gate.
- **The claude.ai copy was not republished** (as instructed).

## Carried to cycle 3
1. **H1** narrow fault-set memory (two identical no-progress climbs); **H2** the cure-rate router replayed under the whole battery. Unchanged.
2. **H3, canvas vs grid shape:** the first same-words data says a 2048 1x1 draws *smaller* faces (.150-.178 vs .169-.208). The fix is not more canvas. Close words gained +.04, with costume drift.
3. **G-FRAME calibration** on the owner-judged episodes. The MCU floor flags 48/84 today.
4. **H5/H6 ghosts:** the narrator backdrop ghost is in the staged sheet for ep18-27. Check the frame-0 backgrounds of narrator takes. A ghost gate can be designed on the 1x/2x pairs now on disk (`c2b\looks\*_1x/_2x`).
5. **H7 bowler family:** still 0 VLM reads. No WotW look picture exists to read.
6. **H8 G-LINEAGE hard:** needs a cast-wide WotW set, not one character. Also, declare Ferrier's age-up on his row when Scarlet is next touched.
7. **H10 speed:** prewarm failed. A merged LoRA and the VAE mode are next. CK8 for dialogue is out until an arm passes the sounding-tail pair.
8. **Two look-table parse faults** (commit 6): a negated hair sentence counts as authored (Watson); "grey eyes … sandy hair" reads grey (Wiggins).
9. **The reader varies on identical pixels** (the S6 no-op crop read "mustache" once and not once). Any content gate that diffs two reads needs two reads.
10. **Carried from C1:** room tone, the Scarlet dq lag blindness, the APPEARANCE regex precision. Also the full-suite pre-existing reds (`test_llm` ×2, `test_canon` tier params, `test_episode_tail`), not this cycle's.

**Publishable (flag):**
- **"The answer already existed":** an LLM self-repair ladder's kept draft came from its history-free rung once in 40 terminal climbs. The same-fault re-climbs progressed in 5 of 10.
- **One prompt per tile:** USDU ghost faces, proved by a bit-exact replay from the PNG's embedded graph (1x clean, 2x ghosted), and removed by a style-only tile prompt.
- **Planned size vs drawn face height:** 396 storyboard panels plus the word and canvas arms. A bigger canvas draws wider; words buy +.04.
- **Head-crop lineage check:** calibrated same-man 0.80-0.96 vs cross-person p95 0.45. It flags exactly the two Scarlet redraws.
