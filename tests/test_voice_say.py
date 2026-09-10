"""Saying a line with the character's timbre and the beat's emotion."""
from __future__ import annotations

from pathlib import Path

from studio import voice_say


def test_the_timbre_and_the_emotion_go_to_different_slots(tmp_path):
    """The whole point of IndexTTS2 here: `ref_audio` is WHO is speaking and
    `emotion_audio` is HOW.  Sending one clip to both would be the old
    single-reference path with extra steps."""
    timbre, emotion = tmp_path / "holmes-calm.wav", tmp_path / "holmes-cold.wav"
    timbre.write_bytes(b"RIFF0000WAVEcalm")      # staging hashes CONTENT, so two
    emotion.write_bytes(b"RIFF0000WAVEcold")     # identical files stage as one
    values = voice_say.values_for("Rache, revenge.", timbre, emotion, seed=7)
    assert values["ref_audio"] != values["emotion_audio"]
    assert values["text"] == "Rache, revenge."
    assert values["seed"] == 7


def test_the_emotion_is_pushed_far_enough_to_hear(tmp_path):
    """Below this the read comes back neutral and the bank was wasted."""
    assert 0.5 <= voice_say.ALPHA <= 0.95


def test_a_line_is_said_through_the_indextts_workflow(tmp_path, monkeypatch):
    made = {}

    def fake_run(name, values, timeout=0):
        made.update(name=name, values=values)
        src = tmp_path / "raw.wav"
        src.write_bytes(b"RIFF0000WAVE")
        return [src]

    monkeypatch.setattr(voice_say, "post_process", lambda src, dst: dst.write_bytes(b"x"))
    monkeypatch.setattr(voice_say, "clip_seconds", lambda p: 2.4)
    timbre, emotion = tmp_path / "t.wav", tmp_path / "e.wav"
    for p in (timbre, emotion):
        p.write_bytes(b"RIFF0000WAVE")
    line = voice_say.say("Choose and eat.", timbre, emotion, seed=3,
                         out=tmp_path / "B15.wav", speaker="jefferson_hope", run=fake_run)
    assert made["name"] == "audio_indextts2_tts_single_speaker"
    assert line.seconds == 2.4 and line.speaker == "jefferson_hope"
    assert line.text == "Choose and eat."
