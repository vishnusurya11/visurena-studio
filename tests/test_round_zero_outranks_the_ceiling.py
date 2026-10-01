"""ep15 (2026-10-01): the plan fight spent the whole 5 h ceiling before one
take existed, and step 09's ceiling check then refused ROUND 0 -- "takes
terminal rungs, not renders" with nothing to take a terminal ON.  A unit in
that state can never finish: terminals keep a best take, and there is none.
The ceiling binds RETAKES (the ladder prices its own rungs); the first render
of the episode's takes runs regardless, on the clock, so the terminals have
something to keep."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.util.spec_from_file_location("step09", ROOT / "scripts" / "episode" / "step_09_shoot.py")
step09 = importlib.util.module_from_spec(loader)
sys.modules["step09"] = step09
loader.loader.exec_module(step09)


def test_round_zero_runs_even_with_the_ceiling_spent(tmp_path):
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    assert step09.round_zero(room) is True          # no kept take yet
    (room / "T03.mp4").write_bytes(b"take")
    assert step09.round_zero(room) is False         # a take exists: the ceiling rules


def test_a_zero_cost_pass_is_never_refused_by_the_ceiling(tmp_path):
    """All takes rendered, ceiling spent: the step only judges -- exactly what
    'terminals, not renders' demands -- so a 0 s want proceeds (ep15)."""
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "T00.mp4").write_bytes(b"take")
    assert step09.round_zero(room) is False      # the ceiling rules renders...
    # ...and the run() guard lets cost<=0 through (asserted by the source: the
    # zero-cost branch precedes the refusal)
    import inspect
    src = inspect.getsource(step09.run)
    assert "cost <= 0" in src.split("REFUSED: the takes want")[0]
