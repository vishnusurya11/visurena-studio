"""ep15 (2026-10-01, eleven plan passes): when an improve rung's draft failed
the contract, its refusals stayed as `pending`, and battery() kept answering
with that ghost -- while a VALID plan stood on disk.  The ladder then deferred
the clean draft under the ghost's note, every resume re-fed the stale note,
and the episode circled for hours.  The judge judges the DISK: pending only
speaks when there is no plan on disk to judge."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.util.spec_from_file_location("step02", ROOT / "scripts" / "episode" / "step_02_plan.py")
step02 = importlib.util.module_from_spec(loader)
sys.modules["step02"] = step02
loader.loader.exec_module(step02)


class Desk:
    def __init__(self, plan: Path, pending):
        self.plan, self.pending = plan, pending


class Ctx:
    def __init__(self, rc: int, out: str):
        self.rc, self.out, self.said = rc, out, []

    def capture_script(self, script):
        return self.rc, self.out

    def log(self, *a, **k):
        self.said.append(a)


def test_pending_speaks_only_when_no_plan_is_on_disk(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text("{}", encoding="utf-8")
    desk = Desk(plan, pending=["CONTRACT: the ghost refusal"])
    ctx = Ctx(0, "")
    assert step02.battery(ctx, desk) is None       # the DISK rules: plan_check passed it
    assert desk.pending is None                     # and the ghost is spent

    desk2 = Desk(tmp_path / "missing.json", pending=["CONTRACT: the draft was never written"])
    assert step02.battery(Ctx(0, ""), desk2) == ["CONTRACT: the draft was never written"]


def test_a_failing_disk_still_refuses(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text("{}", encoding="utf-8")
    desk = Desk(plan, pending=None)
    got = step02.battery(Ctx(1, "G-X shot 1: broken\n"), desk)
    assert got == ["G-X shot 1: broken"]
