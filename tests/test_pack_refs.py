"""The book's reference pack as a take reads it: a location VIEW chosen by the
shot's size, one character sheet, and the chapter's wardrobe said in words."""
import json

import pytest

from studio import pack_refs

VIEWS = [
    {"id": "wide_establishing", "shot_size": "wide"},
    {"id": "reverse", "shot_size": "wide"},
    {"id": "insert_eyepiece_field", "shot_size": "insert"},
    {"id": "medium_little_table", "shot_size": "medium"},
    {"id": "medium_summerhouse_view", "shot_size": "medium-wide"},
]
ALL = {v["id"] for v in VIEWS}


def test_a_wide_shot_takes_the_first_wide_view():
    assert pack_refs.view_for("wide", VIEWS, ALL) == "wide_establishing"


def test_an_insert_takes_the_insert_view():
    assert pack_refs.view_for("insert", VIEWS, ALL) == "insert_eyepiece_field"


def test_a_medium_close_takes_the_medium_view():
    assert pack_refs.view_for("medium_close", VIEWS, ALL) == "medium_little_table"


def test_only_views_on_disk_are_chosen():
    assert pack_refs.view_for("wide", VIEWS, {"reverse", "medium_little_table"}) == "reverse"


def test_a_size_with_no_matching_view_falls_to_the_nearest_drawn_size():
    assert pack_refs.view_for("insert", VIEWS, {"medium_little_table", "reverse"}) == "medium_little_table"


def test_the_named_view_wins_when_it_is_drawn():
    assert pack_refs.view_for("wide", VIEWS, ALL, named="reverse") == "reverse"


def test_a_named_view_that_is_not_drawn_is_refused():
    with pytest.raises(SystemExit, match="medium_little_table"):
        pack_refs.view_for("medium", VIEWS, {"reverse"}, named="medium_little_table")


def test_nothing_drawn_is_refused():
    with pytest.raises(SystemExit):
        pack_refs.view_for("wide", VIEWS, set())


def _book(tmp_path):
    loc = tmp_path / "analysis" / "locations"
    loc.mkdir(parents=True)
    (loc / "observatory.json").write_text(json.dumps({"profile": {"design": {"views": VIEWS}}}))
    drawn = tmp_path / "refs" / "locations" / "observatory"
    drawn.mkdir(parents=True)
    for name in ("wide_establishing", "insert_eyepiece_field"):
        (drawn / f"{name}.png").write_bytes(b"png")
    chars = tmp_path / "analysis" / "characters"
    chars.mkdir(parents=True)
    card = {"name": "Ogilvy", "profile": {
        "physical": "Man of 47, thickset, auburn beard.",
        "wardrobe": {"observatory_night": "Ochre tweed Inverness cape, velvet smoking cap.",
                     "pit_shirtsleeves": "Shirtsleeves rolled, dark with soil."},
        "wardrobe_by_chapter": {"1": "observatory_night", "3": "pit_shirtsleeves"}}}
    (chars / "ogilvy.json").write_text(json.dumps(card))
    sheet = tmp_path / "refs" / "characters" / "ogilvy"
    sheet.mkdir(parents=True)
    (sheet / "sheet.png").write_bytes(b"png")
    return tmp_path


def test_every_size_opens_on_the_one_establishing_wide(tmp_path):
    book = _book(tmp_path)
    got = pack_refs.location_view(book, "observatory", "insert")
    assert got == book / "refs" / "locations" / "observatory" / "wide_establishing.png"


def test_a_named_view_is_ignored_for_the_one_wide(tmp_path):
    book = _book(tmp_path)
    got = pack_refs.location_view(book, "observatory", "wide", "insert_eyepiece_field")
    assert got.name == "wide_establishing.png"


def test_a_location_without_an_establishing_wide_takes_its_first_view(tmp_path):
    loc = tmp_path / "analysis" / "locations"
    loc.mkdir(parents=True)
    views = [{"id": "wide_space", "shot_size": "wide"}, {"id": "wide_pit", "shot_size": "wide"}]
    (loc / "space.json").write_text(json.dumps({"profile": {"design": {"views": views}}}))
    drawn = tmp_path / "refs" / "locations" / "space"
    drawn.mkdir(parents=True)
    for name in ("wide_space", "wide_pit"):
        (drawn / f"{name}.png").write_bytes(b"png")
    assert pack_refs.location_view(tmp_path, "space", "insert").name == "wide_space.png"


def test_an_undrawn_anchor_is_refused(tmp_path):
    book = _book(tmp_path)
    (book / "refs/locations/observatory/wide_establishing.png").unlink()
    with pytest.raises(SystemExit):
        pack_refs.location_view(book, "observatory", "wide")


def test_location_view_of_a_medium_falls_to_what_is_drawn(tmp_path):
    book = _book(tmp_path)
    got = pack_refs.location_view(book, "observatory", "medium")
    assert got.parent.name == "observatory" and got.exists()


def test_character_sheet_is_the_one_sheet(tmp_path):
    book = _book(tmp_path)
    assert pack_refs.character_sheet(book, "ogilvy") == book / "refs/characters/ogilvy/sheet.png"


def test_character_sheet_is_none_when_undrawn(tmp_path):
    assert pack_refs.character_sheet(_book(tmp_path), "stent") is None


def test_the_chapters_wardrobe_is_said_after_the_body(tmp_path):
    row = pack_refs.character_row(_book(tmp_path), "ogilvy", chapter=1)
    assert row["physical"].startswith("Man of 47, thickset, auburn beard.")
    assert "Ochre tweed Inverness cape" in row["physical"]
    assert "Shirtsleeves" not in row["physical"]
    assert row["rel_path"] == "refs/characters/ogilvy/sheet.png"
    assert row["kind"] == "character" and row["entity_id"] == "ogilvy"


def test_a_chapter_with_no_wardrobe_entry_takes_the_latest_earlier_one(tmp_path):
    book = _book(tmp_path)
    row = pack_refs.character_row(book, "ogilvy", chapter=2)
    assert "Ochre tweed" in row["physical"]
    row = pack_refs.character_row(book, "ogilvy", chapter=4)
    assert "Shirtsleeves" in row["physical"]
