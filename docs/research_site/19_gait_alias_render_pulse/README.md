# A walking check that measured the video model's heartbeat: aliasing in gait measurement on generated video

*2026-11-10 (Seattle time). A gate that flags "sliding feet" in AI-generated video failed three shots of a
public episode for shuffling at exactly 4.0 steps per second. None of them was a shuffle. The gate read every
second frame, and a pulse the video model draws into its output folded down to look like a fast, short step.*

## The question

Our studio makes short animated episodes with an open video model (MiniMax-H3). One automatic check, G-GAIT,
looks for a common fault in generated walks: the legs move quickly while the body glides, so the feet
seem to slide over the ground. The check measures two things on the walker:

- **cadence**, the steps per second, read as the main rhythm of the legs' motion against the torso;
- **step length**, the ground the body covers per step, in body heights.

A fast cadence (3 or more steps a second) with a short step (under 0.045 body heights) fails the take.

In one episode three different shots failed with nearly the same reading, 3.92, 4.00 and 4.04 steps a second.
Each was re-rendered six times on new seeds and failed every time. The question was whether three different
walks really shared one cadence.

## What existed before

- The check samples the 24 fps take at 12 fps (every second frame), to save time.
- It was calibrated on 91 walking takes from three earlier series. 20 were measurable, and it fired once, on a
  take whose video no longer exists.
- Video diffusion models decode in short groups of frames. That can leave a faint periodic pulse in motion
  every few frames.

## Method

- We re-measured the three failing takes at the native 24 fps with the check's own code, on CPU.
- We read the frequency spectrum of the legs' motion at both rates.
- We applied the same reading to a walk the owner had liked and to a walk that had shipped without a flag.

## Results

| take | 12 fps reading | 24 fps strongest peak | 24 fps in the step band |
|---|---|---|---|
| shot T19 | shuffle, 4.00 steps/s | 7.95 Hz | no step rhythm (prominence 1.63) |
| shot T00 | shuffle, 3.92 steps/s | 8.04 Hz | no step rhythm (2.31) |
| shot T21 | shuffle, 4.04 steps/s | 8.04 Hz | no step rhythm (1.29) |
| liked walk (another series) | walk, 3.10 steps/s | 1.73 Hz, in band | a walk at 1.73 steps/s |

- **The pulse is about 8 Hz:** one beat every 3 frames at 24 fps.
- **It folds to 4 Hz:** sampled at 12 fps, an 8 Hz signal appears at |12 - 8| = 4 Hz, inside the band of human
  steps. This is classic aliasing: a rhythm sampled at less than twice its rate turns into another rhythm.
- **The gate was reading the pulse:** the three "shuffles" were the model's decoding rhythm, not anyone's feet.
  One of the three walkers does not walk at all; his body crosses 0.005 body heights a second.
- **The simple fix fails:** re-measuring everything at 24 fps with the old thresholds is not a fix. It turned a
  shipped, unflagged walk into a new false failure (a 2-frame pulse at 12 Hz), and the travel measure itself
  changes with the frame rate.

## What changed

- **A shuffle needs a second reading:** a shuffle found at 12 fps now stands only if a 24 fps reading finds the
  same cadence, within 0.3 steps a second and with a clear peak. Otherwise the take is recorded as
  "unmeasured: alias", with both numbers printed.
- **Walks are untouched:** the second read runs only on shuffles, so no walk verdict can change.
- **Replay on the shipped takes:** all three came back "unmeasured: alias".
- **The check is advisory in practice:** until an owner-labelled true shuffle can be replayed at both rates.

## Why it matters beyond this studio

Any motion check on generated video that subsamples frames, whether for gait, lip sync, flicker or camera
shake, can alias against the model's own decoding cadence. The safe pattern is cheap:

- measure at the native rate, or confirm a subsampled finding at the native rate before acting on it;
- print both numbers, so a reader can tell a real rhythm from a folded one.

## Limits

- **Small sample:** three failing takes and two reference walks from one model family.
- **Only one true positive:** the check's one true positive could not be replayed, because its video was gone.
- **Unmeasured across models and settings:** the pulse frequency was not measured across models, step counts or
  decoders.
