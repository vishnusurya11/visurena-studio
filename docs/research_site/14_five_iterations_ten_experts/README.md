# Five retrospective rounds, ten expert reviewers each: what the studio learned from one episode

*2026-10-20 (Seattle time). Ten specialist reviewers read the first finished episode of a Jekyll and Hyde series, five times in a row. Each round, a chair checked their claims against the real files and frames before ruling. Three claims from round four were wrong and were caught in round five.*

## The question

The studio makes a short episode per book chapter, on one local GPU, for $0 in cloud spend. Episode 1 of the Jekyll and Hyde series was finished, but it took about 31 hours of wall-clock time, against a target of 6 hours of machine time. The question was: what in the engineering and creative process makes the episode slow and makes it look wrong, and which fixes are worth building before episode 2?

The owner's order was to run a retrospective with ten experts, improve the engineering and creative process so it fits the deadline, and repeat that for five iterations.

## What existed before

- A pipeline that already had many quality gates (automatic checks that refuse a take or pass it on). Each gate had been added after a past fault.
- A retrospective from earlier the same week (the "deadline retro") that had found the 31-hour wall time and had built the first set of fixes.
- Gate rules written as text files that an AI writer reads. These files had a hard size cap, so new rules could not always be added.
- No rule for when a new gate may stop a run. New gates were often switched on at once.

Terms used below:
- **H3** is MiniMax-H3, the video model that turns a still picture and a text cell into a short moving take.
- **ref2va** is H3's mode that takes reference pictures and produces video.
- **LoRA** is a small add-on file that changes a model's style or identity.
- **DQ** means data-quality or content check run on a finished take.
- **Gate** is an automatic check that either passes a take, refuses it, or parks the run.
- **Ledger** is the running record of cost and time per stage.
- **Wall time** is clock time from start to finish. **Machine time** is GPU and CPU minutes used.

## Method

**Arms.** There were no competing arms in the usual sense. The unit of comparison was the episode itself, read at five stages: episode 1 as built, then four successive plans for episode 2.

**Panel.** Each round used ten experts, each with one lens: screenwriter, storyboard director, cinematographer, image artist, video generation, editor and sound, QA gates, pipeline engineer, production manager, and audience strategist. That is 50 expert reports in total, ten per round.

**Chair.** After each round, one chair (the lead reviewer) wrote a plan. The chair first checked the experts' claims personally against stored records and frames. Each plan section 0 lists which claims were confirmed, which were overturned, and which were left as plausible but not proven.

**Debate rounds.** Each round was one pass: experts report, the chair cross-examines conflicts, the chair rules. There was no second debate round. Where experts disagreed, the chair's ruling in each plan records the choice and its reason.

**Pre-registered rules.** Each plan set decision rules before any test ran. For example, iteration 5 set a single rule for when a new gate may move from "shadow" (logged but not acting) to "acting". It required a neutral lever to be wrongly flipped at most 6% of the time, and a gate to show its effect on at least two books before it could refuse anything.

**What was measured.** The chair re-read stored files (for example, the shot file and the timing log) and looked at frames. Machine-minute estimates are marked as estimates in the plans. No GPU job, network call, or upload ran during the retrospective itself. Tests for the code changes were run afterwards.

**Cost.** The retrospective used only the reviewers' reading time. No credits were spent.

## Results

### How the bar rose, round by round

| Round | Rule added | What it overturned |
|---|---|---|
| 1 | Decide at the cheapest layer that predicts the result. | Refine cost. The budget reads the timing log (28.7 min), not the per-take wall time (93 min). |
| 2 | A rule may refuse only what it has been shown to refuse. | "T08 has no contact." The contact is drawn. The real fault is the missing reaction. |
| 3 | Address each instruction to the layer that draws it. | A grin was blamed on the model. It sits in Hyde's identity text ("cold grin" appears 10 times in the shot file). |
| 4 | Read the result at the last layer before the viewer. Act only when a cure clears the next chapter. | Two camera moves were written as "tilts up from the gaunt to the rugged", which is an adjective, not a place. |
| 5 | Before blaming the model, read the input it was given. | Three round-4 claims were withdrawn or corrected (see below). |

### Round-five corrections to round four

| Round-4 claim | Round-5 finding |
|---|---|
| H3 relights Hyde's brim shadow in 0.25 s | Withdrawn. The take text said "lifts his chin ... from 00:00", so the input commanded the change. |
| Take T11 shipped with a tan coat | Wrong. The coat is black. |
| The 13-second VLM read is a model reload | Wrong. One load per batch. |

