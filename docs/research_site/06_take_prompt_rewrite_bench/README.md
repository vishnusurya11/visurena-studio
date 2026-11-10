# Can a better take prompt make AI video shots more dynamic? A pre-registered bench that said no

*2026-10-21 (Seattle time). A rewrite of the video-take prompt was tested on four shots of a Jekyll and Hyde episode. The full rewrite lost, but one rule inside it, turning held shots into slow pushes, won both held shots on both seeds.*

## The question

Visurena Studio turns public-domain books into short animated episodes. Each shot is a "take": a short AI-generated video clip made from reference pictures and a text prompt. Many takes came out almost still. The picture held one frame while the characters barely moved, and a viewer reads that as a dead shot.

The question was narrow. Can the text prompt for a take be rewritten so the takes move more, without costing face quality or adding duplicate people? The rewrite had to be measured before anything in the production pipeline changed.

Terms used below:

- **H3** is the MiniMax-H3 video model. The studio runs it in its "ref2va" mode, which means it turns reference pictures plus a prompt into a clip.
- **Singularity** is the fine-tuned H3 model the studio uses for these takes. The bench used Singularity v1.3, pruned, which is the version in production.
- **Frozen %** is the share of a take in which the picture is held still. Higher is worse.
- **Take verdict** is the studio's 0 to 100 score for a take. It combines several checks, and a take under the pass line fails.
- **Gate** means an automatic check that a take must pass before it is used.
- **Seed** is the random number that fixes one generation. Two seeds per arm make the comparison less dependent on luck.
- **Camera fit** is a measure of how the picture's content moves across frames. It separates a camera move (the whole frame shifts or zooms) from a moving subject.

## What existed before

The take prompt was written by a studio module from a structured plan. The plan names the subject, the action, the place, the camera move and the style. For the four takes tested here, the old prompt had three problems, recorded in the bench notes:

- It named a camera move on some takes but not others. Two of the four takes had no named move at all. Their camera was described only as a hold or a lock.
- It described the action as two beats, and the main action (a walk) was tied to the camera "across the whole shot". The same walk clause often appeared twice.
- One shot said a character "speaks" while his mouth was marked closed on a silent track. One prompt also gave a style line ("low sun from the west") that did not fit a 3 a.m. night shot.

The studio's own prompt guide asks for the action as an ordered sequence, named camera moves, no repetition and no conflicting cues. The rewrite was built to follow that guide.

## Method

**Takes.** Four takes from episode 1, labelled T06, T13, T18 and T26. Each runs on the graph it used in production. T06 and T18 ran on the Spark graph (Singularity v1.3, pruned). T13 and T26 ran on the Wuli graph.

**Arms.** Each take ran four arms:

| arm | prompt | seed |
|---|---|---|
| OLD, seed 1 | production prompt | the delivered seed (this is the take already in the episode) |
| NEW, seed 1 | rewritten prompt | the delivered seed |
| OLD, seed 2 | production prompt | delivered seed + 1000 |
| NEW, seed 2 | rewritten prompt | delivered seed + 1000 |

Only the prompt text differed between arms. The subject definitions, place, style, framing, light, cast references, seed and frame count were byte-identical. A harness check re-rendered the old prompt for T26 at the delivered seed and got a pixel-identical result, so the bench's render path reproduces the delivered take.

**The rewrite, as one rule set.**

- R1, camera: a head that moves keeps its own camera verb. A held or locked shot on a medium or medium-close framing becomes a slow push toward the subject's face. Wide shots, close-ups and inserts stay locked, because a push overruns there.
- R2, beats: the plan's actions became one sentence each, in order ("First ... Then ... Finally ..."), 2 to 3 beats, at least one second each.
- R3, once: a speech verb is dropped where the mouth is closed. The closed mouth is stated once.
- R4, end: one closing sentence says where the frame arrives at the last frame.

**Pre-registration.** The win rule was written before any render. It is in the bench's PREREG file. A take is a win for the new prompt when two things hold: the mean frozen % over the two seeds falls, and the camera score rises (or was already perfect). The new prompt wins overall only if it wins at least 3 of the 4 takes, no tracked person's identity term gets worse by more than 0.05, and no take gains duplicate (clone) frames.

**Measures.**

