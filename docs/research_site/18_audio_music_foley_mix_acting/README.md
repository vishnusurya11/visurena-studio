# Can an AI episode sound more cinematic? A pre-registered audio bench

**Date:** 2026-10-22 (Seattle time, PDT)

**Abstract:** We tested the music bed, ambience, Foley, dialogue acting, mix and cue sheet of one generated episode against rules written before any render. Nothing in production switched to a new engine. One real defect was fixed: music tones were never checked for singing. The bed engine and the acting engine wait for the owner's ear.

---

## The question

Can an episode sound more cinematic? That covers five parts:

1. The music bed under the story.
2. Ambience and Foley (the small sounds made by actions).
3. The mix, meaning how loud each part sits against the others.
4. The acting, meaning how each spoken line is delivered.
5. The cue sheet, meaning the timing of music changes at the turn of a scene.

The work had a hard budget. Everything had to fit in 80 GPU minutes, plus two listening sessions of about 10 minutes each for the owner.

## What existed before

- **Music bed.** The production bed is ACE-Step 1.5 turbo, an MIT-licensed music model. The older YuE2 model can still be reached with a flag, but it is not the default.
- **Loudness.** Dialogue lines sit at -16 LUFS. The final master lands at -14 LUFS. The master window is -15.5 to -12.5 LUFS, with a true peak of -1.5 dBTP.
- **Dialogue.** IndexTTS2 speaks each line. Each register (a named tone of voice) has one fixed 8-axis emotion vector.
- **Ambience.** A 9-second loop repeats under each scene.
- **Foley.** Stable Audio 3 makes the sound on each measured motion onset.
- **Earlier YuE2 test.** On 2026-10-16 and 2026-10-17, YuE2 ran in a setting called cot=off. It stayed unsung on one cue and sang on the other (2 of 2). The native no-ABC setting passed 3 of 3. A docstring in the code still said cot=off had never been run. That was stale.

The ruling found five premises in the brief that were wrong. The corrected facts:

| What the brief said | What the code and files show |
|---|---|
| The bed is YuE2. | The bed is ACE-Step 1.5. YuE2 is reachable with `--bed=yue2`. |
| YuE2 cot=off was never run. | It was run on 2026-10-16 and 2026-10-17. It sang on 2 of 2 cue renders in that setting. No owner listen was recorded for any YuE2 file. |
| The duck is a fixed 4 dB. | The duck code is built to adjust by bed level. On the shipped Jekyll episode, all 22 lines sat at the 4 dB minimum, so it never engaged. |
| The post chain lands at -20 LUFS. | Lines sit at -16 LUFS and the master lands at -14 LUFS. -20 was the level before the final lift. |
| Widen the step-matching regex so a cane is laid per strike. | The one cane cue in the shipped work has no walker. The regex would find no heel strike and fall back to the planned time. The real defect is "one motion peak per cue". That went to a bench. |

## Method

**Expert panel.** Ten expert agents, each on Sonnet, covered audio ML, composing, dialogue editing, Foley, mixing, music supervision, retention, skeptic review, sound design and voice direction. Each expert wrote a round-one brief (`r1`). Then there was a second round (`r2`). Ten experts over two rounds gave 20 reports.

**Gavel.** An Opus agent acted as gavel. It read the reports, decided what was adopted, rejected or sent to a bench, and wrote the ruling and the pre-registration.

**Pre-registered benches.** The rules were written at about 04:50 PDT. The rule file was last changed at 04:48:30 PDT, and the first GPU render started at 05:36:39 PDT. The skeptic checked these times. Rules could not change after a bench's first render. A change would have meant a new bench.

**Skeptic.** An Opus skeptic attacked the ruling and the bench. It recomputed the numbers from the raw files, read the code that the premises cite, and reported nine major findings (see Limits).

**Builder.** An Opus builder wired the adopted items. Each change was written as a failing test first, then the code.

**Blind-listen protocol.** Each listening pair is three parts: clip one, a short beep, then clip two.

- The two sides are matched in loudness to within 0.3 LU (loudness units).
- A sealed key is written, and its SHA-256 hash is recorded before anyone listens. The hash proves the key was not changed later.
- The owner scores the pairs by naming the first or second clip.
- The scoring rules are binomial. For example, 6 of 6 correct gives p = 0.016, and 10 of 12 correct gives p = 0.019.

**Test material.** Almost all tests used one episode of the Jekyll and Hyde series (ep01). It has three scenes in the music test (S1, S2, S3), 22 dialogue lines, and six Foley clips. The series is public-domain text, and the book names are used freely here.

**Hardware and budget.** One local GPU, through ComfyUI. The GPU budget was capped at 80 minutes. The plan was 64 minutes. 26.7 minutes were used.

