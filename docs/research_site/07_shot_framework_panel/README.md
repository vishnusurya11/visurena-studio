# How a ten-seat expert panel decided the camera grammar for an AI-animated episode, and what the bench said

Date: 2026-10-21 (source folder date; the rulings and bench runs were made the same day)

*A panel of ten specialist "seats" argued over which camera shots an AI video model can hold, measured the disputed moves on a local GPU, and kept only the rules the measurements supported.*

## The question

Visurena Studio makes short episodes from public-domain books. Each episode is a sequence of AI-rendered shots from MiniMax-H3, a video model that takes reference pictures (ref2va, reference-to-video). A "frozen" take is one where the picture hardly changes. In the first Jekyll and Hyde episode many takes stayed frozen for most of their length (78 to 95 percent of frames on the disputed takes). The studio owner asked for normal shots with more movement: establishing shots, a bird's-eye view, and more action inside a shot.

The question for the panel was narrow: which camera moves can the video model actually follow on our path, which of them should the writer be allowed to ask for, and which prompt defects are making the model ignore the camera request?

## What existed before

- **The take gate and the stillness meter.** Each rendered take is scored by a gate (a 0 to 100 score with hard fail rules). A separate meter measures how many frames are frozen. A take that is frozen for 5 seconds or more is refused.
- **An anime-TV framing grammar.** A written house rule capped camera pushes at 2 per episode and asked that at least half of the shots be locked-off. The rule is coded in the framing grammar module.
- **A camera catalogue.** Each camera move (pan, tilt, push, pull, crane, follow, locked) is a catalogue row, and every camera sentence in a prompt must map to one catalogue row.
- **Prompt-writer defects.** Before this work, the text sent to the model had several contradictions: the camera's "holds" was rewritten to "keeps", a closed mouth sat beside a speech verb, and night setups were given a sun clause.
- **Earlier results.** A prompt bench (also on 2026-10-21) had found that a held shot turned into a slow push on one take, and that a walk written as ordered beats froze on the model. The panel was asked to rule on those findings.

## Method

**The panel.** Ten seats, each a specialist lens: action choreographer, anime director, cinematographer, editor, H3 empiricist (the video-model measurement specialist), pipeline engineer, prompt engineer, skeptic, story adapter and storyboard lead. A presiding "gavel" role ran the rounds and wrote the rulings.

**The rounds.**

1. Round 1: each of the ten seats filed a written position (ten files). One earlier draft of the prompt engineer's position was superseded and is not counted.
2. Round 2: each of the ten seats answered the others' positions (ten files). The skeptic's round-2 file is the one that set the admission rule for shot types.
3. Gavel ruling, round 1: the presiding role wrote a ruling that settled the four prompt-bench findings, listed what was adopted, benched and rejected, and pre-registered the bench.
4. Bench: eight GPU renders in round 1, run after the pre-registration was written.
5. Final ruling: the presiding role ruled again on the bench, and wrote the shot framework (adopted shot types, rules and a research plan).

So the panel ran two debate rounds, one gavel ruling before the bench, and one ruling after it.

**Standard of proof.** The gavel's rule for "adopt" was strict. A shot type is adopted only if the move has run on our own path (through the take gate or by eye on a bench) and no measurement on that path contradicts it. A move with a plausible mechanism but no proof is "benched". A move with a contrary measurement, a hard wall it must break, or a standing owner complaint is "rejected".

**Bench 1: shot bench (round 1).** Eight renders, each 121 frames (about 5 seconds) at 768 by 768. Two graphs were used: Wuli (an 8-step graph, for insert to medium shots) and Spark (Singularity v1.3 pruned plus a Ref2V LoRA at 1.0/0.7, for full and wide shots). Each arm used the same first picture, and seeds were fixed (seed 1 is the delivered seed, seed 2 is seed 1 plus 1000).

