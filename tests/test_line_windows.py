"""Where a spoken line may sit.  With a cue plan the windows are the plan's
troughs and sustains, one beat short of the span; without one, the metre's
own troughs and ducked phrases stand, as they did before step 03 wrote a plan.
"""
from __future__ import annotations

import json

from studio import line_windows as lw
from studio.cue_plan import CuePlan
from studio.trailer_dialogue import windows_of
from studio.trailer_stage_spec import Metre, Slot

BAR = 2.0


def metre(grid="metre"):
    beats = [round(i * 0.5, 2) for i in range(160)]
    return Metre(seed=1, rel_path="music/seed_1.wav", seconds=80.0, bpm=120.0, bar=BAR,
                 beats=beats, downbeats=beats[::4], bars_in_mode=0.9 if grid == "metre" else 0.4,
                 grid=grid, fitness=0.8, slots=[Slot(start=10.0, end=16.0)])


def span(index, start, end, kind, section=0, movement="M1"):
    return {"index": index, "start": start, "end": end, "kind": kind, "section": section,
            "movement": movement, "bars": round((end - start) / BAR, 3)}


def plan_doc() -> dict:
    spans = [span(0, 0.0, 8.0, "sustain"), span(1, 8.0, 12.0, "phrase"),
             span(2, 12.0, 12.5, "accent"), span(3, 12.5, 20.0, "trough"),
             span(4, 20.0, 26.0, "phrase", 1, "M2"), span(5, 26.0, 34.0, "sustain", 1, "M2"),
             span(6, 34.0, 40.0, "phrase", 1, "M2"), span(7, 40.0, 48.0, "trough", 1, "M2"),
             span(8, 48.0, 52.0, "phrase", 2, "M3"), span(9, 52.0, 52.5, "accent", 2, "M3"),
             span(10, 52.5, 60.0, "phrase", 2, "M3"), span(11, 60.0, 66.0, "trough", 2, "M3"),
             span(12, 66.0, 72.0, "phrase", 2, "M3"), span(13, 72.0, 80.0, "tail", 2, "M3")]
    sections = [{"index": 0, "start": 0.0, "end": 20.0, "movement": "M1", "pulse": False,
                 "level_db": -20.0},
                {"index": 1, "start": 20.0, "end": 48.0, "movement": "M2", "pulse": True,
                 "level_db": -14.0},
                {"index": 2, "start": 48.0, "end": 72.0, "movement": "M3", "pulse": True,
                 "level_db": -8.0}]
    return {"rel_path": "music/seed_1.wav", "seed": 1, "seconds": 80.0, "bpm": 120.0,
            "bar": BAR, "sections": sections, "spans": spans, "hard_out": 72.0,
            "title_hit": 76.0}


def plan() -> CuePlan:
    return CuePlan.model_validate(plan_doc())


class TestLoadPlan:
    def test_the_plan_is_read_from_music_plan_json(self, tmp_path):
        (tmp_path / "music").mkdir()
        (tmp_path / "music/plan.json").write_text(json.dumps(plan_doc()), encoding="utf-8")
        found = lw.load_plan(tmp_path)
        assert isinstance(found, CuePlan) and found.seed == 1

    def test_an_older_production_has_no_plan(self, tmp_path):
        assert lw.load_plan(tmp_path) is None


class TestWindows:
    def test_a_plan_gives_its_troughs_and_sustains_a_beat_short(self):
        found = lw.windows_for(metre(), plan())
        assert found == plan().line_windows()
        assert [(s.start, s.end, s.made) for s in found] == [
            (0.0, 7.5, True), (12.5, 19.5, False), (26.0, 33.5, True),
            (40.0, 47.5, False), (60.0, 65.5, False)]

    def test_without_a_plan_the_metre_windows_stand(self):
        assert lw.windows_for(metre(), None) == windows_of(metre())


class TestBeat:
    def test_the_plans_beat_is_a_quarter_bar(self):
        assert lw.beat_for(metre("onsets"), plan()) == 0.5

    def test_a_metric_grid_keeps_its_own_beat(self):
        assert lw.beat_for(metre(), None) == metre().beat

    def test_a_rubato_cue_without_a_plan_has_no_beat(self):
        assert lw.beat_for(metre("onsets"), None) is None
