"""ep19 (2026-10-06, launch04): the $3 wall refused the writer INSIDE the plan
ladder, `studio.llm.OverBudget` climbed out through Desk.write, the run died
on a traceback and the drive read `failed` -- indistinguishable from a crash.
The wall is a refusal like the contract's: the desk carries it as a pending
MONEY line, the ladder ends at its terminal (keep_best / defer) with a
deferral on disk, nothing is raised, and the wall's own line is printed so
the drive ledger names the class.  No test spends: the writer is a fake that
raises what guard_spend would have."""
from __future__ import annotations

import json
from types import SimpleNamespace

from scripts.episode import step_02_plan as step02
from studio import judged_gate, llm, plan_ladder
from studio.gate_policy import Policy
from studio.run_budget import EPISODE_SHARES, Budget
from tests.test_episode_writer import canned_plan

WALL = "episode ep03 has spent $3.10 of its $3.00 ceiling; this call would cross it, so it was not sent"


class SpentWriter:
    def __init__(self):
        self.asked = 0

    def write(self, brief, refusals, **kw):
        self.asked += 1
        raise llm.OverBudget(WALL)


class Ctx:
    def __init__(self, tmp_path):
        self.stage, self.unit, self.number = "episode", "ep03", 3
        self.book_dir = tmp_path / "book"
        self.home = self.book_dir / "episodes" / "ep03"
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
        self.learned, self.said = [], []

    def learn(self, learning):
        self.learned.append(learning)

    def log(self, msg, **kw):
        self.said.append(msg)

    def capture_script(self, script, *args):
        return 1, "G-X shot 1: the battery refuses this draft\n"


AUTO = Policy(state="auto", judge="plan@1", decision="2026-09-24-automate-the-taste-gates",
              terminal="keep_best", battery_terminal="defer")


def _desk(ctx, writer):
    ctx.home.mkdir(parents=True, exist_ok=True)
    plan = ctx.home / "plan.json"
    plan.write_text(json.dumps(canned_plan()), encoding="utf-8")
    desk = plan_ladder.Desk(ctx, plan, writer=writer)
    desk.brief = {}
    return desk


def test_the_wall_is_a_pending_money_refusal_not_a_raise(tmp_path, capsys):
    desk = plan_ladder.Desk(SimpleNamespace(book_dir=tmp_path, number=3), tmp_path / "plan.json",
                            writer=SpentWriter())
    desk.brief = {}
    desk.write(None)                                   # nothing raised
    assert desk.pending == [f"MONEY: {WALL}"]
    assert not (tmp_path / "plan.json").exists()
    assert "studio.llm.OverBudget: episode ep03 has spent $3.10" in capsys.readouterr().out


def test_the_ladder_ends_at_its_terminal_with_a_deferral_on_disk(tmp_path):
    ctx = Ctx(tmp_path)
    writer = SpentWriter()
    desk = _desk(ctx, writer)
    desk.battery_terminal = AUTO.battery_terminal
    rungs = judged_gate.Rungs(plan_ladder.ladder(2), take=desk.take)
    signed = judged_gate.clear(ctx, "PLAN", judge=lambda: step02.judge(ctx, desk), sign=desk.sign,
                               ladder=rungs, terminal=desk.terminal, policy=AUTO)
    assert signed.name == plan_ladder.DEFERRED and not desk.plan.exists()
    aside = json.loads(signed.read_text(encoding="utf-8"))
    assert aside["verdict"] == "DEFERRED" and aside["passes"] == 1 and aside["draft"]["number"] == 3
    assert writer.asked == 4                           # improve x2, fresh_brief, model_tier: every rung refused for $0
    last = ctx.learned[-1]                             # the terminal learning: the policy's rung name, the cause's word in the note
    assert last.terminal and last.action == "keep_best" and last.note.endswith("-> defer")
    assert any("studio.llm.OverBudget" in s for s in ctx.said)


def test_the_drive_reads_the_caught_form_as_the_money_wall(capsys, tmp_path):
    """The log of a run that ended this way carries the wall's class line and
    the deferral line; the money is the cause and the ledger says so."""
    from studio import episode_drive
    desk = plan_ladder.Desk(SimpleNamespace(book_dir=tmp_path, number=3), tmp_path / "plan.json",
                            writer=SpentWriter())
    desk.brief = {}
    desk.write(None)
    log = capsys.readouterr().out + "DEFERRED PLAN | ep03 | MONEY: the wall | aside: episodes/ep03/plan.deferred.json\n"
    assert episode_drive.outcome(log) == "overbudget"
    assert episode_drive.error_class(log) == "studio.llm.OverBudget"
