"""A video's series name and episode count come from its own book.

MEASURED 2026-09-22 (audit item 13): `series_title` hardcoded "Sherlock
Holmes" and the retitle script defaulted to 14 episodes -- the other book's
character and chapter count. Run over The War of the Worlds it would have
renamed published videos "Sherlock Holmes: The war of the worlds — Ep 08/14".
"""
import json

import pytest

from scripts.publish.youtube_retitle import series_of

# The title no longer names the series (owner 2026-10-28, test_a_title_is_the_book_and_its_number);
# the book's record still says it, and the metadata brief still reads it.


def book(tmp_path, **fields):
    (tmp_path / "source").mkdir()
    (tmp_path / "source" / "book.json").write_text(json.dumps({"title": "the war", **fields}))
    return tmp_path


def test_the_book_says_its_series_title_and_length(tmp_path):
    b = book(tmp_path, series="H. G. Wells", display_title="The War of the Worlds", episodes=27)
    assert series_of(b) == ("H. G. Wells", "The War of the Worlds", 27)


@pytest.mark.parametrize("missing", ["series", "display_title", "episodes"])
def test_a_book_that_does_not_say_refuses(tmp_path, missing):
    fields = {"series": "H. G. Wells", "display_title": "The War of the Worlds", "episodes": 27}
    fields.pop(missing)
    with pytest.raises(SystemExit, match=missing):
        series_of(book(tmp_path, **fields))
