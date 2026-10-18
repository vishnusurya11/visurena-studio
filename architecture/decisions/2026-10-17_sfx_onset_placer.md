# 2026-10-17 -- sound effects on the measured moment (step 10_04, `studio/sfx_onset.py`)

Status: BUILT 2026-10-18 (owner go 2026-10-17, the test-bench recommendations approved wholesale).
Evidence: `docs/audit/2026-10-16_model_tests/PART2_SUMMARY.md` (F1-F3) and `sfx/sfx_metrics.json`.

## The problem, measured

The plan names a shot's sound and a rough time (`Sound.at`); `sfx_cues.placed` laid the Stable
Audio 3 render there, so a boot or a door landed wherever the writer guessed. On Jekyll ep01 an
SA3 cue put on a HAND-MARKED visual onset landed within 4 ms (T06 stamp) and 41-57 ms (T09
door); free-running SA3 footsteps drifted 200-280 ms by the third step (T03).

## The brick

**A sound lands on the frame where the take shows its event, measured off the take; a sound the
picture cannot time keeps its planned time and says why.**

- `kind_of` reads the sound's words: footsteps / heels / strides are `steps`; a voice, crowd,
  weather or bell is untimed; anything else is one `motion` event.
- steps: the walker is the long-lived person track that crosses the most ground against the
  camera's pan; each peak of his box width is a heel strike. The render is cut into its own steps
  (onset detection, 10 ms pre-roll) and one slice is laid per strike.
- motion: the strongest peak of camera-compensated Farneback motion around the people within
  0.75 s of the planned time; the cue is shifted so ITS first onset hits that frame. H3's repeated
  frames are bridged by a 3-frame running max.
- Clock: take seconds -> master seconds through the run's start and the take's written head; a
  slowed or still take is not measured. Curves are cached by the take's bytes.
- `audio/sfx/onsets.json` records every placement (event, starts, or the fallback reason); QC's
  "every planned sound heard" listens where the cue was laid.

## What it does not do

It never drops or invents a sound, never moves a voice, and never measures a take the cut plays
slowed or as a still. A missing person detector (`gait.yolo`) leaves every cue at its planned time.
