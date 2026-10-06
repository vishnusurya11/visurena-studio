"""Two figures that are one individual fail the twin gate; distinct people pass.

G-TWIN-PANEL, judged in code: `twin_fault` fires when figures >= 2 and
distinct < figures -- the ep17 T12 case, two identical Mrs. Elphinstones that
the one weak 'lookalikes' count answered 0 on.
"""
from studio.panel_content import Twins, twin_fault


def test_the_ep17_mrs_elphinstone_case_is_named_with_its_counts():
    got = twin_fault(Twins(2, 1, ["woman in a grey shawl x2"]))
    assert got is not None and got.startswith("twin:")
    assert "woman in a grey shawl x2" in got
    assert "2 figures" in got and "1 distinct" in got


def test_an_empty_twins_list_still_names_the_fault():
    got = twin_fault(Twins(2, 1, []))
    assert got is not None and got.startswith("twin:")
    assert "two figures share one face and dress" in got


def test_two_different_people_are_no_fault():
    assert twin_fault(Twins(2, 2, [])) is None


def test_one_figure_is_no_fault():
    assert twin_fault(Twins(1, 1, [])) is None
