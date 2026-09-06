"""The editor's arc: a rendered cue's bars re-ordered by MEASURED level into
the ask's staircase, then the ask's holes, stop and title hit cut on top.

Every test builds a stationary noise texture whose bars sit at planted
levels in a scrambled order, on a uniform 120 BPM grid, and re-measures the
result with `beatmap.envelope_of` -- the instrument step 03 grades with.
Nothing decodes a file or spends anything.
"""
from __future__ import annotations

import numpy as np
import pytest

from studio import cue_arc
from studio.beatmap import RATE, envelope_of
from studio.cue_ask import HOLE_BARS
from studio.cue_plan import AskedEvent, CueAsk
from studio.trailer_stage_spec import Metre

BPM = 120.0
BAR = 4 * 60.0 / BPM


def metre_of(bars: int) -> Metre:
    downbeats = [i * BAR for i in range(bars)]
    beats = [i * BAR / 4 for i in range(bars * 4)]
    return Metre(seed=0, rel_path="cue.wav", seconds=bars * BAR, bpm=BPM, bar=BAR,
                 beats=beats, downbeats=downbeats, bars_in_mode=1.0, grid="metre", fitness=0.0)


def planted(levels_db: list[float], seed: int = 1) -> np.ndarray:
    """Noise whose every bar sits at the planted RMS level."""
    rng = np.random.default_rng(seed)
    out = np.concatenate([10 ** (db / 20) * rng.standard_normal(int(BAR * RATE)) for db in levels_db])
    return out.astype(np.float32)


SCRAMBLED = [-20.0, -12.0, -30.0, -24.0, -6.0, -18.0, -28.0, -10.0,
             -26.0, -14.0, -22.0, -8.0, -16.0, -32.0, -34.0, -36.0]
"""Sixteen bars, four phrases whose means are -21.5, -15.5, -17.5, -29.5."""


def measured_bar_levels(samples: np.ndarray, bars: int) -> list[float]:
    times, db = envelope_of(samples)
    return [float(np.median(db[(times >= i * BAR) & (times < (i + 1) * BAR)])) for i in range(bars)]


def test_bar_levels_reads_the_planted_levels():
    samples = planted(SCRAMBLED)
    times, db = envelope_of(samples)
    levels = cue_arc.bar_levels(metre_of(16), times, db)
    assert len(levels) == 16
    assert np.allclose(levels, SCRAMBLED, atol=1.5)


def test_phrases_of_keeps_whole_phrases_only():
    assert cue_arc.phrases_of(16) == [(0, 3), (4, 7), (8, 11), (12, 15)]
    assert cue_arc.phrases_of(18) == [(0, 3), (4, 7), (8, 11), (12, 15)]
    assert cue_arc.phrases_of(6, phrase=2) == [(0, 1), (2, 3), (4, 5)]


def test_ascending_orders_phrases_by_their_mean_level():
    levels = np.array(SCRAMBLED)
    order = cue_arc.ascending(levels, cue_arc.phrases_of(16))
    assert order == [(12, 15), (0, 3), (8, 11), (4, 7)]


def test_bar_order_fills_exactly_the_bars_asked_repeating_the_loudest():
    levels = np.array(SCRAMBLED)
    order = cue_arc.bar_order(levels, 10)
    assert order == [12, 13, 14, 15, 0, 1, 2, 3, 8, 9]
    long = cue_arc.bar_order(levels, 20)
    assert len(long) == 20 and long[16:] == [4, 5, 6, 7]


def test_regular_bars_flags_a_bar_the_tracker_stretched():
    """A stop's silence swallowed a downbeat in one render: the tracker
    reported a 4 s "bar" at 120 BPM.  Cut into the arc it shifts every asked
    bar after it by one, so an irregular bar is no phrase material."""
    metre = metre_of(16)
    downbeats = [d for i, d in enumerate(metre.downbeats) if i != 9]
    stretched = metre.model_copy(update={"downbeats": downbeats})
    regular = cue_arc.regular_bars(stretched)
    assert regular.tolist() == [True] * 8 + [False] + [True] * 6


def test_bar_order_leaves_out_a_phrase_holding_an_irregular_bar():
    levels = np.array(SCRAMBLED)
    usable = np.array([True] * 16)
    usable[13] = False
    order = cue_arc.bar_order(levels, 12, usable=usable)
    assert order == [0, 1, 2, 3, 8, 9, 10, 11, 4, 5, 6, 7]


def test_grid_of_lays_four_beats_on_every_arc_bar():
    """The arc's bar lines are known by construction; re-tracking a cue
    through its own deliberate silences loses the downbeats inside them."""
    beats, downbeats = cue_arc.grid_of([0.0, 2.0, 4.0], 2.0)
    assert downbeats == [0.0, 2.0, 4.0]
    assert beats == [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5]


def test_ranges_of_groups_consecutive_bars():
    assert cue_arc.ranges_of([0, 1, 2, 5, 6, 9]) == [(0, 2), (5, 6), (9, 9)]
    assert cue_arc.ranges_of([3]) == [(3, 3)]


