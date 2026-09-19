"""A references-only take on a book drawn with the pack layout.

OWNER 2026-09-18 (The War of the Worlds, episode 1): no storyboard and no
composed first frame.  Each take is handed the reference pictures themselves --
the location's ONE picture, its establishing wide (owner, 2026-09-18), and the one sheet of every person
in the shot -- and everything else is said in words.  The pack's look is not
photoreal (Krea2 + the cinematic artstyle LoRA), so the take's style line says
the book's own look instead of "Photoreal live-action".
"""
import json
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, "scripts/episode")

import takes_r2v  # noqa: E402
from studio import episode_ref_official as ro  # noqa: E402
from studio import episode_seq_board as sq  # noqa: E402
from studio import house_style  # noqa: E402
from studio.episode_spec import Episode, Shot  # noqa: E402

VIEWS = [{"id": "wide_establishing", "shot_size": "wide"},
         {"id": "insert_eyepiece_field", "shot_size": "insert"},
         {"id": "medium_little_table", "shot_size": "medium"}]


def _book(tmp_path):
    loc = tmp_path / "analysis" / "locations"
    loc.mkdir(parents=True)
    (loc / "ottershaw_observatory.json").write_text(json.dumps({"profile": {"design": {"views": VIEWS}}}))
    drawn = tmp_path / "refs" / "locations" / "ottershaw_observatory"
    drawn.mkdir(parents=True)
    for v in VIEWS:
        (drawn / f"{v['id']}.png").write_bytes(b"png")
    sheet = tmp_path / "refs" / "characters" / "ogilvy"
    sheet.mkdir(parents=True)
    (sheet / "sheet.png").write_bytes(b"png")
    return tmp_path


def test_a_pack_book_opens_every_size_on_the_one_wide(tmp_path):
    book = _book(tmp_path)
    setup = SimpleNamespace(location="ottershaw_observatory")
    shot = SimpleNamespace(size="insert", view="")
    got = takes_r2v.location_picture(book, tmp_path / "boards", setup, "observatory", shot)
    assert got == book / "refs/locations/ottershaw_observatory/wide_establishing.png"


def test_a_shot_may_name_its_view(tmp_path):
    book = _book(tmp_path)
    setup = SimpleNamespace(location="ottershaw_observatory")
    shot = SimpleNamespace(size="medium_close", view="wide_establishing")
    got = takes_r2v.location_picture(book, tmp_path / "boards", setup, "observatory", shot)
    assert got.name == "wide_establishing.png"


def test_a_book_without_the_pack_keeps_its_loc_picture(tmp_path):
    (tmp_path / "refs" / "locations").mkdir(parents=True)
    (tmp_path / "refs" / "locations" / "loc-221b.png").write_bytes(b"png")
    setup = SimpleNamespace(location="221b")
    got = takes_r2v.location_picture(tmp_path, tmp_path / "boards", setup, "sitting_room",
                                     SimpleNamespace(size="wide", view=""))
    assert got.name == "loc-221b.png"


def test_the_cast_sheet_falls_to_the_packs_one_sheet(tmp_path):
    book = _book(tmp_path)
    assert sq.cast_sheet(book, "ogilvy", "observatory", "indoor") == book / "refs/characters/ogilvy/sheet.png"


def test_a_drawn_card_still_wins_over_the_pack_sheet(tmp_path):
    book = _book(tmp_path)
    (book / "refs/characters/char-ogilvy_indoor.png").write_bytes(b"png")
    assert sq.cast_sheet(book, "ogilvy", "observatory", "indoor").name == "char-ogilvy_indoor.png"


def test_the_book_declares_display_names_and_women(tmp_path):
    rows = [{"kind": "character", "entity_id": "narrators_wife", "display": "the Wife", "gender": "female"},
            {"kind": "character", "entity_id": "ogilvy"}]
    takes_r2v.adopt_names(rows)
    try:
        assert ro.name_of("narrators_wife") == "the Wife" and "narrators_wife" in ro.WOMEN
        assert ro.name_of("ogilvy") == "Ogilvy"
    finally:
        takes_r2v.adopt_names([])
    assert ro.DISPLAY == {} and ro.WOMEN == set()


def test_the_narrator_is_whoever_speaks_the_narration():
    lines = [SimpleNamespace(kind="dialogue", speaker="ogilvy"),
             SimpleNamespace(kind="narration", speaker="unnamed_first_person_narrator")]
    assert takes_r2v.narrator_of(lines) == "unnamed_first_person_narrator"
    assert takes_r2v.narrator_of([]) == takes_r2v.NARRATOR


def test_the_look_replaces_photoreal_in_the_take_line():
    house_style.adopt_look("Angular stylised 3D animation")
    try:
        assert house_style.live().startswith("Angular stylised 3D animation, ")
        assert "Photoreal" not in house_style.live()
    finally:
        house_style.adopt_look("")
    assert house_style.live().startswith("Photoreal live-action, ")


def test_the_plan_carries_a_view_and_a_look():
    assert "view" in Shot.model_fields and Shot.model_fields["view"].default == ""
    assert "look" in Episode.model_fields and Episode.model_fields["look"].default == ""


def test_a_pack_picture_is_recorded_by_its_book_path(tmp_path):
    """Every sheet in the pack is called `sheet.png`: a bare name cannot say whose."""
    book = _book(tmp_path)
    sheet = book / "refs" / "characters" / "ogilvy" / "sheet.png"
    assert takes_r2v.ref_name(book, sheet) == "refs/characters/ogilvy/sheet.png"


def test_a_flat_picture_keeps_its_bare_name(tmp_path):
    assert takes_r2v.ref_name(tmp_path, tmp_path / "refs" / "characters" / "char-x.png") == "char-x.png"
    assert takes_r2v.ref_name(tmp_path, tmp_path / "boards" / "plates" / "plate_a.png") == "plate_a.png"


def test_a_book_path_routes_back_to_the_book(tmp_path):
    got = sq.picture_path(tmp_path / "boards", tmp_path, "refs/locations/ottershaw/reverse.png")
    assert got == tmp_path / "refs" / "locations" / "ottershaw" / "reverse.png"