- Arm B1, six renders on two held takes (T10 medium two-shot, T15 medium close): one locked control and two "slow push" seeds per take.
- Arm B2, two renders of a walk on the T06 full shot: the walk bound to the camera "across the whole shot", against the delivered take.
- A pre-registered win rule for a push: the frozen share below 0.45 and at least 0.20 below the control, the actor moving at least as much as the control, the camera really pushing, no head or hat cut by the frame edge, end-to-first face ratio at most 1.6, no identity loss beyond 0.05, and no extra or duplicated people.

**Bench 2: implement proof.** Five delivered episode-one takes (T06, T10, T13, T15, T26) were rebuilt by the changed prompt writer and re-rendered at their delivered seed, with the same measures. Pass rule: frozen share at most 10 points above the delivered take, the camera keeps its direction, faces keep their pixel size and face-match score within a small margin, no new clones, and the take gate no worse. A failed take got one more render on seed plus 1000. If it failed the same term again, the change that moved its words was reverted. Eight renders in total, all on one RTX 4090 GPU.

**Measures.** The frozen share comes from the stillness meter. Camera movement is the sum of whole-frame shifts in pixels at 256 pixels wide. Face identity is a face-embedding similarity to the character sheet ("facenet"). The take gate scores the take as a whole.

## Results

### Bench 1, shot bench (round 1)

| Render | Move asked | Result | Frozen share | Zoom of the last face over the first | Head or hat cut at the end | Identity loss |
|---|---|---|---|---|---|---|
| T10 control (locked) | hold | control | 78 % | 1.03 | no | none |
| T10 push, seed 1 | slow push | fail | 1 % | 1.77 | yes (hat brim) | yes |
| T10 push, seed 2 | slow push | fail | 15 % | 1.86 | yes (hat brim) | yes |
| T15 control (locked) | hold | control | 81 % | 1.24 | from about 1.7 s (hat crown) | none |
| T15 push, seed 1 | slow push | fail | 2 % | 2.23 | yes (crown) | yes |
| T15 push, seed 2 | slow push | fail | 0 % | 1.51 | no | yes (min face size) |
| T06 walk bound to camera, seed 1 | walk, tilt up | fail | 63 % | 2.64 | yes (head, top left) | yes (0.529 against 0.635) |
| T06 walk bound to camera, seed 2 | walk, tilt up | fail | 35 % | 2.07 | no | none |

Reading the table:

- A push always stopped the freeze. It did so on all four push renders.
- It also overran. On three of four push renders the last face was 1.77 to 2.23 times the size of the first, against a limit of 1.6, and a head or hat was cut by the frame edge on three of four.
- The walk bound to the camera did not stop the walker. The walker moved 25 and 13 pixels over the last 24 frames. The camera nearly held, though: the background moved +14 and +17 pixels, against +38.5 pixels in the delivered take. Both walk renders also walked toward the lens, which the cell's starting picture caused.

Verdicts from the bench: 0 of 4 push renders won, so the push was **retired as a freeze cure**. The walk arm passed 0 of 2, so the fixed prompt text was **held** rather than shipped.

### Bench 2, implement proof (episode one takes, rebuilt by the changed writer)

| Take | Shot | Frozen, delivered to new | Take gate, delivered to new | Result |
|---|---|---|---|---|
| T06 | full, night, tilt and walk (Spark) | 6.2 % to 6.8 % | 95.0 to 95.0 | pass |
| T10 | medium two-shot, night (Wuli) | 80.6 % to 83.7 % (seed 1); 79.1 % (seed 1000) | 51.6 to 49.8 (seed 1); 52.5 (seed 1000) | fail on seed 1 (gate only), pass on seed 1000 |
| T13 | medium close over the shoulder, day (Wuli) | 94.2 % to 95.8 % (seed 1); 95.3 % (seed 1000) | 43.5 to 42.5 (seed 1); 42.8 (seed 1000) | fail, confirmed on both seeds |
| T15 | medium close, day, locked (Wuli) | 87.2 % to 86.5 % | 47.7 to 48.1 | pass |
| T26 | medium two-shot handshake, locked (Wuli) | 85.9 % to 84.4 % | 82.8 to 83.1 | pass |

