# The trailer sound chain: what run 10 measured, and what changed

Run 10's master passed every gate it had. The owner's verdict was "all I hear is
music too loud not at all matching tone … it is just some random music .. no
dialogues". Both are true at once, and that is the whole finding: **every number
the gate measured was an average, and a trailer is a shape.**

A sound-designer pass over the delivered file found 92% of the runtime was music
with nothing over it; the single spoken line had been levelled +11.8 dB with a
plain `volume=` into `pcm_s16le` with no ceiling anywhere in the chain (3,096
samples at full scale, flat factor 24.2); the duck covered 250–4000 Hz only, with
a 160 ms attack, so the pulse kept hitting through the one line; `sfx.riser()` had
been in the tree for eleven runs and was never called; the cue faded out over 3 s
into digital silence and the card was struck where the music had died.

This is what the sound chain and the master's shape now do instead, with the
numbers, measured with ffmpeg on this box (ffmpeg 7.1; `ffprobe` is not
installed, so every measurement here comes from `ebur128`, `loudnorm` or
`astats`).

---

## 1. The line chain

`studio/trailer_assemble.py`

A line is now levelled to an **absolute target through a limiter**, never to the
bed and never without a ceiling.

| | run 10 | now |
|---|---|---|
| target | bed's own window + 8 LU | `LINE_TARGET_LUFS = -16.0` integrated |
| ceiling | none | `LINE_TP = -3.0` dBTP via `alimiter` |
| gain bound | `GAIN_LIMIT = 20` | unchanged |

Levelling to the bed's window is what produced a −8.2 LUFS line: the window the
plan chose happened to be the loudest moment of the cue's first half, so the rule
said *shout*. An absolute target cannot do that. The 8 LU of separation the norm
asks for is then made by the duck, which knows exactly how deep it has to go.

`level_line` puts `volume=<gain>dB,alimiter=limit=…:level=disabled` in one chain.
`limiter(ceiling_db)` asks the limiter for `LIMITER_MARGIN = 0.5` dB below the
true-peak ceiling that has to hold afterwards, because `alimiter` is a
sample-peak limiter and intersample peaks run about that much over.

`line_shape(path)` reads back what the file actually is: true peak (from
`loudnorm`), flat factor and crest (from `astats`). Flat factor counts runs of
identical consecutive samples — what clipping leaves behind.

## 2. The duck

The band-split compressor is gone. `DUCK_SPLIT` / `sidechaincompress` are
replaced by a **precomputed envelope**: `duck_db(t, windows)` in Python, and the
same arithmetic as one `volume=…:eval=frame` expression built by `duck_expr`.

Why an expression and not a compressor: every number the rule asks for is then
*exactly* what was asked for. A compressor's depth is a consequence of a
threshold, a ratio and how loud the key happened to be — and run 10's key was
quiet, which is why its deepest duck was 6.2 LU against a rule of 10.

| | run 10 | now |
|---|---|---|
| bands | 250–4000 Hz only | full band |
| attack | 160 ms | `DUCK_ATTACK = 0.02` |
| lookahead | none | `DUCK_PREDELAY = 0.15` (the envelope simply opens early) |
| release | 1000 ms | `DUCK_RELEASE = 0.8` |
| depth | whatever the compressor gave (6.2 LU) | `duck_depth()`: 10 LU minimum, 18 LU maximum, sized to reach `BED_UNDER_LINE = -24` |

The depth is sized against the **loudest** momentary reading of the window
(`bed_peak`), not its mean. This mattered: on the run-10 rebuild the mean under
its one line is −14.8 LUFS and the peak is −9.1, because the line was placed on a
bar the cue puts a hit on. A duck sized to the mean leaves that hit at full
height and the rule reads as met.

`DUCK_DEPTH_MAX = 18.0` exists because past about that the bed is not ducked, it
is gone, and the hole is the worse artefact. A line needing more than that was
placed on a hit — a *placement* fault, which QC's `bed_under_line_lu` names
rather than the mix hiding under a gate.

