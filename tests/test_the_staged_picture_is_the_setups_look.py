"""The grid slot, the take slot and the words all name the setup's look: its
own pick, else the bound row's chapter look (decision 2026-10-10)."""
from __future__ import annotations

from types import SimpleNamespace

from studio import continuity, episode_seq_board as sq
from tests import continuity_fixtures as fx

from scripts.episode import grids, takes_r2v


def test_the_pick_outranks_the_rows_chapter_look():
    setup = SimpleNamespace(looks=[SimpleNamespace(who="narrator", look="borrowed")])
    assert continuity.look_for(setup, "narrator", {"look": "ragged"}) == "borrowed"
    assert continuity.look_for(SimpleNamespace(looks=[]), "narrator", {"look": "ragged"}) == "ragged"


def test_the_grid_stages_the_look_picture(tmp_path):
    book = fx.book(tmp_path)
    assert grids.sheet_of(book, "narrator", "ragged").parent.name == "looks"


def test_the_take_slot_stages_the_look_picture(tmp_path):
    book = fx.book(tmp_path)
    assert sq.cast_sheet(book, "narrator", "s", "indoor", look="ragged").name == "ragged.png"
    refs = takes_r2v.reference_list(book, tmp_path, ["narrator"], "s", [], [], tmp_path / "strip.png",
                                    looks={"narrator": "ragged"})
    assert refs[0].name == "ragged.png"


def test_the_words_follow_a_pick_off_the_rows_look(tmp_path):
    book = fx.book(tmp_path)
    row = {"look": "ragged", "physical": "Grey beard. Man of 34.", "markers": {"hair_colour": "grey"}}
    assert continuity.words_for(book, "narrator", "ragged", row) == row["physical"]
    said = continuity.words_for(book, "narrator", "day_suit", row)
    assert said.startswith("Dark brown hair") and "Man of 34, slender" in said
    assert continuity.markers_for(book, "narrator", "day_suit", row)["hair_colour"] == "dark"


def test_a_book_without_a_table_keeps_the_row(tmp_path):
    book = fx.book(tmp_path, table=False)
    row = {"look": "ragged", "physical": "Grey beard."}
    assert continuity.words_for(book, "narrator", "day_suit", row) == "Grey beard."


def test_the_grid_stages_a_look_picture_wherever_it_lives(tmp_path, monkeypatch):
    """2026-10-10 replay: a look saved outside refs/.../looks/ was taken for the
    base sheet by its folder name, and the grid staged the clean ep01 suit."""
    book = fx.book(tmp_path)
    elsewhere = tmp_path / "replay" / "narrator" / "ragged.png"
    elsewhere.parent.mkdir(parents=True)
    elsewhere.write_bytes((book / "refs" / "characters" / "narrator" / "looks" / "ragged.png").read_bytes())
    monkeypatch.setattr(grids.pack_refs, "look_sheet", lambda b, who, look: elsewhere)
    assert grids.sheet_of(book, "narrator", "ragged") == elsewhere
