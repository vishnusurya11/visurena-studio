# A voice bench that found a bug in our speaker gate

*Source date: 2026-10-21 (Seattle time).*

*We tested a new open-weight text-to-speech model against our production voice engine. The new model was too slow and crashed the engine on our shared machine, so production stayed. The bigger find was a sample-rate bug that had made our speaker-match check unreliable since September 2026. After the fix, it refuses all tested wrong voices and refuses 1 to 3 percent of real lines in held-out books.*

## The question

Our studio turns public-domain books into short AI-made video episodes. Each character has a voice, and a speech engine says every line. We asked two questions.

1. Is Fish Audio's Drama 3 (open weights, FP8 format) a better voice engine than our production engine, IndexTTS-2, for the Jekyll and Hyde episodes?
2. Does our automatic check that a line is spoken by the right character actually work?

Terms used below:

- **TTS**: text to speech.
- **FP8**: a compressed number format that makes a model smaller, so it fits in less memory.
- **ECAPA**: a neural network that turns a voice clip into a set of numbers (an "embedding"). Two clips of the same speaker should give similar numbers. We compare embeddings with a score between 0 and 1.
- **WER**: word error rate. We ran a speech-to-text model on each output and counted the words it got wrong.
- **RTF**: real-time factor. Seconds of compute per second of audio. Lower is faster.
- **Gate**: an automatic check that decides whether a generated line is kept or redone.
- **Floor**: the minimum speaker score a line must reach to pass.
- **Wall**: the time budget a pipeline step is allowed.
- **Ruler**: the exact way a score is measured. Changing the input changes the ruler.

## What existed before

Production used IndexTTS-2 for every speaker. A cast voice is designed once per character with a short reference clip. Each generated line is then checked by three things: a speech-to-text word check, a pace check, and the ECAPA speaker score against that character's design clip. The speaker floor is lower for lines with a strong feeling, such as threat or urgency, because emotion changes how a voice sounds.

Drama 3 was new and had been installed in our local ComfyUI setup. It had not been loaded or measured. Its maker advertises natural-language direction ("speak slowly and grave") and inline emotion tags.

No measure of acting or emotional fit existed in the studio. The only acting proxy in the plan was the spread of pitch.

## Method

**Arms.**

- **A, production.** IndexTTS-2 exactly as the production step calls it: the character's design clip as both voice and emotion reference, the register's emotion vector, the book's pronunciation list, then the same post-processing chain for both arms (high-pass filter, presence boost, loudness to -20 LUFS, limiter, short room tail).
- **B, Drama 3, directed.** The same design clip and exact transcript, with the register written as a director's note (for example "hushed and low, close to the listener, grave and unhurried").
- **B0, Drama 3, plain.** No director's note. This arm was planned as a control and never ran.

**Lines.** Nine lines from chapter 2 of the book: narrator 2, Utterson 2, Hyde 3 (threatening), Poole 1, Lanyon 1. Jekyll does not speak in that chapter. Two seeds per line per arm, the same seeds for every arm.

**Pre-registration.** The win rule was written in a PREREG file before any render. The file dates show the order: the rule was written first, then the measurement script, then the GPU lock, then the first render. The rule had three parts: the mean WER is within 2 points of production, the mean speaker score is within 0.03 of production, and the time fits the step walls. A listening test would decide prosody last. If any of the first three parts failed, production stayed.

**Measures.** Whisper large-v3-turbo for WER, scored with the production error-rate function and the book's pronunciation list. ECAPA scores against the design clip, both on the production ruler (the 24 kHz file fed as-is) and on a 16 kHz resample. GE2E (an older speaker model) as a second opinion. Clip length, RTF from the engine's job history, and loudness.

**Agents and debate.** The run had five roles. A bench agent ran the measures and wrote the report. Two critics wrote separate critiques, one from a skeptic's view (checking the numbers and the pre-registration) and one from an expert's view (checking the speech-model science and the speaker gate). A defender wrote a rebuttal that accepted or rejected each point. A judge (the "gavel") ruled on every claim and ran its own CPU check. That is one debate round: critique, rebuttal, ruling. The gate fix that followed was done by the main session, test first, and was not debated.

**Speaker-gate test.** For the side finding, every generated take and every episode line was scored against every other cast design in its book. A take is a false pass if a wrong voice clears that line's own floor. The same files were scored at 24 kHz (production) and at 16 kHz (the model's expected rate).

## Results

### Table 1. Voice bench, production versus Drama 3

