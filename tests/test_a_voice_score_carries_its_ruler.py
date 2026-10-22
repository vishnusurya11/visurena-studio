"""A voice score names the ruler that made it, and two rulers are never mixed.

2026-10-21 (voice bench VERDICT, step 2): every ECAPA score before today was taken
on 24 kHz audio fed to a 16 kHz model (`ecapa24`); from today the ear resamples
(`ecapa16`).  The two scales differ -- Hyde-Jekyll's designs read 0.578 on the old
ruler and 0.061 on the new -- so a stored number is only ever compared with a
threshold or a number on its own ruler.  A score stored without a tag was taken
before the tag existed, so it is read as the old ruler.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

from studio import voice_ear, voice_register
from studio.judges import look

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("say_ruler", ROOT / "scripts" / "episode" / "say_lines.py")
say = importlib.util.module_from_spec(spec)
sys.modules["say_ruler"] = say
spec.loader.exec_module(say)

OLD, NEW = voice_ear.OLD_RULER, voice_ear.RULER


def test_the_rulers_are_named():
    assert (OLD, NEW) == ("ecapa24", "ecapa16")


def test_an_untagged_score_is_the_old_ruler():
    assert voice_ear.ruler_of({"similarity": 0.8}) == OLD
    assert voice_ear.ruler_of({"similarity": 0.8, "ruler": NEW}) == NEW


def test_each_ruler_has_its_own_same_speaker_line():
    assert voice_ear.same_speaker(OLD) == 0.55
    assert voice_ear.same_speaker(NEW) == voice_ear.SAME_SPEAKER


def test_a_listened_line_is_stamped_with_the_ruler(tmp_path, monkeypatch):
    sf.write(tmp_path / "a.wav", np.zeros(60000, dtype="float32"), 24000)
    records = [{"index": 0, "rel_path": "a.wav", "text": "good morning", "speaker": "x"}]
    monkeypatch.setattr(say, "reference_for", lambda book, who: tmp_path / "a.wav")
    monkeypatch.setattr(say.voice_ear, "similarity", lambda ref, clip: 0.9)
    say.listen_all(records, tmp_path, lambda clip: "good morning")
    assert records[0]["ruler"] == NEW


def test_an_old_ruler_reference_is_judged_on_the_old_floor():
    """Stamford's l00 at 0.795 on the old ruler still qualifies by the old 0.75; a
    new-ruler row qualifies by the new floor; a new-ruler row outranks a higher old one."""
    old = {"speaker": "s", "similarity": 0.795, "passed": True}
    new = {"speaker": "s", "similarity": say.BEST_REFERENCE_FLOOR, "passed": True, "ruler": NEW}
    assert say.best_line_reference({0: old}, "s", exclude=None) == 0
    assert say.best_line_reference({0: old, 1: new}, "s", exclude=None) == 1
    assert say.best_line_reference({0: dict(old, similarity=0.74)}, "s", exclude=None) is None


def test_a_redo_on_the_new_ruler_beats_an_old_number(tmp_path):
    wav = tmp_path / "l03.wav"; wav.write_bytes(b"new")
    (tmp_path / "l03.prev.wav").write_bytes(b"old")
    previous = {"index": 3, "similarity": 0.80, "passed": False}
    new = {"index": 3, "similarity": 0.55, "passed": False, "ruler": NEW}
    assert say.keep_best(new, previous, wav)["similarity"] == 0.55 and wav.read_bytes() == b"new"


def test_a_best_try_on_the_old_ruler_is_replaced(tmp_path):
    wav = tmp_path / "l04.wav"; wav.write_bytes(b"try")
    best = {"similarity": 0.62, "words_ok": True}
    record = {"similarity": 0.40, "words_ok": True, "ruler": NEW}
    assert say.remember_best(record, wav, best, tmp_path)["ruler"] == NEW
    assert (tmp_path / "l04.best.wav").read_bytes() == b"try"


def filed(book: Path, rows: list[dict]) -> None:
    (book / "cast").mkdir(parents=True, exist_ok=True)
    (book / "cast" / "registers.json").write_text(json.dumps({"apart": rows}), encoding="utf-8")


def test_an_untagged_ceiling_is_not_applied_on_the_new_ruler(tmp_path):
    filed(tmp_path, [{"pair": ["hyde", "jekyll"], "below": 0.55},
                     {"pair": ["hyde", "lanyon"], "below": 0.50, "ruler": NEW}])
    assert voice_register.ceilings_of(tmp_path, "hyde") == {"lanyon": 0.50}
    assert voice_register.ceilings_of(tmp_path, "hyde", ruler=OLD) == {"jekyll": 0.55}


def sheet(book: Path, who: str, gates: dict) -> None:
    room = book / "cast" / who / "voice"
    room.mkdir(parents=True, exist_ok=True)
    (room / "voice.json").write_text(json.dumps({"gates": gates}), encoding="utf-8")


def test_the_look_judge_reads_a_sheet_on_its_own_ruler(tmp_path):
    sheet(tmp_path, "old", {"nearest": "x", "nearest_similarity": 0.56})
    sheet(tmp_path, "new", {"nearest": "x", "nearest_similarity": 0.56, "ruler": NEW})
    assert look.voice_fault(tmp_path, "old", "w") is not None
    assert (look.voice_fault(tmp_path, "new", "w") is None) == (0.56 < voice_ear.SAME_SPEAKER)