Commas inside the expression are escaped (`\,`); an unescaped one ends the filter
and ffmpeg then errors on a filter nobody wrote. Verified on this box.

## 3. The master's shape

`studio/trailer_cut.py`, `scripts/trailer/assemble.py`

`title_moment(title_at)` returns `(hard out, hit, card seconds)`. The bed **stops
dead** on the last cut (`gate_expr`, a 20 ms fall — below the ~50 ms where the ear
starts hearing a fade), the card runs on room tone alone for
`PRE_TITLE_SILENCE = 2.2 s`, the synthesised impact lands, and the card holds
`FINAL_HOLD = 4.5 s` past it.

`FINAL_HOLD` was 3.0 — the corpus median last *shot*. Run 10 ended while the hit
was still decaying (momentary −49 LUFS at 104.7 s of a 105.08 s file). A button is
not a shot. It has no knock-on into the picture: `trailer_edit` sizes its own
maximum shot and its own hold, and `FINAL_HOLD` now sizes only the title card.

`PRE_TITLE_SILENCE` is 2.2 rather than 1.5 for a measured reason: the rule that
grades it (momentary ≤ −35 LUFS for ≥ 1.5 s) reads a 400 ms trailing window, so
the first 0.4 s of any silence still carries the music before it. Measured on the
rebuild, 2.0 s of silence reads 1.5 s — exactly on the rule with nothing spare;
2.2 reads 1.7.

`designed_layer()` in the assembler lays four cues where there used to be two:

- **riser** 2.5 s ending on the hard out (`sfx.riser`, first call in eleven runs)
- **sub-drop** 2.4 s ending on the hard out — kept where it always was relative to
  the stop, so it lands *on* the stop rather than inside the silence after it,
  which is what lets the held breath measure as a held breath
- **room tone** across every second after the bed stops (`sfx.room_tone`, new:
  brown noise 40–2500 Hz at `ROOM_TONE_LUFS = -45`). Run 10's pre-title gap was
  digital silence, every sample zero, which reads as a dropped stream
- **impact** 3.0 s on the card

The cue's own `title_impact` is no longer chased. With the no-reuse rule the
picture usually ends before it, and run 10 had `title_impact: null` on every seed
of every caption. The shape is made rather than found.

## 4. Bed and cue mastering

`LIMITING_DB` 5.5 → **2.0**. Five and a half decibels of gain reduction is not a
safety net, it is the sound. The headroom it was buying is made at the source
instead: `shape_bed` peak-limits the bed to `BED_TP = -1.0` dBTP before anything
is summed into it, and every levelled line to −3. `TARGET_LUFS = -14` and
`TARGET_TP = -2` are unchanged, and so is the QC floor of −15.5 … −12.5.

**The level did not suffer.** Re-measured below: the rebuild lands at −14.08 LUFS
/ −1.61 dBTP against run 10's −14.16 / −1.43. Both inside the floor.

## 5. QC measures shape, not averages

`scripts/trailer/qc.py`, `studio/trailer_stage_spec.py`

Every measurement is a pure function over arrays (momentary readings, cut times,
line windows) and is tested on synthetic arrays; the ffmpeg readers are thin and
tested on synthetic audio.

New fields, all defaulting to values that claim nothing so existing constructors
still pass:

| field | target | what it catches |
|---|---|---|
| `music_only_fraction` | ≤ 0.45 | 92% of run 10 was music with nothing over it |
| `longest_music_only_s` | ≤ 15 | the longest stretch that is *not* the final montage |
| `final_music_only_s` | ≤ 20 | the one long stretch the norm allows, at the end |
| `speech_occupancy` | ≥ `speech_target(picture)` | run 10: 0.022 |
| `peak_position` | 0.78 – 0.92 | where the loudest short-term window sits |
| `act3_over_act2_lu` | ≥ +2 | run 10's act 3 was quieter than its act 2 |
| `pre_title_silence_s` | ≥ 1.5 | the held breath before the card |
| `hard_out` | true (**floor**) | the bed stopped, rather than fading into the card |
| `title_hit_lu` | ≥ −25 | a hit that never reached the master, or landed past its end |
| `line_tp` | ≤ −3 (**floor**) | run 10: +0.57 dBTP |
| `line_flat_factor` | 0 (**floor**) | run 10: 24.2 |
| `line_crest_db` | ≥ 10 | speech runs 12–18 dB; a square wave does not |
| `bed_under_line_lu` | ≤ −24 | the loudest the ducked bed gets under each line |
| `cuts_on_beat_by_act` | act1 ≤ 0.5, act3 ≥ 0.8 | replaces the whole-trailer 0.80 |

`cuts_on_beat >= 0.80` across the whole trailer is **removed** from `QC_TARGETS`.
It is the single target that forced a music video: 76% of run 10's cuts were on
the beat with whole-bar lengths, and a viewer starts counting within four shots.
The field is still reported; it is no longer asked for. The per-act pair pulls in
opposite directions, which is what an act break sounds like.

### `speech_target`, and why it is not a flat 0.30

Rule A asks two things that disagree on a short trailer: ≥ 3 lines per 30 s, and
occupancy ≥ 0.30. Three lines of the 1.5–4 s the norm gives them is about 6.6 s —
0.22 of 30 s — and cannot be 0.30 however they are placed. So:

```
speech_target(s) = 0.22                      for s <= 30
                 = 0.22 + 0.08*(s-30)/30     for 30 < s < 60
                 = 0.30                      for s >= 60
```

A 25 s trailer is asked for 0.22 (three real lines). Run 10, at 102 s of picture,
would have been asked for 0.30 and delivered 0.022.

### What QC cannot see, and says so

`bed_under_line_lu` is read from 0.4 s *into* each line window, not from its
start. `ebur128` integrates 400 ms, so a reading at a line's onset is mostly the
bed from before the duck opened. Measured on the rebuild, the same duck reads
4.7 LU of reduction at the onset and 15.0 LU three readings later. That the duck
is already at full depth *when the line starts* is guaranteed by the envelope's
arithmetic (`duck_db`, tested directly) and verified on a rendered file in
`tests/test_line_layer.py`; it cannot be seen at ebur128's resolution, and the
docstring says so rather than pretending.

## 6. What the mix writes down

`lines.level.json` grew from a bare list of `{at, rel_path}` into a document:

```json
{"hard_out": 102.0833,
 "lines": [{"at": 29.755, "seconds": 2.23, "rel_path": "line-0.level.wav",
            "duck_db": -14.9, "bed_peak_lufs": -9.1, "bed_floor_lufs": -24.0}]}
```

QC cannot ask whether the duck was deep enough or the hard out landed unless the
mix records what it chose. `level_sheet()` still reads run 10's list shape,
because that master is the only before-and-after reference this pipeline has.
Paths are relative names beside the master; nothing absolute is stored.

---

## Measured: run 10 before, and the same bed and line through the new chain

**Before** is the delivered master at
`library/…_a-study-in-scarlet/trailer/main/TRAILER-a-study-in-scarlet.mp4`, read
with the new QC readers (read-only; nothing under `library/` was written).

**After** is a synthetic master built in the scratchpad from the *same* bed
(`music/cue-3002.flac`), the *same* raw voice take (`voice/lines/00-0.wav`) at the
same 29.755 s, over black picture of the same 102.08 s, through the new chain and
the new tail. Free — ffmpeg only, no render, no credits.

