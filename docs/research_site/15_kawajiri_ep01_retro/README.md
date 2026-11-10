# One Episode, Sixteen Fixes: A Retrospective on the First Jekyll and Hyde Episode

*Source date: 2026-10-19 (the retro ran 2026-10-18 to 2026-10-19, Seattle time).*

*An overnight, fully local retrospective on one 3-minute AI-made episode. It found that the episode fit its quality bar but ran 6.02 hours against a 6-hour budget, then used about 50 investigation and build agents to trace the cause and fix it. The fixes are tested but the cap-fit claim is not yet proven on a real run.*

## The question

Could the studio produce a finished short episode from a book chapter with every production step inside its time cap, and if not, what broke, and what should change?

The first episode of the Jekyll and Hyde series (the Kawajiri noir style) was the test case. The studio has a rule of six machine-hours per episode of about 2 to 3 minutes. Each production step also has a cap, a maximum number of machine minutes. The question had two parts:

1. Did the episode meet the owner's quality bar, and what was wrong with it?
2. Why did the time run over, and which changes would bring the next episode inside the caps without lowering quality?

## What existed before

Before this retro the studio had a 16-step episode pipeline driven by an autopilot. Each step had a cap in `stages.yaml`. A "gate" is an automatic check that a step's output passes, such as a quality judge, a loudness check or a timing check. A "ledger" is the running record of minutes charged to each step.

The episode was the first of the new series. A previous deadline retro had already cut a 30-hour wall time to the 6-hour machine budget.

Ep01 was run under the autopilot. The autopilot ran steps in order, parked steps that failed a gate, and asked a "brain" (a judging agent) for decisions. Before the retro, the run had:

- 66 minutes against a 50-minute cap in the panel step (step 08).
- 16.6 minutes against a 15-minute cap in the places step (step 03).
- 117.8 minutes in the shoot step (step 09), with two "retake rounds" that rendered nothing.
- A hung video-finishing run (step 10) that the clock did not charge.

## Method

**Arms.** There was no controlled comparison. The single ep01 run was the baseline. The ledger held 11 to 13 runs on 9 code versions, mostly fixes pushed mid-run. The fixes were then replayed against the same ep01 records, at no GPU cost.

**Agents and rounds.** The retro used three phases of agents.

- **Phase A, investigation (36 reports).** The retro lead split the problem into 18 areas, such as plan, panels, voice, warp gate, autopilot and clock. Each area had one proposal agent that read the run's records and the code, and one skeptic agent that tried to refute the proposal against the same files. Each area therefore had one exchange. The files do not show a second round.
- **Phase B, build (16 packages).** The retro lead merged the 18 areas into a build plan. The plan gave each area a rank, a score and an owner. It set 16 work packages (P01 to P16), each with its own file list so that no two packages edited the same file. Builders ran in parallel. P16 alone wrote the docs. The source says "15 builders could run in parallel", which matches 15 code packages plus the docs package.
- **Phase C, close-out (9 builders).** Nine more builders took the open items from phase B. Each was checked by a skeptic.

The source files name 61 agent roles in total (36 + 16 + 9). They do not state one total, and they do not say how many skeptics reviewed phase B. The "about 50" figure is an estimate from those roles, not a number in the sources.

**Rules set before building.** The build plan set five "bricks", base rules that explain most of the 13 failures:

- B1: A round, climb or cap is spent only when it changed bytes.
- B2: A gate is only as true as the population it was fitted on.
- B3: One rule per fact, read by every channel.
- B4: A gate that counts cannot see shape.
- B5: A clock that is not charged when its process dies is not a clock.

The plan also recorded 22 decisions taken for the owner, each with its evidence and the alternative it overruled, so the owner could veto any of them. It also named 12 replay checks (R1 to R12) before any code was written. Each check said what must hold on a named ep01 record.

**What was measured, and how.** Minutes per step came from the run ledger (`clock.jsonl`), the timing file and the attempts file. Warp scores came from the take measurement files. The test suite was counted before and after each phase.

## Results

### The episode

