"""A book's registers are the book's data, not the caster's code (Jekyll ep01 review, 2026-10-13).

`PREFER` was A Study in Scarlet's register table living in book-neutral code
(CLAUDE.md: "the code tree names no book").  Every other book got the raw
allocator, which put Jekyll -- the second-heaviest part, a large man of fifty --
at the top of the male band (175 Hz).  A book now files the registers that are
decisions in `cast/registers.json`, and the pairs that must never sound alike
(Hyde is Jekyll: the ear must hear two men) with the ceiling they must stay under.

A recast that reads the recorded instruction is re-aimed at the filed register,
and an instruction authored by hand (`voice/instruction.json`) outranks the
recorded one, so a voice can be re-described without a paid writing call."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

from studio import voice_ear, voice_register

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cast_voices_data", ROOT / "scripts" / "cast" / "cast_voices.py")
cast_voices = importlib.util.module_from_spec(spec)
sys.modules["cast_voices_data"] = cast_voices
spec.loader.exec_module(cast_voices)

INSTRUCTION = json.loads((ROOT / "tests/fixtures/voice_instruction_ferrier.json").read_text(encoding="utf-8"))

FILED = {"registers": {"narrator": 105, "big_man": 116},
         "why": {"narrator": "calm low storyteller"},
         "apart": [{"pair": ["big_man", "small_man"], "below": 0.18, "ruler": "ecapa16",
                    "why": "one man, two bodies"}]}


def file_registers(book: Path, body: dict = FILED) -> Path:
    path = book / "cast" / "registers.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body), encoding="utf-8")
    return path


def test_the_filed_registers_are_read(tmp_path):
    file_registers(tmp_path)
    assert voice_register.registers_of(tmp_path) == {"narrator": 105, "big_man": 116}


def test_a_book_with_none_filed_has_none(tmp_path):
    assert voice_register.registers_of(tmp_path) == {}
    assert voice_register.ceilings_of(tmp_path, "big_man") == {}


def test_a_pair_ceiling_binds_both_ways(tmp_path):
    file_registers(tmp_path)
    assert voice_register.ceilings_of(tmp_path, "small_man") == {"big_man": 0.18}
    assert voice_register.ceilings_of(tmp_path, "big_man") == {"small_man": 0.18}
    assert voice_register.ceilings_of(tmp_path, "narrator") == {}


def test_the_caster_carries_no_books_table():
    assert not hasattr(cast_voices, "PREFER")
    source = (ROOT / "scripts/cast/cast_voices.py").read_text(encoding="utf-8")
    for name in ("brigham_young", "sherlock_holmes", "john_watson", "jefferson_hope"):
        assert name not in source


# ---- the pair gate --------------------------------------------------------------

def test_a_pair_over_its_ceiling_is_a_fault(tmp_path, monkeypatch):
    monkeypatch.setattr(voice_ear, "similarity", lambda a, b, device="": 0.60)
    why = cast_voices.pair_fault(tmp_path / "a.wav", {"big_man": tmp_path / "b.wav"}, {"big_man": 0.55})
    assert "big_man" in why and "0.60" in why and "0.55" in why


def test_a_pair_under_its_ceiling_or_absent_is_not(tmp_path, monkeypatch):
    monkeypatch.setattr(voice_ear, "similarity", lambda a, b, device="": 0.50)
    assert cast_voices.pair_fault(tmp_path / "a.wav", {"big_man": tmp_path / "b.wav"}, {"big_man": 0.55}) == ""
    assert cast_voices.pair_fault(tmp_path / "a.wav", {}, {"big_man": 0.55}) == ""


def test_an_audition_rolls_past_a_take_too_like_its_pair(tmp_path, monkeypatch):
    scores = iter([0.62, 0.48])
    monkeypatch.setattr(cast_voices, "CANDIDATES", 1)
    monkeypatch.setattr(voice_ear, "self_similarity", lambda clip, device="": 0.8)
    monkeypatch.setattr(voice_ear, "nearest", lambda clip, cast, device="": ("big_man", 0.6))
    monkeypatch.setattr(voice_ear, "similarity", lambda a, b, device="": next(scores))
    monkeypatch.setattr(cast_voices.voice_pitch, "f0_hz", lambda clip: 126.0)

    def render(instruct, dest, seed=0):
        sf.write(str(dest), np.zeros(1600, dtype="float32"), 16000)
        return dest

    got = cast_voices.audition(tmp_path, "small_man", "pitch: 126 Hz.", {"big_man": tmp_path / "b.wav"},
                               hertz=126, render=render, ceilings={"big_man": 0.55})
    assert got.fault == ""


# ---- the instruction is aimed at the filed register ----------------------------

def test_a_recorded_instruction_is_re_aimed_at_the_filed_register():
    got = cast_voices.voice_persona.VoiceInstruction.model_validate(INSTRUCTION)
    moved = cast_voices.retarget(got, 110)
    assert moved.hertz() == 110 and "93 Hz" not in moved.pitch
    assert cast_voices.retarget(got, 93) is got


def test_an_authored_instruction_outranks_the_recorded_one(tmp_path):
    room = tmp_path / "cast" / "john_ferrier" / "voice"
    room.mkdir(parents=True)
    (room / "voice_v1.json").write_text(json.dumps({"instruction": INSTRUCTION}), encoding="utf-8")
    authored = dict(INSTRUCTION, pitch=INSTRUCTION["pitch"].replace("93 Hz", "104 Hz"))
    (room / "instruction.json").write_text(json.dumps(authored), encoding="utf-8")
    assert cast_voices.recorded_instruction(tmp_path, "john_ferrier").hertz() == 104


def test_the_filed_register_beats_the_allocator(tmp_path):
    cards = [{"id": "big_man", "role": "protagonist", "appearances": 16},
             {"id": "lawyer", "role": "protagonist", "appearances": 20}]
    given = voice_register.assign(cards, lambda c: "male", {"big_man": 116})
    assert given["big_man"] == 116
