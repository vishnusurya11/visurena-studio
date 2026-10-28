"""A master-ladder retake moves the take set, so the take eye that settled the ladder's keep_best
takes no longer names these bytes (`assemble.current_eye` matches the whole set's fingerprint).
The recut then read no eye, admitted nothing flagged, and G-DEAD refused takes the ladder had
already kept: Jekyll ep02 T13 and ep05 T00/T11/T16 ("G-DEAD T00: a failed take"), one wasted
launch each; the next launch's step 09 re-signed the eye and the same cut passed.

So the recut re-signs the take eye before it assembles. An eye already signed for the bytes is
kept without a read (`step_09_shoot.signed_for`), so a recut that moved no take costs nothing."""
from __future__ import annotations

from types import SimpleNamespace

from scripts.episode import step_09_shoot, step_11_qc


def test_the_take_eye_is_signed_before_the_recut_assembles(monkeypatch):
    order = []
    monkeypatch.setattr(step_09_shoot, "judge_takes", lambda ctx, flag: order.append(("eye", flag)))
    monkeypatch.setattr(step_09_shoot, "approved", lambda policy: "--approved=render")
    monkeypatch.setattr(step_11_qc, "qc_report", lambda ctx, extra: order.append(("qc",)))
    ctx = SimpleNamespace(stage="episode", run_script=lambda *a, **k: order.append(("run", a[0])))
    step_11_qc.recut(ctx, [])
    assert order == [("eye", "--approved=render"), ("run", "scripts/episode/assemble.py"), ("qc",)]
