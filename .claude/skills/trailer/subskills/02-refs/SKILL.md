---
name: trailer-refs
description: Reference sheets that bind identity - and the collision problem when a book never describes anyone.
---

# Reference sheets

`studio/trailer_refs.py`, `scripts/trailer/build_refs.py`. They belong to the
BOOK (`library/<book>/refs/`), shared by trailer, song and episode: a character
who looks one way in the trailer and another in episode one is two characters
to the audience.

## Binding is the whole point

Every shot showing a character carries that character's reference on
`ref_image_1`; the location rides `ref_image_2`. `ShotSpec.unbound_cast()` asks
what the JOB will carry, never what the prompt says, and a plan with any
unbound shot is refused.

The 2026-08-25 trailer generated twelve good reference sheets and then rendered
every keyframe text-to-image with no image input at all. Nothing ever told the
model Holmes existed.

**Never put an audio reference in a shot where the face matters** — identity
similarity collapses 0.886 → 0.088 and no amount of steps or reference sizing
recovers it.

## Choose refs by story-wide ranking

Not by sampling scenes. Sampling gave *Jekyll and Hyde* a reference set with
**no Henry Jekyll** — he ranks second in the book but did not speak in the
twelve scenes drawn — while spending a sheet on Enfield, who ranks sixth.

## Character collision

The failure mode when a book never describes anyone: seven Jekyll sheets came
back as seven near-identical Victorian gentlemen. Different seeds do not fix
it, because the prompts were identical — Stevenson describes none of them, so
every character got the same generic prompt.

Three layers, in decreasing order of authority:

1. **The book's own epithets.** "the solemn butler", "the lawyer", "a little
   man", "a maid servant" — an epithet is the author describing someone in the
   fewest words they thought necessary. `epithets()` keeps aliases opening with
   an article, drops ones naming a relationship ("our old friend" describes no
   one), and drops only an alias IDENTICAL to the name.
2. **Period dress implied by role** (`costume_for`). Says nothing about hair,
   age or face, so it can sit beside a real description without contradicting
   it. A role is not an image; naming the CLOTHES translates.
3. **Invented distinguishing marks**, ONLY where the book is silent. Appending
   them to a real description contradicts it — Hyde is "a small young man" and
   was handed "a short greying beard".

Put the SUBJECT FIRST in the prompt, before the style block. With the style
leading, the palette dominates and the description barely registers.

**Honest limit:** this separates servants and uniformed characters clearly. It
does NOT separate three well-dressed gentlemen — Krea 2's period prior beats
the text. The real fix is a trained character LoRA (musubi-tuner supports
Krea 2 natively); it is the only method whose fidelity does not decay with
shot count.

## The sheet is read back, and judged twice

Every sheet goes to the local VLM (`studio/describe.py`) and comes back as a
trait card. Two questions, in this order:

1. **Did the render obey its card?** Only on the traits the channel actually
   expresses - hair colour, hair length, facial hair, headgear
   (`distinguish.RELIABLE`). Complexion, build and age are DEAD on this
   channel: run 4's seven sheets read "fair" and "average" against seven
   different card phrases, and age follows the hair colour. A disobedient
   render (Lestrade, run 6: card said walrus moustache, render read
   clean-shaven) is NOT a collision; it goes again as written on a new seed,
   because rewriting the card would move the character off the book for a
   fault of the renderer.
2. **Does it read as someone already bound?** Fewer than `DISTINCT_AT` seen
   traits apart is a collision, and `distinguish` moves exactly the shared
   slots to phrases no other character holds. A hair phrase carries a colour
   AND a length, so both can move it. When the moved slot is one the book's
   own sentence asserts, that sentence is dropped from the prompt - "a full
   beard ... A thin man with a heavy walrus moustache" tells the model two
   things and it obeys whichever it likes.

Vocabulary aliasing is not a difference: a deerstalker reads as "cap", a
tall beaver hat as "top hat" (`describe.NEIGHBOURS`, half a difference).

