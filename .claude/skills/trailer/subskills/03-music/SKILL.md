---
name: trailer-music
description: Write the caption and the lyric sheet, render seeds, MEASURE each one, select on the ask delivered then form before grid, and cut on the grid the music actually keeps. Instrumental always for now — the voice path is BLOCKED on an unpinned dependency. Every ranking term names what SETS the number it reads, reads inside the arc's own mask and in the unit the delivered trailer is graded in, every dimension the step moves has a term that reads it back, every key the ranking reads is written beside its seed, the seed is counted for how many times it lets the trailer SPEAK, and no bar and no landmark is ever heard twice.
---

# 03 — Music (MiniMax Music 3, local ComfyUI)

Code: `scripts/trailer/step_03_music.py`, `scripts/trailer/build_music.py`,
`studio/music_tone.py`, `studio/affirm.py`, `studio/beatmap.py`,
`studio/cue_ask.py`, `studio/cue_arc.py`, `studio/cue_voicing.py`,
`studio/cue_punct.py`, `studio/cue_plan.py`, `studio/cue_spans.py`,
`studio/cue_conform.py`, `studio/music_events.py` — and
`studio/cue_listen.py`, written, tested and imported by nothing (§17). Tags:
**MEASURED** on our own files, **DOCUMENTED** (vendor text, quoted),
**CITED**, **PROPOSED** (a named test not yet passing).

Follow this file top to bottom. Every step is checkable without a HUMAN
listening — which is not the same as without hearing: §17 is the difference,
and it is where every gate that reads its own handwriting is listed.

---

## 0. The three bricks, and the one under them

> **SOUND:** a trailer cue's genre, mood, progression and mix are the
> TRAILER'S, the same for every book — `TRAILER_GENRE`, `TRAILER_MOOD`,
> `TRAILER_ARC` and `TRAILER_MIX` in `studio/music_tone.py`, written into the
> first sentence, the Progression line and the Sonics line by `head()`, and
> they carry INTENSITY WORDS (massive, thunderous, huge, loud, maximum
> intensity, enormous). The book supplies COLOUR only: the family word, two
> or three instruments that name it, the lead voice on top, key, mode, three
> more moods, its own arc after the trailer's, the imagery, the hit.

**MEASURED 2026-09-06 (row 60), 4-bar phrase means, four seeds each:** the
head "Cinematic hybrid orchestral trailer music … coloured by a Victorian
detective mystery, folk violin and a ticking pocket watch" came back FLAT —
quiet-to-loud spread 3.6, 1.5, 13.4, 13.8 dB — tracked at 80, 63, 190, 77 BPM
against 100 asked, and the user heard it: "not dramatic enough for trailer".
The head "Epic trailer music, massive hybrid orchestral, thunderous taiko …
huge, loud, dramatic" with "a whisper that becomes a war" came back with BOTH
registers — spread 13.2, 17.9, 7.9, 6.9 dB — at 86, 100, 96, 97 BPM. Same
model, same cfg, same tempo asked. The model routes on intensity words as it
routes on ensemble nouns, and a caption with neither extreme in it gets the
middle. So the section levels in `cue_ask.LEVEL_TEXT` are "a whisper, quiet
and close" / "huge and loud, the whole orchestra" / "at maximum intensity, the
loudest bars of the piece" — never "at speaking level".

> **EDIT:** the model gives MATERIAL, never ORDER. The ask's staircase is CUT
> from one render on its measured bar lines (`studio/cue_arc.py`): phrases
> sorted by measured level, quiet first, up to the stop bar; the holes gated
> on their bars; a hard out on the stop bar; the render's biggest impact
> landed on the title bar to decay alone; then `studio/cue_punct.py` lays a
> synthesised sub impact on the hit, every hole's return and the title, and
> a noise riser into every hole. The ask is delivered by construction — see
> §16.

