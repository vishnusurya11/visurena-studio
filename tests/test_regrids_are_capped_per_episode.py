"""Owner 2026-10-18: regrids are 2 rounds and 20 min per EPISODE (STEP_CAPS 08d: 5 regrid
batches in one episode).  Persisted in attempts.json; at the cap the panels stand (keep best),
the CAP line is said, the run goes on.  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import panel_ladder as pl, step_attempts, step_caps
from studio.judges.verdict import Fault, Verdict


def _climb(tmp_path, clock=lambda: 0.0):
    ctx = SimpleNamespace(home=tmp_path, number=1, logged=[], log=lambda m, **k: None)
    return pl.Climb(ctx, tmp_path, lambda *a: None, clock=clock)


def _verdict():
    return Verdict(judge="eye_panels", version="1", passed=False, confidence=1.0, reads=3,
                   faults=[Fault(kind="clones", where="S03")])


def test_the_cap_is_two_rounds_and_20_minutes_per_episode():
    row = step_caps.cap("regrid")
    assert (row.rounds, row.wall_s, row.per) == (2, 20 * 60, "episode")


def test_two_episode_rounds_make_the_climb_uncurable(tmp_path, monkeypatch):
    monkeypatch.setattr(pl, "machine_clean", lambda home: False)
    c = _climb(tmp_path)
    assert c.curable(_verdict()) is True
    step_attempts.spend(tmp_path, "regrid", 100.0)
    step_attempts.spend(tmp_path, "regrid", 100.0)
    assert c.curable(_verdict()) is False


def test_the_20_minute_wall_makes_it_uncurable_on_one_round(tmp_path, monkeypatch):
    monkeypatch.setattr(pl, "machine_clean", lambda home: False)
    step_attempts.spend(tmp_path, "regrid", 20 * 60 + 1)
    assert _climb(tmp_path).curable(_verdict()) is False


def test_the_wall_is_read_between_grids_not_inside_one(tmp_path):
    now = [0.0]
    c = _climb(tmp_path, clock=lambda: now[0])
    c.began = 0.0
    assert c.over_wall() is False
    now[0] = 20 * 60 + 1
    assert c.over_wall() is True


def test_a_prior_runs_seconds_count_toward_the_wall(tmp_path):
    step_attempts.spend(tmp_path, "regrid", 19 * 60)
    now = [0.0]
    c = _climb(tmp_path, clock=lambda: now[0])
    c.began = 0.0
    now[0] = 61.0
    assert c.over_wall() is True


def test_the_cap_line_is_said_once_at_the_cap(tmp_path, capsys):
    step_attempts.spend(tmp_path, "regrid", 600.0)
    step_attempts.spend(tmp_path, "regrid", 600.0)
    assert pl.cap_line(tmp_path, 1).startswith("CAP regrid: 2/2 rounds, 20:00, kept best")
