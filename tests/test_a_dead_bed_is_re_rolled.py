r"""A bed 28 dB under target is a failed generation, and a warning is not a fix.

MEASURED on episode 6's first assemble, five tones generated in one pass:

    plain      -30.8 LUFS   (target -31.0)
    light      -30.5        (target -30.5)
    uneasy     -28.8        (target -29.0)
    thrilling  -27.3        (target -27.5)
    grave      -58.0        (target -29.0)   <- silence

Four landed within 0.2 dB. The fifth came back empty, `level()` printed

    WARNING bed_grave.wav: -63.4 LUFS needs +34.4 dB and the lift caps at +6.0;
    it will sit 28.4 dB under target

...and then the assemble used it anyway, which puts 29 seconds of nothing under
the Camberwell flashback -- the one span in the episode that most needs music.

`BED_MAX_LIFT_DB`'s own docstring already says what to do: "A bed far under
target is a failed generation, not something to crank." The clamp exists so the
number cannot lie; acting on it is a separate thing, and it was missing.

WHY A RE-ROLL AND NOT A LOUDER ASK. There is nothing in the request to fix -- the
same prose produced four good beds in the same pass. A generation that returns
silence is a dice roll, so the answer is another roll with a different seed, and
a REFUSAL if it keeps coming back dead rather than an unbounded loop.
"""
import pytest

from studio.episode_bed import DEAD_UNDER, is_dead


def test_a_bed_at_target_is_alive():
    assert not is_dead(-30.8, target=-31.0)


def test_a_bed_a_little_under_is_alive():
    """Within the +6 dB lift the level pass can actually recover."""
    assert not is_dead(-35.0, target=-31.0)


def test_the_silent_grave_bed_is_dead():
    """The measured case: -58.0 against a -29.0 target."""
    assert is_dead(-58.0, target=-29.0)


def test_the_number_the_clamp_printed_is_dead():
    assert is_dead(-63.4, target=-29.0)


def test_the_boundary_is_the_documented_one():
    assert is_dead(-29.0 - DEAD_UNDER - 0.1, target=-29.0)
    assert not is_dead(-29.0 - DEAD_UNDER + 0.1, target=-29.0)


def test_a_bed_louder_than_target_is_never_dead():
    """An over-loud bed is a level problem, and the level pass handles it."""
    assert not is_dead(-10.0, target=-31.0)


def test_the_threshold_is_beyond_what_the_lift_can_recover():
    """Below `BED_MAX_LIFT_DB` the level pass fixes it and nothing is wrong."""
    from scripts.episode.assemble import BED_MAX_LIFT_DB

    assert DEAD_UNDER > BED_MAX_LIFT_DB


def test_an_unmeasurable_bed_is_not_called_dead():
    """No loudnorm pass is "not measured", which is a different thing from
    "measured and empty" -- and this repo's most-found fault is treating one as
    the other."""
    assert not is_dead(None, target=-29.0)