### Final backlog (from the round-5 plan, section 2)

Machine minutes are the estimate in the plan. "Agent h" is the estimated reviewer or builder hours.

| Rank | Item | Expected gain | Machine min | Agent h |
|---|---|---|---|---|
| B1 | Supervisor survives known faults; nothing uploads unasked | p95 wall 24 h to 10.4 h (simulated) | 0 | 1.6 |
| B2 | Writer's brief carries the chapter's own numbers | about -0.3 h mean wall | 0 | 2.0 |
| B3 | One lever table and decision rule; shadow gates | about -0.7 h mean wall | 0 | 3.5 |
| B4 | Gates stop refusing inside their own noise | about -0.2 h | 0 | 2.0 |
| B5 | Soft park resumes on a default after 30 min | about -0.5 h | 0 | 2.0 |
| B6 | Engine recovery from the measured timeline | -24 min per crash | 0 | 3.0 |
| B7 | Hyde kept hidden by pose and geometry, revealed by one timed verb | the face the owner flagged | about -4 | 5.0 |
| B8 | Three-arm test: sun line or chin lift causes the face | decides B7's mechanism | +2.6 GPU | 0.5 |
| B9 | No locked narration of 5 s or more unless declared still | about 20 s of frozen picture moves | about -6.5 | 2.5 |
| B10 | Garment gate reads the garment, shadow only | no re-seed on a rim light | -3 | 2.5 |
| B11 | Dialogue runs alternate sides and light | silent stretches 19.7 s to 8 s | -2.3 | 4.5 |
| B12 | Sound: turn tails, cue contract, pivot pace | holes become events | about -2.7 | 4.0 |
| B13 | Honest delivery message | shipped faults listed with cause | 0 | 2.0 |
| B14 | Credit line correct for a named chapter | correct on 10 of 10 Jekyll episodes | 0 | 0.5 |
| B15 | VLM read: compact reply, per-call log | about -10 min per pass | -10 | 2.5 |
| B16 | Episode 2's paired tests, re-cut | 6.2 min, down from 8.8 | +6.2 | 2.5 |
| B17 | Parallel tests; move caps out of the gate-rules file | about 5,500 bytes of headroom | 0 | 1.5 |
| B18 | Repair cap as code | caps a 12.8 h fault loop | 0 | 0.6 |

### Built during the window (five commits, 23 new tests)

| Item | What changed | New tests |
|---|---|---|
| B1.3 | A publish approval must name each episode it covers. The old approval, signed for episode 1, would have uploaded episodes 2 to 10 unasked on a resume. Now an unlisted episode is parked. | 7 |
| B14 | The credit line for a named chapter is written correctly; a broken line is refused before upload. | 4 |
| B7 (brief layer) and B2 | A picture rule for the writer: a face the chapter keeps back is hidden by camera placement, never lifted or lit on the cheek. The brief also states the dialogue ceiling in words. | 6 |
| B4.3 | A frozen-whole row that was demoted now prints "ADVISORY", never "HARD". | 2 |
| B15.2 | Every text read from the VLM (vision-language model) logs seconds and tokens. | 4 |

The full test suite exited 0 after the five code commits. Tests used no GPU, network, or paid call.

### Projected episode 2 (first pass, estimate)

| Item | Minutes (estimate) |
|---|---|
| Round-4 projected first pass | 239 |
| B7 brief layer (fewer commanded re-seeds) | about -2 |
| Lanyon reference sheet | about +3 |
| Logging | 0 |
| **First pass** | **about 240 min (4.0 h; range 3.5 to 4.5 h)** |

That leaves about 2 hours of the 6-hour budget for retakes. The wall-clock figures are simulations, not measurements: the mean wall time is projected at 9.4 to 9.7 h as-is and 5.3 to 7.5 h with B1 and the owner toggle described below.

## Images

Images rendered by MiniMax-H3 are held from publication until the studio's licence review clears them.

Each image is a contact strip or summary sheet from the source folders. Captions say what to look at.

