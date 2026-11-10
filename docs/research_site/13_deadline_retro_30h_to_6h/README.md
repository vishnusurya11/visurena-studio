# From 31 Hours to a 6-Hour Plan: A Deadline Retro on the First Episode of a Local AI Video Studio

*Source date: 2026-10-20. The first finished episode of Jekyll and Hyde used 6.02 hours of machine time, almost exactly its 6-hour budget, but took 30.85 hours of wall-clock time to reach an upload-ready master, because the owner found two picture faults that no automatic check measured and the repair loop broke the pipeline three more times.*

## The question

The studio makes short AI-animated episodes from public-domain books. Each episode has a hard budget: the machine (one local GPU and its helper programs) should do the work in 6 hours or less, and the episode should be ready to upload. The first episode, Jekyll and Hyde episode 1 (a noir style), met the machine budget on its first full pass but missed the real deadline by a wide margin. The question for this retro was simple: where did the 31 hours go, and can the second episode finish in one unattended pass inside 6 hours?

## What existed before

Before this retro, the studio had:

- A pipeline of about 20 steps (planning, voice lines, storyboard grids, video "takes", checks, edit, upload), run by a runner that charged each step against a per-step time cap and a 6-hour episode clock.
- Automatic checks, called gates, that judged each take (for example a sharpness check, a content check, and an "eye" check made by a vision model). A gate is a pass or fail rule that stops a step from moving on.
- A repair path: when an owner note asked for a change, the runner re-rendered only the affected takes.
- A set of written lessons (a "skill" file) that the studio updated after each run.
- An overnight retro in which many AI agents reviewed the run and wrote changes. That retro produced more than 70 agent runs and about 40 code commits before this retro began.

Terms used below: **H3** is the MiniMax video model that renders each take. **ref2va** is the reference-image mode of that model. **LoRA** is a small add-on weight file that changes a model's style or face. **DQ** (data quality) is the automatic check of a take's pixels. **Ledger** is the written record of what each step cost and what it produced. **Take** is one rendered video clip.

## Method

The retro ran as a debate, not a single review:

- **Three timelines** were written. One counted machine time from the episode's clock records. One counted agent work from the workflow transcripts. One listed every incident from the ledger.
- **Eight proposals** were written, each on one topic: quality at the first pass, GPU schedule, gates that see, change safety, agent process, ops reliability, skill documents, and deadline budget.
- **Eight skeptic reviews** each tested one proposal. The skeptic's job was to find the cases where the proposal would not have saved time, and the ranking in this write-up uses the skeptic-corrected figures.
- The sources do not describe a formal number of debate rounds for the proposals. The pattern was one proposal round followed by one skeptic round per proposal.
- The sources also count the wider agent effort. The retro's own root-cause table says 185 agents ran during the episode's build period with no cap on agent wall time. The overnight retro alone ran more than 70 agents.

**What was measured.** Machine time came from the episode's clock file, its timing rows, its repair log and the launch logs. Agent time came from workflow transcripts, with timestamps that are accurate to about one minute. Where a number was an estimate, the sources mark it as an estimate, and this write-up keeps that mark.

**Rules set in advance.** The sources state the rules for the next build phase rather than for the debate itself. Those rules are: write the failing test before the function; no GPU in any test; each build package owns its own files; no stash and no shared-branch tricks; and each fix must be replayed on the already-delivered episode before it can run.

## Results

### Where the 30.85 hours went

Wall-clock time ran from the first launch to the upload-ready master (30.85 hours in total).

| Bucket | Hours | Share of wall time |
|---|---|---|
| Machine, first delivery (13 runs, master 1) | 6.02 | 20 % |
| Machine, two repairs (5 runs; 1.00 h of it in killed launches) | 1.83 | 6 % |
| Machine idle between first-delivery runs (parks, refusals, two engines stacked for 36 minutes) | 2.15 | 7 % |
| Agents building fixes while the machine waited | 11.2 | 36 % |
| Session dead, nothing running | 4.7 | 15 % |
| Unlogged waiting (owner review, waiting for a go) | 4.7 | 15 % |
| Small gaps between launches | 0.2 | 1 % |
| **Total** | **30.85** | |

The machine was busy about a quarter of the wall time (7.85 hours charged out of 30.85).

### The largest time sinks

