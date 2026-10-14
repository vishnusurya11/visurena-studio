"""ep26 (2026-10-09 12:20Z): four of five panel refusals were the reader's --
'the dark dome of St Paul's sits small on the skyline' (the capital after 'St'
taken for a person) asked the standing narrator on Primrose Hill to sit, and
'their black shadows lying across the gravel road' (a participle counts whatever
precedes it) asked him to lie at his gate.  A saint's name is a place, and light,
shadow, ground and buildings never take a posture.  A person still does."""
from __future__ import annotations

from types import SimpleNamespace

from studio import panel_content as pc


def asked(frame: str, at_rest: str = "") -> str | None:
    return pc.asked_posture(pc.stage_text(SimpleNamespace(frame=frame, at_rest=at_rest), None))


def test_a_saints_dome_does_not_sit():
    assert asked("Medium on the narrator standing on the hill. Behind him at the LEFT third the dark "
                 "dome of St Paul's sits small on the skyline, and the city smokes.") is None


def test_shadows_that_lie_across_a_road_are_not_a_posture():
    assert asked("Wide on the narrator at his gate under the tall beech trees at the LEFT edge, their "
                 "black shadows lying across the gravel road.") is None


def test_a_person_still_sits_and_lies():
    assert asked("Close on the narrator sitting up in the brass bed against the pillow.") == "sitting"
    assert asked("Wide on the yard, the landlord lying at the fence.") == "lying"


def test_a_pool_of_gaslight_lying_on_the_flagstones_is_not_a_posture():
    """Jekyll ep01 shot 3 (2026-10-14): 'a yellow pool of gaslight lying on them' asked the
    walking little man to lie down, on the panel and again on the take -- `light` matched
    as a whole word only, never inside 'gaslight', and a pool is ground, not a person."""
    assert asked("Wide of the lamplit crossroads as the little man stumps along the far pavement",
                 "THE FOCUS OF THE PICTURE IS the frosted flagstones at the BOTTOM third, a yellow pool "
                 "of gaslight lying on them. The little man walks at a walking pace.") is None
    assert asked("Wide of the yard, the firelight lying across the boards.") is None