- Frozen %: the studio's stillness measure, which gives the share of the take where the picture is held.
- Camera obeyed: the camera fit summed over the take, per frame step at 12 frames per second. A take counts as obeyed when the move it asked for shows up in the fit. Each take's camera score is the share of its two seeds that obeyed.
- Faces: the studio's face tracker and readers. Eye cel (eye-openness signal), flicker (face motion between frames), facenet and CCIP (identity similarity; facenet higher is better, CCIP lower is better), clip (a text-image match), and the smallest face in pixels.
- Duplicates: extra large faces beyond the people the plan lists, plus the author's own eye on the strips.
- Take verdict and a motion score (mean optical flow in pixels).

**Cost and limits of the run.** Thirteen renders ran one at a time on an empty GPU queue, grouped by model. Total GPU time was 930.5 seconds (15.5 minutes) against a 30-minute cap. No render was interrupted or skipped.

**Agents and debate.** The source notes do not record any agent count or debate rounds for this bench. The bench was run as a single pass with no multi-agent review.

## Results

### Win rule, per take

| take (graph) | named camera move, old -> new | frozen %, old -> new (seed 1, seed 2) | camera obeyed, old -> new | motion (mean flow px), old -> new | take verdict, old -> new (seed 1 / seed 2) | take wins? |
|---|---|---|---|---|---|---|
| T06 (Spark) | tilt up -> tilt up | 6, 1 -> **69, 67** | 2/2 -> 1/2 | 0.38 -> 0.23 | 95 / 95 -> **54 FAIL / 55 FAIL** | no |
| T13 (Wuli) | held -> push in | 94, 95 -> **15, 11** | 2/2 -> 2/2 | 0.06 -> 0.24 | 43 FAIL / 43 FAIL -> **100 / 100** | yes |
| T18 (Spark) | crane up -> crane up | 17, 22 -> 8, 17 | 0/2 -> 0/2 by the meter (2/2 by eye) | 0.52 -> 0.57 | 95 / 95 -> 90 / 95 | no (camera) |
| T26 (Wuli) | locked -> push in | 86, 86 -> **0, 0** | 2/2 -> 2/2 | 0.10 -> 0.51 | 83 / 83 -> 100 / 70 | yes |

Mean frozen % over the two seeds: T06 3 -> 68; T13 95 -> 13; T18 20 -> 12; T26 86 -> 0.

G-WARP (a warp gate reported by the bench; the source does not define it): T06 pass, pass -> pass, warn. T13 warn, warn -> eye, pass. T18 warn, warn -> pass, pass. T26 pass, pass -> pass, pass.

### Faces

| take | person | smallest face px, old -> new | eye cel | flicker | facenet (higher better) | CCIP (lower better) | clip |
|---|---|---|---|---|---|---|---|
| T06 | Enfield | 51 -> 50 | 116 -> 115 | 15.1 -> 13.8 | 0.68 -> 0.72 | 0.037 -> 0.031 | 0.890 -> 0.891 |
| T06 | Hyde | 11 -> 11 | 0 -> 0 | 3.4 -> 2.9 | 0.36 -> 0.39 | 0.167 -> 0.176 | 0.704 -> 0.690 |
| T13 | Enfield | 60 -> 62 | 129 -> 104 | 5.2 -> 9.0 | 0.60 -> 0.66 | 0.039 -> 0.032 | 0.860 -> 0.863 |
| T18 | Utterson | 45 -> 23 (seed 2) | 74 -> 54 | 17.8 -> 18.2 | 0.25 -> 0.27 | 0.143 -> 0.186 | 0.884 -> 0.859 |
| T18 | Enfield | 33 -> 23 (seed 2) | 65 -> 38 | 15.5 -> 15.0 | 0.23 -> 0.25 | 0.145 -> 0.154 | 0.845 -> 0.819 |
| T26 | Utterson | 68 -> 71 | 62 -> 74 | 4.3 -> 9.1 | 0.57 -> 0.58 | 0.039 -> 0.042 | 0.835 -> 0.833 |
| T26 | Enfield | 60 -> 66 | 71 -> 83 | 5.4 -> 7.4 | 0.34 -> 0.36 | 0.090 -> 0.085 | 0.796 -> 0.785 |

Values are means over the two seeds unless the table says otherwise. The largest identity change against the 0.05 limit is T18 Utterson's CCIP, up by 0.043. That is inside the limit. Flicker rises on the two push takes (T13, T26); the source reads that as the face moving, not as a fault. Utterson on T13 is seen from behind and is not tracked, as in the delivered episode.

**Duplicates.** Zero clone frames in all 16 takes checked (the 13 renders plus the three delivered OLD seed-1 takes). The author saw no duplicate person on any strip.

### The rule, applied

