"""A stale APPROVE whose bytes moved ONLY through recorded mechanical cures,
over a battery that passes now, is re-signed with ZERO writer/critic calls
(ep18: a plan_repair round lapsed the signature and step 02 relaunched the
paid climb on an already-clean plan -- 48 calls, $1.05)."""
from __future__ import annotations

import json

import pytest

from agents import episode_writer
from scripts.episode import step_02_plan as step
from studio import episode_home, plan_provenance, plan_verdict
from studio.judges import plan as plan_judge


class Ctx:
    def __init__(self, tmp_path, rc=0):
        self.book_dir = tmp_path / "book"
        self.number = 3
        self.rc = rc
        self.captured, self.logged = [], []

    def capture_script(self, cmd):
        self.captured.append(cmd)
        return self.rc, ""

    def log(self, msg, **kw):
        self.logged.append(msg)


@pytest.fixture()
def no_paid_calls(monkeypatch):
    def boom(*a, **kw):
        raise AssertionError("a paid call was made on a mechanically-cured plan")
    monkeypatch.setattr(episode_writer, "write", boom)
    monkeypatch.setattr(plan_judge, "judge", boom)


def cured_home(tmp_path):
    """plan.json signed, then moved by one recorded cure round."""
    plan = episode_home.plan_path(tmp_path / "book", 3)
    plan.parent.mkdir(parents=True)
    plan.write_text(json.dumps({"v": 1}), encoding="utf-8")
    plan_verdict.sign(plan, "signed clean", signed_by="judge:plan@1",
                      faults=[{"kind": "pace", "where": "shot 3", "note": "kept"}], flagged=True)
    before = plan_verdict.plan_sha8(plan)
    plan.write_text(json.dumps({"v": 2}), encoding="utf-8")
    plan_provenance.record(plan, before, ["holds", "clamp_beds"])
    return plan


def test_a_recorded_chain_and_a_clean_battery_resign_with_no_call(tmp_path, no_paid_calls):
    plan = cured_home(tmp_path)
    ctx = Ctx(tmp_path, rc=0)
    assert step.resigned(ctx) is True
    assert plan_verdict.current(plan) is True
    doc = plan_verdict.read(plan)
    assert doc["signed_by"] == "judge:plan@1" and doc["flagged"] is True
    assert doc["faults"] and doc["faults"][0]["kind"] == "pace"
    assert "holds" in doc["note"] and "clamp_beds" in doc["note"]
    assert ctx.captured == [step.PLAN_CHECK]


def test_a_dirty_battery_is_never_resigned(tmp_path, no_paid_calls):
    plan = cured_home(tmp_path)
    ctx = Ctx(tmp_path, rc=1)
    assert step.resigned(ctx) is False
    assert plan_verdict.current(plan) is False


def test_a_current_signature_needs_no_resign(tmp_path, no_paid_calls):
    plan = episode_home.plan_path(tmp_path / "book", 3)
    plan.parent.mkdir(parents=True)
    plan.write_text(json.dumps({"v": 1}), encoding="utf-8")
    plan_verdict.sign(plan, "signed clean")
    ctx = Ctx(tmp_path)
    assert step.resigned(ctx) is False
    assert ctx.captured == []                       # not even the free battery runs


def test_no_plan_on_disk_is_no_resign(tmp_path, no_paid_calls):
    assert step.resigned(Ctx(tmp_path)) is False
