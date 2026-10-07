"""ep19 T19 (2026-10-07): a medium-close of the curate at the slit, the pit
behind him, read 'cliff' -- the frame names no pit, the SETUP does.  The
content checks hand `faults` the shot's prose AND the staged place's, so the
pit-wall exemption holds for every shot staged in the pit; a cliff on a lane
is still banned."""
from __future__ import annotations

from types import SimpleNamespace

from studio import panel_content as pc


def _seen():
    return pc.Seen(landform="cliffs", subjects=["a sand cliff", "a man at a slit"], hour="day")


def test_stage_text_carries_the_setups_prose():
    shot = SimpleNamespace(frame="Medium-close view of the curate at the slit", at_rest="his eye to the opening")
    setup = SimpleNamespace(described="Yellow clay banks around the excavation of the pit.")
    assert "excavation" in pc.stage_text(shot, setup) and "curate" in pc.stage_text(shot, setup)


def test_a_cliff_behind_a_shot_staged_in_the_pit_is_not_banned():
    shot = SimpleNamespace(frame="Medium-close view of the curate at the slit", at_rest="")
    setup = SimpleNamespace(described="Banks of clay around the excavation of the pit.")
    got = pc.faults(_seen(), frame=pc.stage_text(shot, setup), planned=1, crowd=False, flat=False,
                    night=False, banned=("cliff",), size="medium_close", extras=0)
    assert not any("banned" in f for f in got)


def test_a_cliff_on_a_lane_is_still_banned():
    shot = SimpleNamespace(frame="Wide of the lane", at_rest="")
    setup = SimpleNamespace(described="A hedged lane under elms.")
    got = pc.faults(_seen(), frame=pc.stage_text(shot, setup), planned=1, crowd=False, flat=False,
                    night=False, banned=("cliff",), size="wide", extras=0)
    assert any("banned from this book: cliff" in f for f in got)
