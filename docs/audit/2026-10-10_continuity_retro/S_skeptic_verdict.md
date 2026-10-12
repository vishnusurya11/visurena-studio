# S (SKEPTIC / budget hawk): verdict on P1 (continuity) and P2 (quality + speed)

Debater S, 2026-10-10. Read-only: nothing changed, rendered or spent. Inputs: A, B, E (investigations),
C, D, F, G (research), P1, P2, `CLAUDE.md`, `.claude/skills/episode/LESSONS.md`, `docs/DECISIONS.md`,
the prior audits `2026-09-29_ep14_time_debate.md`, `2026-09-30_rounds_debate.md`,
`2026-09-28_grid_place_constancy_plan.md`, `2026-10-01_ep16_cloned_cast.md`, `studio/plan_verdict.py`,
`scripts/episode/grids.py`, and every `episodes/ep*/timing.jsonl` (summed by
`D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\timing_sum.py`).

Owner rulings of 2026-10-10 are taken as settled and not reargued.

---

## 0. Five facts both plans under-weight

1. **WotW is finished.** LESSONS records ep27 public on 2026-10-10 and the autopilot at COMPLETE,
   27/27. No shipped episode is re-rendered. Neither owner complaint (the narrator's look, the house)
   can be fixed on screen in WotW. They can only be **prevented in the next book**, and the only
   evidence available before that book is a bench replay on WotW inputs.
2. **No other book has a look timeline.** `profile.wardrobe_by_chapter` exists in WotW's 49 dossiers
   and in **0** dossiers of the other 29 books. No code in `studio/`, `agents/` or `scripts/` writes
   it. `pack_refs.py:136` is its only reader. P1's `looks_from_dossier` (commit 2) therefore returns a
   single base look for every character of the next book, and the continuity build does nothing
   there. What does exist in every book is the script supervisor's `state_changes` (chapter, scene,
   day, evidence quote). A look-timeline producer built on that is **missing from P1** and is required
   for the slice to fix anything.
3. **The budget is not set by renders.** ep19-27 per-episode clock (the sum of `timing.jsonl`):
   3.14, 3.81, 4.50, 5.57, **5.68 (median)**, 5.94, 6.79, 7.05, 9.22 h. The mean is 5.74 h. Three of
   the nine are over 6 h. Per stage: plan 37-206 min (median 64), takes 36-107 min (median 81), checks
   29-75 min, grids 15-87 min. The tail comes from the plan stage and the stops, as ep21 (22 stops),
   ep26 (two plan deferrals, 142 min of plan) and the ep14 / 09-30 debates showed. P1 adds four HARD
   gates to exactly that stage.
4. **The exam already tripled once.** "8 take gates in Sherlock ep01-09 → 26 in ep14 … ~40 % of the
   retake churn was judge false alarms" (`2026-09-30_rounds_debate.md`). Measured cure rates were:
   content fault by take re-render 3/21, by panel redraw 1/1; move_type 89-100 %; seed ~0 % solo.
   Any new gate whose cure is a take re-render is mostly a keep_best generator.
