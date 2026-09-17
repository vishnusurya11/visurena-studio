"""The score may not punish a take for moving.

MEASURED over all 23 of episode 3's take records, 2026-09-13: among the SIXTEEN
takes that passed every hard gate, the only non-zero penalty in the whole
episode is `drift`.  So for every take a human actually compares,

    score == 70 + 40 * end_sim

-- a closed-form function of one cosine.  Verified: T01 0.079 -> 73.2,
T14 0.537 -> 91.5, T16 0.648 -> 95.9.

And `end_sim` is not what the name says.  Only 4 of ep03's 37 segments have an
END target; for the other 33 `segments_of` sets `target = cell`, so `end_sim`
compares the LAST frame to the segment's OWN FIRST FRAME.  That is an inverted
motion measure.  A take whose camera moves -- which is the entire point of
rendering it -- loses up to 30 points, and a take that sits still scores 100.

The three takes that scored 100/100 in episode 3 are the three most nearly
frozen takes in it.

`drift_gate` already scopes its HARD verdict to the aimed segments, with the
reason written out beside it ("a segment with none cannot have failed to reach
one, and legitimately reads 0.25-0.29 against its own start cell").  The PENALTY
was never given the same scope.  This is that one line.
"""
from studio.take_verdict import DRIFT_ADVISORY, Gate, SegmentReport, drift_gate, score


def seg(cell: str, target: str, end_sim: float) -> SegmentReport:
    return SegmentReport(cell=cell, target=target, start_s=0.0, end_s=4.0, lead_in_s=0.0,
                         still_share=0.0, kind="hold", start_sim=0.99, end_sim=end_sim,
                         landed=True, offset=0)


def test_a_segment_with_no_target_carries_no_penalty():
    """It was never aimed anywhere, so it cannot have missed."""
    gate = drift_gate([seg("Q12_0.png", "Q12_0.png", 0.17)])
    assert gate.penalty == 0.0


def test_a_moving_take_is_no_longer_punished_for_moving():
    """The exact shape of ep03's T01: end_sim 0.079 against its own first frame,
    every hard gate clean, and it scored 73.2 purely for having moved."""
    gate = drift_gate([seg("Q01_0.png", "Q01_0.png", 0.079)])
    total, passed = score([gate])
    assert (total, passed) == (100.0, True)


def test_a_segment_that_WAS_aimed_is_still_scored():
    """The gate keeps its teeth where it has a target to measure against."""
    gate = drift_gate([seg("Q07_0.png", "Q07_0E.png", 0.10)])
    assert gate.penalty > 0.0 and gate.hard


def test_an_aimed_segment_that_arrives_is_clean():
    gate = drift_gate([seg("Q07_0.png", "Q07_0E.png", 0.95)])
    assert gate.penalty == 0.0 and not gate.hard


def test_the_worst_aimed_segment_sets_the_penalty_not_the_worst_of_all():
    """One aimed segment that arrived, beside an ordinary segment that moved a
    long way: the ordinary one must not drag the score down."""
    gate = drift_gate([seg("Q07_0.png", "Q07_0E.png", 0.90),
                       seg("Q07_1.png", "Q07_1.png", 0.05)])
    assert gate.penalty == 0.0


def test_the_advisory_has_the_same_scope_as_the_penalty():
    """It used to watch every segment -- "a hold that has wandered is worth
    printing" -- and MEASURED over ep05-10 (analyst H) that printed on 125 of
    137 takes with no END target, 0 of 25 with one: 19 false alarms on ep10,
    Spearman -0.03.  An unaimed segment's end_sim is how far it moved, not how
    far it drifted; it is printed as a number and flags nothing."""
    gate = drift_gate([seg("Q12_0.png", "Q12_0.png", 0.17)])
    assert gate.ok and gate.penalty == 0.0 and gate.note == "0.17"


def test_an_unaimed_take_that_holds_still_is_not_rewarded_either():
    """The mirror: with the penalty gone, stillness stops buying points. A frozen
    take and a moving take now score the same on drift, and the frozen-share and
    cut-landing gates are left to tell them apart -- which is their job."""
    moved = drift_gate([seg("Q01_0.png", "Q01_0.png", 0.08)])
    froze = drift_gate([seg("Q13_0.png", "Q13_0.png", 0.99)])
    assert moved.penalty == froze.penalty == 0.0
