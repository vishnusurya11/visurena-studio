"""The over-push measurer as a verdict row of the take gate.

MEASURED on episode 10 (2026-09-16): seven of thirty takes ended one or two
sizes tighter than the plan -- T05 twice ran "a hand's breadth" to an
eyes-and-nose frame -- and every existing gate passed them, because off-board,
last-vs-cell and drift judge resemblance and none judges scale. The measurer
(studio.take_zoom) separates the reviewer's groups on the subject region:
over-pushed >= 1.63, fine <= 1.50, wall 1.55. This is its seat in the row.
"""
import sys

sys.path.insert(0, "scripts/episode")

from studio import take_zoom as tz

HAND = "The camera pushes in on Brigham Young's face across the whole shot, travelling a hand's breadth; his eyes come up."
FOREARM = "The camera pushes in on Brigham Young across the whole shot, travelling a forearm; he shifts the volume."


def test_a_hand_push_that_ran_to_nostrils_costs_points_but_is_not_hard():
    # MEASURED ep10 re-read: T05's nostrils (1.93x) and T13's whole face leaning
    # into the lens (2.16x, the reviewer's KEEP) read the same to a scale
    # measure. Scale separates pushed from not pushed, not usable from not, so
    # the row is a scored advisory until a face-in-frame read exists.
    g = tz.row({"ratio": 1.93, "measured": True, "monotonic": True}, HAND)
    assert g.name == "zoom" and not g.ok and not g.hard
    assert "1.93x" in g.note and g.penalty == tz.ZOOM_PENALTY


def test_a_hand_push_that_stayed_a_hand_is_clean():
    g = tz.row({"ratio": 1.28, "measured": True, "monotonic": True}, HAND)
    assert g.ok and not g.hard and g.penalty == 0


def test_a_forearm_may_travel_further_than_a_hand():
    assert tz.row({"ratio": 1.90, "measured": True, "monotonic": True}, FOREARM).ok
    far = tz.row({"ratio": 2.40, "measured": True, "monotonic": True}, FOREARM)
    assert not far.ok and not far.hard and far.penalty == tz.ZOOM_PENALTY


def test_an_unmeasured_zoom_is_quiet_like_identity():
    g = tz.row({}, HAND)
    assert g.ok and not g.hard and g.note == "not measured" and g.penalty == 0


def test_the_planned_motion_is_the_first_shot_of_the_take():
    import take_dq

    class Shot:
        def __init__(self, motion):
            self.motion = motion

    class Episode:
        def shot(self, i):
            return {18: Shot("eighteen"), 19: Shot("nineteen")}[i]

    assert take_dq.planned_motion(Episode(), {"shots": [18, 19], "index": 18}) == "eighteen"
    assert take_dq.planned_motion(Episode(), {"index": 19}) == "nineteen"
    assert take_dq.planned_motion(Episode(), {"index": 40}) == ""


def test_the_zoom_reads_only_the_head_of_a_two_shot_take():
    assert tz.head_frame([["Q18_0.png", 0], ["Q19_0.png", 85]]) == 85
    assert tz.head_frame([["Q18_0.png", 0]]) is None
    assert tz.head_frame([]) is None


def test_a_reversal_on_a_near_still_take_is_noise_not_an_advisory():
    # ep10 re-read: T04 1.11x, T05 0.99x, T06 1.14x each lost ten points for
    # "reversed mid-take" -- a sign flip inside the measurer's own noise band.
    assert tz.row({"ratio": 1.05, "measured": True, "monotonic": False}, HAND).ok
    g = tz.row({"ratio": 1.45, "measured": True, "monotonic": False}, HAND)
    assert not g.ok and not g.hard
