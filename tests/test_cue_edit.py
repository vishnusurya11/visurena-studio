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
from studio.cue_plan import CueSection
from studio.trailer_stage_spec import Metre, Slot
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
        _, beats, downbeats = click_track(BPM, 8.0)
        metre = metre_of(beats, downbeats, 8.0, hits=[4.5])
        assert ce.fade_for(metre, on_hit=True) == ce.HIT_FADE == 0.010
        assert ce.fade_for(metre, on_hit=False) == pytest.approx(BEAT / 2)
        assert ce.fade_at(metre, 4.5) == ce.HIT_FADE                 # a measured hit
        assert ce.fade_at(metre, 4.5 + ce.ZERO_WINDOW) == ce.HIT_FADE   # the cut moved to a zero crossing
        assert ce.fade_at(metre, 6.5) == pytest.approx(BEAT / 2)     # texture continues
        assert ce.fade_at(metre, 6.5, marks=[6.5]) == ce.HIT_FADE    # a section start the plan names

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


class TestGrid:
    """The layer steps 03 and 08 call: a span read back to its bars, and the
    grid the cue HAS after an edit, so the plan is re-derived from a metre that
    agrees with the samples."""

    def test_bars_covering_reads_a_span_back_to_its_bars(self):
        _, metre = click(16.0)                       # downbeats 0.5, 2.5, ... 14.5; the cue ends at 16.0
        assert ce.bars_covering(metre, 4.5, 8.5) == (2, 3)
        assert ce.bars_covering(metre, 14.5, 16.0) == (7, 7)   # the last bar ends where the cue ends
        assert ce.bars_covering(metre, 4.5 + ce.ZERO_WINDOW, 8.5) == (2, 3)
        with pytest.raises(ValueError):
            ce.bars_covering(metre, 5.0, 8.5)        # a span opening off the downbeat is not bars

    def test_runs_collapse_bar_indices_to_ranges(self):
        assert ce.runs([0, 1, 4, 5, 8]) == [(0, 1), (4, 5), (8, 8)]
        assert ce.runs(range(3)) == [(0, 2)]
        assert ce.runs([5, 4, 4]) == [(4, 5)]
        assert ce.runs([]) == []

    def test_keep_spans_lays_the_kept_seconds_out_contiguously(self):
        _, beats, downbeats = click_track(BPM, 16.0)
        metre = metre_of(beats, downbeats, 16.0, hits=[8.5, 6.5]).model_copy(
            update={"title_hit": 10.5, "stopdowns": [7.0],
                    "slots": [Slot(start=8.5, end=12.5), Slot(start=2.5, end=6.5)]})
        kept = ce.keep_spans(metre, [(0.5, 4.5), (8.5, 12.5)])
        assert kept.seconds == 8.0
        assert kept.downbeats == [0.0, 2.0, 4.0, 6.0]
        assert len(kept.beats) == 16 and set(kept.downbeats) <= set(kept.beats)
        assert kept.hits == [4.0]                    # 6.5 fell in the dropped seconds
        assert kept.title_hit == pytest.approx(6.0) and kept.stopdowns == []   # 7.0 was in the dropped bars
        assert [(s.start, s.end) for s in kept.slots] == [(4.0, 8.0)]   # a slot cut by the edit is gone
        assert (kept.bpm, kept.bar, kept.grid, kept.seed) == (metre.bpm, metre.bar, metre.grid, metre.seed)

    def test_conform_bars_returns_the_audio_and_the_grid_it_now_has(self):
        samples, metre = click(24.0)
        out, recut = ce.conform_bars(samples, RATE, metre, [0, 1, 4, 5, 8])
        assert np.array_equal(out, ce.conform(samples, RATE, metre, [(0, 1), (4, 5), (8, 8)]))
        assert recut.metre.downbeats == [0.0, 2.0, 4.0, 6.0, 8.0]
        assert recut.metre.seconds == 10.0
        assert abs(len(out) / RATE - recut.metre.seconds) <= 2 * ce.ZERO_WINDOW
        assert off_grid(click_times(out), recut.metre) == []
        assert [(e.op, e.first_bar, e.last_bar, e.at) for e in recut.edits] == [
            ("keep", 0, 1, 0.0), ("keep", 4, 5, 4.0), ("keep", 8, 8, 8.0)]
        assert recut.edits[0].fade_s == 0.0 and recut.edits[1].fade_s == ce.HIT_FADE

    def test_conform_bars_from_a_range_is_the_head_of_the_cue(self):
        samples, metre = click(16.0)
        out, recut = ce.conform_bars(samples, RATE, metre, range(0, 4))
        assert np.array_equal(out, ce.slice_bars(samples, RATE, metre, 0, 3))
        assert recut.metre.seconds == 8.0 and len(recut.edits) == 1

    def test_remove_bars_is_splice_out_with_the_grid_shifted(self):
        _, beats, downbeats = click_track(BPM, 16.0)
        samples = click(16.0)[0]
        metre = metre_of(beats, downbeats, 16.0, hits=[4.5, 8.5])
        out, recut = ce.remove_bars(samples, RATE, metre, 2, 2)
        assert np.array_equal(out, ce.splice_out(samples, RATE, metre, 2, 2))
        assert recut.metre.seconds == 14.0
        assert recut.metre.downbeats == [0.5, 2.5, 4.5, 6.5, 8.5, 10.5, 12.5]   # the pre-roll stays
        assert recut.metre.hits == [6.5]              # the hit on the removed bar is gone, the later one moved
        assert off_grid(click_times(out), recut.metre) == []
        assert abs(len(out) / RATE - recut.metre.seconds) <= 2 * ce.ZERO_WINDOW
        assert [(e.op, e.first_bar, e.last_bar, e.at, e.fade_s) for e in recut.edits] == [
            ("remove", 2, 2, 4.5, ce.HIT_FADE)]

    def test_a_span_between_events_is_removed_by_the_second(self):
        """Run 11's cues measure as onsets, not bars: the plan's spans sit on
        events, and a lost span is cut out between two of them."""
        _, beats, downbeats = click_track(BPM, 16.0)
        samples = click(16.0)[0]
        metre = metre_of(beats, downbeats, 16.0, hits=[4.5, 8.5])
        out, recut = ce.remove_range(samples, RATE, metre, 4.5, 6.5)
        assert np.array_equal(out, ce.remove_bars(samples, RATE, metre, 2, 2)[0])
        assert recut.metre.seconds == 14.0 and recut.metre.hits == [6.5]
        assert [(e.op, e.start_s, e.end_s, e.at, e.fade_s) for e in recut.edits] == [
            ("cut", 4.5, 6.5, 4.5, ce.HIT_FADE)]

    def test_a_join_off_every_hit_fades_over_half_a_beat(self):
        samples, metre = click(16.0)
        _, recut = ce.remove_range(samples, RATE, metre, 4.5, 6.5)
        assert recut.edits[0].fade_s == BEAT / 2

    def test_a_stereo_cue_is_cut_as_one_where_its_mid_crosses_zero(self):
        """The delivered cue is 44.1 kHz stereo; both channels are cut at the
        same sample, chosen on the mid, or the image smears at the join."""
        mono, metre = click(16.0)
        stereo = np.stack([mono, mono], axis=1)
        out, recut = ce.remove_bars(stereo, RATE, metre, 2, 2)
        expect = ce.remove_bars(mono, RATE, metre, 2, 2)[0]
        assert out.shape == (len(expect), 2)
        assert np.array_equal(out[:, 0], expect) and np.array_equal(out[:, 1], expect)

    def test_a_hole_a_stop_and_the_staircase_keep_both_channels(self):
        mono = texture(8.0)
        stereo = np.stack([mono, mono], axis=1)
        assert ce.hole(stereo, RATE, 2.0, 2.0, -30.0, 0.25).shape == stereo.shape
        stopped = ce.stop_at(stereo, RATE, 4.0, 1.0)
        assert stopped.shape == (5 * RATE, 2) and np.array_equal(stopped[:, 0], stopped[:, 1])
        stepped = ce.section_gains(stereo, RATE, [(0.0, 4.0), (4.0, 8.0)], [0.0, 3.0])
        assert stepped.shape == stereo.shape

    def test_hole_bars_is_a_hole_over_whole_bars_returning_on_the_downbeat(self):
        samples, metre = click(8.0)
        out = ce.hole_bars(samples, RATE, metre, 1, 1, depth_db=-30.0, return_s=0.25)
        assert np.array_equal(out, ce.hole(samples, RATE, 2.5, 2.0, -30.0, 0.25))

    def test_section_bounds_read_from_the_plan_sections(self):
        sections = [CueSection(index=0, start=0.0, end=4.5, movement="M1", pulse=False, level_db=-24.0),
                    CueSection(index=1, start=4.5, end=12.5, movement="M2", pulse=True, level_db=-18.0)]
        assert ce.section_bounds(sections) == [(0.0, 4.5), (4.5, 12.5)]

    def test_the_helpers_under_the_grid_layer(self):
        _, metre = click(8.0)                        # downbeats 0.5, 2.5, 4.5, 6.5
        assert ce.lands_on(4.505, [4.5]) and not ce.lands_on(4.6, [4.5])
        assert ce.bar_at(metre, 2.5) == 1
        with pytest.raises(ValueError):
            ce.bar_at(metre, 3.0)
        spans = [(0.5, 4.5), (6.5, 8.0)]
        assert ce.offsets_of(spans) == [0.0, 4.0]
        assert ce.shifted([0.5, 4.5, 6.5, 7.9], spans) == [0.0, 4.0, 5.4]   # 4.5 closes the first span
        assert ce.kept_slots([Slot(start=6.5, end=8.0), Slot(start=4.0, end=6.5)], spans) == [
            Slot(start=4.0, end=5.5)]
        edits = ce.keep_edits([(0, 1), (3, 3)], spans, ce.HIT_FADE)
        assert [(e.at, e.fade_s) for e in edits] == [(0.0, 0.0), (4.0, ce.HIT_FADE)]
