"""ep19 (2026-10-07): the take ladder's move_type cure wrote "The camera pushes
in toward THE FOCUS OF THE PICTURE IS" into five shots -- `aim_of` took the
first clause of at_rest, whose first six words are the FOCUS tag, not the
subject.  H3 got a broken prompt (T10 froze at 90 %) and the battery then read
'FOCUS' as a rack_focus move (G-STILL x5 on a signed plan).  The aim is the
subject noun phrase after the tag, without its parenthetical."""
from __future__ import annotations

from studio import take_ladder as tl

AT_REST = ("THE FOCUS OF THE PICTURE IS the curate (pale blue eyes, black clerical waistcoat), "
           "his head a quarter of the frame's height at the RIGHT edge; the narrator kneels at his LEFT")


def test_the_aim_is_the_subject_after_the_focus_tag():
    assert tl.aim_of("The camera holds a locked-off frame across the whole shot", AT_REST) == "the curate"


def test_a_subject_without_a_parenthetical_keeps_its_words():
    at_rest = "THE FOCUS OF THE PICTURE IS the digging-machine on the eastern terrace at the CENTER RIGHT; vapour"
    assert tl.aim_of("The camera holds a locked-off frame", at_rest) == "the digging-machine on the eastern terrace"


def test_the_substitute_never_carries_the_tag():
    motion = "The camera holds a locked-off frame across the whole shot; the curate presses his eye to the slit"
    out = tl.substitute("frozen-whole", motion, AT_REST)
    assert "FOCUS" not in out and out.startswith("The camera pushes in toward the curate")
    assert out.endswith("; the curate presses his eye to the slit")
