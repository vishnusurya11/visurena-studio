---
name: trailer-music
description: Generate the cue, MEASURE its metre and events, select the seed on structure, and cut on the grid the music actually keeps. Instrumental by default; vocal when the book earns it.
---

# Music

`studio/beatmap.py`, `studio/music_tone.py`, `scripts/trailer/build_music.py`,
`studio/trailer_edit.py`. Evidence: `docs/analysis/research/trailer-music-structure.md`
and `trailer-debate-verdicts.md`. Tags: **MEASURED** on our own cues,
**CITED**, **PROPOSED** (named test not yet passing).

## The brick — a cut is a METRIC object before it is a loudness object

> Cut on the grid the music actually keeps; break the grid only where the
> music breaks it.

The audience counts bars; the editor counts phrases (4 bars); the events the
audience remembers are where the metre breaks — the stopdown and the hit.
Every rule below is that sentence folded over the cue's event list.

**MEASURED, why this section exists:** the shipped Scarlet cut had 35 of 44
cuts "on an onset". Against the tracked beat it had **12 of 44 on a beat and
4 of 44 on a downbeat** — chance is 12% / 4%. The delivered master, scene-
detected and tracked from its own audio, agrees: 12/35 and 4/35. `onsets()`
is a loudness-rise grid. It has no bar, no beat, no phrase.

## Measure the metre, then the events

`beatmap.metre(audio) -> Metre(beats, downbeats, bpm, bar, bars_in_mode,
ibi_cv, confidence)` from **Beat This!** (`beat-this==1.1.0`, MIT code and
weights, 6–11 s per cue on CPU, 20 ms grid). `phrases(metre)` groups
downbeats in fours, re-anchored at every structural event.