**MEASURED across runs 9–12:** sixteen cues, four batches, four ladder rungs,
and every one opened on the book's `genre` — "Period orchestral chamber score
with folk violin, a small acoustic ensemble of 1881 London" — with "one ribbon
microphone … an 1890s parlour session" for Sonics. The ladder changed form and
seed and never the sound, and the user rejected the sound twice ("random
music", "shit music"). The model routes on the first sentence and on Sonics;
whatever ensemble stands there is the ensemble that plays. §1's old table row
told the author to write "a small acoustic ensemble of 1881 London" in place
of the trailer orchestra — that row asked for the parlour piece by name.


> **HARMONY:** a trailer cue is a *harmonic-rhythmic ratchet* — one tonal
> centre, one pulse, and a sequence of one-way moves (a new colour, a doubled
> subdivision, a lifted chord, a widened register) that are each audibly
> irreversible. Mood is **which mode the centre is heard in**; excitement is
> **how many clicks per minute**, and never clicking backwards before the hit.

> **FORM:** a trailer cue is a *staircase with holes* — three plateaus, each
> louder, denser and higher than the last; a hole before every step; the
> deepest hole and the tallest step about five seconds before the end.

A song is a plateau reached early and held. **MEASURED on the cue that
shipped in run 10** (`cue-3002.flac`): −15 LUFS at 8.3 s and held to 97 s,
loudness peak at 52 %, all four structural impacts inside the first third, no
pre-title stop, no title hit, and a five-second fade for an ending. Every
existing fitness term passed it. That is the whole diagnosis of "sounds like a
song, not a trailer".

---

## 1. The affirmative rule — non-negotiable, and mechanical

**Every string that reaches an image, video or music model names what IS
present.** Never "no X", "without X", "not Y", "avoid", "rather than",
"instead of", "-drums", "free of", "nothing".

Why it is a derived rule and not a style preference: a text encoder embeds
tokens, and a negated noun is still that noun in the prompt. Three MEASURED
cases in this repo — "no vocals, no backing vocals" produced humming; "no
signage, no lettering" produced the word CRISTERION painted on a shop board;
"no people, no figures" produced a bar full of drinkers.

**FILL THE SLOT.** Name what occupies the place the unwanted thing would take:

| you mean | write |
|---|---|
| no drums / no kit | "the complete percussion section is a ticking pocket watch, pizzicato cello and double bass, a field snare on two and four" — a closed roster |
| no reverb / dry | "close in one small dry room with a short tail; every note stops the instant the bow lifts" |
| instrumental | "This piece is instrumental throughout. The lead melodic role belongs to a solo violin." — then say nothing more about voices |
| the period colour on top, the trailer orchestra beneath | `genre`: "a Victorian detective mystery, folk violin and a ticking pocket watch"; `mix_space`: "the pocket watch, violin and piano sit close and dry at the front of the wide mix" — the orchestra and the wide mix are `TRAILER_GENRE` / `TRAILER_MIX` and are never written in the tone |
| sparse | "one line at a time; long rests between phrases" |
| no tempo change | "the tempo holds from the first bar to the last; the felt speed doubles by subdivision over the same beat" |

Gate:

```
uv run python -m studio.affirm --scan studio scripts library/<book>/trailer/music/tone.json
uv run pytest tests/test_affirm.py -q
```

Silence from the scan is a pass. `Tone.__post_init__` refuses a negation in
any field and names the field, so an unaffirmative tone cannot even load.
Words that merely *spell* a negation (nocturne, unaccompanied, shadowless,
non-diegetic, no-one) and words that name an *event* (silence, rest, stop,
alone, empty, single) pass — a player can read them as an instruction.

---

## 2. The two inputs, and what each one controls

The node builds one prompt from both and guides them together:

```
<|im_start|><|caption_start|>{clean_caption(caption)}<|caption_end|>
<|lyrics_start|>[start]\n{normalize_lyrics(lyrics)}<|lyrics_end|><|im_end|><|audio_start|>
```

MEASURED from `comfy/ldm/minimax_music/prompt.py`. The unconditioned CFG
branch replaces *everything* between `<|im_start|>` and `<|audio_start|>`, so
**caption and lyrics are one conditioning block** — there is no separate
weight for one against the other, and the cue's stamp covers both.

| | CAPTION | LYRICS |
|---|---|---|
| genre, era, ensemble, production | **yes**, primary | no |
| lead instrument, instrument lifecycle | **yes** | no |
| section-by-section arrangement prose | **yes** — "Describe the song as a section-by-section timeline" (DOCUMENTED, vendor caption skill) | no |
| tempo, key | requested here, **soft** — "generative control rather than strict symbolic guarantees" (DOCUMENTED) | no |
| song structure | prose only | **yes, and the only executable form**: "Tags are the only executable structural instructions" (DOCUMENTED, ComfyUI template) |
| words that are sung | no | **yes — every non-tag line is sung** (MEASURED, §3) |
| length | indirectly | indirectly; the hard stop is `max_duration` |

Node facts, MEASURED from `nodes_minimax_music.py`:

- `max_duration` is a **CAP**, not a target and not a seed: "Maximum duration
  in seconds; the model can end the song earlier". Seven cues under a 150 s
  cap ended by themselves at 101.9–146.8 s. `PINNED_DURATION = 108`
  (`studio/trailer_music.py`) — 38 bars plus a tail is 101–104 s at 92–120
  BPM. Pin it once; iterate on **seed** alone (waveform correlation between
  30/60/150 s renders was −0.03).
- `cfg_scale` 1.7, `top_k` 50, 30 Euler steps — the official values, already
  pinned in the workflow. Leave them.
- Whole prompt cap is **5000 tokens** for caption + lyrics together. The
  "2000 characters" figure people quote is the HOSTED API's and does not
  apply to this path (`music_tone.HOSTED_CHARS` records it).
- `normalize_lyrics` lowercases `[Tags]`, puts each on its own line, and
  **keeps every other character**. There is no tag whitelist anywhere in the
  ComfyUI code.
- `clean_caption` strips `### ` headings, bullets and bold. Keep the three
  headings — the model reads their text as plain lines and the vendor's own
  skill emits them — just never rely on them as structure.
- There is **no `is_instrumental` flag** on the local node. It exists only on
  the hosted API.

---

## 3. THE FINDING: the model sings the lyrics field

Three delivered cues, three different captions, separated with
`demucs htdemucs` and transcribed with `whisper small`. In each one the
**vocal stem is the loudest single element, 3–4 LU above the rest of the mix**,
and it is singing the studio's own arrangement notes, in order:

> "…low note, under audible room tone, nothing else present. The lead states
> its figure plainly and alone, Unhurried, no compeniment. A local centre's
> beneath it, And will not let the figure go… A heart full stop, two full bars
> of total silence. One low impact, then a decay of eight seconds or more.
> With nothing new entering" — whisper on the vocal stem of `cue-1001`

The "bland lyrics" the owner heard were `lyrics_plan()`'s stage directions
being sung. The caption said "This piece is instrumental" in all three and was
outvoted by 121 words of singable prose in the lyrics field.

Why: in every official lyric sheet a parenthetical is a **sung backing line** —
`(take your time, take your time)`, `(typ-typ-typical)`. The only documented
parenthetical meaning "play, do not sing" is the single word `(instrumental)`.

**So: the lyric sheet carries tags and words meant to be sung, and NOTHING
else. All section prose lives in the caption's Arrangement timeline** — which
is what the vendor's caption skill says to do anyway: "preserves musical
instructions attached to lyric section tags in the arrangement description
while keeping the lyric text in the lyrics input."

`tests/test_music_tone.py::test_no_stage_direction_survives_in_any_mode`
asserts the only parenthetical in any sheet is `(instrumental)`.

---

## 4. The sheet: nine tags, this order

```
[Intro] [Verse] [Pre-Chorus] [Chorus] [Bridge] [Pre-Chorus] [Chorus] [Post-Chorus] [Outro]
```

Only the nine tags the open-weights README names are used (`Intro Verse
Pre-Chorus Chorus Post-Chorus Bridge Instrumental Solo Outro`). `[Build]`,
`[Final Build]` and `[Hit]` are not among them and reached the model as
unknown tokens; the length control went with them (one "nine section" sheet
delivered 78.5, 101.75, 114.0, 114.55 and 139.75 s).

Why this order (`music_tone.SHEET_TAGS`):

- **`[Chorus]` twice.** The model was trained on songs: with one `[Chorus]` at
  44 % it made that the peak and treated `[Post-Chorus]` at 78 % as an
  afterthought (MEASURED: loudest tenth 40–50 %, 60–80 % six dB quieter). The
  second `[Chorus]` is **the drop**.
- **`[Pre-Chorus]` twice.** It is the only tag whose learned meaning is "rise
  into the next section", and this form has two rises.
- **`[Bridge]` is the half-time pull-back** and the dialogue slot.
- **`[Post-Chorus]` is the final wave** — the densest bars.
- **`[Outro]` is stop → silence → title hit → tail.**
- **`[Solo]` and `[Instrumental]` are dropped.** Their learned meanings are
  thin texture and moderate level, and act three must be neither: the shipped
  cue's HF/mid ratio dipped 19 dB in its `[Solo]` tenth, exactly where the cut
  wants its densest bars.

### The bar map (38 bars + ~5 s tail)

| block | tag | bars | what happens |
|---|---|---|---|
| Intro | `[Intro]` | 4 | signature sound on the first downbeat, motif once over a held low note |
| Act 1 | `[Verse]` | 8 | ostinato from bar 5, a new layer every 4 bars; **bars 11–12 are a hole** (the hook line lives here) |
| Hit A + rise | `[Pre-Chorus]` | 4 | riser over the last two bars, subdivision doubles to eighths, lead up an octave |
| Wave 1 | `[Chorus]` | 4 | first full statement, hard impact on the downbeat |
| Pull-back | `[Bridge]` | 4 | floor drops to one instrument for 2 bars (**slot 2**), then half-time |
| Rebuild | `[Pre-Chorus]` | 4 | sixteenths, register climbs each bar, long riser |
| THE DROP | `[Chorus]` | 8 | everything at once; low accents on downbeats of 29/31/33/35, each anticipated by a short accent on the previous last eighth; call-and-response every 2 bars |
| Final wave + stop | `[Post-Chorus]` | 2 | densest bars, then a hard full stop |
| Title | `[Outro]` | 1 + tail | two bars of total silence, one low impact (the loudest event), ~5–8 s decay |

Timings at 100 BPM (bar 2.400 s): Intro 0–9.6 · Verse 9.6–28.8 · Pre-Chorus
28.8–38.4 · Chorus 38.4–48.0 · Bridge 48.0–57.6 · Pre-Chorus 57.6–67.2 ·
Chorus 67.2–91.2 · stop 91.2–96.0 · title hit at 96.0 s · runtime 101 s.
**That is the CAPTION's map, and the caption gives no order (§16): the
delivered title is the ARC's, and it is not at 95 %.**

`cue_ask.ask_for` sets
`title_bar = bars − max(2, ceil(register.tail_seconds / bar))` on the TONE's
bar, so the fraction is a bar COUNT over `bars` — quantised to 1/bars, moving
a whole bar at a time as the tempo moves. Detective's 8.0 s tail over
Scarlet's 2.4 s bar is 4 bars: 36 of 40 = **90.0 %**, the bottom of the nine
registers' range (90.0–95.0 % at 40 bars, in 2.5 % steps). MEASURED on run
19's three arced cues, `title_hit / seconds` out of `metre-100{1,2,4}.json`:
80.600/89.523, 105.050/116.709, 65.450/72.720 — 0.9003 / 0.9001 / 0.9000.
The 93–96 % window this file used to claim is a fraction the code cannot
produce at 40 bars.

**And the tail's SECONDS are not the register's.** `fitted` re-lets the ask's
bar COUNTS on the render's measured bar (`update={"bar": metre.bar}`), so one
8.0 s asked tail was delivered as 8.92 / 11.66 / 7.27 s, and `HOLE_BARS` 2 as
4.45 / 5.80 / 3.60 s — the `slots` in those same three files. §16's Open hears
the long hole and does not name why it varies; this is why.

**RULE: a duration that must be HEARD — a tail, a hole, a line slot — is
fixed in SECONDS and re-derived in bars from the RENDER's bar after `fitted`.
Only a duration that must be COUNTED — phrases, sections, the form — survives
`fitted` as a bar count.** PROPOSED: `tail_s` and `hole_s` delivered beside
asked in `metre-<seed>.json`; they cost nothing, and they are the fourth
instance of §16's "an agent's output is its next input".

### Loudness staircase, momentary LUFS relative to the cue median M — the DELIVERED unit (§18); the step's own levels are dBFS and disagree by up to 5 dB

Intro ≤ M−10 · Act 1 ≈ M−4 · Wave 1 ≈ M+1 · pull-back hole ≤ M−12 ·
drop ≈ M+3 · final wave ≈ M+4 (the loudest 5 s of the cue) · stop ≤ M−20 ·
title hit = the peak.

---

## 5. Twelve excitement mechanics — the sentences that ask for them

All twelve are in `music_tone.STAIRCASE`, one clause each. The shipped cue
followed **one** of them (rising register), because nothing in the old caption
asked for anything propulsive — it asked for a chamber piece to get louder.

| # | mechanic | the sentence |
|---|---|---|
| 1 | ostinato | "one low figure repeating to the last bar" |
| 2 | layered entries | "a new colour every four bars, every layer staying" |
| 3 | subdivision doubling | "quarter notes, doubles to eighths at the first rise, doubles to sixteenths for the final third, over the same beat" — **the second doubling cannot be measured here**: at 100 BPM sixteenths are 0.15 s apart, under `ACCENT_GAP` 0.25 s, so a cue that reached them and one that stopped at eighths read the same (§17). Ask for it; never claim it landed |
| 4 | the hole | "its last two bars silent" |
| 5 | riser + hit | "a rising sweep into the downbeat" / "one hard impact there" |
| 6 | half-time drop | "one dry instrument two bars, then half-time, a heavy accent every two beats" |
| 7 | rising register | "each bar higher, a longer sweep" |
| 8 | syncopated braams | "a low accent on every second downbeat after a short accent on the eighth before it" |
| 9 | call-and-response | "the lead calling a bar and the low ensemble answering" |
| 10 | density staircase | "the densest bars of the piece" |
| 11 | pre-title stop | "two full bars of total silence" |
| 12 | title hit + tail | "the loudest event of the piece, one low note decaying alone for eight seconds" |

---

## 6. Mood → mode → key → tempo → palette

Pick the row from the trailer's dramatic structure (`01-story`'s `register`),
never from the visual palette — that is the refs' job.

| mood family | mode | centres, and why | chord devices | tempo / feel | palette (period notes) |
|---|---|---|---|---|---|
| **dread / menace** | Phrygian (♭2), harmonic minor at the cadence | E or A (open strings give the ♭2 rub); C/D for low brass | i – ♭II – i; drone with ♭2 above; tritone bass | 60–80 half-time with an eighth-note tick | low strings sul ponticello, contrabassoon, bass clarinet, low brass pedal, church organ |
| **mystery / curiosity** | Aeolian, Dorian tint; octatonic for "clues" | **G or D minor** (violin open string as tonic or fifth) | lament bass i – i/♭7 – ♭VI – V; a question motif ending on the 2nd; chromatic mediant sidestep | 84–108, ticking eighths | pizzicato cello, walking bass, cimbalom/zither/banjo, detuned upright piano, clock ticks |
| **grief / loss** | Aeolian, Dorian; major with minor plagal (iv → I) | D or A minor (open-string cello); E♭/A♭ major transfigured | descending lament tetrachord; iv → I; Picardy third on the last chord only | 56–72 straight, or 3/4 at 80–96 | solo cello, viola, cor anglais, harmonium, parlour piano, solo fiddle over an open fifth |
| **heroism / triumph** | Ionian with ♭VII and ♭VI; Dorian for folk heroism | D, E♭, B♭, C major (horn keys; D rings on every open string) | I – ♭VII half cadence; I – ♭VI – ♭VII – I; major-third mediant | 100–132 dotted march, or 6/8 at 120 | horns in unison, trumpets, snare + bass drum, full strings in octaves, choir |
| **wonder / awe** | **Lydian** (♯4) | C, F, B♭; high register — the mode needs air above it | I – II; a cadence landing a third from where it was going; planing triads | 66–92, triplet or 6/8 | high strings divisi, harp, celesta, glockenspiel, flute, choir on "ah" |
| **romance / longing** | major with iv and ♭VI borrowed; Aeolian with a major IV | E♭, A♭, D♭ major; A minor for unrequited | appoggiaturas on strong beats; iv → I; V → ♭VI | 60–84, 3/4 waltz | solo violin or clarinet with fortepiano, string quartet, harp |
| **action / chase** | Aeolian/Dorian; harmonic minor at the cadence | **D minor** (every open string in the chord), E minor, C minor | ostinato on i – ♭VI – ♭III – ♭VII; pedal with an ascending bass; **double the subdivision, never the tempo** | 130–160 straight sixteenths, or 65–80 half-time with a sixteenth ostinato | low string ostinato, staccato brass, taiko or field drums, snare rolls, risers |
| **horror / uncanny** | Locrian, whole-tone, octatonic, clusters | any — the point is the absent centre; B or F if one is needed | tone clusters; tritone; Dies Irae; hexatonic pole | pulseless, or a tick faster than a heartbeat | sul ponticello, col legno, over-pressure bowing, waterphone, prepared piano, tubular bells |
| **melancholy period drama** | Aeolian/Dorian with relative-major relief | G minor / B♭ major, E minor / G major | i – ♭VII – ♭VI – ♭VII; i – iv – i – V | 60–76 in 3/4, or 4/4 at 72 | parlour piano, string quartet, harmonium, clarinet, music box, hurdy-gurdy |
| **revenge / obsession** | **harmonic minor** with a Neapolitan ♭II | G, D or A minor — the same centre as the mystery, heard inside out | i – ♭II – V – i; one-note ostinato; the motif at double speed an octave down; hit on a bare open fifth | 92–112 straight, eighths → sixteenths; the pulse never stops before the hit | solo violin at double speed, piano bass octaves, snare, bass drum, one tubular bell; Western: harmonica, jaw harp, whistling |