5. **A rule written and never built is the house's commonest failure.** The 2026-09-28 "views are drawn
   FROM the pinned picture" was ruled and never built (B R1). The 2026-09-16 Sage A/B was proposed
   and never run (F #1). The one-sheet-per-entity rule was never enforced on the refs folder (D §0).
   A 19-commit plan carries the same risk: the late commits (judges, calibration, skill text) are the
   ones that get dropped, and they are the ones that make the early commits safe.

---

## 1. P1 (continuity), item by item

| P1 item | Call | Reason | Evidence |
|---|---|---|---|
| §0 brick: one base picture, one hop per state, a table keyed by story time | **KEEP** | It is the owner's ruling and matches C and D. | A §5, C §2c, D §2a |
| §1a `looks.json` star topology, intervals, closed markers | **KEEP** | Markers in a closed vocabulary are what make the gates able to fire. | A §5 cause 4 (the row says dark AND grey, so no check can fire) |
| §1a rule 1: `body` holds no hair, beard or hat | **KEEP, ship first** | It is the cheapest fix with the widest reach. The same class of bug ("the mustache check concatenating cast rows") was 1 of the 9 false accusations in the 09-30 debate. | rounds debate A1; A §2 ep25 T05 prompt |
| §1a `policy: fresh/edit` and §7 Q1/Q2 | **CHANGE** | Already ruled: one-step edits are allowed, chains and composites are not. The open question is now only *which route wins per delta kind*, and the bench answers it. Drop the owner question. | owner 2026-10-10 |
| §3 `keep_head`: paste the base's head box back over the edit | **CUT** | Pasting pixels from one picture into another is a composite, and composites are ruled out. It is also a seam that a 1.3x box with a 12 px feather will show on a sheet that changes collar and hat. Use the identity edit without the paste, judged by the identity rule. | owner ruling "never composites"; memory `no-composed-frame-zero` |
| §1b `places.json` with members, masters, states, variants | **CHANGE** | Keep members and masters in the slice; that part alone fixes most of the house drift (D §6.1). States and variants enter the slice only for the one-hop state edit (villa abandoned). Hours (relight) and sides (multi-angle) move to phase 2. | B R1, R3; D §6 |
| §1c `Setup.looks`, `Setup.place_state` | **KEEP** | Plans are signed by file bytes (`plan_verdict.plan_sha8`), so new defaulted fields do not void old signatures unless a plan is re-written. | `studio/plan_verdict.py:24` |
| `view = "derive:<master_id>"` (§5) | **CHANGE** | It hides a second format inside a string field that `location_view`, `grids.wide_for`, `places.status`, `panel_place` and the take builder all read. A73 is the precedent: "every value the contract can sign, every consumer can say". Use a separate field (`derive_from`), or resolve it at step 03 into a concrete view id written through `plan_provenance.record`. | LESSONS A73, A70 |
| §2 plug-in table a-m | **KEEP**, with rows k and h first | Row h (the retention line "clothes of <Picture k>") is the direct cause of the mid-take costume changes (ep18/24/25 T0). It is true by construction once the look picture is staged. | A §0.4 |
| §3 look drawing ladder, cap 2 redraws, then flagged | **KEEP** | Bounded: at most about 3 × 90 s per look. | C §5 |
| §4 production designer agent (commit 7) | **DEFER to phase 2** | A new LLM step, new refs substep and new architecture slot. For the slice, code can group by the existing `aliases` plus a 0.85 fuzzy name match, and G-PLACE refuses lookalike ids anyway. | P1 §5 G-PLACE |
| §4 new workflows: relight (dx8152), multi-angle (fal), 2.1 Consistency | **DEFER** | None is needed for the two complaints. The existing `image_qwen_image_edit_2511_single_image.json` covers the one-hop state edit. The relight LoRA "neutralises light rather than setting an hour" (D §3). Multi-angle cards show products, not rooms (D §2b). | D §2b, §3 |
| **Missing:** a look-timeline producer for a new book | **ADD (slice)** | See fact 2. It turns `state_changes` (+ `physical_evolution` where present) into look intervals with verified quotes (0.85, the G-SOURCE matcher), as a Strands agent tested with `FakeModel`. Without it the slice is WotW-only, and WotW is closed. | §0 fact 2 |
| **Missing:** "the panel IS the sheet" check | **ADD (phase 2, advisory)** | A found 4/20 ep25 panels and 4/6 ep18 panels that copy the staged sheet verbatim (front-on, standing). A look picture fixes the costume but not this copying: the panel becomes the look picture. P1 has no gate for it. It costs one DINO or SSIM comparison against the staged sheet, and A's frames are the positives. | A §2, §5.7 |
| §5 plan gates G-LOOK, G-PLACE | **KEEP, deterministic, with a FREE CODE CURE** | An unresolvable look id, or a new location id that fuzzy-matches a member, has one correct answer: rewrite it to the default look or the member/master, and record it. A gate whose cure is code does not loop the writer. | memory `walls-follow-the-chapter` ("run deterministic cures before the contract"); A87 (two gates forbade every plan) |
| §5 G-LOOK-WORDS (regex refusal of hair/hat words) | **CHANGE to a free cure, advisory refusal** | A regex reader on plan prose will misfire: "grey dawn", "grey smoke", "ice cap", "the boater in his hand", "his hat lies on the gravel". The posture reader misread prose on three episodes running (A80, A90). Strip the contradicting marker word from the person's own clause (`panel_content.shot_words` scope) and refuse nothing until the gate has been replayed on all 27 WotW plans. | LESSONS A80, A90, "Read whole words" |
| §5 G-PLACE-STATE | **DEFER** with states beyond the slice | | |
| §6 LOOK-STATE at step 03 | **CHANGE levels** | Position is right: one VL read per new look, before any grid. HARD only on headwear, hair_colour and facial_hair, the three markers that lost (A §0.2). `top` and `dirt` stay advisory: Krea2 drops counts and buried details (memory `prop-sheet-counts`), and dusty vs sooted is not something a VLM reads reliably at sheet scale. | A §0.2; LESSONS "the defining state goes first" |
| §6 relative identity `m > 0` HARD | **CHANGE to advisory** until the bench measures it | facenet is beard-sensitive. A grey, bearded, gaunt look may sit nearer a bearded stranger (the curate, the artilleryman) than its clean base, so a correct look gets refused. The rule is principled but uncalibrated, and "constants outlive their world". | `look.py:46` strangers 0.45-0.82; memory `constants-outlive-their-world` |
| §6 G-PLACE-FIXED (GeomCons ≥ 75) | **CHANGE**: slice uses a DINO same-place band as a flag; GeomCons in phase 2 | GeomCons's κ 0.74 was measured with Gemini-2.5-Flash on CANVAS frames, not with our local VL on painted interiors. The threshold is imported, not fitted. The 17 house pictures give a free negative set to fit a DINO band first. | D §4 |
| §6 G-LOOK-PANEL | **KEEP as advisory in the slice; HARD only after the replay** | It costs four fields in a read that already runs. Its cure is a panel redraw (measured 1/1). Arm it only at recall ≥ 0.8 and false refusals ≤ 0.1, measured over **all** narrator panels of ep01-27, not a handful. | rounds debate cure rates |
| §6 G-LOOK-TAKE (HARD at step 09) | **CUT the HARD level; log only** | It fires after the most expensive render, and its only cure there is a re-render (3/21). 86 % of take faults mirror the panel or prompt. The mid-take costume change has a source fix (staged look + true retention line, row h). A HARD take gate re-opens the ep14 churn. | ep14 time debate (14 rounds, 88 renders); rounds debate 3/21 |
| §8 19 commits | **CHANGE to a 9-commit slice + phase 2** | See the verdict. The slice keeps docs, spec, rows, producer, staging, drawing, places and wiring. It defers the designer agent, three new workflows, GeomCons, take gate, relight/sides and calibration docs. | §0 fact 5 |
| §11 time: +5-12 min typical | **KEEP the number, REJECT the payer** | P1 is paid for by "grid turbo −12 min", which P2 defers because its vendor names duplicates as its failure. Count it at zero. | G #2; P2 §1 |
| §12 migration: WotW none | **KEEP** | WotW inputs serve only as bench fixtures. | |
| §13 publishable continuity bible | **KEEP, as a flag** | It generalizes beyond this repo. It ships after the next book's first episodes prove it, not before. | standing goal |

---

## 2. P2 (quality + speed), item by item

| P2 item | Call | Reason | Evidence |
|---|---|---|---|
| §1 diagnosis: picture source and take model, not upscalers | **KEEP** | Sound, and it agrees with E. | E §3 |
| §1 "2048 native grid" correction, R0c layout check (CPU) | **KEEP** | Free, and it needs no pause. | E §1 |
| **Missing free split of cause 2: ep04** | **ADD (CPU, before the bench)** | ep04 ran Singularity int8 + LoRA 1.7 on the *refs-only* recipe of ep01-03 (E §1). Measured on ep04's shipped takes, the calibrated faceting/flat-patch measures show whether the take model flattens without any Qwen panel. If ep04 reads like ep01-03, cause 2 is small and round 1 shrinks to A1 vs A3 (speed only). | E §1 table, column ep04 |
| §3.1 rulers calibrated as ep01-03 vs ep20-27, AUC ≥ 0.75 | **CHANGE** | The two sets differ in content: wide sunlit heath vs dark interiors, 3/12 vs 9/12 faces (P2's own note), refs-only vs panels. A measure can win the AUC by reading darkness or face share, the "walls follow the chapter" trap. Calibrate on **content-matched pairs**: the same villa and study in ep01-03 against ep26-27 (B lists them), and normalise flat-patch share by face-box size. | memories `walls-follow-the-chapter`, `constants-outlive-their-world` |
| — banding measure | **CHANGE** | The take encode (CRF 23) is identical in both eras, so an era AUC cannot calibrate it. Use it only for A0 vs A1 (the encode arm). | E §1 |
| — detail retention panel→take | **CHANGE** | ep01-03 have no panels, so it cannot be calibrated on the era split. Report it only. | E §1 |
| §3.3 look judge calibrated on 5 pairs | **CHANGE to ≥ 10 content-matched pairs, ≥ 8 correct** | 5 pairs cannot separate a judge from a coin at 4/5. | |
| §3.6 decision rule | **CHANGE** | Fault counts on 4-6 shots × 1-2 seeds detect only gross failure. A duplicate is a rare event, so the bench cannot see a rate change. Adoption therefore needs a production tripwire: the first episode on a new arm records duplicates, identity and lip lag against the ep22-27 medians, and a regression rolls the name back (P2 §7 makes that one line). | rounds debate (first-pass yield 32-35 % historically) |
| R0b post: Lanczos vs RTX VSR (2 modes) vs FlashVSR | **CHANGE: RTX VSR ULTRA only, 3 takes, about 5 min** | FlashVSR means renaming a disabled custom-node folder (an environment change mid-bench), is GPL, and costs 15-25 min per episode, which is over budget anyway. VSR fixes no cause, so the arm is only "does it hurt". | F #2, G #1 |
| R1 arms A1 (crf), A2 (LoRA once), A3 (4-step) | **KEEP, decisive** | A2 vs A1 tests the ep04 change. A3 is the only speed lever large enough to pay for P1. | E §3.2, F #4 |
| R1 arm A4 (stock fp8) | **CONDITIONAL** | It costs a 19.5 GB HDD load and is a reference, not a candidate: Singularity was adopted because it fixed duplicates. Run it only if A2 does not recover the look. | P2 §2.2, memory `h3-singularity-model` |
| R1 six shots | **CHANGE to four + two dialogue** | S5's duplicate is born in the panel (E), so it tests nothing about the take model; drop it from R1. S6 alone cannot measure lip sync: lag depends on length (memory `mux-lag-follows-length`) and varies by seed. Use 3 dialogue takes of different lengths on A1 vs A3. | |
| R1 shift 12/3 inherited at 4 steps | **KEEP the warning** | F says hard cuts smear into dissolves at 4 steps. The `cut`/`jump` judge must read every A3 render. | F #4 |
| R1 `takes_r2v.STEPS=8` overriding the 4-step graph, and the manifest's `optional.unet_name` naming stock fp8 | **KEEP, and make it an acceptance check** | Every arm's *ran* `T*.graph.json` is read back and asserted (UNET, LoRA count and strength, steps, attention, crf) before its numbers count. Otherwise the arm is a "fix that changes nothing". | memory `a-fix-that-changes-nothing` |
| R2 B1: Krea2 + Cinematic restyle of the Qwen panel at 0.35 | **KEEP, decisive** | It is the only arm aimed at E's top cause that keeps the 09-28 room chain. Price it honestly: Krea2 must be swapped in after the Qwen grids. Batch all restyles after all grids; every later panel redraw then costs two swaps. Check identity: at 0.35 a small face can be redrawn as someone else (G #3 states it for the Restore LoRA). | E §3.1, G #3 |
| R2 B2: panel + Krea place picture + full sheet as extra H3 refs | **CUT** | Staging a second picture of the place into H3 is the known hard-cut fault ("opened on another staged picture"). D and P1 both rule out a place slot in H3. | memory `h3-freeze-and-hardcut`; D §2c; ep24 T02 (8 frames of plate) |
| R2 B3: refs-only, the ep01-03 recipe | **CUT** | P2 itself calls it "not a candidate" (it breaks the 09-28 room ruling). The ep01-03 shipped takes are already the reference at zero GPU. | P2 §2.2 |
| R2 B4: full sheet instead of the crop | **CHANGE: fold into the continuity bench, takes only** | Grids may not stage the whole turnaround: ep16 drew it "as up to four people" (`grids.sheet_of` docstring). For takes the crop was chosen by an A/B (ep16 T11/T25). The look-picture arm (P1 bench) asks the same question with the right picture. | `scripts/episode/grids.py:152`, ep16 audit |
| R3 Sage wheel (C1) | **DEFER to its own window** | Swapping the wheel in the portable Python is an environment change with a rollback, not a bench arm. On 4-step it saves only about 5-7 min per episode (25-30 % of about 42 s × about 30 renders), not 8-15. | F #1 |
| R3 CK attention flag (C2) | **KEEP, last arm, droppable** | It is only a relaunch flag, with no install. | F #1 |
| R4 latent upscaler | **CUT** | +50-100 min per episode, over budget by P2's own table. Tiled duplicates in the only test, no ref2va test, and a 691 MB download. | F #3 |
| R5 E1 move-type seed for stills | **KEEP as a ladder rule, not a bench arm** | The cure rate is already measured: move_type 89-100 % on frozen/held. | rounds debate §5 |
| R5 E2 4x-supersample push | **KEEP, CPU, test-first** | Free. | |
| §5.5(b) cap: ≤ 2 stills, ≤ 3 s, else cut or merge | **CHANGE** | Shortening a voiced shot breaks "the voice is the ruler". Past the cap the route is a move-type retake, never a shorter shot. | memory `the-voice-is-the-ruler`; A88 |
| §4 `_crf_visurena` take save (crf 10) | **KEEP** | It removes the lossiest generation. Accept on ffprobe > 5 Mb/s and the ran graph's crf key. Disk: about 1-2 GB per episode. | E §3.3 |
| §5.2 lossless segment extract `-qp 0` | **KEEP, cheap** | Test-first, then measure that the frames hash-match. | |
| §5.4 NVENC for the book compilation | **DEFER** | It is outside the episode clock, and WotW's compilation is a one-off. Keep only the idea of forcing a keyframe at the card boundary in `assemble` (stream-copy the next book's pieces), which is cheap code. | |
| §6 time table | **CHANGE** | Sage and 4-step are not additive (see §3 below). | |
| §8 licence flags | **KEEP as flags** | Note that the Qwen-Image 2.1 flag applies to the grids that already ship, not only to new LoRAs. Not legal advice: the owner's attorney decides. | G finding 3 |
| §9 publishable ref2va bench | **KEEP, as a flag** | Publish the bench as run (configs, seeds, ran graphs, per-phase seconds, content-matched calibration), including the arms that lose. | standing goal |

---

## 3. Is the 6 h budget met? The honest projection

Baseline (ep19-27, measured): **median 5.68 h**, mean 5.74 h, 3 of 9 episodes over 6 h. The owner's
figure of about 6.0 h is about right for the upper half.

| Change | Δ per episode | Basis / why not P1's or P2's number |
|---|---|---|
| P1 slice (look draws, one-hop variants, VL reads, plan gates with free cures) | **+5 to +12 min** | P1 §11. The derived variants replace fresh place draws (net about 0). |
| P1 plan-gate deferral risk | **+0 if the cures are code; +15-30 if HARD-to-writer** | ep26: two deferrals made the plan 142 min against a 64 median |
| crf 10 + lossless segments | +1 | |
| A3 4-step, if it wins | **−15 to −20** | 41 s saved per render × about 25-35 renders. P2's −30 assumes the top of the range. |
| CK/Sage on top of 4-step | **−5 to −7** | 25-30 % of the 42 s left. P2 counted it on 8-step sampling. |
| CK/Sage alone, if 4-step loses | −10 to −12 | |
| B1 Krea restyle, if it wins | +6 to +10 | + two model swaps per panel-redraw rung |
| RTX VSR per take | +3 to +5 | |
| Stills move-type seed (≤ 4 shots) | +5 to +10 | |

**Scenario W (4-step wins, B1 wins):** +8 +1 −18 −6 +8 +4 +7 ≈ **+4 min → median about 5.75 h.**
**Scenario L (4-step loses, B1 wins):** +8 +1 −11 +8 +4 +7 ≈ **+17 min → median about 6.0 h**, and the
upper half over budget.
**If the bench loses (scenario L), cut in this order:** RTX VSR (it fixes no cause) → the stills seed
rung (keep the cap and the supersample) → B1, kept only if its quality win is decisive on the
calibrated measures *and* the owner's view. P1's slice is never cut: it is the owner's complaint.

**What neither plan fixes:** the tail. ep19-21 ran 6.8-9.2 h on the plan stage and on stops. The
P90 stays over 6 h whatever the bench says. That is a separate debate (plan stage + stops), and
it must not be "solved" by quietly loosening the continuity gates.

---

## 4. The bench: cut from 3.3 h to about 2 h

The owner approved 1-2 h of paused GPU. P1's bench (about 30 min) and P2's (about 3.3 h) together
come to about 3.8 h. **3.3 h is not needed.** Round 4 is over budget whatever it shows. B2 and B3 are
not candidates. Round 5's GPU half is already measured. FlashVSR and the Sage wheel are environment
changes, not arms.

**Before the pause (CPU, no GPU, can run now):** content-matched ruler calibration (villa/study ep01-03
vs ep26-27), the ep04 split of cause 2, R0c grid layouts, a replay of the P1 plan gates over all 27
WotW plans (count false refusals), and the G-LOOK-PANEL marker check on the existing
`panel_content.json` subject lists.

| Block | Arms | Renders | GPU min |
|---|---|---|---|
| B-0 post | Lanczos vs RTX VSR ULTRA, 3 shipped takes | 0 H3 | 5 |
| B-1 take model | A1 (crf), A2 (LoRA once), A3 (4-step) × S2, S3, S4, S6; 2nd seed A2 + A3; 2 more dialogue shots A1 vs A3 (A4 only if A2 fails: +10) | 24 | 45 |
| B-2 picture source | B0 vs B1 restyle on S3, S4, S5, S6 (+ 4 Krea passes); 2nd seed for B1 on 2 shots | 6-8 | 20 |
| B-3 continuity (P1) | narrator looks `flannel_buried`, `ragged_greyed`, `epilogue_home`: one-hop edit vs fresh (6 draws + reads); one ep25 grid × {`sheet_front`, look picture} + its 2 takes; villa `abandoned`: 2511 one-hop vs fresh | 2 H3 + 10 stills | 25 |
| B-4 attention (droppable) | CK flag (relaunch) on the winner, 3 shots | 3 | 15 |
| Loads and restarts | | | about 10 |
| **Total** | | | **about 2 h** (1.6 h without B-4) |

Decisive arms: **A2, A3, B1, and B-3's routes**. Everything else is a reference or droppable.

---

## 5. Hidden risks (all plans)

- **`sheet_front` crop vs look picture.** The look picture must be the same shape as the crop (one
  figure, front), or the ep16 clone fault returns in the grids. The verbatim-copy risk then moves:
  the panel becomes the look picture standing front-on (see the ADD row in §1).
- **H3 copies the panel** (E: frame 0 ≈ panel). Every panel fault, the B1 restyle and a wrong look all
  pass straight into the take. That is why the cure belongs at the panel or the sheet, never at the
  take.
- **New view ids vs existing plans.** A `derive:` string in `view` breaks every reader that does not
  know it (A73). New defaulted fields are safe for old signatures (byte-hashed) until a resume
  re-writes a plan; any re-write goes through `plan_provenance.record` (A70).
- **Manifest defaults.** The base take manifest's `optional.unet_name` names stock fp8 and
  `sage_attention` is `disabled`, and `takes_r2v.STEPS=8` overrides a 4-step graph. Each new
  manifest's defaults match its own graph, enforced by a test, and each bench arm is verified on its
  *ran* graph.
- **Lip sync at 4 steps.** The turbo LoRA already "costs audio" (F). A3 is adopted only if lag on 3
  dialogue takes stays within ±0.1 s of A1's, with `lock_audio`-style guarantees unaffected (the guide
  audio stays at frame 0).
