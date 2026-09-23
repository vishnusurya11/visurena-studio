"""A command that writes an episode must be told which episode.

MEASURED 2026-09-22 (audit): twenty CLIs under scripts/episode fell back to
episode 1 when the number was missing, and takes_r2v tested `isdigit()` on
argv[2] -- so `takes_r2v.py <book> --retake=3` read the flag, failed the digit
test, and would have re-rendered EPISODE ONE's take 3 on the GPU. A default
episode is a guess about the one thing the command is for.
"""
import pytest

from studio.episode_home import episode_arg


def test_the_episode_is_the_second_plain_argument():
    assert episode_arg(["prog", "book", "9"]) == 9


def test_flags_before_or_after_do_not_move_it():
    assert episode_arg(["prog", "--approved", "book", "--retake=3", "9"]) == 9


def test_a_missing_episode_refuses_rather_than_guessing():
    with pytest.raises(SystemExit, match="episode"):
        episode_arg(["prog", "book", "--retake=3"])


def test_a_word_where_the_number_goes_refuses():
    with pytest.raises(SystemExit, match="episode"):
        episode_arg(["prog", "book", "nine"])


def test_episode_zero_refuses():
    with pytest.raises(SystemExit, match="episode"):
        episode_arg(["prog", "book", "0"])