**Register rule:** menace is low and close; wonder is high and wide; grief is
middle and alone; heroism is unison across three octaves. When a mood reads
wrong, the register is usually wrong before the key is.

**Say harmony in sound words, never in theory jargon** — the model was trained
on captions, not scores:

| theory | write |
|---|---|
| Neapolitan ♭II → i | "the harmony strikes a major chord one semitone above the tonic and falls back" |
| Picardy third | "the last chord turns major" |
| chromatic mediant | "the harmony brightens to a major chord a third above" |
| open fifth | "a bare open fifth, the chord with its third removed" |
| lament bass | "the bass sinks one step at a time under a held melody" |
| Dorian | "minor with a bright major chord on the fourth degree" |
| Mixolydian ♭VII | "major with the seventh flattened, stepping down like a Western" |
| harmonic minor | "the leading tone sharpened, the chord before the tonic a hard major" |

### One genre recipe per book family

Each names a **lead**, a **bed**, a **pulse**, a **colour per restatement**, and
**one signature sound** — the instrument that names the book in two bars.

| family | signature sound |
|---|---|
| Victorian detective / procedural | a detuned pub piano playing the four-note figure |
| gothic horror | a church organ's lowest pedal note with a solo violin a minor second above |
| adventure | a fiddle jig in Dorian over a bodhrán |
| sea | a male unison shanty phrase answered by a low brass braam |
| science romance | a celesta figure in Lydian over a rising whole-tone bass |
| romance | a fortepiano and violin duet in a waltz |
| social realism | a hurdy-gurdy drone under a music-box tune |
| war / epic | a field snare roll into a horn unison in D |
| fairy tale | a music box whose tune goes minor |

Two rules across all of them: (1) the found percussion must be something the
book contains (clock, hoof, capstan, hammer, bell) so the pulse is diegetic;
(2) **beside the period colour, name one instrument the model has a strong
prior for** (pizzicato strings, snare, bass drum, piano, organ, choir) —
because the period colour is what it is likeliest to miss. The shipped Scarlet
cue lost its solo violin entirely (2–8 kHz sat 21 dB below the mids), and its
pocket-watch-only pulse gave neither the model nor the beat tracker a metre to
hold: 84 asked, 89–189 delivered across eight seeds. `Tone` now refuses a
`pulse_carriers` list with no strong-prior carrier in it.

---

## 7. Tempo: hold one, double the subdivision

- **Never ask for a tempo change.** The cut walks a *bar* grid;
  `beat_period` picks one period for the whole cue by autocorrelation, so a
  two-tempo cue gives it two peaks and one act gets cut on the wrong octave.
- Half-time and double-time are **subdivision** events over a constant beat:
  half-time = an accent every two beats (the bridge); double-time = sixteenths
  in the ostinato (the final third). Same bar, twice the felt speed, and more
  L2 cut points exactly where the 80–92 % band wants them.
- State the tempo **once**, as a range or qualitatively: "tempo is around 100
  BPM, held from the first bar to the last". DOCUMENTED: "Use an exact BPM
  only when explicit or strongly justified". MEASURED: one caption saying
  `bpm is 84` three times delivered 89–189 across eight seeds. Repetition is
  more tokens, not more control. `caption()` asserts one `BPM` and one
  `key is` in the whole text.

**Scarlet is 100 BPM.** The theory brief argued 104 (inside MiniMax's 80–110
"groove" band, 2.31 s bar); the structure brief argued 92–100 (at 84 the
half-beat 0.357 s is under `MIN_SHOT`, so the climax floor is a whole beat;
120 makes a Victorian chamber tone read as a chase). 100 is in both: the bar
is 2.400 s, the beat 0.600 s, the half-beat 0.300 s, sixteenths supply the L2
density in the 85–90 % band, and one bar holds a 5–6-syllable line in a
one-bar slot. It is also the roundest number in the overlap, which matters
because the number is a prior, not a clock.

---

## 8. The lyric path — BLOCKED, and REFERENCE until it is not

**This path cannot run.** Eligibility test 3 below needs `demucs`, which is in
neither `pyproject.toml` nor `uv.lock` (see Dependencies) and which no code
path in `studio/` or `scripts/trailer/` calls. So no book can legally leave
`lyrics_mode: instrumental` — Scarlet's `tone.json` says `instrumental` — and
§§8–9 are REFERENCE, not steps: read them when the pin lands, spend no rung on
them now. **RULE: a step this file names must be runnable from the pinned
dependencies, or its heading says BLOCKED.** The same mark stands over
`cue_listen` (§17): written, tested, imported by nothing, `transformers`
unpinned. No §14 checkbox reaches §§8–9, which is how ninety lines came to
govern nothing.

Instrumental is the trade default anyway. Bergersen, on why his choirs sing
syllables and never sentences (DOCUMENTED, Gear Patrol): *"the moment people
pick up on actual lyrics of meaning, their focus has shifted away from the
musical body."*

A voice is allowed in proportion to how little it asks the audience to parse.
`Tone.lyrics_mode` is one of four:

| mode | what the voice does | parse cost | where it may sit |
|---|---|---|---|
| `instrumental` | nothing; the lead instrument is the voice | 0 | every section |
| `vocalise` | one vowel held, or Latin / invented syllables chanted | ~0 | Chorus, Bridge, Post-Chorus |
| `refrain` | one English line ≤ 7 syllables, the book's thesis, sung 3× | medium | both Choruses + Post-Chorus |
| `whisper` | one line, unpitched, close-miked, over a slot | high | Bridge, one bar |

Eligibility, all three required before anything but `instrumental`:

1. `01-story` emitted a **thesis line** — present tense, ≤ 7 syllables, names
   nobody, not an event. (`refrain` mode refuses to construct without one.)
2. `01-story`'s `register` is elegy / gothic / romance / coming-of-age /
   tragedy. Procedural, detective and comedy sell the *how* through spoken
   lines and a sung word competes with "You have been in Afghanistan".
3. The delivered cue's vocal stem (`demucs==4.1.0`) leaves ≥ 2 gaps that are
   slots. A spoken line never sits under a sung word.

`[Intro]`, `[Verse]` and the pull-back stay voiceless in **every** mode —
that is where `05-dialogue` puts its windows.

### Syllables per bar, by tempo (4/4)

| BPM | beat | bar | sung line, 1 syl/beat | chant, 2 syl/beat | vocalise | whisper |
|---|---|---|---|---|---|---|
| 84 | 0.714 | 2.857 | 4 (6 max) | 8 | 1–2 per bar | ≤ 8 per bar |
| 92 | 0.652 | 2.609 | 4 (6) | 8 | 1–2 | ≤ 7 |
| 100 | 0.600 | 2.400 | 4 (5) | 8 | 1 | ≤ 7 |
| 120 | 0.500 | 2.000 | 4 | 6–8, CV syllables only | 1 | ≤ 6 |

- A sung syllable with a consonant onset needs ≥ 0.33 s → one per beat at
  every tempo here; two per beat only at ≤ 92 BPM and only on open syllables.
- A consonant cluster (str-, spl-, sangu-) costs ~0.1 s → clusters sit on a
  full beat, never on an eighth.
- A held vocalise vowel: 1–2 bars. Longer and the model breathes where you
  did not plan it.
- Sustained vowels by voice: soprano **ah / oh** (ee is squeezed up top, oo is
  hooty); mezzo ah, eh, oh, ay; low male chant **oo, oh, mm**; a whisper is
  carried by consonants (s, sh, th, k, t, ch).

### Placement

- Keyword (noun or verb) on beat 1 or 3; function words (the, of, and, in)
  never on 1 or 3. CITED: 80.8 % of keywords in a corpus land on strong beats,
  and *word type* predicts the beat better than syllable stress (0.765 vs
  0.495) — so the rule is "noun/verb on 1 or 3", not "stressed on 1 or 3".
- Pickup ≤ 2 unstressed syllables on beat 4 before a downbeat keyword.
- The refrain's first stressed syllable is on beat 1 of the Chorus's first bar.
- The last stressed syllable of `[Post-Chorus]` sits on beat 1 of that
  section's last bar, on an open vowel, sustained and **cut by the stop**.
- Never put words in the silence bars or on the title impact. That room
  belongs to the picture.

---

## 9. Lyrics that are not bland — the checklist

The old sheet's content words were *adjectives and adverbs* — sustained,
plainly, unhurried, shifting, bare, exposed. Adjectives have no beat and no
picture. The book has both: a word in blood on plaster, a wedding ring on a
floor, a pill box, a hansom in fog, an alkali plain.

1. Every content word is a **noun or a verb from the book's analysis**.
2. **One verb per line.** Two verbs is a sentence; one verb is a blow.
3. The refrain is a **question or a threat** — an imperative, or a line with
   *who / whose / will / keeps*. A statement describes; a threat addresses.
4. Second person, or no person. Never a name in the sung line.
5. **No rhyme** in a trailer refrain; assonance only (*scarlet / thread*).
6. The title word or its partner lands on the last downbeat before the stop.
7. Vowels chosen by voice (§8); clusters only on beats.
8. ≤ 7 syllables and ≤ 8 words in the refrain; ≤ 7 per chant line.
9. Refrain repeated ≥ 2 times across Chorus + Post-Chorus.
10. Latin or invented words map to a book noun through `tone.vocalise`, and
    each gloss is in the book's own vocabulary.
11. Sung fill 1.0–1.6 syllables per second (PROPOSED — the 2.4 figure was
    measured on prose *notes* and must be re-measured on a sung sheet).
12. `[Intro]`, `[Verse]` and the pull-back bodies stay `(instrumental)`.
13. Every line passes `negations()`.
14. Hyphenate to control pronunciation: `Ra-che`, `Lu-ci-a`.
15. Case is preserved by the encoder — submit normal case.
16. If the sheet delivers under 90 s, add tags. Never pad the bodies.