## Results

Each table shows the numbers from the bench report. The verdict column follows the registered rule.

### B1. Music bed engine

Walls: W1 means no sung renders. W2 means the live (non-silent) share is at least 0.75 of the asked length. W3 means the warm time is at most 120 s per bed.

| Arm | Renders | W1 sung refusals | W2 min / mean live share | W2 failures | W3 warm mean gen | CLAP own-tone rank mean (1 = best) | Rank-1 share | Bed LRA / 3 s std (levelled) | Cut-to-beat within 80 ms |
|---|---|---|---|---|---|---|---|---|---|
| A ACE 1.5 turbo (production) | 8 | 0 | 0.63 / 0.76 | 4 of 8 | 2.8 s | 2.12 | 3 of 8 | 12.8 / 4.9 | 0.35 (n=5 scenes with beats) |
| B ACE 1.5 XL turbo | 8 | 0 | 0.82 / 0.87 | 0 | 2.9 s | 1.75 | 3 of 8 | 7.8 / 2.8 | 0.17 |
| C YuE2 native no-ABC | 10 | 1 | 0.94 / 0.98 | 0 | 5.3 s (first, cold render 93.5 s) | 3.40 | 1 of 10 | 7.1 / 2.6 | 0.44 |
| D HeartMuLa 3B | 0 | not run | | | | | | | |

- Production failed the W2 wall on 4 of 8 renders. The bench applied W1 and W2 to the challengers only and reported production's numbers beside them.
- One YuE2 render, `C_S1t_s101`, sang. The other nine did not.
- HeartMuLa did not run. Its node needs a package the ComfyUI Python lacks, and installing it would change that environment.

**Verdict.** Only ACE XL turbo (B) passed all the walls. It got six listening pairs. YuE2 failed W1 and got no registered pairs. It was also blocked by its licence.

### B2a. Foley (HunyuanVideo-Foley XL against Stable Audio 3)

Rule: within 80 ms of the measured onset on at least 5 of 6 clips. Non-silent on at least 5 of 6. CLAP rank 2 or better on at least 4 of 6. Zero words on every clip.

| Rule | Needed | Got | Result |
|---|---|---|---|
| Within 80 ms | 5 of 6 | 2 of 6 | Fail |
| Non-silent | 5 of 6 | 5 of 6 | Pass |
| CLAP rank 2 or better | 4 of 6 | 6 of 6 | Pass |
| Zero words | 6 of 6 | 0 of 6 (1 to 10 words on every clip) | Fail |

Per-clip detail (Hunyuan arm C after level repair, against the recorded arm A):

| Clip | Raw LUFS seeds 1-4 | C (level-repaired) seed, gain | C onset errors (ms) | Within 80 ms | CLAP rank (C / A) | Whisper words on C | A error |
|---|---|---|---|---|---|---|---|
| T03 footsteps, 4 events | -48 / -41 / -46 / -52 | 1, +20.3 dB | -125, +80, +28, +100 | no | 2 / 1 | 4 | recorded 2026-10-16: -24, -73, -73, -280 |
| T06 boot stamp | -42 / -61 / -34 / -49 | 1, +15.0 | -42 | yes | 1 / 3 | 2 | recorded: +1 |
| T09 key then door | -70 / -38 / -26 / -42 | 2 (seed 1 silent), +12.3 | no onset, +40 | no | 1 / 1 | 1 | recorded: -1, -41 |
| S12 gold coins | -16 / -21 / -14 / -23 | 1, -5.3 | no onset within 300 ms | no | 1 / 1 | 2 | 0 by construction |
| S17 cane on wood | -26 / -32 / -21 / -18 | 1, +3.2 | no onset (seed 2: +140) | no | 1 / 1 | 2 | 0 by construction |
| S27 match | -63 / -61 / -63 / -39 | none under 2 rerolls (seed 4 is the third reroll), +24 (cap) | -21 | yes | 1 / 1 | 10 ("yeah yeah yeah") | 0 by construction |

**Verdict.** Fail. Stable Audio 3 stays on the measured onset. Hunyuan is also blocked by its territory clause (see Licences).

### B2b. Ambience loops

Arm A is the shipped 9-second loop. Arm B is two different seeds alternating. Arm C is an eventless bed with spot sounds. Arm D is HunyuanVideo-Foley. The test is the autocorrelation at a 9-second lag. Lower is better. The rule was that B and C must halve A's value or better.

