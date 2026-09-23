"""Which picture a place IS belongs to the episode, not to the book.

MEASURED 2026-09-22 (audit item 8). To point episode 9's places at the
pictures drawn at episode 9's hour, the BOOK-WIDE location rows were
rewritten so their one anchor view was the ep09 picture. Every earlier
episode shares those rows, so a retake of ep03-ep08 on Horsell Common would
have staged ep09's hot daylight pit, silently.

A setup now names the view it uses. The book-wide anchor stays what every
earlier episode rendered with, and one picture per place per episode -- the
owner's 2026-09-18 rule -- still holds, because the choice is per setup.
"""
import json

import pytest

from studio import pack_refs
from studio.episode_spec import Setup


def book_with(tmp_path, location: str, drawn: list[str], views: list[str]):
    (tmp_path / "analysis" / "locations").mkdir(parents=True)
    (tmp_path / "refs" / "locations" / location).mkdir(parents=True)
    row = {"id": location, "profile": {"design": {"views": [{"id": v, "prompt": v} for v in views]}}}
    (tmp_path / "analysis" / "locations" / f"{location}.json").write_text(json.dumps(row))
    for name in drawn:
        (tmp_path / "refs" / "locations" / location / f"{name}.png").write_bytes(b"png")
    return tmp_path


def test_with_no_view_named_the_book_anchor_is_used(tmp_path):
    book = book_with(tmp_path, "common", ["wide_establishing", "wide_pit_day"], ["wide_establishing"])
    assert pack_refs.location_view(book, "common").name == "wide_establishing.png"


def test_a_named_view_is_that_picture(tmp_path):
    book = book_with(tmp_path, "common", ["wide_establishing", "wide_pit_day"], ["wide_establishing"])
    assert pack_refs.location_view(book, "common", view="wide_pit_day").name == "wide_pit_day.png"


def test_a_named_view_that_was_never_drawn_refuses(tmp_path):
    book = book_with(tmp_path, "common", ["wide_establishing"], ["wide_establishing"])
    with pytest.raises(SystemExit, match="wide_pit_day"):
        pack_refs.location_view(book, "common", view="wide_pit_day")


def test_naming_a_view_never_rewrites_the_book_row(tmp_path):
    book = book_with(tmp_path, "common", ["wide_establishing", "wide_pit_day"], ["wide_establishing"])
    before = (book / "analysis" / "locations" / "common.json").read_text()
    pack_refs.location_view(book, "common", view="wide_pit_day")
    assert (book / "analysis" / "locations" / "common.json").read_text() == before


def test_a_setup_carries_a_view_and_defaults_to_none():
    from pathlib import Path
    plan = (Path(__file__).resolve().parents[1] / "library" /
            "20260827135508_the-war-of-the-worlds" / "episodes" / "ep08" / "plan.json")
    base = next(iter(json.loads(plan.read_text(encoding="utf-8"))["setups"].values()))
    base.pop("view", None)
    assert Setup.model_validate(base).view == ""
    assert Setup.model_validate({**base, "view": "wide_pit_day"}).view == "wide_pit_day"
