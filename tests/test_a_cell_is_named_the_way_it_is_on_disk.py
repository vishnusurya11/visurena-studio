"""`end_key` takes the name the cells USED to have.

`redraw_panel.py` is the $0.08 repair for one wrong cell, and its own docstring
says to call it as

    uv run python scripts/episode/redraw_panel.py <codex_id> <episode> S14.1 --approved

`end_key` strips a leading "S" and splits on ".", which was the i2v-era naming.
Every cell on disk is `Q14_1.png`, written by `cell_name(shot, sub, end)`, and
handing the tool the name it can see raises

    ValueError: invalid literal for int() with base 10: 'Q13_0'

MEASURED 2026-09-14: that is exactly what happened when episode 5's doorway wide
needed its cane removed. `13.0` worked, so the fault cost a minute rather than a
sheet -- but the name a reader has in front of them is the one on disk, and a
tool that refuses it is a tool that gets used wrong under pressure.

It now takes either: `Q13_0`, `Q13_0E`, `S13.0`, `13.0`, `13.0E`.
"""
import pytest

from studio.episode_seq_board import cell_name, end_key


def test_the_name_on_disk_is_accepted():
    assert end_key("Q13_0") == (13, 0, False)


def test_the_end_name_on_disk_is_accepted():
    assert end_key("Q13_0E") == (13, 0, True)


def test_a_sub_shot_on_disk_is_accepted():
    assert end_key("Q02_1") == (2, 1, False)


def test_the_old_s_form_still_works():
    """Three episodes of notes and one docstring use it."""
    assert end_key("S14.1") == (14, 1, False)
    assert end_key("S19.1E") == (19, 1, True)


def test_the_bare_form_still_works():
    assert end_key("13.0") == (13, 0, False)
    assert end_key("13.0E") == (13, 0, True)


def test_a_filename_is_accepted_whole():
    """What a reader actually copies is the file, extension and all."""
    assert end_key("Q13_0.png") == (13, 0, False)
    assert end_key("Q13_0E.png") == (13, 0, True)


def test_it_round_trips_with_cell_name():
    for shot, sub, end in ((13, 0, False), (2, 1, True), (24, 0, False)):
        assert end_key(cell_name(shot, sub, end)) == (shot, sub, end)


def test_lower_case_is_accepted():
    assert end_key("q13_0e") == (13, 0, True)


def test_nonsense_still_raises():
    with pytest.raises(ValueError):
        end_key("not-a-cell")
