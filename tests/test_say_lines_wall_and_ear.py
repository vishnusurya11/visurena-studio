"""The lines wall and the phoneme-equal ear (P11, Jekyll ep01 l11: 'check' heard for 'cheque' x8)."""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import soundfile as sf

from studio import step_attempts
from studio.episode_spec import Line

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_say_wall", ROOT / "scripts" / "episode" / "say_lines.py")
say = importlib.util.module_from_spec(spec)
sys.modules["ep_say_wall"] = say
spec.loader.exec_module(say)

TEXT = "Gold, and a cheque."


def seed(tmp_path, monkeypatch, record, wall=600.0):
    """A one-line episode on disk; every outside edge faked."""
    lines = tmp_path / "episodes" / "ep01" / "audio" / "lines"
    lines.mkdir(parents=True)
    sf.write(lines / "l00.wav", np.zeros(48000, dtype="float32"), 24000)
    (lines / "lines.json").write_text(json.dumps([record]), encoding="utf-8")
    plan = SimpleNamespace(number=1, lines=[Line(index=0, kind="narration", speaker="a", text=record["text"], shot=0)])
    monkeypatch.setattr(say.episode_home, "book_dir", lambda _id: tmp_path)
    monkeypatch.setattr(say.episode_home, "load_plan", lambda book, n: plan)
    monkeypatch.setattr(say, "lines_wall_s", lambda: wall)
    monkeypatch.setattr(say.voice_qc, "any_transcriber", lambda: (lambda clip: "Gold and a check."))
    monkeypatch.setattr(say, "reference_for", lambda book, who: lines / "l00.wav")
    monkeypatch.setattr(say.voice_ear, "similarity", lambda a, b: 0.9)
    return tmp_path / "episodes" / "ep01", lines


def failing(**over):
    return {"index": 0, "speaker": "a", "kind": "narration", "shot": 0, "text": TEXT, "seconds": 2.0,
            "rel_path": "episodes/ep01/audio/lines/l00.wav", "tries": 3, "passed": False, "words_ok": True,
            "similarity": 0.5, "floor": 0.65, "error_rate": 0.0, "heard": "x", "why": "w", **over}


def no_render(monkeypatch):
    calls = []
    monkeypatch.setattr(say, "render", lambda *a, **k: calls.append(1) or (_ for _ in ()).throw(RuntimeError("rendered")))
    return calls


def test_a_spent_lines_wall_keeps_the_best_try_flagged_and_renders_nothing(tmp_path, monkeypatch, capsys):
    home, lines = seed(tmp_path, monkeypatch, failing(), wall=10.0)
    step_attempts.spend(home, "lines", 11.0)
    calls = no_render(monkeypatch)
    say.main("x", 1)                                             # returns: no SystemExit
    row = json.loads((lines / "lines.json").read_text(encoding="utf-8"))[0]
    assert calls == [] and row["passed"] and row["flagged"].startswith("keep_best")
    assert "CAP lines" in capsys.readouterr().out


def test_a_wall_spent_with_no_rightly_heard_try_still_refuses(tmp_path, monkeypatch):
    home, _ = seed(tmp_path, monkeypatch, failing(words_ok=False), wall=10.0)
    step_attempts.spend(home, "lines", 11.0)
    no_render(monkeypatch)
    with pytest.raises(SystemExit):
        say.main("x", 1)


def test_the_revoice_bucket_does_not_spend_the_lines_wall(tmp_path, monkeypatch):
    home, _ = seed(tmp_path, monkeypatch, failing(), wall=10.0)
    step_attempts.spend(home, "voice", 9999.0)
    calls = no_render(monkeypatch)
    with pytest.raises(RuntimeError):
        say.main("x", 1)
    assert calls == [1]


def test_two_identical_wrong_transcripts_file_the_pair_and_relisten_without_a_render(tmp_path, monkeypatch):
    seed(tmp_path, monkeypatch, failing(heard="Gold and a check.", prior_heard="Gold and a check.", error_rate=0.25))
    record = {**failing(heard="Gold and a check.", prior_heard="Gold and a check.", error_rate=0.25)}
    record["passed"] = False
    no_render(monkeypatch)
    cured = say.ear_cure(tmp_path, record, {0: record}, lambda clip: "Gold and a check.")
    assert cured and record["passed"] and record["error_rate"] == 0.0
    assert say.voice_qc.ear_lexicon(tmp_path) == {"check": "cheque"}


def test_one_wrong_transcript_is_not_yet_a_ruler_fault(tmp_path, monkeypatch):
    seed(tmp_path, monkeypatch, failing())
    record = failing(heard="Gold and a check.", prior_heard="something else")
    assert not say.ear_cure(tmp_path, record, {0: record}, lambda clip: "Gold and a check.")
    assert say.voice_qc.ear_lexicon(tmp_path) == {}


def test_a_stable_transcript_that_sounds_different_is_not_filed(tmp_path, monkeypatch):
    seed(tmp_path, monkeypatch, failing(text="The floor."))
    record = failing(text="The floor.", heard="The flour.", prior_heard="The flour.")
    assert not say.ear_cure(tmp_path, record, {0: record}, lambda clip: "The flour.")
    assert say.voice_qc.ear_lexicon(tmp_path) == {}


def test_a_fresh_render_carries_the_last_transcript_as_prior():
    assert say.carried({"heard": "a"}, {"index": 0})["prior_heard"] == "a"
    assert "prior_heard" not in say.carried({}, {"index": 0})
