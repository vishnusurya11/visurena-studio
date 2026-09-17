"""A cast voice is gated at DESIGN time on two numbers, before a line is ever said.

MEASURED on episode 10 (analyst F, and reproduced on CPU ECAPA 2026-09-16):

    half-vs-half self-similarity of each design.wav
        Watson 0.762  Drebber 0.770  Lucy 0.721  Young 0.706  Holmes 0.704
        Hope 0.695  Stangerson 0.559  **Ferrier 0.498**

    design-vs-design, the highest pair in the cast: **Ferrier vs Young 0.847**

Ferrier's 11 s design clip does not agree with ITSELF: its whole-clip embedding
is an average of two voices, and no rendered line can match an average well --
his best line in the book is 0.815 and his median 0.726, against Watson's 0.855.
And three of his five lines score HIGHER against Young's design than his own.

Both faults are visible at cast time and neither was measured there.  So two
gates: a design must agree with itself (>= SELF_FLOOR) and must not be its
nearest neighbour's twin (<= NEAREST_CEIL).  A failing design is re-rolled with
its register nudged AWAY from the rival, up to REROLLS times.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

from studio import voice_ear

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cast_voices", ROOT / "scripts" / "cast" / "cast_voices.py")
cast_voices = importlib.util.module_from_spec(spec)
sys.modules["cast_voices"] = cast_voices
spec.loader.exec_module(cast_voices)


# ---- the ear: one clip against its own other half ---------------------------

def two_halves(path: Path, first: float, second: float, seconds: float = 2.0, rate: int = 16000):
    n = int(seconds * rate / 2)
    sf.write(str(path), np.concatenate([np.full(n, first), np.full(n, second)]).astype("float32"), rate)
    return path


def fake_embed(samples, device=""):
    """A voice is its sign here: positive samples are one speaker, negative another."""
    return np.array([1.0, 0.0]) if float(np.mean(samples)) > 0 else np.array([0.0, 1.0])


def test_a_clip_that_is_one_voice_agrees_with_itself(tmp_path, monkeypatch):
    monkeypatch.setattr(voice_ear, "embed_samples", fake_embed)
    clip = two_halves(tmp_path / "one.wav", 0.1, 0.1)
    assert voice_ear.self_similarity(clip, device="cpu") > 0.99


def test_a_clip_that_changes_voice_halfway_does_not(tmp_path, monkeypatch):
    monkeypatch.setattr(voice_ear, "embed_samples", fake_embed)
    clip = two_halves(tmp_path / "two.wav", 0.1, -0.1)
    assert voice_ear.self_similarity(clip, device="cpu") < 0.01


# ---- the gates ----------------------------------------------------------------

def test_the_measured_ferrier_fails_both_gates():
    why = cast_voices.design_fault(0.498, 0.847)
    assert "itself" in why and "0.498" in why
    assert "nearest" in why and "0.847" in why


def test_the_measured_watson_passes():
    assert cast_voices.design_fault(0.762, 0.79) == ""


def test_the_boundaries_are_the_documented_ones():
    assert cast_voices.SELF_FLOOR == 0.65 and cast_voices.NEAREST_CEIL == 0.80
    assert cast_voices.design_fault(0.65, 0.80) == ""
    assert cast_voices.design_fault(0.649, 0.80)
    assert cast_voices.design_fault(0.65, 0.801)


# ---- the nudge: away from the rival, in the register --------------------------

def test_the_register_is_nudged_away_from_the_rival():
    """Young sits at 76 and Ferrier at 93: Ferrier goes UP.  Charpentier at 171
    against Lestrade at 162 goes up too; Lestrade against Charpentier goes down."""
    assert cast_voices.nudge_step("john_ferrier", "brigham_young") > 0
    assert cast_voices.nudge_step("g_lestrade", "arthur_charpentier") < 0
    assert cast_voices.nudge_step("john_ferrier", "") > 0


def test_the_nudge_rewrites_every_hertz_in_the_instruction():
    text = "pitch: 93 Hz; begins low.\nAt about 93 Hz the voice sits."
    got = cast_voices.nudge(text, 93, 8)
    assert "101 Hz" in got and "93 Hz" not in got


# ---- the audition: re-rolled until the gates pass -----------------------------

class Stage:
    """A fake VoiceDesign: each render is a wav whose scores are scripted."""

    def __init__(self, scores):
        self.scores = list(scores)       # (self_sim, nearest_sim) per render, in order
        self.rendered = []
        self.by_file = {}

    def render(self, instruct: str, dest: Path) -> Path:
        self_sim, near = self.scores[len(self.rendered)]
        sf.write(str(dest), np.zeros(1600, dtype="float32"), 16000)
        self.rendered.append(instruct)
        self.by_file[dest.name] = (self_sim, near)
        return dest


def wire(monkeypatch, stage: Stage):
    monkeypatch.setattr(cast_voices, "CANDIDATES", 1)
    monkeypatch.setattr(voice_ear, "self_similarity",
                        lambda clip, device="": stage.by_file[Path(clip).name][0])
    monkeypatch.setattr(voice_ear, "nearest",
                        lambda clip, cast, device="": ("brigham_young", stage.by_file[Path(clip).name][1]))


def test_a_failing_design_is_re_rolled_with_the_register_nudged(tmp_path, monkeypatch):
    stage = Stage([(0.50, 0.85), (0.60, 0.79), (0.72, 0.70)])
    wire(monkeypatch, stage)
    got = cast_voices.audition(tmp_path, "john_ferrier", "pitch: 93 Hz; low.", {"brigham_young": tmp_path / "y.wav"},
                               hertz=93, render=stage.render)
    assert len(stage.rendered) == 3
    assert "93 Hz" in stage.rendered[0] and "93 Hz" not in stage.rendered[2]
    assert got.self_similarity == 0.72 and got.nearest == 0.70 and got.fault == ""
    assert got.clip.exists() and got.clip.name == "design.wav"
    assert got.hertz > 93


def test_a_passing_design_is_kept_on_the_first_roll(tmp_path, monkeypatch):
    stage = Stage([(0.76, 0.74)])
    wire(monkeypatch, stage)
    got = cast_voices.audition(tmp_path, "john_watson", "pitch: 131 Hz.", {}, hertz=131, render=stage.render)
    assert len(stage.rendered) == 1 and got.fault == "" and got.hertz == 131


def test_when_every_roll_fails_the_least_bad_is_kept_and_named(tmp_path, monkeypatch):
    stage = Stage([(0.50, 0.85), (0.62, 0.83), (0.58, 0.81)])
    wire(monkeypatch, stage)
    monkeypatch.setattr(cast_voices, "REROLLS", 3)
    got = cast_voices.audition(tmp_path, "john_ferrier", "pitch: 93 Hz.", {"brigham_young": tmp_path / "y.wav"},
                               hertz=93, render=stage.render)
    assert got.fault and got.nearest == 0.81, "the lowest collision wins when nothing passes"
    assert got.clip.exists()
    assert not list(got.clip.parent.glob(".take*"))


# ---- a recast keeps the old clip ------------------------------------------------

def test_a_recast_retires_the_old_design_as_v1_then_v2(tmp_path):
    dest = tmp_path / "cast" / "john_ferrier" / "voice" / "design.wav"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"one")
    (dest.parent / "voice.json").write_text("{}", encoding="utf-8")
    assert cast_voices.retire(dest) == dest.with_name("design_v1.wav")
    assert not dest.exists() and dest.with_name("design_v1.wav").read_bytes() == b"one"
    assert dest.with_name("voice_v1.json").exists()
    dest.write_bytes(b"two")
    assert cast_voices.retire(dest) == dest.with_name("design_v2.wav")


def test_retiring_nothing_is_nothing(tmp_path):
    assert cast_voices.retire(tmp_path / "design.wav") is None


def test_the_nudge_keeps_its_first_direction_when_the_rival_changes(tmp_path, monkeypatch):
    """MEASURED on the Ferrier recast 2026-09-16: roll 1 at 93 Hz collided with
    Hope (84, so: up), roll 2 at 101 collided with Stangerson (142, so: down) and
    roll 3 went back to 93 and rendered roll 1 again.  A register that oscillates
    never leaves the crowd; it keeps walking the way it started."""
    stage = Stage([(0.80, 0.86), (0.67, 0.86), (0.75, 0.70)])
    monkeypatch.setattr(cast_voices, "CANDIDATES", 1)
    rivals = iter(["jefferson_hope", "joseph_stangerson", "brigham_young"])
    monkeypatch.setattr(voice_ear, "self_similarity", lambda clip, device="": stage.by_file[Path(clip).name][0])
    monkeypatch.setattr(voice_ear, "nearest",
                        lambda clip, cast, device="": (next(rivals), stage.by_file[Path(clip).name][1]))
    got = cast_voices.audition(tmp_path, "john_ferrier", "pitch: 93 Hz.", {}, hertz=93, render=stage.render)
    assert [("93 Hz" in s, "101 Hz" in s, "109 Hz" in s) for s in stage.rendered] == \
        [(True, False, False), (False, True, False), (False, False, True)]
    assert got.hertz == 109
