"""From the cut map to the cue plan: every rank >= 2 event is a cut, the
picture holds between them, and the fit rule bends the CUE, never the story.

The cut map is hand-made so every span's class is known in advance; the
metre is a 120 BPM click (bar 2.0 s, beat 0.5 s).  Nothing here decodes
audio or spends anything.
"""
from __future__ import annotations

import pytest

from studio import cue_spans as cs
from studio import frame_budget as fb
from studio.cue_plan import SUSTAIN_BARS, CuePlan
from studio.cue_spans import ShorterCue
from studio.music_events import CutMap
from studio.trailer_stage_spec import Metre
from test_metre import click_track

BAR, BEAT = 2.0, 0.5


@pytest.fixture(scope="module")
def metre() -> Metre:
    _, beats, downbeats = click_track(120, 30.0)
    return Metre(seed=1, rel_path="trailer/music/cue-1.flac", seconds=30.0, bpm=120.0,
                 bar=BAR, beats_per_bar=4, beats=beats, downbeats=downbeats,
                 bars_in_mode=1.0, grid="metre", fitness=1.0, title_hit=22.5)


def ev(t, rank, kind, density=2.0, level=-20.0, **kw):
    return dict(t=t, rank=rank, kind=kind, evidence=[kind], affords=1.0,
                level_db=level, onset_density=density, **kw)


EVENTS = [ev(4.5, 3, "section"),                 # 0.0-4.5 is 2.25 bars of hold: a sustain
          ev(6.5, 2, "phrase"),                  # 4.5-6.5 opened by the section
          ev(8.5, 2, "phrase"),
          ev(10.5, 3, "hit"),
          ev(11.0, 2, "phrase"),                 # 10.5-11.0 is one beat on a hit: an accent
          ev(12.5, 3, "section"),
          ev(14.5, 2, "phrase"),
          ev(20.5, 3, "dropout", end=22.5),      # 14.5-20.5 is three bars: a sustain
          ev(22.5, 3, "hit"),                    # the title hit
          ev(26.5, 2, "phrase")]                 # past the hard out: the tail's business
SPANS = [dict(start=0.0, end=4.5, kind="hold", level_db=-24.0, rises_db=0.4, onset_density=1.0),
         dict(start=14.5, end=20.5, kind="swell", level_db=-18.0, rises_db=9.0, onset_density=2.0),
         dict(start=20.5, end=22.5, kind="dropout", level_db=-40.0, rises_db=0.2, onset_density=0.0)]


def cut_map_of(events=EVENTS, spans=SPANS, hard_out=24.5, title_hit=22.5, seconds=30.0) -> CutMap:
    return CutMap.model_validate(dict(events=events, spans=spans, hard_out=hard_out,
                                      title_hit=title_hit, seconds=seconds))


@pytest.fixture(scope="module")
def plan(metre) -> CuePlan:
    return cs.plan_of(cut_map_of(), metre, rel_path="trailer/music/cue-1.flac", seed=1)


def kinds(plan_or_spans):
    spans = plan_or_spans.spans if isinstance(plan_or_spans, CuePlan) else plan_or_spans
    return [(s.start, s.end, s.kind) for s in spans]


# --- cuts --------------------------------------------------------------------

