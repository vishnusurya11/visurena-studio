"""Editing a cue on its MEASURED bar lines, and proving each edit inaudible.

Every test edits a synthetic click (`click_track`) or a stationary noise
"texture" and re-measures the result with the same instruments the pipeline
uses on a real cue: `beatmap.envelope_of` / `onsets` for where the clicks
land, windowed RMS for level.  Nothing here decodes a file or spends anything.
"""
from __future__ import annotations

import numpy as np
import pytest

from studio import cue_edit as ce
from studio.beatmap import RATE, envelope_of, onsets
from studio.trailer_assemble import HARD_OUT_GATE
from studio.trailer_stage_spec import Metre
from tests.test_metre import click_track

BPM = 120.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT


def metre_of(beats, downbeats, seconds, hits=()) -> Metre:
    return Metre(seed=0, rel_path="cue.wav", seconds=seconds, bpm=BPM, bar=BAR,
                 beats=beats, downbeats=downbeats, bars_in_mode=1.0, grid="metre",
                 fitness=0.0, hits=list(hits))


def click(seconds: float = 16.0):
    samples, beats, downbeats = click_track(BPM, seconds)
    return samples, metre_of(beats, downbeats, seconds)


def texture(seconds: float, level: float = 0.1, seed: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return (level * rng.standard_normal(int(seconds * RATE))).astype(np.float32)


def rms_db(x: np.ndarray) -> float:
    return float(20 * np.log10(np.sqrt(np.mean(x.astype(np.float64) ** 2)) + 1e-12))


def click_times(samples: np.ndarray, floor: float = 0.2) -> list[float]:
    """Where the clicks start, read straight off the samples.  `beatmap.onsets`
    needs a window BEFORE a rise, so it cannot see a click at t=0 -- and every
    slice here begins on one."""
    loud = np.flatnonzero(np.abs(samples) > floor)
    starts = loud[np.flatnonzero(np.diff(loud, prepend=-RATE) > 0.1 * RATE)]
    return [float(i / RATE) for i in starts]


def off_grid(times, metre: Metre, tolerance: float = 0.06) -> list[float]:
    """Click times that sit more than `tolerance` from the metre's beat lattice."""
    return [t for t in times
            if abs(((t - metre.beats[0]) / metre.beat) - round((t - metre.beats[0]) / metre.beat))
            * metre.beat > tolerance]


class TestZeroCross:
    def test_finds_the_nearest_sign_change_within_the_window(self):
        x = np.array([1, 1, 1, -1, -1, 1, 1, 1, 1, 1], dtype=np.float32)
        assert ce.zero_cross(x, 4, 3) == 3          # 3 is one away, 5 is one away: earlier wins
        assert ce.zero_cross(x, 6, 3) == 5

    def test_without_a_crossing_the_index_is_kept(self):
        x = np.ones(50, dtype=np.float32)
        assert ce.zero_cross(x, 20, 5) == 20

    def test_rms_db_of_a_full_scale_sine_is_minus_three(self):
        x = np.sin(np.linspace(0, 200 * np.pi, 44100))
        assert ce.rms_db(x) == pytest.approx(-3.01, abs=0.02)


class TestSlice:
    def test_bar_bounds_are_read_from_the_downbeats(self):
        _, metre = click(12.0)
        assert ce.bar_bounds(metre, 1, 2) == (2.5, 6.5)
        assert ce.bar_bounds(metre, 5, 5) == (10.5, 12.0)   # the last bar ends with the cue

    def test_bar_bounds_refuse_a_range_off_the_cue(self):
        _, metre = click(12.0)
        with pytest.raises(ValueError):
            ce.bar_bounds(metre, 2, 1)
        with pytest.raises(ValueError):
            ce.bar_bounds(metre, 0, 6)

    def test_a_slice_starts_and_ends_on_a_zero_crossing(self):
        _, metre = click(12.0)
        t = np.arange(int(12.0 * RATE)) / RATE
        sine = np.sin(2 * np.pi * 90.7 * t).astype(np.float32)   # 0.81 at each downbeat
        start, end = ce.cut_indices(sine, RATE, metre, 1, 2)
        assert abs(sine[int(round(2.5 * RATE))]) > 0.5                # the raw cut would click
        assert np.sign(sine[start - 1]) != np.sign(sine[start])
        assert np.sign(sine[end - 1]) != np.sign(sine[end])
        assert abs(start - 2.5 * RATE) <= ce.ZERO_WINDOW * RATE
        out = ce.slice_bars(sine, RATE, metre, 1, 2)
        assert np.array_equal(out, sine[start:end])

    def test_a_slice_is_whole_bars_long(self):
        samples, metre = click(12.0)
        out = ce.slice_bars(samples, RATE, metre, 1, 2)
        assert len(out) == pytest.approx(2 * BAR * RATE, abs=ce.ZERO_WINDOW * RATE * 2)
        times = click_times(out)
        assert len(times) == 8 and times[0] == pytest.approx(0.0, abs=ce.ZERO_WINDOW)


class TestSplice:
    def test_a_join_on_a_hit_is_ten_milliseconds(self):
        _, metre = click(8.0)
        assert ce.fade_for(metre, on_hit=True) == ce.HIT_FADE == 0.010
        assert ce.fade_for(metre, on_hit=False) == pytest.approx(BEAT / 2)

    def test_a_splice_keeps_the_level_through_the_join(self):
        a, b = texture(2.0, seed=1), texture(2.0, seed=2)
        fade = BEAT / 2
        out = ce.splice(a, b, RATE, fade)
        n = int(round(fade * RATE))
        assert len(out) == len(a) + len(b) - n
        join = out[len(a) - n:len(a)]
        assert abs(rms_db(join) - rms_db(a[-n:])) < 1.0
        assert abs(rms_db(join) - rms_db(b[:n])) < 1.0

    def test_the_second_block_is_untouched_from_the_overlap_end(self):
        a, b = texture(1.0, seed=1), texture(1.0, seed=2)
        n = int(round(0.25 * RATE))
        out = ce.splice(a, b, RATE, 0.25)
        assert np.array_equal(out[len(a):], b[n:])
        assert np.array_equal(out[:len(a) - n], a[:-n])

    def test_incompatible_levels_are_refused(self):
        loud, quiet = texture(1.0, level=0.3), texture(1.0, level=0.03)
        assert ce.compatible(loud, texture(1.0, level=0.3, seed=9), RATE, 0.25)
        assert not ce.compatible(loud, quiet, RATE, 0.25)
        with pytest.raises(ValueError):
            ce.splice(loud, quiet, RATE, 0.25)

    def test_a_fade_longer_than_a_block_is_refused(self):
        with pytest.raises(ValueError):
            ce.splice(texture(0.1), texture(1.0), RATE, 0.5)


class TestSpliceOut:
    def test_splicing_out_a_bar_shortens_the_cue_by_a_bar_and_keeps_the_downbeats_on_the_grid(self):
        samples, metre = click(16.0)
        start, end = ce.cut_indices(samples, RATE, metre, 2, 2)
        out = ce.splice_out(samples, RATE, metre, 2, 2)
        assert len(out) == len(samples) - (end - start)
        assert end - start == pytest.approx(BAR * RATE, abs=ce.ZERO_WINDOW * RATE * 2)
        before, after = click_times(samples), click_times(out)
        assert len(after) == len(before) - 4
        assert off_grid(after, metre) == []
        assert off_grid(onsets(*envelope_of(out)), metre) == []   # the pipeline's own instrument agrees
        assert np.array_equal(out[start:], samples[end:])     # the landing downbeat is untouched

    def test_splicing_out_a_run_of_bars_removes_them_all(self):
        samples, metre = click(16.0)
        out = ce.splice_out(samples, RATE, metre, 1, 3)
        assert len(click_times(out)) == len(click_times(samples)) - 12
        assert off_grid(click_times(out), metre) == []


class TestRepeat:
    def test_repeating_a_block_lengthens_the_cue_by_the_extra_copies(self):
        samples, metre = click(12.0)
        start, end = ce.cut_indices(samples, RATE, metre, 1, 2)
        out = ce.repeat_bars(samples, RATE, metre, 1, 2, times=3)
        assert len(out) == len(samples) + 2 * (end - start)
        assert len(click_times(out)) == len(click_times(samples)) + 16
        assert off_grid(click_times(out), metre) == []
        n = int(round(ce.HIT_FADE * RATE))
        assert np.array_equal(out[:end - n], samples[:end - n])   # the fade rides the bar BEFORE the landing
        assert np.array_equal(out[end:end + (end - start) - n], samples[start:end - n])   # the copy's one is untouched
        assert np.array_equal(out[-(len(samples) - end):], samples[end:])

    def test_one_time_is_the_cue_unchanged(self):
        samples, metre = click(8.0)
        assert np.array_equal(ce.repeat_bars(samples, RATE, metre, 1, 1, times=1), samples)


class TestHole:
    def test_a_hole_drops_and_returns(self):
        samples = texture(8.0)
        out = ce.hole(samples, RATE, start_s=2.0, seconds=2.0, depth_db=-30.0, return_s=0.5)
        assert len(out) == len(samples)
        sl = lambda a, b: slice(int(a * RATE), int(b * RATE))
        assert np.array_equal(out[sl(0, 2.0)], samples[sl(0, 2.0)])
        assert rms_db(out[sl(2.1, 3.4)]) - rms_db(samples[sl(2.1, 3.4)]) == pytest.approx(-30.0, abs=0.3)
        assert np.array_equal(out[sl(4.0, 8.0)], samples[sl(4.0, 8.0)])
        gain = out[sl(3.5, 4.0)] / samples[sl(3.5, 4.0)]
        assert np.all(np.diff(gain) > -1e-6)                    # the return only rises

    def test_the_gate_in_takes_the_hard_out_time(self):
        samples = np.ones(RATE * 4, dtype=np.float32)
        out = ce.hole(samples, RATE, start_s=1.0, seconds=1.0, depth_db=-40.0, return_s=0.5)
        floor = 10 ** (-40.0 / 20)
        assert out[int(1.0 * RATE) - 1] == pytest.approx(1.0)
        assert out[int((1.0 + HARD_OUT_GATE) * RATE) + 1] == pytest.approx(floor, abs=1e-3)


class TestStop:
    def test_a_stop_is_silent_after_the_out(self):
        samples, _ = click(12.0)
        out = ce.stop_at(samples, RATE, at_s=8.5, tail_s=1.0)
        at = int(round(8.5 * RATE))
        assert len(out) == at + int(round(1.0 * RATE))
        assert np.all(out[at:] == 0.0)
        assert np.array_equal(out[:int((8.5 - HARD_OUT_GATE) * RATE) - 1],
                              samples[:int((8.5 - HARD_OUT_GATE) * RATE) - 1])

    def test_a_stop_past_the_cue_is_refused(self):
        samples, _ = click(4.0)
        with pytest.raises(ValueError):
            ce.stop_at(samples, RATE, at_s=5.0, tail_s=0.5)


class TestSectionGains:
    def test_section_gains_step_at_the_bounds_and_ramp_not_click(self):
        samples = texture(8.0)
        out = ce.section_gains(samples, RATE, [(0.0, 4.0), (4.0, 8.0)], [0.0, -3.0])
        gain = out.astype(np.float64) / samples
        assert np.allclose(gain[:int(3.9 * RATE)], 1.0)
        assert np.allclose(gain[int(4.0 * RATE):], 10 ** (-3.0 / 20), atol=1e-4)
        assert np.abs(np.diff(gain)).max() < 0.01                # a ramp, not a step
        assert rms_db(out[int(4.5 * RATE):]) - rms_db(samples[int(4.5 * RATE):]) == pytest.approx(-3.0, abs=0.05)

    def test_the_ramp_ends_on_the_bound(self):
        samples = np.ones(RATE * 4, dtype=np.float32)
        out = ce.section_gains(samples, RATE, [(0.0, 2.0), (2.0, 4.0)], [0.0, 3.0], ramp_s=0.5)
        assert out[int(1.5 * RATE) - 1] == pytest.approx(1.0)
        assert out[int(1.75 * RATE)] == pytest.approx(10 ** (1.5 / 20), abs=1e-3)
        assert out[int(2.0 * RATE)] == pytest.approx(10 ** (3.0 / 20), abs=1e-3)

    def test_a_step_past_the_limit_is_refused(self):
        with pytest.raises(ValueError):
            ce.section_gains(texture(2.0), RATE, [(0.0, 1.0), (1.0, 2.0)], [0.0, -6.0])
        with pytest.raises(ValueError):
            ce.section_gains(texture(2.0), RATE, [(0.0, 1.0)], [0.0, 1.0])

    def test_gain_envelope_interpolates_in_decibels(self):
        env = ce.gain_envelope(5, RATE, [(0.0, 0.0), (4 / RATE, -6.0)])
        assert env[0] == pytest.approx(1.0)
        assert env[2] == pytest.approx(10 ** (-3.0 / 20))
        assert env[4] == pytest.approx(10 ** (-6.0 / 20))


class TestConform:
    def test_conform_rebuilds_from_kept_bars_only(self):
        samples, metre = click(24.0)
        out = ce.conform(samples, RATE, metre, [(0, 1), (4, 5), (8, 8)])
        s0, e0 = ce.cut_indices(samples, RATE, metre, 0, 1)
        s1, e1 = ce.cut_indices(samples, RATE, metre, 4, 5)
        s2, e2 = ce.cut_indices(samples, RATE, metre, 8, 8)
        assert len(out) == (e0 - s0) + (e1 - s1) + (e2 - s2)
        assert len(click_times(out)) == 20
        assert off_grid(click_times(out), metre) == []
        n = int(round(ce.HIT_FADE * RATE))
        assert np.array_equal(out[:e0 - s0 - n], samples[s0:e0 - n])
        assert np.array_equal(out[e0 - s0:e0 - s0 + e1 - s1 - n], samples[s1:e1 - n])
        assert np.array_equal(out[-(e2 - s2):], samples[s2:e2])

    def test_conform_with_no_bars_is_refused(self):
        samples, metre = click(4.0)
        with pytest.raises(ValueError):
            ce.conform(samples, RATE, metre, [])


class TestTempo:
    def test_seeds_a_percent_apart_in_tempo_are_compatible_and_more_are_not(self):
        _, a = click(8.0)
        b = a.model_copy(update={"bpm": BPM * 1.009})
        c = a.model_copy(update={"bpm": BPM * 1.03})
        assert ce.compatible_tempo(a, b)
        assert not ce.compatible_tempo(a, c)
