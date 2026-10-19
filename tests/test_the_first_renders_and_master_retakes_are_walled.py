"""Owner 2026-10-18: the step-09 first renders stop BETWEEN renders at the 120 min wall (a
take in flight finishes, none new starts, CAP line, go on), and a master-eye retake counts
against the episode's 2 retake rounds.  $0."""
from __future__ import annotations

from types import SimpleNamespace

from scripts.episode import takes_r2v as tr
from studio import master_ladder, step_attempts, take_ladder


def test_a_first_render_pass_is_over_the_wall_at_120_minutes():
    assert tr.first_wall_spent(0.0, 119 * 60, []) is False
    assert tr.first_wall_spent(0.0, 120 * 60, []) is True


def test_a_retake_pass_is_not_walled_here():
    assert tr.first_wall_spent(0.0, 999 * 60, [3]) is False


def test_walled_takes_are_not_lost_and_say_the_cap_line():
    lost = [({"index": 4}, tr.BOUNDARY), ({"index": 5}, "boom")]
    kept, line = tr.after_wall(lost, 121 * 60)
    assert kept == [({"index": 5}, "boom")]
    assert line.startswith("CAP takes: 1/1 rounds, 121:00, kept best")


def _ctx(tmp_path, said):
    return SimpleNamespace(home=tmp_path, stage="episode", log=lambda m, **k: said.append(m))


def test_a_master_retake_spends_an_episode_round(tmp_path, monkeypatch):
    calls = []
    def renders(*a, **k):     # a retake that writes the take: only a round that changed bytes is booked
        calls.append(a)
        (tmp_path / "takes" / "r2v").mkdir(parents=True)
        (tmp_path / "takes" / "r2v" / "T03.mp4").write_bytes(b"new take")
    monkeypatch.setattr(take_ladder, "retake", renders)
    monkeypatch.setattr("scripts.episode.step_09_shoot.approved", lambda p: "--x")
    monkeypatch.setattr("studio.gate_policy.of", lambda *a: None)
    v = SimpleNamespace(faults=[])
    master_ladder.retake_through_take_ladder(_ctx(tmp_path, []), 3, v)
    assert calls and step_attempts.count(tmp_path, "retakes") == 1


def test_a_spent_episode_refuses_the_master_retake_and_keeps_the_master(tmp_path, monkeypatch):
    step_attempts.spend(tmp_path, "retakes", 1.0)
    step_attempts.spend(tmp_path, "retakes", 1.0)
    calls, said = [], []
    monkeypatch.setattr(take_ladder, "retake", lambda *a, **k: calls.append(a))
    master_ladder.retake_through_take_ladder(_ctx(tmp_path, said), 3, SimpleNamespace(faults=[]))
    assert not calls and said[0].startswith("CAP retakes: 2/2")