class TestCuts:
    def test_every_rank_two_event_is_a_cut(self, metre, plan):
        starts = {s.start for s in plan.spans}
        for e in cut_map_of().events:
            if e.rank >= 2 and e.t < 24.5:
                assert e.t in starts

    def test_cut_times_run_from_zero_to_the_hard_out(self, metre):
        cuts = cs.cut_times(cut_map_of(), metre)
        assert cuts[0] == 0.0 and cuts[-1] == 24.5
        assert 26.5 not in cuts

    def test_two_cuts_inside_a_shot_keep_the_higher_rank(self, metre):
        events = [ev(4.5, 2, "phrase"), ev(4.7, 3, "hit"), ev(10.5, 2, "phrase")]
        cuts = cs.cut_times(cut_map_of(events=events, spans=[]), metre)
        assert 4.7 in cuts and 4.5 not in cuts

    def test_a_cut_a_flash_frame_before_the_hard_out_yields_to_it(self, metre):
        events = [ev(11.8, 2, "phrase")]
        assert cs.cut_times(cut_map_of(events=events, spans=[], hard_out=12.0), metre) == [0.0, 12.0]

    def test_a_rank_one_accent_is_held_through(self, metre):
        events = [ev(4.5, 1, "accent"), ev(10.5, 2, "phrase")]
        assert cs.cut_times(cut_map_of(events=events, spans=[], hard_out=20.5), metre) == [
            0.0, 10.5, 20.5]


# --- classes -----------------------------------------------------------------

class TestTakeLength:
    """A hold longer than the longest take H3 renders cannot be one shot:
    it is cut where the grid says, the rank-1 event nearest its middle
    before a downbeat before a beat, and never inside MIN_SHOT of an end."""

    def test_a_hold_longer_than_a_take_is_cut_on_the_accent_nearest_its_middle(self, metre):
        events = [ev(7.0, 1, "accent"), ev(9.0, 1, "accent"), ev(16.5, 3, "section"),
                  ev(22.5, 3, "hit")]
        cuts = cs.cut_times(cut_map_of(events=events, spans=[]), metre)
        assert cuts == [0.0, 9.0, 16.5, 22.5, 24.5]

    def test_a_hold_with_no_accent_is_cut_on_the_downbeat_nearest_its_middle(self, metre):
        cuts = cs.cut_times(cut_map_of(events=[ev(16.5, 3, "section"), ev(22.5, 3, "hit")],
                                       spans=[]), metre)
        assert cuts == [0.0, 8.5, 16.5, 22.5, 24.5]

    def test_every_hold_of_the_split_fits_a_take(self, metre):
        cuts = cs.cut_times(cut_map_of(events=[ev(22.5, 3, "hit")], spans=[], hard_out=29.0,
                                       seconds=30.0), metre)
        assert all(b - a <= fb.LONGEST_SHOT for a, b in zip(cuts, cuts[1:]))
        assert cuts[0] == 0.0 and cuts[-1] == 29.0

    def test_split_point_keeps_a_shot_clear_of_both_ends(self, metre):
        assert cs.split_point(0.0, 13.0, cut_map_of(events=[ev(0.4, 1, "accent")], spans=[]),
                              metre) == 6.5

    def test_the_spans_of_a_split_hold_are_a_sustain_and_a_phrase(self, metre):
        plan = cs.plan_of(cut_map_of(events=[ev(16.5, 3, "section"), ev(22.5, 3, "hit")],
                                     spans=[]), metre, rel_path="m/cue.flac", seed=1)
        assert kinds(plan)[:3] == [(0.0, 8.5, "sustain"), (8.5, 16.5, "phrase"),
                                   (16.5, 22.5, "section")]


