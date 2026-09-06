# The trailer is cut to the cue: a music-first pipeline

*Synthesis of five research lenses (audio analysis, editor practice, the cue as
a plan, shots for the music, pipeline redesign) written against the run-10
master and the nine candidate cues of A Study in Scarlet. Every number below is
either measured on those files or marked FLAG.*

## 0. The owner's instruction, and what it means

> "analyse the audio and see where the cuts can go … the shots can be more than
> 3 seconds … first plan the music for the trailer and build shots that go there"

Today every stage of the pipeline invents a cut of its own: step 03 grades a
cue by its beat grid, step 06 walks bar counts per act (`ACT_BARS`), step 07
renders one take per shot at the length the walk chose, step 08 re-fits when
takes fail. The music is a bed the picture lies on. The run-10 audit measured
what that produces: 51 shots, three over 3 s, 28 % of cuts on a structural
event at 0.1 s (chance 11 %), a cut inside every one of the cue's six hold
spans, a hit 2.12 s inside a shot.

## 1. The brick

**Base case.** The render budget is a number of H3 frames. Frames buy picture
seconds; picture seconds bound the cue length that is asked for.

**Recursive rule.** *Cut on the highest-class event the cue offers; between
events, hold.* A shot's length is not chosen: it is READ off the distance to
the next event of the class the position affords. Sections open with the
widest frame and the reveal on the downbeat; sustains (the long shots) hold a
single move through a trough; phrases carry one fact; accents are inserts;
the stopdown answers a set-up line; the button plays out to the hard out.

**Closure.** Once the cue's measured spans ARE the shot list, nothing
downstream of step 03 invents a cut. Step 06 fills spans with story, step 07
renders one take per span, step 08 removes a span the way an editor would
(absorb an accent, splice the cue on a bar line, move the hard out), never by
re-walking. The 25 s short is bar blocks of the same verified cue.

The previous brick (no shot is ever reused; the cycle is measured, never
typed) is unchanged and sits underneath this one.

## 2. Three objects, and who owns each

| object | made by | from | consumed by |
|---|---|---|---|
| `CueAsk` | step 03, derived | frame budget → seconds → bars → 25/45/30 | caption generation; `verify()` against the render |
| `CutMap` | `studio/music_events.py` | the rendered cue (audio in, JSON out) | `spans_of` in step 03; QC |
| `CuePlan` | step 03 `ship` | CutMap + Metre, fitted to the ask | steps 04, 06, 07, 08, QC |

**CueAsk** (03 §4): bar-indexed sections each with `level`, `pulse`,
`density`, `cut_unit_beats`; events `pulse_in`, `hole`, `hit`, `stop`,
`title_hit`, each pinned to a bar; `ending`, `staircase`, `verdict_floor`.
Forms come from the register table (nine rows: BPM, mode, intro bars, pulse
entry, build shape, hole placement, ending). `verify()` fills `measured_*`
per event from the CutMap. The ask is derived, never typed: bars =
seconds / bar, bars split 25/45/30 (FLAG), events land on section starts.

**CutMap** (01 §6): sections by Foote novelty on MFCC+chroma with a
checkerboard kernel of `clip(seconds/6, 12, 24)` s; phrase novelty at 8 s;
`level_steps` (2 s windows, ≥ 6 dB); `dropout_spans`; `swells`; `accents` =
top-10 % onsets (85 % on-beat vs 19 % chance); `snap` ±0.6 s to a downbeat or
accent — mandatory, novelty says WHICH bar, the grid says WHERE; `merge`
within 0.3 s; `hold_spans`; `hard_outs`. Events carry `rank` 3/2/1, spans are
`hold | swell | dropout`. Robust: sections F1 0.87, phrases 0.82–0.92,
lifts/drops 0.83/0.80. Noise, excluded: chord changes (24/min, on-beat at
chance), band entries at 6 dB. `metre.json` alone is insufficient: 67 % of
section boundaries lie > 1 s from every hit/stopdown/lift/drop.

**CuePlan** (05 §2, contract in `studio/cue_plan.py`):

```
CueSection(index, start, end, movement, pulse, level_db)
CueSpan(index, start, end, kind, section, movement, bars, opens_on,
        level_db, onset_density, rises_db, line_room)
CuePlan(rel_path, seed, seconds, bpm, bar, sections, spans, hard_out,
        title_hit, asked)
kind ∈ section | phrase | accent | sustain | trough | tail
```

Validators: spans contiguous from 0 to `seconds`; every section start is a
span start; a `sustain` is ≥ `SUSTAIN_BARS` (FLAG 2); an `accent` ≤ one beat;
no span shorter than `MIN_SHOT`; movements never decrease; `hard_out` is the
start of the last span. `picture_spans()` is every span but the tail;
`by_movement()` groups them.

## 3. Frame budget

