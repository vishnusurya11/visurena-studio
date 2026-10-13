"""Jekyll ep01 l12 (2026-10-13): Whisper heard "And Field said" for "Enfield
said" -- a name the ear does not know, not a bad recording (sim 0.82). A book
files its known mishearings once; the ear reads them before scoring."""
from __future__ import annotations

import json

from studio import voice_qc


def test_a_known_mishearing_is_read_as_the_name():
    assert voice_qc.heard_as("And Field said it was", {"and field": "Enfield"}) == "Enfield said it was"


def test_only_whole_phrases_are_replaced():
    assert voice_qc.heard_as("a grandfield sale", {"and field": "Enfield"}) == "a grandfield sale"


def test_the_lexicon_lifts_the_line_under_the_wall():
    heard = voice_qc.heard_as("And Field said it was like watching", {"and field": "Enfield"})
    assert voice_qc.error_rate(heard, "Enfield said it was like watching") == 0.0


def test_a_book_without_a_lexicon_hears_as_before(tmp_path):
    assert voice_qc.ear_lexicon(tmp_path) == {}
    (tmp_path / "cast").mkdir()
    (tmp_path / "cast" / "ear_lexicon.json").write_text(json.dumps({"and field": "Enfield"}))
    assert voice_qc.ear_lexicon(tmp_path) == {"and field": "Enfield"}


def test_the_wrapped_ear_corrects_what_it_hears(tmp_path):
    ear = voice_qc.with_lexicon(lambda clip: "And Field said", {"and field": "Enfield"})
    assert ear(tmp_path / "x.wav") == "Enfield said"
