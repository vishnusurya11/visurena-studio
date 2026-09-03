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

## Filter the description before it reaches a shot

`analysis/profile.physical` is a BIOGRAPHY, not a look. "Served with the
Berkshires in Afghanistan, was wounded by a Jezail bullet at Maiwand" is true,
sourced and unphotographable. Worse, several profiles state the ABSENCE of a
description, which hands the model the vocabulary of a face while saying
nothing. `visual_description()` keeps only sentences naming a body.

`is_scene_safe()` refuses any description carrying reference-sheet language
("full-body character reference", "mid-grey backdrop") — that reached the video
model once and asked it to animate a photographer's backdrop.
