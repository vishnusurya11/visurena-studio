# Orchestration and parallel scheduling

**Date:** 2026-10-22 (Seattle time)

**Abstract:** Where does an episode's machine time go, and should two episodes share the one graphics card at once? The card is the bottleneck. Step order inside one episode saves almost nothing. Two episodes sharing the card stayed "no" under the registered rule, and the decision is now a risk call for the owner.

> **Publication note.** The three `h3_*` strips in `images/` contain frames from MiniMax-H3 video. They are held from publication under the archive's MiniMax-H3 note. The other two images in this folder hold no H3 frames.

## The question

The studio makes one short episode at a time on one local GPU. A clean episode is meant to fit in a six-hour machine budget. Two questions followed:

1. Where does the time go, step by step?
2. Should two episodes run interleaved on the one card, so that one episode's text and checks run while the other draws pictures?

## What existed before

- **A staged pipeline.** Each episode runs about twelve steps. Some use the GPU (image grids, video takes, speech), some use a CPU lane (content checks, assembly), and some call a cloud model (planning).
- **A busy-time rule that was too loose.** The GPU ledger counted the card as busy when utilisation was 5% or more. Low-utilisation time from other GPU workers was counted as busy, and idle time was counted as busy too.
- **Repeat checks.** A check on a take compared file modification times. Copy-and-restore of unchanged bytes forced a full re-measure.
- **Non-atomic JSON writes.** Most JSON files were written in place. A kill in the middle left an unreadable file.
- **Queue identity.** Queue entries were named by a shared filename prefix. Two episodes could match each other's job after a timeout.
- **Missing timing rows.** Take renders and voice reads wrote no timing row, so some totals were negative.

The first-delivery timing from the ruling (measured from stage timing rows, not from the benches) showed where the minutes went:

| Step | Minutes | Runs on |
|---|---|---|
| Plan | 39.6 | Cloud model |
| Places | 11.0 | GPU |
| Lines | 23.1 | GPU speech plus CPU listening |
| Grids | 19.5 | GPU image model |
| Panel checks | 55.6 | GPU vision model |
| Takes (row only) | 58.7 | GPU |
| Take checks (content) | 84.5 | CPU lane |
| Take content and eye checks | 21.6 and 8.9 | Vision model and API |
| Assemble and upscale | 4.8 and 2.6 | CPU and GPU |
| QC and master eye | 8.8 and 6.4 | CPU and vision model |
| Gaps between 13 runs | 128.8 | Nothing |

The skeptic later re-measured the idle time from raw samples. Counting claimed-but-slow time separately, the card was truly idle 35% of the time in repair runs, not 54%. The rest was claimed by a worker running at low utilisation.

## Method

- **Expert panel.** Ten expert agents (nine lenses and one skeptic) argued over two rounds.
- **Gavel.** An Opus agent read both rounds, ran its own re-checks, and wrote the ruling. It adopted fixes that were defects, and it sent speed claims to benches.
- **Pre-registered benches.** Pass rules were fixed before the first GPU job. A replay ran on measured timing rows. Where a split was not measured, it was marked as an estimate. The benches changed how two tests were run after some results were already in. The pass rules themselves did not change.
- **Budget.** A 40-minute GPU cap and $0 spend.
- **Skeptic.** An Opus skeptic recomputed the numbers from raw files and attacked the ruling. Its findings are below.
- **Builder.** An Opus builder landed the defect fixes, each with a failing test first.

## Results

Every number below comes from the bench record (BENCH.md) unless marked "skeptic" or "ruling".

### GPU use

Total: 2,477 s, which is 41.3 minutes, against a 40-minute cap. The run went 1.3 minutes over. G1 used 2,054 s. G2 used 423 s and stopped after one B repeat, when the cap guard fired. Its last grid started under the guard and ran to the end. G3 was not run.

### G1: card and CPU lane (GPU)