| Setup | A autocorr 9 s | B (two-seed) | C (eventless + spots) | C spots placed | Gap floor A / C (LUFS) | CLAP rank A / B / C | D (Hunyuan) |
|---|---|---|---|---|---|---|---|
| amb_cc179f0d (22.2 s span) | 0.995 | 0.028 | 0.865 | 1 of 3 | -36.4 / -36.8 | 1 / 1 / 1 | 8.7 s clip, -41 LUFS, rank 2 |
| amb_4521711b (14.4 s) | 1.000 | 0.010 | 0.969 | 0 of 3 | -36.0 / -37.4 | 1 / 1 / 3 | 4.4 s, -19 LUFS, rank 1 |
| amb_3469bed7 (36.9 s) | 0.995 | 0.027 | 0.880 | 1 of 3 | -37.1 / -36.8 | 3 / 1 / 2 | 5.8 s, -47 LUFS, rank 3 |

- **B passes** on all three setups. Its autocorrelation is far below A's, and its CLAP rank is never worse. It costs about 1.5 s of GPU per setup.
- **C fails.** The eventless bed is still a 9-second loop (0.87 to 0.97). Only one or two spots fit between the line windows. CLAP is worse on two of three setups.
- **D cannot be tested** on the 9-second lag, because its clips are 4.4 to 8.7 seconds long. It is also licence-blocked.

**Verdict.** B passes. It is an owner sample only (Listen 1, pairs P10 to P12). Not wired.

### B3. Dialogue delivery (IndexTTS2 and challengers)

Arm A is production (IndexTTS2, alpha 0.8). Arm B1 is alpha 0.6. B2 is alpha 1.0. C is emo_text (a text-driven emotion control). D is a new menace and dry vector set. E is Chatterbox. The lines are five Hyde lines (H1 to H5) and five Utterson lines (U1 to U5), each rendered with two seeds. Walls: the speaker gate must pass at least 18 of 20 renders, and the word error rate (WER) must be within A + 2 points.

| Arm | Renders | Gate pass (ECAPA 16 kHz, cast margin 0.08, feeling drop 0.12) | Mean WER (whisper large-v3-turbo) | Wall | Duration vs A | f0 range (st) | RMS dynamics (dB) | Pitch lift H3 / H5 over calm (st) | Mean margin | GPU s per audio s |
|---|---|---|---|---|---|---|---|---|---|---|
| A alpha 0.8 (production) | 19 (one capped, see Limits) | 19/19 | 0.0 % | baseline | 1.00 | 9.6 | 7.3 | +3.8 / +3.4 | 0.369 | 3.0 |
| B1 alpha 0.6 | 20 | 20/20 | 1.0 % | pass | 0.99 | 10.1 | 7.2 | +1.8 / +2.0 | 0.356 | 2.8 |
| B2 alpha 1.0 | 20 | 20/20 | 0.4 % | pass | 0.99 | 10.4 | 7.6 | +7.4 / +5.1 | 0.335 | 2.8 |
| C emo_text | 20 | 20/20 | 2.08 % | fail (A + 2 = 2.0) | 0.98 | 8.6 | 7.2 | -0.9 / +6.5 | 0.364 | 6.0 |
| D new menace/dry vectors | 20 | 20/20 | 0.5 % | pass | 0.95 | 8.8 | 7.2 | +2.6 / +1.5 | 0.364 | 2.8 |
| E Chatterbox (exaggeration 0.7 / cfg 0.3 for Hyde; 0.4 / 0.5 for Utterson) | 20 (4 ComfyUI, 16 CPU) | 20/20 | 0.0 % | pass | 1.18 | 11.8 | 7.6 | +6.8 / +6.5 | 0.394 | 5.0 (CPU path 12 to 54 s per line, not comparable) |

- B2 (alpha 1.0) gave the biggest menace pitch lift and stayed inside the speaker gate on every line. Its mean margin fell from 0.369 to 0.335, still about four times the 0.08 wall.
- C (emo_text) followed its text on H5 but not on H3. It also took twice the GPU time.
- E (Chatterbox) had the widest pitch range and the best margin. It reads 18 percent longer, and it adds a Perth watermark to each output.

**Verdict.** Two challengers, both pending the owner's ear: X is B2 (alpha 1.0) and Y is E (Chatterbox). Had E failed the walls, Y would have been B1. Rule: a challenger needs at least 10 of 12 blind wins. 9 of 12 is only a lean.

### B4. Mix chain (CPU)

Arm A rebuilds the shipped Jekyll episode. Arm B is one room tone on the dialogue. Arm C is the same room with a stereo pan on Foley.

