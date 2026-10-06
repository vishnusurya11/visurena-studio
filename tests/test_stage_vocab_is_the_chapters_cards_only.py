"""The G-STAGE vocabulary is the CHAPTER'S own machine cards plus the cast's
creature rows -- never the whole registry (alias head-noun false positives are
bounded by the card's `appears` chapter filter) and never an `object`-kind card
(a hatchet is scenery the prose may name freely).  tmp_path tree, $0."""
from __future__ import annotations

import json

from studio import pack_refs


def card(folder, pid, kind, chapter, name=None, aliases=(), physical="A thing of metal."):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{pid}.json").write_text(json.dumps({
        "id": pid, "name": name or pid, "kind": kind, "aliases": list(aliases),
        "appears": [{"chapter": chapter, "scene": 1, "shot": 0}],
        "profile": {"physical": physical}}), encoding="utf-8")


def test_stage_vocab_is_the_chapters_machine_cards_only(tmp_path):
    props = tmp_path / "analysis" / "props"
    card(props, "fighting_machine", "machine", 14, name="the Martian fighting-machine",
         aliases=["tripod", "Martian giant"])
    card(props, "digging_machine", "machine", 3, aliases=["digger"])
    card(props, "hatchet", "object", 14, aliases=["hatchet"])
    rows = [{"kind": "character", "entity_id": "martians", "name": "the Martians",
             "display": "the Martian", "gender": "creature"},
            {"kind": "character", "entity_id": "narrator", "name": "the Narrator",
             "gender": "male"}]
    vocab = pack_refs.stage_vocab(tmp_path, rows, 14)
    assert sorted(vocab["machines"]) == ["fighting_machine"]
    got = vocab["machines"]["fighting_machine"]
    assert got["name"] == "the Martian fighting-machine"
    assert "tripod" in got["terms"] and "giant" in got["terms"]
    assert got["physical"].startswith("A thing")
    assert vocab["creatures"] == {"martians": ["martian"]}


def test_a_vessel_card_enters_and_an_off_chapter_machine_does_not(tmp_path):
    props = tmp_path / "analysis" / "props"
    card(props, "thunder_child", "vessel", 17, aliases=["ironclad"])
    card(props, "flying_machine", "machine", 21, aliases=["flier"])
    vocab = pack_refs.stage_vocab(tmp_path, [], 17)
    assert sorted(vocab["machines"]) == ["thunder_child"]


def test_an_empty_book_is_an_empty_vocabulary(tmp_path):
    assert pack_refs.stage_vocab(tmp_path, [], 14) == {"machines": {}, "creatures": {}}


def test_creature_terms_reads_only_creature_rows():
    rows = [{"kind": "character", "entity_id": "martians", "name": "the Martians",
             "display": "A Martian", "gender": "creature"},
            {"kind": "character", "entity_id": "curate", "name": "the curate",
             "gender": "male"}]
    assert pack_refs.creature_terms(rows) == {"martians": ["martian"]}


def test_mask_card_names_blanks_the_phrase_and_keeps_indices():
    text = "The Martian fighting-machine wades; a martian stoops."
    out = pack_refs.mask_card_names(text, ["the Martian fighting-machine"])
    assert len(out) == len(text)
    assert "fighting" not in out and "a martian stoops" in out


def test_first_term_is_word_bounded_and_takes_plurals():
    assert pack_refs.first_term("two tripods stride", ["giant", "tripod"]) == "tripod"
    assert pack_refs.first_term("a tripodal gait", ["tripod"]) is None
