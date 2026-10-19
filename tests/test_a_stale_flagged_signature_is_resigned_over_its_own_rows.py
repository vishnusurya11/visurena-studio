"""A stale FLAGGED signature is re-signed over the rows it already carries (Jekyll ep01 Kawajiri,
2026-10-18, 15:38): one recorded cure moved the bytes, plan_check still printed the one creative row the
signature carried (G-TWO shot 26), `resigned()` wanted rc == 0, and climb 2 ran three rungs for 10.7 min.
Now: 0 writer calls, one critic read, the flag carried.  A NEW row, a bigger count or a tier-1 row climbs.
"""
from __future__ import annotations

import json

import pytest

from agents import episode_writer
from scripts.episode import step_02_plan as step
from studio import episode_home, plan_provenance, plan_verdict, step_attempts
from studio.judges import plan as plan_judge
from studio.judges.verdict import Fault, Verdict

G_TWO = "    G-TWO shot 26: a two-person reaction is a locked medium two-shot, measured medium/pan_to against medium/locked"
SIGNED = ["GRAMMAR      : 1", G_TWO, "VERDICT      : REFUSED -> keep_best"]


def printout(*rows: str, header: str = "GRAMMAR      : ") -> str:
    return "\n".join([f"{header}{len(rows)}", *rows, "VERDICT      : REFUSED"]) + "\n"


class Ctx:
    def __init__(self, tmp_path, rc=1, out=""):
        self.book_dir = tmp_path / "book"
        self.home, self.number, self.rc, self.out = self.book_dir, 3, rc, out
        self.logged = []

    def capture_script(self, cmd):
        return self.rc, self.out

    def log(self, msg, **kw):
        self.logged.append(msg)


@pytest.fixture()
def calls(monkeypatch):
    seen = {"writer": 0, "critic": 0}

    def boom(*a, **kw):
        seen["writer"] += 1
        raise AssertionError("a writer call was made on a carried plan")

    def read(ctx, desk):
        seen["critic"] += 1
        return Verdict(judge=plan_judge.JUDGE, version=plan_judge.VERSION, passed=True, faults=[],
                       confidence=1.0, reads=3)

    monkeypatch.setattr(episode_writer, "write", boom)
    monkeypatch.setattr(step, "critic", read)
    return seen


def cured_home(tmp_path, signed_lines=SIGNED, flagged=True):
    plan = episode_home.plan_path(tmp_path / "book", 3)
    plan.parent.mkdir(parents=True)
    plan.write_text(json.dumps({"v": 1}), encoding="utf-8")
    plan_verdict.sign(plan, "kept", signed_by="judge:plan@1", flagged=flagged,
                      faults=[{"kind": "battery", "where": "plan", "note": n} for n in signed_lines])
    before = plan_verdict.plan_sha8(plan)
    plan.write_text(json.dumps({"v": 2}), encoding="utf-8")
    plan_provenance.record(plan, before, ["holds"])
    return plan


def test_the_1538_case_g_two_carried_gives_no_writer_call_and_one_critic_read(tmp_path, calls):
    plan = cured_home(tmp_path)
    ctx = Ctx(tmp_path, out=printout(G_TWO))
    assert step.resigned(ctx) is True
    assert calls == {"writer": 0, "critic": 1}
    doc = plan_verdict.read(plan)
    assert plan_verdict.current(plan) and doc["flagged"] is True and doc["signed_by"] == "judge:plan@1"
    assert any("G-TWO shot 26" in (f.get("note") or "") for f in doc["faults"])


def test_a_resign_is_counted_as_a_resign_never_as_a_climb(tmp_path, calls):
    cured_home(tmp_path)
    ctx = Ctx(tmp_path, out=printout(G_TWO))
    step.resigned(ctx)
    assert step_attempts.count(ctx.home, step.CLIMBS) == 0
    assert step_attempts.count(ctx.home, step.RESIGN) == 1


def test_the_critics_rows_ride_the_new_signature(tmp_path, monkeypatch, calls):
    plan = cured_home(tmp_path)
    fault = Fault(kind="invented", where="shot_01", note="count 'extras=2' has no chapter span")
    monkeypatch.setattr(step, "critic", lambda ctx, desk: Verdict(
        judge=plan_judge.JUDGE, version=plan_judge.VERSION, passed=False, faults=[fault], confidence=1.0, reads=3))
    assert step.resigned(Ctx(tmp_path, out=printout(G_TWO))) is True
    assert any(f["kind"] == "invented" for f in plan_verdict.read(plan)["faults"])


def test_a_new_row_still_climbs(tmp_path, calls):
    plan = cured_home(tmp_path)
    new = "    G-PRESENT shot 8: child_of_hyde_incident is marked entering and the motion shows no arrival"
    assert step.resigned(Ctx(tmp_path, out=printout(G_TWO, new))) is False
    assert plan_verdict.current(plan) is False and calls == {"writer": 0, "critic": 0}


def test_a_bigger_count_of_a_carried_gate_still_climbs(tmp_path, calls):
    cured_home(tmp_path)
    assert step.resigned(Ctx(tmp_path, out=printout(G_TWO, G_TWO.replace("26", "27")))) is False


def test_a_tier_one_row_still_climbs_even_when_the_signature_carries_it(tmp_path, calls):
    cast = ["CAST BOUND   : ['poole']", "VERDICT      : REFUSED"]
    cured_home(tmp_path, signed_lines=["GRAMMAR      : 1", G_TWO] + cast)
    out = printout(G_TWO) .replace("VERDICT      : REFUSED\n", "") + "\n".join(cast) + "\n"
    assert step.resigned(Ctx(tmp_path, out=out)) is False


def test_an_unflagged_signature_is_never_carried(tmp_path, calls):
    cured_home(tmp_path, flagged=False)
    assert step.resigned(Ctx(tmp_path, out=printout(G_TWO))) is False


def test_a_refusal_with_no_rows_is_never_carried(tmp_path, calls):
    cured_home(tmp_path)
    assert step.resigned(Ctx(tmp_path, out="")) is False


def test_a_broken_provenance_chain_is_never_carried(tmp_path, calls):
    plan = cured_home(tmp_path)
    plan.write_text(json.dumps({"v": 3}), encoding="utf-8")        # a write nobody recorded
    assert step.resigned(Ctx(tmp_path, out=printout(G_TWO))) is False


def test_a_failed_critic_read_keeps_the_carried_signature(tmp_path, monkeypatch, calls):
    plan = cured_home(tmp_path)

    def down(ctx, desk):
        raise RuntimeError("provider down")

    monkeypatch.setattr(step, "critic", down)
    assert step.resigned(Ctx(tmp_path, out=printout(G_TWO))) is True
    assert plan_verdict.current(plan)
