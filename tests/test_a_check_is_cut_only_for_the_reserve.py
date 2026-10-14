"""A CHECK is never cut for time while the episode's 6 h has room (owner 2026-10-14:
"make sure you aren't skipping the DQ checks").

The 5 h ceiling closes RUNGS (re-renders); it was also closing checks: past it a
take's dq report and a passing QC report on the same bytes stood under moved
measuring code, so a new or repaired check never read them.  Jekyll HEL ep01
crossed 5 h at 07:30 with 32 min owed downstream and ~50 min of room under 6 h.
Now a check is cut only when running it would eat the downstream reserve
(`Budget.leaves_reserve` against the owner's limit), and a cheap check never is.
With no limit set the old ceiling rule stands."""
from __future__ import annotations

import json
from types import SimpleNamespace

from studio.run_budget import CHEAP_CHECK_SECONDS, EPISODE_SHARES, OWNER_LIMIT_SECONDS, Budget
from tests.test_a_spent_clock_ships_flagged_and_never_parks import GOOD, _qc_ctx, step09, step11


def _budget(spent: float, limit: float | None = OWNER_LIMIT_SECONDS) -> Budget:
    b = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0, limit=limit)
    b.charge(spent)
    return b


def test_past_the_ceiling_with_room_under_the_limit_a_check_runs():
    assert not _budget(18540).checks_cut("09", 600)          # ep01: 5.15 h + 10 min + 32 min owed < 6 h


def test_a_check_that_would_eat_the_reserve_is_cut():
    assert _budget(20500).checks_cut("09", 600)              # 5.7 h + 10 min + 32 min owed > 6 h


def test_a_cheap_check_is_never_cut():
    assert not _budget(21590).checks_cut("09", CHEAP_CHECK_SECONDS)


def test_without_a_limit_the_ceiling_rule_stands():
    assert _budget(18001, limit=None).checks_cut("09", 600)
    assert not _budget(0, limit=None).checks_cut("09", 600)


def test_step_09_measures_again_past_the_ceiling_while_the_limit_has_room(tmp_path):
    ctx = SimpleNamespace(budget=_budget(18540), home=tmp_path)
    assert step09.dq_flags(ctx) == []
    ctx = SimpleNamespace(budget=_budget(21000), home=tmp_path)
    assert step09.dq_flags(ctx) == ["--ceiling-spent"]


def test_a_passing_qc_report_under_old_code_is_measured_again_while_the_limit_has_room(tmp_path):
    ctx, path = _qc_ctx(tmp_path, {**GOOD, "passed": True}, spent=True)
    ctx.budget = _budget(18540)
    doc = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps({**doc, "measures_sha8": "00000000"}), encoding="utf-8")
    ran = []
    ctx.run_script = lambda *a, **k: ran.append(a)
    step11.qc_report(ctx, ["--engine=r2v"])
    assert ran and ran[0][0] == "scripts/episode/qc.py"
