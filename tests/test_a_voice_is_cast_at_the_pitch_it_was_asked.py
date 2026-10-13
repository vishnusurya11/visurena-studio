"""A voice is cast at the pitch it was asked for, MEASURED (Jekyll ep01 review, 2026-10-13).

SOUND.md measured the Jekyll cast with librosa pYIN (55-400 Hz, median of the
voiced frames) on every design clip: Hyde asked 92 Hz and rendered ~179, Poole
asked 158 and rendered ~99, the narrator asked 175 (nudged to 191) and rendered
~203 -- an octave above WotW's 100 Hz narrator.  `register_rendered_hz` in
voice.json recorded the ASKED number, so the sheet said 92/92 for a 179 Hz man.
Nothing in casting had ever measured F0.

So the measure SOUND.md used becomes a gate: a design outside +-15 % of its
asked register is refused, and what is recorded is what the clip measured."""
from __future__ import annotations

import numpy as np
import pytest
import soundfile as sf

from studio import voice_pitch


def tone(path, hertz: float, seconds: float = 1.5, rate: int = 16000):
    """A voiced-looking harmonic tone at `hertz`, so pYIN has a pitch to find."""
    t = np.arange(int(seconds * rate)) / rate
    wave = sum(np.sin(2 * np.pi * hertz * k * t) / k for k in range(1, 6))
    sf.write(str(path), (0.3 * wave / np.max(np.abs(wave))).astype("float32"), rate)
    return path


def test_the_measure_is_the_one_sound_md_used():
    assert (voice_pitch.FMIN, voice_pitch.FMAX) == (55.0, 400.0)
    assert voice_pitch.TOLERANCE == 0.15


@pytest.mark.parametrize("hertz", [105.0, 180.0])
def test_the_median_f0_of_a_clip_is_its_pitch(tmp_path, hertz):
    got = voice_pitch.f0_hz(tone(tmp_path / "t.wav", hertz))
    assert abs(got - hertz) / hertz < 0.03


def test_silence_has_no_pitch(tmp_path):
    path = tmp_path / "quiet.wav"
    sf.write(str(path), np.zeros(16000, dtype="float32"), 16000)
    assert voice_pitch.f0_hz(path) == 0.0


def test_the_error_is_relative_to_the_ask():
    assert voice_pitch.pitch_error(179.0, 92) == pytest.approx(0.946, abs=0.001)
    assert voice_pitch.pitch_error(110.0, 110) == 0.0
    assert voice_pitch.pitch_error(0.0, 110) == 1.0, "an unvoiced clip is as far off as it gets"


def test_the_measured_hyde_is_refused_and_a_landed_voice_is_not():
    why = voice_pitch.pitch_fault(179.0, 92)
    assert "179" in why and "92" in why
    assert voice_pitch.pitch_fault(103.0, 108) == ""      # Enfield landed: 103 against 108


def test_the_boundary_is_fifteen_percent_either_side():
    assert voice_pitch.pitch_fault(115.0, 100) == ""
    assert voice_pitch.pitch_fault(85.0, 100) == ""
    assert voice_pitch.pitch_fault(115.5, 100)
    assert voice_pitch.pitch_fault(84.5, 100)


def test_no_ask_means_no_gate():
    assert voice_pitch.pitch_fault(179.0, 0) == ""


def test_the_steer_counters_the_miss():
    """A render that came back high asks LOWER next time, and the other way round."""
    assert voice_pitch.steer(179.0, 92, 8) == -8
    assert voice_pitch.steer(70.0, 110, 8) == 8
    assert voice_pitch.steer(0.0, 110, 8) == 0, "nothing measured, nothing to steer by"
