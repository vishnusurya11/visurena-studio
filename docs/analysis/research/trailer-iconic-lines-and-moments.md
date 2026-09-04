# Iconic lines and moments in a book trailer — finding, ordering, speaking

Position paper for the trailer blueprint, dimension: dialogue and set pieces.
Music-structure cutting is another paper. Each rule is tagged **MEASURED**
(run here, reproducible from the repo), **CITED** (source given), or
**PROPOSED** (an untested claim with the test that would settle it).

## 0. The brick

A trailer line is a sentence that **needs no scene and takes a side**. Every
rule below derives from that: length, syntax, position, what to speak and what
to set in type. The book's iconic *moment* is the same thing in pictures — an
image that needs no scene and changes the story. Neither is a property of the
text alone; both are what a culture *kept*, so external evidence outranks any
text feature, and the text features exist only for the book nobody kept.

## 1. Findings

### 1.1 What our pipeline does today (MEASURED)

- `line_value` ranks 271 Scarlet lines. Its top pick is *"I guess you are the
  daughter of John Ferrier. I saw you ride down from his house."* (3.1). The
  four lines placed in `plan.json` are that, *"I've found it!"*, a bet, and a
  line about writing an article. None is rendered — no TTS, no card.
- Wikiquote holds 19 quotations for *A Study in Scarlet*. **Only 4 survive into
  the screenplay** (the adapter dropped *"capital mistake to theorize"*, the
  brain-attic speech, *"His ignorance was as remarkable as his knowledge"*).
  Those 4 rank **39, 51, 104 and 158** of 271 under `line_value`. The book's
  title sentence — *"the scarlet thread of murder running through the
  colourless skein of life"* — is in the source and absent from the screenplay.
  **An iconic-line finder that reads only `screenplay.json` is structurally
  blind to most of what readers quote.** It must read `source/chapters/`.
- Every character analysis file already carries a `quotes` list (extraction's
  `notable_quote`, prose-wrapped; `studio/quotes.py` cleans it). Nothing in the
  trailer reads it.
- `load_iconicity` reads `analysis/iconicity.json`. **No book has one.** The
  6.0-weighted signal the story selector calls "the only one with evidence
  behind it" is always zero.

### 1.2 What real trailer lines look like (MEASURED over a 38-line corpus)

Corpus: 15 lines from WatchMojo's list, 4 from Lieu's *Matrix* breakdown, 19
widely-quoted lines whose trailer placement I could not verify (marked so in
the scratch script; they change no conclusion below).

| feature | value |
|---|---|
| words: median / mean | **4.5 / 6.2** |
| ≤7 words · ≤12 words · <5 words | 28 · 35 · **19** of 38 |
| questions | 7 (18%) — all as hook or threat |
| second person ("you") | 13 (34%) |
| first person opener | 7 (18%) |
| present tense | 37 (97%) |
| function | threat 12 · stakes 9 · hook 7 · promise 5 · button/joke 5 |
| position | pre-title 13 · open 9 · mid 8 · button 7 |

Run through **our** `line_value`: median **−1.5**; 26 of 38 score below zero,
18 below −2. *"This is Sparta!"* scores −7.6. Every question scores −6.6.
Meanwhile the Ferrier line scores 3.1, above all 38. The scorer is not noisy;
it is **inverted** on the two features that matter most:

- `len(words) < 5 → −3.0` deletes half the corpus. Short is not "too little
  said"; short is the *format*.
- `endswith("?") → −4.0` deletes the hook. Lieu: *"Any time someone asks a
  question or creates anticipation, that's a prompt for a shot or line of
  dialogue to be cut in as a response"* — a question is worth **more** when
  the trailer can answer it (§4). (CITED: derek-lieu.com, *How to Break Down
  Dialogue*)
- Exclamation → +1.0 risk. 8 of 38 iconic lines end in "!"; the risk is real
  but belongs to the *engine* choice (§5), not the line.

