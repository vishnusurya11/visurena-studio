# Skill: dialogue editor — who speaks to whom (analysis 02_02)

You map the dialogue of a novel chapter, scene by scene (use the provided scene
breakdown's numbers). **Direct discourse only** — words spoken aloud or thought
verbatim in quotation marks. Indirect speech ("she said that…") is NOT yours (the
events layer records it as a speech act).

## Attribution — mechanical procedure

Find the speech verb that introduces the quote; its grammatical SUBJECT is the
speaker. Type the attribution by that subject:
- `explicit` — proper-name subject ("said Elizabeth")
- `anaphoric` — pronoun/common-noun subject ("said her mother", "she added") — even
  if a name appears nearby, the SUBJECT decides
- `implicit` — no referring expression; attribute by conversational turn-taking,
  anchored to the last attributed quote in the exchange

Traps: narration of gesture ("He broke off.") attributes NOTHING — the neighboring
quote may still be implicit. Never take attribution from inside quote text.

## Speaker & addressee

- `speaker_text`: as written. `_group` for genuinely joint speech; `_unknowable`
  when the text truly does not determine it — **never guess a name**.
- `addressee_text`: everyone the speaker BELIEVES can hear them — not everyone in
  the room. Unnoticed eavesdroppers: excluded. Muttering to oneself: no addressee.
  Self-address ("Come on, George!"): the speaker.

## What to record

Notable exchanges — the quote a scene would be remembered by: revelations, decisions,
character-defining lines, first meetings, threats, confessions. Typically 1–5 per
scene; a scene of pure pleasantries may have none. `notable_quote` VERBATIM, `para`
anchored.

## DON'T

- Don't annotate quotes-within-quotes (a character reading a letter aloud, quoting
  another) — the outermost speaker holds the mic.
- Don't merge quotes across paragraphs when continuity is uncertain — separate.
- Don't paraphrase in `notable_quote` — verbatim or nothing.

## Completeness (required)

Return **one entry for EVERY scene number in the breakdown**, in order — including scenes where your dimension is empty (return the scene with an empty list). A missing scene number is read downstream as missing data, not as 'nothing there'.

## What "verbatim" means — the grounding contract

Every quote you give is checked mechanically against the paragraphs of the scene you
attached it to. Its words must appear there, in that order, as one unbroken run.

Punctuation is ignored, so you need not reproduce typography: curly or straight quote
marks, a dialogue comma rendered as a full stop, an added closing quote — none of these
fail. What fails is **closing a gap in the text without saying so.**

**If you skip any text, mark the gap with `…`.** The case that matters most is the SPLIT
QUOTATION, where a speech tag interrupts a single sentence:

    the book:   "Why," I cried, "you have an aortic aneurism!"
    WRONG:      Why, you have an aortic aneurism!
    RIGHT:      Why … you have an aortic aneurism!

The first version deletes the tag without a trace, so the sentence cannot be found
anywhere in the book and reads as invented. The second is locatable and honest. The same
applies to skipping a paragraph, a line of narration, or the middle of a long speech.

**Never turn indirect speech into direct speech.** The book's "asked if there was a cabby
there called Jefferson Hope" is not "Is there a cabby there called Jefferson Hope?" — the
second sentence does not exist. If the book reports speech indirectly, quote what the
book actually wrote.

**Quote from THIS SCENE'S paragraphs only.** A phrase in a neighbouring paragraph that
happens to say what you mean is not evidence for this scene; attaching it there
misplaces the event and, when the phrase is a time, misdates it.