![Iteration 2: the T08 spike row. The boot is on the child, but the child never reacts and the camera runs into Hyde's grin. This is the fault the round-2 chair corrected.](images/iter2_t08_spike_row.png)

![Iteration 4: the T11 relight strip at 0, 0.25, 0.5, 2.0 and 4.6 seconds. Hyde's eyes go from dark under the brim to lit and smiling. Round 4 read this as a 0.25 s relight; round 5 withdrew it because the take text commanded a chin lift from the start.](images/iter4_t11_relight_strip.png)

![Iteration 4: the T21 "tilt up from the gaunt to the rugged" strip. The move reads as a push: the figure grows and the head drops. The camera verb was aimed at an adjective.](images/iter4_t21_tilt_strip.png)

![Iteration 4: identity sheets for Hyde and Utterson, one figure each on a dark ground. The sheets were the input to the image and video models. The amber rim light on Hyde's right edge is the stripe the image expert traced to the garment drift.](images/iter4_identity_sheets.png)

![Iteration 4: Hyde close-ups across takes. Several frames show the smile that the identity text had asked for; the round-3 chair traced it to a line in the identity text, not to the model.](images/iter4_hyde_faces.png)

![Iteration 3: paired frames from the QA folder, two men side by side under the lamp. Use it to compare how the identity and wardrobe read between takes.](images/iter3_qa_pairs.png)

![Iteration 5: the image artist's strip for the door and dialogue shots: the key in the lock, the hand, and the two men under the lamp. Use it to check the picture stage before video.](images/iter5_artist_all.png)

![Iteration 5: the storyboard run for the dialogue scene, four frames per take. Use it to see the side and light of each shot, which the round-5 plan trimmed to what chapter 2 can hold.](images/iter5_storyboard_all3.png)

![Contact sheet of episode 1's frames, the kind of sheet the round-1 experts were pointed to. Use it as a baseline before any fix.](images/contact_sheet.png)

## Verdict

The retrospective found that most of the 31-hour wall time came from waiting on checks and retakes that were not needed, not from rendering. The five rounds turned the work from "measure it" into "measure the input that caused it". The fixes that were built are small and safe: a publish approval that names its episode, a correct credit line, a writer rule that keeps a face hidden, and a VLM log that shows where time goes.

The projected first pass for episode 2 is about 4.0 hours of machine time, inside the 6-hour budget, but that figure is an estimate. The bigger wall-clock gains depend on items that were not built yet (the supervisor's streak handling, and an owner setting that restarts the machine's supervisor after a Windows update).

## What changed in the pipeline

Commit subjects, in plain words:

- Publish approval now names the episodes it covers; unnamed episodes park before upload.
- Credit line for named chapters is written correctly, and the metadata check refuses an empty quote.
- The writer's brief now contains a rule for hidden faces and states the dialogue word ceiling.
- A frozen-whole check that was demoted now says "advisory", not "hard".
- Every VLM text read writes one log row with seconds and token counts.

## Limits and open questions

- The 31-hour and 6-hour figures come from the studio's own timing logs. Projected wall times are simulations.
- The round-5 face fix (B7) depends on a three-arm test (B8) that had not run; no GPU job ran during the retrospective, so the mechanism is still open.
- Several planned items were deferred: the supervisor's tick-fault streak, the parallel test runner, the repair cap, and the writer rule file's byte cap (the file was 26,614 bytes against a planned 24,900).
- The live episode 1 description still carried a broken credit line at the time; the owner was to decide whether to fix it.
- The claude.ai copy of the architecture page was not republished in this window.
- The episode 1 upload was first blocked on the series title. The sources say the upload later went public; the source did not record the date of the owner's title decision.
- Whether the owner chose the 0.88 or 1.0 tempo for one dialogue line is not in the sources.

**Owner decisions still open (each with a default, none blocking):**
1. Add an episodes list to the publish file before episode 2 can upload. Default: episode 2 is held.
2. A Windows setting that auto-restarts the studio supervisor after an update, plus one test reboot. Default: the supervisor stays down until someone logs on.
3. Whether to repair the live episode 1 description. Default: leave it.
4. A two-minute eye-and-ear check of five clips. Default: ship as measured.

## Sources

- FINAL (five iterations, final report, 2026-10-20)
- PLAN iteration 1 to PLAN iteration 5 (chair's plans, 2026-10-20; headings and round-by-round changes)
- UPLOAD_BLOCKED (episode 1 publish block, 2026-10-20)
- Expert reports for each round (ten per round, 2026-10-20)

## Audio

A listening comparison of one dialogue line at three tempos. The line is "Enfield answering" in episode 1. The owner's ear was the decision rule; 0.88 was the candidate and 1.0 the control. The 0.80 variant is in the folder but is not named in the plan.

- [l17_tempo_1.0.wav (control, unchanged)](audio/l17_tempo_1.0.wav)
- [l17_tempo_0.88.wav (candidate)](audio/l17_tempo_0.88.wav)
- [l17_tempo_0.80.wav (extra variant)](audio/l17_tempo_0.80.wav)
