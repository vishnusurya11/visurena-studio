"""`speech_gap.over_wall` finds EVERY hole over a given wall, with the shots it
crosses; `refusal()` is rewritten as its largest-hole special case at MAX_GAP_S
and keeps the byte-identical sentence step 05 and QC refuse on.  HOLE_MARGIN_S
is the projection's safety margin: measured on ep17 (projected 4.70 vs measured
4.73) and ep18 (5.50 vs 5.54), a hole contains no spoken words, so 0.5 s is 10x
the observed error."""
from __future__ import annotations

from studio import speech_gap as sg


def placed() -> dict:
    """Two lines, a 7.75 s hole between them, a 2.0 s tail hole."""
    return {
        "duration_s": 14.0,
        "lines": [
            {"index": 0, "at": 0.25, "seconds": 2.0, "shot": 0},
            {"index": 1, "at": 10.0, "seconds": 2.0, "shot": 3},
        ],
        "shots": [
            {"index": 0, "t_start": 0.0, "t_end": 3.0},
            {"index": 1, "t_start": 3.0, "t_end": 6.0},
            {"index": 2, "t_start": 6.0, "t_end": 9.75},
            {"index": 3, "t_start": 9.75, "t_end": 14.0},
        ],
    }


def test_the_margin_is_half_a_second():
    assert sg.HOLE_MARGIN_S == 0.5


def test_over_wall_returns_every_hole_over_the_wall_with_its_shots():
    holes = sg.over_wall(placed(), sg.MAX_GAP_S - sg.HOLE_MARGIN_S)
    assert len(holes) == 1
    start, end, shots = holes[0]
    assert (start, end) == (2.25, 10.0)
    assert shots == [0, 1, 2, 3]


def test_a_lower_wall_finds_the_tail_hole_too():
    holes = sg.over_wall(placed(), 1.5)
    assert [(a, b) for a, b, _ in holes] == [(2.25, 10.0), (12.0, 14.0)]
    assert holes[1][2] == [3]


def test_refusal_is_the_byte_identical_sentence_for_the_largest_hole():
    got = sg.refusal(placed())
    assert got == (
        "REFUSED: a 7.75 s hole in speech from 2.25 s (shot 0) against the "
        f"{sg.MAX_GAP_S} s wall; shorten the holds (beat_s/coda_s) of the shots "
        "in it, or give one a line")


def test_refusal_stays_silent_under_the_wall_and_with_no_lines():
    doc = placed()
    doc["lines"][1]["at"] = 8.0          # hole shrinks to 5.75 s, under 6.0
    assert sg.refusal(doc) is None
    assert sg.refusal({"lines": [], "duration_s": 5.0}) is None
