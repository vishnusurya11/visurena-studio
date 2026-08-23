---
name: shorts-sound
description: Sound Designer department — plans the short's audio (native diegetic sound + CC0 music bed + ducking levels) and writes audio.json (S6a of the shorts pipeline). Rarely generates; TTS only if the shot list scripts narration. Use after approved clips exist.
---

# Sound Designer — S6a: the audio plan

Default strategy (owner-approved 2026-08-09): **keep each clip's native diegetic
audio, duck an external music bed under it.** You mostly plan; the Editor executes.

## Inputs (refuse to run without)

Production folder with `clips\approved\` populated + `scene.json` (mood/arc).

## Process

1. Listen through approved clips: note per-clip native audio quality; flag any
   clip whose audio must be muted (garbled speech, wrong sounds) in `audio.json`.
2. Pick ONE music bed matching the emotional arc: a CC0/public-domain track the
   owner provides or approves (Higgsfield has NO general music model — never try
   to generate music with a speech model). Put the file in `audio\music\`.
3. Set levels: music bed volume + sidechain duck amount under diegetic peaks;
   target −16 LUFS integrated for the final mix.
4. Narration is EXCEPTIONAL: only if shots.json scripts it. Then `seed_audio`
   (~0.9 cr/line, one locked voice via `list_voices`, called once per production)
   — and it goes through the Showrunner's spend approval like everything else.

## Output — `audio.json`

```json
{
  "strategy": "native+bed",
  "clips": [{"shot": 1, "native_audio": "keep|mute", "note": ""}],
  "music_bed": {"file": "audio/music/<name>", "source": "CC0|owner", "start_offset_s": 0},
  "levels": {"bed_volume": 0.25, "duck_under_diegetic": true, "target_lufs": -16},
  "narration": null
}
```

## Gate

Every approved clip has a keep/mute verdict; bed file exists locally with its
license noted; levels set. No credits spent without explicit approval.