class TestKinds:
    def test_a_long_hold_becomes_a_sustain(self, plan):
        assert (0.0, 4.5, "sustain") in kinds(plan)
        assert (14.5, 20.5, "sustain") in kinds(plan)
        assert 4.5 / BAR >= SUSTAIN_BARS

    def test_a_section_boundary_opens_a_section_span(self, plan):
        assert (4.5, 6.5, "section") in kinds(plan)
        assert (12.5, 14.5, "section") in kinds(plan)

    def test_a_beat_on_a_hit_is_an_accent(self, plan):
        assert (10.5, 11.0, "accent") in kinds(plan)

    def test_a_dropout_before_the_title_is_a_trough(self, plan):
        assert (20.5, 22.5, "trough") in kinds(plan)

    def test_a_dropout_after_the_title_is_no_trough(self, metre):
        events = [ev(4.5, 3, "dropout", end=6.5), ev(6.5, 2, "phrase")]
        spans = cs.spans_of(cut_map_of(events=events, spans=[], title_hit=2.5), metre, {0: "M1"})
        assert (4.5, 6.5, "phrase") in kinds(spans)

    def test_the_rest_are_phrases(self, plan):
        assert (6.5, 8.5, "phrase") in kinds(plan) and (22.5, 24.5, "phrase") in kinds(plan)

    def test_the_tail_starts_at_the_hard_out(self, plan):
        assert plan.spans[-1].kind == "tail"
        assert plan.spans[-1].start == plan.hard_out == 24.5
        assert plan.spans[-1].end == 30.0

    def test_two_sustains_never_sit_side_by_side(self, metre):
        """Two long holds back to back: the shorter reads as a phrase, because
        a long shot reads long only against a short one."""
        events = [ev(6.5, 2, "phrase"), ev(10.5, 2, "phrase")]
        spans = cs.spans_of(cut_map_of(events=events, spans=[], hard_out=20.5), metre, {0: "M1"})
        assert [k for _, _, k in kinds(spans)] == ["sustain", "phrase", "sustain", "tail"]

    def test_spans_are_contiguous_over_the_cue(self, plan):
        assert plan.spans[0].start == 0.0 and plan.spans[-1].end == 30.0
        assert all(a.end == b.start for a, b in zip(plan.spans, plan.spans[1:]))


class TestSpanFields:
    def test_a_span_opens_on_the_downbeat_it_starts_on(self, metre):
        assert cs.opens_on(4.5, metre) == "downbeat"
        assert cs.opens_on(5.0, metre) == "beat"
        assert cs.opens_on(5.2, metre) == "event"

    def test_a_trough_carries_its_line_room(self, plan):
        trough = next(s for s in plan.spans if s.kind == "trough")
        assert trough.line_room == 2.0

    def test_a_span_inside_a_swell_carries_its_rise(self, plan):
        sustain = next(s for s in plan.spans if s.start == 14.5)
        assert sustain.rises_db == 9.0
        assert sustain.onset_density == 2.0

    def test_a_span_reads_its_level_off_the_event_that_opens_it(self, plan):
        assert next(s for s in plan.spans if s.start == 6.5).level_db == -20.0


class TestHelpers:
    def test_the_opening_event_is_the_highest_ranked_at_that_instant(self):
        events = [ev(4.5, 2, "phrase"), ev(4.5, 3, "section")]
        assert cs.opening_event(cut_map_of(events=events, spans=[]), 4.5).kind == "section"
        assert cs.opening_event(cut_map_of(), 0.0) is None

    def test_kind_of_reads_a_short_section_span_as_a_section(self, metre):
        """A movement door is never an accent, or the fit rule could move it."""
        events = [ev(4.5, 3, "section"), ev(5.0, 2, "phrase")]
        assert cs.kind_of(4.5, 5.0, cut_map_of(events=events, spans=[]), metre) == "section"
        assert cs.kind_of(24.5, 30.0, cut_map_of(), metre) == "tail"

    def test_untwinned_demotes_the_shorter_of_two_sustains(self):
        kinds = ["sustain", "sustain", "sustain", "tail"]
        assert cs.untwinned(kinds, [0.0, 6.0, 10.0, 20.0, 30.0]) ==             ["sustain", "phrase", "sustain", "tail"]

    def test_trough_room_stops_at_the_dropout_or_the_span(self):
        opener = cs.CutEvent(t=20.5, rank=3, kind="dropout", evidence=["dropout"], end=22.5)
        assert cs.trough_room(opener, 24.5) == 2.0 and cs.trough_room(opener, 21.5) == 1.0
        assert cs.trough_room(None, 24.5) == 0.0

    def test_swell_rise_is_the_overlapping_swell(self):
        assert cs.swell_rise(cut_map_of(), 16.5, 18.5) == 9.0
        assert cs.swell_rise(cut_map_of(), 0.0, 4.5) == 0.0

    def test_section_starts_are_zero_and_the_section_cuts(self):
        assert cs.section_starts(cut_map_of(), [0.0, 4.5, 12.5, 24.5]) == [0.0, 4.5, 12.5]
        assert cs.section_starts(cut_map_of(), [0.0, 24.5]) == [0.0]

    def test_section_at_finds_the_section_a_time_falls_in(self, plan):
        assert cs.section_at(plan.sections, 8.5).index == 1
        assert cs.section_at(plan.sections, 0.0).index == 0


