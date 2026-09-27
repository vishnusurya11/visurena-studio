"""One step's overrun is not charged to the next step; the ceiling still binds.

ep13, 2026-09-27: step 08 ran 4634 s of a 3600 s share, the 1034 s overrun was
carried into step 09, and the takes (7176 s of a 7500 s share) were refused
twice -- AFTER step 08 had signed -- with hours of the ceiling still unspent.
And a panel rung priced at one grid (102 s) measured ~1900 s: a rebuild with
the content read plus the eye's read of every panel.
"""
from studio import panel_ladder
from studio.run_budget import Budget


def test_an_overrun_is_not_taken_from_the_next_steps_share():
    t = [0.0]
    b = Budget(10000, {"a": 0.1, "b": 0.5}, clock=lambda: t[0])
    b.start("a")
    t[0] = 2000.0                      # 1000 s over a's 1000 s share
    b.start("b")
    assert b.remaining("b") == 5000.0


def test_unused_time_still_rolls_forward():
    t = [0.0]
    b = Budget(10000, {"a": 0.1, "b": 0.5}, clock=lambda: t[0])
    b.start("a")
    t[0] = 400.0
    b.start("b")
    assert b.remaining("b") == 5600.0


def test_the_ceiling_still_binds_last():
    t = [0.0]
    b = Budget(10000, {"a": 0.1, "b": 0.5}, clock=lambda: t[0])
    b.start("a")
    t[0] = 8000.0
    b.start("b")
    assert b.remaining("b") == 2000.0


def test_a_panel_rung_is_priced_at_what_it_measured():
    assert panel_ladder.RUNG_SECONDS >= 1800.0
