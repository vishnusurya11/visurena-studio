"""Settling the plan like an editor when takes are lost: the cue bends, the
story does not.  Every function is pure -- a CuePlan and the beat ids that
still have a take in, a CuePlan, the ids that survive and the seconds the
music must lose out."""
from __future__ import annotations

import pytest

from studio import cue_settle
from studio.cue_plan import CuePlan
from tests.test_cue_qc import BAR, build_plan, span

IDS = [f"B{i:02d}" for i in range(10)]
"""One beat per picture span of `build_plan`: sustain, phrase, phrase,
section, accent, sustain, phrase, trough, section, phrase."""


def kinds(plan: CuePlan) -> list[str]:
    return [s.kind for s in plan.spans]


def bounds(plan: CuePlan) -> list[tuple[float, float]]:
    return [(s.start, s.end) for s in plan.spans]


def lost(*indices: int) -> set[str]:
    return {b for i, b in enumerate(IDS) if i not in indices}


class TestOneLoss:
    def test_a_lost_accent_is_absorbed_by_the_shot_before_it(self):
        """An insert is a beat long at most; the shot before it plays on
        through it, well inside the take's slack.  The music is untouched."""
        out = cue_settle.settle(build_plan(), IDS, lost(4))
        assert out.removed == [] and out.ids == IDS[:4] + IDS[5:]
        assert bounds(out.plan)[3] == (8.0, 10.5) and kinds(out.plan)[3] == "section"
        assert len(out.plan.picture_spans()) == 9 and out.plan.seconds == 30.0

    def test_a_lost_sustain_is_cut_out_of_the_music(self):
        """No take can grow four bars; the sustain's seconds leave the cue
        and everything after moves up.  Section bounds move with the cue."""
        out = cue_settle.settle(build_plan(), IDS, lost(5))
        assert out.removed == [(10.5, 14.5)] and out.ids == IDS[:5] + IDS[6:]
        assert bounds(out.plan)[5:] == [(10.5, 12.0), (12.0, 16.0), (16.0, 18.0), (18.0, 20.0),
                                        (20.0, 26.0)]
        assert out.plan.seconds == 26.0 and out.plan.hard_out == 20.0 and out.plan.title_hit == 20.0
        assert [(c.start, c.end) for c in out.plan.sections] == [(0.0, 8.0), (8.0, 16.0), (16.0, 26.0)]

    def test_a_lost_phrase_is_cut_out_too(self):
        out = cue_settle.settle(build_plan(), IDS, lost(1))
        assert out.removed == [(4.0, 6.0)] and bounds(out.plan)[1] == (4.0, 6.0)
        assert kinds(out.plan)[:3] == ["sustain", "phrase", "section"]
        assert out.plan.sections[1].start == 6.0 and out.plan.spans[2].start == 6.0

    def test_a_lost_button_moves_the_hard_out(self):
        """The last picture span is the button before the card; without its
        take the card comes on the span's own start.  Nothing is cut."""
        out = cue_settle.settle(build_plan(), IDS, lost(9))
        assert out.removed == [] and out.ids == IDS[:9]
        assert out.plan.hard_out == 22.0 and bounds(out.plan)[-1] == (22.0, 30.0)
        assert kinds(out.plan)[-1] == "tail" and out.plan.seconds == 30.0

    def test_a_lost_section_door_is_cut_out_and_its_successor_opens_the_section(self):
        """The door's bars leave the music; the join lands on the section's
        next downbeat, and the span after the door now starts the section."""
        out = cue_settle.settle(build_plan(), IDS, lost(3))
        assert out.removed == [(8.0, 10.0)]
        assert bounds(out.plan)[3] == (8.0, 8.5) and kinds(out.plan)[3] == "accent"
        assert out.plan.sections[1].start == 8.0 and out.plan.sections[1].end == 18.0


class TestTheCueStaysAPlan:
    def test_a_lost_phrase_between_two_sustains_takes_the_later_sustain_with_it(self):
        """Two long shots against each other read as one long shot; the
        editor loses the second sustain rather than let them touch."""
        plan = CuePlan(rel_path="m/cue.flac", seed=1, seconds=18.0, bpm=120.0, bar=BAR,
                       sections=[dict(index=0, start=0.0, end=18.0, movement="M1", pulse=False,
                                      level_db=-24.0)],
                       spans=[span(0, 0.0, 4.0, "sustain", 0, "M1"), span(1, 4.0, 6.0, "phrase", 0, "M1"),
                              span(2, 6.0, 10.0, "sustain", 0, "M1"), span(3, 10.0, 12.0, "phrase", 0, "M1"),
                              span(4, 12.0, 18.0, "tail", 0, "M1")],
                       hard_out=12.0, title_hit=12.0)
        out = cue_settle.settle(plan, ["A", "B", "C", "D"], {"A", "C", "D"})
        assert out.removed == [(4.0, 6.0), (4.0, 8.0)] and out.ids == ["A", "D"]
        assert bounds(out.plan) == [(0.0, 4.0), (4.0, 6.0), (6.0, 12.0)] and out.plan.hard_out == 6.0

    def test_losses_are_settled_latest_first_so_earlier_seconds_stay_true(self):
        assert cue_settle.lost_indices(IDS, lost(1, 7)) == [7, 1]
        out = cue_settle.settle(build_plan(), IDS, lost(1, 7))
        assert out.removed == [(16.0, 20.0), (4.0, 6.0)]
        assert out.plan.seconds == 24.0 and out.plan.hard_out == 18.0

    def test_every_settle_pass_removes_at_least_one_span(self):
        plan = build_plan()
        for i in range(len(IDS)):
            out = cue_settle.settle(plan, IDS, lost(i))
            assert len(out.plan.picture_spans()) <= len(plan.picture_spans()) - 1
            assert len(out.ids) == len(out.plan.picture_spans())

    def test_nothing_lost_is_the_plan_unchanged(self):
        out = cue_settle.settle(build_plan(), IDS, set(IDS))
        assert out.plan == build_plan() and out.removed == [] and out.ids == IDS


class TestTheCutMapMovesWithTheCue:
    def test_events_inside_the_cut_are_gone_and_later_ones_move_up(self):
        doc = {"events": [{"t": 8.0, "rank": 3, "kind": "hit", "evidence": ["x"]},
                          {"t": 12.0, "rank": 2, "kind": "hit", "evidence": ["x"]},
                          {"t": 16.0, "rank": 2, "kind": "dropout", "evidence": ["x"], "end": 20.0}],
               "spans": [{"start": 8.0, "end": 16.0, "kind": "swell"},
                         {"start": 11.0, "end": 13.0, "kind": "hold"},
                         {"start": 16.0, "end": 20.0, "kind": "dropout"}],
               "hard_out": 24.0, "title_hit": 24.0, "seconds": 30.0}
        out = cue_settle.shifted_cut_map(doc, 10.5, 14.5)
        assert [e["t"] for e in out["events"]] == [8.0, 12.0] and out["events"][1]["end"] == 16.0
        assert [(s["start"], s["end"]) for s in out["spans"]] == [(8.0, 12.0), (12.0, 16.0)]
        assert out["hard_out"] == 20.0 and out["title_hit"] == 20.0 and out["seconds"] == 26.0

    def test_moved_clamps_a_time_inside_the_cut_to_the_join(self):
        assert cue_settle.moved(9.0, 10.5, 14.5) == 9.0
        assert cue_settle.moved(12.0, 10.5, 14.5) == 10.5
        assert cue_settle.moved(16.0, 10.5, 14.5) == 12.0