| Bench | Verdict | Key numbers |
|---|---|---|
| G1-A baseline | Not applicable | 8 video takes, median 35.9 s (first take after vision block 51.9 s, cold video model) |
| G1-B vision reads between takes | **Fail** (one clause) | Median take 37.5 s vs A 35.9 s (+1.6 s). Vision text matched solo 18 of 18. The first read after each take took 108 to 116 s (6 of 6), against 12.8 s warm and 21 s solo cold. Only 2.2 GB of VRAM was free before that read (22.3 GB held). Cost about 600 s over six blocks. |
| G1-C six-worker CPU lane | **Fail** on the render side | Median take 41.2 s vs A 35.9 s (+14.8%, rule +5%). One take took 278.9 s. Lane side passed: lane-alone wall 403 s vs 1,727 s serial = 0.23 (rule at most 1/3). 28 of 28 check outputs matched the serial run's canonical hash. |
| G1 busy rule | **Pass** | 99.3% correct on 2,623 one-second samples (591 truly idle). False-busy on idle 2.7%. Old rule (util 5 or more) 95.3% correct, false-busy 9.1%. Best other cut-off 99.4%, under the 2-point bar. |
| G1 attribution | Closed | Utilisation under 20% was 8.3% of warm take wall: load 7 s, tail 9 s, middle 5 s. Tail 3.6% of wall (rule under 10%). |
| G1 determinism | Dropped | Same seed gave different file and frame hashes for all 4 seeds. No byte comparison. |

### G2: Qwen-Image swap penalty (GPU)

| Measure | Value |
|---|---|
| Warm grids (A) | 13.2 s median (12.8, 13.2, 15.7) |
| Cold first grid | 174.7 s |
| Grid after one video take (B) | 167.5 s |
| Penalty P | 153 s (n = 1, capped) |
| Rule: P at most 30 s for interleave | Failed. Interleave stays "no". |
| Rule: P above 60 s, so the Q3 request goes out with 153 s | Applied |

The five same-seed grids produced five different images, because prompt padding changed the output. No image-identity claim is made.

### B1: step order inside one episode (CPU)

| Measure | Value |
|---|---|
| Card-idle saved per episode | Median 0.1 min, maximum 0.2 min |
| Rule | At least 10 min saved, with 0 gate-order changes |
| Result | **Fail** |
| Gate-order changes | 4 read-before-producer events if a CPU step starts early |

Step order is worth about zero. The skeptic notes the 4 events are typed strings, not observed events. That does not change the conclusion.

### B2: two episodes, serial vs prefetch vs interleave (mechanism, CPU)

| Measure | Result |
|---|---|
| Shared refs file | Red on today's code. The bind step rewrites a shared refs file, so episode N+1 overwrites episode N's chapter. |
| Readers that refuse | 4 (render and retake, content check, panel check, grids) |
| Orderings tested | One check, counted 20 times (skeptic: not 20 independent draws) |

The fix is a per-unit refs file. That fix is a prerequisite for any overlap.

### B3: content-key cache replay on the take check (CPU)

Measured on 28 episode 1 takes. Cold run: 1,727 s in one process, about 62 s per take.

| Mutation | A (today) | B (key prototype) | Right answer |
|---|---|---|---|
| M0 no change | 0 | 0 | 0 |
| M1 touch | 0 | 0 | 0 |
| M2 copy and restore | 0 | 0 | 0 |
| M3 one byte in one take | 1 | 1 | 1 |
| M4 one prompt word | 0 | 0 | 0 |
| M4b one motion word in the plan | **0 (false hit, stale)** | 1 | 1 |
| M5 edit a measuring module | 0 (stale by design) | 28 (coarse) | Per-check digest would re-run only what reads it |
| M6 one pixel in a reference sheet | 14 | 14 | 14 |

Result: unchanged re-entry already costs zero re-measures, so the claimed saving is zero. The case for a key change rests on the stale hits (M4b and M5). The 1-in-10 audit agreed on 28 of 28 cold re-runs. Steps 06 to 08 were not replayed.

### R1: policy replay on the measured table (CPU)

Nine episodes, all 72 ordered pairs, both ready at time zero. Serial was 331 minutes per episode (4.35 per day, card busy 52%). The base split is an estimate.

| Policy | Split | Per-episode wall gain, median (P10) | Pairs at 7% or more / 15% or more | Episode N finish change, median / P90 | P90 latency change, both |
|---|---|---|---|---|---|
| P: prefetch | Base | 9.6% (5.4) | 68% / 29% | 0 / 0 | 0 |
| PF: prefetch plus family windows | Base | 15.5% (11.3) | 100% / 54% | +6.4% / +21.1% | +14.0% |
| I: interleave | Base | 17.8% (11.9) | 100% / 72% | +10.4% / +24.1% | +20.2% |
| I: interleave | Heavy card share | 14.7% (10.0) | 100% / 47% | +8.3% / +34.6% | +19.4% |
| I: interleave | Light card share | 21.2% (14.1) | 100% / 83% | +6.2% / +21.6% | +11.5% |

