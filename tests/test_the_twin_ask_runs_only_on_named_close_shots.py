"""The twin ask runs ONLY on named-cast, medium-and-closer, multi-figure shots.

G-TWIN's false-positive guard (and its GPU economy): wides and fulls hold
legitimately repeated crowd silhouettes, a planned-0 crowd shot casts nobody
to duplicate, an insert holds no face to compare, and a one-figure read has
nothing to twin.  None of them is ever asked.
"""
from studio.panel_content import TWIN_SIZES, twin_applies


def test_a_named_medium_with_two_figures_is_asked():
    assert twin_applies(planned=1, size="medium", people=2)


def test_every_face_size_is_asked():
    assert TWIN_SIZES == ("medium", "medium_close", "close", "extreme_close")
    assert all(twin_applies(planned=2, size=s, people=3) for s in TWIN_SIZES)


def test_a_wide_is_never_asked():
    assert not twin_applies(planned=2, size="wide", people=5)


def test_a_full_is_never_asked():
    assert not twin_applies(planned=2, size="full", people=3)


def test_an_insert_is_never_asked():
    assert not twin_applies(planned=1, size="insert", people=2)


def test_a_pure_crowd_shot_is_never_asked():
    assert not twin_applies(planned=0, size="medium", people=4)


def test_one_figure_has_nothing_to_twin():
    assert not twin_applies(planned=1, size="medium", people=1)
