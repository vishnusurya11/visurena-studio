"""The drift gate scores the segments that HAVE a target, not all of them.

`drift_gate`'s own calibration says it hard-fails "only where an END cell was
drawn (there is a target); a hold without one is advisory, because a static
camera the cab crosses legitimately ends at 0.25-0.29 against its start cell."

The implementation took `min(end_sim)` over EVERY segment and then checked
`has_end` globally, so a take holding one END'd segment and one ordinary one was
judged on the ordinary one's score -- exactly the 0.25-0.29 the comment calls
legitimate.  Measured on episode 2: takes T00, T05 and T19 were hard-failed on
segments with no target at all, while their real END'd segments told a different
story.
"""
from studio.take_verdict import DRIFT_HARD, SegmentReport, drift_gate


def seg(cell: str, target: str, end_sim: float) -> SegmentReport:
    return SegmentReport(cell=cell, target=target, start_s=0.0, end_s=4.0, lead_in_s=0.0,
                         still_share=0.0, kind="narration", start_sim=0.9, end_sim=end_sim,
                         landed=True, offset=0)


def test_a_take_with_no_drawn_end_is_never_hard():
    """Every segment ends on its own start cell: there is no target to reach."""
    gate = drift_gate([seg("Q08_0.png", "Q08_0.png", 0.08),
                       seg("Q09_0.png", "Q09_0.png", -0.09)])
    assert gate.hard is False


def test_a_drawn_end_that_is_reached_passes():
    gate = drift_gate([seg("Q20_0.png", "Q20_0E.png", 0.89)])
    assert gate.hard is False


def test_a_drawn_end_that_is_missed_is_hard():
    gate = drift_gate([seg("Q03_0.png", "Q03_0E.png", -0.16)])
    assert gate.hard is True


def test_a_low_segment_with_no_target_does_not_condemn_a_reached_end():
    """THE BUG.  Q04_1 reaches its END at 0.68; Q04_0 has no target and sits at
    0.48, which the calibration calls legitimate.  The take is not a drift fault."""
    gate = drift_gate([seg("Q04_0.png", "Q04_0.png", 0.48),
                       seg("Q04_1.png", "Q04_1E.png", 0.68)])
    assert gate.hard is False


def test_the_worst_TARGETED_segment_is_the_one_scored():
    """Two drawn ENDs, one reached and one missed: the missed one decides."""
    gate = drift_gate([seg("Q19_0.png", "Q19_0E.png", 0.58),
                       seg("Q19_1.png", "Q19_1E.png", 0.20)])
    assert gate.hard is True
    assert gate.value == 0.2


def test_the_reported_value_ignores_untargeted_segments():
    gate = drift_gate([seg("Q00_0.png", "Q00_0E.png", 0.46),
                       seg("Q00_1.png", "Q00_1.png", 0.14)])
    assert gate.value == 0.46


def test_the_boundary_is_the_documented_one():
    assert drift_gate([seg("a.png", "aE.png", DRIFT_HARD - 0.01)]).hard is True
    assert drift_gate([seg("a.png", "aE.png", DRIFT_HARD)]).hard is False


def test_no_segments_at_all_is_not_a_fault():
    assert drift_gate([]).hard is False
