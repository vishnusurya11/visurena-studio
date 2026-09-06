---
name: trailer-music
description: Write the caption and the lyric sheet, render seeds, MEASURE each one, select on form before grid, and cut on the grid the music actually keeps. Instrumental by default; a voice only when the book earns it.
---

# 03 — Music (MiniMax Music 3, local ComfyUI)

Code: `studio/music_tone.py`, `studio/affirm.py`, `studio/beatmap.py`,
`scripts/trailer/step_03_music.py`, `scripts/trailer/build_music.py`,
`studio/trailer_edit.py`. Tags: **MEASURED** on our own files, **DOCUMENTED**
(vendor text, quoted), **CITED**, **PROPOSED** (a named test not yet passing).

Follow this file top to bottom. Every step is checkable without listening.

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
Chorus 67.2–91.2 · stop 91.2–96.0 · **title hit at 96.0 s = 95 %** ·
runtime 101 s. The title hit lands in the 93–96 % window at 84, 92, 100 and
120 BPM alike.

### Loudness staircase to aim at (momentary LUFS relative to the cue median M)

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
| 3 | subdivision doubling | "quarter notes, doubles to eighths at the first rise, doubles to sixteenths for the final third, over the same beat" |
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

## 8. The lyric path — when a voice is allowed at all

Instrumental is the trade default. Bergersen, on why his choirs sing syllables
and never sentences (DOCUMENTED, Gear Patrol): *"the moment people pick up on
actual lyrics of meaning, their focus has shifted away from the musical body."*

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

Scarlet's Latin lexicon, if a vocalise is ever wanted there: `Ra-che`
(the word on the wall), `vindicta`, `sanguis in pariete` (blood on the wall),
`filum sanguinis` (the scarlet thread), `Lu-ci-a` — and only in the Utah /
grief strand, never over Holmes. Its English alternative, if `01-story` ever
emits a thesis: **"Follow the scarlet thread"** — 6 syllables, imperative,
names nobody, lands the title word.

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
best_of(metres, asked, form) ranks on:
  1. form score          0-2   the two terms below
  2. grid == "metre"
  3. nearest tempo band to the tone's bpm
  4. trailer_fitness
```

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
`lift_term` (≥ 6 dB over the two bars before the hit), `slot_term`,
`late_reach`. A **slot** is a trough ≥ 6 dB under the median, held ≥ 1 bar,
starting in 20–80 %; slots are where lines live (`05-dialogue`).

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

### The cut walk — in BEATS, not seconds (HISTORY: removed in BUILD row 55)

**Superseded.** Step 03 writes `music/plan.json` (`studio.cue_plan.CuePlan`)
whose measured `spans` ARE the shot list; step 06 lays one shot per span and
`plan_cuts`/`ACT_BARS`/`FIGURE`/`BEAT_LOCK` no longer exist in `trailer_edit`.
`MusicBed.sections` carries the measured `CueSection`s and `MusicBed.cuts`
the span starts. What follows is the walk as it was, kept for the record.

```
L0  structural: title hit, structural_impacts, slot starts/ends, phrase starts
L1  downbeat
L2  beat
L3  half-beat        (only <= 75 BPM, only in the 80-92% band)
L4  envelope onset   (rubato fallback only)
```

```
plan_cuts(metre, events, duration, stretch):
    bar, beat = metre.bar, metre.bar / metre.beats_per_bar
    allowed(pos) = {n : MIN_SHOT <= n*beat <= cap(bar)} intersect
                   (pos<.3: {2,4,6,8} | .3-.8: {1,2,3,4} | .8-.92: {.5,1,2} | >.92: hold)
    cuts = [0]
    while cuts[-1] < duration - MIN_SHOT:
        want    = round_to_allowed(target_length(pos)*stretch / beat, allowed(pos))
        landed  = nearest(grid[level(want)], cuts[-1] + want*beat)
        landed  = min(landed, next_event_after(cuts[-1]))     # L0 by construction
        cuts.append(quantise(landed))
        if is_phrase_start(landed): next shot >= 1.5 x previous  # the reset
