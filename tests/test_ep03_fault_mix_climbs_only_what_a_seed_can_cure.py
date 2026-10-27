"""Jekyll ep03 retro #6: the EYE_PANELS round-1 mix (lettering, clones, twin, eight framing rows,
posture, place) climbs ONLY for the faults a seed can move.  Measured over every EYE_PANELS
learnings row of the library (consecutive rows, a fault 'cured' when its kind+shot is absent
from the next read): framing 17/198 (8.6%) under redraw_grid_seed and 13/170 (7.6%) under
reprose; posture 0/74 and 3/62; lettering 10/46 and 5/40; clones 4/8 and 9/11; twin 5/8 and 5/5."""
from __future__ import annotations

from studio import panel_ladder
from studio.judges.verdict import Fault, Verdict

MIX = [("lettering", "shot_11"), ("lettering", "shot_17"), ("clones", "shot_19"), ("twin", "shot_19"),
       ("lettering", "shot_21"), ("framing", "shot_22"), ("framing", "shot_20"), ("framing", "shot_19"),
       ("framing", "shot_17"), ("framing", "shot_14"), ("framing", "shot_10"), ("framing", "shot_09"),
       ("framing", "shot_05"), ("posture", "shot_01"), ("place", "shot_04")]


def verdict(rows) -> Verdict:
    return Verdict(judge="panel_eye", version="1", passed=False, confidence=1.0, reads=25,
                   faults=[Fault(kind=k, where=w) for k, w in rows])


def test_only_lettering_clones_and_twin_choose_the_grids():
    got = panel_ladder.cured_by_redraw(verdict(MIX))
    assert {f.kind for f in got} == {"lettering", "clones", "twin"}
    assert panel_ladder.shots_of(got) == [11, 17, 19, 21]


def test_the_terminal_mix_of_framing_posture_and_place_is_not_curable():
    rest = [(k, w) for k, w in MIX if k in ("framing", "posture", "place")]
    assert not panel_ladder.curable(verdict(rest))