A take is the shot plus the head trim and handle: `take = shot + 2.85 s`
(69 frames of tax per take). `frames = legal_frames(ceil(24·take))` — H3 only
renders f ≡ 5 (mod 17), max 362. A cycle is `a + b·frames` with `b = 2.49
s/frame` FLAG — the AICU figures (124/243/362 f = 16.4/48.1/97.2 min at 20
steps) say render time may be superlinear, so price with the pessimistic
curve until round 1 measures one 243-frame take. `learn_cycle` must record
`frames` on every cycle row.

Longer shots are cheaper per picture second: 24 s as 12 × 2 s costs 1488 f;
as 3 × 8 s it costs 831 f. A 60 s trailer at the music-first mix ≈ 100–115
min, inside the 210-min share.

`affordable_frames(remaining, cycle, takes, reserve)` → the picture seconds
the budget affords → `seconds_for_cue` → the CueAsk length. Nothing else in
the pipeline sizes anything.

## 4. Fit rule — the cue bends, the story does not

When the rendered cue offers more spans than the frames afford
(`plan_fit`): drop accents, latest first → merge phrases inside a section,
earliest first → never touch a sustain or a trough → refuse to step 03
(`shorter_cue` rung: ask again with fewer bars). Section bounds must stay
within `SECTION_TOL` (FLAG 1 bar) of the ask.

## 5. Shot grammar per span class

| span | length | the shot |
|---|---|---|
| section | 1–1.5 bars | widest frame, new location or first face; the reveal arrives ON the downbeat |
| sustain | 5–10 s (cap 10, ceiling 12.2) | ONE camera move + three time-phased actions (open / middle / final-second look-up) + what stays still; the line sits in the trough and ends ≥ 1 beat before the span ends |
| phrase | ½–1 bar | one fact, one motivated move |
| accent | < 1.5 s | insert or ECU, no bound face |
| stopdown | the silence | a static answer to a set-up line |
| tail / button | 5–8 s | plays out to the hard out; the card is struck after it |

`speaker_mode ∈ listening | look_up | ots | profile | walking_away | wide |
two_shot`. No two sustains adjacent. One generation per sustain, never two
stitched. In-take `CUT TO` is an off-by-default experiment. Corpus: long
shots are structural (≈ 5 % > 3 s; 1–3 per trailer at the opening, after
the turn, and the button) and sit 11.6 dB below median level; density rises
to 60–90 % of runtime then collapses; hits are cut 1–2 frames before; never
cut inside a stopdown. Refuse a cue with no opening sustain, no stopdown or
no pre-title trough.

## 6. QC

Target `cuts_on_events ≥ 0.90` (FLAG). Floors: `section_changes_cut == 1.0`,
`cuts_inside_sustain == 0`, `long_shots_on_sustains == 1.0`,
`lines_in_troughs == 1.0`. Shape: `accents_cut`, `movement_medians_s`,
`frames_rendered / frames_played`. Dropped: `cuts_on_beat_act1`,
`on_cap_fraction` — they graded the walk, and the walk is gone.

## 7. Settle

A lost accent is absorbed by its predecessor (rendered carrying those
frames). A lost phrase or sustain is `splice_out` of the cue on bar lines
(10 ms crossfade), the cue is re-measured and the plan re-derived. A lost
button moves `hard_out`. Every pass removes ≥ 1 span, so settle terminates.

**Built (row 53, `studio/cue_settle.py`), and what changed on contact:**

- Real cues measure as `grid: onsets` with `downbeats == []` (seed 1001) or
  as a metre whose spans sit on events, not bar lines (seed 1003, bar 1.86,
  a span 29.0–29.629). A bar-indexed `splice_out` has no bar to name, so
  the settle cuts **between the two measured times** (`cue_edit.remove_range`,
  seconds-based; the fade is 10 ms on a hit, half a beat otherwise) and the
  plan is **shifted, not re-measured**: every later span, section, the hard
  out and the title hit move up by the cut; the cut map moves with them
  (`shifted_cut_map`). Re-measuring would re-decide the kinds of shots that
  already have takes.
- A lost **section door** is cut out too, not absorbed: absorbing it forward
  would give the successor's take a shot longer than it was rendered.
  Cutting the door's bars keeps every take its length and the successor
  opens the section.
- Two sustains the cut brings together lose the later one as well (and its
  beat): the plan's own rule, kept by construction.
- Losses settle **latest first**; `removed` is the list of ranges on the
  progressively edited timeline, in the order `remove_range` applies them.
- A join the cue refuses (levels differ by > `COMPAT_DB` at the join) falls
  back to the fold with a `gate=settle action=folded` learning row.
- Files: `cue-{seed}-settled.flac` beside the original (44.1 kHz stereo,
  PCM 16), `music/metre.json` re-pointed, `cutmap-{seed}-settled.json`,
  `music/plan.json` rewritten; qc grades against the cut map named after the
  cue that plays (`cut_map_name`).

## 8. `studio/cue_edit.py`

