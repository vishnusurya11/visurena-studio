# C3-T: the P90 tail (cycle 3, researcher T)

2026-10-11. Read-only: CPU, the repo, the studio DB (opened `mode=ro`) and the library's run records. No GPU, no code edit, no ComfyUI touch. HEAD at the time of reading: 2ddcbbc.

The bar is the CYCLES one: **95 % = measured on the artefact, in at least 2 independent cases.** Anything weaker is marked as a hypothesis.

**Owner ruling (2026-10-11):** the 6 h limit applies to every episode, so it is a P90 limit, not a P50 one.

**Scratch.** Every number below comes from one of these scripts. Rerun any of them with `python -I <script>`.

Folder: `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\53388bed-712c-4d9b-972d-6c2de9a9f94e\scratchpad\c3\`

| script | output | what it reads |
|---|---|---|
| `relaunch.py` | `relaunch.json` | Every run of WotW ep12-27. Runs come from the DB `events` table (one `run_id` each), deaths from the autopilot `events.jsonl` (stale_lock, park, the next launch), causes from the failed/deferred detail |
| `ledger.py` | `ledger.json` | ep19-27: machine minutes, waste by cause, and redo split by whether the code SHA moved (`drive.jsonl` start rows) |
| `rungs.py` | `rungs.json` | Per-rung minutes and outcomes of every PLAN climb, ep12-27 (`learnings.jsonl`) |
| `stage_p90.py` | `stage_p90.json` | Per-step P50 and P90 against `run_budget.EPISODE_SHARES` |
| `projection_c3.py` | `projection_c3.json` | Starts from the C2 "as built" rows (`..\c2\b\projection.py`) |
| `audio_chunks.py` | `audio_chunks.json` | Whether the master audio stays bit-identical across `master_iterN` |

## Summary

| # | Finding | Measured | Confidence |
|---|---|---|---|
| 0 | **The clock does not see all the machine time.** A killed run writes no `timing.jsonl` row for the step it was in. Over ep19-27, **398 machine-min** are invisible to the clock and to the C2 projection (ep21 +166, ep22 +86, ep26 +75, ep23 +53). With them counted, C2 "as built" is **P50 5.88 h and P90 7.55 h, with 4/9 episodes over 6 h** (published: 5.04 / 6.92 / 2/9). | 23 killed runs, 6 episodes | 95 % |
| 1 | **The P90 tail is entirely relaunch waste.** Remove each relaunch's lost and redone minutes and ep19-27 projects to **P50 4.24 h and P90 4.85 h, 0/9 over** (conservative: failed GPU steps are counted as reused). The plan stage stays fully inside that figure. | 1,218 waste-min, 9 episodes | 95 % |
| 2 | **22 of the 23 killed runs** have a session `pause`/`retry` within 10 minutes. The autopilot never kills a live drive on `code_moved` (`run_loop` only exits, and the drive stays RUNNING). The kills were people fixing code mid-episode. | events.jsonl + code | 95 % |
| 3 | **A killed plan climb loses its best draft.** `Desk.best` lives only in memory until the terminal. In 111 of 329 rung verdicts the draft on disk was worse than the best so far. Four cut climbs restarted worse than their best: ep17 1→38, ep22 35→46, ep26 5→6, ep13 0→22. | 4 cases, 3 books-weeks | 95 % |
| 4 | **The one clock has three holes:** (a) the unlogged time in row 0; (b) every `autopilot retry` resets it (`reset_clock`, dce4aa7), 67 retries over ep19-27; (c) plan rungs cost `0.0` s (`plan_ladder.ladder()`), so the plan stage, which is the largest P90 stage, is never refused by the budget. The ceiling is **5 h** and parked ep19-22 `over_budget` 4 times. Each park was retried, and each retry reset the clock. | code + events | 95 % |
| 5 | **Critic-side savings are worth less than 1 min per episode.** Critic = 3 sequential workhorse reads, median span 27 s (33 critics). Rung minutes are the writer's. | DB usage rows | 90 % |
| 6 | **The master audio changes everywhere on every recut.** 0 of about 50 3-s chunks stay bit-identical between iterations, except where nothing was recut. A per-line Whisper memo keyed on master audio would never hit, so C2's "QC memo" is refuted again at the window level. Whisper (`large-v3-turbo` on the CPU) is the QC: ffmpeg scene, grey decode of the master and 24 takes total about 8 s of a 7-12 min QC. | 7 episodes, 27 iterations | 95 % |

---

## 1. Relaunches: every mid-run stop, why, and what it cost

### 1.1 Method

- **A run** is one `episode.py` process: one DB `run_id`, with `started`/`completed`/`failed`/`deferred` rows per step.
- **A run's end cause** is one of:
  - the failing step's detail (`fail:refused` = a script exit or gate refusal, `fail:qc-refusal`, `fail:llm`, `fail:crash`);
  - `deferred` (the plan battery);
  - `killed` (a step `started` with no end row).
- **The death time of a killed run** is the earliest of: the autopilot `stale_lock` or `parked` for that episode, the next launch of any episode, or the next run.
- **Waste** = minutes in flight at the kill + the failed step's minutes + the next run's **redo**. Redo means steps completed again after an earlier run had completed them.

### 1.2 Per episode, ep19-27 (`ledger.py`)

| ep | timing.jsonl min | + unlogged in-flight | machine min | runs | SHAs | retries | waste | redo after code moved / same code |
|---|---|---|---|---|---|---|---|---|
| 19 | 407 | 5 | 412 | 14 | 13 | 9 | 134 | 88 / 34 |
| 20 | 423 | 6 | 429 | 16 | 13 | 12 | 247 | 45 / 39 |
| **21** | 553 | **166** | **719** | 22 | 22 | 18 | **384** | 124 / 0 |
| 22 | 334 | 86 | 420 | 11 | 10 | 6 | 102 | 8 / 0 |
| 23 | 188 | 53 | 241 | 5 | 4 | 3 | 65 | 13 / 0 |
| 24 | 270 | 6 | 276 | 9 | 8 | 7 | 75 | 33 / 3 |
| 25 | 229 | 0 | 229 | 2 | 1 | 0 | 0 | 0 / 0 |
| 26 | 341 | 75 | 416 | 7 | 6 | 6 | 101 | 17 / 0 |
| 27 | 357 | 1 | 357 | 7 | 7 | 6 | 110 | 29 / 0 |

ep25 is the only clean episode (1 SHA, 0 retries): 229 min. ep12-18 ran before the autopilot existed and logged 8-52 runs each (ep13: 52 runs, about 40 h in total), but they have no death events, so their in-flight minutes are unknown and they are left out of the minute totals.

### 1.3 Waste by cause, ep19-27, ranked

| rank | cause | waste-min | n | why the run stopped (cases) | preventable by code? |
|---|---|---|---|---|---|
| 1 | **killed: session pause, fix, retry** | **527** | 22 | A person or session pauses, kills the drive mid-step, commits, retries. The plan climb was in flight 15 times: ep21 ×5 (32/40/35/7/35 min), ep22 ×4 (23/25/25/12), ep26 69. | **Partly.** T1 (plan checkpoint) and T1b (stop at a boundary) remove the in-flight loss. The redo on moved code is discipline. |
| 2 | **fail:refused** (a script exit or gate refusal: a code fault met in production) | 326 | 15 | takes_r2v/grids/assemble/say_lines exit 1; the measured-pair unpack (ep26, ep27); take_content_check after 101 min of step 09 (ep20 r04) | No, it is a bug per stop. **But** GPU artefacts survive: ep27's failed 71.5 min of grids re-ran in 5.8 min, so the failed minutes overstate the loss. |
| 3 | **fail:qc-refusal** | 222 | 12 | ep20 ×5 and ep24 ×5 on sound and edit rows; ep21, ep22, ep26, ep27 ×1 each | **Partly**, through T2 (fail-fast) |
| 4 | killed: owner order ("publish 19-22 first") | 53 | 1 | ep23 r04 at step 09 | T1b |
| 5 | fail:crash | 47 | 6 | ep19 publish `invalid_grant` ×3 (each relaunch re-ran 09/11 for 31-34 min on moved code), KeyError, `1` | The token park exists now (LESSONS) |
| 6 | fail:llm (provider) | 41 | 6 | ep21 r03/04/06: TypeError on None content, `finish_reason=length` ×2. ep19 OverBudget. | **No:** all were deterministic config faults (grammar too large, max_tokens, reasoning mandatory) that a retry resends identically. 3/3 ep21 cases. |
| — | deferred: plan battery | 0 redo | 23 | Designed: drive resumes, `cure_aside_first`, re-climb. Its minutes are plan-stage minutes (§2). | — |

**Where the P90 episodes' minutes went.**
- ep21 (719 machine-min) had 384 min of waste: 243 from session kills (5 plan climbs killed mid-rung, 166 min unlogged), 77 QC, 38 provider.
- ep20 (429) had 247 min of waste, 186 of it refusals, including step 09's 101-min take_content crash.

### 1.4 Which relaunch costs code can remove

- **T1: plan checkpoint, persist `best` and the climb state.** Replay-safe; 95 % on the issue.
  - `Desk.remember()` keeps the best battery-refused draft in memory. It reaches disk only at the terminal (`best_refused`/`defer`).
  - A kill or crash leaves `plan.json` = the **last** draft, which in 111 of 329 rung verdicts was worse than the best.
  - The fix:
    - write `plan.best.json` (draft, faults, merged refusals, rung index) on every `remember()`;
    - on the next run, start from it: same drafts, same verdicts, same terminals; only crash survival changes.
  - **Saves** the in-flight plan minutes beyond the rung in flight (5 min each): ep21 125, ep22 66, ep26 64 machine-min. The P90 on the honest series goes 7.55 → 7.14 h.
  - Test first: a FakeModel climb killed after rung 2 resumes from the best draft and its merged refusals, not from the last draft. A clean climb writes byte-identical `plan.json`/verdict with and without the checkpoint.
- **T1b: stop at a boundary.** Code change; 90 %.
  - `autopilot pause --at-boundary` drops a flag that `step_runner.run_steps` reads between steps, and that `judged_gate`/`take_ladder` read between rungs. The run then exits cleanly, with its timing rows written.
  - A session that wants to land a fix waits for the boundary instead of killing the run.
  - This removes the reason for 22 of 23 kills, though not the redo the fix itself forces.
  - Saves the non-plan in-flight minutes too (ep23 53, ep21 15, ep26 7, ep24 6). It is an [arch] change: a new stop path for the runner.
- **T2: QC fail-fast.** Replay-safe; issue 95 %, saving 85 %.
  - Run QC's cheap hard rows first: loudness, true peak, cuts, `edit_gate`, `episode_sound.presence`, the gap. Measured ≈ 8 s of ffmpeg on ep27.
  - If one fails, write the FAIL report **without** Whisper and refuse.
  - A pass still needs every row, Whisper included, so no shipped master changes.
  - By commit text, the cheap rows caused **10 of 14** QC-fail runs: ep20 cue and loudness ×5, ep24 T02 head plus spade cue ×4, ep26 still-push. The other two (ep22 'Good dog!', ep27 'Night spring back') were lines-heard.
  - **Saves ≈ 78 min over ep19-27** (0.7 × the failed QC minutes). P90 7.14 → 6.79 h.
  - Test first: a FakeTranscriber that counts calls is never called when the edit gate fails, and is called on every pass.
- **T3: an honest clock.** It saves nothing, but it makes the ceiling true.
  - `episode_clock.timed` writes an **open** row at start and a heartbeat every N minutes, and closes it at the end.
  - `spent_before` counts an open row up to its last heartbeat.
  - Today 398 machine-min (ep21 +166) are invisible, so a P90 guarantee cannot be checked, let alone enforced.
- **Not code-preventable:**
  - fail:refused, which is a new bug each time;
  - the redo after code moved (357 min), since a fix that changes a step's inputs must redo it.
- **The lever on these two is upstream:** run a fix on the replay set before it reaches a live episode, which is what the cycles now do. "One episode, one commit" is already house law: drive.py warns and does not refuse. ep21 ran on 22 SHAs.

### 1.5 What does NOT pay

- **LLM retry.** All 6 provider failures over ep19-27 were deterministic. Grammar too large, `finish_reason=length` at the 4k default, and reasoning mandatory all fail identically on a resend. 41 min in total.
- **A QC memo on the master, at any granularity.** `audio_chunks.py`:
  - every recut re-levels the whole mix (`master_loudness.into_band`), so 0 of 41-57 chunks stay bit-identical between iterations (ep19, ep21, ep24, ep27);
  - the only hits are where no recut happened (ep20 iter2/3, ep22 39/46 chunks, ep26 iter3).
  - A memo keyed on the mix's inputs (line stem sha + bed span + gain) would hit, but it measures something other than the shipped bytes. That is a hypothesis and not replay-safe.

---

## 2. The plan ladder after fresh_brief

### 2.1 Per-rung minutes and outcomes (`rungs.py`, 329 rung verdicts, ep12-27)

| rung | n | median min | P90 min | total min | fault count fell | battery-refused → battery-clean |
|---|---|---|---|---|---|---|
| improve #1 | 90 | 4.0 | 9.4 | 412 | 45/88 (51 %) | **3/64 (5 %)** |
| improve #2 | 88 | 3.9 | 7.9 | 391 | 28/81 (35 %) | 11/75 (15 %) |
| model_tier | 77 | 1.5 | 7.8 | 212 | 44/77 (57 %) | **23/67 (34 %)** |
| (fresh_brief, retired 314b168) | 78 | 6.2 | 11.9 | 570 | 12/77 | 0/61 |

**Climb mix over ep19-27:**
- Plan rung minutes (fresh_brief excluded) were **95 % battery climbs**: 454 of 479 min. Every one of them ended in `keep_best` → **defer**.
- Critic climbs, where a terminal ships `keep_best` flagged, were 25 min.
- **Consequence for any budget:** a plan time cap's terminal is a deferral, and that **parks** the series. A cap cannot bound the plan stage without an owner ruling (§3.3).

### 2.2 Where a rung's minutes go

- **The writer.** `episode_writer` is tier `local`; it writes in parts, sequentially, because each part sees `so_far`. The DB `usage` gaps between consecutive writer calls are median **82 s**, P90 **296 s**, at about 114 tok/s, with output median 6-8k tokens a call and P90 16-33k.
- **The battery.** `plan_check` shell runs about 15 s, plus at most 2 mechanical rounds of about 15 s each.
- **The critic.** `plan_reader.read` runs **K = 3 sequential** workhorse reads, only on a battery-clean draft. The median span from first to last is **27 s** (33 critics, 2,100 output tokens a read). The critic already caches per plan sha inside one `Desk`.

### 2.3 Cheaper rungs, sorted by replay safety

| proposal | replay-safe? | minutes per episode | verdict |
|---|---|---|---|
| **T1 (above): persist `best`.** A killed or crashed climb resumes from its best draft. | **Yes.** Identical drafts and verdicts; only crash survival changes. | 0 median, **−64 to −125 on P90 episodes** | **Build** |
| Parallel critic reads (`ThreadPoolExecutor` over K = 3) | Yes. Independent samples of the same prompt; the verdict is a union over readings. | about −0.3 (≈ 18 s × 1-2 critics) | Not worth a commit |
| Critic cache across runs (`plan_verdict` keyed on plan sha8 + the critic's code sha, written to disk) | Yes, with the code sha in the key (LESSONS A75) | < 1 (a critic is ≈ 30-40 s; it hits only on a relaunch with an unchanged plan) | Not worth a commit. The five-hour plan's "critic cache" P1 is **measured worthless** today. |
| A smaller tier for improve | **No:** the drafts change | unknown | Hypothesis. Replay on the 48 real climbs under every gate. |
| Patch-mode improve (the writer returns only the shots named in the refusals, merged by code) | **No:** the drafts change | Output 6-8k → about 1-2k tokens, so perhaps −2 to −3 min a rung, −10 to −30 on P90 episodes | Hypothesis, 60 %. Needs a replay of the 48 climbs: equal-or-better battery outcomes on 95 % of them, and the kept draft passing every gate. |
| Battery climbs go model_tier first (the 34 % rung before the 5 % one) | **No** | perhaps −4 to −8 per battery climb | Hypothesis, 50 %. The rates are sequence-confounded: model_tier comes after two rungs of merged refusals, and `escalate()` already hands every battery rung to the canon caller. Replay before any routing. |
| C2's H1 (narrow fault-set memory) and H2 (cure-rate router) | No | C2: −10 to −20 (H2) | Unchanged, still a replay first. Only H2 attacks the battery climbs that dominate the minutes. |

**Section verdict:**
- The plan's P90 is not set by how expensive a rung is. It is set by **(a)** climbs killed mid-way (T1 fixes this) and **(b)** battery climbs that end in deferral and get re-climbed across relaunches (H2, a hypothesis).
- No critic-side change is worth building.

---

## 3. A hard ceiling: what exists, what it does, and what a P90 guarantee needs

### 3.1 What exists

The "one clock" is `studio/run_budget.py` + `studio/episode_run.py:64` (`Budget.charge(spent_before(home))`), from the 2026-09-30 five-hour build, fix 1.

- **`EPISODE_CEILING_SECONDS = 5 * 3600`**, below the owner's 6 h. Shares are given per step out of 300 minutes, unused time rolls forward, and overruns are absorbed by the ceiling.
- **At the ceiling, inside a run:**
  - `judged_gate.affordable` → `terminal`: GPU ladders sign keep_best/flagged in the same run.
  - `take_ladder.can_afford` → no rung.
- **Between runs:**
  - `drive.py` will not resume once `spent_before ≥ ceiling`;
  - `studio/autopilot.derive` parks `clock_spent`;
  - this fired as `over_budget` parks on ep19, ep20, ep21 and ep22.

### 3.2 Why it does not guarantee anything (95 %, code plus events)

1. **The clock does not see killed steps.** `timing.jsonl` rows are written when the `timed` context exits. 398 machine-min over ep19-27 are missing.
2. **`autopilot retry` calls `run_budget.reset_clock`** (`scripts/episode/autopilot.py:818`, dce4aa7, "a retry starts the episode's clock over"). All 4 over_budget parks were retried, and every retry handed the episode a fresh 5 h. ep21's clock restarted at 10-08 02:34 local after about 6 h had already been spent.
3. **Plan rungs cost 0 s** (`Rung(IMPROVE, 0.0)`): "every rung costs no GPU second, so the budget never refuses one". The plan share is **8 min**; the measured plan step is **P50 64 min, P90 171**.
4. **Shares are far off the measure** (`stage_p90.py`). They do not bind (unused time rolls, the ceiling absorbs overruns), but the plan, edit and QC shares are fiction:

| step | measured P50 | measured P90 (all runs, ep19-27) | current share (of 300) |
|---|---|---|---|
| 02 plan | 64 | 171 (≈ 125 without fresh_brief) | **8** |
| 04 lines | 12 | 28 | 6 |
| 07 grids | 22 | 55 | **4** |
| 08 panels | 20 | 36 | 60 |
| 09 takes | 118 | 166 (≈ 130 with CK8 narration) | 120 |
| 10 edit | 7 | 16 | 8 |
| 11 qc + master eye | 31 | 69 | **8** |

### 3.3 What a P90 guarantee requires

- **Fix the clock first (T3), then stop resetting it.**
  - A retry may reset a *ladder's* rounds (A55-A57), but the 6 h metric needs one clock per episode, from first launch to public.
  - `reset_clock` should stamp an attempt boundary for the audit, not zero the ceiling.
  - **This one is the owner's ruling:** a retry after a code fix would then go straight to terminals, with fewer rescue rungs on that episode.
- **A lower internal budget per stage does not buy P90 by itself.**
  - The relaunch-free floor is **P90 4.85 h with the plan stage untouched**. Every overrun episode is over because of waste the clock cannot see or resets away, not because one stage overspends.
  - The budget that matters is the **whole-episode ceiling, honestly counted**.
- **Proposed shares.** These are 300 min under the existing 5 h internal ceiling. The 60 min between that and the owner's 6 h is the margin for what the clock does not cover: publish polling and judge reads outside steps. They are priced on measured relaunch-free values: ep25 (the only clean run) and the per-step medians, adjusted for CK8 narration and no fresh_brief.

| step | proposed share (min of 300) | basis |
|---|---|---|
| 01 bind | 1 | 0.0 measured |
| 02 plan | **70** | P50 45-64 after fresh_brief; ep25 64 |
| 03 places | 5 | P90 6 |
| 04 lines | 15 | P50 12 |
| 05 + 06 | 2 | 0.1 |
| 07 grids | 22 | P50 22 |
| 08 panels | 22 | P50 20, P90 36 |
| 09 takes | 105 | P50 118 × (1 − 0.17 CK8) ≈ 98; ep25 93 |
| 10 edit | 6 | P50 7 |
| 11 QC + master eye | 20 | in-run QC 7-12 + one master retake |
| 12 + 13 | 6 | |
| judges | 6 | the cap stays |
| ladders pool | 20 | the take retake ladder |
| **sum** | **300** | |

- **Price the plan rungs at their measured median** (improve 240 s, model_tier 90 s) so the plan ladder draws on the clock like every other ladder.
  - At a spent clock, critic climbs keep_best: they ship flagged, as today.
  - **Battery climbs defer, and a deferral parks the episode.**
  - Over ep19-27, 4 of 9 episodes (ep19, ep21, ep22, ep26) spent more than 90 min in the plan after fresh_brief. A 70-min plan share plus headroom would not have parked them, because headroom pays. A spent 5 h clock would have.
  - **Owner ruling needed:** when the whole clock is spent while the plan battery still refuses, does the episode park (6 h guaranteed, the series stops on it) or does it climb on past 6 h (no guarantee)? A P90 guarantee requires "park".

---

## 4. Ranked fixes

Minutes are per episode, **on P90 episodes**. P90 is projected on the honest series (C2 as built + unlogged), ep19-27 (`projection_c3.py`).

| # | fix | kind | saves (P90 episodes) | P90 after | confidence |
|---|---|---|---|---|---|
| 0 | **T3: an honest clock** (open row + heartbeat; `spent_before` counts it) | code, test first | 0. It makes 7.55 h visible instead of 6.92 h. | 7.55 h (truth) | 95 % |
| 1 | **T1: plan checkpoint** (`plan.best.json` on every `remember()`, resumed from on the next run) | code, replay-safe, test first | −64 to −125 min (ep21, ep22, ep26) | 7.14 h | 95 % issue; minutes are an upper bound (assumes the climb resumes, losing ≤ 1 rung) |
| 2 | **T2: QC fail-fast** (cheap hard rows before Whisper) | code, replay-safe, test first | −20 to −30 (ep20, ep21, ep24) | 6.79 h | 95 % issue, 85 % saving (the cheap-row share comes from commit text) |
| 3 | **T1b: stop at a boundary** (`pause --at-boundary`; the runner exits between steps and rungs) | [arch], the runner's stop path | −15 to −53 per occurrence (ep21 r17, ep23) and the reason for the 22 kills | — | 90 % |
| 4 | **No mid-episode commits, enforced** (drive.py refuses a resume on a moved SHA unless `--fix-lands`, and the autopilot logs the cost) | code (a refusal) + house law | The rest of the waste: the floor | **4.85 h, 0/9** (all waste removed) | 95 % that the floor is under 6 h. How much discipline recovers is a behaviour, not a measure. |
| 5 | **Retry does not reset the 6 h clock** | owner ruling | needed for any guarantee | — | ruling |
| 6 | **Plan rungs priced; at a spent clock a battery climb parks** | owner ruling + code | bounds the plan | — | ruling |
| 7 | H2 cure router / patch-mode improve / model_tier-first | replay first | −10 to −30 hypothesised | — | 50-80 %, not built |

**Without the owner's rulings (#5, #6):**
- Code alone (#0-#2) takes the honest P90 from 7.55 to about **6.8 h**.
- The rest of the tail is mid-episode fixing: **ep21 alone carries 243 min of session kills**.

**The guarantee needs:**
- #4 (discipline, now with a refusal behind it);
- #5;
- #6.

## 5. Not measured or open

- **Scarlet.** Only ep10-14 `timing.jsonl` exists (182-309 min, hand-run in September, the plan not yet clocked). There are no drive or DB records, so it is excluded from every minute above.
- **QC sub-check split.** `timing.jsonl` has no split inside qc.py. The ≈ 8 s ffmpeg figure was measured on one master (ep27) on the CPU. The Whisper share is inferred from the remainder of 7-12 min.
- **Redo after code moved, 357 min.** How much of it was a spurious `done()` invalidation, and how much was a fix that genuinely changed inputs, is not separable from the records.

**Publishable (flag).** "The clock you budget against is not the clock you spend": on 9 consecutive unattended episodes of an agentic media pipeline, 11 % of machine time (398 of 3,499 min) sat in killed steps the step clock never logged. The P90 tail was 100 % relaunch waste, not compute. This is a general result for resumable agent pipelines and fits a short workshop paper with the C2 "most ladder time comes after the final answer" finding.
