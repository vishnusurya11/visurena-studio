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


STRIDE = "The camera pushes in on the two men across the whole shot, travelling one long stride."
PULL = "The camera pulls back from Brigham Young's face across the whole shot, travelling a hand's breadth."
T17 = ("The camera pushes in on the raised hand across the whole shot, travelling a hand's breadth; "
       "the spread fingers close into a fist; the fist drops out of the bottom of the frame.")


def test_a_stride_that_ran_two_sizes_costs_points_and_a_stride_that_did_not_is_quiet():
    """ep10 T12 1.98x (WATCH) sat 0.02 under the old 2.0 stride wall; T33 1.52x (KEEP)."""
    far = tz.row({"ratio": 1.98, "measured": True, "monotonic": True}, STRIDE)
    assert not far.ok and not far.hard and far.penalty == tz.ZOOM_PENALTY
    assert tz.row({"ratio": 1.52, "measured": True, "monotonic": True}, STRIDE).ok


def test_a_pull_back_that_did_not_move_costs_the_advisory_points():
    """ep10 T05, current render: planned pull-back, read 0.99x, scored 100."""
    g = tz.row({"ratio": 0.99, "measured": True, "monotonic": True}, PULL)
    assert not g.ok and not g.hard and g.penalty == tz.ZOOM_ADVISORY_PENALTY and "pull-back" in g.note


def test_a_camera_that_followed_costs_the_advisory_points():
    """ep10 T06: subject 1.14x, whole frame 1.57x -- the camera walked into the doorway."""
    g = tz.row({"ratio": 1.14, "camera": 1.57, "measured": True, "monotonic": True}, STRIDE)
    assert not g.ok and not g.hard and g.penalty == tz.ZOOM_ADVISORY_PENALTY


def test_the_row_judges_the_worst_segment_and_names_it():
    z = {"ratio": 1.2, "measured": True, "monotonic": True,
         "segments": [{"ratio": 1.2, "measured": True, "monotonic": True, "start": 0, "end": 85},
                      {"ratio": 1.93, "measured": True, "monotonic": True, "start": 85, "end": 140}]}
    g = tz.row(z, HAND)
    assert not g.ok and g.penalty == tz.ZOOM_PENALTY and g.note.startswith("s2 1.93x") and g.value == 1.93
    per_shot = tz.row(z, [HAND, STRIDE])                           # each segment against its own shot's plan
    assert not per_shot.ok and per_shot.penalty == tz.ZOOM_PENALTY and "s2" in per_shot.note
    quiet = tz.row({"ratio": 1.2, "measured": True, "monotonic": True, "segments": [z["segments"][0]]}, HAND)
    assert quiet.ok and quiet.note == "1.20x hand"


def test_an_exit_segment_read_to_its_break_loses_nothing_for_the_exit():
    """ep10 T17: 1.73x on the full read (15 points), 1.47x to the break where
    the fist left the boards.  The near-wall band is not applied to an exit
    segment: the approach that precedes a planned exit is the planned action,
    and the read inside it is the subject's, not the camera's."""
    z = {"ratio": 1.467, "full_ratio": 1.727, "exit_at": 89, "measured": True, "monotonic": True}
    g = tz.row(z, T17)
    assert g.ok and g.penalty == 0.0 and "exit" in g.note and "1.47x" in g.note
    over = tz.row(z | {"ratio": 1.60}, T17)
    assert not over.ok and over.penalty == tz.ZOOM_PENALTY           # the wall itself still stands


def test_a_reversal_on_a_near_still_take_is_noise_not_an_advisory():
    # ep10 re-read: T04 1.11x, T05 0.99x, T06 1.14x each lost ten points for
    # "reversed mid-take" -- a sign flip inside the measurer's own noise band.
    assert tz.row({"ratio": 1.05, "measured": True, "monotonic": False}, HAND).ok
    g = tz.row({"ratio": 1.45, "measured": True, "monotonic": False}, HAND)
    assert not g.ok and not g.hard
