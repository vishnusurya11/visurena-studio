"""One record run tries a refused line up to its terminal (Jekyll ep01 HEL v2, 2026-10-14).

The narrator's l15 ("The lawyer walks on, weighing every word.") is heard right every
time and sits at 0.42-0.63 against its 0.65 floor.  `say_lines` gave each run TRIES (2)
attempts, so the keep_best terminal (TERMINAL_TRIES, 8) needed four runs -- and every
failed run went to the autopilot's brain, which parked the episode twice on "REFUSED:
say_lines.py exit 1" (v1 needed 13 relaunches).  A run now takes as many rounds as the
terminal still needs, never fewer than TRIES, so the terminal fires inside one run.
"""
from __future__ import annotations

from scripts.episode import say_lines as say


def test_a_fresh_line_gets_rounds_up_to_the_terminal():
    assert say.rounds_for({15: 0}) == say.TERMINAL_TRIES


def test_a_resumed_line_gets_only_the_rounds_it_still_needs():
    assert say.rounds_for({15: 4}) == say.TERMINAL_TRIES - 4


def test_past_the_terminal_a_run_still_takes_its_tries():
    assert say.rounds_for({15: 9}) == say.TRIES
    assert say.rounds_for({}) == say.TRIES


def test_the_least_tried_line_sets_the_rounds():
    assert say.rounds_for({3: 6, 15: 1}) == say.TERMINAL_TRIES - 1


def test_every_round_has_its_own_seed():
    got = say.attempts_from(4, 4)
    assert got == [4, 5, 6, 7] and say.attempts_from(0) == [0, 1]
