"""INVENTED SPEECH (owner, 2026-10-11): H3 writes its own audio, and in the
digitally silent tail of the voice guide (the line padded to take length) it
sometimes speaks words nobody recorded -- S4_B3ck "...a man indeed. Indeed.",
D1_B3ck "Dead! ... HAHAHAHAHAHA!".  The master drops H3's audio, but the mouth
moves in that tail and the picture ships.  The check: where the guide's speech
ends, cut the take's own audio from there to the end; a tail that carries sound
is heard by local Whisper, and every word it hears is invented.  Mouth motion
in the tail against during the line is measured beside it (advisory)."""
import numpy as np

from studio import invented_speech as inv

SR = 16000


def tone(seconds: float, db: float) -> np.ndarray:
    t = np.arange(int(seconds * SR)) / SR
    return (10 ** (db / 20) * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def guide() -> np.ndarray:
    return np.concatenate([tone(2.0, -12), np.zeros(SR * 2, np.float32)])


def test_the_line_ends_where_the_guide_falls_silent():
    assert abs(inv.speech_end(guide(), SR) - 2.0) < 0.06


def test_a_silent_tail_is_not_sent_to_the_ear():
    take = np.concatenate([tone(2.0, -12), np.zeros(SR * 2, np.float32)])
    v = inv.check(take, guide(), SR, hear=lambda clip: 1 / 0)
    assert v["passed"] and v["words"] == [] and v["tail_db"] < inv.QUIET_DB


def ear(take_said: str, line_said: str = "He was a man indeed."):
    """The whole take and the whole guide are heard (a tail heard alone hallucinates)."""
    said = iter([take_said, line_said])                 # the take is heard first, then the guide
    return lambda clip: next(said)


def test_words_after_the_lines_last_word_are_invented():
    take = np.concatenate([tone(2.0, -12), tone(2.0, -15)])
    v = inv.check(take, guide(), SR, hear=ear("He was a man indeed. Indeed. Heed."))
    assert not v["passed"] and v["words"] == ["indeed", "heed"]


def test_a_sounding_tail_that_adds_no_word_passes():
    take = np.concatenate([tone(2.0, -12), tone(2.0, -15)])
    assert inv.check(take, guide(), SR, hear=ear("He was a man, indeed."))["passed"]


def test_a_misheard_word_inside_the_line_is_not_invented():
    take = np.concatenate([tone(2.0, -12), tone(2.0, -15)])
    assert inv.check(take, guide(), SR, hear=ear("He was a mad indeed."))["passed"]


def test_the_extra_words_are_what_follows_the_last_matched_line_word():
    assert inv.extra(["dead", "every", "one"], ["dead", "every", "one", "ha", "ha"]) == ["ha", "ha"]
    assert inv.extra(["a", "man", "indeed"], ["a", "man", "indeed"]) == []


def test_a_guide_with_no_tail_has_nothing_to_check():
    take = tone(2.0, -12)
    assert inv.check(take, tone(2.0, -12), SR, hear=lambda clip: 1 / 0)["passed"]


def test_mouth_motion_in_the_tail_is_read_against_the_line():
    rng = np.random.default_rng(0)
    still = [np.full((20, 20), 100, np.float32)] * 4
    moving = [rng.uniform(0, 255, (20, 20)).astype(np.float32) for _ in range(4)]
    assert inv.motion_ratio(moving, still) < 0.1
    assert inv.motion_ratio(moving, moving) > 0.5


def test_a_take_without_a_voice_guide_is_not_a_dialogue_take():
    from scripts.bench import speech_tail
    graph = {"21": {"class_type": "LoadAudio", "inputs": {"audio": "silence_03_ab.wav"}}}
    assert speech_tail.check_one("x.mp4", graph, hear=lambda s: 1 / 0) is None


def test_the_review_copy_carries_the_recorded_guide_not_h3s_sound():
    from pathlib import Path
    from scripts.bench import speech_tail
    cmd = speech_tail.review_cmd(Path("t.mp4"), Path("voice.wav"), Path("t_review.mp4"))
    assert cmd[cmd.index("-map") + 1] == "0:v:0" and "1:a:0" in cmd and cmd[-1] == "t_review.mp4"