Numbers are from the corrected bench card. Where the card and the first report disagree, the corrected card is used.

| measure | A, IndexTTS-2 | B, Drama 3 (directed) | better |
|---|---|---|---|
| speaker score, ECAPA at 16 kHz, line L01 (narrator) | 0.903 (2 takes) | 0.723 (1 take) | A |
| speaker score, ECAPA at 16 kHz, all 9 lines | 0.804 (18 takes) | not run | - |
| speaker score, ECAPA on the production 24 kHz ruler, L01 | 0.871 | 0.672 | void (see below) |
| speaker score, GE2E, L01 | 0.953 | 0.899 | A |
| word error rate, L01 | 0.0 points | 0.0 points | tie (n = 1) |
| word error rate, all lines | 0.4 points (18 takes) | not run | - |
| seconds for the same line (L01) | 13.0 s | 16.6 s | no winner (pace differs) |
| first job after a cold start | 296 s | 1,081 s, for one 16.5 s line | A |
| speed after loading (RTF) | 1.79 median (max 4.31) | 11.8, including first-call compile | A |
| engine survived the batch | yes | no (cause not proven) | A |
| takes finished | 18 of 18 | 1 of 18 (B0: 0 of 18) | A |

The first report said "1 of 54 planned takes finished". The judge corrected that to 19 of 54 finished, or 1 of 36 Drama 3 takes, since A had 18 finished and B0 had none.

On the 24 kHz ruler, Drama 3's one take scored nearer the Utterson design (0.694) than the narrator design (0.672). That ruler could not say whose voice that take was, so its speaker numbers are void. Only the 16 kHz row is used for speaker comparisons.

### Table 2. Pre-registered rules, after the debate

| rule | result |
|---|---|
| WER within 2 points of production | Not decided. The single Drama 3 take was word-perfect, but the rule needs a mean over 18 takes. |
| Speaker score within 0.03 of production | Not decided. On the 16 kHz ruler the gap is 0.18 (0.903 against 0.723), about 2.5 pooled take-to-take noise SDs. That is a hint, not a result. Drama 3's direction note also changed the pitch (1.7 semitones lower) and the pace (27 percent slower). Without the B0 control the two effects cannot be separated. |
| Time fits the 15-minute say wall | Fails for Drama 3. One 16.5 s line took 1,081 s. Even with zero load time, the measured speed after loading (RTF 11.8, which includes compile) projects about 1,055 s for an episode-sized run of 89.4 s of speech. |
| Time for production | Projected at 7.2 minutes in the report. The judge said that is a model's number. The measured first pass of episode 01 (22 lines plus listening) ran about 13 minutes by the run log, an estimate, under the 15-minute wall. |
| Prosody (listening test) | Open. The listening test was not blind when it was first made. A blind pair was prepared, but its result is not in the sources. |

**Verdict on the engine comparison.** Production stays. Drama 3 was rejected on operational grounds on this machine, on the day tested. The judge and both critics agreed that it says nothing firm about Drama 3's voice quality.

### Table 3. The speaker-gate bug (side finding)

Each row is a count of wrong-voice trials, or a property of the cast, measured on the production ruler (24 kHz read as-is) and on the 16 kHz ruler.

| measure | 24 kHz (production) | 16 kHz (correct input) |
|---|---|---|
| episode 01 shipped lines: a wrong voice clears that line's floor | 70 of 152 | 3 of 152 |
| episode 01 gated lines that some other cast voice also passes | 15 of 19 | 3 of 19 |
| bench takes: a wrong voice clears the floor (9-voice cast) | 105 of 144 | 7 of 144 |
| nearest cast voice is the true speaker | 37 of 40 | 40 of 40 |
| smallest margin, own design minus best rival | -0.086 | +0.100 |
| own design beats every rival by 0.08 | 24 of 40 | 40 of 40 |
| adult cast design pairs at or above 0.55 | 27 of 28 | 1 of 28 (Hyde and Lanyon, 0.648) |
| Hyde against Jekyll (a filed fault at ceiling 0.55) | 0.578, flagged as a fault | 0.061, not a fault |

The expert critic's smaller trial set (5 voices, 18 takes) gave an equal error rate of 11.1 percent on the production ruler and 0.0 percent at 16 kHz, with separation (d') 1.95 against 4.66. Zero errors in 18 takes means none were seen, not that none exist. The skeptic's count of 62 of 72 false passes on the same 5-voice set is the same finding on a smaller set.

