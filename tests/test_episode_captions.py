"""Captions come in short phrases, timed across the measured line, named when needed."""
from studio import episode_captions as cap


def test_phrases_are_short_and_break_at_punctuation():
    got = cap.phrases("Never mind. The question now is about haemoglobin.")
    assert got[0] == "Never mind."
    assert all(len(p.split()) <= 3 and len(p) <= 24 for p in got)


def test_phrase_windows_tile_the_measured_line_without_overlapping():
    windows = cap.timed(["You mustn't", "blame me", "if you"], at=10.0, seconds=3.0)
    for (_, end, _), (start, _, _) in zip(windows, windows[1:]):
        assert end <= start
    assert windows[0][0] < windows[1][0] < windows[2][0] < windows[2][1]
    assert abs(windows[-1][1] - 13.15) < 0.01


def test_a_speaker_off_screen_is_named_on_the_first_phrase_only():
    text = cap.script(768, 1344, [{"text": "I am the very man for him.", "at": 1.0,
                                   "seconds": 2.0, "speaker": "john_watson", "on_screen": False}])
    assert text.count("JOHN WATSON") == 1


def test_a_speaker_on_screen_is_not_named():
    text = cap.script(768, 1344, [{"text": "Beating the subjects!", "at": 1.0, "seconds": 1.0,
                                   "speaker": "john_watson", "on_screen": True}])
    assert "JOHN WATSON" not in text


def test_the_chip_sits_at_the_top_for_three_seconds():
    text = cap.script(768, 1344, [], chip="EP 1")
    assert "Chip,,0,0,0,,EP 1" in text and "0:00:03.00" in text
