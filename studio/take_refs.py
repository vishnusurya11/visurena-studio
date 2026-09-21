"""Where a storyboard panel sits among a take's reference pictures, and what
the prompt is allowed to say about it.

OWNER 2026-09-20, asking what had happened to the audio inputs. The question
found two things I had not thought through, and a third turned up while wiring
them.

THE AUDIO. ref2va drives LIPS off a voice wav and needs a face to drive. Only
four of ep05's 28 takes carry a voice -- T06, T07, T13, T27 -- and the other 24
carry silence, because the narrator's 21 lines are narration laid over the cut
rather than spoken on camera. A panel's face on an over-the-shoulder is a worse
thing to drive a mouth from than a clean character sheet.

THE FREEZE. `episode_ref_official` already carries the measurement: a composed
still staged as "fully_preserved - subject placement, wardrobe and light" froze
ep03 T02, back at similarity 1.000 to its cell with 0.12 frame-to-frame change,
the still reproduced instead of animated. Same fault as a last-frame pin, same
shape as the composed frame zero the owner rejected in August.

THE NUMBERING. `picture_numbers` assigns <Picture N> in the graph's staging
order, so a panel placed anywhere but last renumbers every other picture and
the prompt cites the sheets by the wrong slot.
"""
from __future__ import annotations


def speaks(card: dict) -> bool:
    """Does this take carry a voice, or silence?

    `takes_r2v.card` already records it: a list of (wav, offset) pairs when
    somebody speaks on camera, and the string "silence" when nobody does."""
    audio = (card or {}).get("audio")
    return bool(audio) and audio != "silence"


def with_panel(refs: list, panel, speaking: bool = False) -> list:
    """The reference list with the storyboard panel appended -- ALWAYS LAST.

    It led on silent takes for one draft, which was my invention rather than a
    measurement, and it cannot work: a panel in front renumbers every other
    picture and the prompt then cites each sheet by the wrong slot. L11 exists
    to catch exactly that.

    Last is also the safer place for the four takes that speak, since the
    character sheet keeps the front where the mouth is driven from. `speaking`
    stays in the signature because the caller knows it and a later A/B may want
    it."""
    if panel is None:
        return list(refs)
    return [r for r in refs if r != panel] + [panel]


def panel_definition(slot: int) -> str:
    """What the storyboard panel IS, for the prompt's subject_definitions.

    Every staged reference must be defined or the L11 PICTURES lint refuses the
    take -- "citing a picture the graph no longer stages is what L11 exists to
    catch". Staging one without defining it is the same fault reversed."""
    return (f"<Picture {slot}> is the storyboard frame drawn for this shot: the place, the people "
            f"in it and the clothes they wear, at this hour of the day, in the house art style.")


def panel_retention(slot: int) -> str:
    """How much of the panel survives into the take -- and it is not the framing.

    A weak_reference, which is this pipeline's OWN word for a picture that
    informs without pinning: "the take's storyboard strip is a weak_reference
    that carries shot order alone". I invented `partially_preserved` for the
    same job first and the lint said so.

    SAID POSITIVELY, because MiniMax cannot read a negation -- the builder
    refuses the take over one, and a fence built out of the word you are
    avoiding is a summons. So instead of saying the framing is not copied, the
    line says where the framing comes FROM."""
    return (f"<Picture {slot}> (the storyboard frame): weak_reference - it shows the location, "
            f"the people and the clothes they wear. The framing, the camera position and the "
            f"movement come from the camera sentence below, which owns the viewpoint.")