What it gets right and should keep: replies (−3.0), unbound "the X" (−2.0),
leading pronouns (−1.8), numerals (−2.5), causal connectives (−1.0). The
Cornell study confirms the pronoun and generality findings independently.

### 1.3 What the literature says makes a line memorable (CITED)

Danescu-Niculescu-Mizil, Cheng, Kleinberg, Lee, *You had me at hello* (ACL
2012; arXiv 1203.6360; corpus of 6,282 IMDb-memorable lines paired with
same-film, same-speaker, same-length controls): memorable lines use **rarer
words on commoner syntax** (lower unigram LM likelihood, higher POS-sequence
likelihood), and are **more general** — fewer third-person pronouns, more
indefinite articles ("a" over "the"), present tense. Distinctiveness is
front-loaded. Combined features ≈60% pairwise accuracy; humans do better, so
text features are a floor, not a finder. Corpus is downloadable and CC-licensed
for research; it is a ready held-out set for any scorer we write.

Lieu's taxonomy of usable dialogue: backstory/world · character · action
illustration · stakes · ideas/themes · setup-prompts (questions) · humour ·
interjections; the test is *"how much context does understanding it require."*

### 1.4 External iconicity for a public-domain book (MEASURED + CITED)

- **Wikiquote** (MediaWiki API, `action=parse&prop=wikitext`, CC BY-SA, no key,
  set a User-Agent) — worked first try. Bonus signal: editors **bold** the
  famous clause inside a longer quotation (`'''You have been in Afghanistan, I
  perceive'''`), which is a human-curated "compress to ≤12 words" already done.
- **Goodreads API**: retired December 2020; the quotes pages are scrape-only
  and against ToS. Do not build on it.
- **Kindle popular highlights**: no API, visible only to purchasers, scraping
  violates Amazon ToS. Ellenberg's Hawking Index is the only public use and he
  calls it "for entertainment purposes only".
- **Project Gutenberg itself**: no quote data, but the *book's own repetition*
  is free: a phrase the author repeats (Scarlet: "Rache" ×3 in the screenplay,
  the title phrase) is the author marking emphasis.
- **Illustration history** (Paget, Steele, Friston plates), film adaptations'
  own trailers, and Wikipedia's plot summary sentences are the moment-level
  equivalents; Wikipedia plot summaries are CC BY-SA and API-reachable the
  same way.

**Wikiquote coverage over the 30 analysed books (MEASURED 2026-09-03, MediaWiki
API, User-Agent set, one revid-keyed fetch per page).** Resolver: the book's
own page (`Title`, `Title (novel)`), else the author's page section, else the
character page section; disambiguation and film pages refused.

| Book | Where | Quotes | Bold |
|---|---|---|---|
| A Study in Scarlet | character page § | 18 | 9 |
| Frankenstein | own page | 67 | 27 |
| Dracula | own page | 37 | 9 |
| Pride and Prejudice | own page | 118 | 62 |
| The Adventures of Tom Sawyer | own page | 26 | 0 |
| Peter Pan | own page | 33 | 3 |
| Moby-Dick | own page | 145 | 39 |
| Metamorphosis | author page § | 7 | 3 |
| Dr Jekyll and Mr Hyde | author page § | 7 | 0 |
| The Picture of Dorian Gray | own page | 162 | 23 |
| Heart of Darkness | own page | 33 | 15 |
| The Time Machine | own page | 19 | 1 |
| The War of the Worlds | author page § | 10 | 3 |
| The Invisible Man | author page § | 17 | 0 |
| A Christmas Carol | own page | 35 | 20 |
| The Call of the Wild | author page § | 4 | 0 |
| Treasure Island | author page § | 10 | 3 |
| The Turn of the Screw | author page § | 10 | 0 |
| Wuthering Heights | own page | 52 | 14 |
| The Hound of the Baskervilles | character page § | 6 | 1 |
| Alice's Adventures in Wonderland | own page | 73 | 22 |
| The Wonderful Wizard of Oz | author page § | 23 | 7 |
| Robinson Crusoe | author page § | 16 | 0 |
| Around the World in Eighty Days | author page § | 4 | 0 |
| Twenty Thousand Leagues | author page § | 12 | 1 |
| The Secret Garden | author page § | 19 | 0 |
| Black Beauty | author page § | 17 | 0 |
| The Prince and the Pauper | own page | 19 | 0 |
| Dubliners | author page § | 14 | 8 |
| Beowulf | own page | 11 | 0 |

