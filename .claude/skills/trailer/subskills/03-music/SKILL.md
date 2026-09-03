---
name: trailer-music
description: Generate the cue, then MEASURE what it plays. The music is the timeline.
---

# Music

`studio/trailer_music.py`, `studio/beatmap.py`, `scripts/trailer/build_music.py`.

## Generate first, measure second, cut to the measurement

A generated cue does not put its hit where the prompt asked. The 2026-08-25
trailer cut its title card 5.29s before its cue's own +37 LU impact, so the
braam landed inside the button shot. A later build missed by 0.85s the same
way. **Conform picture to the audio, never to the section plan.**

`beatmap.py` decodes the file and reads its envelope directly:

| | |
|---|---|
| `onsets()` | the candidate cut grid |
| `structural_impacts()` | the few big hits |
| `stopdowns()` | where the floor drops out — room for a line over black |
| `title_moment()` | the late hit with silence in front of it |

Do NOT scrape ffmpeg's `ebur128` log. An earlier version did; this build prints
only a summary, the parse returned `[]`, and callers reported "0 impacts".
`envelope()` raises rather than returning nothing.

## MiniMax Music 3 facts

- **SECTION COUNT sets length**, not any duration field — the text encoder is
  autoregressive and decides structure before diffusion runs. ~11.1s a section;
  nine sections ≈ 100s.
- **`duration` is a SECOND SEED.** Changing it re-rolls the whole composition
  (waveform correlation between takes at 30/60/150 was −0.03). Pin it and
  iterate on seed alone.
- **Caption prose sets dynamic shape.** One word decided it: a cue told
  "relentless throughout" came back at 4.0 LU range with 3 stopdowns; the same
  plan told "starts near-silent... hard full stop" came back at 9.7 LU with 9.
- **Exclude vocals by saying nothing about voices.** Negation ("no vocals, no
  backing vocals") reliably produces humming.

## Choose the cue on measured fitness, never on filename

The shipped trailer inherited a 4.0 LU wall-of-sound bed purely because
`SH-cue-action_*` sorted first in a glob. **File order chose the trailer's
entire dynamic shape.** `trailer_fitness()` requires a late hit with a stopdown
in front of it, and a grid an editor can choose from (8-40 onsets); loudness
range alone once picked a 90-onset cue over a clean 20-onset one.

Render 2-3 seeds and let the measurement decide.
