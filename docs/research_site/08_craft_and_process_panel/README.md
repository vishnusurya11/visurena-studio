# A Ten-Seat Craft Panel Audited an AI Episode Pipeline: What It Proposed, What Was Built, What Is Still Untested

*Source date: 2026-10-21 (ruling and builds), with the GPU pre-registration on 2026-10-22. One-line abstract: a panel of ten expert agents and one arbiter reviewed how the studio writes and checks its short episodes; the studio adopted 31 changes, built 26 of them, and left the taste and picture changes to be tested.*

## The question

Visurena Studio turns a public-domain book chapter into a short, narrated video episode. Most of the work is done by AI models: a writer drafts a screenplay plan, a set of take prompts drives a video model, and automatic gates check the result. The studio wanted to know why the episodes still have weak craft. Examples are a character who speaks with a closed mouth, a shot that says "the camera holds" as if it were a scene, or a narrator who speaks lines that belong to a character.

The question for the panel was narrow. Which defects in the writing and the prompts are real, which fixes are safe to build now, and which changes need a test with the studio owner, a GPU, or an audience before they ship?

## What existed before

Before the panel, the pipeline had many gates. Each gate checked one thing, such as the share of words spoken as dialogue, or whether a take's face matched its character sheet. The gates were green on most episodes, yet the owner still judged many episodes weak. The panel's own early finding was that a green gate proves only the absence of the faults that gate measures.

One fact changed the picture. The episode writer was told it had 108 words of dialogue to spend. The real gate measured dialogue as a share of the plan's own words. For the first episode, Jekyll and Hyde ep01, the plan had 82 dialogue words out of 239. That is 0.343 against a ceiling of 0.35, so the real room was one or two words, not 26. Four of the first-round fixes had been built on the 108 figure. Their authors conceded that in the second round.

## Method

**The panel.** Eleven seats were filled. Ten were expert seats: screenwriter, dialogue writer, narration and voice-over, series composer, storyboard prompts, take prompts, process engineer, judges designer, audience, and skeptic. The eleventh was the gavel, which ruled on the votes. Each expert seat was run as a separate agent with its own lens.

**Rounds.** There were two rounds of expert work.

- Round 1: each of the ten experts wrote a diagnosis of the pipeline, using evidence from the episode 01 files, and proposed fixes. Each expert also named the brick, the one rule it thought generated the problem.
- Round 2: each expert read the others' round-1 proposals, merged duplicates, and voted on each item, with dissent recorded. Several seats conceded their own round-1 proposals here.

The gavel then wrote one ruling after round 2. It sorted the merged proposals into four groups: adopted, try first, rejected or deferred, and questions for the owner.

**Standard of proof.** The ruling set a different test for each kind of change, so cheap fixes were not blocked by expensive benches.

| kind of change | what it needed before it was wired |
|---|---|
| Defect fix (a contradiction, a garbled phrase) | A failing test on a copy of the episode 01 data, then the fix |
| Advisory row (it reports but never refuses) | A replay over every plan on disk, with a count of how many plans it could read |
| Change that reaches pictures or voice | A pre-registered bench of at least six renders, with the kill rule written before the first render |
| Taste change (story shape, who speaks, length, look) | A sample judged by the owner, or support from k of n listeners |

**Sample.** A hand-written sample of the second episode (ch2, "Search for Mr. Hyde") was written two ways. Version A followed the current writer's habits. Version B followed the adopted rules. It was one draft each, so it shows what the rules ask for. It is not a measured arm.

**Replay.** A read-only replay harness was built to run every screenplay check over all 42 plans on disk. For each check it counts the plans it could read, the fires, and the recall on planted faults made by code.

## Results

### The panel's decisions

| group | count | what it means |
|---|---|---|
| Adopted | 31 | Defect fixes, report-only instruments and shadow rows, in five waves |
| Try first | 30 | Each changes pictures, voice or story taste, so each needs a sample |
| Rejected or deferred | 9 | Not built now |
| Owner questions | 9 | Listed for the studio owner to rule on |

The estimated build time for the adopted items is about 58 hours. Waves 0 to 2, about 43 hours, were to land before the second episode's plan was written.

### Build status (from the two build reports)

