"""The bed stops where the trailer speaks -- it does not duck."""
from __future__ import annotations

import numpy as np
import pytest

from studio import script_mix
from studio.trailer_assemble import DUCK_DEPTH_MAX, TARGET_LUFS, TARGET_TP


def gain_at(t: float, windows, stop_db: float = script_mix.STOP_DB) -> float:
    """Evaluate the bed expression the way ffmpeg would, for one moment."""
    expr = script_mix.bed_expr(windows, stop_db)
    return float(eval(expr.replace("\\", "").replace("max(", "max(").replace("min(", "min("),
                      {"max": max, "min": min, "t": t}))


class TestTheBedStops:
    def test_it_goes_further_down_than_any_duck(self):
        """MEASURED complaint: "music too loud... no dialogues", on a cut whose
        bed ducked by DUCK_DEPTH_DB 10, capped at 18.  Ten decibels down is
        still an orchestra on top of a cloned voice."""
        assert script_mix.STOP_DB > DUCK_DEPTH_MAX + 15

    def test_the_bed_is_out_while_the_line_plays(self):
        """Mid-line the bed is at the floor, not merely quieter."""
        quiet = gain_at(5.0, [(4.0, 7.0)])
        assert quiet < 10 ** (-30 / 20)

    def test_the_bed_is_whole_where_nobody_speaks(self):
        assert gain_at(0.5, [(4.0, 7.0)]) == pytest.approx(1.0, abs=0.01)
        assert gain_at(20.0, [(4.0, 7.0)]) == pytest.approx(1.0, abs=0.01)

    def test_it_clears_before_the_first_syllable_and_returns_after(self):
        """Out before the mouth opens, back once the line is done."""
        assert gain_at(3.95, [(4.0, 7.0)]) < 0.9            # already clearing
        assert gain_at(7.6, [(4.0, 7.0)]) == pytest.approx(1.0, abs=0.05)

    def test_two_lines_close_together_do_not_stack_into_a_hole(self):
        """The deepest window wins; overlapping stops must not multiply."""
        together = gain_at(5.0, [(4.0, 7.0), (4.5, 6.0)])
        alone = gain_at(5.0, [(4.0, 7.0)])
        assert together == pytest.approx(alone, abs=1e-6)

    def test_no_windows_leaves_the_bed_alone(self):
        assert script_mix.bed_expr([]) == "1"


class TestLanding:
    def test_the_gain_lands_the_programme_without_pushing_the_peak_over(self):
        """Whichever binds first: the loudness target or the ceiling."""
        headroom = {"lufs": -24.0, "peak": -20.0}          # loudness binds
        assert script_mix.gain_for(headroom) == pytest.approx(10.0)
        hot = {"lufs": -24.0, "peak": -4.0}                # the ceiling binds
        assert script_mix.gain_for(hot) == pytest.approx(2.0)
        over = {"lufs": -10.0, "peak": -1.0}               # already loud: comes DOWN
        assert script_mix.gain_for(over) < 0

    def test_a_line_is_laid_at_the_second_the_page_put_it(self, tmp_path):
        chains = script_mix.line_filters([(3.5, tmp_path / "a.wav"),
                                          (10.25, tmp_path / "b.wav")])
        assert "adelay=3500|3500" in chains[0]
        assert "adelay=10250|10250" in chains[1]
