"""A stale timeline is not a fault of the plan (ep13, 2026-09-26).

The plan step runs BEFORE the timeline step, and plan_check refused a changed
plan with 'timeline is older than the plan' -- so an edited plan could never
pass its own gate and reach the step that rebuilds the timeline.  The battery
falls back to the plan's own projection and says so; step 05 rebuilds."""
from __future__ import annotations

from scripts.episode import plan_check


def test_a_stale_timeline_falls_back_to_the_projection(tmp_path, monkeypatch, capsys):
    home = tmp_path / "episodes" / "ep13"
    home.mkdir(parents=True)
    (home / "placed.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(plan_check.episode_home, "home", lambda book, n: home)

    def stale(book, number, episode):
        raise SystemExit("episode 13: timeline is older than the plan -- rerun scripts/episode/timeline.py")
    monkeypatch.setattr(plan_check.episode_home, "load_placed", stale)
    monkeypatch.setattr(plan_check, "projected", lambda episode, rate: [{"index": 0}])
    assert plan_check.measured_or_projected(tmp_path, 13, object(), 2.6) == [{"index": 0}]
    assert "timeline is older than the plan" in capsys.readouterr().out