- **Model swaps.** Step 03 would load Krea2 (looks), Qwen 2511 (variants) and VL (judges), then step
  07/08 loads Qwen 2.1 (grids) and perhaps Krea2 again (B1). Each swap is minutes off the NVMe and
  more off `.hdd_bak`. Batch by model and count the swaps in the time table, not only the draws.
- **Licences (flags only, not advice):** Qwen-Image 2.1 (grids today; Consistency/Restore/Viggle
  inherit it) is reported under a Qwen Research License. 2511 is from the earlier line (check it). FlashVSR
  nodes are GPL-3.0. H3/Singularity fall under the MiniMax H3 Community License. The owner's
  attorney decides.

---

## 6. VERDICT: the reconciled, ordered build

**Phase 0: bench (about 2 h GPU, $0, in the owner-approved pause; CPU prework first).**
New workflow files only (`<base>_<source>.json` + manifest). No production name changes.
*Acceptance:* every arm's ran graph matches its claim (UNET, LoRA, steps, crf, attention); the crf
take reads > 5 Mb/s. Each adopted arm is non-inferior on duplicates, identity and the lag of 3
dialogue takes, and wins (quality arms) or ties (speed arms) on ≥ 2 rulers calibrated on
content-matched pairs. A ruler that fails calibration is reported and does not vote. The output is a
page of side-by-side results for the owner (optional, nothing waits on it) plus a decision file. If
nothing wins, the status quo stands.

