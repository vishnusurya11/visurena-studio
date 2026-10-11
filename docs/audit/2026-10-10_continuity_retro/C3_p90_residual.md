# C3 P90 residual: what is left in ep20 and ep21 after the cycle-3 rules

2026-10-11. CPU only, read-only on `library/` (WotW ep20 and ep21 homes, the WotW `learnings.jsonl` and `relaunch.json`), and $0. **No code was built for this item; it is a proposal** (§4 says why it falls short of the 95 % bar).

**Inputs:**
- the builder's 3A replay, `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c3b\replay_3a.py` / `replay_3a.json`, with its numbers: P50 5.10 h, P90 6.45 h, ep20 372 min, ep21 448 min;
- C3_T's `relaunch.json` (`...\scratchpad\c3\`);
- the as-built code: `studio/run_budget.py`, `studio/judged_gate.py`, `studio/take_ladder.py`, `studio/plan_tags.py`, `studio/gate_policy.SAFETY`, `scripts/episode/qc.failed_rows`.

**Scratch scripts.** All of them reuse `replay_3a.py`'s own `span`, `saving`, `cum` and `k`, so every clock below is the same adjusted clock 3A used. Folder: `C:\Users\vishn\AppData\Local\Temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c3cpu\`
- `timeline.py` / `timeline.json`: every run of ep20 and ep21 on the adjusted clock.
- `rungs_at.py`: every learnings rung, with its clock time.
- `plan_tags_ep21.py`: ep21's plan drafts, tagged BUILDER or JUDGED by the as-built `plan_tags`.
- `reserve.py` / `reserve.json`: the proposed rule, priced on ep19-27.

## 1. Summary

| | finding | measure | conf. |
|---|---|---|---|
| 1 | **ep20 is already under 6 h under the as-built rules. 3A did not model D3's QC rule.** 3A cuts only learnings rungs. QC fail → recut → QC loops are not learnings rows, so 3A kept all six of ep20's post-crossing QC cycles. Under 97be974, step 11 at a spent clock ships a non-SAFETY fail flagged. ep20's QC fails were sound cues, the first-frame cue, speech-over-gap (stacked gun reports) and loudness. ac3e6a0's leveller now runs before QC, so the master reaches QC already in band. **None is SAFETY.** | ep20 ends at **314 min** (QC in run 7 starts at clock 304, 4 min past the crossing). If the crossing is 10 min later than modelled, it ends one recut later, at **338**. Both branches are under 360. | 90 % |
| 2 | **ep21's crossing comes 20 min into step 09's round 0** (adjusted clock 300; round 0 runs 281 → 359). Round 0 (32 firsts) always renders, and so do edit, one QC and publish. **The floor after the crossing is ≈ 79 min, so ep21 cannot finish before ≈ 379 min (6.3 h)** even with every post-crossing rung and relaunch removed. This is exactly the "pre-round-0 crossing" C3_verdict §3A told 3A to name. | `timeline.py`, `rungs_at.py` | 95 % (by the record) |
| 3 | **Why the ceiling does not bound ep21: what put it there is pre-crossing relaunch waste, not rungs.** Of the 300 pre-crossing minutes, about 170 are code and config faults met in production: provider config ×4 (34), the MONEY wall deferral (13), the CONTRACT 16-word style-wall deferral (52, a calibration fault), say_lines exit 1 (15), a signed plan re-planned after step 05's unrecorded rewrite (≈ 55, fixed 8eaf7b4), and grids KeyError 'full' (5). The 5 h ceiling sees all of them only as spent time, and they land before it. | `timeline.py` + the fix commits | 90 % |
| 4 | **Shares reset every run.** `Budget.start` measures `in_step` from this process's step start, so each relaunch hands step 02 a fresh 70-min share. Only the ceiling is cumulative, and nothing reserves time for the **firsts still owed downstream**. | code | 95 % |
| 5 | **Proposal: the downstream reserve at 6 h.** A rung of step S runs only if `spent + price + reserve(S) ≤ 6 h`, where reserve(S) is the as-built shares of the firsts after S (02: 203, 08: 137, 09: 32, 11: 6 min). This is in addition to the 5 h rule; refusals are terminal with D3's semantics, and it never parks. On ep19-27 it is **selective**: it refuses rungs only on ep20 (2 panel rungs, 17 min) and ep21 (16 rungs, 103 min), and it adds no terminal anywhere else. | `reserve.py` | 95 % on selectivity; **50-60 % that it brings ep21 under 6 h** |

## 2. ep20: what is left, run by run

On the adjusted clock (k = 0.909), the crossing at 300 falls inside run 7 (292 → 312: 09 retake 10.2, 10 3.1, 11 QC 8.4).

