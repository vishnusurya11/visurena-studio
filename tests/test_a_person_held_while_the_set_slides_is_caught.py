"""A person held at one screen position while the set slides past is caught.

ep09 T02 (owner, 2026-09-23: "he walked with the fence ... ai slop, dq missed
it"): the camera trucks along a fence; the neighbour, leaning on it, stays put
on screen and the fence slides through him. take_dq passed it 92.6. Take-gate
audit: lock = 1 - subject travel / scenery travel reads 1.01 on T02 (1055 px of
fence, 10 px of face) and 1.05 on T10; eligible passes top out at -0.42. The
plan's words decide eligibility: a walker the camera tracks WITH is locked and
correct (ep08 T05 reads 1.06).
"""
import numpy as np

from studio import take_lock as tl

T02 = ("The camera tracks sideways to the right along the fence, a truck with small amplitude, until the "
       "side gate already in the picture is at the centre; he goes on holding the strawberries out")
T05_EP08 = ("The camera tracks with him along the platform at his own pace, a truck with small amplitude, "
            "keeping him in the middle of the picture; he calls out the paper")
T22 = "The camera pans to the right with him as he moves off; he goes on shouting"
PUSH = "The camera pushes in toward him with small amplitude; he laughs"


def test_the_plan_says_when_a_held_subject_is_a_fault():
    assert tl.eligible(T02)
    assert not tl.eligible(T05_EP08) and not tl.eligible(T22) and not tl.eligible(PUSH)


def textured(n=24, shift=5, size=256):
    rng = np.random.default_rng(3)
    wide = (rng.random((size, size + n * shift)) * 255).astype(np.uint8)
    wide = np.repeat(np.repeat(wide[::8, ::8], 8, 0), 8, 1)[:size, :size + n * shift]
    return [np.repeat(wide[:, i * shift:i * shift + size][:, :, None], 3, 2) for i in range(n)]


def fixed_face(frames):
    return {i: {"cx": 0.5, "cy": 0.4, "h": 0.12} for i in range(0, len(frames), 6)}


def test_a_face_held_still_over_a_sliding_set_reads_locked():
    frames = textured()
    face = (np.random.default_rng(9).random((40, 40)) * 255).astype(np.uint8)
    face = np.repeat(np.repeat(face[::4, ::4], 4, 0), 4, 1)          # textured, and it never moves
    for f in frames:
        f[82:122, 108:148] = face[:, :, None]
    got = tl.lock(frames, track=fixed_face)
    assert got["lock"] > 0.75 and abs(got["scen"]) >= 100


def test_the_row_is_hard_only_when_eligible_and_locked_over_real_travel():
    assert not tl.row({"lock": 1.01, "scen": 1055}, T02).ok
    assert tl.row({"lock": 1.06, "scen": 900}, T05_EP08).ok          # walking: not eligible
    assert tl.row({"lock": -0.42, "scen": 600}, T02).ok
    assert tl.row({"lock": 1.0, "scen": 40}, T02).ok                  # the set barely moved
    assert tl.row(None, T02).ok                                       # no face: not measured


def test_a_camera_travel_of_one_stride_is_not_a_walking_subject():
    """The real ep09 T02 head ends 'travelling one short stride': the first cut
    of this rule read 'stride' as the subject walking and excused T02."""
    real = ("The camera tracks sideways to the right along the fence, a truck with small amplitude, until "
            "the side gate already in the picture is at the centre, travelling one short stride; he goes on "
            "holding the strawberries out across the rail and laughs as he speaks")
    assert tl.eligible(real)
    assert not tl.eligible("The camera tracks sideways along the road; he goes on striding toward the gate")
