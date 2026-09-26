"""Each setup's place picture is drawn from the plan, and the book is not rewritten.

Promoted from three ep09 session scripts (audit 2026-09-22, items 5 and 13 of
the skills and structure reports): a typed list of places and views to draw,
a row writer, and a script that REWROTE the book's location rows to point at
ep09's pictures -- which moved every earlier episode's Horsell Common into
daylight. Here the list is the plan's own setups, a setup's `view` is the
choice, and an existing row is never touched.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "refs"))

import places  # noqa: E402


class Setup:
    def __init__(self, location, view, described="a place at noon"):
        self.location, self.view, self.described = location, view, described


def book(tmp_path, rows=(), drawn=()):
    (tmp_path / "analysis" / "locations").mkdir(parents=True)
    for loc in rows:
        (tmp_path / "analysis" / "locations" / f"{loc}.json").write_text(json.dumps(
            {"id": loc, "name": loc, "profile": {"design": {"views": [{"id": "wide_establishing"}]}}}))
    for loc, view in drawn:
        folder = tmp_path / "refs" / "locations" / loc
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{view}.png").write_bytes(b"png")
    return tmp_path


def test_a_drawn_view_is_had(tmp_path):
    b = book(tmp_path, ["common"], [("common", "wide_pit_day")])
    assert places.status(b, {"pit": Setup("common", "wide_pit_day")}) == [("pit", "common", "wide_pit_day", "have")]


def test_a_view_not_drawn_is_missing(tmp_path):
    b = book(tmp_path, ["common"])
    assert places.status(b, {"pit": Setup("common", "wide_pit_day")})[0][3] == "missing"


def test_drawing_draws_only_what_is_missing_and_from_the_setups_words(tmp_path):
    b = book(tmp_path, ["common"], [("common", "wide_have")])
    asked = []

    def draw(prompt, target):
        asked.append((prompt, target.name))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"png")
    setups = {"a": Setup("common", "wide_have"), "b": Setup("common", "wide_new", "ON FIRE at dusk")}
    places.draw_missing(b, setups, draw)
    assert asked == [("ON FIRE at dusk", "wide_new.png")]


def test_a_place_with_no_row_refuses_without_a_name(tmp_path):
    with pytest.raises(SystemExit, match="garden"):
        places.ensure_rows(book(tmp_path), {"g": Setup("garden", "wide_morning")}, names={}, number=9)


def test_a_new_row_is_written_with_the_name_given(tmp_path):
    b = book(tmp_path)
    places.ensure_rows(b, {"g": Setup("garden", "wide_morning")}, names={"garden": "the narrator's garden"}, number=9)
    row = json.loads((b / "analysis" / "locations" / "garden.json").read_text())
    assert row["name"] == "the narrator's garden" and row["first_appearance"] == 9


def test_an_existing_row_is_never_rewritten(tmp_path):
    b = book(tmp_path, ["common"])
    before = (b / "analysis" / "locations" / "common.json").read_text()
    places.ensure_rows(b, {"pit": Setup("common", "wide_pit_day")}, names={"common": "x"}, number=9)
    assert (b / "analysis" / "locations" / "common.json").read_text() == before


def test_a_place_is_drawn_in_the_books_look(tmp_path):
    """Root cause 2026-09-26 (D13): the place pictures had no style words, the
    house model drew them painterly, and from ep09 the storyboard copied its
    style from the place -- 3D people pasted onto paintings."""
    b = book(tmp_path, ["common"])
    asked = []

    def draw(prompt, target):
        asked.append(prompt)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"png")
    places.draw_missing(b, {"b": Setup("common", "wide_new", "a meadow at noon")}, draw,
                        look="Angular stylised 3D animation, brush-stroke texture")
    assert asked[0].startswith("a meadow at noon") and "Angular stylised 3D animation" in asked[0]
    assert "not a painting" in asked[0].lower()
