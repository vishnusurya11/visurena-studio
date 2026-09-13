"""The mix ends where the cut ends, and keeps every frame of it.

MEASURED on episode 1, 2026-09-12: `picture.mp4` went into the mix at 3601
frames and `mixed.mp4` came out at 3597.  `-t` renders exactly the frames the
duration names; `-shortest` alongside it truncated the copied video by four.
Worse than the loss: the concat that follows then held the last picture frame
for the 0.17 s of sound that had nowhere to sit, which is a pause before the
title card that nobody cut.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio import trailer_assemble as ta


def test_a_bounded_mix_is_bounded_by_t_alone():
    assert ta.output_bound(150.041667) == ["-t", "150.0416"]


def test_shortest_never_rides_along_with_t():
    """Together they cost four frames of picture on the real cut."""
    assert "-shortest" not in ta.output_bound(150.041667)


def test_an_unbounded_mix_still_has_to_stop_somewhere():
    """The bed is `apad`ed to an infinite stream, so with no duration to render
    to, `-shortest` is the only thing that ends the file."""
    assert ta.output_bound(None) == ["-shortest"]
    assert ta.output_bound(0.0) == ["-shortest"]


def test_the_bound_renders_the_frames_the_duration_names():
    """`-t` keeps every frame whose timestamp falls below it, so 3601 frames of
    24 fps picture asks for a t inside ((3600)/24, 3601/24]."""
    bound = ta.output_bound(3601 / 24)
    assert len(bound) == 2 and 3600 / 24 < float(bound[1]) <= 3601 / 24
