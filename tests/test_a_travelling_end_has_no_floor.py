r"""The re-staging floor is a question about a camera that was told to stay.

`END_FLOOR = 0.45` asks: did the drawer keep the camera it was told to keep? It
was a fair question while `end_text` said "from the same camera", and it caught
a real fault -- episode 2's 9 of 13 END cells answered "the shot ends here" by
moving to a different setup.

Episode 7's END panels are now told where the camera FINISHED, and the floor
immediately threw away four correct panels. All seven were drawn, looked at one
by one, and judged by eye:

    Q10_0E  0.757  kept     the lane, camera tracked along, boy further off
    Q21_0E  0.489  kept     Holmes's head up off his chest
    Q22_0E  0.855  kept     the doorway, barely moved -- the weakest of the seven
    Q23_0E  0.380  DROPPED  Holmes and the cabman both bent over the strap
    Q24_0E  0.410  DROPPED  Lestrade nearer, the cuffs held out to camera
    Q11_0E  0.340  DROPPED  the same ladder and window, the curtain blown out
    Q14_0E  0.240  DROPPED  camera pulled back two strides, Watson walked in

Every one of the four is right. Their similarity is low because the framing
changed, and the framing changed because the plan said to change it. Measuring
an END panel against its start asks how far the camera moved; a panel whose
camera was TOLD to move cannot be judged by how far it moved.

So the floor keeps its scope and loses the rest: it applies to a shot whose
camera holds still, where it is still a true question and still the gate that
caught episode 2.

The CEILING is not weakened -- it gets sharper. For a locked-off shot a high
score is what an obeyed END cell looks like, which is why `changed` can overturn
it. For a travelling shot a high score means the drawer ignored the travel, and
nothing overturns that. Q22_0E at 0.855 is exactly that panel, and it is the one
of the seven that a person looking at the sheet would also call barely moved.

Fourth instance this session of a constant calibrated on a world that has since
changed -- after CAMERA_MOVE, FOREIGN_MIN and "from the same camera" itself.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import episode_seq_board as sq

PUSH = ("The camera pushes in on the doorway across the whole shot, travelling two long "
        "strides; the boy's hand comes down off his forelock.")
STILL = "The camera is static across the whole shot; Holmes raises the glass to the light."


def test_a_locked_shot_keeps_its_floor():
    """Episode 2's fault, which this gate was written for and still catches."""
    assert sq.end_pair_verdict(0.072, motion=STILL) == "restaged"
    assert sq.end_pair_verdict(0.380, motion=STILL) == "restaged"


def test_a_travelling_shot_has_no_floor():
    """The four panels the floor threw away, at their measured scores."""
    for score in (0.380, 0.410, 0.340, 0.240):
        assert sq.end_pair_verdict(score, motion=PUSH) == "ok", score


def test_a_travelling_shot_that_barely_moved_is_still_a_copy():
    """Q22_0E at 0.855: told two long strides nearer, drew the same picture."""
    assert sq.end_pair_verdict(0.855, motion=PUSH) == "copy"


def test_changed_cannot_excuse_a_copy_when_the_camera_was_told_to_travel():
    """On a locked camera a high score is what an obeyed END looks like, so one
    block of real difference overturns the ceiling. A travelling camera has no
    such excuse: the travel itself was the instruction."""
    assert sq.end_pair_verdict(0.855, motion=STILL, changed=1) == "ok"
    assert sq.end_pair_verdict(0.855, motion=PUSH, changed=1) == "copy"


def test_the_panels_that_were_kept_stay_kept():
    for score in (0.757, 0.489):
        assert sq.end_pair_verdict(score, motion=PUSH) == "ok", score


def test_a_caller_that_names_no_motion_gets_the_old_band():
    """Nothing silently loosens. A caller with no motion to offer is a caller
    that cannot know the camera travelled, and it gets the stricter rule."""
    assert sq.end_pair_verdict(0.380) == "restaged"
    assert sq.end_pair_verdict(0.855) == "copy"
    assert sq.end_pair_verdict(0.600) == "ok"


def test_a_subject_that_fills_the_frame_still_drops_the_floor():
    assert sq.end_pair_verdict(0.100, size="insert") == "ok"


def test_the_drop_reason_says_which_rule_it_applied():
    """`drop_reason` quotes the floor by name. A panel dropped under a floor
    that did not apply to it would name a number that never judged it."""
    said = sq.drop_reason("Q22_0E", "Q22_0", 0.855, motion=PUSH)
    assert "copy" in said and str(sq.END_CEILING) in said, said
