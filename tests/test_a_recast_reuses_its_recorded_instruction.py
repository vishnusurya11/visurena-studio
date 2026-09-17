"""A recast re-renders; it does not re-write.

The instruction that made John Ferrier's clip is recorded in his sheet, and
the words were never the fault -- the RENDER was (self-similarity 0.498; a
VoiceDesign has no seed, so the same words give a different voice each time).
Writing it again would spend a paid reasoning call to arrive at the same sheet,
and the spend rule is that nothing is spent without an itemized go.  So a
recast reads the instruction back from the retired sheet and rolls again.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cast_voices_recast", ROOT / "scripts" / "cast" / "cast_voices.py")
cast_voices = importlib.util.module_from_spec(spec)
sys.modules["cast_voices_recast"] = cast_voices
spec.loader.exec_module(cast_voices)

INSTRUCTION = json.loads((ROOT / "tests" / "fixtures" / "voice_instruction_ferrier.json").read_text(encoding="utf-8"))


def voice_dir(tmp_path):
    room = tmp_path / "cast" / "john_ferrier" / "voice"
    room.mkdir(parents=True)
    return room


def test_the_retired_sheet_is_read_back(tmp_path):
    room = voice_dir(tmp_path)
    (room / "voice_v1.json").write_text(json.dumps({"instruction": INSTRUCTION}), encoding="utf-8")
    got = cast_voices.recorded_instruction(tmp_path, "john_ferrier")
    assert got is not None and got.character == "john_ferrier" and got.hertz() == 93


def test_the_latest_retired_sheet_wins(tmp_path):
    room = voice_dir(tmp_path)
    older = dict(INSTRUCTION, pitch=INSTRUCTION["pitch"].replace("93 Hz", "85 Hz"))
    (room / "voice_v1.json").write_text(json.dumps({"instruction": older}), encoding="utf-8")
    (room / "voice_v2.json").write_text(json.dumps({"instruction": INSTRUCTION}), encoding="utf-8")
    assert cast_voices.recorded_instruction(tmp_path, "john_ferrier").hertz() == 93


def test_a_live_sheet_is_read_when_nothing_is_retired(tmp_path):
    room = voice_dir(tmp_path)
    (room / "voice.json").write_text(json.dumps({"instruction": INSTRUCTION}), encoding="utf-8")
    assert cast_voices.recorded_instruction(tmp_path, "john_ferrier") is not None


def test_no_sheet_means_no_instruction(tmp_path):
    voice_dir(tmp_path)
    assert cast_voices.recorded_instruction(tmp_path, "john_ferrier") is None


def test_cast_one_does_not_write_when_it_can_read(tmp_path, monkeypatch):
    room = voice_dir(tmp_path)
    (room / "voice_v1.json").write_text(json.dumps({"instruction": INSTRUCTION}), encoding="utf-8")
    monkeypatch.setattr(cast_voices.voice_persona, "write",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("a paid write was made")))
    picked = cast_voices.Pick(room / "design.wav", 0.7, "brigham_young", 0.7, "", 101)
    monkeypatch.setattr(cast_voices, "audition", lambda *a, **k: picked)
    got = cast_voices.cast_one(tmp_path, {"id": "john_ferrier"}, "Utah", "1860", 93, {})
    assert got.hertz() == 93
    sheet = json.loads((room / "voice.json").read_text(encoding="utf-8"))
    assert sheet["register_rendered_hz"] == 101 and sheet["gates"]["nearest"] == "brigham_young"
