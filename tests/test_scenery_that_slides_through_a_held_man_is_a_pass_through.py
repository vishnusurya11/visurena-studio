"""The set slides through a person held at one screen place: a pass-through.

The held row (`take_lock.lock`) reads the face's travel against a band of
scenery beside the body.  This measure reads the same fault from a DENSE flow
field: a 4-parameter camera fit over the pixels outside the person, and the
share of the BODY BAND whose flow rides with that fit while the face holds
still.  Synthetic: a translating block-textured set with a fixed textured
person on it.  No video, no model.
"""
import numpy as np

from studio import take_lock as tl
from studio.measure import flow as fl
from synth_frames import fixed_face, pan, pin_person

TRUCK = ("The camera tracks sideways to the right along the fence, a truck with small amplitude, until the "
         "side gate already in the picture is at the centre; he goes on holding the basket out")


def test_dis_flow_reads_a_translation_to_the_pixel():
    a, b = pan(2, shift=5)
    field = fl.dis(a[..., 0], b[..., 0])
    assert abs(float(np.median(field[..., 0])) + 5.0) < 0.3
    assert abs(float(np.median(field[..., 1]))) < 0.3


def test_the_four_parameter_fit_recovers_a_translation_and_no_turn():
    a, b = pan(2, shift=5)
    field = fl.dis(a[..., 0], b[..., 0])
    cam = fl.camera(field)
    assert cam["measured"] and abs(cam["tx"] + 5.0) < 0.3 and abs(cam["theta"]) < 0.3
    assert abs(cam["scale"] - 1.0) < 0.01


def test_a_body_band_that_rides_with_the_camera_fit_is_a_pass_through():
    frames = pin_person(pan())
    got = tl.pass_through(frames, track=fixed_face)
    assert got["pass_through"] > 0.75                      # most of the band moved with the set
    assert got["lock"] > 0.75 and abs(got["scen"]) >= tl.TRAVEL
    assert got["fitted_on"] == tl.FITTED_ON


def test_the_pass_through_row_is_hard_on_a_truck_over_a_kept_subject():
    frames = pin_person(pan())
    got = tl.pass_through(frames, track=fixed_face)
    row = tl.pass_through_row(got, TRUCK)
    assert not row.ok and row.hard and row.value == got["pass_through"] and "slides through" in row.note


def test_a_person_who_rides_with_the_set_is_not_a_pass_through():
    """The person pinned to the SET, not the screen: every pixel moves together."""
    frames = pan()
    for k, f in enumerate(frames):
        x0 = 108 - 5 * k
        f[82:162, x0:x0 + 40] = 255
    track = {i: {"cx": (108 - 5 * i + 20) / 256, "cy": 0.4, "h": 0.12} for i in range(0, 24, 6)}
    got = tl.pass_through(frames, track=lambda fr: track)
    assert got["lock"] < 0.5
    assert tl.pass_through_row(got, TRUCK).ok


def test_no_face_means_not_measured():
    assert tl.pass_through(pan(), track=lambda fr: {}) is None
    row = tl.pass_through_row(None, TRUCK)
    assert row.ok and row.value is None and row.note == "not measured"


def test_the_warp_residual_is_low_on_a_pan_and_high_on_a_morph():
    a, b = pan(2, shift=5)
    ga, gb = a[..., 0], b[..., 0]
    rigid = fl.warp_residual(ga, gb, fl.dis(ga, gb))
    other = pan(2, shift=5, seed=8)[0][..., 0]
    morph = fl.warp_residual(ga, other, fl.dis(ga, other))
    assert rigid < 12 and morph > 4 * rigid
    person = np.zeros((256, 256), bool)
    person[82:122, 108:148] = True
    assert fl.warp_residual(ga, gb, fl.dis(ga, gb), mask=person) <= rigid + 1


def test_the_held_measure_now_says_what_it_was_fitted_on():
    got = tl.lock(pin_person(pan()), track=fixed_face)
    assert got["fitted_on"] == tl.FITTED_ON and "one book" in tl.FITTED_ON
