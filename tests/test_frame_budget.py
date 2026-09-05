"""Frames buy picture seconds; picture seconds bound the cue that is asked for.

Every number here is arithmetic on H3's grid (`studio.h3`), the take tax the
cut already pays (`HEAD_TRIM`, `HANDLE`) and the typed cycle the FLAG table
carries until a round measures one.  Nothing renders, nothing is paid for.
"""
from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from studio import frame_budget as fb
from studio.cue_plan import MIN_FORM_BARS, CuePlan, CueSection, CueSpan
from studio.frame_budget import Cycle
from studio.h3 import FPS
from studio.learnings import Learning

BAR = 2.0  # 120 BPM, four beats


def span(index, start, end, kind, movement="M1"):
    return CueSpan(index=index, start=start, end=end, kind=kind, section=0,
                   movement=movement, bars=round((end - start) / BAR, 3))


def plan_of(*specs):
    spans = [span(i, *spec) for i, spec in enumerate(specs)]
    section = CueSection(index=0, start=0.0, end=spans[-1].end, movement="M1",
                         pulse=False, level_db=0.0)
    return CuePlan(rel_path="trailer/main/music/cue.flac", seed=1, bpm=120.0, bar=BAR,
                   seconds=spans[-1].end, sections=[section], spans=spans,
                   hard_out=spans[-1].start)


GOOD = plan_of((0.0, 8.0, "sustain"), (8.0, 10.0, "phrase"), (10.0, 12.0, "phrase"),
               (12.0, 12.5, "accent"), (12.5, 16.0, "trough"), (16.0, 22.0, "tail"))
"""Picture spans 8, 2, 2, 0.5 and 3.5 s: takes of 277, 124, 124, 90 and 158
frames, 773 in all."""


def cycle_row(frames, seconds, gate="cycle", **kw):
    """A learning row as step 07 writes it; `frames` only when asked for."""
    row = dict(step="07", gate=gate, measured=seconds, threshold=960.0,
               action="round_1", seconds=seconds)
    if frames is not None:
        row["frames"] = frames
    row.update(kw)
    return row


class TestTake:
    def test_a_take_carries_the_head_trim_and_the_handle(self):
        assert fb.take_seconds(2.0) == pytest.approx(2.0 + 2.6 + 0.25)
        assert fb.TAKE_TAX == pytest.approx(2.85)
        assert fb.TAX_FRAMES == 69

    def test_frames_snap_up_to_the_legal_ladder(self):
        """2 s asks for 117 frames and gets 124; 8 s asks for 261 and gets 277."""
        assert fb.take_frames(2.0) == 124
        assert fb.take_frames(8.0) == 277
        assert fb.take_frames(1.0) == 107
        assert fb.take_frames(0.6) == 90
        for shot in (0.6, 1.0, 2.0, 4.0, 8.0):
            assert fb.take_frames(shot) % 17 == 5
            assert fb.take_frames(shot) >= math.ceil(fb.take_seconds(shot) * FPS)

    def test_a_shot_past_the_longest_take_is_refused(self):
        assert fb.take_frames(fb.LONGEST_SHOT) == fb.MAX_FRAMES
        with pytest.raises(ValueError, match="362"):
            fb.take_frames(fb.LONGEST_SHOT + 0.1)

    def test_a_shot_must_have_length(self):
        with pytest.raises(ValueError):
            fb.take_frames(0.0)


