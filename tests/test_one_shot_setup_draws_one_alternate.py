"""A setup with fewer shots than spare cells gets a DIFFERENT alternate in
every spare cell, never the same alternate repeated.

MEASURED on episode 12's plan (2026-09-17): `mountain_gorge_day` held one shot,
the grid had three spare cells, and `alt_panels` filled them with three copies
of "Reverse angle on the gorge" -- the alternate KIND was indexed by the base
panel's number, and every alternate was of panel 1.  Overlap 1.000 with itself,
six hard TWINS and ALTERNATE findings on a sheet that had not been drawn.  The
grid gate needs every cell filled, so the cells stay filled; the kind follows
the cell.
"""
from studio import episode_seq_board as sq


def seg(shot):
    return {"shot": shot, "sub": 0, "size": "wide", "path": 0.5, "faces": [],
            "frame": "Wide down the gorge on a clear day, the trail between the boulders.",
            "camera": "at the trail's head at a standing man's eye, a 35mm lens",
            "at_rest": "The trail runs from the BOTTOM CENTRE to the cleft.", "motion": "The camera holds.",
            "end_frame": "", "changed": "", "crowd": ""}


def test_one_shot_and_three_spare_cells_gives_three_different_pictures():
    alts = sq.alt_panels([seg(27)], spare=3)
    assert len(alts) == 3 and {a["of"] for a in alts} == {1}
    assert len({a["frame"] for a in alts}) == 3


def test_two_shots_and_three_spare_cells_alternate_over_both_panels():
    alts = sq.alt_panels([seg(26), seg(27)], spare=3)
    assert [a["of"] for a in alts] == [1, 2, 1]
    assert len({a["frame"] for a in alts}) == 3


def test_the_kind_of_alternate_follows_the_cell():
    one, two = sq.alt_panel(seg(1), 1, variant=0), sq.alt_panel(seg(1), 1, variant=1)
    assert one["frame"] != two["frame"] and one["of"] == two["of"] == 1
