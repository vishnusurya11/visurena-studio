"""The bed stops where the trailer speaks -- it does not duck."""
from __future__ import annotations

import numpy as np
import pytest

from studio import script_mix
from studio.trailer_assemble import BED_TP, DUCK_DEPTH_MAX, TARGET_LUFS, TARGET_TP


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

    def test_every_max_takes_exactly_two_arguments(self):
        """MEASURED, the first real mix: nine spoken windows produced a nine-arg
        max() and ffmpeg refused it -- "Missing ')' or too many args".  Python's
        own max() is variadic, so the unit tests passed while the mix died.  The
        expression folds pairwise instead."""
        expr = script_mix.bed_expr([(1.0, 2.0), (5.0, 6.0), (9.0, 10.0),
                                    (13.0, 14.0), (17.0, 18.0)])
        depth, worst = 0, 0
        for i, ch in enumerate(expr):
            if expr[max(0, i - 4):i + 1].endswith("max("):
                depth += 1
            args = 0
        # every max( ... ) in the string encloses exactly one top-level comma
        for start in [i for i in range(len(expr)) if expr.startswith("max(", i)]:
            level, commas = 0, 0
            for j in range(start + 4, len(expr)):
                if expr[j] == "(":
                    level += 1
                elif expr[j] == ")":
                    if level == 0:
                        break
                    level -= 1
                elif expr[j] == "," and level == 0 and expr[j - 1] == "\\":
                    commas += 1
            assert commas == 1, f"max() at {start} has {commas + 1} args"

    def test_no_windows_leaves_the_bed_alone(self):
        assert script_mix.bed_expr([]) == "1"


class TestHeadroomIsMadeAtTheSource:
    """MEASURED, the first real premix: bed and lines summed raw landed at
    -19.39 LUFS with a true peak of +0.05 dBTP, so the ceiling bound the gain
    and the master would have shipped 7 dB quiet.  The repo learned this in
    run 10 -- "handed the mix a bed at +0.4 dBTP and a cue at +0.2, then asked
    the limiter to fix it" -- and the answer is headroom BEFORE the sum."""

    def test_the_bed_is_peak_limited_before_it_is_summed(self, tmp_path):
        chain = script_mix.bed_chain([(4.0, 7.0)])
        assert "alimiter" in chain and str(BED_TP) not in chain.split("alimiter")[0]

    def test_every_line_is_peak_limited_before_it_is_summed(self, tmp_path):
        chains = script_mix.line_filters([(3.5, tmp_path / "a.wav")])
        assert "alimiter" in chains[0]


class TestLanding:
    def test_the_master_is_levelled_by_a_measured_two_pass_loudnorm(self):
        """MEASURED, the first real premix: peak-limiting alone left the sum at
        -19.2 LUFS with a -1.26 dBTP peak, so a single gain could only take it
        DOWN and the master would have shipped 6 dB quiet.  Two-pass loudnorm
        applies ONE measured gain toward the target -- single-pass runs in
        dynamic mode and reshapes the dynamics the cue was chosen for."""
        reading = {"lufs": -19.2, "peak": -1.26, "lra": 9.4, "thresh": -29.6}
        chain = script_mix.level_chain(reading)
        assert "loudnorm" in chain and "linear=true" in chain
        assert "measured_I=-19.2" in chain and "measured_tp=-1.26" in chain.lower()
        assert f"I={TARGET_LUFS}" in chain and f"TP={TARGET_TP}" in chain

    def test_a_line_is_laid_at_the_second_the_page_put_it(self, tmp_path):
        chains = script_mix.line_filters([(3.5, tmp_path / "a.wav"),
                                          (10.25, tmp_path / "b.wav")])
        assert "adelay=3500|3500" in chains[0]
        assert "adelay=10250|10250" in chains[1]
