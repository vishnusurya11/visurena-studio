---
name: episode
description: Turn one book chapter into a 90-120 s vertical (9:16) microdrama episode — one event, voice-over on cutaways, a gpt-image 3x3 storyboard as the video model's input, every panel animated on local MiniMax-H3, mixed and captioned for phones. Use when writing, building, fixing or reviewing an episode under library/<book>/episodes/.
---

# Episode

One chapter -> `library/<book>/episodes/epNN/master.mp4`.

```
uv run python scripts/episode/episode.py    <codex_id> <n> [--until=<step>]  # all, in order, resumable
uv run python scripts/episode/say_lines.py  <codex_id> <n>   # 1. AUDIO FIRST: every line, IndexTTS2, measured
uv run python scripts/episode/timeline.py   <codex_id> <n>   # 2. placed.json: shot times FROM the audio
uv run python scripts/episode/frames.py     <codex_id> <n>   # 3. one empty 9:16 plate per setup + sheets
uv run python scripts/episode/storyboard.py <codex_id> <n>   # 4. gpt-image 3x3 sheets -> SNN.png  (PAID)
uv run python scripts/episode/shots.py      <codex_id> <n>   # 5. H3 round: silent i2v, SPEAKING i2v for dialogue
uv run python scripts/episode/storyboard.py <codex_id> <n> --review   # review.png: panel | start | end
uv run python scripts/episode/assemble.py   <codex_id> <n>   # 6. cut to placed.json, mix, title card, black
uv run python scripts/episode/qc.py         <codex_id> <n>   # 7. measure the delivered file
uv run python scripts/episode/title.py      <codex_id>       # once per book: the animated title card (PAID still)
uv run python scripts/episode/runcards.py   <codex_id> <n>   # runcards.html: every shot's panel, audio, settings, prompt
```

The plan is WRITTEN (by an agent or a person) to `episodes/epNN/plan.json`
and validated by `studio/episode_spec.py` on every load. Every script skips
what is on disk, so a rerun resumes and the paid step never spends twice.
Rules come from `docs/analysis/research/episode-01..03-*.md`; the two reviews
that cut this pipeline down are `episode-04-simplify-critic.md` and
`episode-05-defender.md`.

## The brick