Distribution: 30/30 resolved, 0 zero-coverage; 14 own pages, the rest
author/character-page sections. Quotes per book: min 4, median 18.5, max
162, total 1024; ≥5: 28/30, ≥10: 25/30, ≥20: 12/30. The bold
convention holds on 19/30 pages (270 bold clauses); on the rest the whole
bullet is the unit. The "any novel" number is therefore: every canon book has
external evidence, but the thin tail (Call of the Wild 4, Eighty Days 4, Hound 6,
Metamorphosis 7, Jekyll 7) will yield ~1 kept line after the ~20% survival into
the pools measured on Scarlet — the §7 rule for `kept < 2` is what ships there.
A book off Wikiquote entirely was not observed in this corpus; the rule for it
is the same one.

### 1.5 Iconic moments and the trailer template (CITED)

Lieu: cold open → introduction → escalation → (twist) → climax → title →
button; *"at the peak of excitement, it ends and we get the title card."* Two
practices bear on selection: **the money shot is withheld** (the reveal is
implied by reaction, not shown — the shark, the face of the killer), and
**accents must relate to what was just said** or read as non sequitur.
Our `setup_value` sees emphasis (camera move), verbatim density, proper
nouns, ALLCAPS, entrances/exits, bindability. It does not see reversal,
first-sight, or reaction-to-unseen — the three things a trailer set piece is.

### 1.6 Speaking with Qwen3-TTS (MEASURED from the installed node + CITED)

Installed pack registers `FB_Qwen3TTSVoiceDesign`, `FB_Qwen3TTSVoiceClone`,
`FB_Qwen3TTSCustomVoice`, `FB_Qwen3TTSVoiceClonePrompt`, `FB_Qwen3TTSRoleBank`,
`FB_Qwen3TTSDialogueInference`, `FB_Qwen3TTSSaveVoice`, `FB_Qwen3TTSLoadSpeaker`.
Local weights: `Qwen3-TTS-12Hz-1.7B-{Base,CustomVoice,VoiceDesign}` and the
12 Hz tokenizer. Output 24 kHz mono (dialogue node hard-codes `sr = 24000`).

- **VoiceDesign** inputs: `text`, `instruct` (required), `language` (10
  languages + Auto), `seed`, `max_new_tokens` (512–4096), `top_p/top_k/
  temperature/repetition_penalty`. The 0.6B choice exists in the UI but the
  README locks VoiceDesign to 1.7B.
- **Instruct on the clone path**: `generate_voice_clone()` takes no `instruct`
  at all (signature verified in `qwen_tts/inference`). The 05-dialogue note is
  correct. `generate_custom_voice` drops `instruct` on 0.6B.
- **The pack's own stated best practice is "Voice Design then Clone"**
  (`LoadSpeakerNode` docstring): design one reference clip, `SaveVoice` it under
  `models/qwen-tts/voices/`, then clone every line from it. Third-party
  testing agrees: same instruct twice gives "distant vs close" timbre drift;
  the design→clone pipeline is the only consistency mechanism (CITED:
  ocdevel.com Qwen3-TTS guide, 2026-03). This is Brick 1 for voice: **a voice
  is BOUND by a reference clip, never described per line.**
- Instruct dimensions that work (CITED, getstream.io + ocdevel): gender, age
  (years), pitch/register, texture (breathy, raspy, husky, hoarse, mellow),
  emotion, pace, use case. **Accents mostly do not** (British drifts to US);
  celebrity names are blocked; duration words ("finish in 5 seconds") have no
  effect. Instruct language: English or Chinese only.
