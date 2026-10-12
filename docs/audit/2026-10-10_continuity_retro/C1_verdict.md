# C1 verdict: the cycle-1 skeptic on C1_L, C1_A and C1_G

2026-10-11. Read-only, CPU only. Nothing was rendered and no code was edited. This file is the only thing written.

**Bar (CYCLES.md):** a fix is built only when its issue is measured on the artefact, seen in ≥ 2 independent cases, and survives this review. Anything weaker is logged as a hypothesis.

**Inputs:**
- Reports: `C1_L_looks_replayset.md`, `C1_A_audio_tail.md`, `C1_G_gates_speed.md`
- Background: `R2_verdict.md`, `BENCH_r2.md`, `CYCLES.md`, `.claude/skills/episode/LESSONS.md`
- Evidence: `C1_A_evidence\`, and the scratch folder `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c1\` (including `dl\`)

## 0. What I re-checked myself

| Claim | My check | Result |
|---|---|---|
| **G §1: the authors' 4-step ref2v grid is `simple`@12, and R2_verdict cut the one arm on the contract** | Read the downloaded sources. `dl\mt_readme.md.txt` shows the "Ref2VA Turbo 4-step v0.1" row with shift 12/3, NFE 4, at **544p**, and gives "video sigma [1, 0.9730, 0.9231, 0.8000]". `dl\mt_ref2v_wf.json`, parsed: `BasicScheduler ['simple', 4, 1]`, `MiniMaxH3SigmaShift [12, 3]`, `KSamplerSelect ['euler']`, the ref2v 4-step LoRA at 1.0. `dl\lx_h3_scheduler.py.txt` has `linspace(1,0,steps+1)` then `shift·t/(1+(shift−1)t)`. I then recomputed ComfyUI's `beta` (α = β = 0.6 ppf over the 1000-entry table) and `simple` myself. | **CONFIRMED to 4 decimals.** 4 × beta@12 = 1, .9825, .9234, .7207, which is base-t 1000/**824**/501/**177**. 4 × simple@12 = 1, .9730, .9231, .8000, which is 1000/750/500/250 and exactly the published grid. R2_verdict §0.2/§1 reasoned that "a lower last σ is sharper" and cut `simple@12`. **That cut the only on-contract arm. R2_verdict was wrong on this point.** Whether the trained grid keeps the S3 frogs is unmeasured, so it goes to the bench. |
| G §3.2: strips seam and square-ish grids don't | Recounted `seam_by_shape.json`: 2x1 8/60, 3x1 7/141, 1x1 0/92, 2x2 0/100, 3x2 0/6. Fisher test on 15/201 vs 0/198 gives p = 4.7e-5. Opened `ep19_grid_pit_work_2x1_b.png` by eye. | **CONFIRMED.** The 2048×1024 "2x1" is drawn as a **2x2 of four near-identical pit scenes**: Qwen chose its own grid count. |
| G §3.2: keep_best keeps the *last* draw | Read `studio/panel_ladder.py`. `draw()` → `supersede()` moves every earlier draw away, and `Climb.keep_best` only annotates `climbed`. | **CONFIRMED.** No earlier draw is ever restored. |
| G §4: the red test is stale | `uv run pytest tests/test_an_empty_panel_is_not_framed_on_a_person.py`: 1 failed, 16 passed. `Size` in `studio/episode_spec.py:138` includes `extreme_close`. | **CONFIRMED.** |
| L §1a: beard wording | Opened `wotw_beards.png`. | **CONFIRMED.** Captain and Ogilvy ("Full … beard") show beards. Lord Garrick (a qualified chin beard), the brother (stubble) and the gardener (stubble) are clean-shaven. The artilleryman shows only his moustache. |
| L §1b: ghost faces | Opened `ghost_thighs.png`. | **CONFIRMED on 1 picture.** There are two painted faces on the trousers; the right one is grey-bearded. **That is n = 1**, which is below the ≥ 2 bar (see §3). |
| A §2: a mouth articulating in the shipped silent tail | Opened `strip_1.jpg` and `strip_2.jpg`. | **ep10/T21: confirmed.** "Moving!" is shaped at 4.35-4.53 s. **ep26/T25: ambiguous.** The mouth opens wide at 4.8-5.3 s, but the prompt has her swaying or fainting, so it could be a gasp. I count **1 clear shipped case plus 1 possible**. The bench adds 2 echo words, on S4 CK and S4 shift6. The *issue* clears 95 % (≥ 2 measured cases of H3 continuing speech into a silent tail). The *shipped prevalence* is 0.6-1.3 %. |
| A §3b: digital-zero padding | `takes_r2v.py:426` builds the pad with `anullsrc`. | **CONFIRMED.** The contrast arm has never been run, so it is still a bench item. |

**Two corrections the proposers missed:**
1. **G §2.3 says "CK re-judged: PASS", but its own rule 5 fails CK on S4.** CK heard "Indeed." where the control tail heard no word. The correct reading is that CK passes rules 1-4. Its S4 word is unresolved. **This does not block CK on narration takes.** A narration take has no guide voice, so its tail cannot echo a line. So CK can be adopted for narration on rules 1-4. For dialogue it needs the seed pair in §2.
2. **G §3.3 cure 3 ("a sibling redraw may never replace a machine-clean grid") collides with the 2026-09-28 one-room ruling.** A redrawn anchor re-cuts the room, and the siblings are redrawn *so that they stage the new room*. Restoring an older sibling draw would stage the old room beside the new anchor. **Not built.** It is carried to cycle 2 in a narrow form (§3).

---

## 1. BUILD list, in commit order (CPU, test-first, $0, no GPU in any test)

Each commit carries its own LESSONS/GATES lines (§5). Commits marked **[arch]** also update `architecture/index.html` and `architecture/README.md` in the same commit.

| # | Commit | Conf. | Acceptance test (written first, must fail first) |
|---|---|---|---|
| 1 | **Fix the stale red test.** `test_an_unknown_size_is_refused` uses a size that is not in `get_args(Size)` (e.g. `"establishing"`), and the sizes list is read from `get_args(Size)` instead of a hand list. | 100 % | The file goes from 1 failed to 17 passed. A new assertion checks that every member of `Size` has a `cut_clause` for both `peopled` values. |
| 2 | **Recalibrate the bench rulers** (`scripts/bench/rulers.py`). This replaces the 28 dB PSNR wall and the flat −0.02 identity rule. The new rules: (a) a same-draw guard of PSNR(arm, ctl) − PSNR(ctl seed 2, ctl) ≥ 3 dB, used only to decide "numerics vs new draw"; (b) per shot, Δid ≥ −2·σ_seed (σ_seed recomputed from whatever seed-2 controls exist), and the mean over dialogue shots is ≥ −0.02; (c) banding as today; (d) clones ≤ the production take's count on the same shot; (e) invented speech compared to the control's own state on that seed, with prompt-asked mouth actions exempt. | 99 % that the wall is wrong. The new rule is a bench rule, not production. | A replay of `measures_r2.json` + `psnr_pairs.json`: CK passes (a)-(d) and **fails (e) on S4**; shift6-beta fails (e) on "Heed."; A1 is **not** refused by any PSNR rule; D1 A0 with 1 clone is not a fault against itself. |
| 3 | **[arch] No strips: `grid_layout.GOOD = (1, 4)`.** `pieces(n)` returns `[4]*(n//4) + [1]*(n%4)`. This **simplifies** C1_G's proposal (a 2x2 with an empty fourth cell): 3 shots become three 1x1s, at the same 3 MP the 3x1 strip drew, and no new "empty cell" concept is needed. Faces still go to 1x1 as today. | Cause 99 %. The cure's evidence is observational (0/198 on square-ish shapes), and the GPU replay in bench block 2 is its acceptance. | Unit tests: no row from `rows_for` / `pieces` ever has cols·rows ∈ {2, 3}, for n = 1..12. `pieces(6) == [4, 1, 1]`. `pieces(5) == [4, 1]`. Every existing test of anchor and sibling chaining still passes. A CPU replay of ep19-27 `plan.json` reports how many more grid calls each episode makes (expected +2-5; record it, because it feeds the 6 h clock). |
| 4 | **Isolate rung for `seam` / `stacked`** (`panel_ladder`). Reuse `Climb.isolate` for these two kinds, outside the 2-grid cap. Drop `seam` and `stacked` from the reprose `CURES`, because reprose moved nothing on ep22. | 90 % that it helps (0/92 seams in 1x1). Finite by construction, so it cannot loop. | A fake-ctx test: a stacked fault in a 2x2 calls isolate exactly once. On the second verdict `isolate` returns False and the terminal is `keep_best` flagged. `self.redrawn` (the cap) is unchanged. No reprose is written for a stacked-only verdict. |
| 5 | **Beard words come from the closed marker** (`scripts/refs/looks.py` `layers_first` / `fresh_prompt`). When `markers.facial_hair == beard`, the drawn layer carries `a full short <colour> beard covering the jaw, chin and upper lip`, and the duration words are kept only as an adjective. `stubble` is **not** touched (owner ruling, §4). | Issue 95 % (3/3 draws + 6 base sheets). The fix is unproven on the artefact, so the bench decides keep or revert. | Test: the rebuilt ep25 `ragged_greyed` prompt contains the canonical phrase. Base prompts with no beard marker are byte-identical to today. A look with `facial_hair=stubble` is byte-identical to today. |
| 6 | **Beard in the grid tags is a deterministic cure, not a wall.** Before G-LOOK-WORDS runs, a one-face shot tag for a person whose look marker is `beard` and whose tag lacks a beard word gets the look's beard phrase appended. G-LOOK-WORDS then checks it as hard. A wall alone would send the writer around the loop (memory: walls follow the chapter, run deterministic cures first). | 100 % (4/12 ep25 tags, by grep) | A replay of ep25 `plan.json`: exactly the 4 bare tags gain the phrase and the other 8 are byte-identical. A tag that already says "beard" or "bearded" is untouched. |
| 7 | **[arch] The production TAIL gate on dialogue takes** (`studio/invented_speech.py` + `studio/measure/mouth.py`, wired into the take gate). **Fail** when the shipped tail is louder than −45 dB **and** Whisper hears words after the line's last shared word. The mouth branch (open for ≥ 6 frames with ≥ 2 rises) is included **only if** the replay shows 0 false fails on the 17 static-mouth takes and the 7 loud closed-mouth tails; otherwise it is recorded advisory. A tail whose post-line clause asks for a mouth action (laugh, call, shout, pant, eat, drink) is exempt. A guide whose hash does not match `placed.json` reads **unmeasurable**, never "invented". **Cure:** one reseed of that take (cap 1), then `keep_best` flagged into `audit/`. The gate never shortens the shot (the voice is the ruler). | Issue 95 %. Gate cost: Whisper runs only on loud tails (~12 % of dialogue takes). | A replay over `C1_A_evidence\shipped_fixed.rows.json`: fails ep10/T21. ep26/T25 fails only through the mouth branch, if that branch is armed. The exemptions are ep25/T21, ep04/T02, ep22/T12 and scarlet ep11/T17. The 5 stale Scarlet guides read unmeasurable. **Every other row passes.** A ladder test shows the reseed runs at most once and the terminal never re-enters. |
| 8 | **The bench overlay gains a room-tone guide arm** (`scripts/bench/` only; production `composite()` is untouched). The pad after the line is a −50 dBFS bed (brown noise, seeded) instead of `anullsrc`. | Needed for bench block 4. | Test: the RMS of the padded segment is −50 ± 1 dBFS. The line samples are byte-identical. The total length is unchanged. `knobs()` reports `guide_tail=roomtone`, and an arm without it reports `zero`. This guards against a fix that changes nothing. |
| 9 | **The look table refuses a bound character whose head layers are all empty.** This applies only to newly written tables; existing `looks.json` files are not re-judged. | 100 % on Jekyll and Hyde (2 characters) | Test: a Jekyll/Hyde-shaped dossier is refused with a "head unauthored" reason. A CPU replay over every WotW and Scarlet cast row with a look table passes, with **0 refusals**. If any refuses, this commit does not land, because it would park the series. |
| 10 | **A legacy-path Scarlet replay** in `look_replay` (old pipeline: `char-*_indoor` sheets, `boards/plates`, no `looks.json`). It stages exactly the content-addressed names in each `T*.graph.json`, and reads lip lag with `measure/mouth.lag`, not the frozen dq `lag`. | Tooling for bench block 5 | A dry run builds the graphs for ep14 T04/T05 with staged names byte-equal to the shipped `graph.json`, and refuses the unhashed ep01-03 names. `mouth.lag` on the shipped T04/T05 gives a number that is not 0.000, recorded as the baseline. |

**Not built (and why):**
- **The `beat_sentences` speech-verb hygiene (A fix 2).** It was measured 0/25 harmful, so it would be a fix that changes nothing measurable. It is logged.
- **Best-of-draws restore (G cure 3).** It conflicts with the one-room ruling (§0).
- **The ghost-face VLM check.** n = 1 (§3).
- **The APPEARANCE regex words.** "black" matches every black coat, so precision is unmeasured (§3).
- **`StoryTime.order`.** The book is unstarted.
- **`ManualSigmas` in `h3_arms`.** G2 is deferred (§2).

---

## 2. ONE GPU bench, ≤ 90 min (cycle 1)

**Preconditions:**
- Commits 1-10 have landed, and `knobs()` reads back every arm's scheduler, sampler, attention node and guide tail.
- The engine is up and the queue is empty. **Never relaunch it.** If it is down, stop and tell the owner.
- Every render's size is read back with ffprobe.

**Timings used** (from BENCH_r2): 4-step ≈ 100 s per take, 8-step A1 ≈ 150 s, Krea2 look draw ≈ 45 s, Qwen grid ≈ 60-90 s.

| Block | What | Renders | min | Pass / stop rule |
|---|---|---|---|---|
| 0 | Engine and queue check, determinism re-render of S4 A3 (expected PSNR 99) | 1 | 3 | Not bit-identical → **stop the bench**. |
| 1 | **Looks.** (a) ep25 `ragged_greyed`, fresh route with the commit-5 prompt, seeds 4165438081 / +1 / +2. (b) Ghost A/B: the old prompt at seed 4165438081 through the new `image_krea2_cinematic_2x_presave.json` (the 1x decode is saved; the existing file is not edited). (c) Only if (a) draws a beard on < 2/3: `image_krea2_identity_edit` of `sheet_front.png` with the canonical sentence, 3 seeds. (d) The **ep25 `fulham_road` regrid** with the winning look, through `look_replay`. | 3 + 1 + (3) + 1-2 grids | 12 (+3) | Look pass: LOOK-STATE reads `beard` and the eye agrees on ≥ 2/3. Regrid pass: hair colour **and** beard on ≥ 80 % of the panels the narrator is in (the acceptance bar). Ghost: faces on the 1x picture → cause (a), the LoRA; none → cause (b), USDU. Log it, build nothing. Both routes fail → **stop the block** and raise owner ruling 4.3. |
| 2 | **Seams under commit 3.** Replay 6 of the 9 seam setups at their shipped seeds, through the new layout: ep19 `pit_work`, ep20 `scullery_copper`, ep21 `pantry_door`, ep22 `pantry_empty`, ep25 (shot 20/22 setup), ep27 `study_table` (shots 10/16). Add the house set: ep26 villa, ep27 study reverse, ep11 study, dining room, 1 grid each. | ≈ 14 grids of 1x1 / 2x2 | 15 | **Pass:** 0 seams (the 3ea5461 check) and 0 `stacked`. G-SETUP passes on every setup. The house reads as one room against the anchor by the eye. Any seam in a 1x1 → stop the block and log the panels. Commit 3 is then reverted to a hypothesis. |
| 3 | **Speed.** (a) **G1 = the 4-step on the authors' grid** (`..._simple12_modeltc`; one difference from A3: `scheduler` beta → simple, read back), on S2, S3, S6 and S3 seed 2 (narration), plus S4 seed 1 to read the tail on the trained audio grid. (b) **CK on today's 8-step BASE** (`..._crf_visurena_ckattn_comfyorg`), on S2, S3, S4, S6, D1, D2, seed 1, plus S4 seed 2. (c) **The A0 seed-2 controls** for σ_seed on the 8-step: S4, S6, D2. | 5 + 7 + 3 | 9 + 14 + 8 = 31 | **G1:** the S3 frogs at 50 % on **both** seeds, otherwise G1 is out (if seed 1 loses them, skip seed 2). Clones ≤ the production count. Banding as rule (c). G1 is a **narration-only** candidate either way (§5 rule). **CK:** rules 2a-2d against A0, using σ_seed from (c). If it passes, adopt it for **narration** now. Dialogue only if both S4 seeds read the same word state as A0. |
| 4 | **Room-tone tail A/B** (commit 8). S4 on A3 (4-step, the arm that sounds at seed 1) × seeds 1, 3, 4 × {zero, roomtone}. D2 on A0 × roomtone, as the lip-lag control. | 6 + 1 | 13 | **Pass:** roomtone tails show 0/3 words and mouth runs ≤ 3 frames, against ≥ 1/3 inventing with zero. D2 lag is unchanged (`mouth.lag` within ±1 frame) and D2 stays silent. If zero invents on 0/3 as well, the A/B is **inconclusive**: log it, adopt nothing. |
| 5 | **Scarlet** (commit 10). The ep14 `sitting_room_evening` grid replayed with the room pinned on the ep05 `hearth_night` anchor. Takes T04 (Holmes MC dialogue) and T05 (Watson MC dialogue) on the production 8-step. | 1 grid + 2 | 8 | Room: the eye reads ep05's fireplace, windows and carpet. Faces: facenet ≥ the shipped median (Holmes .489 for ep14). Lip: `mouth.lag` is not worse than the shipped baseline. **Skip the whole block if the clock is past 80 min.** |
| — | Slack, loads, ffprobe | | 8 | |
| | **Total** | | **≈ 90** | **Hard stop at 90 min.** Every block is independent, and a block that is stopped is logged, not retried. |

**The replay set this fixes for cycles 1-3** (amending CYCLES.md):
- **WotW:**
  - phase-0 S2/S3/S4/S6/D1/D2;
  - ep25 `fulham_road` (with the beard fix) and ep27 `study_table`;
  - the house: ep26 villa, ep27 study reverse, ep11 study, dining room;
  - the 6 seam setups above.
- **Scarlet** (C1_L, accepted as written):
  - ep14 `sitting_room_evening` T03/T04/T05/T17/T22;
  - ep05 `hearth_night` T09/T11/T12 as the held control;
  - ep03 `garden_path` T07/T08/T10 against ep14 `garden_path_morning` T09;
  - ep07 T23 against ep13 T19 (Hope).
  - Cycle 1 runs only the ep14 grid plus T04/T05 on the GPU. The rest is scored on CPU against the shipped files as the baseline.
- **Jekyll/Hyde:** waits for owner ruling 4.2.

**What the bench does NOT run** (cycle 2, if it is still worth it):
- G2, the 8-step on a 6-of-8 subset. Run it only if G1 fails the frogs; it needs `ManualSigmas` in `h3_arms` first.
- 992 canvas.
- The trimmed-guide arm. It risks the early-clock fault `composite()` documents.
- The "silently" prompt arm. H3 ignores absences.

**The 6 h budget:**
- Today's 8-step production projects to ≈ 6.0 h (BENCH_r2 §5), right at the ceiling.
- Added costs: commit 3 (+2-5 grid calls), commit 7 (Whisper on ~12 % of dialogue takes, plus a reseed on ~1 %) and commit 4 (one 1x1 per seam).
- Offset: CK on narration (≈ −9 to −15 min per episode, an estimate).
- **If CK fails block 3, commits 3, 4 and 7 must be priced on the replay clock before the series resumes.** If the projection crosses 6 h, that is an owner budget ruling.

---

## 3. Hypotheses carried to cycle 2 (logged, not built)

1. **The subject noun first in `fresh_prompt`** ("A man of 34 with …"): 55 %. It runs as an extra arm only if block 1a fails.
2. **Ghost faces.** It is n = 1 picture, so the VLM face-list check is not built. Cycle 2 should first scan **every** WotW look picture and sheet body crop (CPU/VLM) for a second case. Block 1b gives the cause: LoRA or USDU tile prompt.
3. **Room tone cures invented speech:** 60 % until block 4 runs.
4. **The 4-step trained at 544p behaves differently at 768²**: unmeasured. G1's frogs result is the first data point.
5. **CK costs ≈ 0.01 facenet identity** (4/4 negative, p = .06). Watch it on the block 3 seed-2 controls.
6. **A narrow best-of-draws:** restore an earlier draw only for a grid that has **no** anchor kin. This waits for a measured case after the strips are gone.
7. **Jefferson Hope is two men** (sheet 8826eb07, 0.41-0.44). A cross-episode sheet-lineage check (a cast row's staged sheets ≥ MATCH with each other) has n = 1 sheet, so it is not built.
8. **APPEARANCE regex additions** (pale, sick, swell, stature, shrunk, dwarf). The precision must be measured on WotW + Jekyll before adding anything. "black" is rejected outright.
9. **`StoryTime.order`** for flashback and confession chapters. It is needed by Jekyll ch10 and Scarlet Part 2. Design it when Jekyll is ruled.
10. **The Scarlet dq `lag` never moves** (all 80 dialogue rows read ±0.01). Cycle 1 swaps in `mouth.lag` for the replay. Whether production dq `lag` is equally blind on WotW is a cycle 2 check.
11. **`beat_sentences` writes speech verbs after `line_end`** (36/204 takes). It is harmless as measured (0/25). Log it only.
12. **WotW sounding tails are 14 of 15, Scarlet's 2.** Style or soundscape is unexplained.

---

## 4. Owner rulings needed (only those CYCLES.md reserves for him)

1. **A look change: stubble.** Krea2 + Cinematic draws no stubble (0/3 sheets). For a look whose book text says stubble or "N days of", may the drawn word be "a short beard", which is visible but heavier than the text? The alternative is to record stubble as undrawable and stop LOOK-STATE from demanding it. Until he rules, commit 5 touches `beard` markers only.
2. **The Jekyll/Hyde probe:** the book's look, and new Jekyll and Hyde base sheets with distinct silhouettes. The current three men are near-identical. The probe (~30 min GPU) waits for this ruling.
3. **A composite-adjacent beard fallback.** If both the fresh and edit routes fail in block 1, may a masked inpaint of the beard region of the *same* look picture be used? It is one hop and not a paste, but it is masked, so it is his call.
4. **Shipped faults:** wotw ep10/T21 ("Moving!" in the tail), and possibly ep26/T25. Retakes are not done in this retro (shipped files are never overwritten). Whether to retake them after the retro is his ruling.
5. **For information only (no ruling needed unless he objects):** the no-strips layout (commit 3). The room stays held by the anchor chain, as the 2026-09-28 ruling already says.

---

## 5. Skill text changes (each lands with its commit)

**LESSONS.md:**
- **A distilled LoRA is run on its published grid.** The ref2v 4-step is `simple`@12/3, which is σ .973/.923/.800 and t 750/500/250. `beta` puts two of its four calls off the trained timesteps (824, 177), and the audio follows the video grid. Read the authors' graph before ruling a schedule "softer". R2 cut the only on-contract arm on a sharpness intuition.
- **A pixel wall in a chaotic sampler measures the draw, not the quality.** 28 dB would refuse today's shipped 8-step on all 6 shots. Judge numerics with a same-draw margin over the seed-to-seed distance, and identity against the control's own seed spread.
- **Qwen draws its own grid count on a strip.** A 2:1 canvas came back as a 2x2 of four copies, and a 3:1 as four columns. That is 15/201 strip panels seamed against 0/198 square-ish. A seed bump never cured it (ep22 .99/.98/.98, ep14 nine redraws). Grids are 1x1 or 2x2 only.
- **keep_best keeps the last draw, not the best.** Earlier draws, clean ones included, sit in `superseded/`.
- **Krea2 + Cinematic draws a beard only from a plain "full … beard" noun** (2/2). It drops duration, stubble and qualified wording (0/7). The closed marker writes the drawn phrase, and the grid tags carry it too (ep25: 4/12 tags lacked it).
- **H3 continues the line into a digitally silent guide tail.** Every invented word echoes the last word ("Indeed.", "Heed.", "Moving!"). Audio and mouth are one sample: a loud tail means a moving or open mouth, and a quiet tail means a shut mouth. 1-2 of 154 shipped dialogue takes speak into silence.
- **A guide overwritten in `ComfyUI/input` makes the speech check lie.** Hash the guide against `placed.json` first.

**GATES.md:**
- **G-GRID-SHAPE:** a grid holds 1 or 4 cells, never 2 or 3.
- **Seam/stacked rung:** isolate once, outside the cap, then keep_best flagged.
- **G-TAIL (dialogue):**
  - Fails on Whisper words after the line in a tail louder than −45 dB, plus the mouth branch if it is armed.
  - Exempt prompt-asked mouth actions.
  - A stale guide is unmeasurable.
  - Cure: one reseed, then flagged.
- **G-LOOK-WORDS:** the beard is cured into one-face tags before the wall.
- **BENCH arm rule:** a speed arm passes the INVENTED-SPEECH check on S4, D1 and D2 × 2 seeds, or it is adopted for **narration takes only**. Dialogue stays on the 8-step at 12/3 until an arm passes.

**SKILL.md:**
- In the take step: name the TAIL gate.
- In the grid step: "1 or 4 cells".
- In refs/looks: "the closed marker writes the drawn facial-hair phrase".

---

**Publishable (flag):**
- **The off-grid `beta` finding for distilled ref2va LoRAs.** It is checked against the authors' own graph.
- **The calibrated non-inferiority rule for numerical speed arms.**
- **Qwen-Image's own-grid-count behaviour on strip canvases**, with p = 4.7e-5.
- **"Echo of the last word" invented speech in silent guide tails.**

All four belong in the planned public ref2va / storyboard bench.
