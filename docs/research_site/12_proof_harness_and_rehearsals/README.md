# Proof harness and rehearsals: what the ep02 proof could and could not measure

*Source date: 2026-10-21 (proof run 09:42 to 22:34 PDT). A recorded-engine rehearsal harness was built to answer eight questions about the second episode of Jekyll and Hyde before any paid or GPU time was spent. No question has earned a pass rate yet.*

## The question

Could the studio prove, before it renders episode 2 of Jekyll and Hyde, that the pipeline will (a) make faces better than the first master of episode 1, (b) finish in under 6 hours of machine time, and (c) reach an upload-ready state without a human touching it?

The studio owner decided that confidence had to come from a test framework built first, not from an agent's opinion. So the question was not only whether the pipeline works, but whether the studio could show that claim with counted evidence.

The eight questions, as the proof report names them:

| id | question |
|---|---|
| Q1 | Are faces better than episode 1's first master? |
| Q2 | Are faces as good as iteration 3, the first time? |
| Q3 | Do mid-size faces get drawn eyes? |
| Q4 | Do tiny faces look good? |
| Q5 | Does episode 2 finish machine work in under 6 hours? |
| Q6 | Does the episode go from start to upload-ready unattended? |
| Q7 | Is it finished the same day, with an operator? |
| Q8 | Are the story and staging better? |

## What existed before

- **Episode 1 of Jekyll and Hyde** (the first master) took 6.02 hours on the machine clock and 30.85 hours of wall time, including 4.7 hours of unlogged waiting. That is the only clocked baseline.
- **Earlier episodes** of War of the Worlds (episodes 20 to 27) and Scarlet had timing records, but several had no drive logs, so they could not be scored for failures.
- **No rehearsal existed.** Every earlier check either ran the real pipeline on the real GPU or read files. Nothing could replay a full episode with the engine faked while the pipeline code ran unchanged.
- **Two earlier defects were found by the proof itself:** a ComfyUI restart that could launch a second engine (see the costs and crash section), and a publish rule that lets a judge-signed episode clear its own publish lock.

## Method

**The harness idea.** A rehearsal runs the real step code. Each point where the code would leave the machine (the ComfyUI HTTP socket, the Claude SDK transport, the face and speech worker processes) is answered from a recording. Every answer is labelled with how close the match was:

- `exact`: the same inputs as a recorded run.
- `substituted`: a recorded run of the same workflow and index, reused with its frames trimmed or looped.
- `canned`: no recording matched. The fake returns a deliberately refusing answer (for example, an unreadable picture or a blank frame).

**Fences.** An audit hook refuses any write under the real library, any SQLite connection to the real database, any process launch outside an allowlist, and any network call except to localhost. A stat guard checks the real library before and after each run. The scheduled job that runs the studio unattended was meant to be disabled during rehearsals. It was never disabled during this proof, so every scenario was refused by the fence (more in the limits section).

**Scoring rules, written before the runs.**
- A point counts toward a confidence number only if it is a distinct recovery path. Twenty fault positions that run the same recovery code count as one point.
- A row that depends on any `canned` or `substituted` answer is labelled `mechanism`. It shows the code path ran. It is never counted as quality.
- A row measured by an instrument that fails its own calibration contributes nothing.
- The confidence number is a count of passes over distinct points, printed with its Wilson 95 percent lower bound. A Wilson bound is a conservative range for a pass rate from a small sample: 2 of 4 gives a lower bound of 0.150, 26 of 30 gives about 0.70.

**Agents and debate rounds.** The design went through one architect pass, one adversarial skeptic pass (19 challenges, each re-read against the code and ruled on), and two later audit passes that re-ran every count. The proof itself ran as one main session with the owner's go for each window. The design document records that 19 skeptic changes were applied, applied with a change, or rebutted, with reasons.

