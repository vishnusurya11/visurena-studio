"""A take shorter than its placed seconds is refused before the cut.

MEASURED building episode 11 (2026-09-17): two lines were edited after the
takes rendered; shot 15 placed at 8.25 s over a 5.16 s take and shot 19 at
7.08 s over 6.58 s. The picture came out 88 frames short of the audio, the
constant-rate join filled the hole with duplicates, and only the frame count
at the very end noticed. Say it at the top, with the numbers.
"""
import pytest

from scripts.episode import assemble


def test_short_takes_are_named_with_their_numbers():
    segments = [(15, 8.25), (19, 7.08), (20, 5.0)]
    seconds = {15: 5.16, 19: 6.58, 20: 7.29}
    short = assemble.short_takes(segments, lambda i: seconds[i])
    assert short == [(15, 5.16, 8.25), (19, 6.58, 7.08)]


def test_a_take_within_a_frame_of_its_shot_is_fine():
    assert assemble.short_takes([(3, 5.0)], lambda i: 4.97) == []


def test_the_cut_refuses_before_extracting_anything():
    with pytest.raises(SystemExit) as e:
        assemble.refuse_short([(15, 5.16, 8.25)])
    assert "T15" in str(e.value) and "5.16" in str(e.value) and "8.25" in str(e.value)