**Phase 1: the minimal continuity slice (9 commits, test-first, all fakes).**
1. Docs: decision file, `architecture/plan/` tracker, DECISIONS line, README rows, architecture *Future* tab.
2. `studio/continuity_spec.py`: Look (interval chapter[/scene], layers, closed markers, parent = base),
   Place (members, masters, optional states). Star topology validated.
3. Body/layers split: `character_row` never carries two heads; `panel_content.contradictions` and
   `take_content.drifted` compare **markers**.
4. Look-timeline producer for a new book: an agent over `state_changes` (+ `physical_evolution`),
   quotes verified at 0.85, FakeModel test. `looks_from_dossier` for the WotW format.
5. Staging: `look_sheet`, `grids.sheet_of`, `cast_sheet` look rung, `reference_list`, retention line
   true by construction, plus the step-06 lint (subject look = staged look).
6. `scripts/refs/looks.py` at step 03: the one-hop route the bench picked per delta kind (no head
   paste), and LOOK-STATE (headwear, hair, facial hair HARD; the rest and identity advisory).
7. Places: membership by aliases + fuzzy match; G-LOOK and G-PLACE with **code cures**
   (rewrite to the default look or the member/master, recorded); the brief lists drawn views and
   history and drops undrawn ids.
8. `places.py`: a state variant is a one-hop 2511 edit of the master (existing workflow); a new side
   is drawn once and frozen; a DINO same-place band (fitted on the 17 house pictures) flags.
