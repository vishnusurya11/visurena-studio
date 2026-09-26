"""A book scores its own bed (root cause 2026-09-26, D10).

The episode tones were written for A Study in Scarlet -- "the instrument stays
the violin, because Holmes plays one", every tag ending "Victorian London" -- and
War of the Worlds inherited them: an artillery battle scored by a quiet violin.
`library/<book>/audio/bed_tones.json` replaces any tone's words, tempo, key or level."""
from __future__ import annotations

import json

from scripts.episode import assemble as asm
from studio import episode_bed as eb


def book_with(tmp_path, doc):
    (tmp_path / "audio").mkdir(parents=True)
    (tmp_path / "audio" / "bed_tones.json").write_text(json.dumps(doc), encoding="utf-8")
    return tmp_path


def test_no_file_keeps_the_house_tones(tmp_path):
    assert eb.tones_for(tmp_path) == eb.TONES


def test_a_book_file_replaces_a_tones_words_and_keeps_the_rest(tmp_path):
    book = book_with(tmp_path, {"thrilling": {"tags": "orchestral war drums, low brass, timpani", "bpm": 104}})
    tones = eb.tones_for(book)
    assert tones["thrilling"].tags == "orchestral war drums, low brass, timpani" and tones["thrilling"].bpm == 104
    assert tones["thrilling"].key == eb.TONES["thrilling"].key and tones["plain"] == eb.TONES["plain"]


def test_a_book_may_add_a_tone(tmp_path):
    book = book_with(tmp_path, {"battle": {"style": "war", "tags": "war drums", "bpm": 120,
                                           "key": "C minor", "lufs": -26.0}})
    assert eb.tones_for(book)["battle"].bpm == 120


def test_the_request_is_built_from_the_books_tones(tmp_path):
    book = book_with(tmp_path, {"grave": {"tags": "low strings and a distant bell"}})
    _name, values = asm.bed_request("acestep", 60.0, 1, "grave", tones=eb.tones_for(book))
    assert values["tags"] == "low strings and a distant bell"


def test_a_bed_file_finds_its_books_tones(tmp_path):
    book = book_with(tmp_path, {"grave": {"lufs": -33.0}})
    out = book / "episodes" / "ep13" / "audio" / "bed_grave.wav"
    assert asm.book_tones(out)["grave"].lufs == -33.0