Series totals per episode (base split): serial 331 min (4.35 per day), prefetch 256 min (5.63 per day, +22.8%), prefetch plus family windows 225 min (6.39 per day, +32%), interleave 212 min (6.81 per day, +36%). The skeptic notes these series gains include idle that repairs and parks leave inside the measured step unions. They are inflated.

- Prefetch rule (wall at most 0.93 of serial, episode N latency within 1%): met at the median and in 68% of pairs. The mechanism is still red until the refs fix.
- Interleave rule (gain at least 15%, P90 latency rise at most 25%): met on the base and light splits. **Missed on the heavy split**, where episode N's P90 rose 34.6%. Not robust to the unmeasured split.
- The swap penalty barely moves the interleave gain (0.3 points between 0 s and 141 s). The card share decides the outcome, and nothing measured it.

### R3: plan drift for prefetch (records only)

| Measure | Value |
|---|---|
| Adjacent pairs with timing rows on both sides | 13 (39 pairs in total) |
| Pairs with a plan-path change between episode N's step 09 start and episode N+1's step 02 start | 5 of 9 (55.6%) |
| Rule | At most 10% |
| Result | **Fail** |

Four pairs had episode N+1 planned before episode N's step 09 started. Twenty-six pairs had no timing rows. The skeptic re-priced the prefetch gain: 9.6% times (1 minus 0.556) = about 4.3%. That is under the 7% bar. The windows are inflated by parks, so a clean-run rate may be lower. That is a new bench, not a pass.

### R4: repair inputs for the six-hour question (CPU)

| Measure | Value |
|---|---|
| Repair rounds per episode | Mean 3.16, median 2. 20 of 25 episodes had at least one. After the batched ladder (14 episodes): mean 2.6. Model assumed 1.2. |
| Re-render of a round | Median 689 s (n = 79) |
| Re-check after a round | Median 311 s, mean 514 s. Model assumed 39 min. |
| Monte Carlo, uncached, all 25 episodes | 10.8% over 6 h |
| Monte Carlo, cached re-check (60 s, estimate), all 25 | 7.2% |
| Post-ladder 14 episodes, uncached / cached | 4.7% / 1.5% |

Rule: the claim is withdrawn if either figure moves more than 3 points from 9.9% and 0.1%. The cached 0.1% figure moved, so **it is withdrawn** and refit to 1.5 to 7.2%. The owner decides the budget question.

### R5: exit-to-start gaps for the autopilot (CPU)

| Measure | Value |
|---|---|
| Clean pause at a step boundary (n = 5) | Median 237 s (range 53 to 1,170 s) |
| Refused starts (n = 6) | Median 435 s (range 119 to 630 s) |
| Failed starts (n = 2) | Median 296 s |
| Escalated starts (n = 3) | 7 to 20 hours (parks) |
| Non-escalated gaps (13) | Sum 86.8 min |
| Starts on a five-minute mark | 9 of 21 (43%) |
| Sandbox exit-chained relaunch (1, 1, 6, 3 s) | Replay median under 30 s |

Rule: the clean-exit gap is above 60 s today (yes), and under 30 s in replay (yes). The skeptic notes that the 87-minute figure is overstated. Refusals and failures do not go away with an earlier relaunch. The tick can explain about 17 minutes at most.

### I1: torn write (CPU stress loop)

| Measure | Plain write (A) | Temp file, flush, replace (B) |
|---|---|---|
| Kills | 1,000 | 1,000 |
| Unreadable file after kill | 548 of 1,000 | 0 of 1,000 |
| Exactly old or exactly new content | Not all | 1,000 of 1,000 |

The skeptic calls the 548 figure a stress-test rate. Production writes less often. The mechanism is real. The reader-contention case (a reader holding the file open while the replace runs) was not tested, and the cost of flush on the spinning disk was not measured.

## Verdict

