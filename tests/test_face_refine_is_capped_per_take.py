"""Face refine is capped per take and in time (owner 2026-10-18, the cap table's
`face_refine`: 1 per take + 15 min).  The count is persisted in attempts.json, so a relaunch
never re-refines a take a run already refined (STEP_CAPS.md row 09g: no persisted count)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.episode import face_refine as cli  # noqa: E402
from studio import episode_home, step_attempts, step_caps  # noqa: E402


def test_a_take_refined_once_is_never_owed_again(tmp_path, monkeypatch):
    book = tmp_path / "book"
    home = episode_home.home(book, 1)
    (home / "takes" / "r2v").mkdir(parents=True)
    monkeypatch.setattr(cli, "selection", lambda b, n: [3, 5])
    assert cli.pending(book, 1) == [3, 5]
    cli.count_refine(home, 3)
    assert step_attempts.count(home, "face_refine.T03") == 1
    assert cli.pending(book, 1) == [5]


def test_the_refine_stops_queueing_at_its_wall():
    wall = step_caps.wall_s("face_refine")
    assert wall == 15 * 60
    assert not cli.wall_spent(began=0.0, now=wall - 1)
    assert cli.wall_spent(began=0.0, now=wall)


def test_a_no_faces_result_spends_no_refine_round(tmp_path):
    home = tmp_path / "ep"
    work = cli.TakeWork(7, "abc", [], jobs=[], status="no_faces")
    cli.count_if_worked(home, work)
    assert step_attempts.count(home, "face_refine.T07") == 0


def test_a_take_with_a_job_spends_its_round(tmp_path):
    home = tmp_path / "ep"
    cli.count_if_worked(home, cli.TakeWork(7, "abc", [], jobs=[object()]))
    assert step_attempts.count(home, "face_refine.T07") == 1


def test_a_spent_retake_wall_counts_as_the_one_retake_taken(tmp_path, monkeypatch):
    from studio import take_ladder, warp_gate
    monkeypatch.setattr(take_ladder, "episode_spent", lambda home: True)
    monkeypatch.setattr(take_ladder, "attempts_of", lambda room, i: 0)
    assert cli.taken_of(tmp_path, tmp_path, 3) == warp_gate.RETAKES
    monkeypatch.setattr(take_ladder, "episode_spent", lambda home: False)
    assert cli.taken_of(tmp_path, tmp_path, 3) == 0
