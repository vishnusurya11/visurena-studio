"""The panel ladder spends its grid cap on wrong-person panels first (Jekyll ep06 run 33, 2026-10-30).

Four panels failed: 0, 24 and 25 with a wrong person (G-WHO), 19 with lettering.  Two grids may climb, in layout
order, so the round went to shot 0's grid and the lettering grid while 24/25 stayed refs-only and T25 crash-zoomed
out of the room.  A wrong person never feeds a take (G-PEOPLE, owner 2026-10-28), so its grids climb first;
otherwise the layout order holds."""
from studio import panel_ladder as pl
from studio.judges.verdict import Fault

ROWS = [{"setup": "door", "shots": [0], "tag": "a"}, {"setup": "seal", "shots": [17, 18, 19, 20], "tag": "a"},
        {"setup": "step", "shots": [24], "tag": "s24"}, {"setup": "step", "shots": [25], "tag": "s25"}]


def fault(shot: int, note: str) -> Fault:
    return Fault(kind="content", where=f"shot_{shot:02d}", note=note)


def test_wrong_person_grids_come_first_and_keep_their_order():
    faults = [fault(0, "who: a figure fits no cast member"), fault(19, "text or lettering in the picture"),
              fault(24, "who: a figure facing the camera fits none of poole"),
              fault(25, "who: a figure facing the camera fits none of poole")]
    assert [r["shots"] for r in pl.people_first(ROWS, faults)] == [[0], [24], [25], [17, 18, 19, 20]]


def test_without_a_wrong_person_the_layout_order_holds():
    assert pl.people_first(ROWS, [fault(19, "text or lettering in the picture")]) == ROWS