1. **The card is the drum.** A clean episode needs about 192 to 197 minutes of card work. That is an estimate from the cost model, not a measurement.
2. **Step order is worth about 0.1 minutes per episode.** Not worth building.
3. **Two episodes on the card: "no" under the registered rule.** The Qwen reload penalty failed the 30-second rule. Interleave passed the 15% bar on two of three splits and missed on the heavy split. The owner's decision is a risk call.
4. **Plan prefetch fails as registered.** Plans changed in 5 of 9 pairs (rule 10% or less). Re-priced, the gain is about 4%.
5. **No adopted item is a measured speed saving.** The fixes correct measurements and defects. The big "re-check unchanged bytes" saving had already been fixed on 2026-10-20. What remains is a stale-pass correctness bug (M4b), not a speed problem.
6. **Vision reads between video takes stay untested, not failed.** The bench ran without the free-memory step that production uses. The skeptic calls the result void for production. Production's free step costs about 0 to 5 s, which the skeptic cites from the cost notes. The 95-second figure is inferred, not measured.

## What was wired

Commit subjects, in plain words:

| Commit | Plain-words change |
|---|---|
| f334fda | The GPU ledger counts the card as busy when a queue job runs or utilisation is 30% or more. Unsampled time gets its own bucket. The report is advisory, not a gate. |
| 770546e | JSON writes go to a temp file and then replace the old file. Retries four times, then writes in place. |
| cd814ef | A timed-out submit finds its own job by prompt ID, not by a shared filename prefix. |
| 632fe63 | A take is fresh when its bytes match, not when its modification time matches. Old verdicts keep the old test. |
| 983dcc0 | A lint fix: the take writer check now treats the atomic JSON replace as a JSON writer. |
| 0b858aa | Every take render and every voice-check call writes one timing row. |

Test result: nine touched test files gave 64 passed and 2 expected failures. The full suite gave 8 failures. Six came from other agents' uncommitted files, and two passed when re-run alone.

**Not wired:** conversion of the other 121 raw JSON writers (held until the reader test and disk-cost measurement are done), the kill-matrix harness, the declared-inputs lint, the decision file (kept as a proposal), and the stale-pass fix for the motion word (needs a red test first).

## Limits and open questions

- **Measurement gaps.** Per-node timing was not captured, so the mux-to-CPU question rests on position as a proxy. The take-level card and CPU split is an estimate.
- **Not replayed.** Steps 06 to 08 and the vision take check could not be replayed. The bench tool refuses while the real autopilot task is enabled, and the bench did not work around that.
- **Single runs.** G2 is n = 1, on a disk that other groups were using. The Qwen penalty is quoted as about 150 to 175 s.
- **Estimates.** The card-work figures (192 to 197 min, 223.5 min, 237 min) come from a cost simulation that uses typed estimates. Re-running reproduces the arithmetic, not a measurement.
- **The busy rule was tested on a narrow case.** Its ground truth is the queue itself. The case that matters, a non-ComfyUI GPU worker, was not in the test. The skeptic recommends keeping the claimed-but-slow bucket as its own line.
- **The vision-read cost is untested under production.** The owner decides whether a free step is worth its cost.
- **Open decisions for the owner:**
  - Q1: interleave two episodes on the card? (Registered rule says no. The data does not settle it.)
  - Q2: should the six-hour clock charge only card-held time? Needed for prefetch to count.
  - Q3: move the Qwen-Image weights to the fast system drive? Saves about 141 s per reload.
  - Q4: relaunch the autopilot on exit instead of the five-minute tick?
  - Q5: replace per-phase caps with a buffer rule? Not yet.
  - Q6: use a cloud model as a parallel vision judge? Not wired.
  - Go or no-go on the stale-pass fix.
  - A window with the autopilot off, for the replays that need it.

## Images

Five strip images from the bench record, in `images/`:

| File | What it shows | Held? |
|---|---|---|
| `images/00_SUMMARY.png` | Summary table of all benches | No |
| `images/h3_take0_A_vs_B.png` | Video take 0, production vs candidate B | **Yes** (MiniMax-H3 frames) |
| `images/h3_take0_A_vs_C.png` | Video take 0, production vs candidate C | **Yes** (MiniMax-H3 frames) |
| `images/h3_take3_A_vs_B.png` | Video take 3, production vs candidate B | **Yes** (MiniMax-H3 frames) |
| `images/qwen_grid_A_vs_B.png` | Image grid, production vs candidate B | No |

No audio was benched in this group.

## Sources

Public documentation cited in the expert reports:

- Bazel remote caching: https://bazel.build/remote/caching , https://bazel.build/remote/caching.md , https://bazel.googlesource.com/bazel/+/HEAD/docs/remote/caching.mdx
- Bazel hermeticity: https://bazel.build/basics/hermeticity
- Bazel remote caching explainers: https://blog.buildbuddy.io/blog/bazels-remote-caching-and-remote-execution-explained , https://blog.engflow.com/2024/05/13/the-many-caches-of-bazel/ , https://blogsystem5.substack.com/p/bazel-remote-caching , https://jmmv.dev/2025/09/bazel-remote-caching.html , https://www.buildbuddy.io/blog/bazels-remote-caching-and-remote-execution-explained/
- Nix content-addressed derivations: https://nix.dev/manual/nix/2.24/store/store-object/content-address , https://tweag.io/blog/2020-09-10-nix-cas/ , https://tweag.io/blog/2021-12-02-nix-cas-4 , https://wiki.nixos.org/wiki/Ca-derivations , https://fzakaria.com/2025/03/08/demystifying-nix-s-intensional-model
- Ray data pipelines: https://anyscale.com/blog/architecting-multimodal-data-pipelines-that-scale-with-ray
- AWS Deadline Cloud job limits: https://docs.aws.amazon.com/deadline-cloud/latest/developerguide/build-job-limits.html
- Thinkbox Deadline (job scheduling, pools, overview): https://docs.thinkboxsoftware.com/products/deadline/10.1/1_User%20Manual/manual/overview.html , https://docs.thinkboxsoftware.com/products/deadline/10.2/1_User%20Manual/manual/overview.html , https://docs.thinkboxsoftware.com/products/deadline/10.3/1_User%20Manual/manual/job-scheduling.html , https://docs.thinkboxsoftware.com/products/deadline/10.3/1_User%20Manual/manual/pools-and-groups.html , https://docs.thinkboxsoftware.com/products/deadline/10.4/1_User%20Manual/manual/index-admin-features.html , https://docs.thinkboxsoftware.com/products/deadline/10.4/1_User%20Manual/manual/job-scheduling.html
- Pixar RenderMan wiki: https://rmanwiki.pixar.com/display/TRA , https://rmanwiki.pixar.com/x/jJYZAw
- Critical chain project management: https://en.wikipedia.org/wiki/Critical_chain_project_management , https://meisterplan.com/blog/critical-chain-project-management/ , https://umbrex.com/resources/frameworks/project-management-frameworks/critical-chain-project-management-ccpm/ , https://success.sciforma.com/en/node/50080 , https://www.toc-goldratt.com/en/product/a-critical-chain-project-management-primer-chapter-3-of-the-theory-of-constraints-handbook , https://www.fabrico.io/blog/drum-buffer-rope/ , https://www.pmi.org/learning/library/drum-buffer-rope-critical-chain-buffering-8526 , https://www.pmi.org/learning/library/merits-pitfalls-critical-chain-scheduling-1102 , https://www.pmi.org/learning/library/resource-buffer-management-critical-chain-scheduling-8027
- Double buffering: https://inferencex.semianalysis.com/glossary/double-buffering
- Academic index entry on scheduling: https://ideas.repec.org/a/plo/pone00/0336350.html
- Windows file-move API: https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefileexw
- ComfyUI (project, server, API, queue, memory):
  - https://github.com/comfyanonymous/ComfyUI
  - https://github.com/Comfy-Org/ComfyUI/discussions/3683
  - https://github.com/Comfy-Org/ComfyUI/discussions/6659
  - https://docs.comfy.org/api-reference/cloud/workflow/submit-a-workflow-for-execution
  - https://docs.comfy.org/development/comfyui-server/comms_routes
  - https://www.mintlify.com/Comfy-Org/ComfyUI/api/prompt
  - https://mintlify.com/Comfy-Org/ComfyUI/advanced/memory-management
  - https://theneuralbase.com/comfyui/learn/advanced/queue-management/
  - https://theneuralbase.com/comfyui/learn/intermediate/queue-and-iterate/
  - https://dev.to/abdollah_ebadi_cbec8f6471/running-multiple-comfyui-instances-in-parallel-on-a-single-gpu-what-actually-breaks-first-4n04

Pages cited by name only in the expert reports, with no URL, are not listed.