| runs (clock) | what ran | under the as-built rules |
|---|---|---|
| 7 (292-312) | retake, recut, QC FAIL (the 3.0 s clink: sound presence, 78f9071) | QC starts at 304, past the crossing. `qc --ceiling-spent` runs the ear, `failed_rows` = `sound`, and **ships flagged**. |
| 8-15 (312-363) | 4 more QC FAILs (the first-frame cue 9c88eac, loudness -17.49 ac3e6a0, stacked gun reports and speech-over-gap 6.8 c13a4b3, stem lift chasing itself 4172383), 2 assemble refusals, 1 session kill | **do not happen**: the episode shipped at run 7 |
| 16 (363-379) | QC pass, deliver, publish | 12 + 13 only, ≈ 2 min after run 7 |

- **ep20 ≈ 314 min (5.2 h)**, or 338 min if run 7's QC had started before the crossing.
- **The quality price:** ep20 ships with its sound rows flagged on the audit sheet. These are the cue and gap faults the later commits fixed. The owner's audit sheet shows them.
- **What 3A should change:** add one rule to the replay. After the crossing, the first QC whose failed rows are all outside `gate_policy.SAFETY` ends the episode at that QC + 12/13.

## 3. ep21: what is left, run by run

On the adjusted clock (k = 0.899):

| clock | runs | what | kind |
|---|---|---|---|
| 0-57 | 1-8 | 4 provider failures (400, None content, finish_reason=length ×2), 2 plan kills (T1 saves them), MONEY deferral | config faults: deterministic, no rule bounds them |
| 57-114 | 9-10 | plan battery deferral on CONTRACT "17-word style line, the wall is 16" (BUILDER every rung), a kill | a calibration fault |
| 114-170 | 11-12 | plan signed (keep_best critic, JUDGED-only); say_lines exit 1; step 06 refuses packed takes (397cc6a) | code faults |
| 170-238 | 13-16 | **the signed plan re-planned**: step 05 rewrote it unrecorded, so the signature lapsed (8eaf7b4). Run 14's climb: improve#1 BUILDER (PLAN GATES, G-TAKELINT), improve#2 **JUDGED-only (34)**, fb, model_tier BUILDER, keep_best = the JUDGED-only draft → defer; then a kill; run 16 re-climbs and signs; grids KeyError 'full' (d8d47ea) | code faults + plan rungs |
| 238-281 | 17 | grids, panels (+2 panel rungs at 262/272) | firsts + rungs |
| **281-359** | 17 | **step 09 round 0: 32 firsts. The 5 h crossing is at 300, inside it.** | firsts: always render |
| 359-505 | 17-22 | retake rounds and master retakes (the 57 min 3A cut), a session kill at QC, re-judge on moved code (09 redo 5.2 + 21.2), a split voice at the upload door (now cured at step 04, 434213e), revoice, a stale T02 after a master retake (SAFETY `takes_unjudged`; 6a7f8b7, and a spent clock no longer retakes), 3 QC passes | rungs, relaunches |

- **The floor under today's rules**, if nothing after the crossing relaunches: 359 + 0.899 × (10: 4.7 + QC without retake: 14.8 + 12/13: 2.9) = **379 min (6.3 h)**.
- **3A's 448** also keeps the post-crossing relaunches. Of those, the split voice and the stale T02 cannot recur under today's code. The re-judges on moved code (≈ 16 adj min) and the session kills can.
- **So ep21 lands somewhere in 379-448 under the as-built rules.** It is over 6 h either way.

## 4. The smallest code-only fix, and why it is a proposal

**The downstream reserve at the owner's 6 h.**
- **Where:** `judged_gate.affordable`, `take_ladder.can_afford` and the plan ladder's budget check get one extra condition: `budget.headroom_to(6 h) - price >= reserve(step)`.
- **The reserve:** `reserve(step) = EPISODE_CEILING_SECONDS × Σ EPISODE_SHARES of the steps after it`. It is computed from the existing shares; nothing new needs pricing.
- **A refusal** is the D3 terminal:
  - a ladder signs its best, flagged;
  - a plan with JUDGED-only lines signs `keep_best` flagged;
  - a BUILDER line buys its ≤ 3 `ladder_over_clock` rungs, then stops on SAFETY, as at a spent clock.
- **What does not change:** firsts are never refused, nothing parks, and the 5 h rule stays as it is.
- **Size:** about 15 lines in `run_budget.Budget` (one method) plus the three call sites, written test-first.

**Measured effect on ep19-27 (`reserve.py`):**