- Text: ≤2,048 chars; VoiceDesign ignores chunking for long text — keep every
  trailer line under one sentence group anyway. Ref clip for cloning 5–15 s;
  >30 s can hang generation. Provide `ref_text` or you are in x-vector mode.
- InstructTTSEval APS 82.9 (English) for 1.7B-VoiceDesign (CITED: Qwen3-TTS
  Technical Report, arXiv 2601.15621).

### 1.7 Trailer voice in the mix (CITED)

BOOM Library: VO mono and centred; HPF the low end, boost presence mids;
"a light, small-room reverb" to ground it without pushing it back;
consistent compression, upward compression on word-ends; **frequency-based
ducking** of music and SFX rather than a full level drop. Lieu's sound-mixer
piece: music/SFX "dropped dramatically" only when the story point must land;
reverb sets distance. **Correction (critic):** no duck exists in
`scripts/trailer/assemble.py`; the 12–15 dB figure is a SKILL assertion, not
code. The mix rule is therefore PROPOSED in §7.4, with its filter shape and
the LU gate that measures it.

### 1.8 Text cards (CITED)

Netflix Timed Text Style Guide: ≤20 characters/second adult reading speed,
≤42 characters a line, minimum 5/6 s, maximum 7 s. A 12-word quotation (~60
characters) is legible in 3.0 s; our card rule (`0.55 × words + 0.5 s`, floor
1.4 s) holds it 7.1 s — about 2× the reading floor, which is right for a card
that must be *felt*. Keep the rule; the cps figure becomes the **lower gate**.

## 2. Blueprint rules

**R1 (MEASURED).** Candidate lines come from THREE pools, merged and deduped:
screenplay dialogue, `analysis/characters/*.quotes` (cleaned by `quotes.py`),
and quoted speech in `source/chapters/`, plus a FOURTH pool — unquoted
narration — whose speaker is the book's narrator character when there is one
(§7.4). A line absent from the screenplay may still be spoken; it is
attributed by `attribute()` (§7.5) and placed on a shot of that speaker (R9);
a line `attribute()` cannot place is a card.

**R2 (MEASURED).** Fetch `analysis/iconicity.json` once per book from
Wikiquote (book page, author page, character page) and cache it. Fields per
line: `text`, `bold` (the editor-emphasised clause), `source`. Fuzzy-match
(token-set ratio ≥ 85) against the three pools. Missing file → text signals
only, and the run prints that it is flying blind.

**R3 (MEASURED).** Delete the `<5 words → −3.0` and `? → −4.0` terms. Replace
with: **length band** +1.0 for 3–12 words, −1.0 per 4 words past 14; **question
bonus** +1.5 when a later line can answer it (§4), else 0.