ONE EVENT split by a title card: a TURN (the lead's choice, 50-75 % in) and a
BUTTON (the world's answer, the last line, never the lead's). AUDIO FIRST:
the plan carries no seconds; every line is rendered and measured, and each
shot's length is derived from the lines it carries, so there is no hole in
the voice that the plan did not name as a beat. A first-person NARRATOR (the
book's narrator, in that character's cast voice) carries ~90 % of the words
over cutaways; the few DIALOGUE lines are spoken ON CAMERA, the speaker's
face at close or medium close-up, the lips driven by the line's own wav.
Continuity is a STORYBOARD DRAWN AS ONE PICTURE, every panel the first frame
the video model animates. No text on the picture. An episode is the WHOLE
chapter: TWO MINUTES is the target, and the 2-3 minute room is only for a
chapter that needs it (owner, 2026-09-10); closed by the book's animated
title card.

## THE SYNC RULE (owner-approved, non-negotiable)

The picture is cut to the voice, never the voice laid on the picture.
Lines are rendered and MEASURED first. A shot is exactly: 0.25 s handle +
its lines' measured seconds + 0.35 s breath between two lines + 0.25 s handle
+ any beat the plan names, snapped UP to a whole frame. Every line is laid
at its own shot's start + 0.25 s. A speaking take is driven by the SAME wav
at frame 6, so mouth and sound are one recording. Nothing is scheduled,
shifted or dropped afterwards; `timeline.py` refuses a placement that breaks
this (`episode_timeline.misaligned`). Measured result on the first
audio-first master: 33/33 lines heard, 25/25 cuts on frame, owner: "great job
on the audio narration voice over sync with the video".

## 1. Write the plan (`plan.json`) — no seconds anywhere

Order is the method: button first, then hook, then the lines in playback
order, then a shot for every line. `Line{index, kind, speaker, text, shot}`;
`Shot{index, section, setup, size, faces, frame, motion, take, beat_s, coda_s}`.
A line NAMES the shot it plays on; a shot carries one or two lines; a shot
with no line names a `beat_s` (<= 1.5) or the `coda_s` (<= 4, last shot). The
shot before the button names a beat >= 1.0. The validator projects the
runtime at the measured pace (3.8 words/s) and refuses outside 120-180 s.

- **Button** = last spoken line: not the protagonist; leaves the question open.
- **Hook** = shot 0, ends by 0:05: the latest element that carries conflict and
  reads on mute. Everything before it is cut or becomes a picture plant.
- **Lines** have a `kind`: `narration` (written fresh, first person, the
  narrator's cast voice) or `dialogue` (the 3-5 lines that turn the story,
  5-20 % of the words: the dial). <= 18 words each. Spell honorifics and
  numbers out ("Doctor", "Mister"). A DIALOGUE line's shot must show the
  speaker in `faces` at `close` or `medium_close` — the lips are driven, so
  the mouth must be readable (the old rule is inverted for dialogue).
  Narration may sit over anyone's face with the mouth closed.
- **Shots** tile the runtime, >= 1 s each, `setup` names a key of `setups`
  (1-3 setups). `size` in insert/extreme_close/close/medium_close/medium/full/wide.
  `faces` = whose face is frontal and readable; a speaker in `faces` at
  close/medium_close/medium/extreme_close is refused (F1). A line never starts
  within 0.25 s of a cut (T1) — lead or trail it.
- **Under a line**, the shot shows: the listener with the mouth closed, the
  speaker's back or strict profile, a wide where heads are small, an insert of
  hands or the object. Never the speaker's readable face.
- `frame`: the storyboard panel — shot type first, then who does what, then the
  light ("Close on Watson's gloved hand on the stick; Stamford ahead, out of
  focus, glancing back"). `motion`: two to four clauses separated by
  semicolons, the camera idea first; the take prompt places them in order.
- **Geography is continuous inside a setup, and every frame says WHERE.** The
  first corridor sheet put the men at the side-door in shot 2 and walking
  toward it in shot 3 (owner caught it, 2026-09-10): the sheet was faithful,
  the plan was wrong. So each `frame` states the position relative to the
  previous shot ("still mid-corridor; the door still far ahead", "now at the
  doorway"), and a person who has reached a place in shot N is never on the
  way to it in shot N+1.
- **A beat may only move what the panel shows.** Measured on iteration 1
  (2026-09-10): "his hand tightens on the stick" in a face close-up with no
  stick in frame produced an invented hand holding an object; "his eyes go to
  his own hand" raised a hand into a face close-up; "turns to the bench and
  pricks his finger" swung the camera round to show it; "the drop falls and
  blooms" turned the whole vessel red inside the shot that only needed one
  drop. Name a body part, object or change only if it is IN the panel and
  belongs to this shot's beat; leave the rest to the next panel.
- `setups[name].described` is the empty room for the plate; `.cast` who appears.

Validate: `uv run python -c "from studio import episode_home as h; h.load_plan(h.book_dir('<codex>'), <n>)"`.
Fix what it names; never weaken the validator.

## 2. Lines — `say_lines.py`, then `timeline.py`

IndexTTS2 from `cast/<who>/voice/design.wav` as both timbre and emotion
reference (MEASURED: 0.80 speaker similarity to the designed voice vs 0.73
for the Qwen3 clone, both word-perfect; ~4x slower). All renders first, then
all listening: Whisper WER <= 0.20 AND ECAPA similarity >= 0.70 against the
designed voice, one re-roll. `lines/lines.json` carries the measured seconds.
`timeline.py` then writes `placed.json`: `shot.seconds = 0.25 + sum(lines) +
0.35 x (lines-1) + 0.25 + beat_s + coda_s`, every line at its shot's start +
0.25, the runtime the sum; refused outside 120-180 s. Every later stage reads
placed.json; nothing is scheduled or dropped afterwards.

## 3. Plates and sheets — `frames.py`

Krea 2 turbo, `9:16 (Portrait Widescreen)`, `location_prompt(described)`,
conformed to 768x1344. A character sheet is made for any speaker the trailer
never drew (Stamford's body is invented once, in `STAMFORD`). `refs.json` is
never written here.

## 4. Storyboard — `storyboard.py` (PAID: gpt-image-2.5-sunburst, owner's go 2026-09-10)

Per setup, the shots spread evenly over 3x3 sheets at 2048x3072 (`chunks`:
ten shots are two sheets of five). References attached in order: the plate,
each character's sheet, the previous sheet of the same scene. The prompt
(`episode_board.prompt`) states the grid and reading order, what every
attached image is, `Panel k: <frame>` per shot, alternates for spare cells
(never black), the still register. Each panel is cropped and conformed to
`frames/SNN.png`; any edge of a cell that reads near-white is trimmed first
(a sheet's gutters are not all the same width: three corridor panels kept a
white bottom edge before this). The prompt and reference list are written
beside a sheet ONLY when it is drawn. Look at the sheets before the round: same room, same
person in the same clothes, listener's mouth closed. A bad sheet is deleted
and redrawn with a corrected `frame`.

Measured 2026-09-10: three sheets, sixteen panels, first try — Watson's tweed,
bowler, moustache and stick identical across both setups. The image-edit
compositor lane tried first swapped wardrobes between people; it is gone.

## 5. Takes — `shots.py`, two lanes

Narration lane: `video_minimax_h3_i2v_turbo` from the panel, frames =
`legal_frames(24 x (placed seconds + 0.25))`. DIALOGUE lane:
`video_minimax_h3_i2v_turbo_speak` — the same base with the line's wav as an
audio guide at frame 6 (`MiniMaxH3AddGuide`, 0.25 s silent head): the person
in the panel speaks OUR line with moving lips. MEASURED 2026-09-10 (research
06): words verbatim, voice 0.844 against the input wav, mouth motion 10x
higher during the line than after, identity and framing the panel's. The
master lays the original wav at the same 0.25 s, so mouth and sound are one
recording. Takes run one lane at a time so weights load once. 768x1344,
8 steps, H3 resident, queue empty (`episode.py` refuses otherwise). FLF
between panels is a morph (measured) and is not used. `shots/prompts.json` is
the one place every run card lives; `shots.json` repeats it per take with the
render time.

The take prompt (`studio/episode_take_prompt.py`) is the official H3 Start
Frame skeleton — alignment line, `integrated_multimodal_description: [Shot 1]`,
`overall_soundscape`, `non_diegetic_music: N/A`. A SPEAKING shot's body: a
quarter-second silent head, `<Name> (S1) speaks to the person just off-screen,
physically speaking with natural lip movement on every syllable: <d>[English]
<the line>.</d>`, the beats, silence after the line, the LOCK. A silent
shot's body is the shortest that measured as holding the frame: the panel's own `frame` text, the `motion`
beats in playback order with prose positions (the format keeps timestamps for
cuts), a framing LOCK, the rules. MEASURED on one panel and seed, four
variants: every element the prompt names, the model shows — a room paragraph
pulled the camera back to show the room, a bystander's description pulled his
face in. Nothing else is named.

## 6. Review — `storyboard.py --review`

`review.png`: one row per shot, panel | take at 0.3 s | take at its last
frame. Judge the END frame: every drift of iterations 1-2 was invisible at
the start and plain at the end (a window appearing behind a profile, a hand
raised into a close-up, a vessel gone red a shot early). The eye is the gate;
nothing automatic compares panel to take yet (research 02 §5).

## The iteration loop (three passes on chapter 1, 2026-09-10)

Render -> `review.png` -> three frames of the master at line times (captions)
-> `qc.json` -> write the defects in `episodes/epNN/iterations.md` -> fix the
plan's `motion`, the assemble stage or this skill -> delete ONLY the takes
whose motion changed and rerun `episode.py` (everything else is cached).
Iteration 1: 17 takes, 93 min; 4 takes drifted, captions overlapped, -15.8 LUFS.
Iteration 2: 5 takes re-rendered, 3 of 4 drifts gone, QC PASS at -15.3 LUFS.
Iteration 3: 1 take. A background that is DESCRIBED gets embellished (a
profile "against the plain wall" grew a window twice); describe only the
person and the move, never the background of a tracking shot. And a rerun
with the SAME seed drifts the same way — three S04 reruns did — so a retake
is `Shot.take += 1` in the plan, which changes the seed; the motion text is
only changed when the drift is something the words named.

## 7. Assemble and QC — `assemble.py`, `qc.py`

Cut each take from its first frame to its PLACED seconds; ACE-Step bed at
least the runtime long; lines laid at their placed `at` (a dialogue take's own
track is discarded, the driving wav is laid instead); `trailer_assemble.mix_with_lines`
(-16 LUFS lines, bed ducked to -24 under them, master -14 LUFS / -2 dBTP
pre-encode, then one final gain toward -14 bounded by the -1.0 dBTP ceiling);
then the book's animated title card (`title/title.mp4`, made once by
`title.py`: a gpt-image still animated 3.5 s by H3), then 2 s of black. No
captions or text on the picture (`studio/episode_captions.py` stays for a
future subtitle FILE). QC on the delivered file: length, -15.5..-12.5 LUFS,
TP <= -1.0, every planned cut seen within 0.12 s, every line heard ON THE
MASTER (WER <= 0.20); reports `speech_s` and `longest_gap_s` (the dial the
narration ratio is turned by). Not yet measured on a real master: captions, the cut
detector on same-setup cuts.

## Open items

- No automatic panel-vs-take identity gate.
- Models load off the D: HDD; moving the H3 weights (~64 GB) to the C: NVMe is
  user-side and the largest unmeasured speed-up.
- Lip-sync is a future lane; every line is VO. `ComfyUI-MiniMaxH3-Director`
  (timeline editor, retake-stitch of a range) is the interactive retake lane
  to try when a take fails in one beat.
