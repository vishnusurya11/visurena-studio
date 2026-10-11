"""The look-table writer takes a silent head from the bound row (C2_verdict #6).

Three measured faults kept Scarlet from ever having a look table:
- `dossier_text` did `min(card['appearances'])`, and `appearances` is a COUNT in
  every real dossier (Scarlet, WotW, Jekyll): the writer path crashed before the
  head check ran; the test fixture had typed a list by hand;
- 11 of Scarlet's 26 bound rows have no dossier at all;
- 9 of its 15 dossiers name no head, while 26/26 refs.json rows do -- the bound
  sheet was drawn from those words.
The head now falls back, per layer, to the bound row's `physical`; a row with no
dossier becomes one look per refs.json card.  Jekyll and Hyde, whose rows are
headless too, are still refused."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.refs import looks_table
from studio import episode_home, look_timeline

SCARLET = "20260822113400_a-study-in-scarlet"
WOTW = "20260827135508_the-war-of-the-worlds"
JEKYLL = "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"
HOLMES_ROW = "A man of about thirty, very tall and lean, dark hair swept back, clean-shaven, a grey frock coat."
WATSON = {"entity_id": "john_watson",
          "physical": "A man in his late twenties, thin, dark hair swept back, a thin waxed moustache, a tweed waistcoat.",
          "wardrobe": {"outdoor": "wears the brown bowler hat squarely on his head and a brown tweed overcoat",
                       "indoor": "is bare-headed in his shirtsleeves and tweed waistcoat"}}


def book_or_skip(name: str) -> Path:
    book = episode_home.book_dir(name)
    if not (book / "refs" / "refs.json").exists():
        pytest.skip(f"{name} is not on this machine")
    return book


def test_dossier_text_reads_first_chapter_on_a_real_dossier():
    book = book_or_skip(SCARLET)
    card = looks_table.card_of(book, "jefferson_hope")
    assert isinstance(card["appearances"], int)                      # a count, never a list
    assert f"FIRST SEEN: chapter {card['first_chapter']}" in look_timeline.dossier_text(card)


def test_a_silent_dossier_head_is_filled_from_the_bound_row_per_layer():
    layers = look_timeline.with_head(look_timeline.Layers(top="grey frock coat"), "Very tall and lean.",
                                     fallback=HOLMES_ROW)
    assert "dark hair" in layers.hair and "clean-shaven" in layers.face.lower()
    markers = look_timeline.markers_from(layers, "Very tall and lean.", fallback=HOLMES_ROW)
    assert (markers.hair_colour, markers.facial_hair) == ("dark", "none")      # clean-shaven


def test_the_bound_rows_hat_is_never_taken():
    """A row's physical carries one chapter's costume: its hat is not the body's."""
    layers = look_timeline.with_head(look_timeline.Layers(), "Tall.", fallback="Grey hair. Wearing: Straw gardening hat.")
    assert layers.headwear == "" and "Grey hair" in layers.hair


def test_the_dossier_head_wins_where_it_speaks():
    layers = look_timeline.with_head(look_timeline.Layers(), "Tall. Sandy hair cut short.", fallback=HOLMES_ROW)
    assert "Sandy hair" in layers.hair and "clean-shaven" in layers.face.lower()


def test_a_row_with_no_dossier_is_one_look_per_card():
    looks = look_timeline.looks_from_cards(WATSON)
    assert list(looks.looks) == ["outdoor", "indoor"] and looks.base == "outdoor"
    assert looks.looks["outdoor"].markers.headwear == "bowler"
    assert looks.looks["indoor"].markers.headwear == "none"
    assert look_timeline.head_refusal("john_watson", looks) is None


def test_table_for_builds_a_dossierless_row_from_its_cards(tmp_path):
    (tmp_path / "refs").mkdir()
    (tmp_path / "refs" / "refs.json").write_text(json.dumps({"refs": [WATSON]}), encoding="utf-8")
    looks = looks_table.table_for(tmp_path, "john_watson")
    assert sorted(looks.looks) == ["indoor", "outdoor"]


def test_the_wotw_tables_are_byte_identical_with_the_fallback():
    book = book_or_skip(WOTW)
    for row in looks_table.rows(book):
        path = book / "analysis" / "characters" / f"{row['entity_id']}.json"
        card = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        if card is None or look_timeline.looks_from_dossier(card) is None:
            continue
        plain = look_timeline.looks_from_dossier(card).model_dump_json()
        assert look_timeline.looks_from_dossier(card, fallback=row.get("physical", "")).model_dump_json() == plain


@pytest.mark.parametrize("who", ["henry_jekyll", "edward_hyde"])
def test_jekyll_and_hyde_are_still_refused(who, monkeypatch):
    """Their refs.json rows name no head either: the wall stays where C1 put it."""
    from agents import look_timeline_writer as writer
    book = book_or_skip(JEKYLL)
    headless = writer.LookDraft.model_validate({"looks": [{"look_id": "base", "start_chapter": 1, "top": "dark coat",
                                                           "quote": "", "quote_chapter": 1}]})
    monkeypatch.setattr(writer, "write", lambda text, _agent=None: headless)
    looks = looks_table.table_for(book, who)
    assert "head unauthored" in (look_timeline.head_refusal(who, looks) or "")