Two other facts matter. The expert found the ECAPA model's own documentation says its input must be 16 kHz, and the speech library's input function does not resample. Every file in the test was 24 kHz, so every score was wrong in the same way. The same ECAPA model with the correct input is about as good as the older GE2E model it replaced (d' 4.66 against 5.25, not separable at this sample size).

### Table 4. Gate constants re-set on the 16 kHz ruler

Calibration used the owner-watched published episodes of three books (Scarlet, War of the Worlds, Jekyll and Hyde episode 01): 411 calm lines of 2 seconds or more and 9,809 wrong-voice trials.

| constant | old (24 kHz) | new (16 kHz) |
|---|---|---|
| same-speaker threshold | 0.55 | 0.60 |
| self-similarity floor | 0.65 | 0.45 |
| nearest-design ceiling | 0.80 | 0.75 |
| calm floor, 4 s or longer | 0.70 | 0.60 |
| calm floor, 2 to 4 s | 0.65 | 0.55 |
| split-voice floor (same speaker's lines) | 0.70 | 0.53 |
| feeling drop, one line | 0.20 | 0.12 |
| feeling drop, a pair of felt lines | 0.20 per line | 0.17 once per pair |
| cast margin (new) | none | 0.06 |

The 0.06 cast margin means a line's own cast design must beat every other cast design of its book by at least 0.06. Lines under 2 seconds are not held to the margin, because the encoder cannot measure them that short.

### Table 5. Gate after the fix

| book | real lines passed | wrong voice from inside the cast passed | voice from outside the cast passed |
|---|---|---|---|
| Scarlet (300 lines) | 300 of 300 | 0 of 8,093 | 18 of 8,093 |
| War of the Worlds (92 lines) | 92 of 92 | 0 of 1,564 | 1 of 1,564 |
| Jekyll and Hyde (37 lines) | 37 of 37 | 0 of 296 | 10 of 296 (13 with the old 0.20 drop) |

Held-out check (one book left out each time, with the constants set on the other two): real lines refused were 3 of 300 (Scarlet), 0 of 92 (War of the Worlds) and 1 of 37 (Jekyll). Wrong voices from inside the cast passed in 0 of every book. So a fresh book should expect about 1 to 3 percent of real lines to be refused, which costs a retake, not a shipped fault.

The "outside the cast" row is a voice that belongs to nobody in the book. The margin cannot see it, and the floor stops most of it but not all. A second check, comparing a line with the same speaker's other lines, is the next guard. Its own overlap is discussed under limits.

## Images

![The first bench card, now superseded. It shows the FAIL on the speaker rule and the 24 kHz speaker row that the debate later called void.](images/bench_card_v1_original.png)

![The corrected bench card. Read the 16 kHz row first, read the WER tie as n = 1, and note the void rows.](images/bench_card_v2_corrected.png)

![The speaker-gate bug on the shipped episode 01 lines. The left column is production's 24 kHz input, the right column is the same files resampled to 16 kHz. Look at the impostor counts, 70 of 152 against 3 of 152.](images/speaker_gate_24k_vs_16k.png)

Audio, for listening (relative links; every take was normalised to -20 LUFS by the same post chain):

- [A, then a beep, then B: IndexTTS-2 then Drama 3, narrator line L01](audio/narrator_A_beep_B_drama3.wav). The order and labels are known to the listener, so this is not a blind test.
- [A alone: IndexTTS-2, narrator line L01](audio/L01_narrator_A_indextts2.wav)
- [B alone: Drama 3 directed, narrator line L01](audio/L01_narrator_B_drama3.wav). It is about 3.6 seconds longer than A.
- [All nine production lines, including Hyde's threatening lines L05 to L07](audio/all_9_lines_production.wav)

## Verdict

- **Keep IndexTTS-2 in production.** The reason is operational: on this shared machine Drama 3 took too long and crashed the engine. It is not a verdict on Drama 3's voice.
- **Drama 3 is not yet judged on voice.** One directed take, against no plain control, on a broken ruler, is not a result. Its acting was never measured.
- **The speaker gate was broken.** It used the wrong sample rate from September 10, 2026, so the check could not reliably tell characters apart. On episode 01 a wrong voice would have passed 70 of 152 times. Read correctly, it passes 3 of 152.
- **The gate is fixed on the tested books.** It uses a 16 kHz input, re-set thresholds, and a cast margin. It passes every real line in the tested books and refuses every wrong voice from inside the cast.
- **A false alarm was also removed.** A filed rule had flagged Hyde as sounding like Jekyll (0.58). On the correct ruler they score 0.06 apart.

## What changed in the pipeline

Two commits, both on the same day:

- **68079e2, the 16 kHz speaker ear.** The speaker model now receives 16 kHz audio. The file records which ruler produced each score, so old and new scores are not mixed. Thresholds were re-set on the new ruler. A cast-margin rule was added. Three new tests were added: a kept take must be the one in its own voice; a felt line keeps a floor that separates voices; two designs are twins only on one line.
- **8557cbb, review fixes.** Two reviewers found three faults in the first commit. The kept take was still chosen by raw score, so a take in another character's voice could ship. A failing redo could replace a passing take. The feeling drop had been left at its old value, which let an outside voice pass 13 times in 296 trials. The reviewers also found that the cast-check printout compared the wrong kind of score. Each was fixed. The feeling drop was reduced to 0.12, and the printout now uses the design gate's own ceiling of 0.75.

Test result after the change: 15,088 tests passed, 3 failed, 9 skipped. The three failures were in unrelated areas (a skill-size check, a command-table check, and a writer contract test under peer work in progress), and two of them passed on re-run. The 157 voice tests, including the real-audio ones, passed.

## Limits and open questions

- **Sample size.** One book, nine voices, 18 production takes, one Drama 3 take. Every headline comparison is on that. The speaker-gate result is strong because it is a bug with a cause that is visible in code and documentation. The bench result is weak.
- **Drama 3 control missing.** The plain arm (B0) never ran, so the direction note and the model cannot be separated.
- **Acting not measured.** Emotion-matching and naturalness measures (for example emotion2vec, UTMOSv2, WavLM speaker verification) were not installed. Installing them is a download that the studio owner must approve.
- **Listening test not blind.** A blind pair was prepared, but it was byte-identical to the labelled pair files, so publishing it would have revealed the answer. It has been left out of this page. The answer key stays with the owner. A blind test needs freshly shuffled files.
- **Cause of the ComfyUI crash not proven.** The memory state was not saved, no crash trace was written, and Windows logged no low-memory event. Memory pressure is the likely cause. The fair retry needs a fresh engine restart, at least 50 GB of free RAM, the model file on the fast system drive, and two seeds per line with the plain control included.
- **Load time not split.** The 872-second load window mixes disk reads, memory paging and voice encoding. The disk alone does not explain it: 38.6 GB in 872 seconds is about 44 MB/s, slower than a plain sequential read.
- **Outside voices still pass some.** Under the fix, 18 of 8,093 outside-cast trials pass in Scarlet, 1 of 1,564 in War of the Worlds, and 10 of 296 in Jekyll and Hyde. A split-voice check is the next guard, but its thresholds overlap: calm pairs of different speakers reach 0.573, and the worst real same-speaker pair is 0.567. No single threshold separates them.
- **Untested backstops.** The self-similarity floor (0.45) and the nearest-design ceiling (0.75) have no known bad design on the new ruler, because no bad design has been rendered to test them.
- **Close casting pair.** Hyde and Lanyon score 0.648 on the correct ruler, the closest real pair. Whether that is too close for the owner's ear is open. Lanyon and Enfield (0.547) are next.
- **Feeling drops rest on one book.** The feeling-line drops were set on 24 feeling lines from one book and one engine. Scarlet and War of the Worlds have no feeling lines. How to measure acting is the owner's decision.
- **Publishing.** A short note on the sample-rate bug, with a small checker that measures equal error rate and separation at native and 16 kHz for any cast, is a candidate public artifact. Nothing has been published. The studio's standing rule is that public work needs the owner's go.
- **Retry of Drama 3.** It needs a download of about 32.7 GB for the smaller FP8 variant and one GPU window of roughly 45 minutes with the series paused. The studio owner has not decided.

## Sources

- REPORT, voice bench of Drama 3 against production (2026-10-21)
- PREREG, voice bench pre-registration (2026-10-21, written before any render)
- DEBATE, skeptic critique of the voice bench (2026-10-21)
- DEBATE, expert critique of the voice bench and speaker gate (2026-10-21)
- REBUTTAL, defender's answer to both critiques (2026-10-21)
- VERDICT, judge's ruling on the claims and the debate (2026-10-21)
- CALIBRATION, voice gate re-set on the 16 kHz ruler (2026-10-21)
- RESULT, voice gate fix: what was wrong, what changed, suite result (2026-10-21)
- Corrected bench card and speaker-gate card (2026-10-21)
