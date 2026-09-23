r"""A serial's title leads with the serial and the number, not with the episode.

OWNER, 2026-09-14: "update all youtube title so far to SH : A Study in Scarlet
Ep 01/14 something like that ... book name and episode list should come first in
title".

What shipped, five times, was the other order:

    "You Have Been in Afghanistan, I Perceive" -- A Study in Scarlet Ep.1

which fails at the only place a title is read: a search result, a sidebar, a
phone. YouTube truncates to roughly 40-70 characters depending on surface, so a
viewer sees the CHAPTER and never learns this is episode 1 of a series, nor
which series. Two of the five (`Ep.4`, `Ep.5`) are also unreadable as a position
-- "Ep.4" of how many is not stated anywhere.

Nothing built this string. Each `episodes/epNN/youtube.json` carried a title
somebody typed, so "the format" existed only as five imitations of each other,
and episode 6 would have been a sixth. This is the function that builds it.

THE SHAPE, and what each part is doing:

    Sherlock Holmes: A Study in Scarlet - Ep 04/14 - "What John Rance Had to Tell"
    \_____________/  \________________/   \_______/   \___________________________/
     the character    the book             where you   what this one is
     people search    this serial is       are in it
                      part of

`04/14` and not `Ep.4` because a viewer deciding whether to start a serial wants
to know how long it is, and a viewer who has seen three wants to know how many
are left.

WHAT GIVES WHEN IT DOES NOT FIT.  YouTube's wall is 100 characters. The series
and the number are the part the owner asked to come first and the part that
identifies the video, so they are never what is cut; the chapter title is. This
is not hypothetical -- chapter 13 is "A Continuation of the Reminiscences of
John Watson, M.D.", 56 characters, which overruns by seven.
"""
import pytest

from studio.youtube_publish import TITLE_MAX
from studio.youtube_publish import series_title as _series_title


def series_title(*args, **kw):
    """These are the Scarlet book's titles, so they name its series. The series
    used to be a hardcoded default; it is the caller's now (audit item 13)."""
    return _series_title(*args, series="Sherlock Holmes", **kw)


def test_the_series_comes_first():
    got = series_title("A Study in Scarlet", 4, 14, "What John Rance Had to Tell")
    assert got.startswith("Sherlock Holmes: A Study in Scarlet")


def test_the_episode_number_is_padded_and_says_the_total():
    got = series_title("A Study in Scarlet", 4, 14, "What John Rance Had to Tell")
    assert "Ep 04/14" in got


def test_the_chapter_title_is_quoted_and_last():
    got = series_title("A Study in Scarlet", 4, 14, "What John Rance Had to Tell")
    assert got.endswith('"What John Rance Had to Tell"')


def test_the_whole_thing():
    assert series_title("A Study in Scarlet", 1, 14,
                        "You Have Been in Afghanistan, I Perceive") == (
        'Sherlock Holmes: A Study in Scarlet — Ep 01/14 — '
        '"You Have Been in Afghanistan, I Perceive"')


def test_every_episode_of_this_book_fits_the_wall():
    """All fourteen, against the real chapter titles."""
    for n, chapter in enumerate(CHAPTERS, start=1):
        got = series_title("A Study in Scarlet", n, 14, chapter)
        assert len(got) <= TITLE_MAX, f"ep{n:02d} is {len(got)}: {got}"


# ---- what gives when it does not fit ---------------------------------------

LONG = "A Continuation of the Reminiscences of John Watson, M.D."


def test_a_long_chapter_is_elided_not_the_series():
    got = series_title("A Study in Scarlet", 13, 14, LONG)
    assert got.startswith("Sherlock Holmes: A Study in Scarlet — Ep 13/14")
    assert len(got) <= TITLE_MAX


def test_an_elided_chapter_says_it_was_elided():
    got = series_title("A Study in Scarlet", 13, 14, LONG)
    assert got.endswith('…"')


def test_an_elision_does_not_end_mid_word():
    got = series_title("A Study in Scarlet", 13, 14, LONG)
    inside = got.split("—")[-1].strip().strip('"').rstrip("…")
    assert LONG.startswith(inside) and not inside.endswith(" ")
    assert LONG[len(inside)] in " ,", "cut between words, not inside one"


def test_a_chapter_that_fits_is_never_touched():
    """Thirteen of the fourteen fit whole; only chapter 13 is ever cut."""
    cut = [c for c in CHAPTERS
           if c not in series_title("A Study in Scarlet", 7, 14, c)]
    assert cut == [LONG]


# ---- refusals ---------------------------------------------------------------

def test_an_episode_past_the_total_is_refused():
    with pytest.raises(ValueError, match="15 of 14"):
        series_title("A Study in Scarlet", 15, 14, "The Conclusion")


def test_a_chapterless_episode_is_refused():
    with pytest.raises(ValueError, match="chapter"):
        series_title("A Study in Scarlet", 1, 14, "   ")


def test_the_result_is_a_title_youtube_accepts():
    """It is handed straight to `spec`, which walls it again."""
    from studio.youtube_publish import spec
    body = spec(series_title("A Study in Scarlet", 13, 14, LONG), "d", [], synthetic=True)
    assert body["snippet"]["title"]


CHAPTERS = (
    "You Have Been in Afghanistan, I Perceive",   # ep01 leads with the hook, not "Mr. Sherlock Holmes"
    "The Science of Deduction",
    "The Lauriston Garden Mystery",
    "What John Rance Had to Tell",
    "Our Advertisement Brings a Visitor",
    "Tobias Gregson Shows What He Can Do",
    "Light in the Darkness",
    "On the Great Alkali Plain",
    "The Flower of Utah",
    "John Ferrier Talks with the Prophet",
    "A Flight for Life",
    "The Avenging Angels",
    LONG,
    "The Conclusion",
)
