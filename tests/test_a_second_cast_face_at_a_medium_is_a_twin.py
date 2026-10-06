"""A cast-sized EXTRA face at medium-and-closer is a twin, crowd notwithstanding.

G-TWIN-DQ (2026-10-05): ep18 shot 16 read 'faces 3/2' and passed, because the
declared crowd stood the 'people' flag down.  A face big enough to be somebody
(>= CAST_FACE) in a size where the face IS the picture cannot be an onlooker:
beyond planned + extras it is a second copy of a cast member.  The guards are
structural -- wides and fulls are excluded, planned-0 pure-crowd shots are
excluded, and `near` already drops crowd-sized silhouettes.
"""
from studio.panel_dq import verdict


def test_the_ep18_shot_16_regression_is_a_hard_twin():
    row = verdict(faces=[0.2, 0.25, 0.3], planned=2, extras=0, crowd=True,
                  size="medium", sharp=1.0, ink=0.0, tiled=0.0)
    assert "twin" in row["flags"] and not row["passed"]


def test_the_same_faces_at_a_wide_are_a_crowds_business():
    row = verdict(faces=[0.2, 0.25, 0.3], planned=2, extras=0, crowd=True,
                  size="wide", sharp=1.0, ink=0.0, tiled=0.0)
    assert "twin" not in row["flags"]


def test_a_pure_crowd_shot_names_nobody_and_is_never_a_twin():
    row = verdict(faces=[0.2, 0.25, 0.3], planned=0, extras=0, crowd=True,
                  size="medium", sharp=1.0, ink=0.0, tiled=0.0)
    assert "twin" not in row["flags"]


def test_a_declared_extra_is_honoured():
    row = verdict(faces=[0.2, 0.25, 0.3], planned=2, extras=1, crowd=True,
                  size="medium", sharp=1.0, ink=0.0, tiled=0.0)
    assert "twin" not in row["flags"]


def test_the_planned_count_at_a_close_passes():
    row = verdict(faces=[0.2, 0.25], planned=2, extras=0, crowd=True,
                  size="close", sharp=1.0, ink=0.0, tiled=0.0)
    assert "twin" not in row["flags"]


def test_crowd_sized_silhouettes_never_count_against_the_cast():
    """`near` is cast faces: a skyline band of small heads is not a twin."""
    row = verdict(faces=[0.25, 0.2] + [0.02] * 5, planned=2, extras=0, crowd=True,
                  size="medium", sharp=1.0, ink=0.0, tiled=0.0)
    assert "twin" not in row["flags"]
