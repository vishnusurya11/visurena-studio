"""A storyboard panel is measured, not admired.

OWNER 2026-09-20: "the images are shit in the ones you shared .. you did not do
any dq."

Right. 28 panels went out with five faults marked BY EYE and nothing measured.
An eye is not evidence, and this repo has gates for exactly that reason -- the
lesson already written down as "green tests are not evidence a prompt fix
reached the artefact; measure the artefact". The same rule applies to a picture
I am about to call good.

The gates here are the ones the video already uses, pointed at a still:
`face_end.faces` for who is in it, `people_count.clones` for two of the same
man, `motion_quality.sharpness` for a panel that came back soft. Plus two the
storyboard taught today: lettering burned into a reference, and a panel that is
secretly a tiled sheet.
"""
import numpy as np
import pytest


def flat(value: int = 128, size: int = 256) -> np.ndarray:
    return np.full((size, size, 3), value, dtype=np.uint8)


def test_a_panel_with_more_faces_than_planned_is_flagged():
    from studio.panel_dq import verdict
    row = verdict(faces=[0.2, 0.19, 0.2], planned=2, sharp=1.0, ink=0.0, tiled=0.0)
    assert "people" in row["flags"]


def test_the_planned_count_passes():
    from studio.panel_dq import verdict
    assert "people" not in verdict(faces=[0.2, 0.19], planned=2,
                                   sharp=1.0, ink=0.0, tiled=0.0)["flags"]


def test_a_panel_that_names_nobody_may_still_hold_a_crowd():
    """Shot 9's band of people on the skyline names no character and is right."""
    from studio.panel_dq import verdict
    row = verdict(faces=[0.02] * 20, planned=0, sharp=1.0, ink=0.0, tiled=0.0)
    assert "people" not in row["flags"], "small far faces are a crowd, not a cast"


def test_two_of_the_same_size_face_where_one_was_planned_is_a_clone():
    from studio.panel_dq import verdict
    assert "clone" in verdict(faces=[0.3, 0.3], planned=1,
                              sharp=1.0, ink=0.0, tiled=0.0)["flags"]


def test_a_soft_panel_is_flagged():
    """`sharp` is the panel's sharpness OVER the median of its own set: raw
    Laplacian variance has no absolute scale, which an absolute 0.45 floor
    learned the hard way by passing a panel that measured 279."""
    from studio.panel_dq import verdict
    assert "blur" in verdict(faces=[], planned=0, sharp=0.2, ink=0.0, tiled=0.0)["flags"]


def test_the_yardstick_is_the_median_of_the_set():
    from studio.panel_dq import softness
    assert softness([100.0, 200.0, 300.0]) == 200.0
    assert softness([]) == 0.0


def test_lettering_in_a_reference_is_a_fault():
    """Measured today: WIDE/MEDIUM/INSERT were drawn into the corners, and a
    reference's lettering becomes the video's lettering."""
    from studio.panel_dq import verdict
    assert "text" in verdict(faces=[], planned=0, sharp=1.0, ink=0.9, tiled=0.0)["flags"]


def test_a_tiled_panel_is_a_fault():
    """The six 1x1 'grids' came back as sheets of the same picture repeated."""
    from studio.panel_dq import verdict
    assert "tiled" in verdict(faces=[], planned=0, sharp=1.0, ink=0.0, tiled=0.95)["flags"]


def test_a_clean_panel_carries_no_flags():
    from studio.panel_dq import verdict
    assert verdict(faces=[0.25], planned=1, sharp=1.0, ink=0.0, tiled=0.0)["flags"] == []


def test_tiledness_sees_a_repeated_half():
    """Half the picture equal to the other half is a sheet, not a shot."""
    from studio.panel_dq import tiledness
    half = np.tile(np.arange(128, dtype=np.uint8)[:, None, None], (1, 256, 3))
    assert tiledness(np.vstack([half, half])) > 0.9


def test_tiledness_is_low_on_an_ordinary_picture():
    from studio.panel_dq import tiledness
    rng = np.random.default_rng(3)
    assert tiledness(rng.integers(0, 255, (256, 256, 3), dtype=np.uint8)) < 0.5


def test_sharpness_is_judged_inside_its_own_hour():
    """MEASURED 2026-09-20 against a CONTROL, which is what made it provable.

    Nine of ep05's panels failed 'blur' and every one was a night panel. So I
    measured a picture known to be good: `wide_night.png`, drawn in the house
    style an hour earlier and perfectly sharp, scores 37 where the sunset wide
    scores 253. It would fail its own gate.

    Laplacian variance falls with darkness and with emptiness, neither of which
    is softness -- shot 20 is green smoke on a bare sky, bright and nearly
    detailless. A panel can only be compared with panels of the same hour, the
    same way the grid unit is the setup because the light differs."""
    from studio.panel_dq import by_setup
    got = by_setup({0: ("sunset", 250.0), 1: ("sunset", 260.0),
                    2: ("dark", 36.0), 3: ("dark", 38.0)})
    assert got[2] > 0.9, "a dark panel is normal among dark panels"
    assert got[0] > 0.9


def test_a_genuinely_soft_panel_still_fails_among_its_own():
    from studio.panel_dq import by_setup
    got = by_setup({0: ("dark", 40.0), 1: ("dark", 38.0), 2: ("dark", 4.0)})
    assert got[2] < 0.5


def test_a_crowd_shot_is_not_a_cast_overflow():
    """Shots 10, 12 and 19 name no CAST and are full of onlookers by design --
    the washerwoman, the governess, the deputation. Counting detected faces
    against named characters calls every crowd a fault."""
    from studio.panel_dq import verdict
    row = verdict(faces=[0.2, 0.18, 0.17], planned=0, sharp=1.0, ink=0.0,
                  tiled=0.0, crowd=True)
    assert "people" not in row["flags"]


def test_a_solo_shot_with_an_extra_face_still_fails():
    from studio.panel_dq import verdict
    row = verdict(faces=[0.3, 0.28], planned=1, sharp=1.0, ink=0.0,
                  tiled=0.0, crowd=False)
    assert "people" in row["flags"]


def test_a_figure_where_the_plan_wants_none_is_still_caught():
    """Shot 21's fairy: nobody planned, no crowd in the prose, a face present."""
    from studio.panel_dq import verdict
    assert "people" in verdict(faces=[0.25], planned=0, sharp=1.0, ink=0.0,
                               tiled=0.0, crowd=False)["flags"]