| Wall | A | B (room) | C (room + pan) | Rule |
|---|---|---|---|---|
| Integrated after AAC 192 | -14.0 | -14.0 | -14.0 | -14 ± 0.3 |
| True peak after AAC | -1.9 | -1.7 | -1.7 | ≤ -1.5 |
| 1-4 kHz voice-over-rest | 15.16 dB | 15.22 | 15.22 | within 1 dB of A |
| WER (whisper on the master, 249 words) | 5.44 % | 2.93 % | 6.69 % | ≤ A + 1 |
| ECAPA, dialogue + room vs dry (14 lines): change in cast margin | | -0.026 to +0.048 | same | within 0.05 |
| Mono-fold loss, lines | 0.00 LU | 0.02 | 0.02 | ≤ 1 LU |
| Mono-fold loss, cues alone | 0.11 | | 0.11 | ≤ 1 LU |
| H3 / gate wavs byte-identical (23 files) | | yes | yes | yes |

- **Rebuild check.** Arm A matched the shipped mix at 0.0 LU. The skeptic notes that both are normalised to -14, so this check is weaker than it sounds.
- **Room.** Room passes every wall. All 14 dialogue lines on this episode are classed "exterior", so the bench tested one room, not four.
- **Pan.** Pan was measured as the centroid of camera-compensated motion. Measured pans were between -0.05 and +0.08. The cap was 0.3, so arm C was nearly arm B.
- **C fails WER** by 0.25 points, which is three words. B and C differ by at most 0.08 in pan, so the bench calls this ASR noise.
- **Finding.** The shipped stereo bed loses 2.4 LU when folded to mono. The cues lose 0.1 LU. On a phone speaker the bed is quieter than the stereo master suggests.
- **Audit of production.** Voice-over-rest in line windows has a median of 17.0 LU. 41 percent of the 22 lines sit under 16 LU. None sit under 12 LU.

**Verdict.** Room passes. It is an owner sample only (pairs P07 to P09 in Listen 1). Pan fails WER by 0.25 points and is not wired.

### B5. Cue sheet at the turn (CPU)

The turn is the bed change into the thrilling section at 35.33 s, on shot 7.

| Rule | Result |
|---|---|
| Dip ≥ 12 dB over the 1.5 s before the turn | Applied gain reaches -12.0 dB at the cut. Measured: -9.4 dB at 0.5 s before, -11.7 dB at 0.15 s before. **Fail by 0.3 dB.** |
| Hit offset in [-0.1, 0] s | -0.05 s. **Pass.** |
| Master within 0.5 LU of A | 0.00 LU. **Pass.** |
| Voice-over-bed not lower on any line | **Fail.** Line 6 (starts 35.58 s) falls from 32.6 LU to 19.3 LU, a drop of 13.3 LU. Lines 5 and 7 go up (+0.8 and +1.5). |

The cause is that the new tone enters at full level on the cut. Its loud opening lands under the first 0.7 s of line 6. Production crossfades the same tone in over 2 s, so its opening is spent before the line. The constants fit one episode.

**Verdict.** Fail. Not wired.

### B6. Foley strikes and sound kinds (CPU)

- **(a) Wider sound-word vocabulary.** There were 164 cues in 42 shipped plans, 136 distinct strings. Only four are footstep strings, and they stay footsteps under the wider list. The wider list made one new false positive ("slipping plaster running and smashing down a heap of debris"). A refined list had zero false positives and zero real gains. **No case for the change.**
- **(b) k-th onset to k-th motion peak.** On gold coins there are four onsets and two peaks. Two onsets land 160 ms and 370 ms from a peak. **Fail.**
- **(c) Strike variation.** Varying each strike by ±1.5 dB and ±4 % pitch changed neighbour correlation by -3.5 % (child steps) and +4.1 % (boot heels). The rule needed 30 % lower. **Fail.** Production never repeats a slice back to back with four strikes.
- **(d) Shared strike times.** Shot 7 lays boot heels and a child's running footsteps on the same four strike times (36.073, 36.566, 36.893 and 37.240 s). This was confirmed.

**Verdict.** Findings only. No fix proposed.

### B7. The "!" delivery rule (replay, not a measurement)

A line that ends in "!" with no written delivery is voiced as shouting (+3 dB, angry and afraid vectors, pitch lift). This is a deliberate cure that dates from 2026-09-26.

| Book | Lines ending in "!" with no written delivery | Lines in the book's shipped plans |
|---|---|---|
| Scarlet | 2 | 360 |
| War of the Worlds | 21 | 653 |
| Jekyll and Hyde | 0 | 22 |

