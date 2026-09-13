"""Binding, checking and drawing a book's object references.

The same three verbs the character path has (`cast_bust.py` draws, `cast_cards.py
--check` gates, `refs.json` binds), for the third reference kind.
"""
import json

import pytest

from scripts.episode import prop_refs as cli

STICK = dict(
    id="walking_stick", name="Watson's walking stick",
    overall="stands hip high on a six-foot man",
    cross_section="its shaft is as thick as one finger",
    detail="a polished silver ball knob the size of a plum caps it",
    material="black lacquered hardwood", sits="on the ground beside his right boot",
    held_by="john_watson")


def a_book(tmp_path):
    (tmp_path / "refs").mkdir(parents=True)
    (tmp_path / "refs" / "refs.json").write_text(json.dumps(
        {"book_id": "b", "palette": "Muted soot-black and gaslight amber.",
         "refs": [{"ref_id": "char-john_watson", "kind": "character", "entity_id": "john_watson",
                   "name": "Watson", "physical": "A man.", "rel_path": "refs/characters/x.png"}]}),
        encoding="utf-8")
    return tmp_path


def test_binding_adds_a_prop_row_and_keeps_the_characters(tmp_path):
    book = a_book(tmp_path)
    assert cli.bind(book, [STICK]) == ["walking_stick"]
    rows = json.loads((book / "refs" / "refs.json").read_text(encoding="utf-8"))["refs"]
    assert [r["kind"] for r in rows] == ["character", "prop"]
    assert rows[1]["ref_id"] == "prop-walking_stick"


def test_binding_the_same_prop_twice_replaces_rather_than_duplicates(tmp_path):
    book = a_book(tmp_path)
    cli.bind(book, [STICK])
    cli.bind(book, [{**STICK, "detail": "a silver ball knob the size of a walnut caps it"}])
    props = cli.bound(book)
    assert len(props) == 1 and "walnut" in props[0]["physical"]


def test_a_prop_missing_a_measure_is_refused_at_bind_time(tmp_path):
    """Refused here, not discovered in a drawn sheet."""
    book = a_book(tmp_path)
    with pytest.raises(Exception):
        cli.bind(book, [{**STICK, "cross_section": ""}])


def test_check_reports_a_row_whose_picture_is_missing(tmp_path):
    book = a_book(tmp_path)
    cli.bind(book, [STICK])
    assert "walking_stick" in cli.check(book)


def test_check_is_clean_once_the_picture_is_on_disk(tmp_path):
    book = a_book(tmp_path)
    cli.bind(book, [STICK])
    out = book / "refs" / "props" / "prop-walking_stick.png"
    out.parent.mkdir(parents=True)
    out.write_bytes(b"png")
    assert cli.check(book) == {}


def test_drawing_writes_the_rows_own_path_and_asks_for_a_body(tmp_path):
    book = a_book(tmp_path)
    cli.bind(book, [STICK])
    seen = {}

    def render(prompt, prefix, seed, dest):
        seen.update(prompt=prompt, prefix=prefix, seed=seed)
        dest.write_bytes(b"drawn")
        return dest

    made = cli.draw(book, "walking_stick", render=render)
    assert made == book / "refs" / "props" / "prop-walking_stick.png"
    assert seen["prefix"] == "REF-prop-walking_stick"
    assert "hand" in seen["prompt"].lower()
    assert "hip high on a six-foot man" in seen["prompt"]


def test_a_picture_on_disk_is_never_redrawn(tmp_path):
    book = a_book(tmp_path)
    cli.bind(book, [STICK])
    out = book / "refs" / "props" / "prop-walking_stick.png"
    out.parent.mkdir(parents=True)
    out.write_bytes(b"kept")
    assert cli.draw(book, "walking_stick",
                    render=lambda *a: pytest.fail("redrew")).read_bytes() == b"kept"


def test_an_unbound_prop_is_refused_not_invented(tmp_path):
    book = a_book(tmp_path)
    with pytest.raises(KeyError, match="bind it before you draw it"):
        cli.draw(book, "a_lamp")


def test_the_seed_is_stable_and_clear_of_the_character_band(tmp_path):
    assert cli.seed_for("walking_stick") == cli.seed_for("walking_stick")
    assert cli.seed_for("walking_stick") >= cli.SEED_BASE
    assert cli.seed_for("walking_stick") != cli.seed_for("violin")
