"""Putting the chosen lines onto actual beats.

`dialogue_candidates` and `pick_lines` existed, were tested, and were imported
by nothing.  0 of 9 Scarlet beats and 0 of 14 Jekyll beats carried a line, so
the trailers were silent -- the "add dialogues" ask, unbuilt.
"""
from __future__ import annotations

from studio.trailer_dialogue import assign_lines, speech_seconds

BEATS = [
    {"beat_id": "B00", "scene": 3, "cast": ["sherlock_holmes"], "seconds": 3.5},
    {"beat_id": "B01", "scene": 7, "cast": ["john_watson"], "seconds": 1.0},
    {"beat_id": "B02", "scene": 9, "cast": ["sherlock_holmes"], "seconds": 3.0},
    {"beat_id": "B03", "scene": 11, "cast": ["jefferson_hope"], "seconds": 3.2},
]
LINES = [
    {"scene": 9, "speaker": "sherlock_holmes", "text": "There is a scarlet thread of murder.",
     "emotion": "quiet", "seconds": 2.4, "risk": 0.0, "score": 9.0},
    {"scene": 11, "speaker": "jefferson_hope", "text": "I have hunted him across the world.",
     "emotion": "level", "seconds": 2.6, "risk": 0.0, "score": 8.0},
    {"scene": 3, "speaker": "john_watson", "text": "You have been in Afghanistan, I perceive.",
     "emotion": "calm", "seconds": 2.8, "risk": 0.0, "score": 7.0},
]


class TestAssignLines:
    def test_a_line_lands_on_a_beat_whose_speaker_is_present(self):
        for beat_id, line in assign_lines(BEATS, LINES).items():
            beat = next(b for b in BEATS if b["beat_id"] == beat_id)
            assert line["speaker"] in beat["cast"]

    def test_a_line_may_carry_across_the_cut_that_follows_it(self):
        """A line starts on the speaker and runs over the next picture -- that
        is how trailers work, and requiring it to fit inside one 2.5s shot
        placed exactly one line in each of two trailers."""
        placed = assign_lines(BEATS, LINES)
        for beat_id, line in placed.items():
            start = next(i for i, b in enumerate(BEATS) if b["beat_id"] == beat_id)
            room = sum(b["seconds"] for b in BEATS[start:start + line["span"]])
            assert speech_seconds(line["text"]) <= room + 1e-9

    def test_a_line_never_runs_past_the_shots_it_was_given(self):
        placed = assign_lines(BEATS, LINES)
        for beat_id, line in placed.items():
            assert 1 <= line["span"] <= 2

    def test_two_lines_never_overlap_the_same_picture(self):
        """A line spanning two shots owns both; nothing else may start there."""
        placed = assign_lines(BEATS, LINES)
        owned: list[int] = []
        for beat_id, line in placed.items():
            start = next(i for i, b in enumerate(BEATS) if b["beat_id"] == beat_id)
            owned += list(range(start, start + line["span"]))
        assert len(owned) == len(set(owned))

    def test_the_line_prefers_the_beat_from_its_own_scene(self):
        """A line spoken over its own moment is dialogue; anywhere else it is
        voice-over, and voice-over over the wrong picture is a lie."""
        assigned = assign_lines(BEATS, LINES)
        assert assigned["B02"]["speaker"] == "sherlock_holmes"
        assert assigned["B02"]["scene"] == 9

    def test_a_beat_carries_at_most_one_line(self):
        assigned = assign_lines(BEATS, LINES)
        assert len(assigned) == len(set(assigned))

    def test_a_line_is_never_used_twice(self):
        assigned = assign_lines(BEATS, LINES)
        texts = [line["text"] for line in assigned.values()]
        assert len(texts) == len(set(texts))

    def test_a_line_still_needs_somewhere_to_finish(self):
        """B01 is 1.0s and is the last beat Watson appears in; his line needs
        2.8s and there is nowhere for it to land."""
        short = [dict(b, seconds=0.4) for b in BEATS]
        assert assign_lines(short, LINES) == {}

    def test_no_lines_yields_no_assignment_rather_than_an_error(self):
        assert assign_lines(BEATS, []) == {}

    def test_it_leaves_most_of_the_trailer_silent(self):
        """A trailer that talks throughout is a scene, not a trailer."""
        assigned = assign_lines(BEATS, LINES, ceiling=2)
        assert len(assigned) <= 2