- The 23 lines are: Scarlet ep13 line 4 (Watson) and ep14 line 22 (Holmes); WotW ep01 line 10; ep02 lines 8, 13, 15 and 22; ep03 lines 3, 12 and 17; ep04 lines 2, 4 and 15; ep06 line 27; ep08 lines 4 and 18; ep09 line 21; ep10 lines 6 and 23; ep11 line 10; ep12 lines 11, 16 and 20.
- Most read as real shouts in the text. WotW ep12 line 16 is narration, and it shouts. Scarlet ep14 line 22 is doubtful.
- This list was built by replay. The shipped files do not store the delivery, so no one checked what was rendered.

**Verdict.** The owner decides (T6 in the ruling). Not changed.

### B8. Hook audio against early retention

**Not run.** There is no retention data. The stored YouTube token has no analytics scope, and no analytics file exists for the three books. n = 0. The next step needs the owner's consent.

## What it cost

GPU time was timed from ComfyUI's job history. The lock was held from 05:36:28 to 06:09:01 PDT.

| Group | Jobs | GPU seconds |
|---|---|---|
| B1 ACE 1.5 (A) | 8 | 30.8 |
| B1 ACE XL turbo (B) | 8 | 26.0 |
| B1 YuE2 (C), first render cold: 93.5 s | 10 | 136.0 |
| B1 HeartMuLa (D), failed at node import | 1 | 1.0 |
| B2 Stable Audio 3 | 15 | 29.9 |
| B2 HunyuanVideo-Foley XL (27 renders + 20 s load) | 27 | 319.1 |
| B3 IndexTTS2 arm A (includes the 182 s capped cold load) | 20 | 316.2 |
| B3 arm B1 | 20 | 137.9 |
| B3 arm B2 | 20 | 134.5 |
| B3 arm C (emo_text) | 20 | 274.7 |
| B3 arm D | 20 | 130.0 |
| B3 arm E, Chatterbox on ComfyUI | 4 | 66.9 |
| **Total** | 193 | **1603 s = 26.7 min of the 80 min cap** |

Warm costs for the next planner: ACE 2.8 s, ACE XL turbo 2.9 s, YuE2 5.3 s, Stable Audio 3 2.0 s (ambience) or 1.5 s (spot), Foley 10.9 s, IndexTTS2 6 to 7 s per 2 to 4 s line, emo_text 12 to 13 s, Chatterbox 7 s on ComfyUI.

## Verdict

- **Nothing in production switched.** The bed is still ACE-Step 1.5. The dialogue is still IndexTTS2 at alpha 0.8.
- **One defect fixed.** Music tones were never checked for singing. A sung tone could ship. Every tone is now checked, and a sung one is re-rolled. This was the skeptic's finding M1.
- **Two open questions, waiting for the owner's ear.**
  - Which bed engine: production ACE or ACE XL turbo. YuE2 is blocked by its licence whatever it scores.
  - Which acting setting: alpha 0.8, alpha 1.0, or Chatterbox.
- **Dropped.** Foley (Hunyuan), the cue-sheet dip, and the strike changes failed their rules. Nothing from them is wired.
- **Rejected in the ruling.** Eighteen proposals were rejected with reasons. They included a re-run of YuE2, a dialogue pan, a level sweep, the de-esser, and a widened step regex.

## What was wired

| Commit | Subject (as written) | Plain meaning |
|---|---|---|
| e12b455 | Every tone of the toned bed is listened to, and one that sings is re-rolled like an empty one | Each music tone is checked for singing. A sung one is re-rolled, the same way an empty one already was. The stale YuE2 comment was corrected. Four lessons were added to the internal lessons archive. |
| 6f40d46 | The audio lessons sit under the archive's indexed sound-effects section, so the index names every archive section | The new audio lessons moved under the indexed section, so the index test passes. |
| 7a95cc1 | A re-run whose tone sings again no longer collides with the roll kept by the last run | A second assemble run no longer overwrites a kept sung roll. This was found in review. |

- **Cost.** The singing check adds one Whisper pass per tone at assemble. The time cost has been estimated but not yet measured on a real assemble.
- **Tests.** Before the last two commits, the full suite gave 15,361 passed, 2 failed, 9 skipped, 53 deselected and 10 xfailed. One failure was fixed in 6f40d46. The other is a stray control byte in two audit files outside this group. The suite was not re-run after 7a95cc1.

Not wired: the blind-listen kit, the CPU audits, and the hook screen.

## Limits and open questions

**The owner's listens are pending.** Listen 1 has 12 pairs. Listen 1b is an advisory set of 6 YuE2 pairs. Listen 2 has 24 pairs. Until the owner scores them, no engine or acting setting is chosen.

**Skeptic findings.** The skeptic reported nine major findings and ten minor ones. Here is how each stands.