**What was measured, and how.**
- The face path was replayed on episode 1's first-master takes. Each take's first-pass decisions were compared with the repair's decisions.
- Panel face size (on the storyboard panels) was compared with the face size of the rendered take, over 21 pairs.
- A time model was leave-one-out tested on nine episodes with full records.
- The ComfyUI engine was killed mid-job four times on the real GPU, and the restart path was timed.
- GPU job costs were measured on the real engine, one job at a time on an empty queue, with a warm run and a cold run where the cache allowed.
- Every gate added since 2026-10-14 was replayed on 42 delivered episodes to count false refusals.

## Results

### Pass table (final report, 17:27 PDT, HEAD 24f1f55)

| Q | status | distinct passing points | why |
|---|---|---|---|
| Q1 faces better than first master | REAL-RUN | 0 | the face eye instrument has 0 of the 30 owner labels it needs |
| Q2 as good as iteration 3 | REAL-RUN | 0 | same instrument gate |
| Q3 mid faces get drawn eyes | REAL-RUN | 0 | predictor of face tier failed (R squared 0.731, below the 0.8 bar) |
| Q4 tiny faces look good | REAL-RUN | 0 | no recording can answer it |
| Q5 under 6 hours | REAL-RUN | 2 of 9 (lower bound 0.063) | predictor failed; base rate 0 of 1 under 6 hours |
| Q6 unattended to upload-ready | FAILING | 0 | no scenario has run; 0 of 32 incident classes handled |
| Q7 same day, with an operator | REAL-RUN | 0 | only a real run can answer it |
| Q8 story and staging | REAL-RUN | 0 | the owner's judgement; compliance checks only |

The status words mean: **REAL-RUN** = no recording can answer it, a staged real run is needed; **FAILING** = a check failed with a counted number; **PARTIAL** = some evidence but not enough.

### How the confidence report changed

| report | date | Q3 | Q5 | Q6 |
|---|---|---|---|---|
| iteration 1 (CPU instruments only) | 09:51 | FAILING, 0 of 21 | FAILING, 2 of 4 (lower bound 0.150) | PARTIAL |
| iteration 11 (after the first harness fixes) | 14:26 | FAILING | FAILING | FAILING (blocked) |
| iteration 15 (final, GPU data folded in) | 17:27 | REAL-RUN | REAL-RUN, 2 of 9 (lower bound 0.063) | FAILING (blocked) |

Between iterations 1 and 15, the two predictor failures were reclassified. A failed predictor means the question cannot be answered from recordings. It does not mean the question failed. An independent audit said this was a category error in the first reports, and the reclassification followed it.

### Time model (leave-one-out, nine episodes)

| measure | value |
|---|---|
| episodes scored | 9 (episode 1 of Jekyll and Hyde, War of the Worlds 20 to 27) |
| within 15 percent of measured | 2 of 9 |
| pre-registered pass rule | 3 of 4 on a held-out set (the four-episode set failed at 2 of 4) |
| episode 1 timing-row total | 4.69 hours (machine clock: 6.02 hours) |
| step 02 (writer) mean error | 46.3 minutes |
| step 09 (takes) mean error | 26.0 minutes |

The model scores timing-row seconds, not the machine clock, so even a pass would not have predicted the 6-hour quantity directly. The projection for episode 2 is a P50 of about 5.98 hours with the uncovered clock and a P90 of about 11.4 hours. These are projections from a model that failed its own test. They are not a proof.

### GPU costs (RTX 4090, ComfyUI 0.41.2, measured)

| job | warm cost | load after a free |
|---|---|---|
| Krea2 character sheet | 6.6 s per sheet | 5.2 s |
| Qwen3-VL read | 9.6 s median (4.8 to 15.9 s) | 3.5 s |
| Qwen-Image grid, 1x1 (1024 px, 25 steps) | 12.7 s | 140.9 s (weights on the slower D: disk) |
| Qwen-Image grid, 2x2 (2048 px, 25 steps) | 69.7 s | same as 1x1 |
| H3 take, Wuli graph, 768 px | 9.9 s + 0.489 s per frame | 4.2 s |
| H3 take, Spark graph, 768 px | 14.8 s + 0.412 s per frame | about 0 s |
| H3 face refine | 11.0 s + 0.558 s per frame | about 0 s |
| av3 master upscale | 44.4 s per 1,000 frames, plus 28.3 s per pass | worker start about 20 s |

