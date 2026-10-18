"""Owner 2026-10-18: retakes are 2 rounds and 45 min per EPISODE, persisted in attempts.json,
so a relaunch, a second drive run or a master-eye redo reads the same count (STEP_CAPS 09f:
7 retake batches in one episode after the per-climb cap).  At the cap: keep best, say the CAP
line, go on.  $0."""
from __future__ import annotations

from studio import step_attempts, step_caps, take_ladder as tl


def _room(home):
    room = home / "takes" / "r2v"
    room.mkdir(parents=True)
    return room


def _curable(monkeypatch):
    monkeypatch.setattr(tl, "route", lambda v, r, try_i=1: {"seed": {2: []}})
    return type("V", (), {"faults": []})()


def test_the_cap_is_the_tables_two_rounds_and_45_minutes():
    row = step_caps.cap("retakes")
    assert (row.rounds, row.wall_s, row.per) == (2, 45 * 60, "episode")
    assert tl.ROUNDS_CAP == 2


def test_two_episode_rounds_close_the_climb_though_the_room_is_fresh(tmp_path, monkeypatch):
    room, v = _room(tmp_path), _curable(monkeypatch)
    assert tl.still_curable(room, v, home=tmp_path) is True
    step_attempts.spend(tmp_path, "retakes", 600.0)
    step_attempts.spend(tmp_path, "retakes", 600.0)
    assert tl.still_curable(room, v, since=10**12, home=tmp_path) is False   # a retry's `since` cannot reset it


def test_the_45_minute_wall_closes_the_climb_on_one_round(tmp_path, monkeypatch):
    room, v = _room(tmp_path), _curable(monkeypatch)
    step_attempts.spend(tmp_path, "retakes", 45 * 60 + 1)
    assert tl.episode_spent(tmp_path) is True
    assert tl.still_curable(room, v, home=tmp_path) is False


def test_one_round_under_the_wall_still_climbs(tmp_path, monkeypatch):
    room, v = _room(tmp_path), _curable(monkeypatch)
    step_attempts.spend(tmp_path, "retakes", 300.0)
    assert tl.episode_spent(tmp_path) is False
    assert tl.still_curable(room, v, home=tmp_path) is True


def test_the_cap_line_names_rounds_time_and_what_was_kept(tmp_path):
    step_attempts.spend(tmp_path, "retakes", 600.0)
    step_attempts.spend(tmp_path, "retakes", 600.0)
    assert tl.cap_line(tmp_path, 3) == "CAP retakes: 2/2 rounds, 20:00, kept best (3 advisories)"


def test_a_spent_episode_renders_no_retake_batch(tmp_path):
    step_attempts.spend(tmp_path, "retakes", 1.0)
    step_attempts.spend(tmp_path, "retakes", 1.0)
    said = []
    ctx = type("C", (), {"home": tmp_path, "log": lambda s, m, **k: said.append(m)})()
    assert tl.refuse_spent(ctx, 2) is True
    assert said and said[0].startswith("CAP retakes: 2/2")


def test_the_first_renders_keep_a_120_minute_wall_and_say_the_overrun():
    from scripts.episode import step_09_shoot as s9
    assert s9.first_wall_line(119 * 60) == ""
    assert s9.first_wall_line(121 * 60).startswith("CAP takes: 1/1 rounds, 121:00, kept best")
