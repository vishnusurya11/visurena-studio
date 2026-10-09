"""ep26 (2026-10-09 10:10Z): with a 2.2 s button line and ONE wordless closing
shot, ONE PER TAKE needs the pair at 8.3 s, so the tail (the pair less the button's
speech) is at least 6.1 s -- over G-STORY's 6.0.  No hold, no writer edit short of
cutting the closing shot can satisfy both: the two gates forbade every closing
shot after a short last line.  The tail limit is never lower than what the pair
rule itself demands when one wordless shot follows the button.  The calibration
stands (ep05 4.6 and ep07 4.7 pass; ep10's 11.5 still fails)."""
from __future__ import annotations

from studio import plan_gates


def test_one_closing_shot_after_a_short_line_gets_the_pair_floor():
    assert plan_gates.tail_limit(spoken_button=2.2, wordless_after=1) == round(8.3 - 2.2 + 0.1, 2)


def test_the_calibrated_limit_holds_otherwise():
    assert plan_gates.tail_limit(spoken_button=4.0, wordless_after=1) == plan_gates.WORDLESS_TAIL_S
    assert plan_gates.tail_limit(spoken_button=2.2, wordless_after=0) == plan_gates.WORDLESS_TAIL_S
    assert plan_gates.tail_limit(spoken_button=2.2, wordless_after=2) == plan_gates.WORDLESS_TAIL_S


def test_ep10s_long_silent_ending_still_fails():
    assert 11.5 > plan_gates.tail_limit(spoken_button=0.5, wordless_after=1)