| Rank | Sink | Lost | What happened |
|---|---|---|---|
| 1 | Face blur, found by the owner, then fixed | About 5.5 h of agent work plus 0.6 h of machine time | The face-refine step reached only 2 of 28 takes, because a 60-pixel size wall, a wide-shot-only rule and a photo face detector skipped the rest. The owner saw it about 7 hours after the master. |
| 2 | Session death | 4.7 h | The supervisor's heartbeat stopped from about 00:58 to 05:39. The cause is not known. |
| 3 | Unlogged waiting after the second master | 4.7 h | No run and no workflow ran in this window. |
| 4 | Paste warp, found by the owner | About 2.4 h of agent work | The repair pasted the whole re-rendered square, so about 80 % of the pasted pixels were hat, hair, collar and background. The seam and flicker gates passed it, and flicker even improved. |
| 5 | Retro changes broke the repair | 1.0 h of machine time plus 1.5 h of agent cleanup | Three launches failed on three different faults. |
| 6 | First-delivery parks and refusals | 2.15 h | A voice check heard "cheque" as "check" eight times, plus rules about code, prompt length and crowds. |
| 7 | Repeated checks on unchanged takes | 103.7 min of checks for a job of about 18 min | The 28 takes were measured about three times. The repair re-measured all 28 unchanged takes (1,070 seconds). |
| 8 | A video encode that hung with no watchdog | 0.67 h | The encode had written 3,259 of 3,348 frames and then waited forever. |

### Machine time per step (first delivery)

| Step | Charged (min) | Cap (min) | Note |
|---|---|---|---|
| 02 plan | 39.7 | 60 | Second climb re-signed one carried row (10.7 min) |
| 03 places | 32.9 | 15 | Vision-model reads fell to the CPU (285 s a read, against 54 s on the GPU) |
| 07 board | 17.0 | 30 | Inside cap |
| 08 panels | 66.1 | 50 | Whole-board eye check re-read four times to change two panels |
| 09 shoot | 119.6 | 242 | Take checks 32.8 min against a 30 min cap; take content 21.2 against 20 |
| 10 edit | 45.7 | 30 | Includes a 40-minute hang in the video encoder |
| 11 QC | 15.8 | 60 | Inside cap |
| **Total** | **361.2** | **360** | Over by 1.2 minutes |

Take renders were not logged with a timing row. The sources estimate about 85 minutes of render time across three spans, so the render share in this table is an estimate, not a record.

### The five root causes

The retro reduced the 31 hours to five causes:

1. **No gate measured a face at the size the viewer sees, or the pixels outside a paste.** The gates counted whole-frame sharpness and motion. A face is only 1 to 4 % of the frame, so a whole-frame check cannot see it. The owner's eye was the first instrument, twice.
2. **A change to a shared decision rule was never replayed on the delivered episode before it could launch.** The dry-run check read counters, not the real decision functions, and nothing called it.
3. **Re-entering a step repeated whole-set work on unchanged inputs,** and the code moved under a live run (nine code versions over 13 runs).
4. **Nobody owned idle time.** Dead sessions, open-ended pauses, hangs and killed launches sat on no clock.
5. **Agent loops built before measuring, with no budget.** In the first build round, two of three builds changed nothing measurable.

### The projected second episode

The retro projects the second episode's machine time from the first episode's unit costs. These are estimates.

| Clock (central estimate) | Step | Minutes (low-high) |
|---|---|---|
| 0:00 | Preflight: clean tree, dry check, engine process, token age | about 1 |
| 0:01 to 0:32 | Plan, one climb | 29 to 33 |
| 0:32 to 0:43 | Places, vision reads on the GPU | 10 to 12 |
| 0:43 to 1:01 | Record (voice lines) | 15 to 20 |
| 1:01 to 1:16 | Timeline and storyboard grids | 15 |
| 1:16 to 1:42 | Panels | 26 |
| 1:42 to 2:57 | Renders, with take checks run on the CPU beside them | 60 to 85 (estimate; no render timing row exists) |
| 2:57 to 3:27 | Content, eye and face-list checks, each run once | about 30 |
| 3:27 to 3:57 | Face refine at full scale | 21 to 42 |
| 3:57 to 4:17 | One retake round | 10 to 30 |
| 4:17 to 4:23 | Edit, one upscale | 5 to 6 |
| 4:23 to 4:41 | QC and master-eye check | 16 to 25 |
| **4:41** | **Upload-ready** | **3.9 to 5.4 hours (central 4.7)** |