| ep | rungs the 5 h crossing cuts today | reserve@6h refuses | note |
|---|---|---|---|
| 19, 22, 23, 24, 25, 26, 27 | 0-1 each | **0** | No new terminal: the rule touches only episodes headed past 6 h |
| 20 | 1 (8 min) | 2 panel rungs (17 min, clock 222/235) | ep20 is under 6 h without it (§2) |
| 21 | 6 (57 min) | **16 (103 min)**: 6 improve, 2 model_tier, 2 panel, 4 take cures, 2 master retakes | see below |

**The effect on ep21, bracketed:**
- **Rung-only accounting** (3A's method): 505 − 103 = **402 min (6.7 h). Over.**
- **With the plan signed at run 14's JUDGED-only draft** (08:04, two rungs in; the reserve refuses the rest), runs 15-16's re-climb disappears (≈ 29 adj min of non-fresh_brief plan work). The panel rungs go as well (9). On the §3 floor that gives **≈ 341 min (5.7 h). Under.**
- The re-judges on moved code after the crossing (≈ 16) put it back to **≈ 357**, right at the line.

**Why it is not built:**
- The bar is 95 %, measured, in both episodes.
- ep20 does not need it.
- ep21 is **one case**, and its result depends on two things:
  - the counterfactual that an earlier signature removes runs 15-16, which the record cannot show;
  - the k-scaled clock, which is good to about ±10 min against a margin of 3-20 min.
- That puts my estimate at **50-60 %**.
- The quality price is real: ep21 would ship a plan with 34 JUDGED battery lines flagged (G-VARIETY, G-STORY-class).

**What would raise it to build:**
1. **Correct 3A with the D3 QC rule** (§2; CPU, about 10 lines in `replay_3a.py`). That alone moves ep20 to 314-338 and changes the P90 table below.
2. **A second case:** run `reserve.py` over the Scarlet ep10-14 timing rows. They have no drive or DB records, so this needs a clock reconstruction first.
3. **One companion rule:** "at a spent clock a signed verdict stands under moved code: a re-judge is a repeat, flagged with the old measuring sha". It removes ep21's ≈ 16 post-crossing minutes, and it is the same "refuse repeats, never firsts" law. `takes_stale` (edit provenance) stays SAFETY, so stale bytes still stop the episode.

**Projection:**

| scenario | P50 | P90 | over 6 h |
|---|---|---|---|
| 3A as published | 5.10 h | 6.45 h | 2/9 |
| 3A + the D3 QC rule (ep20 → 314; ep21 kept at 448) | 5.10 h | **6.05 h** | 1/9 (ep21) |
| + the reserve@6h, rung-only (ep20 297, ep21 402) | 4.95 h | 5.90 h | 1/9 (ep21) |
| + the reserve and the run-14 signature (ep21 ≈ 341-357) | 4.95 h | 5.69-5.75 h | 0/9 |

Note that the P90 statistic can pass 6 h while ep21 itself stays over. The owner's rule is "every episode" (C3_T), so only the last row meets it.

## 5. The bedrock

- **The ceiling bounds rungs. It cannot bound firsts, or waste that lands before it.** The guarantee is "the episode ends by 6 h" only when `crossing + firsts owed ≤ 6 h`.
- **ep21 broke that inequality.** About 170 minutes of production code faults before the crossing pushed it into round 0 of a 32-shot episode.
- **Code can do two things:**
  - **reserve the firsts' time** (the proposal): rungs stop while the firsts still fit;
  - **stop repeats after the crossing** (the companion rule).
- **Code cannot bound the faults themselves.** They are new bugs each time, and the lever is upstream: fixes run on the replay set before a live episode (C3_verdict §6.2).

**Publishable (flag):** this is the missing half of "the clock you budget against is not the clock you spend". A resumable pipeline's ceiling guarantees its completion time only when it reserves the never-refusable work still owed. The measured case is ep21's crossing 20 min into round 0. It fits the same short paper.

## 6. Also this pass: the tick_error fix (committed)

**Commit 50a35c8, "A book upload row never stops the tick".**
- **The cause:** `book_compilation` writes `uploads.jsonl` rows with `episode: "compilation"`. `studio.autopilot.next_unit`/`published` call `int()` on them, so from 2026-10-10 23:24Z every tick raised (1,932 `tick_error` events by 2026-10-11 18:37Z) and status.json froze.
- **The fix:**
  - `episode_rows` keeps only chapter rows;
  - the CLI reads uploads through `uploads_of` at gather, status_doc and tick. This also stops `status_doc`'s `sorted()` from mixing `str` and `int`, the TypeError that would have come next.
- **Tests:** written first (4 failed, then green), in `tests/test_a_book_upload_row_never_stops_the_tick.py`. The autopilot suites are green (125).
- **On the real WotW file:** `next_unit` now answers None (the series is complete).