| Measure | Result |
|---|---|
| Master file | Landed 2026-10-18, 22:54 Seattle time. 858 MB, 3,348 frames |
| QC (step 11) | Passed. -14.2 LUFS, -1.8 dBTP. 27 of 27 cuts exact. 22 of 22 lines heard |
| Upload | None. The publish gate was escalated, as the owner's rule requires |
| Charged machine time | 361.2 minutes = 6.02 hours (1.2 minutes over the 6-hour budget) |
| Wall time | 8.17 hours. About 129 minutes of dead gaps were not charged |
| Flagged takes shipped | 9 (T01 gait; T07, T10, T15, T16, T19, T20, T21, T24 warp) |

### Minutes per step, before and after

"Projected" is the replay with the fixes in place, assuming one clean run per step.

| Step | Actual (min) | Projected (min) | Cap (min) | Fits after fixes? |
|---|---|---|---|---|
| 01 bind | 0.5 | 0.5 | 2 | yes |
| 02 plan | 39.7 | 29.0 to 32.7 | 60 | yes |
| 03 places | 32.9 | 9.7 to 12.1 | 15 | yes, if the vision-model free step fires |
| 04 voice | 23.8 | 5.6 to 15.5 | 40 | yes, but the new lines wall is unproven |
| 05 timeline | 0.1 | 0.1 | 2 | yes |
| 06 prompts | 0.1 | 0.1 | 2 | yes |
| 07 board | 17.0 | 17.0 | 30 | yes |
| 08 panels | 66.1 | 42.8 | 50 | yes |
| 09 shoot | 119.5 | 124.1 | 242 | yes as a step, but two sub-caps stay over |
| 10 edit | 45.7 | 4.8 to 5.8 | 30 | yes (the actual figure includes a hung run) |
| 11 QC and eye | 15.8 | 15.8 | 60 | yes |
| 12 deliver | 0.1 | 0.1 | 2 | yes |
| 13 publish | 0.0 | 0.0 | 10 | yes |
| **Episode** | **361.2 (6.02 h)** | **249.6 to 266.6 (4.16 to 4.44 h)** | 360 (6 h) | yes, if the projection holds |

Three numbers in the table stay over their cap:

- Step 09's `take_dq` round 1: 32.8 minutes against a 30-minute cap.
- Step 09's `take_content`: 21.2 minutes against a 20-minute cap.
- The new 10-minute "lines" wall in step 04 has no measured run behind it.

### Test suite

| Run | Failed | Passed | Skipped | Notes |
|---|---|---|---|---|
| Before the retro | 7 | 12,382 | 4 | Baseline |
| After the first build pass | 9 | 13,140 | 5 | Two new failures, both fixed |
| After the build | 7 | 13,142 | 5 | The same 7 as the baseline |
| After phase C | **0** | **13,201** | 5 | All 7 baseline failures were stale tests or a flaky threshold |

### Warp scores on the shipped takes

All eight warp failures on ep01 were "eye-only": the face-stability score (S) stayed under its 2.5 wall on every one. Only the secondary score (Se) was over. Seed retakes cured 0 of 4 attempts.

| Take | S | Se |
|---|---|---|
| T07 | -0.04 | 4.16 |
| T10 | 0.52 | 3.31 |
| T15 | 1.96 | 4.40 |
| T16 | 0.13 | 4.97 |
| T19 | 1.88 | 3.22 |
| T20 | 0.81 | 4.35 |
| T21 | 0.10 | 3.55 |
| T24 | -0.64 | 3.40 |

## Images

No images exist in the source folder for this retro. None were copied. The retro's evidence is all text, JSON and log records. The storyboard panels and the master's frames are in the episode's own library folder, outside this source.

Images rendered by MiniMax-H3 are held from publication until the studio's licence review clears them.

## Verdict

The episode met its quality gate and shipped unuploaded. It ran 1.2 minutes over the 6-hour machine budget, and about 2 hours of wall time were lost to parks, a hung process and an engine that started twice. The retro's fixes are projected to bring the next run to 4.2 to 4.4 hours, but that projection is a replay of ep01's records, not a measured run. Two cap rows (`take_dq` and `take_content`) have no safe speedup yet, and the owner must rule on them or change the GPU side.

The retro's core rules are brick B1 (a round, a climb or a cap is spent only when something actually changed) and brick B5 (a clock must still charge a process that dies).

## What changed in the pipeline

The retro's 16 packages landed as 26 commits from the first (`6572728`) to `689b3ec`. Phase C added 14 more from `ada8fda` to `4a7ceba`. The changes, in plain words:

