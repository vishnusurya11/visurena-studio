"""Retro 2026-10-20 item 12 / V4: 9 shas ran over ep01's 13 first-delivery runs
(drive_launch01..13 print "code moved mid-episode"), 62 `code_moved` and 35
`successor` rows fell in the ep01 window, and 6 of the 13 runs ended refused.

Code is held still under a live drive:
  (1) the launch records the sha it launched on (gpu.lock and the launch row);
  (2) HEAD moving while a drive is alive hands the supervisor over to nothing:
      one `code_moved_during_run` row, the loop keeps ticking, and the handover
      happens once the drive has ended;
  (3) `may-commit` refuses a runtime commit while a drive is alive and names
      `pause --at-boundary`;
  (4) a relaunch on moved code prints which checks the new judge code invalidates."""
from __future__ import annotations

import json

from studio import autopilot as ap
from tests import autopilot_cli_fixtures as fx

OLD = "0ld0ld0ld0ld"


def _live(tmp_path, heads):
    """A RUNNING episode 1: a gpu.lock and its drive.py in the process table."""
    cli = fx.load()
    live = cli.ProcRow(777, 0.0, f"python scripts/episode/drive.py {fx.CODEX} 1")
    d = fx.deps(tmp_path, "RUNNING", procs=[live])
    d.root.mkdir(parents=True, exist_ok=True)
    (d.root / "gpu.lock").write_text(json.dumps({"drive_pid": 777, "episode": 1}), encoding="utf-8")
    seq = iter(heads)
    d.git = lambda *a: "" if a[0] in ("status", "diff", "log") else next(seq, heads[-1])
    return cli, d


def _events(cli, book, name=None):
    rows = cli.rows_of(book / "autopilot" / "events.jsonl")
    return [r for r in rows if name is None or r["event"] == name]


def test_head_moving_under_a_live_drive_keeps_the_loop_and_spawns_no_successor(tmp_path):
    book = fx.book(tmp_path)
    cli, d = _live(tmp_path, ["aaa\n", "aaa\n", "bbb\n"])
    assert cli.run_loop(book, fx.CODEX, d, every=0, ticks=4) == 0
    assert not _events(cli, book, "successor") and not _events(cli, book, "code_moved")
    held = _events(cli, book, "code_moved_during_run")
    assert len(held) == 1 and held[0]["from"] == "aaa" and held[0]["to"] == "bbb"
    assert cli.read_json(d.root / "heartbeat.json")["tick"] == 4, "every tick ran"


def test_head_moving_with_no_drive_alive_still_hands_over(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "PAUSED", reason="paused")
    heads = iter(["aaa\n", "aaa\n", "bbb\n", "bbb\n", "bbb\n"])
    d.git = lambda *a: "" if a[0] == "status" else next(heads)
    cli.run_loop(book, fx.CODEX, d, every=0, ticks=5)
    assert _events(cli, book)[-1]["event"] == "successor"


def test_the_launch_records_the_sha_it_launched_on(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    cli.launch(book, fx.CODEX, 1, d, "launch")
    assert cli.read_json(d.root / "gpu.lock")["sha"] == "abc123def"
    assert _events(cli, book, "launch")[-1]["sha"] == "abc123def"


def test_a_runtime_commit_waits_while_a_drive_runs(tmp_path):
    book = fx.book(tmp_path)
    cli, d = _live(tmp_path, ["aaa\n"])
    said = cli.commit_hold(book, fx.CODEX, d, ["studio/face_refine.py", "tests/test_x.py"])
    assert said and "pause --at-boundary" in said and "ep01" in said
    assert cli.commit_hold(book, fx.CODEX, d, ["tests/test_x.py", "docs/a.md", "architecture/index.html"]) is None


def test_any_commit_may_land_with_no_drive_alive(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    assert cli.commit_hold(book, fx.CODEX, fx.deps(tmp_path), ["studio/face_refine.py"]) is None


def test_judge_code_names_the_checks_it_invalidates():
    names = ["studio/judges/master_eye.py", "scripts/episode/take_dq.py", "studio/face_gate.py",
             "studio/comfy.py", "tests/test_take_dq.py", "gates.yaml", "scripts/episode/take_content_check.py"]
    assert ap.invalidated_checks(names) == ["face_gate", "gates.yaml", "master_eye", "take_content_check", "take_dq"]
    assert ap.invalidated_checks(["studio/comfy.py", "docs/x.md"]) == []


def test_a_relaunch_on_moved_code_prints_the_invalidated_checks(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    home = book / "episodes" / "ep01"
    home.mkdir(parents=True)
    (home / "drive.jsonl").write_text(json.dumps({"event": "start", "sha": OLD}) + "\n", encoding="utf-8")
    d.git = lambda *a: ("studio/judges/master_eye.py\nstudio/comfy.py\n" if a[0] == "diff"
                        else "" if a[0] == "status" else "abc123def\n")
    cli.launch(book, fx.CODEX, 1, d, "relaunch")
    log = (home / "drive_launch01.log").read_text(encoding="utf-8")
    assert "master_eye" in log and "comfy" not in log and OLD[:8] in log
    row = _events(cli, book, "judge_code_moved")[-1]
    assert row["checks"] == ["master_eye"] and row["from"] == OLD[:8]


def test_a_relaunch_on_the_same_code_prints_nothing(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    home = book / "episodes" / "ep01"
    home.mkdir(parents=True)
    (home / "drive.jsonl").write_text(json.dumps({"event": "start", "sha": "abc123def"}) + "\n", encoding="utf-8")
    cli.launch(book, fx.CODEX, 1, d, "relaunch")
    assert not _events(cli, book, "judge_code_moved")


def test_the_cli_has_a_may_commit_command():
    assert fx.load().parser().parse_args(["may-commit", "--book", "x"]).cmd == "may-commit"
