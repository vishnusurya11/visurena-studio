"""The look-back: a drawn picture read against the nouns its own prompt asked for.

The reader LISTS (a closed question, no yes/no); the nouns come from the prompt
by a small deterministic rule; the comparison is code.  Advisory this pass.
"""
from __future__ import annotations

import json

import pytest

from agents import look_back as agent
from studio import look_back


def test_nouns_after_with_holding_wearing_are_the_heads_of_their_phrases():
    prompt = "A tall man with a black beard, wearing a top hat and a long cape, holding a brass lantern."
    assert look_back.nouns_of(prompt) == ["beard", "hat", "cape", "lantern"]


def test_a_capitalised_word_asks_for_the_thing_it_qualifies_and_a_sentence_start_is_not():
    prompt = "Character reference sheet. The man carries a Gladstone bag."
    assert look_back.nouns_of(prompt) == ["bag"]


def test_a_name_asks_for_nothing():
    """The first real bible's 39 misses were names, countries and ranks."""
    prompt = "Albin Blythe, a lieutenant of the Royal Navy, home from England, in a blue coat."
    assert look_back.nouns_of(prompt) == []
    assert look_back.nouns_of("Old Albin, on the Kent road at dusk.") == ["road"]


def test_a_must_word_present_in_the_prompt_is_asked_for_and_an_absent_one_is_not():
    prompt = "A woman in a grey shawl by a window."
    assert look_back.nouns_of(prompt, must=("shawl", "window", "lantern")) == ["shawl", "window"]


def test_nouns_are_unique_and_keep_first_appearance_order():
    prompt = "A man with a cane, holding a cane, wearing a coat."
    assert look_back.nouns_of(prompt) == ["cane", "coat"]


def test_diff_is_every_asked_noun_whose_stem_no_seen_phrase_carries():
    seen = ["a bearded man", "two top hats", "a stone wall"]
    assert look_back.diff(seen, ["hat", "beard", "cape", "wall"]) == ["beard", "cape"]


def test_parse_unwraps_the_caption_workflows_list_of_one_json_string():
    said = json.dumps([json.dumps({"seen": ["a man", "a hat"], "text": "false"})])
    assert look_back.parse(said) == (["a man", "a hat"], False)


def test_parse_refuses_an_answer_with_no_list():
    with pytest.raises(look_back.Unreadable):
        look_back.parse("I cannot see the picture.")


def test_read_with_a_fake_reader_names_what_is_missing(tmp_path):
    picture = tmp_path / "sheet.png"
    picture.write_bytes(b"png")
    asked = []

    def reader(path, question):
        asked.append((path, question))
        return json.dumps({"seen": ["a man in a coat", "a lantern"], "text": True})

    reading = look_back.read(picture, "A man wearing a coat, holding a lantern and a cane.", reader=reader)
    assert reading.seen == ["a man in a coat", "a lantern"]
    assert reading.missing == ["cane"]
    assert reading.text is True
    assert asked[0][0] == picture and "absent" in asked[0][1].lower()


def test_the_agent_returns_the_same_reading_and_a_must_list_widens_the_ask(tmp_path):
    picture = tmp_path / "sheet.png"
    picture.write_bytes(b"png")
    reader = lambda path, question: json.dumps({"seen": ["a horse"], "text": False})
    reading = agent.look(picture, "A cart on a road.", reader=reader, must=("cart", "road"))
    assert isinstance(reading, agent.LookReading)
    assert reading.missing == ["cart", "road"] and reading.text is False


def test_an_adjective_series_asks_for_the_noun_it_qualifies():
    """Jekyll Kawajiri LOOK (2026-10-18): 'with lean, corded, knuckly pale hands' asked for 'lean' and
    'with a full, broad, smooth face' for 'full' -- the phrase was cut at the series' first comma."""
    assert look_back.nouns_of("A pale man with lean, corded, knuckly pale hands.") == ["hands"]
    assert look_back.nouns_of("A man of fifty with a full, broad, smooth face and white hands.") == ["face", "hands"]
    assert look_back.nouns_of("A man with a hat, coat and gloves.") == ["hat"]


def test_a_noun_the_reader_does_not_list_but_does_not_call_absent_is_not_missing(tmp_path):
    """The question asks the reader which asked nouns are ABSENT; its answer is part of the reading.
    Utterson's Kawajiri sheet: the band is drawn, the reader listed 'hat' and answered absent: []."""
    picture = tmp_path / "sheet.png"
    picture.write_bytes(b"png")
    said = json.dumps({"seen": ["man", "hat", "coat"], "text": False, "absent": ["cane"]})
    reading = look_back.read(picture, "A man wearing a hat with a band, holding a cane.", reader=lambda p, q: said)
    assert reading.missing == ["cane"]


def test_an_answer_without_an_absent_list_keeps_the_seen_rule(tmp_path):
    picture = tmp_path / "sheet.png"
    picture.write_bytes(b"png")
    said = json.dumps({"seen": ["man", "hat"], "text": False})
    reading = look_back.read(picture, "A man wearing a hat with a band.", reader=lambda p, q: said)
    assert reading.missing == ["band"]


def test_the_skill_asks_the_one_question_without_naming_a_book():
    text = agent.load_skill().lower()
    assert "absent" in text and "list" in text