# --- sections ----------------------------------------------------------------

class TestSections:
    def test_sections_start_at_zero_and_every_section_event(self, plan):
        assert [(s.start, s.end) for s in plan.sections] == [(0.0, 4.5), (4.5, 12.5), (12.5, 30.0)]

    def test_movements_follow_the_story_quota_over_the_sections(self, plan):
        assert [s.movement for s in plan.sections] == ["M1", "M2", "M3"]
        assert cs.movements_of(5) == {0: "M1", 1: "M2", 2: "M2", 3: "M3", 4: "M3"}

    def test_a_section_is_pulsed_when_its_onsets_are_dense(self, metre):
        events = [ev(2.5, 2, "phrase", density=1.0), ev(4.5, 3, "section", density=0.2),
                  ev(12.5, 3, "section", density=2.0)]
        sections = cs.sections_of(cut_map_of(events=events, spans=[]), [0.0, 4.5, 12.5, 24.5],
                                  cs.movements_of(3))
        assert [s.pulse for s in sections] == [True, False, True]

    def test_density_in_reads_the_events_inside_the_stretch(self):
        level, density = cs.density_in(cut_map_of(), 4.5, 12.5)
        assert density == 2.0 and level == -20.0
        assert cs.density_in(cut_map_of(events=[], spans=[]), 0.0, 5.0) == (0.0, 0.0)

    def test_every_span_belongs_to_the_section_it_starts_in(self, plan):
        assert [s.section for s in plan.spans] == [0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2]

    def test_the_plan_carries_the_title_hit(self, plan):
        assert plan.title_hit == 22.5 and plan.seconds == 30.0 and plan.bar == BAR


# --- fit ---------------------------------------------------------------------