The three source documents do not agree exactly on the ideal single-pass cost. The machine timeline gives 4.0 to 4.8 hours, the budget document gives about 4.5 hours of planned minutes, and the retro gives 3.9 to 5.4 hours. This write-up reports all three. None of them is measured yet.

## Images

No images. The source folder for this topic contains markdown files only, so this section is empty by design.

## Verdict

The machine was not the main problem. The first master finished within 1.2 minutes of its 6-hour machine budget. The loss came after delivery: two faults that no gate measured were found by the owner, and the repair that fixed them ran through several broken launches. The retro's verdict is that the 6-hour budget is the right size for a clean pass, but that the budget only protects a deadline if three things hold: the face and paste faults are measured on the first master, every change is replayed on the delivered episode, and idle time is charged to a clock.

The retro's proposed changes are ranked by expected hours saved. The top items were a face list at the first master, a hard refusal of unmeasured paste pixels, a dry-run check that calls the real decision functions before any repair launches, a supervisor watchdog with timed pauses, and a rule that code does not change under a running episode.

The retro is explicit that its projection is unproven until the second episode runs. Its own words are that the projection "is unproven until ep02 actually runs".

## What changed in the pipeline

Changes that were built during the repair (commit subjects in plain words):

- A 60-second stall watchdog was added to the video encoder after it hung.
- The panel-eye check got a per-input cache, so an unchanged board is not re-read after a rewind. This landed after the expensive passes had already run.
- The engine restart now checks for a live engine process first, so a second engine cannot start over a loading one.
- The voice check gained a phoneme-equality test that catches repeated identical wrong transcripts.
- The freeze that stops finished takes from being re-rendered was extended, after a launch re-rendered a frozen take.

Changes proposed by the retro but not yet built (the sources list them as a ranked plan, with the build packages in order):

- A dry-run check that calls the real decision functions and refuses to launch a repair that would re-render delivered takes.
- A face list at the first master, with an advisory label for faces under 120 pixels.
- An outside-the-face refusal that cannot pass when the measure is missing.
- A face contact strip for the quality check, so the owner's labels can be collected.
- A refine step that is budgeted and cut last, not first.
- Replay of the decision functions on the delivered first episode at commit time.
- Supervisor watchdog, timed pauses, and a rule that a running episode is not restarted by a code commit.
- A timing row for every take render, and charging killed launches to the clock.
- Content-addressed caches for the take checks, so unchanged takes are not re-measured.
- A single operator page for the repair protocol, replacing four scattered copies.

## Limits and open questions

- **The second episode is the test.** Every figure for it is an estimate until it runs under the new rules.
- **Take render time is not logged.** It is the largest step item, so every machine total in this write-up is a lower bound.
- **The cause of the 4.7-hour session death is not known.** Sleep, logoff and a crash are all possible.
- **Two numbers disagree.** The master-eye check shows 1,037 seconds in one record and 49 seconds in another, and the cap line shows yet another figure. This is not resolved.
- **The repair-cap display is wrong.** It adds two repairs and compares the sum with one cap. Each repair stayed inside its own cap.
- **Reference images for new characters were not measured.** The retro says they are the largest unbudgeted block and sit outside the 6-hour clock.
- **The ideal-pass projections differ** across the three sources (see the projection table).
- **The face thresholds were calibrated on one episode.** The 120-pixel rule is labelled a refine trigger, not a wall, until the owner has labelled faces to check it against.
- **Most of the proposals were reviewed by agents.** The skeptic reviews are agent reviews. The retro itself says the overnight retro never looked at a picture, and the picture-level fix came from the owner.
- **The owner's OAuth consent step is open.** The upload token expires every 7 days while the app is in testing mode, and the upload waits on a manual step.

## Sources

- RETRO (deadline retro, 2026-10-20)
- Timeline of machine time, every run (2026-10-20)
- Incident and rework ledger (2026-10-20)
- Deadline budget for a 6-hour unattended pass (2026-10-20)
- Eight skeptic reviews, one per proposal (2026-10-20)
- Episode clock, timing, repair and launch records for Jekyll and Hyde episode 1 (studio run data)