- Tempo is `60·(n−1)/(t_last − t_first)` over tracked beats. **Never** the
  median of 60/IBI on the 20 ms grid — that is 3000/n and carries octave
  doubles (the first draft's 187.5 was 93.7 twice).
- The cut uses the **bar** (median downbeat interval), which is octave-
  invariant. Report bpm; walk in bars.
- **The metre is not a caption control.** Eight seeds of ONE byte-identical
  caption ranged 0.31–0.97 bars-in-mode and 89–95 real BPM against 84 asked.
  Select on the measured metre; do not write sentences and hope.
- `onsets()` stays as the rubato fallback (`bars_in_mode < 0.65`). The
  manifest says which grid cut the trailer.
- Do NOT add `allin1` (NATTEN API removed), `madmom` (models CC BY-NC-SA),
  or `natten`. `librosa` is for features only — it agreed with Beat This on
  37% of beats on the drumless cue.
- Timbral self-similarity does not recover authored sections (MEASURED,
  negative). Sections are envelope events snapped to downbeats.
- **Open:** a hand-tapped 16-bar fixture for the drumless seed. Until it
  exists the tracker's `bars_in_mode` is an opinion about a rubato cue, and
  no seed may be *refused* on it — only ranked.

## The seed is chosen on STRUCTURE — never on filename, never on peak

```
fitness = dynamic_range(P95 − P5)
        × metric_term    # bars_in_mode ≥ .85 → 1.0 ; ≥ .65 → 0.7 ; else 0.4
        × tempo_term     # |bpm/asked − 1| ≤ .10 → 1.0 ; ≤ .25 → 0.8 ; else 0.5
        × title_term     # title_moment on a downbeat, ≥1 bar quiet in front,
                         # AND the pre-title trough holds threat + 2 beats → 1.0 ; else 0.3
        × lift_term      # ≥ 6 dB rise over the 2 bars before the hit → 1.0 ; else 0.7
        × slot_term      # slots ≥ 2 → 1.0 ; 1 → 0.7 ; 0 → 0.4
        × (0.4 + 0.6 × late_reach)
```
A **slot** is a trough ≥ 6 dB under the median, held ≥ 1 bar, starting in
20–80%. Slots are where lines live (`05-dialogue`); the metre-best Scarlet
seed had ONE slot and the plan wanted four. Thresholds are feel — the ranking
they produce is tested (`test_fitness_ranks_metric_seed_above_rubato_seed`,
`test_fitness_prefers_cue_with_two_slots`).

Render 3–8 seeds. Pin `duration` — it is a second seed (waveform correlation
between durations −0.03). Iterate on seed alone.

## MiniMax Music 3 facts (MEASURED, unchanged)

- Only nine executable tags: `Intro Verse Pre-Chorus Chorus Post-Chorus
  Bridge Instrumental Solo Outro`. Anything else is read as lyrics or noise.
- **Section count sets length** (~11.1 s each; nine ≈ 100 s). Not `duration`.
- Caption prose sets dynamic shape: "starts near-silent … hard full stop"
  gave 9.7 LU and 9 stopdowns; "relentless throughout" gave 4.0 LU and 3.
- Exclude vocals by saying nothing about voices. Negation produces humming.
- Filler in section notes is read as instructions; shared padding once
  contradicted `[Outro]` and killed every stopdown (9 → 1).
- Caption 250–450 words, three headings; the cue is stamped with the caption
  digest (`caption_stamp`) so a new caption cannot reuse an old file.

## The instrumental sheet — author the hit at section 8 of 9, then FIND it

```
[Intro]        (one sustained low note, room tone)           plateau
[Verse]        (the figure stated once, alone)                plateau
[Pre-Chorus]   (a pulse enters and does not stop)             rise
[Chorus]       (first full statement)                         turn
[Instrumental] (the figure answered, ground shifting)         fill
[Bridge]       (the pulse STOPS; one instrument, dry)         SLOT
[Solo]         (the lead alone; the last bar is silence)      rise → silence
[Post-Chorus]  (everything returns at once on one downbeat)   HIT
[Outro]        (one low note left to die)                     button
```
Section 8 starts at 7/9 = 78% — inside the 80–90% band the corpus wants the
hit in. Then **measure** where the return downbeat fell and conform the title
to it (`test_post_chorus_downbeat_lands_in_hit_band`: ≥ 6 of 8 seeds in
0.75–0.92, PROPOSED).

The pulse stops **by section name** inside `[Bridge]` and the last bar of
`[Solo]`. Never ask for "a clear pulse on every downbeat" — that sentence
deletes the slots the lines need. For a drumless tone the caption must name
what carries the pulse (struck objects, a walking bass); it is a request, not
a control.

## The vocal path — lyrics are the thesis, never the synopsis

Instrumental is the trade default (Vickers: "a good vocal tells the story, a
good instrumental sets the tone"). Every canonical trailer song — "Creep" for
*The Social Network*, "I've Got No Strings" for *Ultron* — states the film's
thesis or irony, never its plot. The lyric is the commentary layer.

A book is **eligible** for a vocal cue only when all three hold:

1. `01-story` emitted a **thesis line** — present tense, ≤ 7 syllables, names
   nothing, not an event ("nobody is who they say").
2. `01-story` emitted `register` in the vocabulary that gates eligibility
   (elegy / gothic / romance / coming-of-age / tragedy). Procedural, detective
   and comedy sell the *how* through spoken lines; the voice would compete.
3. The delivered cue's **vocal stem** (`demucs==4.1.0`) has ≥ 2 gaps that are
   slots. Vocals and dialogue take turns (Lieu); a line never sits under a
   sung word.

```
### Vocal Details
One voice, low and close; few words, held long; silent under the spoken lines.
[Intro]        (instrumental, room tone)
[Verse]        2 lines, present tense, second person, no names
[Pre-Chorus]   2 lines, the question the book asks
[Chorus]       THE REFRAIN — one line, ≤ 7 syllables, sung once
[Instrumental] (dialogue slot; no voice)
[Bridge]       one line whispered over near-silence
[Chorus]       THE REFRAIN — full; the first syllable IS the hit
[Outro]        one word, or none
```
≤ 7 syllables because one bar at 84 BPM is 2.86 s at the measured 2.4 syl/s
fill (measured on notes, not sung words — PROPOSED for lyrics). Where the
refrain's first syllable *actually* lands is read from the stem
(`test_refrain_first_syllable_on_downbeat`, within 60 ms) and the title
conforms to it exactly as it conforms to a hit. The genre table that once
lived here is withdrawn: eligibility is the three measurable properties above.

## The cut walk — in BEATS, not seconds

Hierarchy, strongest first. A cut MUST land on every L0 point; between them it
takes the highest level within reach.

```
L0  structural: title hit, structural_impacts, slot starts/ends, phrase starts
L1  downbeat
L2  beat
L3  half-beat        (only ≤ 75 BPM, only in the 80–92% band)
L4  envelope onset   (rubato fallback only, bars_in_mode < 0.65)
```

```
plan_cuts(metre, events, duration, stretch):
    bar, beat = metre.bar, metre.bar / metre.beats_per_bar
    allowed(pos) = {n : MIN_SHOT <= n*beat <= cap(bar)} intersect
                   (pos<.3: {2,4,6,8} | .3-.8: {1,2,3,4} | .8-.92: {.5,1,2} | >.92: hold)
    cuts = [0]
    while cuts[-1] < duration - MIN_SHOT:
        want    = round_to_allowed(target_length(pos)*stretch / beat, allowed(pos))
        nominal = cuts[-1] + want*beat
        landed  = nearest(grid[level(want)], nominal)
        landed  = min(landed, next_event_after(cuts[-1]))     # L0 by construction
        cuts.append(quantise(landed))
        if is_phrase_start(landed): next shot >= 1.5 x previous  # the reset
```

- Candidates are filtered by the constants **before** the arc chooses, so the
  walk cannot emit a shot under `MIN_SHOT` (0.4 s) or over the cap at any
  tempo. MEASURED on click grids 60–180 BPM: min shot 0.42–1.00 s, exactly
  one hold, on-cap fraction 0–4%, every L0 event cut on. On the real Scarlet
  grid: 57 shots, 0 on cap, 93% on beat, 56% on downbeat, 4/4 events.
- **The hold** is exactly one 2-bar shot on a downbeat in the first third —
  the named cap exemption (its own cap `2·bar + beat`). The title card is the
  other exemption. Nothing else may exceed the cap.
- `MAX_SHOT = max(4.0, 1.25·bar)`, quantised UP one frame (68 BPM: 4.42 s).
  At 84 BPM it stays 4.0. On the onset grid the cap *filled holes* (five
  consecutive 4.0 s shots at 78–94 s; 10 of 45 shots exactly at the cap). A
  beat grid has no holes; the cap becomes a safety net.
- Accelerando in beats: 2 bars → 1 bar → 2 beats → 1 beat → half-beat at
  85–90% → the hold. The corpus arc on the metre, so it survives any tempo.
- A **slot is a shot of its own**: starts on the downbeat the bed drops on,
  ends on the return downbeat. The line inside starts one beat after the
  drop, ends one beat before the return (`05-dialogue` owns the line).
- Never 100% on beat — phrase-interior cuts on *actions* (Lieu's sync points)
  are what stop it reading as a metronome.
- The walk produces ~57 shots at stretch 2.5 where the onset grid produced
  44. Re-read `04-shots` coverage economics before shipping it.

## QC reads the DELIVERED file, never the plan

`qc.py` extracts the master's audio, tracks it, scene-detects the picture
(seeded from the manifest and *verified*, threshold below 0.3 — 9 of 44
low-contrast cuts were missed at 0.3), and reports `cuts_on_beat`,
`cuts_on_downbeat`, `cuts_on_L0`, `on_cap_fraction`, `title_on_downbeat`.
Targets (PROPOSED, numbers to beat): ≥ 80% / ≥ 30% / 100% / ≤ 10% / true.
A gate whose expectation comes from `plan.json` is the plan grading itself.

## Dependencies

`[dependency-groups] music`: `beat-this==1.1.0`, `torch==2.14.0` and
`torchaudio==2.11.0` from the CPU index under `[tool.uv.sources]` (the GPU
stays with ComfyUI), `librosa==0.11.0`, `soxr==1.1.0`, `einops==0.8.2`,
`rotary-embedding-torch==0.9.1`, `demucs==4.1.0`. Tests inject a `FakeMetre`;
nothing here calls a paid API.
