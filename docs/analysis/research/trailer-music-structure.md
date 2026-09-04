# Research 12 — Music-structure cutting: instrumental and vocal

*Position paper for the `trailer` skill, 2026-09-03. Dimension: how the cut follows
the music's STRUCTURE (beat, bar, phrase, section, hit), and when a book gets a song
with words instead of a cue. Iconic-dialogue/TTS and the adversarial critique are
other papers.*

Every claim is tagged. **MEASURED** = run on this machine on our own cues this week.
**CITED** = a source is linked. **PROPOSED** = follows from the two, not yet tested.

## 0. The brick

A trailer cut is a *metric* object before it is a *loudness* object. The unit the
audience counts is the bar; the unit the editor counts is the phrase (4 or 8 bars);
the events the audience remembers are the few places where the metre is broken —
the stopdown and the hit. Everything below regenerates from one rule:

> **Cut on the grid the music actually keeps; break the grid only where the music
> breaks it.**

The current pipeline cuts to `onsets()` — a loudness-rise grid. It has no bar, no
beat, no phrase. That is why 35 of 44 cuts "on an onset" are, measured against the
tracked beat, only 12 of 44 on a beat and 4 of 44 on a downbeat (§2.1).

## 1. Findings — how the professionals cut

### 1.1 Beat vs downbeat vs phrase vs hit — CITED

- "Cutting to the beat of music is probably the first and most basic stylistic
  choice of an editor" — but "putting literal cuts on the beat can sometimes trap
  you into a predictable editing rhythm". Lieu's preferred unit is the *sync
  point*: "I generally prefer to cut to actions rather than put my cuts on the
  beat" ([Lieu, Elevating Your Trailer Editing](https://www.derek-lieu.com/blog/2021/1/10/elevating-your-trailer-editing-intermediate)).
  He will "'cheat' some audio a few frames for the sake of having it land closer
  to the beat" ([Lieu, Music-video style](https://www.derek-lieu.com/blog/2019/11/26/trailer-music-video-style-editing)).
