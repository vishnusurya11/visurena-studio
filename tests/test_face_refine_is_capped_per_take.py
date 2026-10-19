"""Face refine is capped per take and in time (owner 2026-10-18, the cap table's
`face_refine`: 1 per take + 15 min).  The count is persisted in attempts.json, so a relaunch
never re-refines a take a run already refined (STEP_CAPS.md row 09g: no persisted count)."""
from __future__ import annotations

import json
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


def stale_room(tmp_path):
    """Jekyll ep01's shape: T06 decided `no_faces` under the 60 px wall, its round spent with no job."""
    book = tmp_path / "book"
    home = episode_home.home(book, 1)
    room = home / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "T06.mp4").write_bytes(b"take")
    entry = {"status": "no_faces", "take_sha8": cli.sha8(room / "T06.mp4"), "people": []}
    (room / "refine.json").write_text(json.dumps({"T06": entry}))
    step_attempts.spend(home, "face_refine.T06")
    return book, home, room


def test_a_no_faces_row_of_the_60_px_wall_is_owed_a_look_under_the_new_one(tmp_path, monkeypatch):
    book, home, room = stale_room(tmp_path)
    monkeypatch.setattr(cli, "selection", lambda b, n: [6])
    assert cli.pending(book, 1) == [6]


def test_the_refund_ends_with_the_first_new_decision(tmp_path, monkeypatch):
    book, home, room = stale_room(tmp_path)
    monkeypatch.setattr(cli, "selection", lambda b, n: [6])
    cli.write_entry(room, 6, {"status": "all_readable", "take_sha8": "0" * 8, "people": []})
    assert cli.pending(book, 1) == []


def test_the_refine_stops_queueing_at_its_wall():
    wall = step_caps.wall_s("face_refine")
    assert wall == 15 * 60
    assert not cli.wall_spent(began=0.0, now=wall - 1)
    assert cli.wall_spent(began=0.0, now=wall)


def test_a_none_found_or_all_readable_result_spends_no_refine_round(tmp_path):
    home = tmp_path / "ep"
    for status in ("none_found", "all_readable"):
        cli.count_if_worked(home, cli.TakeWork(7, "abc", [], jobs=[], status=status))
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
