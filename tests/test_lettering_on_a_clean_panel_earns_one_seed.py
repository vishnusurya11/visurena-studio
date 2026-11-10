"""Jekyll ep07 retro S11: T21's panel read `text: false` and its take `text: true` -- the lettering was
render-borne, yet `lettering` is INPUT_BORNE and routed to '' (no cure), so five rolls never aimed at
it.  On a clean panel lettering earns one seed, like content; a second, repeated sighting is the
terminal's.  The (lettering, seed) rate row starts at (0, 0) so the outcome is counted, not assumed."""
from __future__ import annotations

from studio import take_ladder
from studio.judges.verdict import Fault


def lettering(**evidence) -> Fault:
    return Fault(where="T21", kind="lettering", severity="high", note="text or lettering in the picture",
                 evidence=evidence)


def test_lettering_on_a_clean_panel_is_one_seed():
    assert take_ladder.cure_of([lettering()], panel_clean=True) == "seed"


def test_lettering_the_panel_also_drew_is_the_boards():
    assert take_ladder.cure_of([lettering()], panel_clean=False) == ""


def test_a_repeated_lettering_after_its_seed_is_the_terminals():
    assert take_ladder.cure_of([lettering(repeated=True)], panel_clean=True) == ""


def test_the_lettering_seed_rate_is_counted_from_zero():
    assert take_ladder.CURE_RATES[("lettering", "seed")] == (0, 0)