Other facts from this bench:

- The frozen share moved by no more than about 3 points at the same seed. The new and delivered renders are nearly the same draw.
- The T13 failure: the face-match score on the 60-pixel face dropped from 0.634 to 0.574 and 0.551, and the take gate fell by about one point. A further render that changed only the over-the-shoulder hold (not the speech words) also failed the gate (42.2). That pins the failure on the hold, not on the speech words.
- The total GPU time was 790 seconds, against a cap of 900 seconds.

### Counts for the record

| Item | Count |
|---|---|
| Panel seats | 10 |
| Debate rounds | 2 (round 1 positions, round 2 answers) |
| Gavel rulings | 2 (before the bench, after the bench) |
| Shot-bench renders | 8 |
| Implement-proof renders | 8 (5 takes, with 3 extra seed or attribution renders) |
| Test suite at the implement commit | 14,976 passed, 9 skipped, 10 expected failures, 3 failed |

The three failing tests were all one check that scans source files for mangled escape characters. They point at a proof-workflow file that the commits did not touch. They were not caused by this change.

## Images

![Summary card of the round-1 shot bench: the push rule is retired, the walk fixed text is held, and the tilt is not admitted.](images/summary_bench_round1.png)
This card lists all eight renders with their verdicts; look at the red FAIL rows for the pushes, and the frozen percentages beside each one.

![The locked control for T10: a two-shot held still for about five seconds, with the two men in frame.](images/strip_b1_t10_locked_control.png)
The control strip shows the held medium two-shot that the push arms were compared against; the frozen share is 78 percent.

![The T10 slow push on seed 1: the camera moves in and the hat of the man on the right is cut by the right edge of the frame in the last frames.](images/strip_b1_t10_push_seed1.png)
Look at the last frame: the push un-froze the take, but the end framing is much tighter and the hat brim is cut.

![The T15 slow push on seed 1: the last face is about 2.2 times the size of the first, and the crown of the hat is cut at the top.](images/strip_b1_t15_push_seed1.png)
This is the worst overrun in the round: the camera travelled from a full figure to a medium close in 5 seconds.

![The T06 walk bound to the camera on seed 1: the walker drifts toward the lens and his head is cut at the top left.](images/strip_b2_t06_walk_seed1.png)
Look at the walker's size over the strip: he grows toward the lens, which the starting picture set, not the words.

![Summary card of the implement proof: four of five episode-one takes pass, T13 fails on both seeds.](images/summary_implement_proof.png)
Pass cards are green and the one fail is grey; T10 shows green because it passed on the confirm seed, and its seed-1 gate drop (51.6 to 49.8) is in the table above.

![The T13 strip, with the delivered row above the changed row: the over-the-shoulder take fails the face and gate checks.](images/strip_implement_t13_failed.png)
The two rows look almost the same to the eye; the failure is in the face-match score on a small face and the gate score, which is why the rule was run on measures and not on the eye alone.

Images rendered by MiniMax-H3 are held from publication until the studio's licence review clears them.

## Verdict

The panel's ruling, in plain terms:

1. **Every scene opens on a moving establishing shot**: either a pull reveal or a follow. Adopted with conditions (the picture must already hold the things the camera reveals; a follow must walk sideways or away, never toward the lens).
2. **One bird's-eye rise per episode**, a camera rising from an eye-level full shot. Adopted for one use per episode, only as a closer or transition, with no dialogue on it. Its first use on a night set is a trial.
3. **Action is cut, not morphed.** A walk, then a boots insert, then a reaction close. The walk is bound to one camera sentence "across the whole shot", with at most two timed gestures.
4. **Talk stays locked** (two-shots and close-ups), so at least half the shots stay locked.
5. **A push is not a cure for a frozen shot.** It overran on three of four renders. The two-push-per-episode cap stays, and the cure writer no longer writes pushes.
6. **Angle is a picture, not a word.** A high or low view reaches a take only through a drawn panel or through the rise. No drawn high-angle panel exists yet, so this is the next research step.

