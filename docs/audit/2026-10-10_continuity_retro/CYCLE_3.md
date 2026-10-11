D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\c3\FINAL_before_after.jpg

# CYCLE 3 (final): build + bench + final measurement

2026-10-11. Builder for `C3_verdict.md`.
- **All 11 verdict commits landed test-first**, plus P1 (the neutral tile in production) and two suite follow-ups. P2 and P3 were not built, each by its own rule.
- **The bench ran 41.4 GPU-min** (budget 60). The **3B picture replay ran about 68 GPU-min** (budget 120). Total ≈ 110 GPU-min, $0.
  - ComfyUI was down during the morning build, until 11:33. It was never started or relaunched by me; the owner's main session brought it back.
  - Once it was up, the bench started at 11:45 and the GPU stayed fed to 13:36.
- **Nothing under `library/*/episodes/` or `library/*/refs/` was written.** Every replay wrote to scratch or to `bench_evidence/c3/`. No read touched the library VLM cache: every bench read used `run_text`, uncached.
- **The CPU lane was shared.** My 3A replay and the `tick_error` diagnosis were done first. A helper then:
  - fixed the `tick_error` loop (`50a35c8`);
  - built the downstream reserve and its companion rule (`4931687`, `6f343d3`);
  - corrected the 3A replay (`2f8e06e`, `C3_p90_residual.md`).

  Those results are folded into the 3A section below and into FINAL.md.

