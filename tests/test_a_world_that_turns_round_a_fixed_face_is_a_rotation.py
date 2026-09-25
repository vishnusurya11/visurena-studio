"""The world turned round a fixed face: a rotation no plan asked for.

One owner-caught take: a laid-down man whose room rotated about his face, and
no take row saw it because the face detector lost him at the end.  The zoom
fit gains the fourth parameter (theta) over its own window lattice; the take's
cumulative theta against a plan with no roll is the row.  Synthetic rotation of
a textured picture, a fixed textured face at the centre.
"""
import numpy as np

from studio import take_zoom as tz
from studio.measure import flow as fl
from synth_frames import hold, patch, picture, rotate

STEP, N = 1.5, 13
PUSH = "The camera pushes in on his face across the whole shot, travelling a hand's breadth; he speaks."
ROLL = "The camera rolls a quarter turn about his face as he lies there; he speaks."


def turning_world(seed: int = 21) -> np.ndarray:
    frames = rotate(picture(seed), N, STEP)
    face = patch(9, 40)
    frames[:, 108:148, 108:148] = face[None]                   # the face never turns
    return frames


def test_the_fit_reads_one_step_of_rotation():
    a, b = turning_world()[:2]
    theta, inliers = tz.step_theta(a, b)
    assert inliers >= tz.MIN_INLIERS
    assert abs(abs(theta) - STEP) < 0.4


def test_the_cumulative_theta_of_a_turning_world_is_the_turn():
    z = tz.zoom_frames(turning_world(), samples=7)
    assert abs(abs(z["cum_theta"]) - STEP * (N - 1)) < 0.15 * STEP * (N - 1)
    assert len(z["theta_steps"]) == len(z["per_step"])


def test_a_still_world_and_a_pan_read_no_turn():
    z = tz.zoom_frames(hold(picture(22), 12), samples=4)
    assert abs(z["cum_theta"]) < 0.5
    big = picture(23, 256 + 40)
    panned = np.stack([big[:256, 3 * k:3 * k + 256] for k in range(12)])
    assert abs(tz.zoom_frames(panned, samples=4)["cum_theta"]) < 0.5


def test_the_rotation_row_is_a_fault_only_when_no_roll_was_planned():
    z = {"cum_theta": 18.0, "measured": True}
    row = tz.rotation_row(z, PUSH)
    assert not row.ok and row.value == 18.0 and "no roll planned" in row.note and row.penalty > 0
    assert tz.rotation_row(z, ROLL).ok and tz.planned_roll(ROLL) and not tz.planned_roll(PUSH)
    assert tz.rotation_row({"cum_theta": 1.2, "measured": True}, PUSH).ok
    quiet = tz.rotation_row({}, PUSH)
    assert quiet.ok and quiet.value is None


def test_the_wall_carries_what_it_was_fitted_on():
    assert tz.ROLL_WALL > 0 and "one" in tz.ROLL_FITTED_ON
    row = tz.rotation_row({"cum_theta": tz.ROLL_WALL + 1, "measured": True}, PUSH)
    assert not row.ok and not row.hard                            # advisory until the bench has a second row


def test_similarity_unpacks_scale_and_theta_from_the_linear_fit():
    sol = np.array([np.cos(np.radians(10)) * 1.2 - 1, np.sin(np.radians(10)) * 1.2, 2.0, -3.0])
    got = fl.unpack(sol)
    assert abs(got["scale"] - 1.2) < 1e-9 and abs(got["theta"] - 10.0) < 1e-9
    assert got["ty"] == 2.0 and got["tx"] == -3.0
