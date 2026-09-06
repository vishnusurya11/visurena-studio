"""Conforming a verified cue to the frames the budget affords: one render, a
shorter length cut from it.  The fit rule folds what it can; past that the
smallest interior span leaves the music (row 53's cut), never the opening
image, never the button, and only when nothing is left does step 03 ask the
model for a shorter cue."""
from __future__ import annotations

import json

import numpy as np
import pytest

from studio import cue_conform, frame_budget
from studio.cue_settle import Settled
from studio.cue_spans import ShorterCue
from tests.test_cue_qc import build_plan

CYCLE = frame_budget.TYPED


def cost(plan) -> float:
    picture = plan.picture_spans()
    return CYCLE.cost_seconds(frame_budget.plan_frames(picture), takes=len(picture))


def budget_for(plan) -> float:
    """Seconds that afford exactly this plan and nothing longer."""
    return cost(plan) / (1.0 - frame_budget.RETRY_RESERVE) + 0.01


def folded_out() -> Settled:
    """The canonical plan with every fold the fit rule has taken."""
    out = Settled(plan=build_plan(), ids=cue_conform.indices(build_plan()), removed=[])
    while (one := cue_conform.folded(out)) is not None:
        out = one
    return out


class TestTheRule:
    def test_the_fit_rule_folds_before_anything_is_cut(self):
        plan = build_plan()
        out = cue_conform.conform_to_budget(plan, budget_for(plan) - 1.0, CYCLE)
        assert out.removed == [] and len(out.ids) == 9
        assert [s.kind for s in out.plan.spans][3:5] == ["section", "sustain"]

    def test_past_the_folds_the_smallest_interior_span_leaves_the_music(self):
        start = folded_out()
        assert cue_conform.folded(start) is None
        assert [s.kind for s in start.plan.spans] == ["sustain", "phrase", "section", "sustain",
                                                       "phrase", "trough", "section", "tail"]
        out = cue_conform.conform_to_budget(build_plan(), budget_for(start.plan) - 1.0, CYCLE)
        assert out.removed == [(14.5, 16.0)]
        assert out.plan.seconds == 28.5 and out.plan.hard_out == 22.5
        assert [s.kind for s in out.plan.spans] == ["sustain", "phrase", "section", "sustain",
                                                    "trough", "section", "tail"]
        assert len(out.ids) == 6 and "4" not in out.ids

    def test_the_opening_image_and_the_button_are_never_cut(self):
        picture = folded_out().plan.picture_spans()
        chosen = cue_conform.smallest_interior(folded_out().plan)
        assert 0 < chosen < len(picture) - 1
        two = build_plan().model_copy(update={"spans": build_plan().spans[:1] + build_plan().spans[-2:]})
        assert cue_conform.smallest_interior(two) is None

    def test_among_equal_spans_the_latest_leaves_first(self):
        out = folded_out()
        cut = cue_conform.cut(out)
        again = cue_conform.cut(cut)
        assert again.removed == [(14.5, 16.0), (8.0, 10.5)]

    def test_a_plan_that_fits_is_untouched(self):
        plan = build_plan()
        out = cue_conform.conform_to_budget(plan, budget_for(plan), CYCLE)
        assert out.plan == plan and out.removed == [] and out.ids == cue_conform.indices(plan)

    def test_when_nothing_interior_is_left_the_model_is_asked_for_a_shorter_cue(self):
        with pytest.raises(ShorterCue):
            cue_conform.conform_to_budget(build_plan(), 10.0, CYCLE)


class TestTheCueIsCut:
    CUE = "trailer/main/music/cue-7.flac"
    CUT_MAP = {"events": [{"t": 8.0, "rank": 3, "kind": "hit", "evidence": ["x"]},
                          {"t": 20.0, "rank": 2, "kind": "hit", "evidence": ["x"]}],
               "spans": [{"start": 16.0, "end": 20.0, "kind": "dropout"}],
               "hard_out": 24.0, "title_hit": 24.0, "seconds": 30.0}

    def stage(self, tmp_path, monkeypatch):
        from tests.test_cue_edit import RATE, click
        music = tmp_path / "trailer/main/music"
        music.mkdir(parents=True)
        samples, metre = click(30.0)
        (music / "metre.json").write_text(
            metre.model_copy(update={"rel_path": self.CUE}).model_dump_json(), encoding="utf-8")
        (music / "cutmap-7.json").write_text(json.dumps(self.CUT_MAP), encoding="utf-8")
        seen = {}
        monkeypatch.setattr(cue_conform, "read_cue", lambda path: (samples, RATE))
        monkeypatch.setattr(cue_conform, "write_cue",
                            lambda path, out, rate: seen.update(path=path, samples=len(out), rate=rate))
        return music, seen

    def test_the_settled_cue_its_metre_and_its_cut_map_are_written_beside_the_original(self, tmp_path, monkeypatch):
        from tests.test_cue_edit import RATE
        music, seen = self.stage(tmp_path, monkeypatch)
        cue = build_plan().model_copy(update={"rel_path": self.CUE})
        rel = cue_conform.cut_files(music, tmp_path, cue, [(14.5, 16.0)])
        assert rel == "trailer/main/music/cue-7-settled.flac"
        assert seen["path"] == tmp_path / rel and seen["samples"] == int(28.5 * RATE)
        metre = json.loads((music / "metre.json").read_text(encoding="utf-8"))
        assert metre["rel_path"] == rel and metre["seconds"] == 28.5
        cut_map = json.loads((music / "cutmap-7-settled.json").read_text(encoding="utf-8"))
        assert cut_map["seconds"] == 28.5 and [e["t"] for e in cut_map["events"]] == [8.0, 18.5]

    def test_the_names_derive_from_the_cue_that_plays(self):
        assert cue_conform.cut_map_name("trailer/main/music/cue-1003.flac") == "cutmap-1003.json"
        assert cue_conform.cut_map_name("m/cue-1003-settled.flac") == "cutmap-1003-settled.json"
        cue = build_plan().model_copy(update={"rel_path": "m/cue-1003-settled.flac"})
        assert cue_conform.settled_rel(cue) == "m/cue-1003-settled.flac"
        wav = build_plan().model_copy(update={"rel_path": "m/cue-1003.wav"})
        assert cue_conform.settled_rel(wav) == "m/cue-1003-settled.wav"

    def test_a_join_the_cue_refuses_is_the_callers_to_settle(self, tmp_path, monkeypatch):
        from studio import cue_edit
        music, _ = self.stage(tmp_path, monkeypatch)

        def refuse(*args, **kwargs):
            raise ValueError("levels differ")

        monkeypatch.setattr(cue_edit, "remove_range", refuse)
        cue = build_plan().model_copy(update={"rel_path": self.CUE})
        with pytest.raises(ValueError):
            cue_conform.cut_files(music, tmp_path, cue, [(14.5, 16.0)])
        assert not (music / "cutmap-7-settled.json").exists()
