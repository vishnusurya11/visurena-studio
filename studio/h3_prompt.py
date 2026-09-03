"""Writing a MiniMax-H3 reference-to-video prompt to its actual specification.

We were sending one flat ~120-word paragraph.  H3's published Ref2VA guide asks
for a six-section document, and one of those sections exists precisely to say
what identity binding needs and had no home in our text:

    subject_definitions   what each reference IS
    summary               one paragraph, task-type prefix in brackets
    retention_analysis    HOW each reference is preserved -- one line per label
    detailed_description  350-500 words, shot by shot, labels inserted
    overall_soundscape    ambience and physical sound
    non_diegetic_music    score the characters cannot hear

`retention_analysis` is the field for "keep this face, change everything else".
Its markers are a closed set: fully_preserved, partially_preserved,
attribute_transfer, weak_reference.  We had been asserting that relationship
implicitly and hoping.

Two label types, and they are not interchangeable: <Subject N> is reusable
visible content -- a person, a style -- and <Picture N> is a concrete frame
anchor.  Both bind POSITIONALLY to the reference slot of the same number, so
reordering the injected images silently repoints every tag in the text.
"""
from __future__ import annotations

RETENTION = ("fully_preserved", "partially_preserved", "attribute_transfer",
             "weak_reference")


def subject_definitions(character: str | None, place: str) -> str:
    """Declare what each reference is, before anything refers to it."""
    lines = []
    if character:
        lines.append(f"<Subject 1>: {character} The person whose identity, face, "
                     f"build and dress the target video must keep.")
        lines.append(f"<Subject 2>: {place} The location whose architecture, "
                     f"materials and light the target video is set in.")
    else:
        lines.append(f"<Subject 1>: {place} The location whose architecture, "
                     f"materials and light the target video is set in.")
    return "\n".join(lines)


def retention_analysis(has_character: bool) -> str:
    """State how each reference survives into the shot.

    The character is fully_preserved -- that IS the binding.  The location is
    only attribute_transfer, which is an honest description of what was
    measured: a bar-interior plate plus a slug name produced an arcade carrying
    the bar's tables and gaslights.  Claiming fully_preserved for a place the
    model blends anyway would be asserting something the output contradicts.
    """
    if has_character:
        return ("<Subject 1>: fully_preserved. The face, build, hair and "
                "clothing are carried into the new scene unchanged; only the "
                "lighting, framing and action differ.\n"
                "<Subject 2>: attribute_transfer. The palette, materials, "
                "period and quality of light are carried over; the exact "
                "architecture may differ.")
    return ("<Subject 1>: attribute_transfer. The palette, materials, period "
            "and quality of light are carried over; the exact architecture "
            "may differ.")
