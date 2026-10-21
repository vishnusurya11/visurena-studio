"""A sweep past its 4 h budget runs in shards (2026-10-21_ep02_proof DESIGN 3.3): the harness
plans a shard at the MEASURED cost of one point (the unfaulted baseline run), stops a shard when
the clock says the next point would overrun, keeps every tried point in results/<id>.json so the
next night resumes where this one stopped, and reports the untried count, never extrapolated.
A scenario with untried points is never a pass; a blocked scenario is skipped only when the real
scheduler refused it or its inputs are absent, never for any other reason."""
from __future__ import annotations

import json
from itertools import count

from scripts.proof import rehearse
from studio.rehearsal import sweep


def points(n: int) -> list[sweep.Point]:
    return [sweep.Point("F10", {"workflow": "ref2v_take", "k": k}) for k in range(1, n + 1)]


def test_a_shard_is_planned_at_the_measured_cost_of_one_point():
    todo = rehearse.shard_of(points(10), done=set(), cost_s=3600.0, budget_s=4 * 3600.0)
    assert [p.where["k"] for p in todo] == [1, 2, 3, 4]
    assert rehearse.shard_of(points(3), done=set(), cost_s=None, budget_s=10.0) == points(3)


def test_the_next_shard_skips_the_points_an_earlier_shard_tried():
    done = {p.id for p in points(4)}
    todo = rehearse.shard_of(points(10), done=done, cost_s=3600.0, budget_s=4 * 3600.0)
    assert [p.where["k"] for p in todo] == [5, 6, 7, 8]


def test_a_shard_stops_when_the_next_point_would_overrun_its_budget():
    ticks = count(0, 100)                                       # each clock read is 100 s later
    ran = rehearse.run_budgeted(points(10), lambda p: {"id": p.id}, budget_s=450.0, clock=lambda: next(ticks))
    assert 1 <= len(ran) < 10
    assert len(rehearse.run_budgeted(points(2), lambda p: {"id": p.id}, budget_s=1.0, clock=lambda: next(ticks))) == 1


def test_untried_points_are_counted_and_the_scenario_is_never_a_pass():
    sc = rehearse.TABLE["F10"]
    tried = [{"id": p.id, "passed": True, "trace": "t1", "rows": []} for p in points(4)]
    r = rehearse.summary_row(sc, tried, planned=10)
    assert r["passed"] is False and r["instrument_state"] == "untried 6" and "6 untried" in r["detail"]
    assert rehearse.summary_row(sc, tried, planned=4)["passed"] is True


def test_a_prior_shard_on_the_same_sandbox_is_resumed_and_another_sandboxs_is_not(tmp_path):
    doc = {"box": str(tmp_path / "box"), "points": [{"id": "F10:k=1", "passed": True, "trace": "t"}],
           "rows": [{"check": "A-caps", "instrument": "files"}, {"check": "F10", "instrument": "trace"},
                    {"check": "A-real", "instrument": "guard"}]}
    (tmp_path / "F10.json").write_text(json.dumps(doc))
    got, rows = rehearse.prior_shard(tmp_path, "F10", tmp_path / "box")
    assert [p["id"] for p in got] == ["F10:k=1"] and [r["check"] for r in rows] == ["A-caps"]
    assert rehearse.prior_shard(tmp_path, "F10", tmp_path / "other") == ([], [])
    assert rehearse.prior_shard(tmp_path, "F99", tmp_path / "box") == ([], [])


def test_only_a_scheduler_refusal_or_an_absent_input_is_skippable():
    assert rehearse.skippable({"blocked": ["refused: the real Task Scheduler entry is enabled"]})
    assert rehearse.skippable({"blocked": ["absent: studio.rehearsal.fake_comfy"]})
    assert not rehearse.skippable({"blocked": ["checkpoint after_08 absent: run checkpoints first"]})
    assert not rehearse.skippable({"scenario": "F1", "path": "x"})
