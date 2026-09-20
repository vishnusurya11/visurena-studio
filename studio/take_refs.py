"""Where a storyboard panel sits among a take's reference pictures.

OWNER 2026-09-20, asking what happened to the audio inputs. It found a risk I
had not thought through: H3 ref2va drives LIPS from a voice wav and needs a
face to drive. Of ep05's 28 takes only four carry a voice -- T06, T07, T13,
T27 -- and the other 24 carry silence, because the narrator's 21 lines are
narration laid over the cut rather than spoken on camera.

So a panel cannot simply replace the references everywhere:

  SILENT TAKE -- the panel LEADS. Nobody's mouth has to move, and the panel
  carries the framing, the place and the people in one picture already checked
  by eye and by `panel_dq`.

  SPEAKING TAKE -- the character sheet keeps the front. T07 is an
  over-the-shoulder and T27 a medium: the panel's face is small and half
  turned, which is a worse thing to drive a mouth from than a clean sheet. The
  panel goes last, informing the take without leading it.

Conservative on purpose. Everything the builder already decided about the
sheets stays decided; this only inserts one picture.
"""
from __future__ import annotations


def speaks(card: dict) -> bool:
    """Does this take carry a voice, or silence?

    `takes_r2v.card` already records it: a list of (wav, offset) pairs when
    somebody speaks on camera, and the string "silence" when nobody does."""
    audio = (card or {}).get("audio")
    return bool(audio) and audio != "silence"


def with_panel(refs: list, panel, speaking: bool) -> list:
    """The reference list with the storyboard panel put where it belongs."""
    if panel is None:
        return list(refs)
    rest = [r for r in refs if r != panel]
    return rest + [panel] if speaking else [panel] + rest


def panel_definition(slot: int) -> str:
    """What the storyboard panel IS, for the prompt's subject_definitions.

    Every staged reference must be defined or the L11 PICTURES lint refuses the
    take -- "citing a picture the graph no longer stages is what L11 exists to
    catch". Adding a picture to the graph without adding its definition is the
    same fault the other way round."""
    return (f"<Picture {slot}> is the storyboard frame drawn for this shot: the place, the people "
            f"in it and the clothes they wear, at this hour of the day, in the house art style.")


def panel_retention(slot: int) -> str:
    """How much of the panel survives into the take -- and it is NOT the framing.

    MEASURED ALREADY, in `episode_ref_official`: a composed still staged as
    "fully_preserved - subject placement, wardrobe and light" froze ep03 T02,
    which came back at similarity 1.000 to its cell with 0.12 frame-to-frame
    change. The still reproduced instead of animating. It is the same fault as
    a last-frame pin (`NO_ENDS`) and the same shape as the composed frame zero
    the owner rejected in August.

    So the panel keeps WHO and WHERE, and hands the framing and the movement
    back to the camera sentence, which owns the viewpoint."""
    return (f"<Picture {slot}> (the storyboard frame): partially_preserved - the location, the "
            f"people and their clothes are kept exactly; the framing, the camera position and "
            f"the movement are NOT copied from it and follow the camera sentence below instead.")
