"""A gate's printed number must be the one it ruled on, or say what else it used.

`drift_gate` reports `end_sim` -- the worst of the segments that HAVE a target --
and decides `ok` on `every`, the worst of ALL segments. Both scopes are
deliberate and documented: a segment aimed at nothing cannot miss, so the HARD
verdict and the penalty belong to the aimed ones; and "a hold that has wandered
is worth printing even when nothing was aimed at", so the advisory watches
everything.

What was missing is that the reader is shown only one of the two. A take could
print `drift 0.95` and carry `adv`, because an unaimed segment elsewhere read
0.29 -- and an unaimed segment legitimately reads 0.25-0.29 against its own
start cell, as the calibration says. The number on the line then explains
nothing, which is the same fault as a gate measuring the wrong thing, one step
later.

It is latent today rather than live: episodes 4 and 5 run one shot per take, so
there is exactly one segment and the two quantities coincide. It bit on the
multi-segment takes of episodes 1 to 3, and it will bite again the moment a take
holds two shots.

So the row now names the second number when it differs.
"""
from studio.take_verdict import DRIFT_ADVISORY, DRIFT_HARD, SegmentReport, drift_gate


def seg(cell: str, target: str, end_sim: float) -> SegmentReport:
    return SegmentReport(cell, target, 0.0, 1.0, 0.0, 0.0, "hold", 1.0, end_sim, True, 0)


def test_one_aimed_segment_reports_its_own_number():
    row = drift_gate([seg("Q00_0.png", "Q00_0E.png", 0.91)])
    assert row.value == 0.91 and row.note == "0.91"


def test_an_unaimed_hold_that_wandered_is_still_printed():
    """The advisory's wider scope is the point; it is not silently dropped."""
    row = drift_gate([seg("Q00_0.png", "Q00_0.png", 0.29)])
    assert row.ok is False


def test_the_row_names_the_worst_hold_when_it_is_not_the_judged_number():
    rows = [seg("Q00_0.png", "Q00_0E.png", 0.95),      # aimed, arrived
            seg("Q01_0.png", "Q01_0.png", 0.29)]       # unaimed, wandered
    row = drift_gate(rows)
    assert row.value == 0.95
    assert "0.95" in row.note and "0.29" in row.note
    assert row.ok is False


def test_the_hard_verdict_still_belongs_to_the_aimed_segment():
    """Episode 2 lost T00, T05 and T19 to segments that had no target at all."""
    rows = [seg("Q00_0.png", "Q00_0E.png", 0.95),
            seg("Q01_0.png", "Q01_0.png", 0.10)]
    assert drift_gate(rows).hard is False


def test_an_aimed_segment_that_missed_is_still_hard():
    rows = [seg("Q00_0.png", "Q00_0E.png", DRIFT_HARD - 0.01)]
    assert drift_gate(rows).hard is True


def test_a_clean_take_says_one_number():
    """The second number is named only when it is the REASON for the verdict.
    On a clean row it is noise."""
    rows = [seg("Q00_0.png", "Q00_0E.png", 0.95),
            seg("Q01_0.png", "Q01_0.png", 0.90)]
    row = drift_gate(rows)
    assert row.ok is True and row.note == "0.95"


def test_an_aimed_miss_does_not_blame_a_hold():
    """When the aimed segment is itself under the wall, it is the whole story."""
    rows = [seg("Q00_0.png", "Q00_0E.png", 0.40),
            seg("Q01_0.png", "Q01_0.png", 0.29)]
    assert drift_gate(rows).note == "0.40"


def test_no_segments_at_all_is_not_a_drift_failure():
    row = drift_gate([])
    assert row.ok is True and row.hard is False


def test_the_advisory_wall_is_unchanged():
    assert DRIFT_ADVISORY == 0.75 and DRIFT_HARD == 0.50
