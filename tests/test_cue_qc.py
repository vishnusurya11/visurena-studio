"""The cut graded against its cue: every measure is a pure function of the
detected cuts, the shipped CuePlan and the mix's line windows."""
from __future__ import annotations

import pytest

from studio import cue_qc
from studio.cue_plan import CuePlan

BAR = 2.0


def span(index, start, end, kind, section, movement):
    return dict(index=index, start=start, end=end, kind=kind, section=section,
                movement=movement, bars=round((end - start) / BAR, 3))


def build_plan() -> CuePlan:
    sections = [dict(index=0, start=0.0, end=8.0, movement="M1", pulse=False, level_db=-24.0),
                dict(index=1, start=8.0, end=20.0, movement="M2", pulse=True, level_db=-18.0),
                dict(index=2, start=20.0, end=30.0, movement="M3", pulse=True, level_db=-14.0)]
    spans = [span(0, 0.0, 4.0, "sustain", 0, "M1"), span(1, 4.0, 6.0, "phrase", 0, "M1"),
             span(2, 6.0, 8.0, "phrase", 0, "M1"), span(3, 8.0, 10.0, "section", 1, "M2"),
             span(4, 10.0, 10.5, "accent", 1, "M2"), span(5, 10.5, 14.5, "sustain", 1, "M2"),
             span(6, 14.5, 16.0, "phrase", 1, "M2"), span(7, 16.0, 20.0, "trough", 1, "M2"),
             span(8, 20.0, 22.0, "section", 2, "M3"), span(9, 22.0, 24.0, "phrase", 2, "M3"),
             span(10, 24.0, 30.0, "tail", 2, "M3")]
    return CuePlan(rel_path="m/cue.flac", seed=1, seconds=30.0, bpm=120.0, bar=BAR,
                   sections=sections, spans=spans, hard_out=24.0, title_hit=24.0)


@pytest.fixture(scope="module")
def plan() -> CuePlan:
    return build_plan()


PLANNED = [4.0, 6.0, 8.0, 10.0, 10.5, 14.5, 16.0, 20.0, 22.0]


class TestEvents:
    def test_the_plans_events_are_its_span_starts_after_the_first(self, plan):
        assert cue_qc.events_of(plan) == PLANNED + [24.0]  # the hard out is the card's cut

    def test_a_cut_map_supplies_its_own_events_of_rank_two_or_more(self, plan):
        cut_map = {"events": [{"t": 3.0, "rank": 1}, {"t": 4.0, "rank": 2}, {"t": 8.0, "rank": 3}]}
        assert cue_qc.events_of(plan, cut_map) == [4.0, 8.0]

    def test_cuts_on_events_is_the_share_within_a_tenth_of_a_second(self, plan):
        cuts = [4.0, 6.05, 8.0, 10.0, 10.5, 14.5, 16.0, 20.0, 22.0, 13.0]
        assert cue_qc.cuts_on_events(cuts, PLANNED) == 0.9

    def test_no_cuts_is_no_share(self):
        assert cue_qc.cuts_on_events([], PLANNED) == 0.0


class TestFloors:
    def test_a_section_change_the_picture_missed_fails_the_floor(self, plan):
        assert cue_qc.section_changes_cut([8.0, 13.0], plan) == 0.5
        assert cue_qc.section_changes_cut([8.0, 20.02], plan) == 1.0

    def test_a_cut_inside_a_sustain_fails_the_floor(self, plan):
        """A cut on a hold's boundary is the hold's own; one inside it, or
        inside a stopdown, is the mistake the viewer hears."""
        assert cue_qc.cuts_inside_holds([12.0, 2.0, 10.5, 4.0], plan) == 2
        assert cue_qc.cuts_inside_holds([18.0], plan) == 1

    def test_a_long_shot_off_a_hold_fails_the_floor(self, plan):
        cuts = [4.0, 8.0, 10.0, 10.5, 14.5, 16.0, 20.0, 22.0]
        assert cue_qc.long_shots_on_holds(cuts, plan) == 0.75  # 4.0-8.0 is a long phrase

    def test_a_cut_with_no_long_shot_holds_the_floor(self, plan):
        assert cue_qc.long_shots_on_holds(PLANNED, plan) == 1.0

    def test_a_line_outside_every_window_fails_the_floor(self, plan):
        assert cue_qc.lines_in_troughs([(16.5, 19.0), (8.5, 9.5)], plan) == 0.5
        assert cue_qc.lines_in_troughs([(0.5, 3.4), (11.0, 13.9), (5.0, 7.0)], plan) == 1.0
        assert cue_qc.lines_in_troughs([], plan) == 1.0


class TestShape:
    def test_an_accent_is_cut_when_both_its_edges_are(self, plan):
        assert cue_qc.accents_cut([10.0, 10.5], plan) == 1.0
        assert cue_qc.accents_cut([10.0], plan) == 0.0

    def test_movement_medians_are_the_measured_shot_lengths_per_movement(self, plan):
        assert cue_qc.movement_medians(PLANNED, plan) == [2.0, 2.0, 2.0]

    def test_shots_are_read_between_the_cuts_and_the_hard_out(self, plan):
        assert cue_qc.shots_of([4.0, 8.0], plan) == [(0.0, 4.0), (4.0, 8.0), (8.0, 24.0)]

    def test_frames_rendered_are_summed_off_the_takes(self):
        clips = {"takes": [{"frames": 121}, {"frames": 243}, {"seconds": 3.0}]}
        assert cue_qc.frames_rendered(clips) == 364

    def test_frames_played_are_the_pictures_frames(self, plan):
        assert cue_qc.frames_played(plan) == round(24.0 * cue_qc.FPS)


def test_the_cue_cut_is_measured_whole(plan):
    cut = cue_qc.measure(PLANNED, plan, lines=[(16.5, 19.0)], clips={"takes": [{"frames": 100}]})
    assert cut.cuts_on_events == 1.0 and cut.section_changes_cut == 1.0
    assert cut.cuts_inside_sustain == 0 and cut.long_shots_on_sustains == 1.0
    assert cut.lines_in_troughs == 1.0 and cut.accents_cut == 1.0
    assert cut.frames_rendered == 100 and cut.frames_played == round(24.0 * cue_qc.FPS)
    assert cut.floor_misses() == []