| wave | items | built | not built or not shipped |
|---|---|---|---|
| 0, instruments | A1-A3 | 3 of 3 | none |
| 1, plan-side fixes and shadow rows | A4-A16 | 12 of 13 | A15 was measured and did not beat the old rate, so nothing shipped |
| 2, picture-side text | A17-A22 | 6 of 6 | none |
| 3, operations | A23-A28 | 5 of 6 | A25 waits for another package (proof P6) |
| 4, bench lines and retention | A29-A31 | 0 of 3 | all three marked "next" |
| **total** | **31** | **26** | **5** |

### Measured numbers from the instruments

Craft census over the 28 rendered takes of episode 01, printed by the new $0 counter:

| defect | count |
|---|---|
| hold heads renamed (a "hold" written as "keeps") | 12 |
| "now in frame" in a take prompt | 19 |
| "walking pace" wording | 8 hits in 5 prompts |
| speech verb beside a closed mouth | 1 (take 13) |
| sky word on a night setup | 8 |
| repeated six-word runs | 66 runs in 13 prompts |
| garbled text | 2 |
| camera sentence used as an end line | 1 |

Prompt provenance: 27 of 28 rendered takes were built from older wording than today's build, and 8 of 28 fail a current hard rule. The new QC line prints both. Nothing was re-rendered automatically.

Voice floor: 3 of 22 lines in episode 01 shipped with their similarity floor set to 0.0, which the new QC line now prints. One of them, line 11, had failed 11 times before it shipped.

Replay over all 42 plans on disk (Jekyll, War of the Worlds, Sherlock Holmes "A Study in Scarlet"):

| check | plans it could read | fires | fires on approved plans | recall on planted faults |
|---|---|---|---|---|
| Speech verb on a silent face (G-MUTE) | 42 | 20 | 0 of 5 | 100 of 100 |
| Narration line holding a cast member's words (G-STOLEN) | 42 | 63 | 13, on 3 of 5 | 108 of 108 |
| Orphan reply (ORPHAN-REPLY) | 16 | 3 | none readable | 3 of 3 |
| Paragraph no line reaches (PARAGRAPH-HOLE) | 16 | 65 | none readable | 20 of 20 |
| Face lit before its reveal (G-REVEAL) | 1 | 3 | none readable | no planted case |

The approved set is three War of the Worlds episodes and two Scarlet episodes. Only 16 of the 42 plans carry the source spans the orphan and hole checks need, so "no fires on approved plans" for those two checks means only the readable ones. The G-STOLEN result is the one the studio has not settled: its 13 approved fires are Watson relaying what Holmes and Lestrade said in the book. No cure for it ships without the owner's ruling.

### The ch2 sample, version A against version B

| measure | A (current writer) | B (adopted rules) |
|---|---|---|
| Narration share of words | 0.73 | 0.60 |
| Dialogue plus off-screen dial | 57 of 213 words (0.268) | 67 of 250 words (0.268) |
| Words spoken in a character's voice | 27% | 40% |
| Quotes in the narrator's mouth | 4 | 0 |
| Orphan replies | 1 | 0 |
| Speech verb on a silent face | 3 | 0 |
| Hyde's face shown before the book reveals it | 5 shots | 0 |
| Book paragraphs reached (of 50) | 24 | 30 |
| Estimated runtime | 135.6 s | 142.7 s |

Both versions keep the dialogue share at 0.268. B reaches the voice back through inner thoughts, which the ceiling does not count, and through one off-screen line. A spent the same room by moving speech into narration.

## Images

No images are included. The panel's output is text rulings, prompt wording and counts, and the episode pictures in the source folder are picture-side reference sheets rather than evidence of craft. The sample is text only.

## Verdict

The panel's strongest result is a measurement, not an opinion. The brief the writer was given misstated the dialogue budget, which pushed book speech into the narrator's voice. The fix for the brief is built, and the sample shows what the change does on a second chapter. The gap between the two versions is one draft each, so it is a direction and not a rate.

Most of the adopted work is built and tested, with about 15,279 tests passing and none failing at the final commit. The rest of the panel's proposals are still open. Each one that changes pictures, voice or story taste is waiting on a sample: 30 items in all, mostly run on the writer's subscription, on the GPU in one idle window, or by the owner listening once. The studio owner's rulings on nine questions are the next step. Those rulings decide, for example, whether the dialogue ceiling should rise for heavily quoted chapters and whether the honest speech measure should replace the old one.