- **M1, singing check missing.** Fixed in e12b455 (see above).
- **M2, the YuE2 test was not symmetric.** The 0.75 live-share wall was waived for production but applied strictly to YuE2. Production has a remedy (looping for short beds, re-rolls for sung ones). YuE2 is blocked by its licence, so this does not change the outcome. The advisory pairs were built from the renders that did not sing, and that is a selection.
- **M3, the duck is dormant, not dynamic.** The duck formula clamps to its 4 dB minimum at today's bed levels. The right description is "built, but dormant, with no measured need".
- **M4, the ambience test is true by construction.** The 9-second test compares two different seeds. A full scan of every lag found a repeat at 0.967 at 32.0 s in one B setup, and a partial echo at 11.5 s in another. The repeat period moved from 9 s to about 32 s. B is still probably better than A, but any ambience audit must scan all lags.
- **M5, Chatterbox used two pipelines.** Only 4 of 20 renders used the shipped ComfyUI workflow. The other 16 ran on the CPU with a direct call to the engine. Most of the Listen 2 Chatterbox pairs therefore used the CPU path. The mean cast similarity was 0.757 on the GPU path (n = 4) and 0.728 on the CPU path (n = 16). The GPU driver reset happened during a Chatterbox job.
- **M6, the WER wall sits inside ASR noise.** In B4, arms B and C differed by pans of 0.08 or less, yet their WER differed by 3.8 points. The wall cannot separate these arms. A next test would transcribe arm A twice to measure the noise floor.
- **M7, the "!" list is a replay.** The shipped files do not record the delivery, so the 23-line list is not what was rendered.
- **M8, the blind listens are sealed but not hidden.** The hash proves the key was not changed. It does not hide the key. Pair order in P01 to P06 follows scene and seed order, not random order. The kit must fix these before it enters the repo: the key must sit outside the listener's folder, there must be no arm-named files, and the pair order must be shuffled.
- **M9, the licence card was missing at the time of the skeptic's review.** A licence card has since been written. It covers ACE-Step 1.5 and Stable Audio 3 as well as the benched models.
- **Minor.** The CLAP probes use ACE's own tags, so they favour ACE. Rank-1 share was 3 of 8 for both A and B, so "B picks its own tone more often" is not supported at this sample size. YuE2's mean rank of 3.40 is at chance (3.0). Listen 2's instructions tell the listener which way to judge. Two different folders both use pair IDs Y01 to Y06 and Y01 to Y12, so scoring the wrong folder would give a wrong score without an error.

**Other limits.**

- **Single episode.** Almost all results come from one episode. The cue-sheet and room constants fit that episode. Quiet chapters of other books may behave differently.
- **More seeds than registered.** Foley used four seeds per clip where the rule called for two plus rerolls. The S27 clip was scored on its third reroll.
- **GPU incident.** The GPU driver reset at 06:08 PDT. ComfyUI was restarted at 06:17 PDT. The GPU lock was not returned for about an hour. Because of this, the two samples that needed the GPU (a calm re-render of the "!" lines and a strings-and-organ timbre sample) were not made. Sixteen Chatterbox renders moved to the CPU.
- **HeartMuLa did not run.** Its package is missing from the ComfyUI Python environment.
- **Retention is unmeasured.** No retention data exists yet.
- **Short clips.** Ambience and Foley are measured on short clips, not on full episodes.

**Audio files in this folder.** The four pairs in `audio/` are copies of owner test files. They are published as examples of the blind format. The owner has not yet scored them. Publishing them before the owner's listen can affect that listen. The sealed keys are not in this folder and are not published.

**Licences (facts from the licence files, not legal advice).** The questions below are open for the owner's counsel to decide.

| Model | Role | Licence, as read | Terms worth counsel's attention |
|---|---|---|---|
| ACE-Step 1.5 turbo | music bed (production) | MIT | The card says output may be used commercially. |
| ACE-Step 1.5 XL turbo | bed candidate, not shipped | MIT | Same family. |
| Stable Audio 3 medium | Foley and ambience (production) | Stability AI Community License | Free below US $1,000,000 annual revenue for the licensee and affiliates. Above that, an enterprise licence is needed. Attribution: "Powered by Stability AI" on a related page, and a copy of the agreement when distributing. |
| IndexTTS 2.5 | voices (production) | bilibili Model Use License | Worldwide and royalty-free. A separate licence is needed above 100M monthly active users or RMB 1 bn revenue. Outputs may not be used to improve other commercial models. |
| YuE2 | bed candidate, benched | CC BY-NC 4.0 | Non-commercial. |
| MERT2 | not used | CC BY-NC 4.0 | Non-commercial. |
| Fish Audio S2 pro | voice candidate, benched | Fish Audio Research License | Commercial use needs a separate licence. |
| HunyuanVideo-Foley | Foley candidate, benched | Tencent Hunyuan Community Licence | Does not apply in the EU, UK or South Korea. Output may not be used or displayed outside the territory. |
| HeartMuLa | bed candidate, did not run | apache-2.0 per its README | Not read further. |
| Chatterbox | voice candidate, benched | Node: Apache 2.0. Model: MIT per upstream (not read on disk). | Adds a Perth watermark to every output. |

