"""Tests for studio.storytime — dating scenes from the book's own words."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from studio import storytime as st


# --- spelled-out numbers ---


@pytest.mark.parametrize("text,expected", [
    ("eighteen hundred and forty-seven", 1847),
    ("twenty-nine", 29),
    ("three", 3),
    ("nineteen hundred", 1900),
])
def test_words_to_number(text, expected):
    assert st.words_to_number(text) == expected


def test_words_to_number_none_for_plain_text():
    assert st.words_to_number("last night") is None


# --- absolute dates the book states ---


def test_parse_spelled_out_date_from_the_book():
    assert st.parse_date("the fourth of May, eighteen hundred and forty-seven") \
        == date(1847, 5, 4)


def test_parse_numeric_date_from_the_book():
    assert st.parse_date("August 4th, 1860") == date(1860, 8, 4)


def test_parse_date_uses_context_year_when_text_omits_it():
    assert st.parse_date("the 4th of March", default_year=1881) == date(1881, 3, 4)


def test_parse_date_none_without_a_month():
    assert st.parse_date("Tuesday, the 4th inst.", default_year=1881) is None
    assert st.parse_date("for a week") is None


def test_parse_date_rejects_impossible_day():
    assert st.parse_date("February 44th, 1860") is None


# --- offsets that advance the clock ---


@pytest.mark.parametrize("text,days", [
    ("three days", 3),
    ("Three weeks", 21),
    ("Twenty-nine days", 29),
    ("about five years", 5 * 365),
    ("a month", 30),
    ("a fortnight", 14),
    ("a few days", 3),
])
def test_parse_offset(text, days):
    assert st.parse_offset(text) == timedelta(days=days)


def test_parse_offset_ignores_sub_day_spans():
    assert st.parse_offset("another half hour") is None
    assert st.parse_offset("For twenty minutes or more") is None


def test_parse_offset_none_for_non_durations():
    assert st.parse_offset("last night") is None
    assert st.parse_offset("") is None


def test_parse_offset_rejects_absurd_spans():
    assert st.parse_offset("nine hundred years") is None


def test_format_date_is_readable():
    assert st.format_date(date(1881, 3, 4)) == "4 March 1881"
