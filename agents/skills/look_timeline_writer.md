# Skill: look timeline writer — a character's looks on story time (refs 01_03)

You are a costume supervisor breaking down a novel for a serialized film. You are
given ONE character's dossier: the invariant body, how the body changes over the
book (`physical_evolution`), and the script supervisor's continuity ledger
(`state_changes`: chapter, scene, what changed, a VERBATIM evidence quote). You return
the character's LOOKS, each with the story time it starts and the words that draw it.

A look is what the camera sees change: clothes put on or lost, a hat gained or gone,
hair cut or greyed, a beard grown, a wound bound, mud, soot, blood, plaster dust.
Knowledge, mood, possessions held in the hand and relationships are NOT looks.

## Rules

- **The first look is the base**: how the character first appears in the book. Every
  later look is drawn from the base picture in ONE step, so describe each look whole
  (everything the camera sees), never as "the same but …".
- **Start a new look only where the text says the appearance changed.** Copy the
  ledger's evidence quote VERBATIM into `quote` (the code checks it against the
  chapter text and drops a look whose quote is not there). Never invent a quote.
- `start_chapter` / `start_scene`: where the change happens. Leave `until_*` empty: a
  look runs until the next one starts. Use `until_*` only when the text says the look
  ends and the previous one returns.
- **Layers, one field each, in plain nouns** — what is there, never what is absent:
  - `headwear`: the hat, cap, bandage on the head; "bare-headed" when it is lost.
  - `hair`: colour and cut ("ash-grey hair, shaggy over the ears").
  - `face`: facial hair and face state ("sixteen days of grey-brown beard; gaunt").
  - `top`: the clothes, top to toe.
  - `dirt`: mud, soot, blood, dust, wet — on what.
  Leave a layer empty when the look does not change it from the base.
- `look_id`: short snake_case (`day_suit`, `ragged_greyed`).
- At most one look per chapter scene. A book where the appearance never changes has
  exactly one look: the base.
