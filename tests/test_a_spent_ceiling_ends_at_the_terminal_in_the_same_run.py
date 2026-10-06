"""The budget deferral is gone (five-hour verdict): with ONE episode-wide
clock, idling clocks nothing, so no later run can ever pay more than
headroom() says now.  `judged_gate.affordable` answers share -> pool ->
headroom -> terminal(False); it never raises, and climbed() falls through to
ended() so keep-best/still signs flagged IN THE SAME RUN (ep16: EYE_TAKES
'DEFERRED: needs 565 s ... run again to resume' spun the drive forever)."""
from __future__ import annotations

from studio import judged_gate
from studio.ladder import Rung
from studio.run_budget import Budget

SHARES = {"09": 0.1, "ladders": 0.0}


class Ctx:
    def __init__(self, t, ceiling=1000.0):
        self.stage, self.unit = "episode", "ep16"
        self.budget = Budget(ceiling, SHARES, clock=lambda: t[0])
        self.learned = []
        self.budget.start("09")

    def learn(self, learning):
        self.learned.append(learning)


def test_true_exhaustion_is_terminal_false_never_a_systemexit():
    t = [0.0]
    ctx = Ctx(t)
    t[0] = 950.0                                    # share overdrawn, pool 0, headroom 50
    assert judged_gate.affordable(ctx, "EYE_TAKES", Rung("seed", 565.0), 0) is False
    assert [(l.gate, l.action, l.terminal) for l in ctx.learned] == [("budget", "terminal", False)]
    assert ctx.learned[0].threshold == 565.0


def test_headroom_pays_what_the_share_cannot_with_an_audit_row():
    t = [0.0]
    ctx = Ctx(t)
    t[0] = 400.0                                    # share gone, headroom 600
    assert judged_gate.affordable(ctx, "EYE_TAKES", Rung("seed", 565.0), 0) is True
    assert [l.action for l in ctx.learned] == ["headroom"]


def test_an_affordable_share_pays_in_silence():
    t = [10.0]
    ctx = Ctx(t)
    t[0] = 20.0                                     # 90 s of the 100 s share left
    assert judged_gate.affordable(ctx, "EYE_TAKES", Rung("seed", 50.0), 0) is True
    assert ctx.learned == []


def test_the_gate_no_longer_carries_the_deferral():
    """judged_gate.affordable was the ONLY emitter of 'DEFERRED: ... needs
    ... s' (verified by grep before landing); episode_drive.outcome keeps its
    regex for OLD drive logs only."""
    from pathlib import Path
    import inspect
    source = inspect.getsource(judged_gate.affordable)
    assert "SystemExit" not in source and "DEFERRED" not in source
    drive = (Path(__file__).resolve().parents[1] / "studio" / "episode_drive.py").read_text(encoding="utf-8")
    assert "deferred" in drive                      # the historical-log regex stays
