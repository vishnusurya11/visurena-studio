"""Voice: a reference designed from the card, every line cloned from it, and the
seconds MEASURED from the file.

Nothing here renders.  `comfy.run` is replaced by a fake that writes a
synthetic wav of a length the TEXT could never predict, so a seconds value
that matches the file proves the measurement path and a value derived from
the words would fail.  Speaker similarity needs a real model and a real
render, so the threshold test is local-only.
"""
from __future__ import annotations

import math
import os
import struct
import wave
from pathlib import Path

import pytest

from studio import comfy, voice
from studio.trailer_stage_spec import VoiceLine

local = pytest.mark.skipif(not os.environ.get("VISURENA_LOCAL"),
                           reason="needs the local ComfyUI and a GPU; set VISURENA_LOCAL=1")


def write_wav(path: Path, seconds: float, hz: float = 220.0, rate: int = 24000) -> Path:
    """A mono sine of exactly `seconds`, the file a fake engine hands back."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(seconds * rate)
    with wave.open(str(path), "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(rate)
        fh.writeframes(b"".join(
            struct.pack("<h", int(12000 * math.sin(2 * math.pi * hz * i / rate)))
            for i in range(frames)))
    return path


class FakeComfy:
    """Records what it was asked and returns a wav the test chose."""

    def __init__(self, produced: Path, seconds: float):
        self.produced, self.seconds, self.calls = produced, seconds, []

    def __call__(self, name, values, timeout=3600.0):
        self.calls.append((name, dict(values)))
        return [write_wav(self.produced, self.seconds)]


HOLMES = {
    "id": "sherlock_holmes", "name": "Sherlock Holmes", "role": "protagonist",
    "aliases": ["Holmes", "the detective", "my friend"],
    "profile": {
        "physical": "A young man of restless energy, over six feet, excessively lean.",
        "mental": "Highly analytical, observant, energetic when presented with a case.",
        "voice": "His speech is direct, confident, formal, and concise. He explains "
                 "deductions bluntly."},
    "quotes": [{"chapter": 1, "quote": "“You have been in Afghanistan, I perceive.”"}],
}


@pytest.fixture()
def book(tmp_path):
    out = tmp_path / "book" / "trailer" / "main" / "voice"
    out.mkdir(parents=True)
    return tmp_path / "book"


class TestCloneLine:
    def test_clone_line_writes_measured_seconds(self, tmp_path, book, monkeypatch):
        fake = FakeComfy(tmp_path / "engine" / "out.wav", seconds=2.75)
        monkeypatch.setattr(comfy, "run", fake)
        monkeypatch.setattr(comfy, "stage_image", lambda p: Path(p).name)
        reference = write_wav(book / "trailer/main/voice/refs/sherlock_holmes.wav", 6.0)
        reference.with_suffix(".txt").write_text("You have been in Afghanistan.", encoding="utf-8")
        out = book / "trailer/main/voice/lines/00-1.wav"

        line = voice.clone_line(reference, "Poison.", seed=11, out=out, index=0,
                                speaker="sherlock_holmes")

        assert isinstance(line, VoiceLine)
        assert out.exists()
        # 2.75s from the file; one word could never predict that.
        assert line.seconds == pytest.approx(2.75, abs=0.05)
        assert line.rel_path == "trailer/main/voice/lines/00-1.wav"
        assert line.seed == 11 and line.speaker == "sherlock_holmes" and not line.card

    def test_the_clone_is_keyed_on_the_reference_and_its_text(self, tmp_path, book, monkeypatch):
        fake = FakeComfy(tmp_path / "engine" / "out.wav", seconds=1.0)
        monkeypatch.setattr(comfy, "run", fake)
        staged = []
        monkeypatch.setattr(comfy, "stage_image", lambda p: staged.append(Path(p)) or Path(p).name)
        reference = write_wav(book / "trailer/main/voice/refs/lucy.wav", 6.0)
        reference.with_suffix(".txt").write_text("Where is mother?", encoding="utf-8")

        voice.clone_line(reference, "Kiss it and make it well.", seed=3,
                         out=book / "trailer/main/voice/lines/01-3.wav")

        name, values = fake.calls[0]
        assert name == voice.CLONE_WORKFLOW
        # Staged under a content hash, not `lucy.wav`: two books' narrators must not collide.
        assert values["ref_audio"] == staged[0].name != "lucy.wav"
        assert staged[0].read_bytes() == reference.read_bytes()
        assert values["ref_text"] == "Where is mother?"
        assert values["target_text"] == "Kiss it and make it well."
        assert values["seed"] == 3
        assert values["max_new_tokens"] == voice.MAX_LINE_TOKENS

    def test_a_line_lands_at_the_line_level(self, tmp_path, book, monkeypatch):
        """Every line arrives at the same loudness so the ducker keys on the same thing."""
        fake = FakeComfy(tmp_path / "engine" / "out.wav", seconds=2.0)
        monkeypatch.setattr(comfy, "run", fake)
        monkeypatch.setattr(comfy, "stage_image", lambda p: Path(p).name)
        reference = write_wav(book / "trailer/main/voice/refs/x.wav", 6.0)
        out = book / "trailer/main/voice/lines/00-1.wav"
        voice.clone_line(reference, "A line.", seed=1, out=out)
        assert voice.integrated_lufs(out) == pytest.approx(voice.LINE_LUFS, abs=1.0)


class TestDesignReference:
    def test_design_reference_uses_the_character_card(self, tmp_path, book, monkeypatch):
        fake = FakeComfy(tmp_path / "engine" / "ref.wav", seconds=8.0)
        monkeypatch.setattr(comfy, "run", fake)
        refs = book / "trailer/main/voice/refs"

        path = voice.design_reference(HOLMES, refs)

        name, values = fake.calls[0]
        assert name == voice.DESIGN_WORKFLOW
        instruct = values["instruct"].lower()
        assert "man" in instruct and "young" in instruct
        assert "direct, confident, formal" in instruct
        # The reference sentence is the character's own, not a trailer line.
        assert values["text"] == "You have been in Afghanistan, I perceive."
        assert path == refs / "sherlock_holmes.wav" and path.exists()
        assert path.with_suffix(".txt").read_text(encoding="utf-8") == values["text"]
        assert 15 <= len(values["instruct"].split()) <= 40

    def test_a_designed_reference_is_cached_by_speaker(self, tmp_path, book, monkeypatch):
        fake = FakeComfy(tmp_path / "engine" / "ref.wav", seconds=8.0)
        monkeypatch.setattr(comfy, "run", fake)
        refs = book / "trailer/main/voice/refs"
        voice.design_reference(HOLMES, refs)
        voice.design_reference(HOLMES, refs)
        assert len(fake.calls) == 1

    def test_instruct_never_names_an_accent(self):
        """An accent word drifts the model to American; era goes into diction."""
        instruct = voice.voice_instruct(HOLMES).lower()
        assert not any(w in instruct for w in ("accent", "british", "english", "american"))
        assert "diction" in instruct

    def test_reference_text_falls_back_when_the_card_has_no_quote(self):
        assert voice.reference_text({"id": "x", "quotes": []}) == voice.NEUTRAL_SENTENCE
        assert voice.reference_text({"id": "x", "quotes": [{"quote": "Yes."}]}) == voice.NEUTRAL_SENTENCE

    def test_a_woman_is_described_as_one(self):
        lucy = {"id": "lucy", "name": "Lucy Ferrier", "aliases": ["the girl", "his daughter"],
                "profile": {"physical": "a young woman", "voice": "She speaks plainly."}}
        assert "woman" in voice.voice_instruct(lucy).lower()


class TestInstructParts:
    def test_first_sentence_gets_a_full_stop(self):
        assert voice._first_sentence("Blunt and dry") == "Blunt and dry."
        assert voice._first_sentence("Blunt. Dry.") == "Blunt."
        assert voice._first_sentence("") == ""

    def test_a_long_card_is_cut_to_forty_words(self):
        long = dict(HOLMES, profile=dict(HOLMES["profile"], voice=" ".join(["word"] * 30) + "."))
        assert len(voice.voice_instruct(long).split()) <= voice.MAX_INSTRUCT_WORDS


class TestSimilarity:
    def test_a_file_is_most_similar_to_itself(self, tmp_path):
        pytest.importorskip("resemblyzer")
        a = write_wav(tmp_path / "a.wav", 2.0, hz=180.0)
        assert voice.similarity(a, a) == pytest.approx(1.0, abs=1e-4)


class TestSeeds:
    def test_one_seed_per_character_and_a_new_one_per_reroll(self):
        first, second = voice.seed_for("holmes", 0), voice.seed_for("holmes", 1)
        assert first != second
        assert voice.seed_for("holmes", 0) == first
        assert voice.seed_for("watson", 0) != first


class TestBookRelative:
    def test_paths_are_relative_to_the_book(self, tmp_path):
        path = tmp_path / "lib" / "b" / "trailer" / "main" / "voice" / "lines" / "a.wav"
        assert voice.book_relative(path) == "trailer/main/voice/lines/a.wav"

    def test_a_path_outside_a_book_is_refused(self, tmp_path):
        with pytest.raises(ValueError):
            voice.book_relative(tmp_path / "elsewhere" / "a.wav")


@local
@pytest.mark.local
class TestThresholdLocal:
    def test_threshold_separates_two_designed_voices(self, tmp_path):
        """Two designed voices, five clones each: every same-voice pair must sit above
        SIMILARITY_FLOOR and every cross-voice pair below it.  This is the run
        that set the floor (2026-09-04: same 0.696-0.884, cross 0.393-0.521);
        print the two ranges so a rerun leaves its own evidence."""
        refs = tmp_path / "refs"
        holmes = voice.design_reference(HOLMES, refs)
        lucy = voice.design_reference(
            {"id": "lucy_ferrier", "name": "Lucy Ferrier", "aliases": ["the girl"],
             "profile": {"physical": "a young woman", "voice": "She speaks softly and plainly."},
             "quotes": [{"quote": "That is what mother used to do. Where is mother?"}]}, refs)
        lines = ["There has been murder done.", "The question now is about haemoglobin.",
                 "You would lose your money.", "I wrote the article myself.", "Come along."]
        same, cross = [], []
        for i, text in enumerate(lines):
            h = voice.clone_line(holmes, text, seed=i, out=tmp_path / "trailer/main/h" / f"{i}.wav")
            l = voice.clone_line(lucy, text, seed=i, out=tmp_path / "trailer/main/l" / f"{i}.wav")
            same += [h.similarity or voice.similarity(tmp_path / h.rel_path, holmes),
                     voice.similarity(tmp_path / l.rel_path, lucy)]
            cross += [voice.similarity(tmp_path / h.rel_path, lucy),
                      voice.similarity(tmp_path / l.rel_path, holmes)]
        print(f"same {min(same):.3f}-{max(same):.3f}  cross {min(cross):.3f}-{max(cross):.3f}")
        assert min(same) >= voice.SIMILARITY_FLOOR
        assert max(cross) < voice.SIMILARITY_FLOOR
