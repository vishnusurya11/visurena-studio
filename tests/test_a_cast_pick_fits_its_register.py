"""The caster picks the voice that FITS, then the one that is distinct (Jekyll ep01 review, 2026-10-13).

SOUND.md R1: `best_of` kept the candidate with the lowest nearest-similarity and
had no term for pitch, and the cheapest way to be unlike everyone is to be high.
Jekyll v1 (~134 Hz, a plausible big man) lost to v2 (~203 Hz); Hyde v1 (~121)
lost to v2 (~179).  And `nudge_step` moved a register UP whenever no fixed table
named the rival: Jekyll went 175 -> 191 Hz.

Now: a candidate outside its register is a fault; among the ones that pass, the
nearer the asked register wins, and only then the distance from others; a nudge
steers against the measured miss, or away from a rival whose register the book
filed, and otherwise does not move."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

from studio import voice_ear, voice_pitch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cast_voices_fit", ROOT / "scripts" / "cast" / "cast_voices.py")
cast_voices = importlib.util.module_from_spec(spec)
sys.modules["cast_voices_fit"] = cast_voices
spec.loader.exec_module(cast_voices)


def pick(name, nearest=0.5, measured=110.0, target=110, self_sim=0.8, fault=""):
    return cast_voices.Pick(Path(name), self_sim, "rival", nearest, fault, target, measured, target)


# ---- the gate -------------------------------------------------------------------

def test_a_design_off_its_register_is_a_fault():
    assert "179" in cast_voices.design_fault(0.80, 0.50, measured=179.0, asked=92)
    assert cast_voices.design_fault(0.80, 0.50, measured=95.0, asked=92) == ""


# ---- the pick -------------------------------------------------------------------

def test_the_measured_jekyll_v1_beats_the_v2_that_was_kept():
    """v1 rendered ~134 against an asked 116; v2 rendered ~203 and was LESS like
    the others.  Pitch fails v2 outright, so v1 wins on fit."""
    v1 = pick("v1", nearest=0.70, measured=120.0, target=116)
    v2 = pick("v2", nearest=0.55, measured=203.0, target=116,
              fault=voice_pitch.pitch_fault(203.0, 116))
    assert cast_voices.best_of([v2, v1]) is v1


def test_among_passing_picks_the_asked_register_comes_before_distance():
    near_the_ask = pick("a", nearest=0.70, measured=111.0, target=110)
    far_but_distinct = pick("b", nearest=0.40, measured=124.0, target=110)
    assert cast_voices.best_of([far_but_distinct, near_the_ask]) is near_the_ask


def test_within_one_band_of_fit_the_more_distinct_voice_wins():
    a = pick("a", nearest=0.70, measured=110.0, target=110)
    b = pick("b", nearest=0.50, measured=112.0, target=110)
    assert cast_voices.best_of([a, b]) is b


def test_when_nothing_passes_the_one_on_pitch_beats_the_one_off_it():
    twin_on_pitch = pick("a", nearest=0.85, measured=110.0, target=110, fault="twin")
    off_pitch = pick("b", nearest=0.40, measured=180.0, target=110, fault="off pitch")
    assert cast_voices.best_of([off_pitch, twin_on_pitch]) is twin_on_pitch


# ---- the nudge ------------------------------------------------------------------

def test_a_render_that_came_back_high_is_asked_lower():
    high = pick("a", measured=179.0, target=92, fault="off")
    assert cast_voices.nudge_step(high, "edward_hyde", {}) < 0


def test_there_is_no_default_upward_nudge():
    """Jekyll 175 -> 191: no fixed table named his rival, so the register went up."""
    landed = pick("a", measured=176.0, target=175, fault="twin")
    landed = cast_voices.Pick(landed.clip, 0.8, "edward_hyde", 0.85, "twin", 175, 176.0, 175)
    assert cast_voices.nudge_step(landed, "henry_jekyll", {}) == 0


def test_on_pitch_a_rival_the_book_placed_pushes_away():
    twin = cast_voices.Pick(Path("a"), 0.8, "brigham_young", 0.85, "twin", 93, 93.0, 93)
    registers = {"brigham_young": 76, "john_ferrier": 93}
    assert cast_voices.nudge_step(twin, "john_ferrier", registers) > 0


# ---- the record -----------------------------------------------------------------

def test_the_sheet_records_what_the_clip_measured(tmp_path):
    got = cast_voices.voice_persona.VoiceInstruction.model_validate(
        json.loads((ROOT / "tests/fixtures/voice_instruction_ferrier.json").read_text(encoding="utf-8")))
    done = cast_voices.Pick(tmp_path / "design.wav", 0.8, "x", 0.6, "", 101, 97.43, 93)
    sheet = cast_voices.sheet_of("john_ferrier", got, done)
    assert sheet["register_hz"] == 93 and sheet["register_asked_hz"] == 101
    assert sheet["register_rendered_hz"] == 97.4
    assert sheet["gates"]["pitch_error"] == round(abs(97.43 - 93) / 93, 3)
    assert "pYIN" in sheet["pitch_measure"]


# ---- the audition gates on pitch ------------------------------------------------

def test_an_audition_rolls_past_a_render_off_its_register(tmp_path, monkeypatch):
    pitches = iter([180.0, 118.0])
    monkeypatch.setattr(cast_voices, "CANDIDATES", 1)
    monkeypatch.setattr(voice_ear, "self_similarity", lambda clip, device="": 0.8)
    monkeypatch.setattr(voice_ear, "nearest", lambda clip, cast, device="": ("x", 0.5))
    monkeypatch.setattr(voice_pitch, "f0_hz", lambda clip: next(pitches))
    asked = []

    def render(instruct, dest, seed=0):
        asked.append(instruct)
        sf.write(str(dest), np.zeros(1600, dtype="float32"), 16000)
        return dest

    got = cast_voices.audition(tmp_path, "henry_jekyll", "pitch: 116 Hz.", {}, hertz=116, render=render)
    assert len(asked) == 2 and got.measured_hz == 118.0 and got.fault == ""
    assert "108 Hz" in asked[1], "rendered high, so the second roll is asked lower"
    assert got.target_hz == 116
