"""OWNER, 2026-10-28: "I don't like the title of shorts fix it. The book name and episode
number 01/20 something like that .. I don't need author".

What shipped on Jekyll and WotW led with the author, the book's `series` field:

    Robert Louis Stevenson: Dr Jekyll and Mr Hyde — Ep 05/10 — "Incident of the Letter"

The author spent 24 of the characters a search result shows before the book was named.
The title now leads with the book and its position; the chapter stays last, where it is
what gives at the 100-character wall.
"""
import inspect

from studio.youtube_publish import series_title

WAS = 'Robert Louis Stevenson: Dr Jekyll and Mr Hyde — Ep 05/10 — "Incident of the Letter"'


def test_the_title_leads_with_the_book_and_its_number():
    got = series_title("Dr Jekyll and Mr Hyde", 5, 10, "Incident of the Letter")
    assert got == 'Dr Jekyll and Mr Hyde — Ep 05/10 — "Incident of the Letter"'


def test_the_author_is_not_in_the_title():
    got = series_title("The War of the Worlds", 8, 27, "Friday Night")
    assert "Wells" not in got and got.startswith("The War of the Worlds — Ep 08/27")


def test_the_title_takes_no_series_name():
    assert "series" not in inspect.signature(series_title).parameters


def test_the_new_title_is_the_old_one_without_its_lead():
    assert series_title("Dr Jekyll and Mr Hyde", 5, 10, "Incident of the Letter") == WAS.split(": ", 1)[1]
