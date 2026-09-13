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


def test_a_redo_that_scores_lower_than_the_try_before_is_thrown_away(tmp_path):
    """l21 went 0.69 -> 0.64 -> 0.66 -> 0.64 on redo; the best try is the one kept."""
    wav = tmp_path / "l21.wav"; wav.write_bytes(b"new")
    kept = tmp_path / "l21.prev.wav"; kept.write_bytes(b"old")
    previous = {"index": 21, "similarity": 0.69, "passed": False, "seconds": 2.9}
    new = {"index": 21, "similarity": 0.64, "passed": False, "seconds": 2.6}
    best = say.keep_best(new, previous, wav)
    assert best["similarity"] == 0.69 and wav.read_bytes() == b"old" and not kept.exists()
    wav.write_bytes(b"new"); kept.write_bytes(b"old")
    best = say.keep_best({"index": 21, "similarity": 0.72, "passed": True}, previous, wav)
    assert best["similarity"] == 0.72 and wav.read_bytes() == b"new" and not kept.exists()


def test_a_stubborn_line_is_cloned_from_the_speakers_best_passed_line():
    """Audio reviewer, iteration 3: l21 measured closer to Watson's design voice than
    Stamford's after six seeds from the design clip; Stamford's own l00 (0.795) is the
    better reference for his second line."""
    records = {0: {"speaker": "stamford", "similarity": 0.795, "passed": True, "rel_path": "episodes/ep01/lines/l00.wav"},
               21: {"speaker": "stamford", "similarity": 0.66, "passed": False, "rel_path": "episodes/ep01/lines/l21.wav"},
               13: {"speaker": "sherlock_holmes", "similarity": 0.9, "passed": True, "rel_path": "x"}}
    assert say.best_line_reference(records, "stamford", exclude=21) == 0
    assert say.best_line_reference(records, "john_watson", exclude=None) is None
    assert say.best_line_reference({0: dict(records[0], similarity=0.71)}, "stamford", exclude=None) is None  # below 0.75
