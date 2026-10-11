D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\c1\C1_seam_replay_contact.jpg

# CYCLE 1: build + bench report

2026-10-11. Builder for `C1_verdict.md`. All 10 verdict commits landed test-first, plus 2 follow-ups. One GPU bench ran on the production ComfyUI (no relaunch, queue empty at start): **69.4 of 90 minutes, every block run, nothing retried**. $0. No shipped file under `library/*/episodes/` was written.

**Evidence folder:** `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\c1\`
- `C1_seam_replay_contact.jpg`: the 13 seamed shots, shipped strip panel against the no-strip replay (the main deliverable)
- `C1_house_replay_contact.jpg`: the house setups, shipped anchor / shipped panel / replay
- `contact_S3_G1.jpg`, `S3_frogs_50pct.jpg`: the S3 frogs on A1, A3 and G1
- `faces_CK8_S4.jpg`, `faces_CK8_D2.jpg`: CK8 against A1 seed 1 and seed 2
- `fresh_contact.jpg`, `ghost_ab_legs.jpg`, `looks_judge.json`: the ragged_greyed look and the ghost A/B
- `regrid_contact.jpg`, `regrid_ep25_report.json`: the ep25 fulham_road regrid
- `cells_contact.jpg`, `contact_T04_T05.jpg`, `b5_measures.json`: Scarlet ep14
- `measures_c1.json`, `judge_c1.json`, `tails_c1.json`, `tails_room_c1.json`, `b2.json`, `bench.log`: the numbers

Scripts and raw renders are in `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c1b\`:
- `bench_c1.py` (the driver), `post.py` (the CPU measures), `make_arms_c1.py` (the new workflows)
- `runs_b0`, `runs_b3`, `runs_b4`, `runs_b5`, `grids\`, `looks\`, `regrid_ep25\`, `scarlet\`

## Commits

| # | sha | title (short) |
|---|---|---|
| 1 | 46e0a35 | The red size test reads the contract: 1 failed/16 passed → 37 passed |
| 2 | 9ed7073 | Bench rulers judge an arm against the control's own seed spread, not a 28 dB wall |
| 3 | a51ecef | G-GRID-SHAPE: a grid is 1 or 4 cells, never a strip [arch] |
| 4 | 0f6c92d | The seam rung and the refs-only fallback (owner ruling) [arch] |
| 5 | fda4b9f | Beard words come from the closed marker |
| 6 | f58cfa1 | G-LOOK-WORDS on the beard is a deterministic cure, then a wall |
| 7 | 2aeb777 | G-TAIL, the production tail gate on dialogue takes [arch] |
| 7b | 7778b97 | G-TAIL follow-up: casebook class `invented_speech`; the skill line out of the registry table |
| 8 | baf08c4 | The bench's room-tone guide arm |
| 9 | e83913a | A new look table refuses a character whose head is unauthored |
| 10 | 08e1210 | The legacy-path replay for Scarlet |
| bench | 06d8ade | Narration takes render on CK int8 attention (block 3 adoption) |
| comfy_studio | 26e7b82 | New files only: G1 `..._ref4_singularity_simple12_modeltc`, CK8 `..._ref8_crf_visurena_ckattn_comfyorg`, `image_krea2_cinematic_2x_presave` (branch `poc/2k-video-pipeline`) |

Owner rulings applied:
- **Seam fallback:** per-shot refs-only (`storyboard/refs_only.json`). The shot ships, and its fault is signed `refs_only: true` into the audit sheet.
- **ep10/T21 and ep26/T25:** left as shipped and logged as known faults. G-TAIL fails both on replay.
- **Jekyll/Hyde:** skipped. Commit 9 still applies.
- **Stubble:** not touched. Only the duration beard ("sixteen days of …") is rewritten. That changes 1 look across WotW and Scarlet. It is logged in LESSONS as a look decision the owner can veto.

## Per issue: before → after on the replay set

| Issue | Before (measured) | After (measured) | Verdict bar | Met? |
|---|---|---|---|---|
| **Red test** | 1 failed / 16 passed | 37 passed | file green | **met** |
| **Bench rulers** | 28 dB wall refused shipped A1 on 6/6 shots | Replay of r2: CK passes (a)-(d) and fails (e) on S4; shift6-beta fails (e) on "Heed."; A1 is classed as a new draw and never refused; D1 A0's clone is not a fault against itself | the 4 replay claims | **met** |
| **Seams (commit 3, block 2)** | shipped: 15/201 strip panels seamed. On the 13 replayed shots, the shipped panels read stacked 1.0 plus a seam line (instrument checked on ep22 s5, ep19 s17, ep20 s9) | **0 seams, 0 stacked on all 25 replayed panels.** 17 grids in all: 13 seam-setup grids and 4 house. By eye, every one is a single picture | 0 seams and 0 stacked | **met** |
| **The house reads as one room** | shipped house panels | ep26 villa, ep27 study reverse, ep11 study and ep11 dining replay the same house and room. Only ep27 has a stored anchor, and the replay matches it | eye | **met** (n = 4) |
| **Seam rung (commit 4)** | 16/18 seams shipped on keep_best | Tests only: isolate once outside the cap, then refs-only flagged. No GPU case, because no seam appeared in the replay | test | **met (CPU)** |
| **Beard look (commit 5, block 1a)** | ragged_greyed fresh: beard on **0/3** draws; LOOK-STATE read stubble or none | **3/3 draws have a grey-brown beard** by eye. LOOK-STATE reads `beard` on 3/3 | ≥ 2/3 read and eye | **met** |
| **LOOK-STATE headwear** | — | refuses all 3 draws: a battered brown felt hat read as `other_hat` | — | **new judge fault** (cycle 2) |
| **Beard tags (commit 6)** | ep25: 4/12 head tags bare | exactly those 4 gain the phrase; the other 8 are byte-identical | as stated | **met** |
| **ep25 regrid (block 1d)** | shipped: 0/4 narrator panels show the look | **2/4 by the reader.** The 2 misses are back views (shot 2 walking away; shot 4, a tiny figure in a wide), where no beard can be seen. Both face-visible panels show grey hair, beard and felt hat by eye | ≥ 80 % | **NOT met as written.** The bar counts back views; carried to cycle 2 |
| **Ghost faces (block 1b)** | 2 faces on the thighs (1 picture) | Same prompt and seed: **no face on the 1x decode, a face on the 2x USDU output.** Cause (b), the USDU tile pass. The new prompt's s1 and s2 draws look clean; s0 has a possible faint eye at the knee | log only | **cause found** (n = 1 prompt) |
| **G-TAIL (commit 7)** | 2/154 shipped dialogue takes speak into silence, ungated | Replay over 204 takes: **fails exactly ep10/T21 and ep26/T25** (the mouth branch, armed on 0 false fails), exempts the ep25/T21 laugh, and the 5 stale Scarlet guides read unmeasurable | as stated | **met** |
| **Look table head (commit 9)** | Jekyll/Hyde markers blank | refused "head unauthored"; WotW 0/47 refused | 0 refusals on the replay | **met.** Scarlet has no table, but 9/15 of its bound dossiers author no head (see carry-over) |
| **Scarlet legacy replay (commit 10, block 5)** | ep14 room drifted (text similarity 0.15). Holmes T04 id 0.673, Watson T05 0.764. Lip: T04 cannot tell (corr .18), T05 −1 frame | Cells drawn on the ep05 `hearth_night` room: the eye reads ep05's fireplace (left), the far windows and the red carpet. **id T04 0.853, T05 0.800, 0 clones.** Lip: T04 cannot tell (corr .20), T05 −2 frames (corr .48) | room by eye, id ≥ shipped, lag not worse | **room and id met. Lag is 1 frame later**, inside the 2-frame advisory tolerance. **New fault:** both cells came back wider than the planned medium close (waist-up and seated full) |
| **Determinism (block 0)** | — | S4 A3 re-render: PSNR 99 (bit-identical) | bit-identical | **met** |

## The speed bench (block 3)

**G1, the 4-step on the authors' grid (`simple`@12/3): OUT.**
- At 50 % the S3 frogs are smeared shapes on seed 1 and gone on seed 2. A1 shows five clear frogs (`S3_frogs_50pct.jpg`).
- The verdict's rule needs both seeds, so the 4-step stays unwired.
- G1's S4 tail is −56 dB (A3 beta: −30), so the trained grid does quiet the tail. It is still out on content.

**CK8, CK int8 attention on today's 8-step BASE: PASS, adopted for narration (06d8ade).**
- Same draw: PSNR against A1 seed 1 is 22.9-33.9 dB. The seed-to-seed distance is 13.1 (D2), 17.3 (S6) and 22.2 (S4).
- σ_seed (8-step) = .021, so the per-shot identity floor is −.042.
- Identity Δ: S4 −.030, S6 +.002, D1 +.016, D2 −.006. The dialogue mean is −.005.
- Banding and clones are unchanged.
- Invented speech: S4 seed 1 is −55.6 dB with no word; S4 seed 2 is −91 dB, silent. Both match A1's state.
- The face sheets are indistinguishable from A1 seed 1.
- **Sampling is 39-45 % faster** on the same shots (S4 66→40 s, S6 88→51 s, D2 121→67 s). Whole takes are about 30 % faster.
- **Dialogue stays on BASE**, because GATES' arm rule asks for D1 and D2 on a second seed as well. That is 2 renders in cycle 2.

**Room-tone tail (block 4): INCONCLUSIVE, nothing adopted.**
- The zero tail sounded on S4 seeds 1 and 4 (−30 dB) but invented **no word** on any of seeds 1, 3 and 4.
- With room tone: seeds 1 and 3 sit at the bed (−51 and −50 dB); seed 4 sounded at −39 dB; 0 words.
- The mouth ratio did not fall (.46 / .27 / .48 against .33 / .26 / .38).
- D2 with room tone stays silent (tail −53.7 dB, which is the bed).
- **A trap for any production room-tone guide:** `speech_end` reads a −50 dB brown-noise bed as speech in its 50 ms windows. The bench re-measured those takes against their zero guides.

**GPU minutes:**
- B0: 2
- B3: 25 (15 renders)
- B4: 8 (6)
- B1: 8 (4 Krea2, 4 VLM reads)
- B5: 6.5 (2 cells, 2 takes)
- B1d: 2 (2 grids)
- B2: 13.5 (17 grids)
- VLM regrid read: 3
- **Total: 69.4 min** (`bench.log`)

## Per-episode time projection against 6 h

- Today's 8-step baseline: **≈ 6.0 h** (BENCH_r2 §5).
- Commit 3 adds **+4.4 grid calls per episode** (ep19-27 replay, range +1 to +7) at the same megapixels. A warm 1x1 measured 15-21 s and a 2x2 66-102 s, so this is **about +1-2 min**.
- Commit 4 adds one 1x1 per seam (0 seams appeared in the replay): **~0**.
- Commit 7 adds a Whisper pass on the guide for loud dialogue tails (~12 %) plus FaceMesh on those, about 10-15 s CPU each, and a reseed on ~1 %: **about +1-2 min**.
- CK8 on narration: about 75 % of takes, each ~35-45 s faster. With retakes that is **about −15 to −20 min**.
- **Projection: ≈ 5.7 h, under the ceiling.** No owner budget ruling is needed.

## Carried to cycle 2

1. **LOOK-STATE headwear vocabulary.** `felt_hat` against `other_hat` refuses a correct hat (3/3). Either fold `other_hat` into the brimmed-hat family, or ask the reader for the closed word.
2. **The regrid bar counts back views.** Exempt panels whose plan asks for a back or far view, or tally face-visible panels only. Re-score ep25 and ep27 on that rule.
3. **CK8 for dialogue.** D1 and D2 at seed 2 (2 renders), then adopt or not.
4. **Ghost faces.** The USDU tile prompt paints faces. The cure to bench is a neutral tile prompt in a new `_neutraltile` workflow (A/B on the same seed). Scan every WotW look and sheet body crop for a second case first.
5. **Scarlet 1x1 cells drift wider than planned** when a room picture is staged (medium close came back waist-up and seated full). Check framing on the replayed WotW 1x1s too (G-SCALE / framing judge).
6. **Scarlet dossiers author no head** (9/15, Holmes included). Commit 9 would refuse a Scarlet look table. Read the head from `refs.json`'s `physical` before writing one.
7. **Room tone:** inconclusive at n = 3. A repeat needs a shot whose zero tail actually invents a word (S4 on CK at seed 1 did in r2), and a `speech_end` that ignores a bed.
8. **The ep21 seam setup.** The verdict named `pantry_door`, but the seamed shots 22-24 are in `kitchen_breach`; that is what was replayed. Likewise ep27 shots 10/16 are in `study_essay`, not `study_table`.
9. **Pre-existing red test, not mine:** `tests/test_only_reports_read_the_timeline_raw.py` (`book_title.py` reads `placed.json` raw). It arrived with the main-title commits. The full suite also shows `test_a_plan_script_regenerates_its_plan[...-ep11]` failing on `cast_refs` (the artilleryman row), which predates this cycle.
10. **The replay dresses WotW grids from the ch27 `refs.json` row.** For example, the ep22 s5 replay shows the narrator in his suit. This is a known limitation of replaying old chapters, not a production fault.

**Publishable (flag):**
- The calibrated non-inferiority rule, now with an 8-step σ_seed.
- Qwen-Image's own-grid-count on strips, with the 0/25 no-strip replay.
- The USDU tile pass as the source of ghost faces (1x against 2x, same seed).
- The "echo of the last word" G-TAIL replay (2/154).