### A read that outlives its timeout, and an engine that ignores the interrupt

A read past `describe.TIMEOUT` (600 s) is interrupted, logged
`accepted_on_timeout`, and the sheet binds unseen (`patiently`). That was
bounded for one read and unbounded for a round. Run 18: a Qwen3-VL read on
a VRAM-full engine (H3 still staged from a killed run, the VLM offloaded to
CPU) ignored the interrupt and stayed at the head of the queue; the NEXT read
sat `comfy.QUEUE_SECONDS` (7200 s) in line behind it before its own 600 s -
the learnings are 130 min apart, five times: 11 h in step 02, budget -590 min
at step 03. The interrupt is now verified (`comfy.stuck`: still running
`STUCK_SECONDS` 30 after it) and one `describe.Patience` per round remembers
the verdict - stuck, every later read of the round returns unseen at once,
logged `accepted_on_timeout` / "engine stuck: read skipped". Cost of a stuck
engine: 630 s once per round (step 02's cast, each step 07 round), not
130 min per read. The engine itself still needs a restart; the run does not
attempt one.

## The book's own portrait comes first

`analysis/profile.physical` says "limited physical description" for Holmes,
Gregson and Lestrade, so run 6 INVENTED them: a white-haired, bearded Holmes
at forty. Doyle wrote the portraits; the analysis lost them. `studio/portrait.py`
reads them back from `source/chapters/`: a candidate paragraph carries a look
word (`LOOK`) and names the character, or sits beside one that does, within
`SPAN` (3) chapters of the first appearance, at most `CAP` (12); the reasoning
model quotes VERBATIM sentences and fills six slots (age, hair, facial hair,
headgear, build, complexion) only from those sentences; `verify` refuses any
sentence not in the book, once with the violation quoted back, then the
portrait is silent. Silence falls through to the dossier. Cached in
`refs/portraits.json`.

In the chapter of first appearance everything before the first naming is a
candidate too: Ferrier is "the traveller", gaunt and haggard, for fifty
paragraphs before a rescuer asks his name. Doyle describes, then names.

Three rules the extraction taught (Scarlet, 2026-09-04):

- An alias BY RELATION ("my companion", "his daughter") names whoever the
  speaker is with, not the character: Watson's portrait came back as Holmes's
  six feet and hawk nose. `RELATIONAL` aliases are not names.
- The analysis lists "Dr. Watson" and never "Watson"; Stamford says "Watson,
  you are as thin as a lath". A capitalised surname is a name.
- What the book states outranks the rotation (`portrait.stated` →
  `card_for(stated=)`): "flaxen-haired" in the quoted sentence beside "dark
  hair swept back" from the pool tells the model two things. A phrase the
  vocabulary reads whole is the slot as written ("long chestnut hair"); one
  read in part snaps onto the pool phrase that reads the same and shares the
  most words ("flaxen-haired" → "receding sandy hair", "about forty-three" →
  "about forty"); one it cannot read states nothing ("frightened face"),
  because the fidelity gate reads every slot. A list ("fair face; cheek more
  ruddy; pale-faced") states its first readable phrase; a comma is the
  book's, not a list. A phrase over `WORDS` (6) snaps onto the pool: a card
  is a list of short attributes. Build has no reading and is kept as written. `describe.nearest` matches at word starts only:
  "flaxen-haired" had read as RED.

## Filter the description before it reaches a shot

`analysis/profile.physical` is a BIOGRAPHY, not a look. "Served with the
Berkshires in Afghanistan, was wounded by a Jezail bullet at Maiwand" is true,
sourced and unphotographable. Worse, several profiles state the ABSENCE of a
description, which hands the model the vocabulary of a face while saying
nothing. `visual_description()` keeps only sentences naming a body.

`is_scene_safe()` refuses any description carrying reference-sheet language
("full-body character reference", "mid-grey backdrop") — that reached the video
model once and asked it to animate a photographer's backdrop.