## What changed in the pipeline

Plain-language summary of the commits, in the order they landed:

- **Instruments:** a craft census that counts the defects above on every step-06 report; a provenance line in QC showing which takes were built from older wording; a replay harness over all plans on disk.
- **Brief and writer:** the brief now states the dialogue room as a share of the plan's own words, with a worked example; a documented rule that the inner-thought cap is a hard limit; a gap-mark check that refuses an ellipsis the book does not use; one scene per retold run in the screenplay input, with "where the chapter and the screenplay disagree, the chapter wins."
- **Shadow checks:** a speech verb on a face with no line; a narration line that repeats a quote; an orphan reply check; a paragraph-hole report; a reveal check against a hand-written schedule of when each face may be shown.
- **Picture text:** a closed set of hours for each setup (night, dawn, day, dusk, interior lamp), so one setup no longer carries both a sun and a night; fixes for doubled commas, a beat stamped on a block's final second, and an insert scope left open; a rule that an end line may not be a camera sentence; at the guidance setting where ComfyUI never reads a negative prompt, the grid now sends none, with a lint warning on negations; wording fixes for grid prompts; a warning above 350 words.
- **Operations:** a preflight at the start of a run that says "refuse now" or "will park at step N"; a cap of two re-draws per take and fault, with an owed-cure row after that; a count of cross-stage conflicts between the grammar and the hold cures; a load ledger for model changes; a read-only check of the machine's update and sign-in settings.

Two review passes found serious bugs in the builds, and each was fixed test-first. One change silently removed the light placement that the plan had chosen on four takes. Another changed the ledger so no row was ever written in production, because the job ran in a different process.

## Limits and open questions

- **The panel's votes are not independent evidence.** Ten agents read the same files and voted on the same proposals. Agreement among them shows the proposals were consistent, not that they are right. The rulings that matter are the ones with a measured number behind them.
- **The sample is n = 1 per version.** It was written by hand to show what the rules ask for. It is not a result from the writer agent and must not become a test fixture.
- **The GPU proof is pre-registered and has not run.** The rule: keep today's wording for the night takes only if at least 6 of 8 renders pass four checks against the delivered take, which are the hard-fault count, the face-similarity drop, the brightness of night frames, and the light side on one day close-up. If fewer than 6 pass, the night style line goes back to naming its source. The source folder contains no results for this proof.
- **The subscription draft arms (T1 to T11) have not run.** Each needs three drafts per chapter and a stop if the five-hour usage limit is hit.
- **The G-STOLEN cure is blocked on the owner.** Its approved fires are real relays of the book's speech, so a rule that moves narration back to its speaker could also move correct text.
- **A dial ceiling of 0.35 may be wrong for heavily quoted chapters.** Chapter 1 is about 64% quoted. The owner has not ruled on whether the ceiling should follow it.
- **Two review findings on the repeat-fault cap remain open.** The count never resets after a plan cure rewrites a shot's motion, so the new take gets no re-draw for that fault. And a take capped on one fault kind also gets no re-draw for a new fault kind. The owner must rule on the second.
- **Episode 01 is frozen.** Its delivered takes were not re-rendered. The wording fixes apply to the next episode only, so the census counts on episode 01 describe the past, not a fix.
- **The architecture page was not republished.** The claude.ai copy of the architecture page was three changes behind the file after the operations wave, and the session that owns the page must republish it.
- **The eleventh seat is not an expert.** The gavel ruled on the votes and wrote the dissents into its ruling as a section of their own.

## Sources

- RULING, craft and process panel (2026-10-21)
- SAMPLE, ch2 "Search for Mr. Hyde", version A against version B (2026-10-21)
- PREREG, craft wave-2 night-prompt proof (2026-10-22)
- WAVES 0-1, craft ruling build report (2026-10-21)
- WAVES 2-3, craft ruling build report (2026-10-21)
- Round 1 expert files, ten seats: screenwriter, dialogue writer, narration and voice-over, series composer, storyboard prompts, take prompts, process engineer, judges designer, audience, skeptic (2026-10-21)
- Round 2 expert votes, same ten seats (2026-10-21)
