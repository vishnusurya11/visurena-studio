"""On a drawn (cel) look a take is HARD-still only when it also HOLDS (Jekyll HEL ep01, 2026-10-14).

frozen-whole's WALL (0.65 static share) was calibrated on WotW's painted Krea2 takes.
Flat cel shading gives optical flow nothing to read across its fills, so a take that
acts reads static: Jekyll ep01 T14 (Enfield lifts his hand, turns his head and speaks
"It was a man of the name of Hyde") read 76 % static with its longest still run 1.08 s,
and failed HARD three times.  On a drawn look the row is HARD only when the share is
over the wall AND the frame holds still longer than G-DEAD's 2.5 s; a painted or
photoreal book is judged exactly as before.
"""
from __future__ import annotations

from studio import stillness as st


def m(share: float, run: float) -> dict:
    return {"static_share": share, "longest_static_run_s": run}


def test_a_house_take_is_judged_by_its_share_alone():
    assert st.is_still(m(0.76, 1.08), 5.9) is True


def test_a_drawn_take_that_acts_is_not_still():
    assert st.is_still(m(0.76, 1.08), 5.9, drawn=True) is False


def test_a_drawn_take_that_holds_is_still():
    assert st.is_still(m(0.92, 4.33), 6.6, drawn=True) is True
    assert st.is_still(m(0.87, 2.71), 8.0, drawn=True) is True


def test_a_planned_still_stays_exempt():
    assert st.is_still(m(0.92, 4.33), 6.6, exempt=True, drawn=True) is False
