"""An unplanned cut inside a take is called by three readers -- the brightness
step (`take_coherence.hard_cut`), the picture jump (`take_jump.min_step`) and
PySceneDetect's adaptive detector -- and it takes two of the three to make a
HARD row.  One reader alone is an advisory.  The detector runs on numpy
frames here; no video is decoded.
"""
import numpy as np

from studio import take_coherence as tc, take_jump
from studio.measure import cuts
from synth_frames import hold, picture, rgb


def two_pictures(at: int = 20, n: int = 40) -> np.ndarray:
    a, b = picture(51), picture(52)
    return np.concatenate([hold(a, at), hold(b, n - at)])


def test_scenedetect_finds_the_cut_at_its_frame():
    frames = [rgb(f) for f in two_pictures(20)]
    assert cuts.scene_cuts(frames) == [20]
    assert cuts.scene_cuts([rgb(f) for f in hold(picture(53), 30)]) == []


def test_a_cut_on_a_pin_is_planned_and_one_elsewhere_is_not():
    assert cuts.unplanned([20], [("Q00_0.png", 0), ("Q01_0.png", 20 + tc.PIN_TOL)]) == []
    assert cuts.unplanned([20], [("Q00_0.png", 0), ("Q01_0.png", 20 + tc.PIN_TOL + 1)]) == [20]
    assert cuts.unplanned([], [("Q00_0.png", 0)]) == []


def test_two_of_three_votes_make_the_cut_and_one_does_not():
    one = cuts.vote(jump=True, step=False, scene=False)
    assert one["count"] == 1 and one["cut"] is False
    two = cuts.vote(jump=True, step=False, scene=True)
    assert two["count"] == 2 and two["cut"] is True and two["votes"] == {"jump": True, "step": False, "scene": True}
    assert cuts.vote(jump=True, step=True, scene=True)["cut"] is True
    assert cuts.vote(jump=False, step=False, scene=False)["count"] == 0


def test_the_row_is_hard_on_two_votes_and_advisory_on_one():
    hard = cuts.row(cuts.vote(jump=True, step=True, scene=False))
    assert not hard.ok and hard.hard and hard.value == 2 and "jump+step" in hard.note
    adv = cuts.row(cuts.vote(jump=False, step=False, scene=True))
    assert not adv.ok and not adv.hard and adv.penalty < hard.penalty
    assert cuts.row(cuts.vote(jump=False, step=False, scene=False)).ok


def test_the_three_readers_agree_on_a_synthetic_cut():
    frames = two_pictures(20)
    m = tc.measure(frames, {"Q00_0.png": __import__("PIL.Image", fromlist=["Image"]).fromarray(frames[0])})
    from studio import cut_landing as cl
    jump = take_jump.min_step(cl.signatures(frames.astype(np.uint8)))
    v = cuts.vote(jump=jump < take_jump.WALL, step=m["hard_cut"] > tc.CUT_HARD,
                  scene=bool(cuts.unplanned(cuts.scene_cuts([rgb(f) for f in frames]), [])))
    assert v["count"] == 3 and v["cut"]