Questions left for counsel: whether channel revenue counts toward the Stability revenue line, and whether a published episode counts as a product that uses Stable Audio 3 for the attribution clause. The full card was written by the group and sits in the audit folder.

**Scale.** The engine choice would be a per-book setting. Each engine costs seconds of GPU per bed. Ambience with a second seed adds about one render per setup per episode. A book-level pool of loops would bring that near zero after the first episode.

## Sources

Links taken from the expert round-one reports.

**Music models**
- ACE-Step 1.5 paper: https://arxiv.org/abs/2602.00744
- ACE-Step 1.5 code: https://github.com/ace-step/ACE-Step-1.5
- ACE-Step 1.5 model card: https://huggingface.co/ACE-Step/Ace-Step1.5
- ACE-Step (v1) paper: https://arxiv.org/pdf/2506.00045
- ACE-Step in ComfyUI: https://blog.comfy.org/p/ace-step-15-is-now-available-in-comfyui
- ACE-Step ComfyUI tutorial: https://docs.comfy.org/tutorials/audio/ace-step/ace-step-v1-5
- ACE-Step essentials: https://help.scenario.com/articles/2070476460-ace-step-1-5-audio-models-the-essentials
- ACE-Step setup guide: https://www.olares.com/docs/use-cases/ace-step-1.5
- YuE code: https://github.com/multimodal-art-projection/YuE
- YuE paper: https://arxiv.org/pdf/2503.08638
- YuE2 model page: https://huggingface.co/mrfakename/YuE2-3B
- YuE2 news: https://comfyui-wiki.com/en/news/2026-09-16-fl-yue2
- YuE2 review (secondary; songs, not beds): https://airmore.ai/tw/ai-review/yue2-3b-review
- HeartMuLa code: https://github.com/HeartMuLa/heartlib
- Stable Audio Open model card: https://huggingface.co/stabilityai/stable-audio-open-1.0
- Community ACE-Step discussion (anecdote): https://civitai.com/models/2946237 and https://vi-control.net/community/threads/ace-step-1-5-do-we-now-have-an-ethically-trained-suno-at-home.170009/
- Paper cited for emotion F1 ranking: https://arxiv.org/pdf/2603.24430 (partly author-reported)
- Paper cited in the reports: https://arxiv.org/pdf/2601.03888
- Paper cited in the reports: https://arxiv.org/abs/2601.10547
- Paper cited in the reports: https://arxiv.org/pdf/2505.17589
- Paper cited in the reports: https://arxiv.org/pdf/2508.16930

**Foley and sound effects**
- HunyuanVideo-Foley code: https://github.com/Tencent-Hunyuan/HunyuanVideo-Foley
- HunyuanVideo-Foley commit: https://huggingface.co/tencent/HunyuanVideo-Foley/commit/f3fda473b027296b5680981b10657d599763d5c9
- MMAudio code: https://github.com/hkchengrex/MMAudio
- MMAudio models note: https://huggingface.co/AEmotionStudio/mmaudio-models/blob/main/README.md
- Video-to-audio benchmark: https://paperswithcode.co/benchmark/vggsound-v2a
- Video-to-audio paper: https://arxiv.org/abs/2502.05139
- Video-to-audio paper: https://arxiv.org/pdf/2110.01763
- Video-to-audio paper: https://aclanthology.org/2025.naacl-demo.19.pdf
- Footstep variation (game audio, secondary): https://bugnet.io/blog/how-to-implement-footstep-variation-to-avoid-repetition
- Repetitive game audio (secondary): https://sounddesign.irpr.agency/solutions/game-audio-repetitive/
- Footsteps SFX (secondary): https://krotos.studio/blog/footsteps-sound-effects
- AI sound for video (secondary): https://www.creativeainews.com/articles/how-to-add-sound-effects-to-ai-video-2026/
- Foley article (secondary, Russian-language): https://habr.com/ru/articles/942412
- Ambience loops (secondary): https://sounddesign.irpr.agency/solutions/ambience-loops-obvious/
- Game soundscapes (secondary): https://splice.com/blog/audio-soundscape-for-video-games
- Ambient sound design (secondary): https://pixflow.net/blog/ambient-sound-design
- Ambient layering (secondary): https://pixflow.net/blog/ambient-sound-design-layering/
- Ambience sound effects (secondary): https://morphic.com/jp/resources/sounds/ambience-sound-effects