**R4 (CITED, Cornell).** Add generality features: +0.6 indefinite article,
−0.8 per third-person pronoun anywhere, +0.5 present tense, −0.6 past tense
main verb. Add distinctiveness: +1.0 × (mean IDF of content words against
the book's own dialogue) capped at 2.0 — a per-book LM, not a fixed THEME list.

**R5 (PROPOSED).** Title echo: +3.0 if the line contains a content word of the
book's title (`scarlet thread`, `one, but truly two`). Test: across the 30
analysed books, how many titles appear verbatim in a dialogue or narration
sentence; the rule is only worth keeping above ~40%.

**R6 (PROPOSED).** Function label per line via one FakeModel-testable Strands
call: `hook | stakes | threat | promise | button | exposition`. The slate must
contain ≥1 hook and ≥1 threat-or-stakes, else refuse; the button is optional.

**R7 (PROPOSED, replaces the rejected train=test rule).** The text scorer is
graded on a held-out set it was never tuned on: Cornell pairwise accuracy
≥ 0.55 and within-book Wikiquote-kept lines in the top quartile with the
iconicity term OFF (§7.2). The 38-line corpus is a smoke test only
(`test_sparta_outscores_ferrier_errand`).

**R8 (CITED, Lieu).** Moment candidates gain: **reversal** +3.0 (a scene whose
`state_changes` flips the lead's knowledge/allegiance — already in the
character analysis), **first sight** +2.5 (the figure's `first_chapter` scene,
or the first scene a named thing appears — RACHE, the ring, the pills),
**reaction to the unseen** +2.0 (an action line with `face|eyes|stares|
recoils` and no object named). **Withheld reveal** rule: the last lead/figure
meeting may be shown ≤0.6 s and never carries a line (already), AND the line
that *names* the figure's identity is forbidden even outside that scene.

**R9 (MEASURED).** A spoken line must start on a shot bound to its speaker
(exists). Add: a line from the *source* pool with no screenplay scene is
placed on the speaker's highest-`setup_value` beat in the matching chapter.

**R10 (PROPOSED).** Speak at most 4 lines (05-dialogue's budget stands); of
these the over-black line is a **card**, and any line with `risk ≥ 2` is a
card. A card and a voice never carry the same sentence.

## 3. Algorithms

```
rank_lines(book):
    pool  = dedupe(screenplay_dialogue + character_quotes + source_quotes)
    icon  = load_iconicity(book)              # {norm_text: {bold, sources}}
    idf   = idf_over(pool)                    # per-book, content words only
    for line in pool:
        s  = stance(line)                     # keep: first-person, absolutes, anaphora
        s -= penalties(line)                  # keep: reply, unbound, pronoun-open, numeral, causal
        s += length_band(line)                # R3
        s += generality(line)                 # R4: a/the, 3rd-person, tense
        s += min(2.0, distinctiveness(line, idf))
        s += 3.0 * title_echo(line, title)    # R5
        s += 6.0 * icon.get(norm(line), 0)    # external evidence outranks all text terms
        s += 2.0 * (line in icon.bold)        # editor-compressed clause
        line.score = s
    return sorted(pool, by=-score)

rank_moments(book):                           # extends setup_value
    for setup in authored_setups(scenes):
        v  = setup_value(setup)               # emphasis, verbatim, names, caps, entrance, bound
        v += 3.0 * reversal(setup)            # scene has a knowledge/allegiance state_change for lead
        v += 2.5 * first_sight(setup)         # figure's first scene, or a named thing's first scene
        v += 2.0 * reaction_to_unseen(setup)
        v += 6.0 * icon_scene(setup.scene)    # Wikipedia-plot-sentence / illustration match
        v  = 0 if reveals_identity(setup)     # withheld
    return sorted(...)

order_lines(top, troughs, figure):            # the conversation across cuts
    hook   = first(top, kind in {hook, question})
    answer = first(top, kind in {stakes, exposition}, speaker != hook.speaker,
                   shares_content_word(hook))  # Lieu: the accent must relate
    threat = first(top, kind == threat, speaker == figure) or first(top, threat)
    button = first(top, kind in {button, joke}, words <= 6)
    seq = [hook, answer, threat]              # question -> answer -> threat -> TITLE
    slots = measured_slots(cue)               # stopdowns / instrumental gaps, from the DELIVERED cue
    n = min(len(slate), len(slots))           # lines = min(slate, measured slots)  (agreed with music paper)
    for slot in slots[:n]:                    # choose the LINE for the SLOT; never compress a line into it
        line = first(seq, measured_seconds(line) <= slot.seconds - 2 * slot.beat)
        place line on whole beats from beat 2 or 3 when bars_in_mode >= 0.65, else span rule
    button after the title impact if a slot exists
    refuse if hook is None or (answer is None and threat is None)
```

`shares_content_word` is the minimum test for "answered": *"What is the
Matrix?"* → *"The Matrix is the world…"*; for Scarlet, *"You have been in
Afghanistan, I perceive"* (hook) → *"It was easier to know it than to explain
why I know it"* (answer) → *"There is death in one and life in the other"*
(threat, Hope) → title → *"No data yet."* (button, in type).

## 4. Qwen3-TTS voice-design recipe

**Design once, clone always** (§1.6). Per character with a bound line:

1. `instruct` from the cast card + analysis, English, 15–40 words:
   `"{age_band → 'a man in his late thirties'}, {gender}, {register from
   profile.mental → 'precise, quick, dry'}, {class/role → 'educated London
   professional'}, {texture from epithets → 'lean, clear, slightly nasal'},
   measured pace, no accent named."` Never name an accent (drifts to US
   anyway) or a real actor (blocked). Era goes into *diction* ("formal,
   clipped Victorian phrasing"), not accent.
2. Render a **neutral 8–12 s reference** with that instruct on a fixed seed
   (a sentence of the character's own, from the pool, NOT a trailer line),
   `SaveVoice` → `voices/<book>-<char>.wav` + `.qvp` + `ref_text`.
3. Render every trailer line with `FB_Qwen3TTSVoiceClone` from that prompt
   (`ref_text` supplied → ICL mode), one seed per character, `max_new_tokens`
   capped at 512 for a ≤12-word line (the infinite-loop failure mode).
4. **Emotion** is not an instruct on the clone path. It is a second reference:
   design `holmes-urgent.wav` with the same instruct + *"speaking urgently,
   raised pitch, fast"* and clone the urgent line from that. Two references per
   character, `calm` and `peak`, is the whole emotion vocabulary a trailer needs.
5. **Gate** (PROPOSED, mirrors `identity.py`): speaker-embedding cosine
   between each rendered line and the character's reference ≥ 0.75
   (resemblyzer); below that the line re-rolls with a new seed, three tries,
   then falls back to a card. Test the threshold on 20 lines before trusting it.
6. **Never `atempo`.** Render every slate line, measure its seconds from the
   file, and choose the line for the slot (§3, §7.1). A line that fits no slot
   is a card or is dropped.
7. Post: HPF 90 Hz, +2 dB at 3 kHz, light small-room reverb (pre-delay ~15 ms,
   RT ~0.4 s), mono centre, −20 LUFS-S per line before the ducker.

**Multi-character**: `DialogueInferenceNode` is for continuous scenes with
`pause_*` timing; a trailer wants each line as its own file placed on its own
trough, so use the per-line clone path and skip it.

**When the voice cannot be designed**: a first-person narrator (Watson,
Utterson) is a character with a card — design him. A pure omniscient narrator:
design *"the author's voice"* from the era/gender of the author, use it only
for the title-echo line, and prefer the card. No speaker at all → card.

**Workflow shape** (API-format JSON + manifest, as `comfy.py` expects):

```
audio_qwen3tts_design_reference.json
  1 FB_Qwen3TTSVoiceDesign  {text, instruct, model_choice=1.7B, language=English, seed}
  2 FB_Qwen3TTSVoiceClonePrompt {ref_audio<-1, ref_text=text}
  3 FB_Qwen3TTSSaveVoice   {voice_clone_prompt<-2, audio<-1, ref_text, filename}
  4 SaveAudio              {audio<-1, filename_prefix}
  inject: text, instruct, seed, filename, filename_prefix

audio_qwen3tts_clone_line.json
  1 FB_Qwen3TTSLoadSpeaker {filename}
  2 FB_Qwen3TTSVoiceClone  {target_text, voice_clone_prompt<-1, ref_text<-1, model_choice=1.7B, seed, max_new_tokens=512}
  3 SaveAudio              {audio<-2, filename_prefix}
  inject: filename, target_text, seed, max_new_tokens, filename_prefix
```

The existing `audio_qwen3tts_tts_single_speaker` uses the *other* pack
(`Qwen3TTSEngineNode`, tts_audio_suite) and clones from `voice_narrator_
attenborough.wav` — a real person's voice on a commercial trailer; retire it
for this use.

**File layout** under `library/<book>/trailer/voice/`:

```
voices/<char>.calm.wav  <char>.calm.qvp  <char>.calm.txt   (reference + prompt + ref_text)
voices/<char>.peak.wav  ...
lines/<beat_id>.<n>.wav                                    (24 kHz mono, raw)
lines/<beat_id>.<n>.json  {text, speaker, register, seed, seconds_measured, similarity, slot}
voice.json               {instructs per char, seeds, gate results, cards[]}
```

## 5. Packages

- `resemblyzer==0.1.4` — speaker embedding for the identity gate (R-gate in §4).
  Old but pure-PyTorch; if it fails on the pinned torch, `speechbrain==1.1.1`
  ECAPA is the fallback.
- `rapidfuzz==3.14.6` — token-set matching of Wikiquote lines to the pools.
- Nothing else; Wikiquote is `urllib`.

## 6. Not verified

- No line was rendered; §4 steps 2–7 and the 0.75 threshold are untested
  here. The drift claim (same instruct → different timbre) is third-party.
- Trailer placement for 19 of the 38 corpus lines is from memory; the 15
  WatchMojo + 4 Lieu lines alone give the same medians (4 words, 79% ≤7).
- Whether the Wikiquote bold convention is consistent across books (checked on
  one page).
- R5's title-echo frequency across the 30-book corpus.
- Whether `resemblyzer` installs cleanly against the repo's torch pin.
- The Cornell release size (critic: 6,282 lines; paper: ~2,200 pairs).
- `speech_seconds` residual against rendered lines (§7.1 test not yet run).
- Qwen3-TTS output sample rate is inferred from the dialogue node's constant
  and third-party docs; the official card does not state it.

## 7. Rebuttal (critic's round, 2026-09-03)

**7.1 `speech_seconds` — CONCEDE, FIX.** `0.22 × vowel-groups + 0.45` never met
a rendered line, and a speaking rate belongs to the *designed voice*, not to
English. (a) Placement reads no prediction: `order_lines` (§3) renders the
slate, reads `seconds_measured` from each file, and chooses the line for the
measured slot; `speech_seconds` is only a pre-filter (skip lines predicted
> 2× the longest slot). (b) The formula becomes a fit:
`tests/test_voice.py::test_rate_fit_residual_under_15pct` (`@pytest.mark.local`)
renders 20 lines per designed voice (16 `pick_lines` candidates + 4 corpus
lines), fits `seconds = a·groups + b`, writes
`library/<book>/trailer/voice/<char>/rate.json`, fails if residual P90 > 15%
— that residual is the number asked for.

**7.2 R7 train=test — CONCEDE, FIX.** R7 rewritten (§2). Held-out: the Cornell
corpus (ACL P12-1094) — ~2,200 (M, N) pairs, same character, same word count,
median 5 lines apart. `tests/test_line_value.py::test_beats_chance_on_cornell_pairs`
runs `line_value(speaker=None, leads=())` with iconicity off and asserts
pairwise accuracy ≥ 0.55 (chance 0.50; the paper's generality 56.7%,
distinctiveness 62.1%, all features 64.3%, humans 78%). Pairs are
length-matched, so the length band is inert and the test grades exactly the
other terms. Within-book gate, iconicity OFF: ≥ 50% of Wikiquote-kept lines in
the pools rank in the top quartile (Scarlet: 39/51/104/158 of 271 → 2/4). The
38 lines remain one smoke test.

**7.3 Wikiquote coverage — FIX, measured (§1.4).** 30/30 resolve, none at
zero, once the resolver tries the author page and the character page. Median
18.5 quotes, min 4, total 1,024; 28/30 ≥ 5, 25/30 ≥ 10; bold on 19/30. For
the thin tail (4–7 quotes: Call of the Wild, Eighty Days, Hound, Metamorphosis,
Jekyll) and for a pageless book: `iconicity.json` records `{source, revid, n,
kept}`; when `kept < 2` the manifest says `iconicity: thin`, the finder is the
text floor plus the in-repo judged signals (`characters/*.quotes`, title echo,
repetition) plus the R6 function judge, and — PROPOSED — spoken lines ≤ 2, the
rest cards — without external evidence a spoken line bets on a model's
taste, and a card is the cheaper way to be wrong.

**7.4 Duck and narration — CONCEDE both, FIX.** No duck exists; the rule is
PROPOSED: each line loudnormed to −20 LUFS-S; bed −26 LUFS-S inside the line
window (6 LU under), untouched outside; attack 160 ms, release 0.8–1.2 s; one
window per line. Shape:
```
[bed][line]sidechaincompress=threshold=0.03:ratio=6:attack=160:release=1000:level_sc=1[d];
[d][line]amix=inputs=2:normalize=0[mix]
```
Build sections: `acrossover=split=250 4000` on the bed, sidechain the mid band
only. Gate: `test_line_sits_six_lu_over_bed_in_its_window` (synthetic bed +
tone, `ebur128`). Narration is a fourth pool (R1): unquoted sentences through
the same scorer, speaker = the narrator character. Scarlet's `scenes.json` has
`frame.narrator` only for 9 embedded-testimony scenes; the first-person
narrator is recorded nowhere, so the story stage must emit
`narrator: <character_id | omniscient>` per book. A character narrator has a
card and is designed like any speaker; omniscient → card (V9). "The scarlet
thread" is Holmes's dialogue, not narration — it enters via §7.5.

**7.5 Attribution — CONCEDE the gap, FIX, measured.** Scarlet: 617 quoted
paragraphs. A speech tag naming exactly one alias attributes 109 (18%); 29 name
two (the addressee too: "Dr. Watson, Mr. Sherlock Holmes," said Stamford) and
are refused; 479 carry a pronoun tag or none ("said he", "my friend remarked").
"Nearest preceding tag" is the weak rule. The function:
```
attribute(paragraph):
    for sentence in paragraph:                  # paragraph-sibling match
        m = best_match(sentence, screenplay_dialogue + character_quotes)
        if m.ratio >= 0.85: return m.character  # 168/617 (132 screenplay, 36 quotes)
    names = aliases inside the paragraph's own speech tag
    return names[0] if len(names) == 1 else None   # 109/617; None = card only
```
Union 246/617 (40%); where both fire they agree 20/31. The `quotes` list alone
is not enough: capped at 12 per character, holding none of the three thesis
lines. The sibling rule places "scarlet thread": its paragraph also holds "I
shall have him, Doctor", which the screenplay gives to Holmes.
Failure modes: the 11/31 disagreements (quoted letters, a speaker quoting
another) → a line the rules split on is refused; reported speech inside
narration lands on the narrator. Tests: `test_source_pool_lines_carry_a_speaker_or_are_cards`,
`test_scarlet_thread_attributes_to_holmes`.

**Resolved with the music paper.** `lines = min(slate, measured slots)`; with
`bars_in_mode ≥ 0.65` a line occupies whole beats from beat 2 or 3, the span
rule only in the rubato fallback; no `atempo` — the line is chosen for the slot
(§3, §4 step 6). The pre-title stopdown must hold threat + 2 beats; that slot
is a fitness term the music paper owns.

Sources: arXiv 1203.6360 · aclanthology.org/P12-1094 · cs.cornell.edu/~cristian/memorability.html ·
arXiv 2601.15621 · github.com/QwenLM/Qwen3-TTS · huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign ·
ocdevel.com/blog/20260302-qwen-tts-voice-cloning · getstream.io/blog/qwen3-voice-design ·
derek-lieu.com (Basic Trailer Story Structure; How to Break Down Dialogue; The Trailer Line of Rising Action;
Why Start Story Trailers With Dialogue; Intercutting Dialogue With Gameplay; Sound Mixers) ·
watchmojo.com Top 10 Greatest Movie Trailer Quotes · boomlibrary.com Sound Design, VO and Music for Film Trailers ·
partnerhelp.netflixstudios.com Timed Text Style Guide · en.wikiquote.org/w/api.php ·
en.wikipedia.org/wiki/Hawking_Index · goodreads.com developer forum (API deprecation, 2020-12).