class TestFit:
    def test_a_plan_inside_the_budget_is_returned_whole(self, plan):
        assert cs.plan_fit(plan, affordable=10) == plan

    def test_fit_drops_the_latest_accent_first(self, plan):
        fitted = cs.plan_fit(plan, affordable=9)
        assert "accent" not in [s.kind for s in fitted.spans]
        assert (8.5, 11.0, "phrase") in kinds(fitted)
        assert len(fitted.picture_spans()) == 9

    def test_fit_merges_phrases_inside_their_section(self, plan):
        fitted = cs.plan_fit(plan, affordable=8)
        assert (6.5, 11.0, "phrase") in kinds(fitted)
        assert [s.start for s in fitted.sections] == [0.0, 4.5, 12.5]

    def test_fit_never_touches_a_sustain(self, plan):
        fitted = cs.plan_fit(plan, affordable=6)
        assert (0.0, 4.5, "sustain") in kinds(fitted)
        assert (14.5, 20.5, "sustain") in kinds(fitted)
        assert (20.5, 22.5, "trough") in kinds(fitted)
        assert len(fitted.picture_spans()) == 6

    def test_fit_refuses_with_the_bars_it_needed(self, plan):
        with pytest.raises(ShorterCue) as caught:
            cs.plan_fit(plan, affordable=5)
        assert caught.value.bars_needed == 1

    def test_absorbing_an_accent_at_the_head_goes_forward(self, metre):
        events = [ev(0.5, 2, "phrase"), ev(6.5, 2, "phrase")]
        plan = cs.plan_of(cut_map_of(events=events, spans=[]), metre, "trailer/music/c.flac", 1)
        assert (0.0, 0.5, "accent") in kinds(plan)
        fitted = cs.plan_fit(plan, affordable=len(plan.picture_spans()) - 1)
        assert fitted.spans[0].start == 0.0 and fitted.spans[0].end == 6.5

    def test_two_absorbed_accents_read_as_a_phrase(self, metre):
        span = cs.stretched(cs.plan_of(cut_map_of(), metre, "trailer/music/c.flac", 1).spans[4],
                            10.5, 11.5, metre.bar)
        assert span.kind == "phrase" and span.bars == 0.5

    def test_removable_spares_fixed_kinds_and_a_section_door(self, plan):
        by_kind = {s.kind: i for i, s in enumerate(plan.spans)}
        assert cs.removable(plan.spans, by_kind["accent"])
        assert cs.removable(plan.spans, by_kind["phrase"])
        assert not any(cs.removable(plan.spans, by_kind[k]) for k in ("sustain", "trough", "tail"))
        assert not cs.removable(plan.spans, by_kind["section"])

    def test_next_removal_prefers_accent_then_phrase_pair_then_section_pair(self, plan):
        assert plan.spans[cs.next_removal(plan.spans)].kind == "accent"
        one = cs.absorbed(plan.spans, cs.latest_accent(plan.spans), plan.bar)
        assert cs.earliest_pair(one, ("phrase",)) == 3
        assert cs.earliest_pair(one, cs.MERGEABLE) == 2
        assert cs.next_removal(one) == 3

    def test_absorbed_renumbers_and_keeps_the_cue_contiguous(self, plan):
        out = cs.absorbed(plan.spans, 4, plan.bar)
        assert [s.index for s in out] == list(range(len(plan.spans) - 1))
        assert all(a.end == b.start for a, b in zip(out, out[1:]))
        assert (out[3].start, out[3].end) == (8.5, 11.0)

    def test_replaced_runs_the_plan_validators_again(self, plan):
        assert cs.replaced(plan, plan.spans) == plan
        with pytest.raises(ValueError):
            cs.replaced(plan, plan.spans[1:])

    def test_bars_needed_is_the_shortest_spans_over_the_budget(self, plan):
        """Three over: the accent (0.25 bar), the 1.5 s phrase (0.75) and a
        one-bar span, rounded up to whole bars for the next ask."""
        assert cs.bars_needed(plan.picture_spans(), affordable=8) == 1
        assert cs.bars_needed(plan.picture_spans(), affordable=7) == 2


class TestFitToBudget:
    """The frames say how many seconds of render there are; the fit rule turns
    that into how many spans, one removal at a time."""

    def cost(self, plan):
        return fb.TYPED.cost_seconds(fb.plan_frames(plan.picture_spans()), takes=len(plan.picture_spans()))

    def test_a_plan_the_frames_afford_is_returned_whole(self, plan):
        remaining = self.cost(plan) / (1.0 - fb.RETRY_RESERVE) + 1.0
        assert cs.fit_to_budget(plan, remaining, fb.TYPED) == plan

    def test_the_plan_is_trimmed_until_it_fits(self, plan):
        remaining = self.cost(plan) * 0.8 / (1.0 - fb.RETRY_RESERVE)
        fitted = cs.fit_to_budget(plan, remaining, fb.TYPED)
        assert len(fitted.picture_spans()) < len(plan.picture_spans())
        assert fb.fits(fitted, remaining, fb.TYPED) and fitted.sections == plan.sections

    def test_a_budget_the_fixed_spans_alone_exceed_asks_for_a_shorter_cue(self, plan):
        with pytest.raises(ShorterCue) as caught:
            cs.fit_to_budget(plan, 60.0, fb.TYPED)
        assert caught.value.bars_needed >= 1
