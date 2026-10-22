"""S0a and F5 answer the episode writer from ep01's delivered plan (2026-10-21_ep02_proof DESIGN 3.2).

The first real window (2026-10-21 17:40 PDT) ran S0a with NO writer source: the scenario table named
none and run_point never wrote F5's `writer_plan` into the manifest, so every PartFrame/PartShots/
PartLines ask was canned, the contract refused the empty draft ("an episode with no line has no
button"), step 02 deferred, and no checkpoint past step 02 could ever be cut.  The plan is the
fixture copy of ep01's plan (same content as the library's), renumbered to the scenario's episode
(F5 is "ep02 with ep01's plan renumbered"), written into the sandbox, named by the manifest."""
from __future__ import annotations

import json

from scripts.proof import rehearse


def test_s0a_and_f5_name_ep01s_plan_as_their_writer():
    assert rehearse.TABLE["S0a"].fault.get("writer_plan") == "ep01"
    assert rehearse.TABLE["F5"].fault.get("writer_plan") == "ep01"


def test_the_writer_plan_is_ep01s_plan_renumbered_to_the_scenario_episode(tmp_path):
    path = rehearse.writer_plan(tmp_path, rehearse.TABLE["F5"])
    doc = json.loads(path.read_text(encoding="utf-8"))
    ep01 = json.loads(rehearse.EP01_PLAN.read_text(encoding="utf-8"))
    assert path.parent == tmp_path and doc["number"] == 2
    assert {k: v for k, v in doc.items() if k != "number"} == {k: v for k, v in ep01.items() if k != "number"}


def test_a_scenario_with_no_writer_plan_gets_none(tmp_path):
    assert rehearse.writer_plan(tmp_path, rehearse.TABLE["F1"]) is None
    assert not list(tmp_path.iterdir())


def test_a_points_manifest_carries_the_writer_plan_path(tmp_path):
    fields = rehearse.point_manifest(tmp_path, rehearse.TABLE["S0a"])
    assert fields["writer_plan"] == str(tmp_path / rehearse.WRITER_PLAN)
    assert fields["checkpoints"] is True and fields["bound"] is None
    assert json.loads((tmp_path / rehearse.WRITER_PLAN).read_text(encoding="utf-8"))["number"] == 1


def test_a_points_manifest_clears_an_earlier_writer_plan(tmp_path):
    fields = rehearse.point_manifest(tmp_path, rehearse.TABLE["F1"])
    assert fields["writer_plan"] is None and fields["checkpoints"] is False and fields["bound"] == "09"