**Evidence:** `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\c3\`
- `FINAL_before_after.jpg`: the main sheet. Narrator 3B (shipped | replay), house, seams.
- `FINAL_retro_before_after.jpg`: the CPU composite from the cycle 1-2 evidence.
- `b2_streak_arms.jpg`, `b2_measures.json`, `b2.json`: block 2.
- `b1.json`, `b1_flips.json`: block 1.
- `bench.log`, `replay_3b.log`: the clocks.
- `3b_house.json`, `3b_takes.json`, `3b_scarlet.json`, `3b_fixtures.json`: 3B.
- `replay\ep25_fulham_road\`, `replay\ep27_study_table\`: the narrator replay. `report.json`, the strips, `looks\...` (the look pictures drawn on the new tile), and `review.png` / `strips_all.png`, the sheets read by eye.
- CPU replays: `replay_3a.json`, `clock_replay.json`, `clock_smoke.json`, `cut_climbs.json`, `budget_replay.json`, `gframe_c10.json`, `qc_rows_timing.json`, `looks_identity_c9.json`.

**Scripts:** `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c3b\`
- the bench: `bench_c3.py`, `post_c3.py`, `pick_b1.py`, `make_wf_c3.py`, `make_wf_p1.py`
- 3B: `replay_3b.py` (it imports the C1 driver and writes only to c3b)
- 3A: `replay_3a.py`
- `clock_smoke.py`, `final_sheet.py`
- `stage_mine.py`: stages only this builder's hunks of files a peer had uncommitted edits in

## Commits

| # | sha | title (short) |
|---|---|---|
| 1 | a303cf2 | The plan climb checkpoints its best draft every rung (T1) |
| 2 | bf09d3a | QC fails fast: cheap rows first, Whisper only on a master that can still pass (T2) |
| 3 | 644a5aa | [arch] The honest clock: the process, not the step (D1) |
| 4 | 08f3e58 | Retry stamps an attempt; it never resets the ceiling (D2) |
| 5 | 97be974 | [arch] At the ceiling: take the best, flag it, continue; never park on the clock (D3) |
| 6 | 315ccde | Plan rungs priced; shares re-priced on the measure (D10) |
| 6b | a279597 | A panel ladder test reads its rungs, not the budget's audit row |
| 7 | 39ec248 | [arch] Stop at a boundary: `autopilot pause --at-boundary` (D4) |
| 8 | aa4085b | Look table (a): a negated clause names no layer |
| 9 | 27ca328 | Look table (b): the colour next to "hair" |
| 10 | 5385ee4 | G-FRAME floors, still advisory: MCU 0.15, close 0.25 (D9) |
| 11 | 323d735 | Skill lines and retirements; the H5 eye job |
| 5-7b | 81e202c | Suite follow-ups: tests that pinned the old rules, rewritten; the ceiling audit row moved to `studio/ceiling.py` |
| P1 | a74e6a5 | [arch] New refs draws use the neutral-tile 2x, arm (b) at denoise 0.15 |
| comfy_studio | 8d7c4f3 | New files only: `image_krea2_cinematic_2x_neutraltile_visurena`, `image_krea2_upscale2x_neutraltile_visurena` (branch `poc/2k-video-pipeline`) |
| P2 | — | **Not built**: block 1 measured a 0.9 % seed flip (rule: ≥ 5 %) |
| P3 | — | **Not built; H7 retired**: 1 bowler look picture on disk (rule: ≥ 2) |
| helper | 50a35c8, 4931687, 6f343d3, 2f8e06e | the `tick_error` fix, the downstream reserve, its companion rule, the corrected 3A replay (not mine; folded in) |

The series was paused before commit 1 and is **left paused**: WotW is complete and no new book is to start.

## Per issue: before → after, measured

| Issue | Before | After (measured) | Met? |
|---|---|---|---|
| **T1 plan checkpoint** | A killed climb restarted from the draft on disk: ep17 1 → 38, ep22 35 → 46, ep26 5 → 6 | `plan.climb.json` every rung. The resume edits the best draft with every refusal and runs only the rungs left. A critic verdict is reused only on unchanged code. | **met** (a)-(e) |
| **T2 QC fail-fast** | Whisper ran before every cheap row | A cheap fail makes 0 ear calls and writes `lines: null`, which is never read as heard. On ep27 every cheap row is ≤ 17.3 s, so none moved after the ear. | **met** |
| **Honest clock** | 398 unlogged machine-min | Run rows plus a 60 s beat; the ceiling is the union of the spans. Replay: 3,540 vs 3,499 min (+1.2 % in total; −5.8 to +3.7 % per episode). Block 4 smoke (CPU, real processes): a killed run counts to 1.45 s before the kill; a boundary stop exits `paused_at_boundary`; the resume consumes the flag and renders only the missing steps. | **met**; (c) holds in total, not per episode |
| **No reset** | 67 retries, each a fresh 5 h | `retry` writes `attempt_at`; `spent_before` ignores it. | **met** |
| **The ceiling rule** | A half-rendered round 0 was refused forever; a spent clock parked | Firsts render, rungs go terminal, nothing parks on the clock, and only the closed SAFETY list stops. BUILDER/JUDGED tags are read from the code. | **met** (deviation: ONE PER TAKE is JUDGED; G-LIGHT, PLAN GATES, MOTION hard and ACTOR are BUILDER) |
| **Prices, shares** | Plan rungs cost 0 s | 240 / 90 s and §3.3's table; 0 new terminals below 5 h. | **met** |
| **Boundary stop** | 22 of 23 kills were mid-step | Read between steps, rungs, grids and takes; PAUSED, never a stop. | **met** (a started step closes `deferred`; the events CHECK has no `paused`) |
| **Negated clause** | 117 of 281 dossiers read a negated "hair" | Scarlet: Watson, Hope, Lestrade and Gregson get their hair; the WotW tables are byte-identical; Jekyll and Hyde are still refused, **Utterson is now refused too** (headless). | **met** |
| **Adjacent colour** | Gregg bald, Lennox red, Wiggins grey | Gregg red, Lennox '', Wiggins fair; grey modifiers hold. WotW also: the artilleryman's `putney_feral` red → dark ("red cut across the chin"). | **met** (+1 recorded fix outside (d)) |
| **G-FRAME** | 7 of 13 owner-good MCU panels flagged | Owner-good 1/13, owner-bad 3/6; shipped ep12-27: MCU 14/86, close 2/23. | **met** |
| **H5 (eye job)** | 0/20 at sheet size | 0/12 at full 768 px. | **met**; H5 closed |

## The bench (41.4 GPU-min, `bench.log`)

| Block | What ran | Measured | Rule → result |
|---|---|---|---|
| 0 | `ep14 s22` (WotW) re-read at seed 11 through `run_text`, uncached | **Byte-identical to the cache** (50 s, cold) | pass → block 1 has its control |
| 1 J2 | 12 shipped WotW panels (4 refused at shipping on text or count, 6+ with 2+ people, 3 night, 6 with signage) × seeds 111, 211, 311 against the cached 11 | **2 flips in 216 field-reads (0.9 %), on 1 panel** (ep14 s14, a 12-figure crowd's count). 0 unreadable. Subject-list Jaccard median 0.86. Crowd reads cost up to 2 min (1,024-token decode). | flips < 5 % → **P2 not built.** The 6-16 % instability C3_R measured is the **pixel** term, not the seed. **The beam-2 arm did not run:** the installed AILab QwenVL node (the `-Mod` package) rejected the graph (it requires `camera_tag` and `passthrough`, and its model list has no `Qwen3-VL-8B-Instruct`), and by then the 30-min rule had passed. The beam workflow file was removed, never committed. |
| 2 streak | 4 looks' 1x × arms a-d through `image_krea2_upscale2x_neutraltile_visurena` (16 tiles, 50 s each) | **0 ghost faces in any arm** (backdrop and trousers of arm b read at full 3072 px). Streak share vs today's subject-prompt tile: **a 1.23-4.71×, b 0.59-1.49×, c 1.14-3.10×, d 1.09-1.26×**. Trousers: b 0.98-1.00. Head facenet vs 1x: **b best on all four** (.924-.967 vs a .884-.950). | **No arm met the 1.2× clause on the narrator**, so the verdict's fallback was (a). **Shipped (b) instead**, decided on the owner's behalf: it beats (a) on every measured column with 0 ghosts. Recorded for veto in the decision file. |
| 3 H7 | CPU precondition | 1 bowler look picture on disk (`char-john_watson_outdoor.png`); Stamford's bowler look has no picture; the bowler prop is a prop | < 2 → **H7 retired** |
| 4 clock | CPU, real processes (`clock_smoke.py`) | See above | **pass**; no clock commit reverted |

## 3A: the clock replay of ep19-27 (CPU)

**My replay (`replay_3a.py`, rung-only accounting):** honest P50/P90 5.88/7.55 h → code fixes 5.30/6.74 → plus the 5 h terminals **5.10/6.45 h, 2/9 over 6 h** (ep20 372, ep21 448).
- 11 rungs over 5 episodes become terminals: 6 EYE_TAKES cure rounds and 5 MASTER retakes.
- ep20 and ep21 run more than 60 min past the crossing.
- ep21 crosses 20 min into round 0 of its 32 takes, the "pre-round-0 crossing" the verdict asked to name.

**Corrected by the helper (`C3_p90_residual.md` §7, CPU, k-scaled ±10 min):**

| scenario | P50 | P90 | over 6 h |
|---|---|---|---|
| my 3A | 5.10 h | 6.45 h | 2/9 |
| + D3's QC rule (built in 97be974; my replay missed it: a non-SAFETY QC fail at a spent clock ships flagged) | 5.10 h | 6.05 h | 1/9 |
| + the downstream reserve (4931687: rungs leave the firsts still owed their time under 6 h) | 5.10 h | 5.90 h | 1/9 |
| + the companion rule (6f343d3: past the ceiling a verdict on the same bytes stands under moved code) | 5.10 h | 5.64 h | 1/9 (ep21 371) |
| + ep21's upload-door split voice cured at step 04 (434213e, already on master) | 5.10 h | **5.54 h** | **0/9** |

**The honest line:**
- P90 is 5.5-5.6 h and every episode is under 6 h, **only with the door fix counted**. Strictly, ep21 is 371 min.
- The reserve's price is panel rescue on light episodes: a false positive on ep17 (2 panel rungs).

## 3B: the final picture replay (≈ 68 GPU-min)

| Set | Expected | Measured | Verdict |
|---|---|---|---|
| **WotW narrator**: ep25 `fulham_road` and ep27 `study_table`. Looks drawn **new on P1's tile**, grids at the shipped seeds, regrid bar on face-visible panels. | changed (P1); keep the beard, 0 ghosts, regrid PASS | **ep25:** ragged_greyed LOOK-STATE **passed** (dirt advisory only); grey beard and felt hat by eye; regrid **1/1** face-visible (shipped 0/1). **ep27:** epilogue_home passed; ash-grey hair and moustache; regrid **3/3** (shipped 0/3). 0 ghosts on both look pictures by eye; the tweed carries the measured light streaking. | **met** |
| **WotW house + seams**: ep26 villa, ep27 study reverse, ep11 study and dining; ep20 scullery_copper, ep27 study_essay (8 grids) | identical | **8/8 bit-identical to the C1 replay, words identical; 0 seams, 0 stacked on 15 panels** | **met** |
| **WotW phase-0 takes**: S2/S3/S4/S6 on CK8, D1/D2 on BASE (seed+1) | identical to the C1/C2 renders | **Not bit-identical: PSNR 41.9-44.4 dB, mean \|Δ\| ≈ 1/255.** The same draw by eye (`eye/takes_3b_vs_c1.png`). The seed-to-seed distance is 13-22 dB, so this is far closer. The engine was relaunched at 11:33 with the same flags (`--reserve-vram 2`); C1's in-session re-render was PSNR 99. | **same draw; bit-exactness across an engine restart is NOT held** (new finding, cause not isolated) |
| **Scarlet**: the C1 ep14 T04/T05 cells on the ep05 room, then the takes | identical | Cells **bit-identical** (2/2); takes 45.4 / 44.0 dB (the same restart effect). The look-table head fallback, re-judged: see commits 8-9 (Scarlet: 26 rows, 0 refused; 4 heads now authored from the row). | **met** for the pictures; the gates as above |
| **Gate regression**: the owner-judged fixtures, every shipped panel read once at seed 11 and judged by today's `panel_content` | good stays passing; no bad refusal vanishes | **ep05 (good): 23/28 refused. ep07 (good): 5/27. ep08 (bad): 0/20. ep09 (bad): 0/23.** These episodes predate the content gate (no shipped `panel_content.json`), so no refusal could "vanish". But today's gate **refuses the owner's good episodes and passes his bad ones.** ep05's refusals are rule and format faults: "hills" on a place the setup calls flat (12), figures against a plan that declared no extras or fewer people (12), "day" light on a night shot (4). | **NOT met. A measured inversion.** The content gate measures plan format and rule calibration, not what the owner judged. J5 (rule calibration on the owner fixtures) is now the top open item. |

**GPU minutes:** B0 1.4, B1 26.1, B2 13.9 (bench 41.4); 3B house 8, takes 9, narrator 16 (+8 for a first ep27 run before the shot list was fixed), Scarlet 6, fixtures 21 (≈ 68). **≈ 110 min in total.**

## tick_error (read-only; fixed by the helper)

- **Cause:** 1,927 events from 2026-10-10 23:24Z, all `ValueError: int('compilation')`. `book_compilation.py` appends the book video's upload rows with `"episode": "compilation"`, and `studio/autopilot.next_unit` called `int()` on every public row. Reproduced read-only.
- **Impact:** no episode was lost (the series had completed 12 minutes earlier). But status and heartbeat froze, and pause, park and retry read a stale status. It would recur at the end of every book.
- **Fixed** in `50a35c8` (helper, test-first); `next_unit` now answers None on WotW.

## D1-D12 as applied

| # | Applied |
|---|---|
| D1 clock = process | commit 3 |
| D2 no reset | commit 4 |
| D3 the ceiling rule; only SAFETY stops | commit 5 (`gate_policy.SAFETY`), with the helper's reserve and companion on top |
| D4 resume from a boundary | commit 7 |
| D5 ceiling 5 h | unchanged (the reserve uses the owner's 6 h as its limit) |
| D6 confirm-before-refuse only on the measure | block 1: 0.9 % → not built |
| D7 neutral tile for refs, not the plate | P1; `book_title` untouched |
| D8 benched before the switch | done; **arm (b)**, not the fallback (a); recorded for veto |
| D9 G-FRAME 0.15 / 0.25 advisory | commit 10 |
| D10 priced rungs, shares | commit 6 |
| D11 retirements | commit 11 + H7 |
| D12 content rules unchanged | unchanged. 3B's fixture inversion is the evidence for revisiting them (J5) |

## The suite
- After all commits, with ffmpeg on PATH: **4 failed / 10,640 passed** (`scratchpad\c3b\suite_final.txt`).
- The 4 are the pre-existing reds: `test_llm` ×2, `test_canon`, `test_episode_tail`. No redder.
- `tests/test_comfy_text.py` hangs while the engine is down, so it was run apart.

## Architecture
- Changed in the same commits:
  - `architecture/index.html`: Platform run clock; Autopilot; episode/02, /09, /11; refs/02.
  - `architecture/README.md`.
  - `architecture/decisions/2026-10-11_cycle3_honest_clock.md`.
  - The `docs/DECISIONS.md` line naming C3_verdict §4.
- Peer edits in the same files were not staged.
- **The claude.ai copy was NOT republished** (instructed). It is owed.

## Open after cycle 3
1. **J5: the content gate is inverted on the owner fixtures** (good ep05 23/28 refused, bad ep08/09 0). Calibrate the landform/flat, declared-extras and hour rules against these four episodes before trusting a content refusal.
2. **Determinism across an engine restart:** the takes come back 42-45 dB, not bit-exact. Grids are still bit-exact. Find out which node is nondeterministic after a relaunch (attention backend, kernel autotune) before any bench claims bit-identity across sessions.
3. **The beam-2 reader arm:** a new workflow built for the installed `-Mod` node's inputs, if reader stability is ever pursued. It is not needed: the seed term is 0.9 %.
4. **P90:** 5.54 h with every episode under 6 h, only with the door fix; ep21 is 371 min strictly. What remains is production code faults before the crossing. The lever is fixing on the replay set before a series runs.
5. Carried: room tone, the Scarlet dq lag blindness, stubble wording, the Jekyll/Hyde/Utterson heads, framing (MCU drawn a size wide), the shipped faults never overwritten (ep10/T21, ep26/T25, Hope, Brigham).