| check | result |
|---|---|
| takes won (frozen falls and camera rises or stays at 2/2) | T13, T26 = **2 of 4** (needs 3) |
| identity terms worse by more than 0.05 | none |
| new clone frames or duplicate people by eye | none |
| **verdict** | **LOSE. Nothing wired.** |

## Images

The five images are labelled strips. Each one puts the old and new prompt side by side for one take, with the frozen %, camera call, take verdict and smallest face size printed on it.

![Summary card: the four takes, old prompt against new prompt, with the rule result. Look at the right-hand column: two wins, one tie and one loss, with the rule needing three.](images/ab_strip_summary.png)

![T06, Enfield walks under the lamp: the new prompt stopped the walk. Look at rows one to three: the old prompt (left two columns) keeps Enfield moving toward the camera, while the new prompt (right two columns) leaves him nearly still.](images/ab_strip_t06.png)

![T13, Enfield at the door over Utterson's shoulder: the held frame became a push-in with a gesture. Look at the columns in order: the old prompt (first and third columns) stays on a still picture, and the new prompt (second and fourth columns) moves in while Enfield turns and gestures.](images/ab_strip_t13.png)

![T18, Utterson and Enfield walk on, crane up: both prompts crane up, and the walkers stay small at the bottom of the frame in the new version. Look at the bottom row: the new faces are smaller on seed 2.](images/ab_strip_t18.png)

![T26, two-shot handshake: the locked frame became a push-in. Look at the seed-2 new column: the push overruns and cuts off the top of Utterson's head by the end.](images/ab_strip_t26.png)

Images rendered by MiniMax-H3 are held from publication until the studio's licence review clears them.

**Audio.** None. The bench produced no listening comparison. The bench's work folder holds four silent WAV placeholders, not an A/B listening pair, so none were copied.

## Verdict

**The full rewrite lost.** The rule needed three wins out of four takes and the new prompt won two. T06 got much worse: Enfield stopped walking and frozen % rose from 3 to 68. Nothing was wired into the pipeline, and the studio owner decided to keep the current prompt in production.

**One part clearly worked.** Rule R1, turning a held or locked medium shot into a slow push toward the face, won both held takes on both seeds, with no measured face cost:

- T13: frozen 95 % to 13 %, and the take verdict moved from 43 (fail) to 100 (pass) on both seeds.
- T26: frozen 86 % to 0 %, and the take verdict moved from 83 to 100 and 70.

**The failure came from the beat rewrite, not the camera.** The old prompt tied the walk to the camera "across the whole shot". The new prompt stated the walk once as beat 1 of 3. The model finished the walk when beat 2 began and Enfield stood still. T06 kept its own tilt, and the walk was the thing that broke.

**The camera meter is wrong for one case.** On T18 the crane rises while it also tilts down to look at the street, which moves the content upward in the frame. The pre-registered meter wanted the content to move down, so it scored 0 of 2 for both arms. By eye, all four renders rose. The rule was not changed after the fact, so T18 counts as a tie.

## What changed in the pipeline

Nothing. The source records no commits and no production change for this bench. The prompt builder, the workflow files, the tests and the skill notes were left as they were. The bench's own scripts (a rewrite module, a prompt builder, a run script, a measure script and a label script) live in the source folder and were not wired in.

## Limits and open questions

- **Two seeds per arm.** That is enough to see a large effect such as frozen 95 % to 13 %, but not enough to size small effects.
- **Four takes.** The rule's three-of-four threshold is strict for a sample this small, and the sample has two held takes and two moving takes.
- **Silent single-shot takes only.** The rewrite was tested only on takes with no dialogue. Takes with spoken lines were not covered.
- **Push risk.** T26 seed 2 pushed far enough to crop Utterson's head by the last frame. A push is therefore not safe on every medium shot, and the next bench should check the end frame.
- **Style and content conflicts** (for example the "low sun" light line on a night shot) were left in both arms on purpose, to keep the style words identical. They may still hurt takes, and that was not measured.
- **Grammar conflict.** The studio's anime shot grammar says a push is a sign of a weak plan and should appear at most twice per episode. Wiring R1 is therefore a creative decision as well as a measured one, and the studio owner must decide it.
- **Next step, not done.** Bench R1 alone, with the rule pre-registered, on more held and locked medium shots, including dialogue takes, and check the end frame for overrun.

## Sources

- "PREREG" (prompt bench pre-registration, 2026-10-21): the win rule, written before any render.
- "BENCH" (prompt bench report, 2026-10-21): the verdict, the per-take results, the face table, the eye review and the limits.
- Labelled strips and summary card (prompt bench, 2026-10-21): the images used above.
