# Assumptions made while you were asleep

You said to assume rather than wait, and to note what I assumed. Here it is,
most consequential first.

## 1. Two books: A Study in Scarlet and Jekyll & Hyde

Sherlock because its twelve reference sheets already existed and were good —
it is the fair test of whether binding was the missing piece. Jekyll because
the duality is inherently cinematic and it has a complete 50-scene screenplay.
Its references were generated fresh (6 characters, 7 locations).

## 2. Literary register, not action

Both are canonical texts, so there is no plot to withhold — the trailer's job
shifts from raising questions to proving a world exists. That follows Woollen
rather than Lieu: one cue whole, long holds, **no voice-over**, mood over plot.
Practically it also suits the pipeline, since long takes are what H3 renders
most cheaply.

If you wanted the louder action register instead, it is one parameter:
`cut_points(..., stretch=1.0)` restores the measured corpus arc and roughly
triples the shot count.

## 3. Nothing was spent

No paid API was called at any point. Beat selection is mechanical arithmetic
over `screenplay.json`, and every render is local GPU. The $0 was a
constraint I set myself given the standing spend rule and you being asleep —
not a limit of the design. An LLM pass over beat selection would likely
improve shot choice and would cost cents; I did not make that call for you.

## 4. Coverage, not shots

Each beat renders as one 243-frame (10.1s) take, and the edit cuts 2–4 shots
out of it. A second angle inside one H3 generation measured free, and 243
frames is the cheapest unit per usable second. This also means a beat reused
as a rhythm motif shows a different moment of its take each time.

## 5. 1344x768, not 1920x1080

That is H3's native canvas *and* its hard pixel cap — anything larger is
silently area-scaled back. Upscaling to 2K is a separate SeedVR2 pass that I
have not run.

## 6. Clip length: 11 beats per trailer

Enough to cover 33–42 shots with deliberate motif repetition, and it fits the
overnight GPU budget (~17 min per clip, ~3 h per trailer). More beats would
mean less repetition and more variety; fewer would lean harder on the motif.

## Known gaps, honestly

- **The clips run dark.** The probe was beautiful but low-key. A grade pass
  matching every clip to one hero clip is the documented fix (the prompt does
  not lock exposure — measured luma across the old clips spanned 42.9–96.6 of
  255). Not yet done.
- **No dialogue.** The literary register bans voice-over, and Qwen3-TTS
  discards `instruct` on its cloning path, so the screenplay's `emotion` field
  has nothing to bind to there. IndexTTS-2 is the engine with real per-line
  emotion and is already installed. A character-dialogue trailer is the
  obvious second variant.
- **Sherlock's `screenplay.json` is stale** — the split re-draft produced 30+
  scenes but the render never re-ran, so the trailer draws on 22.
- **No SeedVR2 upscale, no title typography beyond a plain centred card.**
  `libass` would give real tracking and fades in one filter; the font must be
  asserted to exist first, because libass substitutes a missing one silently.
