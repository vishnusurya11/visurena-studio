"""ep24 (2026-10-09 00:10Z): five of seven panel refusals read 'posture
standing: the shot asks for lying/sitting' over panels that were right -- the
narrator standing at the roof parapet over London.  The reader was handed the
SETUP's words with the shot's ('Beyond it the London valley lies black'), took
the capital 'London' for a person, and asked every roof shot to lie down.
Shot 14's 'His face sits above it in the TOP third' is a composition, not a man
sitting.  Posture is read from the shot's own words, and a body part is never
the one who sits or lies."""
from __future__ import annotations

from types import SimpleNamespace

from studio import panel_content as pc

ROOF = SimpleNamespace(described="A brick parapet crosses the lower third. Beyond it the London valley "
                                 "lies black to the northern hills.")
STANDING = SimpleNamespace(frame="THE FOCUS OF THE PICTURE IS the narrator at the brick parapet in the LEFT third",
                           at_rest="he stands with one hand on the coping")


def test_the_setup_never_orders_a_posture():
    frame = pc.stage_text(STANDING, ROOF)
    seen = pc.Seen(people=1, posture="standing")
    assert pc.posture_fault(seen, frame, 1) is None


def test_the_setup_still_reaches_the_pit_wall_check():
    pit = SimpleNamespace(described="The pit's terraced sand wall rises behind.")
    assert pc.pits_own_wall("cliff", pc.stage_text(STANDING, pit))


def test_a_face_that_sits_in_the_frame_is_not_a_man_sitting():
    shot = SimpleNamespace(frame="the champagne bottle in the artilleryman's fist at the centre",
                           at_rest="his thumb at the cork. His face sits above it in the TOP third")
    assert pc.asked_posture(pc.stage_text(shot, None)) is None


def test_a_man_who_sits_is_still_asked_to_sit():
    shot = SimpleNamespace(frame="the narrator by the window", at_rest="he sits on the bed with his head bowed")
    assert pc.asked_posture(pc.stage_text(shot, None)) == "sitting"