| measurement | before | after | target |
|---|---|---|---|
| `line_tp` (dBTP) | **+0.57** | **−3.20** | ≤ −3 (floor) |
| `line_flat_factor` | **24.23** | **0.0** | 0 (floor) |
| `line_crest_db` | 8.24 | **13.58** | ≥ 10 (speech: 12–18) |
| `bed_under_line_lu` | −18.1 | **−28.2** | ≤ −24 |
| `hard_out` | **false** | **true** | true (floor) |
| `pre_title_silence_s` | **0.0** | **1.7** | ≥ 1.5 |
| `act3_over_act2_lu` | −0.61 | −0.17 | ≥ +2 — still missed |
| `peak_position` | 0.312 | 0.525 | 0.78–0.92 — still missed |
| `music_only_fraction` | 0.958 | 0.958 | ≤ 0.45 — unchanged |
| `speech_occupancy` | 0.022 | 0.022 | ≥ 0.30 — unchanged |
| `longest_music_only_s` | 40.5 | 40.5 | ≤ 15 — unchanged |
| `integrated_lufs` | −14.16 | −14.08 | −15.5 … −12.5 |
| `true_peak` (dBTP) | −1.43 | −1.61 | ≤ −1.0 |
| `title_hit_lu` | −9.9 | −9.5 | ≥ −25 |
| master seconds | 104.95 | 108.70 | — |

Read honestly:

- **Everything the sound chain owns is fixed.** The line no longer clips, its
  crest is back in the speech range, the bed is 10 LU further out of its way, the
  bed stops instead of fading, and there is a held breath before the card.
- **The level did not suffer** from `LIMITING_DB` 5.5 → 2.0: −14.08 LUFS, well
  inside the floor, with 0.2 dB more true-peak headroom than before.
- **`peak_position` moved for an interesting reason.** Run 10's loudest
  short-term window was at 31% of the picture — not its chorus, but the clipped
  line itself, at −8.2 LUFS. With the line at −16 the cue's own chorus at ~54 s
  wins instead, which is 0.525. Still not 0.78–0.92: that is the *cue's* shape,
  and it is fixed by asking for a different cue, not by mixing.
- **Four numbers did not move, and could not.** `music_only_fraction`,
  `speech_occupancy`, `longest_music_only_s` and `act3_over_act2_lu` are
  properties of how many lines were placed and what the cue does — one line over
  102 s stays one line over 102 s however it is levelled. These now *fail loudly*
  where before nothing measured them at all, which is the point: the pipeline can
  no longer ship 92% music-only and call it a pass.

## Rules not implemented here, and why

- **A: ≥ 8–12 lines per 100 s, Watson VO, declared cards rendered.** Owned by
  steps 04/05 and the plan. This work makes the failure measurable
  (`speech_occupancy` vs `speech_target`) but cannot write lines.
- **C: pulse-free intro, ≥ 2 deliberate drop-outs mid-trailer, cue hits in
  65–95%, a tempo change, beat-grid gaps.** Properties of the *cue*; owned by the
  music step. `peak_position` and `act3_over_act2_lu` flag the consequence.
- **E: SFX on ≥ 30% of act-3 cuts, ≥ 6 designed layers per 100 s.** The designed
  layer went from 2 cues to 4 and room tone now covers every deliberate silence,
  but per-cut whooshes need the cut list, which is the editor's.
- **F: reauthored caption written in full to `music/cue-{seed}.caption.json`.**
  The music step owns what it sends.
- **G: cut-interval variance, act-1 off-beat share.** `cuts_on_beat_by_act` now
  measures the act split; the cut list itself is the editor's.
- **B: "line on a shot whose cast holds the speaker".** Needs the plan's cast,
  which the editor owns.
- **D: "title hit offset ≤ ±0.25 s of a downbeat".** By construction the card is
  now struck 2.2 s after a hard out at the last cut, which is where the picture
  ends, not where a downbeat is. `title_on_downbeat` is still reported and will
  usually be false; that is a deliberate consequence of choosing a made shape
  over a found one, not an unmet rule.
