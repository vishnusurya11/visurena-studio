# Episode 07 — audio first: the picture is cut to the voice

Date: 2026-09-10. Owner's direction: the episode is the WHOLE chapter,
120-180 s; every line is rendered and measured BEFORE any picture; dialogue is
spoken on camera (audio-driven H3 take, speaker's face readable); narration
stays voice-over on cutaways; ~90/10 narration/dialogue; no text on screen.

What this replaces. Today `plan.json` times shots and lines by hand from a
word count (`WORDS_PER_SECOND = 3.8`), `say_lines.py` measures the files, and
`assemble.schedule()` pushes narration around the planned dialogue `at`s,
dropping what does not fit. Measured on the 90 s cut (`ep01_short/qc.json`):
speech 58.1 s of 90, longest hole 3.45 s, and the owner heard "so much pause
after haemoglobin" — the picture was 90 s long because the plan said 90, not
because the voice needed 90. The fix is not a better estimate: it is to
remove the estimate. Seconds enter the plan exactly once, measured.

## The brick

```
shot.seconds = LEAD + sum(line.seconds for line in shot.lines)
             + BREATH * (len(shot.lines) - 1) + TRAIL + shot.beat_s
LEAD = TRAIL = 0.25     # the handle on either side of speech (T1: a line never starts on a cut)
BREATH = 0.35           # between two sentences on one cutaway
beat_s <= 1.5           # silence only where the plan names it
coda_s <= 4.0           # the last shot, no line
t_start[i] = sum(seconds[:i]);  runtime = sum(seconds)
```

Everything else is derived from that line: a dialogue shot is the rule with
one dialogue line (line + 0.5 s), a narration cutaway is the rule with one or
two narration lines, silence is the rule with no line. There is no `at` to
schedule and no hole to fill, because a hole can only exist as a named beat.

## 1. Plan schema: lines first, shots derived

`plan.json` loses every number of seconds. `Line` loses `at`; `Shot` loses
`t_start`/`t_end`. Both gain a binding: a line names the shot it is spoken
on; a shot is a picture with no time of its own.

`Line` fields: `index`, `kind` (`narration` | `dialogue`), `speaker`, `text`,
`shot` (the shot id this line is heard on). For `dialogue` the shot MUST show
the speaker: `speaker in shot.faces` and `shot.size in {close, medium_close}`
— F1 is inverted for dialogue, because the mouth now moves. For `narration`
the old rule stands: any face in frame has its mouth closed; the narrator's
own face is allowed.

`Shot` fields: `id`, `section`, `setup`, `size`, `faces`, `frame`, `motion`,
`take`, plus `beat_s` (default 0, max 1.5: silence after this shot's last
line) and, on the last shot only, `coda_s` (max 4). A shot with no line must
have `beat_s > 0` or be the coda; a dialogue shot carries exactly one line
and no narration; a narration shot carries one or two narration lines whose
measured sum lands the shot in 3-8 s — the writer splits at sentence ends and
moves the second sentence to the next cutaway when it does not fit.

`lines/lines.json` (written by `say_lines.py`) is where seconds first exist.
`placed.json` (new step, below) is where `t_start`/`t_end`/`at` are computed
from them. The plan is validated on structure only; the timeline is validated
on measured seconds.

### Example: the first 20 s of chapter 1

Measured seconds are from `ep01_short/lines` (IndexTTS2 will re-measure;
l02 is not yet rendered and is shown as an estimate). Five shots in 20 s is
the rate the whole chapter runs at: 120 s -> ~30 shots.

`plan.json` (excerpt):

```json
{
  "number": 1,
  "title": "A Study in Scarlet",
  "protagonist": "john_watson",
  "setups": {
    "corridor": {"described": "A long stone corridor inside St Bartholomew's Hospital, 1881 ...",
                 "cast": ["john_watson", "stamford"]}
  },
  "lines": [
    {"index": 0, "kind": "dialogue",  "speaker": "stamford",    "shot": "S00",
     "text": "You mustn't blame me if you don't get on with him."},
    {"index": 1, "kind": "narration", "speaker": "john_watson", "shot": "S01",
     "text": "Stamford said it lightly. But he did not look at me when he said it."},
    {"index": 2, "kind": "narration", "speaker": "john_watson", "shot": "S02",
     "text": "I had been standing him lunch at the Criterion, glad of any face I knew."},
    {"index": 3, "kind": "narration", "speaker": "john_watson", "shot": "S03",
     "text": "A fellow at the chemical laboratory had rooms, he told me, and wanted someone to go halves."},
    {"index": 4, "kind": "narration", "speaker": "john_watson", "shot": "S04",
     "text": "I had come home from Afghanistan with a shattered shoulder and eleven shillings a day."}
  ],
  "shots": [
    {"id": "S00", "section": "hook", "setup": "corridor", "size": "close",
     "faces": ["stamford"],
     "frame": "Close on Stamford's face in three-quarter as he walks, glancing back over his shoulder to speak, mouth closed at the first frame; the corridor's barred window light behind him; near the START of the corridor.",
     "motion": "Handheld tracking beside him at walking pace; he looks back and speaks the line; his eyes drop away before the end."},
    {"id": "S01", "section": "setup", "setup": "corridor", "size": "medium_close",
     "faces": ["john_watson"],
     "frame": "Medium close-up of Watson walking, drawn thin face listening, mouth closed, eyes ahead; Stamford's shoulder blurred at the left edge; still near the start of the corridor.",
     "motion": "Tracking back in front of him at walking pace; he listens, mouth closed, a small frown; a bar of window light passes over his face."},
    {"id": "S02", "section": "setup", "setup": "corridor", "size": "insert",
     "faces": [],
     "frame": "Insert of Watson's gloved hand clenched on the silver head of his stick as he walks, the stiff leg dragging; flagstones passing beneath; mid-start of the corridor.",
     "motion": "Tracking beside the hand at walking pace; the stick plants and lifts once; the leg drags."},
    {"id": "S03", "section": "friction", "setup": "corridor", "size": "medium",
     "faces": [],
     "frame": "Over Watson's shoulder from behind, mid-corridor: Stamford two paces ahead, half turning his head back; the narrow side-door STILL FAR AHEAD, small. Nobody has reached the door.",
     "motion": "Slow push forward following them; Stamford half turns his head back; the far door grows only a little nearer."},
    {"id": "S04", "section": "friction", "setup": "corridor", "size": "full",
     "faces": [],
     "frame": "Full shot from behind, the two men small in the long corridor walking away toward the far side-door, Watson a half pace behind with his stick, bars of grey light across the flagstones; MIDDLE of the corridor.",
     "motion": "Locked off; the two figures walk steadily away, Watson's limp visible; Stamford does not turn round."}
  ]
}
```

`placed.json` derived from it (the first 20 s), the SOURCE of every shot time:

```json
{
  "runtime_s": 23.28,
  "shots": [
    {"id": "S00", "lane": "dialogue",  "t_start": 0.00,  "t_end": 3.69,  "seconds": 3.69, "frames": 90,  "lines": [0], "audio": "episodes/ep01/lines/l00.wav"},
    {"id": "S01", "lane": "narration", "t_start": 3.69,  "t_end": 7.62,  "seconds": 3.93, "frames": 107, "lines": [1]},
    {"id": "S02", "lane": "narration", "t_start": 7.62,  "t_end": 11.82, "seconds": 4.20, "frames": 107, "lines": [2]},
    {"id": "S03", "lane": "narration", "t_start": 11.82, "t_end": 18.15, "seconds": 6.33, "frames": 158, "lines": [3]},
    {"id": "S04", "lane": "narration", "t_start": 18.15, "t_end": 23.28, "seconds": 5.13, "frames": 141, "lines": [4]}
  ],
  "lines": [
    {"index": 0, "at": 0.25,  "seconds": 3.19, "rel_path": "episodes/ep01/lines/l00.wav"},
    {"index": 1, "at": 3.94,  "seconds": 3.43, "rel_path": "episodes/ep01/lines/l01.wav"},
    {"index": 2, "at": 7.87,  "seconds": 3.70, "rel_path": "episodes/ep01/lines/l02.wav", "note": "estimate until rendered"},
    {"index": 3, "at": 12.07, "seconds": 5.83, "rel_path": "episodes/ep01/lines/l03.wav"},
    {"index": 4, "at": 18.40, "seconds": 4.63, "rel_path": "episodes/ep01/lines/l04.wav"}
  ]
}
```

`frames` = `h3.frames_for(seconds + 0.25)` for narration (the i2v handle that
exists today) and `h3.frames_for(seconds)` for dialogue (the 0.5 s handle is
already inside `seconds`); the legal grid (`frames % 17 == 5`) overshoots by
up to 16 frames and `assemble.picture` trims to `seconds`, as now.

Where the whole 29-line plan lands: the measured lines average 4.0 s; 29 lines
~ 116 s of speech + 30 x 0.5 s handles + breaths + a 1.5 s beat before the
button + a 4 s coda ~ 138 s. Inside 120-180 with no hole. Its six dialogue
lines are ~18 % of speech, above the 10 % dial: merge Stamford's two closing
lines into one take, or narrate Watson's question, to get to 10-13 %.

## 2. The pipeline order

```
say_lines -> timeline -> frames -> storyboard:grids -> shots -> storyboard:review -> assemble -> qc
```

| script | change |
|---|---|
| `say_lines.py` | Reads `plan.lines` only (no `at`). Voice through `audio_indextts2_tts_single_speaker` (the workflow exists in `comfy_studio/workflows/audio/`; `studio/voice.py` gets a second clone function beside the Qwen3 one, the cast `design.wav` as the prompt audio). Still: all renders, then all listening; WER <= 0.20; one re-roll. Output unchanged in shape: `lines/lines.json` with measured `seconds`. Drops the `at` field. |
| `timeline.py` (NEW) | `lines.json` + plan -> `episodes/epNN/placed.json` by the brick above (promoted out of `work/`: it is now an input, not a record). Runs the measured validators (§3) and refuses before anything is drawn. Pure functions in `studio/episode_timeline.py`: `derive(plan, lines) -> placed`, testable with a fake `lines.json`, no model call. |
| `frames.py` | Unchanged. |
| `storyboard.py` | Panel order from plan shots (unchanged). A dialogue shot's `frame` states "mouth closed, about to speak" so the start frame is neutral; `episode_board.prompt` marks it `Panel k (speaking shot)`. `--review` unchanged. |
| `shots.py` | Two lanes from `placed.json`. Narration: `video_minimax_h3_i2v_turbo` from the panel, `frames` from `placed`. Dialogue: the audio-driven H3 workflow the other agent is proving (candidates on disk: `video_minimax_h3_r2v_turbo_voice*`; the constant is `DIALOGUE_WORKFLOW`), inputs = panel + `lines/lNN.wav`, `frames = frames_for(line.seconds + 0.5)`. Run card gains `lane` and `audio`. Takes are grouped by lane so a lane that loads different weights pays ONE swap, not one per dialogue shot. |
| `assemble.py` | `schedule()` and `BREATH` deleted; `picture()` trims every take to `placed.seconds`; lines laid at `placed.at`; the dialogue take's own audio track is discarded and the line wav laid at `t_start + 0.25` (same file the take was driven by, so the mouth and the sound are the one recording). `bed`, `mix_with_lines`, `tail`, `trim` unchanged. Nothing is ever dropped. `BED_SECONDS` becomes `runtime_s` rounded up. |
| `qc.py` | `planned_cuts` from `placed.json`; adds line-onset check on the master (§3); `longest_gap_s` must be <= 2.0 and `speech_s / seconds >= 0.80`; `speech_s`, `dialogue_s` reported as the dial readings. |
| `episode.py` | `STEPS` gains `timeline` after `say_lines`. The queue check stays before `shots`. |
| `studio/episode_spec.py` | Structure only: sections, setups, faces/size bindings, words <= 18, the line->shot binding, `beat_s`/`coda_s` caps. Removes `WORDS_PER_SECOND`, `planned_seconds`, `shot_at`, `button().at`, the tiling check. |
| `SKILL.md` | §1 rewritten for lines-first; §7's scheduling paragraph deleted; the brick paragraph loses "no hole longer than 3 s" and gains "silence only where named". |

`storyboard` stays the one paid step. Nothing new spends.

## 3. Validators: planned seconds -> measured seconds

Structural (still in `episode_spec.py`, no seconds needed):

- exactly one hook / turn / button section; the button line's speaker is not
  the protagonist; the button line sits on the button shot (via `line.shot`).
- every line names an existing shot; a dialogue shot holds one dialogue line
  and its speaker is in `faces` at `close`/`medium_close` (F1 inverted); a
  narration shot holds 1-2 narration lines; a shot with no line has `beat_s`
  or is the coda; `beat_s <= 1.5`; `coda_s <= 4`; 2-3 speakers; <= 3 setups.
- words <= 18 per line (kept: it is the writer's wall, not a clock).

Measured (new `studio/episode_timeline.py`, run by `timeline.py` on
`lines.json`, refusing before the paid step):

| today (planned) | tomorrow (measured) |
|---|---|
| `duration_s` in 80-150 | `runtime_s` in 120-180 |
| `_shots_tile_the_runtime` | tautological: deleted |
| `_no_hole_in_the_voice`, `MAX_SILENCE 3.0` | structural: the only gaps are 0.5 s handles, breaths and named beats; QC confirms `longest_gap_s <= 2.0` on the master |
| silence before the button >= 2.0 | the shot before the button has `beat_s = 1.5` (0.25 + 1.5 + 0.25 = 2.0) |
| `speech_share <= 0.92` | `speech_s / runtime_s >= 0.80` (the cap inverts: silence is bounded above by construction, so the check catches a writer who beats everywhere) |
| `vo_share <= 0.60` of runtime | `dialogue_s / speech_s` in `DIALOGUE_SHARE = (0.05, 0.20)`, the 90/10 dial, one constant |
| hook ends by 5 s, setup by 15 s | same, on derived `t_end` |
| turn at 50-70 % | same, on derived `t_start / runtime_s` |
| T1 (line not within 0.25 s of a cut) | structural: LEAD = TRAIL = 0.25 |
| `MIN_SHOT 1.0` | narration shot 3-8 s measured; dialogue shot = line + 0.5; a single line <= 6.5 s measured (the longest measured so far is 5.83) |
| — | `frames` legal (`% 17 == 5`) and `seconds_for(frames) >= seconds` |

QC on the master (new): each line's wav cross-correlated against its window
of the master audio; the lag must be <= 40 ms of `placed.at`. That is the
"heard on the master" gate turned from words into time — the only check that
proves the mouth and the sound are where the timeline says.

## 4. Storyboard sheets for 120-180 s

Sheets = sum over setups of `ceil(shots_in_setup / 9)` (`episode_board.chunks`
spreads evenly; a sheet never holds more than 9). One gpt-image call per
sheet, the same call as ep01's (2048x3072, plate + character sheets +
previous sheet attached). Dialogue shots take a panel like any other.

| runtime | shots | split (corridor / lab / street) | sheets | calls incl. one redraw |
|---|---|---|---|---|
| 120 s | 25-30 | 7 / 15 / 8 | 1 + 2 + 1 = 4 | 5 |
| 150 s | 30-35 | 8 / 18 / 9 | 1 + 2 + 1 = 4 | 5 |
| 180 s | 35-40 | 9 / 20 / 10 | 1 + 3 + 2 = 6 | 7 |

Ep01 (17 shots) paid 3 sheets + 1 redraw = 4 calls; the whole chapter is 4-6
sheets, at most 7 calls. The repo does not record the per-call price; the
ep01 invoice for 4 calls is the reference to multiply. A setup that crosses
18 shots costs a third sheet, so the writer holds the lab at <= 18 shots
unless the chapter needs more. Takes: ~330 s each on the 4090 (ep01 mean),
30 takes ~ 2.75 h, 35 ~ 3.2 h in one resident round; the dialogue lane's
time per take is unmeasured until the other agent's workflow lands.

## 5. Two risks and the measurement that settles each

**R1 — the driven mouth is late.** The plan lays the line wav at
`t_start + 0.25` and assumes the audio-driven take begins speaking at the
wav's first voiced sample. If the workflow pins a silent head (the H3
continuation notes mention a 22-frame pinned head, 0.92 s) or re-times the
audio, every dialogue shot is a dub that is a fraction of a second off — the
exact ventriloquist defect F1 existed to avoid. Measurement: one dialogue
take from `l00.wav`; per-frame mouth-open ratio (face landmarks on the mouth
box) against the wav's first frame above -40 dBFS; report the lag in frames;
accept <= 2 frames (83 ms). If it fails, `assemble` lays the TAKE's own audio
for dialogue shots instead of the wav, and `placed.at` is read back from the
take.

