"""A take prompt that fails the lint says WHICH take.

MEASURED on episode 13 (2026-09-17): the dry build stopped on "L8 NO PACE
[Shot 1]" -- and every single-shot take's own shot is [Shot 1], so the message
named none of 28 takes.  The refusal now leads with the take and its shots.
"""
import sys

import pytest

sys.path.insert(0, "scripts/episode")


def test_a_lint_failure_is_raised_with_the_take_and_its_shots():
    import takes_r2v

    def fails(*_a, **_k):
        raise ValueError("the prompt fails the lint (1 faults): L8 NO PACE [Shot 1]: a walk")

    with pytest.raises(SystemExit, match=r"T05 \(shots \[5\]\).*L8 NO PACE"):
        takes_r2v.named_card(fails, {"shots": [5]})


def test_a_card_that_builds_is_returned_unchanged():
    import takes_r2v

    assert takes_r2v.named_card(lambda: {"prompt": "ok"}, {"shots": [2]}) == {"prompt": "ok"}
