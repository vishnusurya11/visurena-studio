"""The gate that listens: it must catch wrong words and runaway length."""
import soundfile as sf
import numpy as np
import pytest

from studio import voice_qc

LINE = "It is better that one should perish than that many be led astray."


def clip_of(tmp_path, seconds: float, name: str = "clip.wav"):
    """A silent file of a given length -- the gate reads duration, not content."""
    path = tmp_path / name
    sf.write(path, np.zeros(int(24000 * seconds), dtype="float32"), 24000)
    return path


class TestItHearsTheSameLine:
    def test_a_perfect_transcript_scores_zero(self):
        assert voice_qc.error_rate(LINE, LINE) == 0.0

    def test_punctuation_and_case_are_not_errors(self):
        assert voice_qc.error_rate("IT IS BETTER, that one should perish; "
                                   "than that many be led astray!", LINE) == 0.0

    def test_a_curly_apostrophe_is_not_an_error(self):
        assert voice_qc.error_rate("it’s here", "it's here") == 0.0

    def test_one_wrong_word_in_thirteen_is_a_small_rate(self):
        rate = voice_qc.error_rate(
            "It is better that one should perish than that many be led away.", LINE)
        assert 0 < rate < voice_qc.MAX_ERROR_RATE

    def test_a_hallucination_scores_far_above_the_threshold(self):
        rate = voice_qc.error_rate("Thank you for watching this video.", LINE)
        assert rate > 0.5


class TestItRulesOnAClip:
    def test_a_clip_that_says_its_line_passes(self, tmp_path):
        got = voice_qc.check(clip_of(tmp_path, 4.0), LINE, transcribe=lambda _: LINE)
        assert got.passed and got.why == "said the line"

    def test_a_clip_that_says_something_else_fails(self, tmp_path):
        got = voice_qc.check(clip_of(tmp_path, 4.0), LINE,
                             transcribe=lambda _: "Subscribe to my channel.")
        assert not got.passed and "said something else" in got.why

    def test_the_right_words_at_runaway_length_still_fails(self, tmp_path):
        """Lucy's third angry pass ran 9.36 s against a 4.38 s source, and a
        transcript can match while the tail babbles."""
        source = clip_of(tmp_path, 4.38, "source.wav")
        got = voice_qc.check(clip_of(tmp_path, 9.36, "long.wav"), LINE,
                             transcribe=lambda _: LINE, source=source)
        assert not got.passed and "ran away" in got.why

    def test_a_slower_read_is_allowed_because_grief_is_slow(self, tmp_path):
        source = clip_of(tmp_path, 3.0, "source.wav")
        got = voice_qc.check(clip_of(tmp_path, 4.5, "slow.wav"), LINE,
                             transcribe=lambda _: LINE, source=source)
        assert got.passed

    def test_it_reports_what_it_actually_heard(self, tmp_path):
        got = voice_qc.check(clip_of(tmp_path, 4.0), LINE,
                             transcribe=lambda _: "something else entirely")
        assert got.heard == "something else entirely"


class TestTheReport:
    def test_failures_are_listed_before_passes(self, tmp_path):
        good = voice_qc.check(clip_of(tmp_path, 4.0, "a.wav"), LINE,
                              transcribe=lambda _: LINE)
        bad = voice_qc.check(clip_of(tmp_path, 4.0, "b.wav"), LINE,
                             transcribe=lambda _: "nonsense words here now")
        text = voice_qc.report([good, bad])
        assert text.index("b.wav") < text.index("a.wav")
        assert text.startswith("1/2 clips said their line")


class TestItRefusesToGuess:
    def test_asking_for_a_missing_model_names_the_way_out(self, monkeypatch):
        monkeypatch.setitem(voice_qc._HEARD, "fake", None)
        monkeypatch.delitem(voice_qc._HEARD, "fake")
        import builtins
        real = builtins.__import__

        def blocked(name, *args, **kwargs):
            if name == "whisper":
                raise ImportError("no whisper")
            return real(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", blocked)
        with pytest.raises(voice_qc.NoTranscriber, match="transcribe="):
            voice_qc.transcriber("nowhere")


class TestTheComfyEar:
    def test_the_clean_transcript_is_the_first_plain_text(self, tmp_path):
        clip = tmp_path / "a.wav"
        clip.write_bytes(b"RIFF")
        heard = voice_qc.comfy_transcriber(run=lambda values: [" hello there", "{'text': 'x'}"])
        import studio.comfy as comfy
        comfy.stage_image = lambda p: p.name  # no server in a test
        assert heard(clip) == "hello there"


def test_an_abbreviated_honorific_is_the_spoken_word():
    assert voice_qc.error_rate("Dr. Watson, Mr. Sherlock Holmes.",
                               "Doctor Watson, Mister Sherlock Holmes.") == 0.0


def test_a_numeral_heard_for_a_number_word_is_the_same_word():
    """ep11's countersign: Whisper heard "9. From Seven" and "7 from 5" for
    "Nine from seven" / "Seven from five" and the ear scored 0.17 and 0.33."""
    from studio import voice_qc

    assert voice_qc.normalised("9. From Seven") == voice_qc.normalised("Nine from seven")
    assert voice_qc.error_rate("Travelers for Nevada, 7 from 5.", "Travellers for Nevada. Seven from five.") == 0.0
    assert voice_qc.normalised("twenty-nine days") == voice_qc.normalised("29 days")