- The working map an editor makes of a cue is by *section function*, not by beat:
  green = repeats an idea, red = melody changes, cyan = short fills "good for
  cutting in short bursts of action", yellow = "a rise ... before a really big
  beat or hit", purple = "really big beats, big changes"
  ([Lieu, How to Prepare Music](https://www.derek-lieu.com/blog/2017/6/20/how-to-prepare-music-for-editing)).
  That is a five-class section grammar: **plateau / turn / fill / rise / hit**.
- The music stop is "the most useful trick a trailer editor can learn": the bed
  stops on "a natural beat in the music", a line or a visual sits in the hole, and
  the return is sweetened with "drum beats, hits and/or cymbal crashes". Overuse
  makes it "hard for the audience to find their rhythm"
  ([Film Editing Pro](https://www.filmeditingpro.com/the-most-powerful-trailer-editing-technique-you-could-ever-learn/)).
  "Typically on a downbeat the music will simply cut out, or reverb out, and a
  sound effect will enhance or mask the moment" ([Lieu, Sound-design driven](https://www.derek-lieu.com/blog/2021/2/1/sound-design-driven-game-trailers)).
- Library cues are written as acts with a hit-and-silence at each act end:
  Act 1 30s / Act 2 60s / Act 3 60s / Act 4 (button) 5s; Act 3 is "fast edits, big
  drums, huge sounds"; the button is "compressed material from Act 3"
  ([Pryn](https://richardpryn.com/how-to-structure-trailer-music/)). Library
  guidance to composers: "lean builds, flexible transitions, natural rise and
  fall" — editability is the product ([Rareform](https://www.rareformaudio.com/blog/how-production-music-reveals-trailer-structure)).
- The braam is a *musical* event, not an effect: Hemsey's innovation was "to
  include the sound as part of the music rather than as an effect"
  ([BRAAAM](https://en.wikipedia.org/wiki/BRAAAM)). Our `sfx.py` hits are
  therefore reinforcement of a measured cue event, never a substitute — already
  the rule in `08-assemble`.

**What I could not find:** any published count of the *proportion* of trailer cuts
on downbeats vs off-beats. Redfern's corpus (which our arc comes from) has shot
lengths, not audio. The honest position is that the professionals describe
downbeat-and-hit alignment as the skeleton and beat-cutting as the default
texture, and warn against 100% beat-cutting; no one publishes a ratio.

### 1.2 The rise → hit → silence → title grammar — CITED + MEASURED

Three sources agree on the same order (Pryn, Rareform, After Sunset's
"intro / buildup / climax" for trailerized songs). On our own cues the envelope
detector and an independent metre tracker agree where those events are: 26 of
36 `structural_impacts()` sit on a tracked beat (±60 ms) and 16 of 36 on a
downbeat; every `title_moment()` found (3 of 3) is on a downbeat. **The hit is a
downbeat with silence in front of it.** Two measurements that do not share code
say so.

### 1.3 Vocal trailers — CITED

- The trade default is instrumental: "include instrumentals for any vocal
  versions because instrumentals make it easier to hear ... what we're selling,
  the movie." When lyrics are used it is for a *character/thematic* reason
  (Suicide Squad: "the joker ... he's nuts and he tells jokes"). "A good vocal
  will tell the story, whereas a good instrumental will set the tone." Every song
  must "build and build and BUILD as they get near the end"
  ([Vickers, Trailer Park](https://www.marmosetmusic.com/journal/interview-with-music-supervisor-brian-vickers/)).
- Why the trailerized cover works: "the old-comfortable-shoe phenomenon" —
  familiarity plus contrast; the definition is "changing every aspect of the song
  but leaving the lyrics" ([AV Club](https://www.avclub.com/here-s-why-so-many-movie-trailers-use-slowed-down-versi-1847565865)).
  The lyrics survive because they are the *commentary* layer; the arrangement is
  rebuilt into intro → buildup → climax ([After Sunset](https://www.aftersunsetmusic.com/blog/what-does-it-mean-to-trailerize-a-music-track/)).
  The canonical examples — "Creep" for *The Social Network*, "I've Got No
  Strings" for *Age of Ultron*, "Say My Name" for *Candyman*, "It's Nice to Have a
  Friend" for *M3GAN* — are all lyrics that state the film's *thesis or irony*,
  never its plot ([Collider](https://collider.com/movie-trailer-songs-popular-covers/)).
- Vocals and dialogue take turns: "the first line of dialogue doesn't happen
  until after the lyric", the line is placed "between that lyric and the next",
  and where they must overlap "the lyrics lower in volume". Lyric + dialogue +
  graphics "all make space for each other"; it is "extra difficult"
  ([Lieu, Intercutting Dialogue](https://www.derek-lieu.com/blog/2022/9/26/intercutting-dialogue-with-gameplay)).

## 2. Findings — measured on our cues

All eight `cue-*.flac` for *A Study in Scarlet* share one caption stamp
(`c51fab09bf6230be`): same prompt, eight seeds. Tracked with Beat This! `final0`
on CPU, no DBN.

### 2.1 The onset grid is not the metric grid — MEASURED

| grid | on tracked beat (±1 frame) | on downbeat |
|---|---|---|
| the 86 `onsets()` of the chosen cue | 35 (41%) | 16 (19%) |
| the 44 delivered cuts | 12 (27%) | 4 (9%) |
| chance, same tolerance | 12% | 4% |

Cutting to loudness rises lands on the beat about twice as often as chance and on
the downbeat about twice as often as chance. That is not "on the music".

### 2.2 The chosen cue has the worst metre of the usable seeds — MEASURED

Tempo is `60 * (n-1) / (t_last - t_first)` over the tracked beats (the first
draft's column was the median of 60/IBI on a 20 ms grid, i.e. 3000/n — see
§8.1). Bar = median downbeat interval, which is what the cut needs anyway.

| seed | BPM (mean IBI) | bar (s) | bars in modal metre | beat-interval CV | tracker conf. beat / downbeat |
|---|---|---|---|---|---|
| **331107 (chosen)** | 88.7 | 2.72 | **0.51** (4) | 0.23 | 0.92 / 0.89 |
| 770301 | 95.2 | 2.52 | **0.97** (4) | 0.07 | 0.99 / 0.98 |
| 770302 | 123.4 | 1.94 | 0.81 (4) | 0.06 | 0.99 / 0.98 |
| 664410 | 104.2 | 2.38 | 0.67 (4) | 0.16 | 0.96 / 0.96 |
| 920603 | 151.9 | 1.42 | 0.84 (4) | 0.28 | 0.97 / 0.95 |
| 442208 / 553309 | 174.9 / 136.4 | 0.98 / 1.16 | 0.80 / 0.78 (3) | 0.26 / 0.53 | 0.95 / 0.92 |
| 880401 / 910502 | 189.3 / 90.5 | 0.93 / 1.42 | 0.31 / 0.36 | 0.18 / 0.19 | 0.95 / 0.80 |

Three seeds track at a 3-beat "bar" under one second — a 6/8 or triplet feel
read at the fast level, a metre/octave ambiguity the tracker cannot settle on
its own and neither can I without listening (§8.1). What the table shows
without ambiguity: `trailer_fitness()` has no metric term, so it chose the seed
in which only half the bars keep a metre over one in which 97% do. **Select on
measured metre; the caption's BPM (asked 84, delivered 89–189) is not a control.**

### 2.3 Section boundaries — MEASURED, negative

Bar-synchronous agglomerative segmentation (librosa, chroma+MFCC+RMS, k=9) did
not recover the nine authored sections: one block of 57 s, one of 2 s. The
boundaries it did find at 111.5 s and 117.3 s coincide with measured stopdowns
(111.0, 116.2) and an impact (117.35). **Section boundaries are better derived
from envelope events snapped to downbeats than from timbral self-similarity.**

### 2.4 Tooling — MEASURED

- `beat-this 1.1.0` installs clean in a uv venv (Python 3.11, Windows, CPU torch),
  auto-downloads `final0`, and tracks a 150 s cue in **6–11 s on CPU**. MIT
  licence, code and weights. GTZAN F1 89.1 beat / 78.3 downbeat without DBN
  ([paper](https://arxiv.org/abs/2407.21658)). Output frame rate 50 fps = 20 ms,
  finer than our 41.7 ms frame.
- `librosa 0.11.0 beat_track` gives no downbeats; on the chosen cue it agreed
  with Beat This on 37% of beats (73% on the clean 770301). Keep it for features,
  not for the grid.
- `allin1 1.1.0` **does not run here**: it imports `natten1dav`, removed from
  NATTEN ≥0.15, and the only NATTEN that resolves is 0.21.7. It also requires
  madmom from git, whose *models* are CC BY-NC-SA 4.0 ([PyPI](https://pypi.org/project/madmom/))
  — a licence problem for a monetised channel regardless of the build.
- madmom itself: last release 0.16.1 (2018), classifiers to Python 3.7; the git
  head installed but is the NC-licensed path. Not adopted.
- BeatNet (ISMIR 2021, particle filter) not tested; superseded by Beat This on F1.

## 3. Proposed blueprint section (for `03-music` and `08-assemble`)

### 3.1 Measure the metre, then the events — PROPOSED, mechanism MEASURED

`beatmap.py` gains `metre(audio) -> Metre(beats, downbeats, bpm, bars_in_mode,
ibi_cv)` from Beat This. `phrases(metre)` groups downbeats in 4s, re-anchored at
every structural event. `onsets()` stays as the fallback grid for rubato cues.

### 3.2 Seed fitness rewards a *usable* structure — PROPOSED, terms MEASURED

```
fitness = dynamic_range(P95-P5)
        * metric_term       # bars_in_mode >= 0.85 -> 1.0 ; >= 0.65 -> 0.7 ; else 0.4
        * tempo_term        # |tracked/asked - 1| <= 0.10 -> 1.0 ; <= 0.25 -> 0.8 ; else 0.5
        * title_term        # title_moment on a downbeat with stopdown >= 1 bar in front -> 1.0 ; else 0.3
        * lift_term         # envelope rises >= 6 dB over the 2 bars before the title hit -> 1.0 ; else 0.7
        * (0.4 + 0.6 * late_reach)   # unchanged
        * slot_term         # min(slots, 3) / 3 ; slot = trough >= 6 dB below median, held >= 1 bar, in 20-80%
```
Thresholds (0.85 / 0.65 / 0.10 / 0.25) are feel, labelled so. On the eight
seeds this ranks 770301 first on metre, but it has **one** slot; 553309 has
two; 331107 has one (§8.5). No refusal on `bars_in_mode` until the tracker is
validated against human taps on a drumless cue (§8.1); below 0.65 the cut
degrades to the onset grid and the manifest says so.

### 3.3 Author the hit, then find it — PROPOSED

The model executes only nine tags and ~11.1 s a section, so a nine-section sheet
puts the start of section 8 at 7/9 = 78% and section 9 at 89% — inside the
80–90% band the corpus wants the hit in. Author for that, then *measure* where
the downbeat of the return actually fell and conform to it.

**Instrumental sheet** (tags are executable; parentheticals are not sung):
```
[Intro]        (one sustained low note, room tone)                  plateau
[Verse]        (the figure stated once, alone)                       plateau
[Pre-Chorus]   (a pulse enters and does not stop)                    rise
[Chorus]       (first full statement)                                turn
[Instrumental] (the figure answered, ground shifting)                fill
[Bridge]       (everything falls away to one instrument, dry)        stopdown
[Solo]         (the lead alone, slower, then a held silence)         rise -> silence
[Post-Chorus]  (everything returns at once on one downbeat)          HIT
[Outro]        (one low note left to die)                            button
```
The caption prose keeps the two sentences already proven to shape dynamics
("starts near-silent", "hard full stop"). The shipped caption already names
what carries the pulse ("struck objects only") and still returned 0.31–0.97
across seeds, so no caption sentence is claimed to fix the metre (§8.2). The
one change is for the *slots*: the pulse must stop **by section name** — "the
pulse stops entirely inside [Bridge] and for the last bar of [Solo]" — because
a pulse on every downbeat removes the holes the lines need (critic C6).

### 3.4 Vocal sheet — PROPOSED, lyric rules CITED

```
### Vocal Details
One voice, low and close, a slowed cover in feel; the words are few, held long,
and stop entirely under the spoken lines.
[Intro]        (instrumental, room tone)
[Verse]        2 lines, present tense, second person, no names
[Pre-Chorus]   2 lines, the question the book asks
[Chorus]       THE REFRAIN — one line, <= 7 syllables, sung once
[Instrumental] (dialogue slot; no voice)
[Bridge]       one line whispered over near-silence
[Chorus]       THE REFRAIN — full, the first syllable ON the hit
[Outro]        one word, or none
```
Lyric rules: (a) no character or place names, no past-tense narration — the
refrain is the thesis, not the synopsis (Collider examples); (b) the refrain is
≤7 syllables because at 84 BPM one bar is 2.86 s and the measured fill is 2.4
syl/s — a refrain that fits one bar can land on one downbeat; (c) verse fill at
~60% of 2.4 syl/s so the voice leaves bars empty; (d) every spoken line sits in
`[Instrumental]` or between two sung lines (Lieu), never under a sung one; (e)
the second `[Chorus]` first syllable is the title moment — the "lyric drop on the
title". Where it *actually* falls is measured from the vocal stem (demucs 4.1.0,
already resolvable) and the title conforms to it exactly as it does to a hit.

## 4. The decision rule: instrumental or vocal — PROPOSED, premises CITED

Default is instrumental (Vickers). A book earns a vocal trailer only when all
three hold, and each is a measurable property, not a genre:

1. **A thesis line exists.** `trailer-story` writes the book's argument in one
   present-tense line of ≤7 syllables that is *not* an event ("nobody is who
   they say", "the house remembers"). If the best line is a plot beat, no.
2. **Register is eligible.** Nobody owns a book-level register today (critic
   C4). Proposal: `01-story` emits `register` on its structure output with an
   enumerated vocabulary — `procedural | adventure | gothic | tragedy | romance
   | satire | elegy` — decided from the analysis once per book, beside the lead
   and the turn. The field only *gates eligibility* (`procedural` and
   `adventure` sell the how through spoken lines and stay instrumental); it
   never chooses. The genre table in the first draft is withdrawn.
3. **The delivered cue has the slots.** `lines = min(slate, measured slots)`
   (critic C1); the vocal path is on only if the vocal stem leaves ≥2
   instrumental gaps of ≥1 bar in 20–80% — hook and threat need a hole each.

## 5. The cut grid — PROPOSED

Hierarchy of cut points, strongest first. A cut MUST land on a level-0 point
when one exists in its window; it prefers the highest level within tolerance.

```
L0  structural: title hit, structural_impacts, stopdown starts, phrase starts
L1  downbeat
L2  beat
L3  half-beat            (only inside the 80-92% band)
L4  envelope onset       (only when bars_in_mode < 0.65: rubato fallback)
```

Shot lengths are chosen in **beats**, from the arc, then converted to seconds.
The walk below was run on synthetic 4/4 grids at 60–180 BPM and on the two real
tracked cues (§8.3); every branch respects `MIN_SHOT` and the cap.

```
def plan_cuts(beats, downbeats, events, duration, stretch, hold_at=0.15):
    bar, beat = median(diff(downbeats)), median(diff(beats))
    cap  = max(4.0, 1.25 * bar)                       # non-hold shots only
    grid = {L1: downbeats, L2: beats, L3: beats + half-beats}
    cuts, hold_done = [0.0], False
    while cuts[-1] < duration - MIN_SHOT:
        pos    = cuts[-1] / duration
        cands  = {2,4,6,8} if pos<.30 else {1,2,3,4} if pos<.80 else {0.5,1,2} if pos<.92 else {2,4}
        cands  = [n for n in cands if MIN_SHOT <= n*beat <= cap] or [ceil(MIN_SHOT/beat)]
        want_b = argmin_n |n*beat - target_length(pos)*stretch|
        if not hold_done and pos >= hold_at and cuts[-1] is on a downbeat:
            want_b, kind, hold_done = 2*beats_per_bar, HOLD, True   # the ONE exemption: 2 bars, cap 2*bar+beat
        level  = L1 if want_b*beat >= bar else L2 if want_b >= 1 else L3
        landed = nearest(grid[level] beyond cuts[-1]+MIN_SHOT, cuts[-1] + want_b*beat)
        if landed - cuts[-1] > cap(kind): landed = last beat <= cuts[-1] + cap(kind)
        nxt = first event > cuts[-1]
        if nxt and landed >= nxt - MIN_SHOT: landed = nxt           # never step past an L0 event
        landed = quantise(landed); if landed - cuts[-1] < MIN_SHOT: landed = cuts[-1] + max(MIN_SHOT, beat)
        cuts.append(landed)
    return cuts + [duration]
```

Rules that the walk enforces:

- **Phrase = 4 bars, re-anchored at every L0 event.** The `>1.50` length reset
  in `08-assemble` fires at phrase starts; the plateau cap of 6 lives inside a
  phrase.
- **Accelerando in beats, not seconds:** early 2 bars → 1 bar → 2 beats → 1 beat
  → half-beat at 85–90% → the hold. This is the corpus arc expressed on the metre,
  so it survives any tempo.
- **The hold** is exactly one shot of 2 bars starting on a downbeat in the
  first third; it and the title card are the only shots exempt from the cap.
- **The stopdown** is a shot on its own: it starts on the downbeat the bed drops
  on and ends on the return downbeat. A spoken line inside it starts one beat
  after the drop and ends one beat before the return (`05-dialogue` owns the
  line; this paper owns the slot).
- **The title** starts on the hit downbeat — the same rule as today, now with a
  second witness (tracker) for the same instant.
- **Dialogue** occupies whole beats, begins on beat 2 or 3 of a bar (after the
  downbeat, so the cut and the first word are not the same event), and never
  crosses an L0 point.
- **`MAX_SHOT`** becomes `max(4.0, 1.25 * bar)`: at 84 BPM (bar 2.86 s) it stays
  4.0; at 68 BPM (bar 3.53 s) it is 4.41 so a bar-and-a-beat still fits. The
  five consecutive 4.0 s shots at 78–94 s in the shipped cut are what the cap
  does when the onset grid has a hole; a beat grid has no holes. On the real
  331107 grid the walk puts 0 of 57 shots on the cap (shipped: 10/45).
- **Half-beats exist only where they clear `MIN_SHOT`**: `beat/2 >= 0.4` means
  ≤75 BPM. At 84 BPM the climax floor is one beat (0.68 s); at 180 BPM one beat
  is 0.33 s so the floor is two beats. The constants filter the candidate set;
  the arc never overrides them.
- **Rubato fallback** (`bars_in_mode < 0.65`): use L4 and today's algorithm, and
  say so in the manifest. Better: refuse the seed (§3.2).

Gate: `qc.py` measures the **delivered master** — scene cuts from its picture
(`select=gt(scene,0.3)`, blacks subtracted) and beats/downbeats from its own
audio track — and writes `cuts_on_beat`, `cuts_on_downbeat`, `cuts_on_L0` into
the manifest beside the plan's numbers (§8.4 shows the run). Thresholds ≥80% /
≥30% / 100% are numbers to beat, not measurements; and *never* 100% on beat —
the phrase-interior cuts on actions (Lieu) are a plan-level choice the walk
cannot make, so the walk's own output is expected near 95%.

## 6. Libraries to add — versions verified installing on this machine

| package | version | role | licence |
|---|---|---|---|
| `beat-this` | `==1.1.0` | beats + downbeats, no DBN | MIT (code and weights) |
| `torch` | `==2.14.0` (CPU index) | beat-this runtime; GPU not needed at 6–11 s/cue | BSD |
| `torchaudio` | `==2.11.0` (CPU index) | decoding for beat-this | BSD |
| `librosa` | `==0.11.0` | bar-synchronous features, RMS/novelty | ISC |
| `soxr` `==1.1.0`, `einops` `==0.8.2`, `rotary-embedding-torch` `==0.9.1` | | beat-this deps | |
| `demucs` | `==4.1.0` | vocal stem for the vocal path (resolves; not yet run) | MIT |

Add as a `[dependency-groups] music` in `pyproject.toml` with the CPU torch
index under `[tool.uv.sources]` so the GPU stays with ComfyUI. Tests inject a
`FakeMetre`; nothing here calls a paid API. Do not add `allin1`, `madmom`, or
`natten`.

## 7. What I could NOT verify

- Any published ratio of on-downbeat vs off-beat cuts in real trailers.
- Whether MiniMax Music 3 puts the `[Post-Chorus]` return on a *clean downbeat
  with silence in front* more often when the metre sentence is in the caption —
  the 0.51 vs 0.97 split above is across seeds of ONE caption, not across
  captions. One caption A/B (8 seeds each) settles it; costs no credits (local).
- Whether the model sings a ≤7-syllable refrain on the section's first downbeat,
  or leads into it. Needs one vocal render measured on the demucs stem.
- Beat This on drumless, rubato chamber music: the 0.51 figure could be the
  model's failure rather than the music's — the paper itself warns it "performs
  worse on continuity metrics" and on "underrepresented genres". Listening
  test on 331107 outstanding.
- The 2.4 syl/s fill figure was measured on parenthetical *notes*, not sung
  lyrics; the vocal fill ratio (proposed 60%) is a guess.
- The ≥80% / ≥30% gate targets in §5 are numbers to beat, not measurements.

## 8. Rebuttal

**8.1 Tempo column = 3000/n — CONCEDE, then FIX.** Correct: `bpm_median` was
the median of 60/IBI on Beat This's 20 ms output grid, so every value was
3000/n. §2.2 is recomputed from mean IBI (331107: 88.7 not 85.7; 770301: 95.2)
and reports the bar length, which is the quantity the cut uses and is
octave-invariant for the walk. The 3-beat sub-second "bars" on 442208 / 553309
/ 880401 are an unresolved 6/8-vs-fast-4 ambiguity: I cannot hand-tap here, so
the human-tap fixture the critic asks for stays open and the refusal rule is
withdrawn (§3.2). What I can add: the tracker's own confidence at its
predicted beats/downbeats is 0.92/0.89 on 331107 and 0.99/0.98 on 770301, and
onset-strength autocorrelation at the tracked beat lag is 0.65 vs 0.68 —
the tracker is *sure* of the beats it places on 331107; what varies is the
number of them between downbeats. That is consistent with rubato in the music
and with a downbeat model losing the "one" in a drumless texture; the tap test
decides which.

**8.2 Metre sentence already in the caption — CONCEDE.** The shipped caption
says "struck objects only"; 0.31–0.97 is seed variance under it. The causal
sentence is deleted (§3.3). The claim is now "select on measured metre", and
the caption A/B (8 vs 8 seeds, median `bars_in_mode` up ≥0.15) is the only
thing that could restore a caption claim. Critic C6 is adopted in the same
paragraph: the pulse stops *inside* `[Bridge]` and the last bar of `[Solo]`
by name, never "a clear pulse on every downbeat" — that sentence would have
removed the slots.

**8.3 The walk violates its own constants — FIX, shown.** Candidate beat-sets
are now filtered by the constants before the arc chooses (`MIN_SHOT <= n*beat
<= cap`), so half-beats exist only ≤75 BPM and at 180 BPM the floor is two
beats. The hold is exactly one 2-bar shot, on a downbeat, in the first third,
and is the *named* cap exemption (its own cap `2*bar + beat`); the title card
is the other. L0 landing is by construction (`landed = min(landed, next
event)`), not by tolerance. Run on synthetic 4/4 click grids with four
downbeat events at 60/68/84/100/120/150/180 BPM: min shot 1.00/0.88/0.71/
0.58/0.50/0.42/0.67 s (all ≥0.4), max non-hold shot ≤ cap at every tempo
except 68 BPM where frame quantisation lands 4.42 against 4.41 (fix: quantise
the cap up one frame), exactly one hold everywhere, on-cap fraction 0–4%,
every L0 event cut on. On the real tracked grids: 331107 → 57 shots, 0.71 min,
3.67 max, 0 on cap, 93% on beat, 56% on downbeat, 4/4 events landed, not
uniform; 770301 → 62 shots, 95% / 63%, 5/5 events. Note the shot count rises
from 44 to ~57 at stretch 2.5: the coverage economics in `04-shots` must be
re-read against it before this ships.

**8.4 Nothing measures a delivered file — FIX, demonstrated.** Ran the QC on
the shipped master: audio track extracted from the mp4 and tracked; picture
scene cuts from `select=gt(scene,0.3)` (35 found, all 35 within one frame of a
planned cut; the 9 misses are low-contrast cuts, so `qc.py` should lower the
threshold or seed detection from the manifest and *verify* each). Delivered:
12/35 on beat, 4/35 on downbeat; planned cuts against the master's own audio:
14/44 and 5/44. The title impact at 128.95 sits on the master's downbeat at
128.94. The gate now reads the file, and its numbers agree with the plan's
within the scene detector's recall.

**8.5 Slots absent from fitness — FIX, measured.** Slot = trough ≥6 dB below
the median held ≥1 bar starting in 20–80% (6 dB, not the 12 dB stopdown,
because the mix ducks 12–15 dB under a line; the 12 dB hole is only needed
for a line over black). Counted on the eight seeds: 331107 **1**, 770301 1,
553309 2, 880401 5 (sub-second bars), all others 0–1. The critic's number is
confirmed and the metre-best seed is slot-poor, so `slot_term` enters the
fitness (§3.2) and the resolutions are adopted verbatim: `lines = min(slate,
slots)`; vocal path only with ≥2 stem gaps; whole-beat line timing wins at
`bars_in_mode >= 0.65` and `assign_lines(max_span=2)` survives only in the
rubato fallback; a line is chosen for its slot, never `atempo`'d into it; the
pre-title stopdown must hold threat + 2 beats and `title_term` scores it
(331107's is 1.9 s, room for ~4 syllables at 2.4 syl/s — a word, not a
line).

**Register ownership (C4).** Proposed in §4: `01-story` emits `register` with
the enumerated vocabulary; it gates eligibility only; the genre table is gone.
