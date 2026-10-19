"""When the episode ends and when each step ends (page experts 2026-10-18, A1+A2; the owner's
#1 pain).  'done around 15:20' was the episode's finish printed under the running step, with
step medians that mixed resumes (a step finding its outputs, seconds) with full runs (09 shoot:
10 min median against 80 min full-run), and no step had a projected window.  Now:

- a step's norm is its full-run pairs (>= 0.25 x p90 of its history), rule D;
- which steps run again comes from the registry's in:/out: graph, rule W;
- every step that will run gets a start->end, the episode a separate finish, rule B;
- past the running step's p90 the finish is a floor, never blank."""
from __future__ import annotations

import time

import pytest

from studio import eta, registry
from studio.command_center import models, progress_view

ORDER = [s["id"] for s in registry.steps("episode")]


def test_resume_pairs_do_not_set_a_full_runs_norm():
    mins = [80, 1.3, 2, 85, 100, 1.5, 90]
    xs = eta.full_runs([m * 60 for m in mins])
    assert sorted(xs) == [m * 60 for m in (80, 85, 90, 100)]


def test_a_short_or_flat_history_is_kept_whole():
    assert eta.full_runs([]) == [] and eta.full_runs([5.0]) == [5.0]
    assert eta.full_runs([60.0, 61.0, 59.0]) == [60.0, 61.0, 59.0]


def test_globs_meet_either_way():
    assert eta.globs_meet("episodes/ep01/plan.json", "episodes/ep01/*.json")
    assert eta.globs_meet("episodes/ep01/*.json", "episodes/ep01/plan.json")
    assert not eta.globs_meet("refs/refs.json", "episodes/ep01/plan.json")


def test_a_replan_invalidates_every_step_that_reads_the_plan():
    ins = {s: registry.inputs_of("episode", s, "ep01") for s in ORDER}
    outs = {s: registry.outputs_of("episode", s, "ep01") for s in ORDER}
    will = eta.will_run(ORDER, "02", kept=set(ORDER), ins=ins, outs=outs)
    assert list(will) == ORDER[2:] and all(will.values()), will


def test_a_step_reading_nothing_rewritten_stays_kept():
    will = eta.will_run(["01", "02", "03"], "02", kept={"03"},
                        ins={"03": ["refs/x.png"]}, outs={"02": ["episodes/ep01/plan.json"]})
    assert will == {"03": False}


def test_a_step_never_done_runs():
    assert eta.will_run(["01", "02", "03"], "02", kept=set(), ins={}, outs={}) == {"03": True}


def test_each_step_gets_a_window_and_the_episode_its_own_finish():
    p = eta.project(1000.0, 100.0, 0.0, [("03", True, [60.0, 60.0]), ("04", False, [500.0]),
                                         ("05", True, [30.0, 30.0])], ceiling_at=1e9)
    s = {x["id"]: x for x in p["steps"]}
    assert (s["03"]["start_at"], s["03"]["end_at"]) == (1100.0, 1160.0)
    assert s["04"]["will_run"] is False and s["04"]["end_at"] is None
    assert (s["05"]["start_at"], s["05"]["end_at"]) == (1160.0, 1190.0)
    assert p["finish_at"] == 1190.0 and p["step_end_at"] == 1100.0 and p["steps_left"] == 2


def test_past_p90_the_finish_is_a_floor_not_blank():
    p = eta.project(1000.0, None, 0.0, [("03", True, [60.0, 60.0])], ceiling_at=1e9)
    assert p["finish_at"] == 1060.0 and p["long"] is True and p["step_end_at"] is None


def test_the_ceiling_caps_the_finish():
    p = eta.project(1000.0, 100.0, 0.0, [("03", True, [9000.0, 9000.0])], ceiling_at=5000.0)
    assert p["finish_at"] == 5000.0 and p["capped"] is True


def test_the_rail_carries_each_steps_window():
    plan = {"steps": [{"id": "03", "will_run": True, "start_at": 1e9, "end_at": 1e9 + 900},
                      {"id": "04", "will_run": False, "start_at": None, "end_at": None}]}
    steps = [{"id": "02", "state": "running"}, {"id": "03", "state": "waiting"}, {"id": "04", "state": "waiting"}]
    out = {s["id"]: s for s in progress_view.with_windows(steps, plan)}
    # 32e9899 (owner 2026-10-18): a later step reads its duration `~15m`; the clock range is the tooltip
    assert out["03"]["will_run"] is True and out["03"]["window"].startswith("~") and "–" in out["03"]["when"]
    assert out["04"]["will_run"] is False and out["04"]["window"] == "kept"
    assert out["02"].get("window", "") == ""


def test_the_contract_carries_the_windows_and_the_step_end():
    assert {"will_run", "window"} <= set(models.RailStep.model_fields)
    assert {"step_end", "steps_left"} <= set(models.Eta.model_fields)


def test_the_valuetext_names_the_episode_finish():
    p = {"now_step": {"id": "02", "name": "plan", "kind": "loop"}, "eta": {"finish": "16:40"}}
    assert progress_view.valuetext(p) == "02 plan, episode done around 16:40"