9. Step 03 wiring, `stages.yaml`, SKILL/GATES/LESSONS, architecture *Current* tab, republish.

*Acceptance (artefact, not tests):* a bench replay of one ep25 grid and one ep27 grid with the
look pictures. The narrator shows grey hair and beard in ≥ 80 % of his panels (VLM list plus a contact
sheet looked at), against 0-1 of about 24 shipped. The ep26/ep27 plans replayed: `narrators_dining_room`
and a fresh `reverse` are rewritten to the member/master, not drawn. The villa `abandoned` variant
shows the forced door and sits inside the same-place band. The P1 gates replayed on all 27 WotW plans
give ≤ 1 false refusal per plan, each one read by hand.

**Phase 2: judges armed and continuity widened (after the slice runs on the next book's first episodes).**
G-LOOK-PANEL armed HARD at recall ≥ 0.8 and false refusals ≤ 0.1 over all ep01-27 narrator panels;
the "panel is the sheet" advisory; GeomCons G-PLACE-FIXED fitted on our pictures; G-PLACE-STATE;
the production-designer agent; relight and multi-angle workflows; G-LOOK-TAKE as a logged measure
only.
*Acceptance:* the next book's first three episodes show zero wrong-look and zero new-room faults on
the owner's audit sheet, and add ≤ 1 stop per episode against the ep22-27 average.

**Phase 3: adopt the bench winners in production.** The `takes_r2v.BASE` name, B1 behind a flag,
crf, lossless segments, the stills rule (move-type retake, supersampled push, a cap that never
shortens a voiced shot), and RTX VSR only if scenario W holds.
*Acceptance:* a production tripwire on the first episode (duplicates, identity, lag, clock vs ep22-27
medians), with a one-line rollback.

**Phase 4: deferred.** Sage wheel (its own window), latent upscaler, grid turbo, realism LoRA,
360 plates, NVENC, Consistency LoRA (subject to the licence ruling).

**Per-episode time projection:** median 5.68 h today → **about 5.8 h after phase 1** → **about 5.75 h
(4-step wins) or about 6.0 h (it loses)** after phase 3, with the scenario-L cuts in §3. The P90 stays
over 6 h in every scenario until the plan stage and stops are debated on their own.

**Publishable (flag):** (a) the ref2va consumer-4090 bench with content-matched calibration; (b) the
continuity bible (look and place tables, star rule, list-then-judge verifiers), after the next book proves it.
