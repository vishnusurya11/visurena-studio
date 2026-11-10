# Ten experts, five cycles, one GPU: does any open video workflow beat our production anime takes?

*Visurena Studio research note, 2026-11-08. Everything here ran locally on one RTX 4090, $0 in API spend.*

## The question

Our anime action pipeline renders each shot with MiniMax-H3 reference-to-video. The model is given cast sheets, a place
picture and a storyboard panel, and the recorded line is the audio guide. The renders are 1344x768 and are upscaled by
RTX VSR. We asked whether any other open workflow beats it on the four kinds of shot a story needs: establishing,
talking, camera movement and fighting. We asked this at 2K and at true 4K, and we wanted measured evidence rather than
hearsay. The candidates were a different video model, VAE, text encoder, LoRA, attention kernel, upscaler or
storyboard method.

## Method

- **Panel.** Ten subject-matter agents covered ComfyUI runtime, video models, VAE, text encoders, LoRA, character
  consistency, speed, upscaling, image editing and production auditing. A skeptic and a judge sat over them.
- **Cycles.** Each cycle ran propose, attack plus queue tests, measure on the GPU, skeptic refutes, experts revise,
  judge ranks the top 3. A claim survived only with a measurement on our bench or a primary source. Five cycles ran.
- **Bench.** A one-shot renderer changed one thing at a time. Prompts, sheets, panels and voices came from finished
  scenes, so the variant was the only difference. One GPU queue ran under hard caps and a 10-minute watchdog.
- **Shots.** Twelve test shots, three per kind. Later cycles added three breadth and "carry beat" shots, chosen after
  the hypothesis was stated.
- **Instruments, each one added after the previous one was caught misleading:**
  - Flow-compensated warp residual. Raw optical flow rewarded morphing.
  - warp_resid, which is warp minus its fit on camera motion. Raw warp correlated r = 0.94 with how much the camera
    moved.
  - Split-screen and hard-cut detectors. A split-screen take had scored best on every metric.
  - A geometry-break cluster-cut detector, built on ORB features and a RANSAC homography.
  - CCIP character identity on face crops.
- **Blind scoring.** Four rounds of blind scoring answered the question "did the commanded action happen?".
  - The yes/no questions were frozen before rendering.
  - Two independent scorers were used.
  - Hidden repeats measured how consistent each scorer was.
  - In crop tests the sides were swapped, after one scorer chose the left side 20/21 times.
- **Noise floor.** A seed noise floor was measured on 121 same-shot seed pairs. No difference smaller than it was read
  as a result.

About 165 test takes were rendered and 177 were measured, across 163 GPU jobs.

## Results

**No take workflow beat production on any picture metric, for any shot kind, beyond the seed noise floor.** That
includes:
- Singularity v2 (dense, Sol-Attn and official 4-step LoRA variants);
- Pika 4-step, base H3 at 20 steps, a hybrid unet, LTX-2.5 and Wan 2.2 Fun-Camera;
- latent 2x upscale passes, 1920x1088 native renders and SeedVR2;
- text-encoder precision, prompt rewrites, reference-slot order, one-picture panels and staged-agree pinning.

**What did survive is mostly about inputs, not models.** Each finding came out of the debate:

1. **Split storyboard panels.** 29 of 183 panels in ten action scenes contained two pictures, mostly split
   top/bottom. The production seam gate only checked columns. A split panel stages two pictures, and the take often
   "jumps" between them.
2. **The continuity pin was not the last frame.** The frame-extraction command took frame 190 of 192. On 2 of 8
   checked takes frame 191 was a glitch, which shows as a one-frame flash at the cut.
3. **The staged picture beats the text.** On one carry shot, the 4-step Singularity v2 lane showed the scripted rope
   and climb far more often: blind, two scorers, 8/8 vs 3/8 and 9/16 vs 0/16. The cause was not better action skill.
   That panel showed a different moment from the script; production obeyed the panel and Singularity v2 obeyed the
   text. The fix is a panel that shows the beat.
4. **Today's random faults are seed-random.** Splits, cuts and empty close-ups were cured by one same-model retake
   in every measured case.
5. **The 4K finish.** Cropping to true 16:9 and running RTX VSR directly to 3840x2160 costs about 1 minute per
   episode. Blind crop judges could not see a difference from 1920x1088 native renders, which cost 2.1-2.6x the
   render time.

## What we got wrong along the way, and how the protocol caught it

- **Optical-flow motion.** It ranked the warpiest model best. The fix was a flow-compensated residual.
- **Raw warp.** It ranked the stillest camera best. The fix was the camera-matched residual.
- **A split-screen take.** It scored best on every metric. The fix was split and cut detectors.
- **"Model X cuts away mid-shot."** Frame-by-frame review showed a fast continuous camera swing.
- **"9/9 vs 0/5 on the key beat."** It came from 6-frame contact strips too small to see a held key; at crop zoom
  production held the key too. Small held objects are never scored on strips again.
- **"The rewritten script fixes the jump."** The pre-registered kill rule fired.

## Reproducing

The bench, variants, queue, measuring tools, blind sets and every cycle's proposals, attacks, skeptic reports and
judgements are kept in the studio's audit folder (`docs/audit/2026-11-07_expert_debate/`). The panel-audit and
split-detector code is general. It works on any storyboard-to-video pipeline that stages panels as references, and is
a candidate for release as a standalone tool.