def test_step_join_is_a_short_equal_power_crossfade():
    a = np.full(RATE, 0.5, dtype=np.float32)
    b = np.full(RATE, 0.5, dtype=np.float32)
    out = cue_arc.step_join(a, b, RATE)
    n = int(cue_arc.STEP_FADE * RATE)
    assert len(out) == 2 * RATE - n
    assert np.all(out[RATE - n:RATE] > 0.49) and np.all(out[RATE - n:RATE] <= 0.71)


def test_assemble_lands_each_range_on_the_next_downbeat():
    samples, metre = planted(SCRAMBLED), metre_of(16)
    out, downbeats = cue_arc.assemble(samples, RATE, metre, [(12, 15), (0, 1)])
    assert len(downbeats) == 6
    assert abs(len(out) / RATE - 6 * BAR) < 0.05
    assert np.allclose(downbeats, [i * BAR for i in range(6)], atol=0.02)


def test_arc_is_a_staircase_ending_in_stop_silence_and_the_title_hit():
    samples, metre = planted(SCRAMBLED), metre_of(16)
    ask = CueAsk.for_bars(16, bar=BAR, bpm=int(BPM))
    out, downbeats = cue_arc.arc(samples, RATE, metre, ask, *envelope_of(samples))
    assert len(downbeats) == ask.bars
    assert abs(len(out) / RATE - ask.seconds) < BAR
    levels = measured_bar_levels(out, ask.bars)
    stop, title = 11, ask.title_bar
    phrase_means = [np.mean(levels[i:i + 4]) for i in range(0, stop - 3, 4)]
    assert all(b >= a for a, b in zip(phrase_means, phrase_means[1:]))
    assert levels[stop] < levels[stop - 1] - 30 and levels[title - 1] < levels[stop - 1] - 30
    assert levels[title] > levels[title - 1] + 20


def test_arc_gates_every_asked_hole_and_returns_on_its_downbeat():
    samples, metre = planted(SCRAMBLED), metre_of(16)
    ask = CueAsk.for_bars(16, bar=BAR, bpm=int(BPM))
    ask = ask.model_copy(update={"events": ask.events + [AskedEvent(kind="hole", bar=6)]})
    whole, _ = cue_arc.arc(samples, RATE, metre, ask.model_copy(update={"events": ask.events[:-1]}),
                           *envelope_of(samples))
    out, _ = cue_arc.arc(samples, RATE, metre, ask, *envelope_of(samples))
    levels, before = measured_bar_levels(out, ask.bars), measured_bar_levels(whole, ask.bars)
    assert levels[6] < before[6] - 30 and levels[6 + HOLE_BARS - 1] < before[6 + HOLE_BARS - 1] - 30
    assert abs(levels[6 + HOLE_BARS] - before[6 + HOLE_BARS]) < 1.0 and abs(levels[5] - before[5]) < 1.0


def test_hit_bar_is_the_loudest_onset_bar_of_the_cue():
    samples, metre = planted(SCRAMBLED), metre_of(16)
    samples[int(4 * BAR * RATE):int(4 * BAR * RATE) + 200] += 3.0
    times, db = envelope_of(samples)
    assert cue_arc.hit_bar(metre, times, db) == 4


def test_arc_refuses_a_cue_with_fewer_bars_than_one_phrase():
    samples, metre = planted(SCRAMBLED[:3]), metre_of(3)
    ask = CueAsk.for_bars(8, bar=BAR, bpm=int(BPM))
    with pytest.raises(ValueError):
        cue_arc.arc(samples, RATE, metre, ask, *envelope_of(samples))


def test_octave_steps_is_the_doubling_that_brings_the_bar_nearest_the_ask():
    """MEASURED (run 13): the tracker read raw-1001 at 214 BPM (1.12 s bars)
    against 100 asked and the arc cut 38 of them: a 43.7 s cue for a 91.2 s
    ask.  A tempo octave is the tracker's ambiguity, not the render's."""
    assert cue_arc.octave_steps(1.12, 2.4) == 1
    assert cue_arc.octave_steps(0.56, 2.4) == 2
    assert cue_arc.octave_steps(2.92, 2.4) == 0          # within the octave band: the render's bar
    assert cue_arc.octave_steps(1.82, 2.4) == 0
    assert cue_arc.octave_steps(4.8, 2.4) == -1


def test_at_octave_merges_bars_in_pairs_and_keeps_the_grid_consistent():
    metre = metre_of(16)
    up = cue_arc.at_octave(metre, 2 * BAR)
    assert up.bar == pytest.approx(2 * BAR) and up.bpm == pytest.approx(BPM / 2)
    assert up.downbeats == [i * 2 * BAR for i in range(8)]
    assert set(up.downbeats) <= set(up.beats) and up.seconds == metre.seconds
    assert Metre.model_validate(up.model_dump())


def test_at_octave_splits_bars_at_their_midpoints():
    metre = metre_of(8)
    down = cue_arc.at_octave(metre, BAR / 2)
    assert down.bar == pytest.approx(BAR / 2) and down.bpm == pytest.approx(2 * BPM)
    assert down.downbeats == pytest.approx([i * BAR / 2 for i in range(16)])
    assert set(down.downbeats) <= set(down.beats)


def test_at_octave_leaves_a_bar_inside_the_octave_band_alone():
    metre = metre_of(8)
    assert cue_arc.at_octave(metre, BAR * 1.3) is metre