`zero_cross`, `slice_bars`, `splice` (equal-power; beat/2, or 10 ms on a
hit), `repeat_bars`, `hole`, `stop_at`, `section_gains`, `compatible`,
`conform` (a ladder rung between more seeds and reauthor). No stretching.
The short is `slice_bars` of the verified long cue.

**Built (row 56, `studio/cue_conform.py`):** the conform is not a rung but
the gate's own arithmetic. `ShorterCue` used to buy a second render batch
for a cue that had already passed the ask; now `conform_to_budget` folds
what the fit rule can, then cuts the smallest interior span out of the cue
(latest first among equals, never the opening image, never the button) and
re-checks `frame_budget.fits` each time. Only when nothing interior is left
does step 03 re-ask. The audio side is `cut_files` -- the cue, its metre
and its cut map moved together -- shared with step 08's settle. A join the
cue refuses ships the whole cue with a warning. The 25 s short is still
unbuilt: nothing downstream consumes one.

## 9. What is unmeasured (FLAG table)

| constant | typed | measured by |
|---|---|---|
| `b` s/frame | 2.49 | one 243-frame take in round 1 |
| `a` s/take | from run-10 rows | cycle rows with `frames` |
| SESSION / SHEET | 240 s + 20 s | gate=`read` rows |
| RETRY_RESERVE | 15 % | reroll count per round |
| longest_take | 12.2 s | identity at 362 frames |
| SHORT_SHOT | 0.6 | a wrong face read at length |
| SUSTAIN_BARS | 2 | eye |
| SECTION_TOL | 1 bar | verify rows |
| LONG_SHOT | 3.0 | corpus |
| cuts_on_events target | 0.90 | first music-first master |
| 25/45/30 | story spine | first music-first master |
| HOOK_BY / PULSE_DENSITY | 12 s / 0.6 | first music-first master |

**Found while building rows 48-56 (each is a FLAG until a run measures it):**

- Real cues measure as `grid: onsets` with no downbeats (seed 1001) or as a
  metre whose bar (1.86 s, seed 1003, bpm 81.5 against 100 asked) makes the
  ask's bar count and the delivered bar count two different rulers. Every
  bar-indexed edit in `cue_edit` (`remove_bars`, `conform_bars`,
  `hole_bars`) has nothing to name on an onset grid; the seconds-based
  `remove_range` is what rows 53 and 56 use.
- `cue_edit`'s `Recut.metre` is a grid derived from the edit, not a
  re-measurement of the edited audio. A run should re-measure one settled
  cue and diff the two before the grid is trusted for a second edit.
- `structural_impacts` marks the click track's clicks as hits: the
  detector's floor is set against textures, and a click is all transient.
  Fixtures use `metre_of(..., hits=)` explicitly for that reason.
- The pooled frame (`frame_budget` and the research scripts) is 0.2554 s
  measured against 0.25 s typed; `music_events` carries the note.
- A line's room has two rulers: `CueSpan.line_room` is the measured
  dropout's length (`cue_spans.trough_room`) and the plan's `line_windows()`
  (troughs and sustains, a beat short of the span) is what step 04 lays
  lines in whenever `music/plan.json` exists (verified, `line_windows.windows_for`);
  `trailer_dialogue.made_slots` (`LINE_ROOM` 5.4 s plus two beats, capped at
  the next hit) is the no-plan fallback only. Whether a beat short of a
  trough leaves the tail of a 14-word line clear of the return is unmeasured.
- `CAPTION_WORDS` (250, 560) is typed against a measured 5000-token node
  limit; a reauthor adds pulse-carrier and supporting-section text to the
  caption, and whether a reauthored caption stays under 560 is unmeasured.
- `Learning.frames`: verified, one gate=cycle row per fresh take (step 07
  `learn_cycle`), `frames` the take's frames and `measured` its render
  seconds, so `frame_budget.cycle_points` fits per-take points. The
  docstring said "mean"; it now says the take's.

## 10. Build order (BUILD.md rows 43–62)

Contracts first, then the four disjoint modules in parallel, then step
integration in dependency order:

1. `studio/cue_plan.py` contracts (43)
2. `studio/music_events.py` — the cut map (44); `studio/frame_budget.py`
   (45–46); `studio/cue_ask.py` derive/forms/caption/verify (47–48);
   `studio/cue_edit.py` (49)
3. `spans_of(cut_map, metre)`, `plan_fit` (50–51); step 03 `best_of` by
   `verify`, `ship` writes `music/plan.json`, `shorter_cue` rung (52–53);
   step 04 `windows_of(plan)` (54); step 06 `shots_from_spans`, grammar,
   `fit_to_frames`, `counts_by_movement` (55–57); step 07 frames-first,
   `learn_cycle` with `frames` (58); step 08 settle moves (59); QC fields
   and floors (60); remove the walk (61); `MusicBed` measured sections (62).

## 11. Publishable

The cut-opportunity map — audio in, JSON out, librosa only, with the
synthetic-signal test suite as its benchmark — is a standalone package
(`music-cut-map`). Nothing in it knows about books, H3 or this repo.