Two findings changed the time model. The face refine cost depends on frame count, not face size, and the code's old per-face figure underpriced short crops (41.8 s predicted against 55 to 57 s measured at 73 frames). And Qwen-Image reloads cost about 141 s every time the engine frees memory, so grouping jobs by model matters most for it. The fitted costs come from three references and silent audio. Production graphs use up to eight references and real audio, which were never measured, so the true cost is probably higher.

### Crash recovery (real engine, four kills)

| cycle | state when killed | engine answered after restart | first job done after restart | restart returned |
|---|---|---|---|---|
| 1 | cold, 187 s into a job | 775 s | 1,029 s | False, after 605 s |
| 2 | warm, 6 s into a job | 386 s | 556 s | True, after 387 s |
| 3 | warm, 6 s into a job | 333 s | 482 s | True, after 338 s |
| 4 | old rescue order, reading a stale process table | 784 s | 979 s | True, after 789 s, with 606 s blind wait and a second engine launched |

Each crash cost about 5.5 to 13 minutes of engine-down time, plus a cold model load of 2.5 to 3 minutes. The client correctly raised a loss error in every cycle and never hung. Cycle 4 showed two real defects in the restart code: it trusted a cached process list, and after a timed-out wait it launched a second engine without re-reading the list. Both were fixed in commit 04374b4 and then not re-measured on the real engine. Cycle 1 also showed that the 600-second ready limit was below the cold start of 775 seconds. The restart returned False while the engine was still starting, and the caller ignored the return value.

## Images

![Four warm Qwen-Image panels of the same character, 2048 by 2048 px, the output of the 2x2 grid cost run. Look at how the four cells hold one character across angles.](images/qwen_grid_2x2_warm.png)

The 2x2 grid is the most expensive storyboard job measured (69.7 seconds warm). Look at the four cells as one picture: the character keeps the same hat, coat and face across all four.

![One warm Qwen-Image 1x1 grid, 1024 by 1024 px, from the warm cost run. Look at how long it takes compared with the 2x2 grid.](images/qwen_grid_1x1_warm.png)

The single-cell version costs 12.7 seconds warm. The gap between this and the 2x2 image is the case for the cost model: cost scales with pixel count, not with the number of cells.

![The single-cell picture the engine returned after the fourth forced kill and restart. Look for a complete image: the job finished on the new engine.](images/crash_cycle4_grid.png)

After the fourth kill and restart, the engine finished the same job and returned a whole picture. That is the evidence that the job was resubmitted and completed, not lost.

![The single-cell picture the engine returned after the first forced kill and restart, on a cold engine. Look for the same completed output as cycle 4.](images/crash_cycle1_grid.png)

Cycle 1 is the cold-start case, where the restart returned False before the engine was up. The picture arrived anyway, about 170 seconds after the restart returned, which is why the false return did not stop the job.

## Verdict

**No question has an earned pass rate.** The harness is honest about this in its own status words. Q5 is the closest to a number, at 2 of 9 episodes, and its predictor failed its own pre-registered test.

What the proof did establish, with counts:

- On all 11 recorded face pastes, the paste step changed no pixel outside the face. This is one episode, so the lower bound is 0.74.
- The first-pass face decision matched the repair's decision on 8 of 12 takes (lower bound 0.39). On the real GPU it matched on 6 of 7 faces, but five of those seven renders were byte-identical replays of episode 1, so only two were new evidence.
- Panel face size matched the rendered face tier on 19 of 21 pairs (lower bound 0.71). The fit of the face size itself was not good enough to predict the size (R squared 0.731).
- Eight gates were false-refusal tested on delivered episodes. Five held with no unruled refusal. Five had refusals the owner had not yet ruled on, including a credit-line refusal that was a real false refusal and was fixed.
- Three production defects were found and fixed with failing tests first: a partial-accept engine response read as success, an av3 hang alarm that fired on every long pass, and a restart that could launch a duplicate engine.

