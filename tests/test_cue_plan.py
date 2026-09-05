"""The cue plan: the music's measured spans ARE the shot list.

The contract is the spec.  Everything downstream of step 03 reads spans from
it and invents no cut of its own, so the validators here are the whole
guarantee that a cut lands where the music has an event.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from studio import cue_plan as cp
from studio.cue_plan import CuePlan, CueSection, CueSpan

BAR = 2.0  # 120 BPM, four beats


def span(index, start, end, kind, section=0, movement="M1", **kw):
    bars = round((end - start) / BAR, 3)
    return CueSpan(index=index, start=start, end=end, kind=kind, section=section,
                   movement=movement, bars=bars, **kw)


def spans_of(*specs):
    """`(start, end, kind[, movement])` tuples -> contiguous CueSpans."""
    out = []
    for i, spec in enumerate(specs):
        start, end, kind = spec[:3]
        movement = spec[3] if len(spec) > 3 else "M1"
        out.append(span(i, start, end, kind, movement=movement))
    return out


def plan_of(spans, sections=None, **kw):
    sections = sections or [CueSection(index=0, start=0.0, end=spans[-1].end,
                                       movement="M1", pulse=False, level_db=0.0)]
    fields = dict(rel_path="trailer/main/music/cue.flac", seed=1, bpm=120.0, bar=BAR,
                  seconds=spans[-1].end, sections=sections, spans=spans,
                  hard_out=spans[-1].start, title_hit=None)
    fields.update(kw)
    return CuePlan(**fields)


GOOD = spans_of((0.0, 8.0, "sustain"), (8.0, 10.0, "phrase"), (10.0, 12.0, "phrase"),
                (12.0, 12.5, "accent"), (12.5, 16.0, "trough"), (16.0, 22.0, "tail"))


class TestSpan:
    def test_a_span_knows_its_own_length(self):
        assert span(0, 0.0, 8.0, "sustain").seconds == 8.0

    def test_an_accent_longer_than_a_beat_is_refused(self):
        """An accent is an insert on a hit; at two beats it is a phrase."""
        with pytest.raises(ValidationError, match="accent"):
            span(0, 0.0, 1.5, "accent")

    def test_a_sustain_under_two_bars_is_refused(self):
        with pytest.raises(ValidationError, match="sustain"):
            span(0, 0.0, 3.0, "sustain")

    def test_a_span_shorter_than_a_shot_can_be_read_is_refused(self):
        with pytest.raises(ValidationError, match="MIN_SHOT"):
            span(0, 0.0, 0.25, "accent")


class TestPlan:
    def test_spans_cover_the_cue_without_gaps(self):
        plan = plan_of(GOOD)
        assert [s.start for s in plan.spans] == [0.0, 8.0, 10.0, 12.0, 12.5, 16.0]

    def test_a_gap_between_spans_is_refused(self):
        gapped = spans_of((0.0, 8.0, "sustain"), (8.5, 12.0, "phrase"), (12.0, 18.0, "tail"))
        with pytest.raises(ValidationError, match="contiguous"):
            plan_of(gapped)

    def test_spans_that_stop_short_of_the_cue_are_refused(self):
        with pytest.raises(ValidationError, match="cue end"):
            plan_of(GOOD, seconds=30.0)

    def test_a_section_start_that_is_not_a_cut_is_refused(self):
        """A section change the picture does not cut on is the run-10 fault:
        the boundary at 43.0 s sat inside shot B17."""
        sections = [CueSection(index=0, start=0.0, end=9.0, movement="M1", pulse=False, level_db=0.0),
                    CueSection(index=1, start=9.0, end=22.0, movement="M2", pulse=True, level_db=6.0)]
        with pytest.raises(ValidationError, match="section"):
            plan_of(GOOD, sections=sections)

    def test_movements_never_run_backwards(self):
        back = spans_of((0.0, 8.0, "sustain", "M2"), (8.0, 10.0, "phrase", "M1"),
                        (10.0, 16.0, "tail", "M1"))
        with pytest.raises(ValidationError, match="movement"):
            plan_of(back)

    def test_the_hard_out_is_where_the_tail_begins(self):
        with pytest.raises(ValidationError, match="hard_out"):
            plan_of(GOOD, hard_out=15.0)

    def test_two_sustains_side_by_side_are_refused(self):
        """A long shot reads as long only against a short one."""
        twin = spans_of((0.0, 8.0, "sustain"), (8.0, 16.0, "sustain"), (16.0, 22.0, "tail"))
        with pytest.raises(ValidationError, match="adjacent"):
            plan_of(twin)

    def test_the_picture_is_every_span_but_the_tail(self):
        assert [s.kind for s in plan_of(GOOD).picture_spans()] == [
            "sustain", "phrase", "phrase", "accent", "trough"]

    def test_spans_group_by_movement_in_order(self):
        three = spans_of((0.0, 8.0, "sustain", "M1"), (8.0, 10.0, "phrase", "M2"),
                         (10.0, 12.0, "phrase", "M2"), (12.0, 16.0, "trough", "M3"),
                         (16.0, 22.0, "tail", "M3"))
        by = plan_of(three).by_movement()
        assert [(m, len(v)) for m, v in by.items()] == [("M1", 1), ("M2", 2), ("M3", 1)]

    def test_a_line_window_is_a_trough_or_a_sustain(self):
        """A line sits where the music leaves room: in a trough the cue has,
        or under a sustain the mix can duck.  Phrases and accents are too
        short to carry speech and sections carry the reveal."""
        slots = plan_of(GOOD).line_windows()
        assert [(s.start, s.made) for s in slots] == [(0.0, True), (12.5, False)]

    def test_a_line_ends_a_beat_before_its_span_does(self):
        slots = plan_of(GOOD).line_windows()
        assert slots[0].end == 8.0 - BAR / 4 and slots[1].end == 16.0 - BAR / 4

    def test_the_plan_round_trips_through_json(self):
        plan = plan_of(GOOD)
        assert CuePlan.model_validate_json(plan.model_dump_json()) == plan


class TestAsk:
    def test_an_ask_is_bars_split_by_the_story_quota(self):
        ask = cp.CueAsk.for_bars(32, bar=BAR, bpm=120)
        assert [s.bars for s in ask.sections] == [8, 14, 10]
        assert ask.seconds == 64.0

    def test_every_event_sits_on_a_section_start(self):
        ask = cp.CueAsk.for_bars(32, bar=BAR, bpm=120)
        starts = {s.bar for s in ask.sections}
        assert all(e.bar in starts | {ask.title_bar} for e in ask.events)

    def test_an_ask_under_the_shortest_form_is_refused(self):
        with pytest.raises(ValueError, match="bars"):
            cp.CueAsk.for_bars(3, bar=BAR, bpm=120)
