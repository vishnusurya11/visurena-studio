r"""Three gates the per-line table of episode 10 showed were missing or miscalibrated.

THE FLOOR SCALES WITH LENGTH.  MEASURED by truncating a GENUINE line and scoring
the truncation against its own design (same voice, less audio):

    Ferrier ep08/l25  5.27 s 0.815 | 1.5 s 0.690 | 2.5 s 0.771 | 4.0 s 0.819
    Watson  ep10/l26  5.84 s 0.824 | 1.5 s 0.640 | 2.5 s 0.709 | 4.0 s 0.796
    Young   ep10/l16  5.42 s 0.853 | 1.5 s 0.677 | 2.5 s 0.708 | 4.0 s 0.826

A correct voice loses ~0.05 at 2.5 s and 0.12-0.18 at 1.5 s.  Lucy's four lines
run 1.5-2.6 s and three sit under 0.75 with a design that reads 0.864 on a 2.6 s
line.  A flat 0.70 refuses the TRUE voice under 2 s.

A LINE ENDS ON ITS LAST PHONEME.  l14 and l05 end with 0.00 s of trailing room
and -25 / -30 dB in the last 50 ms: "young." is cut off without release.  Across
the episode the median trail is 0.05 s.  So `ends_abruptly` fails a clip whose
last 50 ms are still within 30 dB of its peak with under 0.05 s of room, and
`voice_say` pads 120 ms after the last sample so the release has somewhere to go.

A LINE CAN BE RUSHED.  l01 4.20 wps, l10 4.11, l29 4.00 (Lucy's six-word button
in 1.50 s, also the loudest line) against an episode mean of 3.02.  WPS_MAX 3.8.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

from studio import voice_qc, voice_say

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_say3", ROOT / "scripts" / "episode" / "say_lines.py")
say = importlib.util.module_from_spec(spec)
sys.modules["ep_say3"] = say
spec.loader.exec_module(say)

RATE = 24000
LINE = "It is better that one should perish than that many be led astray."


# ---- the floor ----------------------------------------------------------------

def test_the_floor_is_the_measured_truncation_loss():
    assert say.similar_floor(5.3) == 0.70
    assert say.similar_floor(4.0) == 0.70
    assert say.similar_floor(3.99) == 0.65
    assert say.similar_floor(2.0) == 0.65
    assert say.similar_floor(1.99) == 0.60
    assert say.similar_floor(1.5) == 0.60


def test_lucys_true_voice_at_one_and_a_half_seconds_now_passes(tmp_path, monkeypatch):
    clip = tmp_path / "l29.wav"
    sf.write(str(clip), np.zeros(int(1.5 * RATE), dtype="float32"), RATE)
    records = [{"index": 29, "rel_path": "l29.wav", "text": "But they won't let us leave.",
                "speaker": "lucy_ferrier", "reference": "design.wav"}]
    monkeypatch.setattr(say, "reference_for", lambda book, who: clip)
    monkeypatch.setattr(say.voice_ear, "similarity", lambda ref, clip: 0.64)
    assert say.listen_all(records, tmp_path, lambda c: records[0]["text"]) == []
    assert records[0]["floor"] == 0.60


def test_a_long_line_still_needs_the_full_floor(tmp_path, monkeypatch):
    clip = tmp_path / "l26.wav"
    sf.write(str(clip), np.zeros(int(5.8 * RATE), dtype="float32"), RATE)
    records = [{"index": 26, "rel_path": "l26.wav", "text": "x", "speaker": "john_watson", "reference": "design.wav"}]
    monkeypatch.setattr(say, "reference_for", lambda book, who: clip)
    monkeypatch.setattr(say.voice_ear, "similarity", lambda ref, clip: 0.64)
    assert say.listen_all(records, tmp_path, lambda c: "x") == [26]


# ---- the end of the line ---------------------------------------------------------

def spoken(path: Path, seconds: float = 3.0, room: float = 0.0, release: float = 0.0):
    """A tone at speech level; `room` of silence after it; `release` of decay before that."""
    t = np.arange(int(seconds * RATE)) / RATE
    one = (0.3 * np.sin(2 * np.pi * 180 * t)).astype(np.float32)
    if release:
        n = int(release * RATE)
        one[-n:] *= np.linspace(1.0, 0.0, n, dtype=np.float32) ** 3
    if room:
        one = np.concatenate([one, np.zeros(int(room * RATE), dtype=np.float32)])
    sf.write(str(path), one, RATE)
    return path


def test_the_measured_l14_ends_abruptly(tmp_path):
    assert voice_qc.ends_abruptly(spoken(tmp_path / "l14.wav"))


def test_a_line_with_room_after_it_does_not(tmp_path):
    assert not voice_qc.ends_abruptly(spoken(tmp_path / "ok.wav", room=0.12))


def test_a_line_that_released_into_silence_does_not(tmp_path):
    assert not voice_qc.ends_abruptly(spoken(tmp_path / "rel.wav", release=0.3, room=0.06))


def test_a_silent_clip_is_not_abrupt(tmp_path):
    clip = tmp_path / "z.wav"
    sf.write(str(clip), np.zeros(RATE, dtype="float32"), RATE)
    assert not voice_qc.ends_abruptly(clip)


def test_check_fails_an_abrupt_end(tmp_path):
    got = voice_qc.check(spoken(tmp_path / "l14.wav"), "Give us time. My daughter is very young.",
                         transcribe=lambda _: "Give us time. My daughter is very young.")
    assert not got.passed and "cut off" in got.why and got.abrupt


# ---- the pace --------------------------------------------------------------------

def test_words_per_second_is_measured_off_the_file():
    assert abs(voice_qc.words_per_second("But they won't let us leave.", 1.50) - 4.0) < 0.01
    assert voice_qc.words_per_second("", 1.0) == 0.0


def test_the_rushed_l29_fails_and_a_normal_line_passes(tmp_path):
    text = "But they won't let us leave."
    got = voice_qc.check(spoken(tmp_path / "l29.wav", seconds=1.5, room=0.12), text, transcribe=lambda _: text)
    assert not got.passed and "rushed" in got.why and got.wps > voice_qc.WPS_MAX
    got = voice_qc.check(spoken(tmp_path / "l22.wav", seconds=3.92, room=0.12),
                         "Don't you scare yourself. We'll fix it up somehow.",
                         transcribe=lambda _: "Don't you scare yourself. We'll fix it up somehow.")
    assert got.passed and got.wps < 3.0


def test_the_ceiling_is_the_documented_one():
    assert voice_qc.WPS_MAX == 3.8


# ---- the room after the last sample ---------------------------------------------

def test_a_said_line_gets_room_after_its_last_sample(tmp_path, monkeypatch):
    def fake_run(name, values, timeout=0):
        return [spoken(tmp_path / "raw.wav", seconds=2.0)]

    monkeypatch.setattr(voice_say, "post_process", lambda src, dst: spoken(dst, seconds=2.0))
    for p in (tmp_path / "t.wav", tmp_path / "e.wav"):
        p.write_bytes(b"RIFF0000WAVE")
    line = voice_say.say("Give us time.", tmp_path / "t.wav", tmp_path / "e.wav", seed=1,
                         out=tmp_path / "l14.wav", run=fake_run)
    assert abs(line.seconds - 2.12) < 0.005
    assert not voice_qc.ends_abruptly(tmp_path / "l14.wav")


def test_the_room_is_the_documented_amount(tmp_path):
    assert voice_say.ROOM_S == 0.12
    got = voice_say.pad_room(spoken(tmp_path / "a.wav", seconds=1.0))
    assert abs(voice_qc.seconds_of(got) - 1.12) < 0.001
