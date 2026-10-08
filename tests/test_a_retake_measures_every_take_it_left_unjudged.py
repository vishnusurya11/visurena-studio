"""ep21 (2026-10-08 16:20Z): the master eye asked for a retake of shot 1; the
renderer re-rendered T01 AND T02 (T02 was stale), and the round measured only
the shot it asked for.  T02 shipped to QC with no verdict ('unjudged': T02),
QC failed the master, and the brain parked the episode as a gate that gave up.
A retake round measures what it named AND every take it left unjudged."""
from __future__ import annotations

from types import SimpleNamespace

from studio import judged, take_ladder


def test_the_round_measures_the_named_take_and_every_take_left_unjudged(tmp_path, monkeypatch):
    calls = []
    ctx = SimpleNamespace(home=tmp_path, run_script=lambda script, *a, **k: calls.append((script, a)))
    monkeypatch.setattr(take_ladder, "measured", lambda ctx, script, clock, suffix, *extra: calls.append((script, extra)))
    monkeypatch.setattr(judged, "unjudged_takes", lambda take_dir, kinds=("dq",): ["T01", "T02"])
    take_ladder.retake(ctx, [1], "retake_shot", "--approved=x")
    dq = [extra for script, extra in calls if script.endswith("take_dq.py")]
    assert dq and set(dq[0]) >= {"1", "2", "--attempts"}


def test_nothing_unjudged_measures_only_the_named(tmp_path, monkeypatch):
    calls = []
    ctx = SimpleNamespace(home=tmp_path, run_script=lambda script, *a, **k: calls.append((script, a)))
    monkeypatch.setattr(take_ladder, "measured", lambda ctx, script, clock, suffix, *extra: calls.append((script, extra)))
    monkeypatch.setattr(judged, "unjudged_takes", lambda take_dir, kinds=("dq",): [])
    take_ladder.retake(ctx, [1], "retake_shot", "--approved=x")
    dq = [extra for script, extra in calls if script.endswith("take_dq.py")]
    assert [e for e in dq[0] if e.isdigit()] == ["1"]
