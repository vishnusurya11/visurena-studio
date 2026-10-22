"""A line must sound more like its own character than like anyone else in the cast.

2026-10-21 voice bench (VERDICT, X-S2 and step 3): an absolute floor cannot make the
gate on its own.  On the 16 kHz ruler today's floors still let 10 of 296 wrong voices
through, and a calm floor on every line stops them all but refuses 5 of 37 real lines.
Comparing a line with the REST of the cast does both jobs: the line's own design must
beat every other cast design by CAST_MARGIN.  The absolute floor stays as a backstop.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
VOICE = ROOT / "tests" / "fixtures" / "voice"
spec = importlib.util.spec_from_file_location("say_margin", ROOT / "scripts" / "episode" / "say_lines.py")
say = importlib.util.module_from_spec(spec)
sys.modules["say_margin"] = say
spec.loader.exec_module(say)


def cast_book(book: Path, voices: dict[str, Path]) -> Path:
    """A book whose cast/<who>/voice/design.wav are the given clips."""
    for who, clip in voices.items():
        room = book / "cast" / who / "voice"
        room.mkdir(parents=True, exist_ok=True)
        (room / "design.wav").write_bytes(Path(clip).read_bytes())
        (room / "design.txt").write_text("the passage", encoding="utf-8")
    return book


def blank(path: Path, seconds: float = 3.0) -> Path:
    sf.write(str(path), np.zeros(int(24000 * seconds), dtype="float32"), 24000)
    return path


SCORES = {"narrator": 0.62, "utterson": 0.70, "enfield": 0.20}
"""A planted wrong voice: a 'narrator' line that sounds like Utterson."""


def scripted(design: Path, clip: Path) -> float:
    return SCORES[Path(design).parent.parent.name]


def planted(tmp_path, monkeypatch) -> tuple[Path, list[dict]]:
    book = tmp_path / "book"
    cast_book(book, {who: blank(tmp_path / f"{who}.wav") for who in SCORES})
    blank(book / "l00.wav")
    monkeypatch.setattr(say.voice_ear, "similarity", scripted)
    return book, [{"index": 0, "rel_path": "l00.wav", "text": "good morning", "speaker": "narrator"}]


def test_the_margin_is_a_documented_constant():
    assert 0.0 < say.CAST_MARGIN < 0.3
    assert say.line_floor(5.0, "calm") > 0.0, "the absolute floor stays as the backstop"


def test_a_planted_wrong_voice_is_refused_in_the_gates_words(tmp_path, monkeypatch):
    book, records = planted(tmp_path, monkeypatch)
    monkeypatch.setattr(say, "line_floor", lambda seconds, delivery: 0.30)     # the floor alone would pass it
    assert say.listen_all(records, book, lambda clip: "good morning") == [0]
    why = records[0]["voice_why"]
    assert "utterson" in why and "narrator" in why and f"{say.CAST_MARGIN:.2f}" in why
    assert records[0]["rival"] == "utterson" and records[0]["margin"] == pytest.approx(-0.08)


def test_a_line_that_leads_the_cast_by_the_margin_passes(tmp_path, monkeypatch):
    book, records = planted(tmp_path, monkeypatch)
    monkeypatch.setitem(SCORES, "narrator", 0.70 + say.CAST_MARGIN)
    monkeypatch.setattr(say, "line_floor", lambda seconds, delivery: 0.30)
    assert say.listen_all(records, book, lambda clip: "good morning") == []
    assert records[0]["voice_why"] == ""


def test_a_line_under_the_floor_is_refused_by_the_backstop(tmp_path, monkeypatch):
    book, records = planted(tmp_path, monkeypatch)
    monkeypatch.setitem(SCORES, "utterson", 0.10)
    monkeypatch.setattr(say, "line_floor", lambda seconds, delivery: 0.65)
    assert say.listen_all(records, book, lambda clip: "good morning") == [0]
    assert "floor" in records[0]["voice_why"]


def test_a_line_too_short_to_measure_is_not_held_to_the_margin():
    assert say.margin_ok(("utterson", -0.3), say.SIM_MEASURABLE_S - 0.1)
    assert not say.margin_ok(("utterson", -0.3), say.SIM_MEASURABLE_S)


def test_a_book_with_no_other_voice_has_no_margin(tmp_path):
    assert say.cast_margin(tmp_path, "narrator", tmp_path / "l00.wav", 0.8) is None
    assert say.margin_ok(None, 5.0)


@pytest.mark.local
def test_every_real_fixture_line_leads_its_cast(tmp_path):
    """Jekyll ep01's own lines against four of its cast designs, trimmed (tests/fixtures/voice)."""
    book = cast_book(tmp_path, {w: VOICE / f"{w}_design.wav" for w in ("narrator", "enfield", "utterson", "hyde")})
    for line, who in (("narrator_l02", "narrator"), ("enfield_l08", "enfield"),
                      ("utterson_l16", "utterson"), ("hyde_l10", "hyde")):
        clip = VOICE / f"{line}.wav"
        own = say.voice_ear.similarity(book / "cast" / who / "voice" / "design.wav", clip, "cpu")
        rival, margin = say.cast_margin(book, who, clip, own)
        assert margin >= say.CAST_MARGIN, (line, rival, margin)


@pytest.mark.local
def test_a_real_line_said_in_the_wrong_voice_is_refused(tmp_path):
    """The narrator's l02 filed as Utterson's line: Utterson's design is not its nearest."""
    book = cast_book(tmp_path, {w: VOICE / f"{w}_design.wav" for w in ("narrator", "enfield", "utterson", "hyde")})
    clip = VOICE / "narrator_l02.wav"
    own = say.voice_ear.similarity(book / "cast" / "utterson" / "voice" / "design.wav", clip, "cpu")
    rival, margin = say.cast_margin(book, "utterson", clip, own)
    assert rival == "narrator" and not say.margin_ok((rival, margin), 4.0)