Implementation verdict: the prompt-writer defect fixes reached the output and mostly held. The locked-off hold passed on three takes. The speech-verb change (D-b) was reverted, because it rode on the failing T13 take. The over-the-shoulder part of the hold change was reverted for that shot type only. A proof on five takes at n = 1 to 2 seeds is a "no regression" result, not evidence that any change made the takes more alive.

Tilt (a slow camera tilt up) is not admitted for the Jekyll path. The eye saw no tilt on two blind labels, while the automatic meter read 14 to 17 pixels of drift as a tilt. The threshold of 6 pixels was judged too low and was voided.

## What changed in the pipeline

Plain-language list of the commits the sources record (short hashes are in the source files):

- **Prompt-writer defect fixes (first commit).** The camera's "holds a locked-off frame" is no longer rewritten to "keeps"; a garbled clause in the camera sentence is removed; a night set's style line keeps its lamp (this was already fixed by an earlier commit and is locked by a test); cure aims no longer split on commas or aim at adjectives, and a tilt starts on the ground.
- **Framework rules (second commit).** No camera cure writes a push. A crane that rises must be the only silent shot of its kind per episode, and a rise with dialogue is a fault. A silent locked hold of five seconds or more is named as advisory, with the cure "split the line across a reaction or an insert". A push on a panel drawn one size wider than planned is named as advisory. The storyboard grid draws the target of a rise in the top third. The writer's brief carries the shot framework, and the episode skill and its gate list were updated.
- **Revert (third commit).** The speech-verb change and the over-the-shoulder part of the hold change were reverted after the proof.
- **Not changed.** The push cap (2 per episode) and the locked share (50 percent) stay as they were. No stage, step, runner or owner gate moved, so the architecture page was not changed.
- **Still held.** The follow clause for a side-on walker, the verb count and the repeated action wording wait for further bench rounds.

## Limits and open questions

- **Small n.** Two seeds per arm, two takes for the push bench, one cell for the walk. Every verdict is stated at this size and should be read as a direction, not a law.
- **The control was not a locked frame.** On the push bench both controls drifted slightly (the men stepped in, a hat crept up). Two of the push rules compare against the control's own minimum face size, which the shared first picture sets by construction. The overrun and head-crop failures are not affected by this, and they decided the bench.
- **The meter disagreed with the eye.** The tilt and crane meters are not yet refit against blind labels. Until they are, no gate reads them.
- **The face-box tracker missed hat brims.** Three head crops were not caught by the meter and were caught by eye.
- **The panel's shot types are not measured on a drawn high-angle picture.** The bird's-eye is adopted on one prior shipped take and one bench take. The drawn high-angle research (choosing among image-edit adapters) is queued and needs an owner go.
- **Open items the sources list but did not decide.** Whether faceless establishing shots count against the wide-shot budget (owner ruling); whether shot type should be derived by code or authored by the writer; two aim nouns ("shorter", "town") that the cure replay found and did not rule on.
- **Publishable.** The move-by-cell obedience table (move, starting cell, obeyed or not, with path and n for each cell) could be released as an open benchmark of camera-move obedience for open image-to-video models. This is flagged in the sources, not built.

## Sources

- FRAMEWORK, final ruling on the shot framework (studio audit, 2026-10-21)
- GAVEL round 1, the presiding ruling and pre-registered bench rules (studio audit, 2026-10-21)
- Round 1 and round 2 seat files: action choreographer, anime director, cinematographer, editor, H3 empiricist, pipeline engineer, prompt engineer, skeptic, story adapter, storyboard lead (studio audit, 2026-10-21)
- BENCH, shot-framework bench round 1 (studio audit, 2026-10-21)
- RESULT and PREREG, implement proof (studio audit, 2026-10-21)