One book's lexicon belongs in that book's `tone.vocalise`, not in a skill that
runs on every book; the Scarlet Latin list that stood here has been deleted for
that reason, not because it was wrong.

---

## 10. The Tone contract (`studio/music_tone.py`)

One file per book at `library/<book>/trailer/music/tone.json`. Absent is an
error, never a default. A v1 file (key / scale / percussion / sonics /
progression / instruments) is refused by name.

| field | rule |
|---|---|
| `genre` | the BOOK'S COLOUR, ≤ 12 words: the family word (`cue_ask.KEYWORDS` routes on it) + the two or three instruments that name the book. The trailer's genre is `TRAILER_GENRE`, prepended by `head()`; a `genre` that names an ensemble ("a small acoustic ensemble of 1881 London") asks for that ensemble's music, and sixteen cues did |
| `tonal_centre` | one of the twelve; one centre for the whole cue; prefer one whose tonic or fifth is an open string of the lead |
| `mode` | one of ten (§6). `key` and `scale` are derived from these two |
| `mood` | exactly three adjectives |
| `bpm` | one integer, held; inside the band its mood family names |
| `time_signature` | "4/4" unless the book earns otherwise |
| `tempo_plan` | the subdivision ladder, over one beat |
| `chord_plan` | the ratchet, in sound words |
| `pulse_carriers` | ≥ 2, in order of entry, ≥ 1 with a strong rhythmic prior. `percussion_palette` is read off this, so the two cannot drift |
| `signature_sound` | the instrument that names the book in two bars |
| `lead_instrument` | instrument + technique + placement |
| `supporting_instruments` | the bed and the colour per restatement |
| `register_arc` | the top and bottom of the climax against the first statement |
| `dynamics_arc` | the emotional arc as prose |
| `mix_space` | where the colour instruments sit IN the trailer mix (front, close, dry). The mix itself — width, sub, brass, risers, mastering — is `TRAILER_MIX` |
| `era_reference` | "in the manner of a modern <family> trailer cue"; never a living artist or a brand |
| `imagery` | what the cue is scoring |
| `hit` | the final impact: a bare fifth or a unison, low |
| `lyrics_mode` | one of four (§8) |
| `refrain` | required exactly when `lyrics_mode == "refrain"` |
| `vocalise` | the sung syllables, when there are any |

Every string field is checked by `negations()` at construction.

---

## 11. Seed selection — FORM first, then the grid

```
best_of(metres, asked, form, score, fit) ranks on:
  1. ask delivered       0-1   cue_ask.plan_score
  2. form score          0-2   the two terms below
  3. grid == "metre"
  4. ride fit            by FIT_BAND 2.0 dB
  5. tempo band          by TEMPO_BAND 0.15
  6. trailer_fitness     the arc's own gate depth (§17), not the music
```

Keys 1–5 are all written by the arc. On run 19 one of keys 1, 2 or 4 chose an
82.25 BPM cue over a 107.22 one for a 100 BPM ask, and which one is unknowable
because `grade` writes none of them to disk. **Read §17 before adding a
seventh — the sixth is the arc's gate depth, and the three that decide
(delivered, form, fit) are written to no file.**

Form outranks grid steadiness on purpose: run 10's chosen seed had the
steadiest grid of its family and was a plateau from 8 s that ended in a fade.
A staircase on a wobblier grid is the better trailer — `04-shots` can cut to
onsets, and it cannot invent a climax that is missing.

**Term 1 — staircase** (`step_03_music.climbs`): the median of tenths 8–9 is
≥ the median of tenths 2–3 **+ 4 dB**, AND the loudest 5-second window starts
in **75–92 %** of the runtime. cue-3002: +1.6 dB, loudest 5 s at 52 % — this
is the one term that would have failed it while every other term passed.

**Term 2 — stop, not fade** (`step_03_music.stops_dead`): **zero onsets after
`title_hit + one bar`**, and a title hit exists at all. cue-3002 fell
monotonically over five seconds from 97.1 s; a fade under the title card reads
as a song ending.

Then the pre-existing terms, unchanged: `metric_term` (bars_in_mode),
`tempo_term`, `title_term` (the pre-title trough holds threat + 2 beats),
`lift_term` (≥ 6 dB over the two bars before the hit), `slot_term`, and the
`crowding` × `reach` pair inside `trailer_fitness` (`late_reach` is not a
function; the term is `beatmap.late_density` in 80–95 %, capped at 4). A
**slot** is a trough ≥ 6 dB under the median, held ≥ 1 bar, starting in
20–80 %; on every arced seed they are the arc's own holes, so `slot_term` is
a constant (§17), and no line step reads them while a plan exists (§19).
**A seventh key is owed to §19: the line windows the seed's plan affords,
because `order_lines` places one line per window and the delivered master is
graded on `speech_occupancy`.**

Render 4 seeds a batch; the ladder is `first_seeds → four_more_seeds →
reauthor_caption ×2 → best_seed`. `reauthor` may change **only**
`pulse_carriers` and `supporting_instruments`, its answer is validated as a
`Tone` (so a negation or a weak pulse is refused and asked again), and after
two refusals the authored tone stands.

Never write a reauthor brief like run 10's — "instruments STRUCK on every beat
… hold {bpm} BPM from first bar to last". A metronome satisfies every word of
that sentence, and a click track is what came back.

---

## 12. What was actually sent, recorded beside what came back

`stamp_cue` writes two files next to every cue:

- `cue-{seed}.caption.txt` — the digest, which keys the render cache
- `cue-{seed}.caption.json` — `{"stamp", "caption", "lyrics"}`, the full text

`caption_stamp(caption, lyrics)` covers **both** inputs, because the node
guides them as one block. Before this, cue-3002's stamp matched no committed
caption × any committed tone.json, and the text that made the shipped cue was
unrecoverable.

---

## 13. Measuring the cue, and cutting to it

`beatmap.metre(audio) -> Metre(beats, downbeats, bpm, bar, bars_in_mode, …)`
from **Beat This!** (`beat-this==1.1.0`, MIT, 6–11 s per cue on CPU, 20 ms
grid). `phrases(metre)` groups downbeats in fours.