**Dialogue, emotion and voice**
- IndexTTS2 paper: https://arxiv.org/pdf/2506.21619 and https://arxiv.org/abs/2506.21619
- IndexTTS code: https://github.com/index-tts/index-tts
- IndexTTS 2.5 recipe: https://recipes.vllm.ai/IndexTeam/IndexTTS-2.5
- IndexTTS2 ComfyUI wrapper: https://github.com/snicolast/ComfyUI-IndexTTS2
- IndexTTS2 emotion guide (wrapper): https://github.com/EnidPinxit/TTS-Audio-Suite-COMFYUi/blob/main/docs/IndexTTS2_Emotion_Control_Guide.md
- Emotion2vec on synthetic speech: https://arxiv.org/pdf/2603.16483
- Fish Audio S2 licence: https://huggingface.co/fishaudio/s2-pro/blob/main/LICENSE.md
- Chatterbox code: https://github.com/resemble-ai/chatterbox
- Voice-over loudness study: https://arxiv.org/pdf/2006.14282 and https://salford-repository.worktribe.com/OutputFile/1488623
- Dialogue editing techniques (secondary): https://www.production-expert.com/production-expert-1/5-techniques-for-dialogue-editing-in-film-and-tv
- De-essing (reference): https://en.wikipedia.org/wiki/De-essing
- Dialogue mixing tips (secondary): https://digitalfilms.wordpress.com/2020/07/25/dialogue-mixing-tips/
- Dialogue match (secondary): https://www.provideocoalition.com/izotope-dialogue-match/

**Mix, loudness and ducking**
- YouTube loudness, creator sources (YouTube turns down only): https://youlean.co/?p=30813 and https://productionadvice.co.uk/youtube-loudness/
- YouTube loudness guide (secondary): https://youlean.co/how-to-edit-a-video-to-achieve-good-audio-loudness-on-youtube/
- YouTube LUFS guide (secondary): https://audioforgepro.com/blog/youtube-lufs-normalization-guide
- Audio normalisation (reference): https://en.wikipedia.org/wiki/Audio_normalization
- Ideal volume on YouTube (forum): https://forum.shotcut.org/t/ideal-volume-levels-for-audio-on-youtube-uploads/12293/13
- Loudness normalisation guide (secondary): https://www.soundbridge.io/loudness-normalization-a-mixing-and-mastering-guide
- Loudness levels (secondary): https://videvo.net/blog/?p=40770
- Ducking for dialogue clarity (secondary): https://www.production-expert.com/production-expert-1/using-ducking-to-improve-the-clarity-of-reverberated-dialogue

**Composing and spotting**
- Spotting a film (secondary): https://soundbridge.io/spotting-session-film
- Spotting (reference): https://en.wikipedia.org/wiki/Spotting_(filmmaking)

**Retention (industry blogs, secondary)**
- https://subscribr.ai/youtube-strategy/youtube-shorts-low-watch-time-boost
- https://www.opus.pro/blog/youtube-shorts-hook-formulas
- https://www.gofaceless.ai/en/blog/high-retention-youtube-shorts-attributes
- https://blitzcutai.com/blog/how-to-remove-silence-youtube-shorts
- https://digiday.com/sponsored/75-percent-of-people-watch-mobile-videos-on-mute/
- https://ads.tiktok.com/business/creativecenter/quicktok/online/Power_Creative_Elements/pc/en
- https://roirevolution.com/blog/july-2021-social-media-water-cooler/

## Files in this folder

- `README.md` (this page)
- `images/` holds the summary card (`00_SUMMARY.png`) and one card per bench (`B1_music_bed.png`, `B2_foley.png`, `B2_ambience.png`, `B3_delivery.png`, `B4_mix.png`, `B5_cue_sheet.png`, `B6_strikes.png`).
- `audio/` holds four blind pairs. Each file is clip, beep, clip. `pair_P01.wav` is the bed test (production against ACE XL turbo). `pair_P10.wav` is the ambience test. `pair_X02.wav` is alpha 0.8 against alpha 1.0. `pair_Y03.wav` is alpha 0.8 against Chatterbox.

![Summary card of all benches](images/00_SUMMARY.png)

![B1 music bed](images/B1_music_bed.png)

![B2 Foley](images/B2_foley.png)

![B2 ambience](images/B2_ambience.png)

![B3 dialogue delivery](images/B3_delivery.png)

![B4 mix](images/B4_mix.png)

![B5 cue sheet](images/B5_cue_sheet.png)

![B6 strikes](images/B6_strikes.png)