- **Plan ladder (P01):** Counts only real refusal rows. A new plan climb is counted only when the writer model is called. A stale plan is re-signed over the rows it already carries.
- **Plan cures and rulers (P02):** A two-shot cure no longer needs a writer call. A grammar plan is judged by different rules. A new check catches crowds with no shot (G-CROWD-ORPHAN) and a floating-limb advisory.
- **Prompt builder (P03):** Crowds are drawn only where a shot declares extras. Night scenes keep their lamp and never get "low sun". Fifteen of 28 take prompts are now byte-identical to before.
- **Storyboard draw (P04):** Figures under haze are drawn solid. A repaired anchor no longer redraws neighbouring panels when the place did not move.
- **Panel eye (P05):** Each panel is read once per proven input. A rewind re-reads only the changed panels.
- **Content check (P06):** A take's crowd is judged against its own panel. An optional anatomy question was added as advisory.
- **Warp gate and face refine (P07):** A hard fail is S above 2.5 only. Se alone becomes an advisory "eye" state. One seed retake, then a refine or a flagged ship.
- **Take ladder (P08):** A retake round is spent only when a take changed. A batch that cannot be afforded is trimmed, not refused.
- **Ship and assemble (P09):** Kept takes ship flagged, and each flagged take is listed with its seconds in a file.
- **Master and QC (P10):** A pass counts its frames. A master rung that changed nothing takes no recut. A pace guard was added for the upscaler.
- **Voice (P11):** A 10-minute lines wall. A homophone pair (cheque and check) is filed and re-heard, not re-rendered.
- **Clock ledger (P12):** Step walls are charged even if the process is killed. Attempts are locked.
- **Autopilot (P13):** Does not park on a dirty working tree or a moved HEAD. Keeps its own log per launch.
- **GPU and device (P14):** The router reads video memory first. The engine is freed once at a model-family boundary.
- **Tracking card (P15):** Keeps each step's history across rewinds and prints the debt.
- **Docs (P16):** The skill and gate documents now describe the code. The mandatory read shrank from 236 KB to 128.9 KB.
- **Phase C close-out:** A stall watchdog and a charge for killed runs. The av3 edit gate got its own limits, which took the ep01 edit-gate faults from 7 to 0. A GPU whisper worker that exits after 30 seconds of idle is named in its error message, and the CPU fallback is kept.

The changes were measured against the ep01 records. Several are proven only in tests, and some are not yet run on a GPU (see the limits).

## Limits and open questions

- **The cap projection is not proven.** The 4.2 to 4.4 hour figure is a replay of ep01's records with the fixes assumed to work. The next episode run under the autopilot is the real test.
- **Two caps stay over.** `take_dq` (32.8 against 30) and `take_content` (21.2 against 20) have no safe speedup. Both are bound by real model work.
- **The lines wall has no measurement.** Its 10-minute size needs the first run's figures.
- **Eight warp takes shipped flagged.** Only the owner's labels can re-arm the hard secondary-score wall. Until then the warp gate uses an advisory state, and the owner must label T07, T10, T16, T20, T21 and T24.
- **Several fixes are untested on a GPU.** The solid-figure change, the panel-eye cache on a live run, the VL free-up at step 03 and the NVENC check all need a GPU window.
- **Known gaps remain.** A clone-detection path never fires, the casebook shows a shipped take as a default pass, and a manual pause still counts against a step's cap.
- **Dead time was not charged.** About 129 minutes of wall time came from gaps. The fixes name the causes, but no record predicts the next episode's gaps.
- **Labels by agents.** Any label made by an agent is marked as such until the owner labels it.
- **Skeptic coverage.** The files show a skeptic for every investigation area and for phase C. They do not show a skeptic for each phase B build package.

## Sources

- EP01_RESULT (episode result and per-step minutes, 2026-10-18)
- FINAL (overnight retro close-out and phase C, 2026-10-19)
- BUILD_PLAN (retro build plan, 18 areas, packages P01 to P16, decisions D1 to D22, replays R1 to R12, 2026-10-18)
- cap_fit (replay and cap-fit projection, 2026-10-19)
- Area reports and their skeptic reports: autopilot, caps and clock, DQ upgrade, face refine, finish and upscale, GPU scheduling, panel review, plan, prompt builder, QC and master eye, retake cures, rulers, ship policy, skill docs, storyboards, tracking UI, voice, warp gate (2026-10-18 to 2026-10-19)
- Late findings (2026-10-18)