class TestCycle:
    def test_a_cycle_prices_frames_per_take(self):
        cycle = Cycle(a=10.0, b=2.0)
        assert cycle.cost_seconds(124) == pytest.approx(258.0)
        assert cycle.cost_seconds(124, takes=3) == pytest.approx(3 * 10.0 + 2.0 * 124)

    def test_a_negative_fixed_cost_is_refused(self):
        with pytest.raises(ValidationError):
            Cycle(a=-1.0, b=2.0)
        with pytest.raises(ValidationError):
            Cycle(a=0.0, b=0.0)

    def test_with_no_rows_the_cycle_is_the_typed_curve(self):
        cycle = Cycle.from_rows([])
        assert (cycle.a, cycle.b) == (fb.A_TYPED, fb.B_TYPED)
        assert cycle.b == 2.49

    def test_two_frame_counts_fit_a_line(self):
        rows = [cycle_row(124, 400.0), cycle_row(277, 706.0)]
        cycle = Cycle.from_rows(rows)
        assert cycle.b == pytest.approx(2.0)
        assert cycle.a == pytest.approx(152.0)

    def test_one_frame_count_keeps_the_typed_slope(self):
        rows = [cycle_row(175, 450.0), cycle_row(175, 470.0), cycle_row(175, 900.0)]
        cycle = Cycle.from_rows(rows)
        assert cycle.b == fb.B_TYPED
        assert cycle.a == pytest.approx(470.0 - 2.49 * 175)

    def test_rows_without_frames_are_not_points_on_the_line(self):
        """Run-10 rows carry seconds per take and no frame count, and every one
        of them paid a reload the round renderer does not: they say nothing
        about seconds per frame, so the curve stays typed."""
        rows = [Learning(step="07", gate="cycle", measured=945.6, action="round_1"),
                Learning(step="07", gate="cycle", measured=930.0, action="round_2")]
        assert fb.cycle_points(rows) == []
        assert Cycle.from_rows(rows) == fb.TYPED

    def test_only_cycle_rows_are_read(self):
        rows = [cycle_row(124, 400.0), cycle_row(277, 706.0),
                cycle_row(362, 5.0, gate="read"), cycle_row(362, "stalled")]
        assert fb.cycle_points(rows) == [(124, 400.0), (277, 706.0)]

    def test_a_fit_with_a_negative_intercept_falls_back_to_the_typed_slope(self):
        """Two noisy rounds whose line crosses below zero: a fixed cost under
        zero is a fiction, so the slope stays typed and the offset is the median."""
        rows = [cycle_row(124, 100.0), cycle_row(277, 900.0)]
        cycle = Cycle.from_rows(rows)
        assert cycle.b == fb.B_TYPED
        assert cycle.a >= 0.0

    def test_fit_line_is_least_squares(self):
        a, b = fb.fit_line([(124, 400.0), (277, 706.0), (175, 502.0)])
        assert b == pytest.approx(2.0)
        assert a == pytest.approx(152.0)

    def test_a_line_needs_two_distinct_frame_counts(self):
        with pytest.raises(ValueError, match="distinct"):
            fb.fit_line([(175, 400.0), (175, 420.0)])

    def test_the_typed_slope_runs_through_the_medians(self):
        cycle = fb.typed_slope([(124, 300.0), (124, 320.0), (124, 9000.0)])
        assert cycle == Cycle(a=320.0 - 2.49 * 124, b=2.49)
        assert fb.typed_slope([(362, 1.0)]).a == 0.0

    def test_a_row_is_read_the_same_as_a_dict_or_a_learning(self):
        learning = Learning(step="07", gate="cycle", measured=400.0, action="round_1")
        assert fb._field({"measured": 400.0}, "measured") == 400.0
        assert fb._field(learning, "measured") == 400.0
        assert fb._field(learning, "frames") is None
        assert fb._field({}, "frames") is None


