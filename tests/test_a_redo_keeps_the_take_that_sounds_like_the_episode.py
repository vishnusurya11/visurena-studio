"""ep27 (2026-10-09 16:40Z): the narrator measured as a split voice, every failing
pair through l01 'Yet I write on.' (mean 0.698 to his other lines -- the lowest
of ~60 calm narrator lines over four episodes).  Two revoice rounds re-said it
and both KEPT THE ORIGINAL: keep_best compares each try to the design clip,
where l01 already scored 0.71, while the fault is against the episode's other
lines.  A redo keeps the take that sits closer to the speaker's other lines in
this episode when both tries can be measured so; the design clip decides only
when they cannot."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("say_lines_fit", ROOT / "scripts" / "episode" / "say_lines.py")
say = importlib.util.module_from_spec(spec)
sys.modules["say_lines_fit"] = say
spec.loader.exec_module(say)


def _wavs(tmp_path):
    wav = tmp_path / "l01.wav"
    wav.write_bytes(b"new")
    wav.with_suffix(".prev.wav").write_bytes(b"old")
    return wav


def test_the_take_closer_to_the_episode_wins_over_the_design_clip(tmp_path):
    wav = _wavs(tmp_path)
    new, old = {"similarity": 0.66, "passed": True}, {"similarity": 0.71, "passed": True}
    kept = say.keep_best(new, old, wav, fit=(0.79, 0.70))
    assert kept is new and wav.read_bytes() == b"new"


def test_a_take_further_from_the_episode_loses(tmp_path):
    wav = _wavs(tmp_path)
    new, old = {"similarity": 0.80, "passed": True}, {"similarity": 0.71, "passed": True}
    kept = say.keep_best(new, old, wav, fit=(0.68, 0.70))
    assert kept["similarity"] == 0.71 and wav.read_bytes() == b"old"


def test_a_take_the_ear_failed_never_wins_on_fit(tmp_path):
    wav = _wavs(tmp_path)
    new, old = {"similarity": 0.66, "passed": False}, {"similarity": 0.71, "passed": True}
    kept = say.keep_best(new, old, wav, fit=(0.90, 0.70))
    assert kept["similarity"] == 0.71


def test_the_split_voice_cure_gets_a_third_round():
    from scripts.episode import step_04_record
    assert step_04_record.REVOICE_ROUNDS == 3
