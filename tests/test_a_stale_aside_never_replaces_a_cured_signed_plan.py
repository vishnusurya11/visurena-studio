"""ep19 launch07 (2026-10-07 15:10Z): plan_repair had cured the SIGNED 21-shot
plan (G-PROPCARD, one recorded round), so its signature was stale by one
recorded link.  step 02 read the aside FIRST -- a plan.deferred.json left from
the day before, 12 shots -- and `cure_aside_first` restored it over the plan;
the chain was then broken and the climb ran again on the old draft, 35 min.
Two rules: a stale APPROVE with a recorded chain is re-signed BEFORE anything
reads the aside, and a signature retires the aside.  $0: no writer, no critic."""
from __future__ import annotations

import json

import pytest

from agents import episode_writer
from scripts.episode import step_02_plan as step
from studio import episode_home, plan_ladder, plan_provenance, plan_verdict
from studio.judges import plan as plan_judge


class Ctx:
    def __init__(self, tmp_path, rc=0):
        self.book_dir = tmp_path / "book"
        self.number = 3
        self.stage = "episode"
        self.extra = []
        self.rc = rc
        self.captured, self.logged = [], []

    @property
    def home(self):
        return episode_home.home(self.book_dir, self.number)

    def capture_script(self, *cmd):
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


def cured_home_with_an_old_aside(tmp_path):
    plan = episode_home.plan_path(tmp_path / "book", 3)
    plan.parent.mkdir(parents=True)
    plan.write_text(json.dumps({"shots": 21}), encoding="utf-8")
    plan_verdict.sign(plan, "signed", signed_by="judge:plan@1")
    before = plan_verdict.plan_sha8(plan)
    plan.write_text(json.dumps({"shots": 21, "cured": True}), encoding="utf-8")
    plan_provenance.record(plan, before, ["legal_props"])
    aside = plan.parent / plan_ladder.DEFERRED
    aside.write_text(json.dumps({"draft": {"shots": 12}, "note": "old"}), encoding="utf-8")
    return plan, aside


def test_the_cured_signed_plan_is_resigned_before_the_aside_is_read(tmp_path, no_paid_calls):
    plan, aside = cured_home_with_an_old_aside(tmp_path)
    ctx = Ctx(tmp_path, rc=0)
    step.run(ctx)
    assert json.loads(plan.read_text(encoding="utf-8")) == {"shots": 21, "cured": True}
    assert plan_verdict.current(plan) is True
    assert all("plan_repair" not in " ".join(map(str, c)) for c in ctx.captured)


def test_a_signature_retires_the_aside_and_a_deferral_keeps_it(tmp_path):
    plan, aside = cured_home_with_an_old_aside(tmp_path)
    ctx = Ctx(tmp_path)
    step.retire_aside(ctx, plan.parent / plan_ladder.DEFERRED)
    assert aside.exists()
    step.retire_aside(ctx, plan.parent / plan_verdict.FILE)
    assert not aside.exists()