## What changed in the pipeline

Commit subjects in the sources, in plain words:

- **Engine restart reads a fresh process list and re-reads it before launching.** Fixes the cycle 4 twin engine.
- **A partial engine accept is not success.** A reply with node errors is now treated as a failed submit, not a finished picture.
- **The av3 hang alarm re-arms while frames move.** Stops false stall traces on long master upscales.
- **The memo fill keeps its reading if a worker dies.** A dying reader keeps what it already read.
- **Canned worker and Claude answers count as mechanism, not quality.** A row that rests on an empty detection or a stand-in reply can no longer count as a pass.
- **Substituted takes count as mechanism too.** A row that reads a recorded take from a different episode is labelled as a stand-in.
- **Sweeps need every planned point.** A scenario with one sample no longer reaches PROVEN.
- **Preconditions count the unknown walk-on in the denominator.**
- **Episodes without drive records are marked absent, not zero incidents.**
- **The fence allows a no-op create of an existing folder.** It still refuses writes.
- **Tests no longer write into the real ComfyUI input or the real compute-routing log.** Found when a full test run left 180 picture files in the real input folder.
- **The rehearsal's mid-run checks scored two scenarios that had died at step 01 as passes.** Fixed so each scenario is scored on the outcome it registered in advance.

## Limits and open questions

- **No rehearsal has run its main path.** The scheduled job that runs the studio unattended was never disabled during the proof, so every scenario was refused by the fence. The first runs will test the harness before they test the pipeline. An independent audit flagged this as the largest risk.
- **The fake answers do not carry pixels.** Every picture gate in a rehearsal reads stand-ins. The harness labels those rows as mechanism, which is correct, so Q1 to Q4 and Q8 cannot be rehearsed.
- **The master upscale's real GPU path was never run in a rehearsal.** Every rehearsal used the CPU Lanczos path. The real path was costed separately.
- **Step 02 (the writer) is the largest timing miss.** Its mean error was 46 minutes. The writer's real output for chapter 2 does not exist until a real session runs.
- **Two loss cases were not covered.** A silent face-detect worker death switched the tracker to a weaker model for the rest of the episode without writing a row. A timing-related permission error appeared once in the live loop and its cause is unknown.
- **Four gate rulings are waiting on the owner:** a G-HOLE-SLACK refusal on seven delivered episodes, a G-CROWD-ORPHAN refusal on 19, an L28 refusal on 24, and a LAUNCH-DRY-CHECK refusal on 76. A gate that refuses delivered work may be a threshold calibrated on an earlier episode.
- **The publish rule is an open production question.** A judge-signed episode can clear its own publish lock. A rehearsal of a chapter with unresolved content refusals would count as a wrong upload-ready episode, which is the failing outcome the design pre-registered. The owner has to rule on whether a content refusal should block the auto-clear.
- **The GPU data is one machine on one day.** The costs and crash timings are from one RTX 4090 with the D: disk, not a range over hardware.
- **Still to do:** the staged real runs (SR-0 to SR-5) need the owner's go. These are the face labels, one real writer session for chapter 2, a sandbox run of episode 2 steps 01 to 08, and the first-pass refine on episode 1's takes.

## Sources

- DESIGN, iteration 2, after the skeptic (proof harness design, 2026-10-21)
- DESIGN_SKEPTIC (skeptic's challenges to the design, 2026-10-21)
- PROOF (what the harness measured, 2026-10-21 14:26)
- AUDIT (independent audit of the proof, 2026-10-21 14:45)
- PROOF_GPU (final run with the GPU data, 2026-10-21 15:27 to 17:30)
- TRIAGE window 1, window 2 and window 3 (rehearsal window triage, 2026-10-21)
- COSTS (measured GPU costs, 2026-10-21)
- CRASH (crash recovery on the real engine, 2026-10-21)
- CONFIDENCE iterations 1 to 15 (proof-backed confidence reports, 2026-10-21)
- TIME_BACKTEST iterations 1 to 8 (time-model back-tests, 2026-10-21)
