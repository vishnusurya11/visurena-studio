"""Each research run reads the library it has, and merges only styles it does not hold."""
from __future__ import annotations

import json

from prism.catalog import load_styles, write_style
from prism.research import brief, duplicate_of, merge, next_run
from tests.prism_fixtures import style


def test_the_brief_lists_every_held_style_so_research_skips_them():
    text = brief([style(), style("live_sin_city_noir", "Sin City noir")], run="r002")
    assert "anime_hellsing_gothic" in text and "live_sin_city_noir" in text
    assert "anime: 1" in text and "live_action: 1" in text
    assert "r002" in text


def test_a_same_id_is_a_duplicate():
    assert duplicate_of(style(name="Other"), [style()]) == "anime_hellsing_gothic"


def test_a_same_name_under_a_new_id_is_a_duplicate():
    assert duplicate_of(style("anime_hellsing_ova", "Hellsing  GOTHIC!"), [style()]) == "anime_hellsing_gothic"


def test_a_new_style_is_no_duplicate():
    assert duplicate_of(style("anime_ghibli", "Ghibli"), [style()]) is None


def test_merge_adds_the_new_and_refuses_the_held_and_the_broken(tmp_path):
    held, inbox = tmp_path / "styles", tmp_path / "inbox"
    held.mkdir(), inbox.mkdir()
    write_style(style(), held)
    write_style(style(), inbox)
    write_style(style("anime_ghibli", "Ghibli"), inbox)
    (inbox / "anime_bad.json").write_text(json.dumps({"id": "anime_bad"}), encoding="utf-8")
    added, refused = merge(inbox, held)
    assert added == ["anime_ghibli"]
    assert set(refused) == {"anime_hellsing_gothic.json", "anime_bad.json"}
    assert [s.id for s in load_styles(held)] == ["anime_ghibli", "anime_hellsing_gothic"]


def test_two_new_cards_of_one_style_in_one_inbox_merge_once(tmp_path):
    held, inbox = tmp_path / "styles", tmp_path / "inbox"
    held.mkdir(), inbox.mkdir()
    write_style(style("anime_ghibli", "Ghibli"), inbox)
    write_style(style("anime_ghibli_2", "Ghibli"), inbox)
    added, refused = merge(inbox, held)
    assert added == ["anime_ghibli"] and list(refused) == ["anime_ghibli_2.json"]


def test_the_next_run_follows_the_highest_held():
    assert next_run([]) == "r001"
    assert next_run([style(run="r001"), style("anime_b", "B", run="r003")]) == "r004"