class TestFramesAndPicture:
    def test_a_plan_costs_one_take_per_picture_span(self):
        assert fb.plan_frames(GOOD.picture_spans()) == 277 + 124 + 124 + 90 + 158

    def test_longer_shots_are_cheaper_per_picture_second(self):
        """24 s of picture: twelve 2 s shots cost 1488 frames, three 8 s shots 831."""
        short = fb.plan_frames([span(i, 2.0 * i, 2.0 * (i + 1), "phrase") for i in range(12)])
        long = fb.plan_frames([span(i, 8.0 * i, 8.0 * (i + 1), "sustain") for i in range(3)])
        assert short == 1488
        assert long == 831
        assert long < short

    def test_the_reserve_is_kept_back(self):
        unit = Cycle(a=0.0, b=1.0)
        assert fb.affordable_frames(1000.0, unit, takes=1, reserve=0.0) == 1000
        assert fb.affordable_frames(1000.0, unit, takes=1) == 850
        assert fb.RETRY_RESERVE == 0.15

    def test_every_take_pays_its_fixed_cost_first(self):
        cycle = Cycle(a=10.0, b=1.0)
        assert fb.affordable_frames(1000.0, cycle, takes=5, reserve=0.0) == 950
        assert fb.affordable_frames(40.0, cycle, takes=5, reserve=0.0) == 0

    def test_picture_seconds_undo_the_take_tax(self):
        """A take pays 69 frames of tax and, on average, 8 of legal rounding."""
        assert fb.picture_seconds(124 * 12, takes=12) == pytest.approx((1488 - 12 * 77) / 24)
        assert fb.picture_seconds(277, takes=1) == pytest.approx((277 - 77) / 24)
        assert fb.picture_seconds(10, takes=1) == 0.0

    def test_bars_never_round_up(self):
        assert fb.bars_for(17.99, BAR) == 8
        assert fb.bars_for(16.0, BAR) == 8
        assert fb.bars_for(40.5, BAR) == 20
        with pytest.raises(ValueError, match=str(MIN_FORM_BARS)):
            fb.bars_for(15.99, BAR)


class TestShare:
    def test_a_sixty_second_trailer_fits_the_share(self):
        """The corpus mix -- 4 sustains of 8 s, 10 phrases of 2 s, 8 accents
        of 1 s, 60 s of picture in 22 takes -- at the typed curve, inside the
        210 min share of step 07 with the retry reserve kept back."""
        assert sum(fb.CORPUS_MIX) == pytest.approx(60.0)
        frames = sum(fb.take_frames(s) for s in fb.CORPUS_MIX)
        minutes = fb.TYPED.cost_seconds(frames, takes=len(fb.CORPUS_MIX)) / 60
        assert frames == 3204
        assert minutes == pytest.approx(132.97, abs=0.01)
        assert minutes <= 210 * (1 - fb.RETRY_RESERVE)

    def test_cue_seconds_scale_the_mix_to_the_budget(self):
        """A budget that pays for the mix exactly affords the mix's own length."""
        frames = sum(fb.take_frames(s) for s in fb.CORPUS_MIX)
        cost = fb.TYPED.cost_seconds(frames, takes=len(fb.CORPUS_MIX))
        assert fb.cue_seconds_for(cost, fb.TYPED, fb.CORPUS_MIX, reserve=0.0) == pytest.approx(60.0)
        assert fb.cue_seconds_for(2 * cost, fb.TYPED, fb.CORPUS_MIX, reserve=0.0) == pytest.approx(120.0)
        assert fb.cue_seconds_for(cost, fb.TYPED, fb.CORPUS_MIX) == pytest.approx(51.0)

    def test_the_share_affords_forty_bars_at_the_corpus_mix(self):
        seconds = fb.cue_seconds_for(210 * 60, fb.TYPED, fb.CORPUS_MIX)
        assert seconds == pytest.approx(80.54, abs=0.01)
        assert fb.bars_for(seconds, BAR) == 40

    def test_an_empty_mix_is_refused(self):
        with pytest.raises(ValueError, match="mix"):
            fb.cue_seconds_for(1000.0, fb.TYPED, [])

    def test_a_plan_fits_when_its_takes_cost_less_than_the_share_kept(self):
        """GOOD's 773 frames cost 1924.8 s at the typed curve."""
        assert fb.fits(GOOD, 3000.0, fb.TYPED)
        assert not fb.fits(GOOD, 2000.0, fb.TYPED)
        assert fb.fits(GOOD, 2000.0, fb.TYPED, reserve=0.0)
