"""The inner voice (anime-TV grammar, 2026-10-17; G1, docs/audit/2026-10-16_model_tests/
voice/results.json).  A hushed Qwen3-TTS VoiceDesign read was breathier but another
man (ECAPA 0.23 / 0.67 against the IndexTTS2 line's 0.81, and 'Hide', 'wheel'
misheard), so an inner line keeps its SPEAKER'S OWN ENGINE with the hushed
delivery, and assemble gives it the close-mic treatment G1 tested (highpass
110 Hz, lowpass 6.5 kHz, a short 35/70 ms reflection).  The hushed -5 dB is the
mix's delivery offset, never applied twice.  ADVISORY until the owner has heard
it.  $0: no ffmpeg runs here."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from studio import episode_emotion, inner_voice


def test_an_inner_line_is_said_hushed_unless_its_delivery_says_otherwise():
    line = SimpleNamespace(kind="inner", delivery="", text="Hyde. I know that name.")
    assert episode_emotion.delivery_of(line) == "hushed"
    line.delivery = "cold"
    assert episode_emotion.delivery_of(line) == "cold"


def test_the_inner_mix_offset_is_the_hushed_one_unclamped():
    assert episode_emotion.offset_of("hushed", "inner") == episode_emotion.OFFSETS["hushed"]


def test_the_close_mic_chain_is_the_one_g1_tested_without_its_gain():
    assert inner_voice.CHAIN.startswith("highpass=f=110,lowpass=f=6500,aecho=")
    assert "volume" not in inner_voice.CHAIN


def test_only_inner_lines_are_treated(tmp_path):
    ran = []
    wavs = {0: tmp_path / "l00.wav", 1: tmp_path / "l01.wav"}
    lines = [{"index": 0, "kind": "dialogue"}, {"index": 1, "kind": "inner"}]
    got = inner_voice.treat(wavs, lines, tmp_path, run=lambda cmd, **kw: ran.append(cmd))
    assert got[0] == wavs[0] and got[1] == tmp_path / "inner_l01.wav"
    assert len(ran) == 1 and inner_voice.CHAIN in ran[0] and str(wavs[1]) in ran[0]


def test_assemble_treats_the_inner_lines_before_the_mix():
    import inspect
    from scripts.episode import assemble
    src = inspect.getsource(assemble.main)
    assert src.index("inner_voice.treat(") < src.index("mix_with_lines(")