- Tempo is `60·(n−1)/(t_last − t_first)` over tracked beats. **Never** the
  median of 60/IBI on the 20 ms grid — that is 3000/n and carries octave
  doubles (a first draft's 187.5 was 93.7 twice).
- The cut uses the **bar** (median downbeat interval), which is octave
  invariant. Report bpm; walk in bars.
- `onsets()` stays as the rubato fallback (`bars_in_mode < 0.65`). The
  manifest records which grid cut the trailer.
- Do NOT add `allin1` (NATTEN API removed), `madmom` (CC BY-NC-SA weights) or
  `natten`. `librosa` is for features only — it agreed with Beat This on 37 %
  of beats on the drumless cue.
- Timbral self-similarity does not recover authored sections (MEASURED,
  negative). Sections are envelope events snapped to downbeats.

### Where the cut plan comes from now (the beat walk went in BUILD row 55)

Step 03 writes `music/plan.json` (`studio.cue_plan.CuePlan`) whose measured
`spans` ARE the shot list; step 06 lays one shot per span, and
`plan_cuts`/`ACT_BARS`/`FIGURE`/`BEAT_LOCK` no longer exist in `trailer_edit`
(`grep` finds the names only in its own docstring). `MusicBed.sections`
carries the measured `CueSection`s — including each one's `pulse`, which
`cue_spans.sections_of` sets from the cut map's onsets per second against
`PULSE_DENSITY` 0.6 (drones measured under 0.3/s, pulsed sections 1.5–3.5/s
on `cut_map_331107.json`) — and `MusicBed.cuts` the span starts. The walk as
it was is BUILD row 55's, not this file's.

QC reads the DELIVERED file, never the plan: `qc.py` extracts the master's
audio, tracks it, scene-detects the picture (threshold below 0.3 — 9 of 44
low-contrast cuts were missed at 0.3) and reports `cuts_on_beat`,
`cuts_on_downbeat`, `cuts_on_L0`, `title_on_downbeat` (`on_cap_fraction`
graded the walk and left with it, row 55).
`cuts_on_beat` is REPORTED and no longer TARGETED: `QC_TARGETS`' own
docstring calls a whole-trailer ≥ 0.80 "the single target that FORCED a music
video" (76 % of run 10's cuts on the beat, whole-bar lengths, "a viewer starts
counting within four shots"), and it was replaced by `cuts_on_beat_act3` 0.80
alone. The live targets are `cuts_on_downbeat` 0.30, `cuts_on_L0` 1.0,
`cuts_on_events` 0.90 and `title_on_downbeat` true.

---

## 14. Pre-submit checklist

- [ ] `tone.json` exists, loads as `Tone` (a v1 file is refused by name)
- [ ] `uv run python -m studio.affirm --scan studio scripts library/<book>/trailer/music/tone.json` prints nothing
- [ ] the caption names the lead instrument in its first sentence
- [ ] the caption says "instrumental" when `lyrics_mode` is instrumental
- [ ] BPM appears once, as "around N BPM, held from the first bar to the last"; `key is` appears once
- [ ] the Arrangement names all nine sections in sheet order
- [ ] the percussion line starts "the complete percussion section is"
- [ ] the sheet holds the nine tags in `SHEET_TAGS` order and no parenthetical other than `(instrumental)`
- [ ] `PINNED_DURATION` is 108 and unchanged
- [ ] four seeds rendered per batch; `metre-<seed>.json` carries every key
      `best_of` reads — delivered, form, fit, grid, bpm, fitness — for every
      seed, not only the winner (§17)
- [ ] every ranking term names what SETS the number it reads, and at least one
      reads the render and not the arc (§17)
- [ ] every envelope term reads inside the arc's mask, and
      `metre-<seed>.json` carries `material_fraction` (§17)
- [ ] `metre-<seed>.json` carries `residual` and `brightening` (§17) and the
      two LU terms `fit_lu` and `cue_tp` (§18)
- [ ] `metre-<seed>.json` carries `windows`, `window_s` and `speech_afforded`
      (§19) for every seed, and `speech_afforded` is stated against
      `qc.speech_target(hard_out)`
- [ ] `metre-<seed>.json` carries `holes_landed` (§19) and `repeat_max` and
      `supply` (§20), and no shipped cue's `repeat_max` is above 0.9
- [ ] no two landmarks in one cue carry the identical impact or riser (§20)
- [ ] `cue-{seed}.caption.json` exists beside every cue
- [ ] `uv run pytest tests/test_music_tone.py tests/test_step_03_music.py tests/test_affirm.py -q`

---

## 15. Still unmeasured — do these before trusting anything above

1. **BLOCKED — the `(instrumental)` sheet has never been rendered here.** The
   recipe is DOCUMENTED (SGLang reference render, vendor caption skill) and not
   MEASURED on this machine, and the check it needs — render one seed at
   `max_duration` 20, `demucs` the result, require the vocal stem well under
   the mix with an empty whisper transcript — needs `demucs` AND
   `openai-whisper`, and neither is in `pyproject.toml` or `uv.lock`. By §8's
   rule the heading says so. This is the BLOCKED item that governs EVERY run:
   every book ships `lyrics_mode: instrumental` and §3's finding was measured
   with exactly these two tools. Pin them, or find a check that runs on the
   pinned set; do not spend a rung pretending this one ran.
2. **Section length with empty bodies.** "≈ 11.1 s per section" was measured
   while every section carried sung prose — the per-section time was the time
   to *sing* the note. Re-measure, then decide whether nine tags still land
   near 100 s or the sheet needs more.
3. **Whether the model parses "harmonic minor", "Neapolitan" or "sixteenth
   notes" at all.** Hence the sound-word translations in §6.
4. **Whether 100 BPM holds better than 84.** PARTLY MEASURED (§0): the
   asked 100 held at 86–100 on the four epic-head seeds and was ignored
   (63–190) on the four detective-head seeds — the tempo follows the
   DRUMS the caption names, not the number. 84 is still unmeasured.
5. **A hand-tapped 16-bar fixture** for the drumless seed. Until it exists,
   `bars_in_mode` is an opinion about a rubato cue and no seed may be
   *refused* on it — only ranked.
6. **How many onsets per SECOND a trailer cue's last third carries.** Run 19's
   three arced seeds measured 1.15 / 2.02 / 0.99 in their LAST THIRD against a
   detector ceiling of
   4.0/s (§17) and no reference cue has been measured here, so there is no
   floor: the number may RANK seeds and, by item 5's rule, refuse none.
7. **The register arc has never been measured on any cue rendered here.**
   `cue_voicing` moves the whole file's bands toward one shape; whether the
   last third comes out brighter than the first is unknown on every seed in
   `trailer/main/music/` (§17's `brightening`).

---

## 16. The editor's arc — the ask is cut, not hoped for (BUILD row 60)

**MEASURED, five rounds of captions on the epic experiment set:** intensity
adjectives, a "Dynamics" sentence, descriptive section tags, a late
`[Chorus]` — each moved the timbre and never the ORDER. Every seed reached
its plateau by 20–30 % of the runtime and stayed there (climb −0.6 dB over
three seeds; the late-chorus sheet −4.4 and +3.5). The vendor's rule holds:
mood words are weak, tags command structure — and structure is not dynamics.
What the model reliably gives, when the caption asks for both extremes (§0),
is material in both registers in ONE render: intro bars at −27 to −37 dBFS,
loud bars at −10 to −16, same key, tempo and mastering.

So step 03 renders `raw-<seed>` (ask seconds + `TAIL_HEADROOM`) and
`arc_cue` writes `cue-<seed>` from it:

1. `beatmap.metre(raw)` — the render's bar lines. Fewer than one 4-bar phrase
   (rubato) → the raw render ships as the cue, nothing to re-order.
2. `fitted(ask, metre)` — the ask's COUNT of bars on the render's MEASURED
   bar. raw-1001 came back at 2.69 s bars against 2.4 asked; cut on the
   ask's bar the arc ran 101.8 s for a 91.2 s ask with beats laid 2.4 s apart
   on 2.69 s bars (bars_in_mode 0.81). Before that, `cue_arc.at_octave`:
   a tracked bar more than sqrt(2) off the asked bar is the tracker's
   tempo octave (run 13: 214 BPM for 100 asked, 38 one-second bars, a
   43.7 s cue) and its bar lines are merged in pairs or split at their
   midpoints first. Length follows the render's bar inside that band;
   the fit rule (row 56) trims the plan.
3. `cue_arc.arc` — `bar_levels` (median dBFS per bar) → `has_material` (the
   only bar with nothing in it is a black one, < −60 dB; a phrase holding
   one is left out) → `bar_order` (whole 4-bar phrases, quiet to loud; short
   of whole phrases, the loudest one plays TWICE — §20 measures whether it
   did, and on run 19 it did not) → `assemble` (every bar cut to the CUE'S
   bar from its downbeat, whatever length the tracker gave it; 10 ms
   equal-power `step_join` — the level step IS the arc, so
   `cue_edit.conform`'s 3 dB refusal does not apply) →
   `gate_holes` → `stop_at` → `title_piece` on the render's biggest impact.
   Measured on epic_cfg17-7005: climb −0.9 → 11.0 dB, loudest 25 % → 76 %.
4. `cue_punct.punctuate` — sub impact (70→32 Hz sine, click on the front,
   1.6 s) on the hit, every hole's return; a 2.5 s one at full gain on the
   title; a noise riser over the two bars into every hole; bed −3 dB; tanh
   knee at 0.85. Seed 7, so the same ask punctuates the same way every run.
5. `cue-<seed>.grid.json` — the arc's own bar lines AND its events
   (`events_of`: the ask's events in the cut map's kinds, witnessed
   `arc:<kind>`, the stop and holes with their `end`). `measure` reads the
   cue on the lines (`known_grid`), because re-tracking a cue through its
   deliberate holes loses two downbeats per hole; `map_cue` lays the
   events over the detectors' (`music_events.with_known`) and takes the
   stop as the hard out (`known_hard_out`), because a detector only SEES
   what the arc cut — cutmap-1001 had the bar-10 impact as no hit, the
   stop merged under a 'section', the hard out at 62.9 s for a stop at
   76.4: delivered 0.62 for an arc that had delivered everything.

Three "an agent's output is its next input" bugs this surfaced, all fixed:
`Metre.seconds` was the last envelope window, not the decoded length (plan
82.079 ≠ 82.1); a stop's silence made the tracker report a 4 s bar the arc
placed first, shifting every asked bar; the arc'd cue re-tracked lost the
downbeats inside its holes. Each is a test now.

Then three more (ARC_VERSION 4, BUILD row 61): the tracker read raw-1001's
drumless intro at HALF TIME (six bars of 4.44 s on a 2.24 s bar) and
`assemble` sliced on its lines; `regular_bars` threw those quiet phrases
away as "stretched", so every run-13/14 arc opened loud; and the cut map
did not know what the arc had cut. The tracker's bar lines are where a bar
STARTS; how long a bar IS is the cue's, and what the arc did is written
down, not re-detected.

Then the LEVEL (ARC_VERSION 5–7, BUILD row 62). Ordering bars by level
can only build a staircase as tall as the render's range, and the render
comes back mastered flat: run 16's cue-1001 had phrase means −24 −24 −17
−23 −18 −18 −25 −23 −26, 9 dB end to end, where a trailer cue climbs
15–20. A caption cannot ask a mastered model for dynamics it flattens, so
the arc RIDES them: `cue_arc.ride` takes every material bar to the level
the ask wrote (`RIDE_DB`: low −26 held, a step at the hit, mid −18 → −14,
high −14 → −12 finishing on the bar before the stop), within `RIDE_MAX`
12 dB, as one envelope whole at bar centres and sliding between them.
Re-arced, the same render reads −28..−32 / −22..−16 / −17..−15 with the
loudest five seconds at 79 %. Two smaller ones: a long render loses its
MIDDLE, not its climax (`cut_middle`; v5 kept raw-1001's −13/−12 bars),
and the title material holds a beat and rings out within a bar (`ring_out`,
`RING_BARS`) — the decay under the card is the punctuation's own impact,
and `stops_dead` reads rises more than `RING_FLOOR_DB` under the hit as
the hit ringing. `best_of` then ranks seeds by `fit_of` — dB RMS from the
ridden levels — because the range is now the ask's and only the fit is
still the render's. Its first run (17) taught the rule's own corollary
(v8, BUILD row 63): the ride reads the level of what it MOVES, after the
cut, on the body's uniform lines (`body_levels`) — read off the tracker's
wandering lines on the render, a −4 dB gain landed on a bar `assemble`
had cut from elsewhere and left −40 in the opening. And `climbs` measures
the material up to the stop, not the silence the ask put after it. Every
seed of run 16's raws then fits within 1.4 dB with form 2/2.

Then the VOICING (ARC_VERSION 9, BUILD row 64). Level solved and the
word still "not dramatic": so the spectrum. Measured against finished
music's mean spectrum (Elowsson & Friberg 2017) the model voices every
render alike -- sub hot, body scooped, low mids boxy, top 9-15 dB dark.
`cue_voicing.voice` moves each octave band toward the reference shape,
at most 6 dB, before the arc cuts; the ride then reads the voiced bars.
Nothing the arc does to level can fix a spectrum, and nothing the
prompt says fixes the model's vocoder.

**Open:** `HOLE_BARS` 2 delivers 3.60–5.80 s of hole depending on the
render's bar, and §4 now says why; riser and impact gains are typed
constants until a sound check names them; the epic renders (§0) track
cleanly at the asked tempo, which is the other reason the caption carries
the drums; `RIDE_DB` is the first sound check's number, not a measured
one — the next lever after the ride is the material itself (a
percussion-first preamble), since the ride can lift a bar's level but not
put a drum in it.

---

## 17. What a gate is allowed to read

Level is solved — fit 1.3 / 1.1 / 1.4 dB, form 2/2, delivered 1.00 (rows
63–64, measured on run 16's RE-ARCED RAWS) — and the owner's word is still
"not dramatic enough". The defect is in what the terms READ. After
ARC_VERSION 4–9, ALL SIX of `best_of`'s keys are numbers the arc itself wrote —
the sixth was the one this file called "the render" until it was measured:

| key | who sets it | what it read, and WHERE that reading lives |
|---|---|---|
| `delivered` | `cue_arc.events_of` → `music_events.with_known` (*a known event keeps its time and kind*) | 1.00 (row 63, run 16's raws); run 19's WINNER is recoverable from `music/plan.json`'s `asked` — six events, every one `measured` non-null, so 1.00 — and no loser's is anywhere |
| `form` | `ride` + `stop_at` + `ring_out` impose the contour `climbs`/`stops_dead` then read | 2/2 (row 63, run 16's raws); run 19 wrote none to disk |
| `grid`, `bars_in_mode` | `cue_arc.grid_of` lays four beats on every bar line | exactly 160 beats / 40 downbeats and `bars_in_mode` 1.0000 on all three; cue-1003, the rubato copy `arc_cue` passed through untouched, 0.3438 / "onsets" |
| `fit_of` | distance from `ride_targets` — the curve `cue_arc.ride` drove those bars to | 1.3 / 1.1 / 1.4 inside `FIT_BAND` 2.0 (row 63, run 16's raws); run 19 wrote none to disk |
| tempo | also `grid_of`: the reported bpm is **240 / the arc's own bar** | 2.24 s → 107.22, 2.92 → 82.25, 1.82 → 132.00, exact to two decimals |
| `m.fitness` | **the arc too** — `dynamic_range` is P95 − P5 over the WHOLE envelope, and a fifth of an arced cue is the gate the step wrote | 78.603 / 82.436 / 22.512 — and 78.6 / 82.4 ARE those two cues' P95 − P5 to the decimal (below) |

The last three rows are read out of run 19's own files
(`music/metre-100{1,2,4}.json`, `cue-*.grid.json`). The first three are in no
PER-SEED file run 19 wrote; only the winner's verified ask survives, inside
`music/plan.json`, and it says the shipped cue delivered **1.00** of its ask.

**And the sixth key is the arc's gate depth.** `trailer_fitness` opens on
`beatmap.dynamic_range`, P95 − P5 of the 50 ms envelope over the WHOLE file,
while `gate_holes` writes two holes at `HOLE_FLOOR_DB` −70, `stop_at` the stop
and `ring_out` the tail to `RING_DB` −50. **MEASURED 2026-09-06 on run 19's
cues:** 21.9 / 22.3 / 21.2 % of cue-1001 / 1002 / 1004 sits under −60 dBFS, so
P5 is −92.2 / −95.2 / −95.4 against a P95 of −13.6 / −12.8 / −13.5, and
P95 − P5 is **78.6 / 82.4 / 81.9**. `m.fitness` is 78.603 / 82.436 / 22.512,
and 1004's whole discount is two COUNT terms, not its level: 12 grid onsets is
under `crowding`'s 15, and its single late onset gives `reach` 0.25 —
81.9 × 0.5 × 0.55 = 22.51, so `structure_terms` is 1.0 on all three and key 6
is the gate depth alone. Read over MATERIAL only — outside the `arc:hole` and
`arc:stop` spans `cue-<seed>.grid.json` already carries with their `end` — the
same three cues measure **19.5 / 19.7 / 21.7 dB** (material is 0.75 of every
one), and the two seeds key 6 separates by 3.8 dB are 0.2 dB apart. cue-1003,
the rubato copy `arc_cue` passed through with no gate in it at all, measures
35.7: an arced seed and a rubato one are ranked on axes 45 dB apart.
`dynamic_range`'s own docstring says it exists because `max − min` "reduces to
`peak + 53`" and was "ranking by LOUDNESS, which is the wall-of-sound bug it
was written to prevent, reappearing inside its own fix". The arc put the floor
back: the term now reduces to `P95 + 95` and ranks by how much SILENCE the ask
asked for.

Two terms inside it read the same handwriting. **Every slot `beatmap.slots`
finds on every arced seed is one of the arc's own two holes** — 1001
(26.90, 31.35) (49.30, 53.70) against `arc:hole` ends 31.35 / 53.71; 1002
(35.05, 40.85) (64.25, 70.00) against 40.86 / 70.02; 1004 (21.85, 25.45)
(40.05, 43.60) against 25.47 / 43.63. Not one comes from the music, so
`slot_term` is pinned at 1.0 — a constant with a number's face on it. It
costs the RANKING a term and costs the LINES nothing: no line step reads
`slots` while a plan exists. `step_04_lines.line_windows` calls
`line_windows.windows_for(metre, plan)`, which returns `plan.line_windows()`
whenever `music/plan.json` loads, and run 19's plan afforded FIVE windows
against the metre's two — the two instruments disagree 5 against 2 on the
same file (§19). Fix the ranking term here; the lines are capped elsewhere. `late_density` counts onsets in 80–95 % of the runtime, which on an
arced cue is mostly the stop and the title the arc wrote: cue-1004's ONLY late
onset is its `arc:title_hit` at 65.45 s, and that one onset costs it 45 % of
its score.

**REFUTED, and recorded so nobody fixes it twice:** `climbs` is not corrupted,
though its input is. Its tenth medians up to the stop run
−29.2 −28.5 −27.6 −22.4 −20.1 −19.1 **−84.5** −17.2 −16.7 −15.4 on cue-1002 —
the seventh median IS the hole floor, and −85.0 / −85.2 on 1001 / 1004, because
the ask puts the second hole at the same fraction of every cue. But `climbs`
compares tenths 2–3 with 8–9 and never reads the seventh, so the corruption
lands deterministically in the one slot the term skips: holes excluded, the
term moves 0.71 / 0.45 / 0.27 dB (cue-1002 11.09 → 11.54). Mask it for the
record, not for the ranking.

**RULE: an envelope term reads MATERIAL, and material is what the ARC'S GRID
says it is, not what a percentile finds.** §16 already applied this to the hard
out — "a detector only SEES what the arc cut". `dynamic_range`, `slots` and
`late_density` are owed the same mask, and `metre-<seed>.json` should carry
`material_fraction` beside `fitness` so a later round can tell a term's reading
from its mask.

**RULE: a number the step writes cannot grade the step.** Every term names the
quantity it reads AND what sets it; if the answer is *the arc*, it ranks
nothing.

**And `delivered` is a RATIO whose denominator the ask fixes.** `plan_score`
is weighted landed/asked, so landing all six of a six-event ask scores exactly
what landing all twenty of a twenty-event ask would. `cue_ask.placed_events`
writes four landmarks plus `REGISTERS[<row>].holes` — one hole for six of the
nine registers (elegy, gothic, romance, coming_of_age, tragedy, adventure),
two for procedural and detective, four for comedy — and the holes are
FRACTIONS of the form, so `bars` moves their position and never their number.
The LENGTH is set elsewhere: `bars_of` → `frame_budget.cue_seconds_for(
picture_budget(ctx), …)`, step 07's render allowance. **So a bigger picture
budget buys a longer cue with the same six landmarks, and no term reads the
rate back.** MEASURED on run 19: six asked landmarks over the 116.7 s cue that
shipped is 3.09 a minute; the cut maps carry 30 / 25 / 22 events
(`cutmap-100{2,1,4}.json`) = 15.4 / 16.8 / 18.2 a minute — and the shipped
seed is LAST of the three arced seeds on both rates. §0's HARMONY brick says
excitement is "how many clicks per minute"; nothing here counts them.
PROPOSED: `event_rate`, cut-map events per minute, into `metre-<seed>.json` —
free, `map_cue` already wrote the map — carrying the name of the instrument
that counted it, because the ask's landmarks and the cut map's events are 6
and 30 on the same file and may never be compared.

**And nobody can say which key decided run 19.** `grade` keeps `form`, `fit`
and `delivered` in the in-memory `state`; `ship` writes only the winner, to
`music/metre.json`. A `metre-<seed>.json` holds bar, bars_in_mode, beats,
beats_per_bar, bpm, downbeats, fitness, grid, hits, phrase_starts, rel_path,
seconds, seed, slots, stopdowns, title_hit — no fit, no form, no delivered.
What run 19's files DO say is that the choice did not fall to tempo:
`music/metre.json` is seed **1002 at 82.25 bpm** against 100 asked
(`tempo_error` 0.1775 → key −1) where seed 1001 at 107.22 gives 0.0722 →
key 0. Under `best_of` 1001 wins the tempo key and 1002 shipped, so one of
delivered / form / `fit_of` separated them and the step recorded none of the
three. All four seeds were rendered in one batch (18:50–18:55) at one ask, so
`in_the_running` retired nobody. `warn_short` logged what that cost:
**shipped OFF TONE**, an 82 BPM cue for a 100 BPM ask, with an on-tone
sibling beside it.

**RULE: a selection that cannot be replayed from the files the step wrote is
not a measurement.** Write `delivered`, `form` and `fit` into
`metre-<seed>.json` beside `fitness`, for every seed, before this file argues
from it again.

The first rule kills the ladder too: four step-03 runs in
`trailer/main/learnings.jsonl` carry a
byte-identical `measured` string across attempts 1–4 ("ask 0.62 delivered,
85.4 bpm against 100 asked, metre, fitness 4.2" ×4, rows 221–224; again at
rows 277–280, "ask 0.75 delivered, 131.9 bpm … fitness 78.4" ×4 for 1780 s of
wall clock) — four extra seeds and two reauthors for a constant — and the 0.85
floor is met in no recorded run (best 0.75). It is a constant because
`verdict` reports four of the six keys: form and fit, the two that actually
separate seeds, are neither in the string nor on disk. A rung that cannot move
a term is not a rung, and ~30 min a run is spent proving it against a 6 h
ceiling.

**And `delivered` is TIME, not content.** `cue_ask.verify` matches an asked
event to a cut-map event of the right kind within one bar (`match_event`) and
fills `measured`; nothing anywhere reads what the audio DOES there. The four
instruments that would are written, tested and have **no production caller** —
`pulse_present` (the share of a window's BEATS carrying an onset),
`onset_density` (onsets per BAR), `section_level`, `ending_kind` — all four
proved on audio synthesised from the ask (`tests/synth_ask.py`) and never
pointed at a render. (`music_events.span_stats` does write `onset_density`
beside every cut-map event, but per SECOND and over `affords`, the gap to the
next event — 1.1 s on cue-1001's `arc:pulse_in` row, half a bar. That is
texture for `cue_spans.sections_of`, not the asked window.)

MEASURED on run 19's cut maps — the median `onset_density` of the events
before `hard_out`, dropouts excluded, **per SECOND**, over all the material
and by TIME-third of it:

| seed | all | first third | middle | last third |
|---|---|---|---|---|
| 1001 | 0.71 | 0.33 | 1.01 | 1.15 |
| **1002 — SHIPPED** | 1.26 | **1.26** | **0.71** | **2.02** |
| 1004 | 0.55 | 0.41 | 0.14 | 0.99 |

(Round 1 of this file stated these per BAR and no reading of the cut maps
reproduces those figures; the recipe above does. Cite a recipe or do not cite
a number.) No term ranks on any of it, and the seed that shipped (1002,
`music/plan.json`) is the densest of the three by accident.

**And the ORDER is chosen on the one property the next line overwrites.**
`cue_arc.ascending` sorts the render's 4-bar phrases by MEAN LEVEL, then
`ride_gains` moves every material bar to `ride_targets` within `RIDE_MAX`
12 dB: delivered = level + `clip(target − level, ±12)`. The targets span 14 dB
(`RIDE_DB` −26 → −12) and §16's measured phrase range is 9 dB, so the clip can
bind by at most 14 − 12 = **2 dB** and reversing the entire order moves the
delivered staircase by at most 2 dB of 14. The sort therefore decides only
WHICH MATERIAL is where, on the one criterion the next call erases — and
`fit_of` then grades the ride's own arithmetic on the result. What survives a
per-bar gain and an FIR is the ONSET COUNT, and it ratchets 1.6× where the
level ratchets 14 dB, and not monotonically: the shipped cue's INTRO is busier
than its middle, where `cue_ask.DENSITY_TEXT` wrote "one figure at a time"
over the first section and "the densest bars of the piece" over the drop.

**RULE: an ordering sorts on a property the stages after it cannot change.
Level is not one — the ride writes it. Density is.** PROPOSED, no GPU, no
credits, no new pin: `ascending` keyed on the phrase's onset count, level
breaking ties, and **`density_arc`** — last material third minus first, per
second — into `metre-<seed>.json`. By §15 item 5's rule it RANKS.
UNVERIFIED: whether a density key would order THESE renders differently from
the level key is unmeasured — it needs the renders' per-phrase onset counts,
and no file the step writes carries them.

**State a rate per SECOND, never per bar, and name its ceiling.**
`music_events.onset_peaks` thins peaks by `ACCENT_GAP` 0.25 s — a hard ceiling
of 4.0 onsets per second — and every density in every cut map and span carries
it. On run 19's bars (2.24 / 2.92 / 1.82 s) that one ceiling is 8.96 / 11.68 /
7.28 PER BAR, so a per-bar floor is a 60 % different demand per seed and asks
LEAST of the fastest cue. `beatmap.onsets` is a different instrument again — a
`GRID_DB` rise thinned at 0.35 s, ceiling 2.86/s — and it is what grades
`late_density`, `crowding` and `stops_dead`. The two onset counts in this step
are not the same quantity and may never be compared.

Why three consecutive levers could not have answered him: `cue_arc.ride` is a
per-bar gain (`samples * 10 ** (gain / 20)`) and `cue_voicing.voice` is a
linear-phase FIR (`fftconvolve`). **Neither changes an onset count.** Rows
62–64 moved every level and every band; the word did not move. §16's Open
already names the next lever — the MATERIAL — and onset density per second is
the number it has to hit.

**And ARC_VERSION 9 moved a dimension it never reads back.**
`cue_voicing.voice` takes ONE mean spectrum over the WHOLE render (`spectrum`:
half-overlapping 8192-pt Hann windows, power-summed, so the loudest bars set
the gains) and lays ONE linear-phase FIR over the whole file. It is a static
tilt: it cannot brighten the last third against the first, and it gives the
intro the climax's voicing. Nothing reads a band back — `best_of`'s six keys
are level and time, and half the bands it moves are above the instrument's
Nyquist anyway (§18). The one voicing number that exists, "the arced cue's
distance to the reference 3.6 → 2.5 dB", was taken by hand on raw-1001 for
BUILD row 64 and is in no file the step writes. All seven
`tests/test_cue_voicing.py` tests are on synthesised noise and planted bumps;
none has read a rendered cue. `tone.register_arc` is the same shape:
`cue_ask.form_text` and `music_tone.arrangement` write it into the caption and
nothing anywhere reads a register off a render — so §6's "when a mood reads
wrong, the register is usually wrong before the key is" is unenforceable, and
§5's mechanic 7 is asked for by every caption and checked by nothing.

**RULE: a dimension the step MOVES gets a term that READS that dimension back
on the delivered file.** Level has `fit_of`; spectrum and register have
nothing, so the voicing is a hope. Rows 62–64 moved level, level again, then
every band — the three dimensions the step can see — and the word did not
move.

The two missing numbers cost no GPU, no credits and no dependency (PROPOSED):

- **residual** — `band_levels(*spectrum(cue, rate))` against
  `reference_db(centres)`, dB RMS, over the material before the stop. Row 64's
  hand number, made a term.
- **brightening** — the same read on the LAST material third minus the FIRST,
  above 1.6 kHz. That is `register_arc`, delivered, in dB.

Both belong in `metre-<seed>.json` beside `fitness`. By §15 item 5's rule
neither may REFUSE a seed until a reference trailer cue has been measured
here; they RANK, and they give the next round something to argue from.

The one instrument already built that reads the RENDER and not the arc:
`studio/cue_listen.py` (CLAP, 13 tests, BUILD row 59 — the music block's only
open row, "not wired into step 03"). It reproduced the owner before he spoke:
the sixteen rejected cues were heard as `song` (mean 0.595, AUC 0.04 against
trailer-asked cues), and `as_chamber` separates at AUC 0.97. Wiring it spends
no credits — but `transformers` is in neither `pyproject.toml` nor `uv.lock`,
and `ClapEmbedder` defaults to CUDA, so it must be constructed `device="cpu"`
or it takes VRAM from ComfyUI. Rank, never a threshold, and only the probes
with an AUC behind them (`parlour`, `song`, `drone`) may refuse a seed.

---

## 18. The instrument — one argv decides what this step can hear

`beatmap.decode` asks ffmpeg for `-ac 1 -ar 22050` and `envelope_of` reports
the dBFS of a 50 ms broadband RMS. Every level in the step is that number:
`RIDE_DB`, `BLACK_DB`, `STAIRCASE_DB`, `RING_DB`, `fit_of`, `climbs`,
`stops_dead`, `trailer_fitness`. Nothing downstream is graded in it — step 08
normalises the master to `TARGET_LUFS` −14 and `qc.py` reports
`integrated_lufs`, `title_hit_lu` and `act3_over_act2_lu`, momentary LUFS from
`trailer_assemble.loudness_readings` (ffmpeg `ebur128`, already a dependency,
no new pin). §4 names the delivered unit in the one place that cannot act on
it — a caption's aim, and §16 established the model gives no order.

They are not the same reading. **MEASURED 2026-09-06 on the shipped
`cue-1002.flac`, bar by bar on its own `cue-1002.grid.json` downbeats, 25
material bars, each median taken from 0.4 s into the bar so the 400 ms window
has filled: momentary LU minus 50 ms dBFS is mean +5.38, sd 1.30, min +2.46,
max +7.43 — a spread of 4.98 dB.** Two mechanisms, both in that argv: `-ac 1`
mono-SUMS, so a wide bar reads quieter than a centred one of the same loudness,
and there is no K-weighting, so a bar's spectrum moves its reading. `fit_of`
separates seeds at `FIT_BAND` 2.0 and scored 1.1 / 1.3 / 1.4 — the
instrument's disagreement with what is heard is larger than the tolerance and
larger than the fit. On that file bars 26–27 (−17.1 / −17.6 dBFS) and bars
28 / 30 (−17.6 / −17.1) are four bars the ride and `fit_of` call identical;
heard, they are −13.3 / −14.0 against −10.2 / −11.0. Three LU of wobble in the
climax that no term in this step can see.

**And `-ar 22050` caps the step at 11.025 kHz.** `cue_voicing.EDGES` runs to
20 000 and `edges_within(44100)` keeps every edge, so the top two bands the
voicing moves — 6.4–12.8 k and 12.8–20 k — are half and wholly outside the
decoder. **MEASURED: above 11.025 kHz raw-1002 integrates at −45.87 LUFS and
the shipped cue-1002 at −32.63, +13.2 dB, where the whole file moved +1.6
(−13.30 → −11.70).** Not one decibel of that reaches any level, onset, impact,
slot or fitness number. So §17's `residual` and `brightening` are read at the
cue's own rate, `cue_voicing.spectrum` over `cue_conform.read_cue` — built the
obvious way, on `beatmap.envelope` like every other term here, `brightening`
would return a constant and close the question wrongly.

**Every arced cue also arrives at step 08 over full scale.** MEASURED,
`loudnorm` `input_tp`: cue-1001 **+0.19**, 1002 **+0.18**, 1003 **+0.24**, 1004
**0.00** dBTP, out of `cue_punct`'s 0.85 tanh knee, at −12.80 / −11.70 /
−15.18 / −12.03 LUFS integrated. The master they fed landed at −15.46 LUFS for
a −14.0 target (`qc.json`), and `mix` takes
`gain = min(to_target, to_ceiling + LIMITING_DB)` — so a peak-bound master is
POSSIBLE and unproven, because `mix` measures the mix's `input_tp` and writes
it nowhere. That ledger line belongs to `08-assemble`, not here.

**RULE: the number that RANKS a seed reads back in the unit the delivered
trailer is graded in.** The ride keeps working in dBFS — it is a per-sample
gain and LU is not — but the ranking terms are PROPOSED in LU, one `ebur128`
pass per seed (about 2 s of CPU on a 117 s cue, measured here), no GPU, no
credits, no new pin:

- **`fit_lu`** — per-bar median momentary LU on the arc's own downbeats against
  `RIDE_DB` shifted by that cue's measured mean offset, dB RMS, scored exactly
  as `fit_of` is.
- **`cue_tp`** — the cue's true peak, so a cue that arrives over 0 dBTP is
  visible where it is made instead of in the master.

Both in `metre-<seed>.json` beside `fitness`. By §15 item 5's rule they RANK
and refuse nothing until a reference trailer cue has been measured here.

---

## 19. How many times the trailer can SPEAK is decided here

`studio/trailer_dialogue.order_lines` — "Hook -> answer -> threat -> (title) ->
button, one line per window" — opens on
`budget = min(len(slots), len(pool), MAX_LINES)`. On run 19 `pool` was 25
labelled lines and `MAX_LINES` is 13
(`ceil(SPEECH_CEILING_PER_100S 12 × PINNED_DURATION 108 / 100)`), so the term
that bound was `len(slots)` — the line windows of the plan THIS step ships.
It is in none of `best_of`'s six keys.

**MEASURED 2026-09-07 on run 19's own files.** Recipe:
`cue_spans.plan_of(CutMap(cutmap-<seed>.json), Metre(metre-<seed>.json))`,
then `len(plan.line_windows())`; the 1002 row also reads straight out of the
shipped `music/plan.json` and matches it window for window.

| seed | picture (`hard_out`) s | sections | windows | afforded occupancy |
|---|---|---|---|---|
| 1001 | 76.09 | 5 | 5 | **0.187** |
| **1002 — SHIPPED** | 99.20 | 6 | 5 | **0.144** |
| 1003 (the rubato copy) | 29.40 | 3 | 2 | 0.194 |
| 1004 | 61.81 | 4 | 4 | **0.184** |

`lines.json` carries exactly the plan's five windows — 2.19–15.872,
20.95–40.129, 46.689–60.539, 64.178–78.039, 90.438–98.468 — one line in each.
Step 05 turned the Police Inspector's into a card (learnings row 316, gate
`speaker_card`), so four were spoken: `lines.level.json` gives 1.59 + 2.31 +
5.74 + 1.75 = 11.39 s, mean **2.85 s** a line. Over a 99.2 s picture that is
`qc.json`'s `speech_occupancy` **0.115** against `speech_target` **0.30**,
with `music_only_fraction` **0.765** against QC_TARGETS' 0.45 and
`longest_music_only_s` **21.0** against 15.0 — three of the nine flags on a
master with `floor_pass` false and `shipped_flagged` true, and they are the
owner's first verdict in numbers: *all I hear is music … no dialogues.*

**The mechanism, one level down.** `CuePlan.line_runs` takes maximal runs of
`LINE_KINDS` spans (trough, sustain, phrase) INSIDE one section; an accent, a
section start and the tail each end a run, and a run under two beats is no
window. Accents measured 0 / 2 / 0 on the three arced seeds, so the run count
is the SECTION count or one under it (5 of 5, 5 of 6, 4 of 4, 2 of 3). And
sections are the DETECTOR's: `music_events.sections`, novelty at a
`clip(seconds/6, 12, 24)` kernel, boundaries `SECTION_GAP` **12 s** apart.
`cue_ask.KINDS` has no `section` entry — **the ask never asks for the one
event that decides how many times the trailer can speak.**

**One level under that: the sections mostly ARE the arc's own holes, and the
detector says so in its own evidence string.** MEASURED 2026-09-07, every
`kind: "section"` event in `cutmap-<seed>.json` against the `arc:hole` ends in
`cue-<seed>.grid.json` — 1001's four boundaries are 2.24, 17.91, **31.35**,
**53.71** against hole ends 31.35 / 53.71; 1004's three are 10.92, **25.47**,
**43.63** against 25.47 / 43.63; 1002's five are 0.73, 16.60, **40.86**,
61.27, 78.77 against 40.86 / 70.02. **Five of the twelve boundaries in the
batch are the moment an asked hole returns**, and that is not a coincidence of
times: each of those five carries `rms_rise>=6dB` and `step:+71.7…+73.2dB` in
its own evidence — `gate_holes` coming off — and the single highest-novelty
boundary of each seed (1.0) is a hole return. Five of the six asked hole
returns landed one. The sixth, 1002's second at 70.02, made none because a
DETECTED boundary at 61.27 held `SECTION_GAP` 12 s off it: one window lost, on
the seed that shipped, and lost to a neighbour, not to hole placement — its
two holes are 10 bars, 29.2 s, apart.

**RULE: the number of times the trailer can SPEAK is set by the number of
HOLES the register asks for.** `REGISTERS[<row>].holes` is the lever — one for
elegy, gothic, romance, coming_of_age, tragedy and adventure, two for
procedural and detective, four for comedy — and it is the only one of the
three routes to 0.30 below that step 03 already owns, needs no new event kind
and costs no render. PROPOSED: **`holes_landed`** (asked hole returns that
produced a boundary within one bar) into `metre-<seed>.json` beside `windows`;
a book whose picture needs more speech is given more HOLES, not longer lines.
The ceiling it shares with `SECTION_GAP`: a hole return within 12 s of any
other boundary buys no window, so comedy's four holes are not four — on a
40-bar form `round(f * bars)` puts its last two at bars 29 and 32, whose
returns are 3 bars = 5.4–7.2 s apart at comedy's 1.8–2.4 s bar, and collapse
into one.

**And the ceiling is under the target.** 12 s apart caps a 99.2 s picture at
nine sections; nine windows at the measured 2.85 s line is 0.26 occupancy,
still under the 0.30 `qc.speech_target` asks. So ranking seeds on windows
cannot reach it — it would only have shipped 1001 (0.187) over 1002 (0.144),
the same five lines in 23 fewer seconds. Reaching 0.30 needs longer lines
(one of run 19's four was over 2.4 s), or two lines in a window, or an asked
`section` landmark that puts the boundaries where the speech goes. The
dialogue step's own floor is written in the other unit and passes while this
fails: `SPOKEN_PER_100S` 5 wanted five lines on a 99.2 s picture and got
five, and five × 2.85 s is 0.144.

**RULE: step 03 does not only choose a cue, it chooses how many times the
trailer can speak. Count the windows before shipping the seed, and report
them in the unit the master is graded in.** PROPOSED — no GPU, no credits, no
new pin, since `plan_of` is one pass over a cut map already in
`state["maps"]`:

- **`windows`** = `len(plan.line_windows())` and **`window_s`** into
  `metre-<seed>.json` beside `fitness`, for every graded seed, not the winner
  alone.
- **`speech_afforded`** = `windows × 2.85 / hard_out`, against
  `qc.speech_target(hard_out)`. The 2.85 s is run 19's four spoken lines
  (1.59–5.74 s), not a norm; re-measure it and say which lines it came from.
- By §15 item 5's rule these RANK and refuse nothing — and note what a floor
  would have done here: no seed in run 19's batch afforded the target, so a
  floor on this term refuses the whole batch. That is a finding about the ASK,
  not about the seeds.

---

## 20. Never reuse a shot applies to SOUND

The arc can repeat material. `bar_order` fills a short render with
`order += list(range(phrases[-1][0], phrases[-1][1] + 1))` — the loudest
phrase again, at the END of the order, which is the drop — and
`tests/test_cue_arc.py::test_bar_order_fills_exactly_the_bars_asked_repeating_the_loudest`
asserts exactly that. §16 named it in a parenthesis and no number anywhere
said whether it had ever fired. It is worth a number twice over: a repeated
phrase fits its own ride target exactly, so `fit_of` REWARDS it, and the
standing order is that nothing is ever reused.

**The measurement, and it costs one ffmpeg decode.** Cut the delivered cue on
its own `cue-<seed>.grid.json` downbeats, mean-remove and unit-normalise each
bar up to the stop, dot every pair. Identical source material reads ≈ 1.0
whatever the ride did to its gain; unrelated bars read under 0.3. No GPU, no
torch, no tracker, no credits.

**MEASURED 2026-09-07 on run 19's three arced cues: nothing repeats.** Highest
pair 0.667 / 0.574 / 0.670, fourth-highest 0.155 / 0.127 / 0.294. The filler
did not fire on any seed of run 19 and the shipped climax is not a loop. The
arithmetic behind that was never written down: the arc spends `stop` = 34 bars
and so needs `ceil(34 / 4) × 4` = **36** whole-phrase bars, while
`render_batch` buys `ceil(ask.seconds) + TAIL_HEADROOM` = 96 + 4 = **100.0 s**
for every seed (FLAC STREAMINFO of raw-100{1,2,4}: 100.00 s each — the model
ran to the cap, it did not end early). At the bars those renders tracked —
2.24 / 2.92 / 1.82 s — 100 s holds about 44 / 34 / 55 bar lines, so 1002 is
the one that should have starved and did not. That is where derivation stops:
`seconds ÷ median bar` is not a bar count, and `len(metre.downbeats)` for a
RAW is in no file the step writes.

**It does fire, and five of the seven older arced cues on the same disk carry
it.** The same scan over every `cue-*.grid.json` in `trailer/main/music/`:
2001 bars 28 vs 32 at **1.000**, 2002 25 vs 29 at **0.997**, 3002 18 vs 26 at
**1.000**, 3004 15 vs 31 at **1.000**, 4003 29 vs 33 at **0.993** — bit-identical
bars, against 0.61–0.78 for 2003 / 2004 and 0.57–0.67 for run 19's three.
Those cues were cut by an earlier `ARC_VERSION` and their asks are not on
disk, so they establish *the defect exists*, never a rate. What makes it
invisible is that the threshold is ONE-SIDED: the arc is fed only when
`bpm ≥ 240 × ceil(stop / 4) × 4 / (ask.seconds + TAIL_HEADROOM)` — 240 × 36 /
100 = **86.4 BPM** for run 19's ask — while `TEMPO_BAND` 0.15 calls
85.0–115.0 on tone. A seed can be ON TONE and starved; a fast seed never can.

**What the scan found instead is a reuse the ask makes on purpose.** On all
three run-19 cues the most similar bars in the cue are 10, 14 and 24 — 1001
(10,14) 0.667, (10,24) 0.578, (14,24) 0.531; 1002 0.574 / 0.490 / 0.447; 1004
0.670 / 0.575 / 0.537 — and those are exactly the `arc:hit` bar and the two
`arc:hole` returns on every seed. `cue_punct.punctuate` calls `impact(rate)`
once per landmark with the same arguments under `SEED = 7`, so the hit and
both hole returns carry the **bit-identical 1.6 s sub impact**, and
`riser(rate, RISER_BARS * ask.bar)` gives both holes the bit-identical riser;
`tests/test_cue_punct.py::test_impact_is_deterministic` asserts the identity.
The three largest events in the cue — the same three moments §19 shows carry
the section boundaries, and therefore the speech windows — are one sound
played three times. A trailer's three braams escalate.

**RULE: a landmark is a shot. Deterministic ACROSS runs, never identical
WITHIN a cue.** The standing order says never reuse a shot, build a similar
one; `impact` already takes `seconds`, `f0`, `f1` and `gain`, so the similar
one is free — seed and sweep derived from the landmark's index, the third
landmark bigger than the first, and the run-to-run determinism `SEED = 7` was
written for kept intact. PROPOSED, no GPU, no credits, no new pin:

- **`repeat_max`** — the highest normalised bar-pair correlation up to the
  stop, with the pair — into `metre-<seed>.json` beside `fitness`. Above 0.9
  the cue contains a loop; run 19's three read 0.67 / 0.57 / 0.67, which is
  the punctuation, not the material.
- **`supply`** = `len(metre.downbeats) / (ceil(stop / 4) × 4)`, written from
  the RAW's metre inside `write_arc`, where it is already in hand.
- `duration` bought at the SLOWEST bar the register's band admits: 40 bars at
  detective's 84 BPM floor is 114.3 s, not 96, so an on-tone slow seed still
  supplies whole phrases.
- By §15 item 5's rule `supply` RANKS. `repeat_max` above 0.9 is the one
  refusal this file can justify with no reference cue, because the standing
  order names it: a repeated phrase is a reused shot in sound.

---

## Dependencies

`[dependency-groups] music` holds three pins and no more: `beat-this==1.1.0`,
`torch==2.14.0`, `torchaudio==2.11.0`. `librosa`, `soxr`, `einops` and
`rotary-embedding-torch` arrive under `beat-this` in `uv.lock` — they are
transitive, so never quote a version for them from this file. Two packages
this file's own steps name are in NEITHER `pyproject.toml` nor `uv.lock`:
**`demucs`** (the vocal-stem check in §8's third eligibility test and §15's
first item) and **`transformers`** (`cue_listen`, §17). Those two steps cannot
run until someone adds them. Tests inject fakes; nothing here calls a paid API.