```

- Candidates are filtered by the constants **before** the arc chooses, so the
  walk cannot emit a shot under `MIN_SHOT` (0.4 s) or over the cap.
- **The hold** is exactly one 2-bar shot on a downbeat in the first third (its
  own cap `2·bar + beat`). The title card is the other exemption.
- `MAX_SHOT = max(4.0, 1.25·bar)`, quantised UP one frame. At 100 BPM it stays
  4.0.
- Accelerando in beats: 2 bars → 1 bar → 2 beats → 1 beat → half-beat at
  85–90 % → the hold.
- A **slot is a shot of its own**: starts on the downbeat the bed drops on,
  ends on the return downbeat.
- Never 100 % on beat — phrase-interior cuts on *actions* are what stop it
  reading as a metronome.

QC reads the DELIVERED file, never the plan: `qc.py` extracts the master's
audio, tracks it, scene-detects the picture (threshold below 0.3 — 9 of 44
low-contrast cuts were missed at 0.3) and reports `cuts_on_beat`,
`cuts_on_downbeat`, `cuts_on_L0`, `title_on_downbeat` (`on_cap_fraction`
graded the walk and left with it, row 55).
Targets (PROPOSED): ≥ 80 % / ≥ 30 % / 100 % / true.

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
- [ ] four seeds rendered per batch; every seed measured; the form score logged
- [ ] `cue-{seed}.caption.json` exists beside every cue
- [ ] `uv run pytest tests/test_music_tone.py tests/test_step_03_music.py tests/test_affirm.py -q`

---

## 15. Still unmeasured — do these before trusting anything above

1. **The `(instrumental)` sheet has never been rendered here.** The recipe is
   DOCUMENTED (SGLang reference render, vendor caption skill) but not
   MEASURED on this machine. Cheapest check, one GPU minute and zero credits:
   render **one seed at `max_duration` 20**, run `demucs` on the result and
   require the vocal stem to sit well below the rest of the mix with an empty
   whisper transcript. Then render the full cap.
2. **Whether `[Chorus]` twice reads as a drop.** The A-B-A-B-A argument is
   from library practice; what the model does with a second, later `[Chorus]`
   in a chamber score is a guess until eight seeds are measured with `climbs`.
3. **Section length with empty bodies.** "≈ 11.1 s per section" was measured
   while every section carried sung prose — the per-section time was the time
   to *sing* the note. Re-measure, then decide whether nine tags still land
   near 100 s or the sheet needs more.
4. **Whether the model parses "harmonic minor", "Neapolitan" or "sixteenth
   notes" at all.** Hence the sound-word translations in §6.
5. **Whether 100 BPM holds better than 84.** The guess is yes (100 is inside
   the vendor's own "groove" band and the pulse now sits on instruments with
   strong priors), and the tempo gate grades it per seed.
6. **`title_moment`'s look-back is a constant 6.0 s** (`studio/beatmap.py`).
   Two bars at ≤ 80 BPM exceed it, so a correct cue would be rejected.
   PROPOSED: make it metre-aware, `2·bar + beat`. `beatmap.py` belongs to
   another step; this is a request, not a change made here.
7. **A hand-tapped 16-bar fixture** for the drumless seed. Until it exists,
   `bars_in_mode` is an opinion about a rubato cue and no seed may be
   *refused* on it — only ranked.

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
   on 2.69 s bars (bars_in_mode 0.81). Length follows the render; the
   fit rule (row 56) trims the plan.
3. `cue_arc.arc` — `bar_levels` (median dBFS per bar) → `regular_bars` (a bar
   more than 10 % off the cue's bar is one the tracker stretched across a
   silence: cut in, it shifts every asked bar after it by one) → `bar_order`
   (whole 4-bar phrases, quiet to loud, the loudest repeated when short) →
   `assemble` (10 ms equal-power `step_join` at downbeats — the level step
   IS the arc, so `cue_edit.conform`'s 3 dB refusal does not apply) →
   `gate_holes` → `stop_at` → `title_piece` on the render's biggest impact.
   Measured on epic_cfg17-7005: climb −0.9 → 11.0 dB, loudest 25 % → 76 %.
4. `cue_punct.punctuate` — sub impact (70→32 Hz sine, click on the front,
   1.6 s) on the hit, every hole's return; a 2.5 s one at full gain on the
   title; a noise riser over the two bars into every hole; bed −3 dB; tanh
   knee at 0.85. Seed 7, so the same ask punctuates the same way every run.
5. `cue-<seed>.grid.json` — the arc's own bar lines. `measure` reads the cue
   on them (`known_grid`), because re-tracking a cue through its deliberate
   holes loses two downbeats per hole and reports stretched bars.

Three "an agent's output is its next input" bugs this surfaced, all fixed:
`Metre.seconds` was the last envelope window, not the decoded length (plan
82.079 ≠ 82.1); a stop's silence made the tracker report a 4 s bar the arc
placed first, shifting every asked bar; the arc'd cue re-tracked lost the
downbeats inside its holes. Each is a test now.

**Open:** the two holes are two bars each (5.4 s at 2.69 s bars) — the line
slot the ask specifies, long on the ear; riser and impact gains are typed
constants until a sound check names them; the tracker's downbeats on the
detective renders were jittery enough that only 3 of 8 phrases in raw-1001
passed `regular_bars` — the epic renders (§0) track cleanly at the asked
tempo, which is the other reason the caption carries the drums.

---

## Dependencies

`[dependency-groups] music`: `beat-this==1.1.0`, `torch==2.14.0` and
`torchaudio==2.11.0` from the CPU index under `[tool.uv.sources]` (the GPU
stays with ComfyUI), `librosa==0.11.0`, `soxr==1.1.0`, `einops==0.8.2`,
`rotary-embedding-torch==0.9.1`, `demucs==4.1.0`. Tests inject fakes; nothing
here calls a paid API.
