"""Lines are rendered together and listened to together; failures come back by index."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_say", ROOT / "scripts" / "episode" / "say_lines.py")
say = importlib.util.module_from_spec(spec)
sys.modules["ep_say"] = say
spec.loader.exec_module(say)


def test_listen_all_marks_each_record_and_returns_the_failures(tmp_path, monkeypatch):
    import soundfile as sf
    import numpy as np
    for name in ("a.wav", "b.wav"):
        sf.write(tmp_path / name, np.zeros(2400, dtype="float32"), 24000)
    records = [{"index": 0, "rel_path": "a.wav", "text": "good morning"},
               {"index": 1, "rel_path": "b.wav", "text": "good morning"}]
    heard = {"a.wav": "good morning", "b.wav": "something else entirely"}
    monkeypatch.setattr(say, "reference_for", lambda book, who: tmp_path / "a.wav")
    monkeypatch.setattr(say.voice_ear, "similarity", lambda ref, clip: 0.9)
    for r in records:
        r["speaker"] = "x"
    failed = say.listen_all(records, tmp_path, lambda clip: heard[Path(clip).name])
    assert failed == [1]
    assert records[0]["passed"] and not records[1]["passed"]


def test_a_line_that_is_not_the_character_fails_even_if_the_words_are_right(tmp_path, monkeypatch):
    import soundfile as sf
    import numpy as np
    sf.write(tmp_path / "a.wav", np.zeros(2400, dtype="float32"), 24000)
    records = [{"index": 0, "rel_path": "a.wav", "text": "good morning", "speaker": "x"}]
    monkeypatch.setattr(say, "reference_for", lambda book, who: tmp_path / "a.wav")
    monkeypatch.setattr(say.voice_ear, "similarity", lambda ref, clip: 0.4)
    assert say.listen_all(records, tmp_path, lambda clip: "good morning") == [0]


def test_seeds_differ_per_attempt():
    from studio.episode_spec import Line
    line = Line(index=3, kind="narration", speaker="a", text="x", shot=0)
    assert say.seed_for(1, line, 0) != say.seed_for(1, line, 1)
