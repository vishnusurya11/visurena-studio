"""A line is said the way it is written (root cause 2026-09-26, D11).

`say_lines` passed the cast's quiet reading clip as IndexTTS2's EMOTION
reference too, so every line in the series came out at one temperature: the
largest pitch lift on any '!' line across twelve episodes is +2.3 semitones,
and ep12's "Get under the water!" was the flattest line in its episode.  Then
every line was levelled to one loudness, so a whisper and a scream sat level."""
from __future__ import annotations

import json
from types import SimpleNamespace as NS

import numpy as np
import pytest
import soundfile as sf

from studio import episode_emotion as ee
from studio.episode_spec import Line


def test_a_line_carries_a_delivery_and_the_contract_names_them():
    line = Line(index=0, kind="dialogue", speaker="a", text="Run!", shot=0, delivery="shouting")
    assert line.delivery == "shouting"
    with pytest.raises(ValueError):
        Line(index=0, kind="dialogue", speaker="a", text="Run!", shot=0, delivery="loud")


def test_an_exclamation_with_no_delivery_is_shouted():
    assert ee.delivery_of(NS(text="Get under the water!", delivery="")) == "shouting"
    assert ee.delivery_of(NS(text="We talked in whispers.", delivery="hushed")) == "hushed"
    assert ee.delivery_of(NS(text="At dawn we crept out.", delivery="")) == "calm"


def test_the_design_instruction_is_kept_and_the_delivery_added():
    said = ee.instruct_for({"instruction": "A man of forty, dry and precise."}, "shouting")
    assert said.startswith("A man of forty, dry and precise.") and "shout" in said.lower()


def test_a_calm_line_uses_the_design_clip_and_renders_nothing(tmp_path):
    voice = tmp_path / "cast" / "narrator" / "voice"
    voice.mkdir(parents=True)
    (voice / "design.wav").write_bytes(b"wav")
    rendered = []
    assert ee.emotion_clip(tmp_path, "narrator", "calm", render=lambda i, d: rendered.append(d)) == voice / "design.wav"
    assert rendered == []


def test_a_shouted_line_designs_its_clip_once(tmp_path):
    voice = tmp_path / "cast" / "narrator" / "voice"
    voice.mkdir(parents=True)
    (voice / "voice.json").write_text(json.dumps({"instruction": "A dry man."}), encoding="utf-8")
    made = []

    def render(instruct, dest):
        made.append(instruct)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"wav")
        return dest

    first = ee.emotion_clip(tmp_path, "narrator", "shouting", render=render)
    again = ee.emotion_clip(tmp_path, "narrator", "shouting", render=render)
    assert first == again == voice / "emotion" / "shouting.wav" and len(made) == 1


def tone(path, hz, seconds=1.0, rate=16000):
    t = np.arange(int(seconds * rate)) / rate
    sf.write(str(path), 0.4 * np.sin(2 * np.pi * hz * t), rate)
    return path


def test_the_lift_is_measured_in_semitones(tmp_path):
    assert ee.lift_st(tone(tmp_path / "shout.wav", 200.0), 100.0) == pytest.approx(12.0, abs=0.5)


def test_a_shout_that_does_not_lift_fails_and_a_calm_line_is_not_asked(tmp_path):
    flat = tone(tmp_path / "flat.wav", 102.0)
    assert not ee.prosody_ok("shouting", flat, 100.0)
    assert ee.prosody_ok("calm", flat, 100.0)
    assert ee.prosody_ok("shouting", tone(tmp_path / "up.wav", 130.0), 100.0)


def test_the_mix_offset_follows_the_delivery():
    assert ee.OFFSETS["shouting"] > 0 > ee.OFFSETS["hushed"] and ee.offset_of("calm") == 0.0


# ---- say_lines: the emotion clip goes in, and a flat shout comes back as a failure ----

def test_a_shouted_line_is_rendered_with_its_emotion_clip(tmp_path, monkeypatch):
    from scripts.episode import say_lines as say
    from studio import voice_say
    seen = {}
    monkeypatch.setattr(say, "line_reference", lambda book, records, line, attempt: tmp_path / "design.wav")
    monkeypatch.setattr(say.episode_emotion, "emotion_clip", lambda book, who, reg: tmp_path / f"{reg}.wav")
    monkeypatch.setattr(say, "ENGINE", "indextts2")
    monkeypatch.setattr(say.episode_home, "relative", lambda book, p: p.name)

    def fake_say(text, timbre, emotion, seed, out, index=0, speaker=None):
        seen.update(timbre=timbre, emotion=emotion)
        return NS(seconds=1.2, seed=seed)
    monkeypatch.setattr(voice_say, "say", fake_say)
    line = Line(index=16, kind="dialogue", speaker="narrator", text="Get under the water!", shot=16)
    rec = say.render(tmp_path, NS(number=13), line, tmp_path, 0)
    assert seen == {"timbre": tmp_path / "design.wav", "emotion": tmp_path / "shouting.wav"}
    assert rec["delivery"] == "shouting"


def test_a_flat_shout_is_a_failed_line(tmp_path, monkeypatch):
    from scripts.episode import say_lines as say
    tone(tmp_path / "l16.wav", 102.0)
    monkeypatch.setattr(say, "reference_for", lambda book, who: tone(tmp_path / "design.wav", 100.0))
    rec = {"delivery": "shouting", "speaker": "narrator"}
    assert not say.lift_ok(tmp_path, rec, tmp_path / "l16.wav") and rec["lift_st"] < 1.0
    assert say.lift_ok(tmp_path, {"delivery": "calm", "speaker": "narrator"}, tmp_path / "l16.wav")


def test_the_cast_record_is_the_instruction_it_was_designed_from():
    """voice.json keeps the structured instruction as a dict; what VoiceDesign was
    sent is `persona` and `sheet` (cast_voices SHAPE 'both')."""
    said = ee.instruct_for({"instruction": {"character": "curate"}, "persona": "A curate of 34.",
                            "sheet": "Gender: male."}, "hushed")
    assert said.startswith("A curate of 34.\n\nGender: male.") and "whisper" in said