**R2 — a silent cutaway that moves its lips.** Once on-camera lips mean
"speaking", any lip motion on a narration cutaway that shows a face (S01,
S06, S11, S22 of the ep01 plan show Watson at medium_close under his own VO)
reads as a broken dub; iteration 1 already logged "listener's mouth parts
slightly at the end" on S01. Measurement, zero renders, today: run the same
mouth-open metric over the 17 takes on disk at
`D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\library\20260822113400_a-study-in-scarlet\episodes\ep01_short\shots\T00.mp4` … `T16.mp4`;
report per take the max mouth-open change; the four face cutaways set the
threshold. If more than one of them exceeds it, narration cutaways with a
readable face get "lips sealed" in the take prompt's LOCK line and the review
sheet grows a mouth column; if that does not hold, the plan rule becomes
"no readable face under narration" and the narrator's own close-ups are
dialogue-lane takes driven by silence.

Not a risk, a known loop: the runtime and the turn band are only known after
the audio. A plan that reads right on the page can derive to 118 s or put
the turn at 72 %; the fix is a line added or moved and a re-render of the
lines touched (minutes, free), before any sheet is drawn.

Note on the voice swap: the cast voices were designed and gated for the Qwen3
clone (`/cast-voices`). IndexTTS2 prompting on the same `design.wav` is a
different speaker model; run the existing similarity gate on its first line
before the rest are rendered.
