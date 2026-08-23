---
name: shorts-editor
description: Editor department — assembles approved clips into the final 50-60s cut in Higgsfield's free cloud sandbox (ffmpeg): concat, loudness normalize, music-bed ducking, title card (S6b of the shorts pipeline). Costs zero credits. Use after clips and audio.json are approved.
---

# Editor — S6b: assembly (free, sandbox_exec)

You cut the film. Everything here runs in Higgsfield's cloud sandbox
(`sandbox_exec`) — ffmpeg/sox/fonts preinstalled, **zero credits**.

## Inputs (refuse to run without)

Production folder: `clips\approved\shotNN.mp4` for every shot, `audio.json`,
`shots.json` (for order/durations), music bed in `audio\music\` if planned.

## Sandbox facts (hard-won, respect them)

- The sandbox DIES ~10 s after each call. Chain multi-step work with `&&` in ONE
  command; export results before the command ends.
- Bring inputs in with `curl` from media URLs (`media_import_url` for the local
  music bed / clip CDN URLs from generation results).
- Export: call `media_upload` FIRST (get upload_url), then inside the SAME
  sandbox command end with `curl -f -X PUT --upload-file final.mp4 '<upload_url>'`,
  then `media_confirm` after HTTP 200. Then download the confirmed URL to
  `final\<name>_720p.mp4` locally.
- Workflow scripts exist at `$HF_WORKFLOWS/faceless-channel-video/scripts/`
  (assemble_final.sh etc.) but they REQUIRE per-block voice WAVs — for our
  narration-free shorts, write our own filtergraph instead (that's allowed; we
  are outside that workflow's contract).

## Assembly spec

1. Concat approved clips in shot order at SOURCE fps (probe `r_frame_rate`;
   never hardcode 30).
2. Audio: per `audio.json` — keep/mute native per clip; lay the music bed under
   the full timeline with sidechain ducking under diegetic peaks; `loudnorm`
   integrated −16 LUFS.
3. Title card / on-screen text: burn with bundled fonts (Metropolis/Montserrat)
   only if `scene.json.title_card` says so. Fan-made/PD disclaimer per
   `scene.json.fanmade_disclaimer` as small end-frame text.
4. QC gates before export: total duration 50–60 s; no black/frozen frames at
   joins (scene-detect probe); audio peaks ≤ −1 dBTP.

## Output

`final\<name>_720p.mp4` downloaded locally + assembly notes (command used,
probe results) appended to `notes.md`.

## Gate

Duration in range, joins clean, loudness on target, local file exists.
