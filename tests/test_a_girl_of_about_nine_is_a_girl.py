"""'A small girl of about nine' was staged to H3 as "<Picture 2> defines this woman alone"
(Jekyll ep01 v2 T05-T07, 2026-10-15): `age_of` read digits only, so the child's row stated
no age and the builder fell back to the adult noun beside her sheet."""
from __future__ import annotations

from studio import episode_ref_official as ro


def test_an_age_in_words_after_about_is_read():
    assert ro.age_of("A small girl of about nine, thin and quick") == 9


def test_digits_still_read():
    assert ro.age_of("Boy of 13") == 13 and ro.age_of("52 years old") == 52


def test_words_years_old_are_read():
    assert ro.age_of("a lad, twelve years old") == 12


def test_a_man_of_about_fifty_is_not_young():
    assert ro.age_of("a man of about fifty") == 50


def test_no_age_is_none():
    assert ro.age_of("a small or little man") is None
