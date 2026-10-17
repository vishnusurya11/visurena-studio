"""The writer is told every number the grammar measures (feedback 'walls follow
the chapter', 2026-10-07: a number the brief never stated cost a ladder rung
each time), the chapter's own dialogue band, and the book's motif.  $0."""
from __future__ import annotations

import json

from studio import grammar_battery, plan_brief


def test_the_band_carries_the_grammar_table():
    band = plan_brief.band()
    for key, value in grammar_battery.band().items():
        assert band["grammar_rules"][key] == value
    assert band["grammar"] == "anime_tv" and band["grammar_rules"]["max_shots"] == 30


def _chapter(book, speech_words: int, other_words: int):
    folder = book / "source" / "chapters"
    folder.mkdir(parents=True)
    said = '"' + " ".join(["said"] * speech_words) + '," he said.'
    doc = {"title": "One", "paragraphs": [{"text": said}, {"text": " ".join(["plain"] * other_words)}]}
    (folder / "ch_01.json").write_text(json.dumps(doc), encoding="utf-8")


def test_the_dialogue_band_is_the_chapters(tmp_path):
    _chapter(tmp_path, 60, 40)
    low, high = plan_brief.band(tmp_path, 1)["dialogue_share"]
    assert low == 0.05 and high == 0.35


def test_a_book_without_a_chapter_keeps_the_default_band(tmp_path):
    assert plan_brief.band(tmp_path, 1)["dialogue_share"] == [0.05, 0.20]


def test_the_motif_is_the_series_then_the_first_episodes(tmp_path):
    assert plan_brief.book_motif(tmp_path) == ""
    home = tmp_path / "episodes" / "ep01"
    home.mkdir(parents=True)
    (home / "plan.json").write_text(json.dumps({"motif": "the blind door"}), encoding="utf-8")
    assert plan_brief.book_motif(tmp_path) == "the blind door"
    (tmp_path / "series.json").write_text(json.dumps({"motif": "the lamp"}), encoding="utf-8")
    assert plan_brief.book_motif(tmp_path) == "the lamp"
