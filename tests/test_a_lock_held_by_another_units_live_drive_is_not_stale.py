"""2026-10-08 00:37Z: ep19 was un-parked (its token re-minted) while ep20's
drive was mid-takes.  The tick for ep19 read ep20's gpu.lock as stale (its pid
runs drive.py, but for episode 20) and launched ep19 beside it: two drives on
one GPU, and ep19's bind rewrote the shared refs.json to chapter 19's cast
under ep20's take check ("refs.json holds chapter 19's cast, not chapter 20's").
One unit at a time: a lock whose own episode's drive is alive is live, and
the tick for any other unit waits."""
from __future__ import annotations

import json
from types import SimpleNamespace

from tests import autopilot_cli_fixtures as fx


def _setup(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    live = cli.ProcRow(777, 0.0, f"python scripts/episode/drive.py {fx.CODEX} 20")
    d = fx.deps(tmp_path, "IDLE", procs=[live])
    d.root.mkdir(parents=True, exist_ok=True)
    (d.root / "gpu.lock").write_text(json.dumps({"drive_pid": 777, "episode": 20, "book": fx.CODEX}), encoding="utf-8")
    return cli, book, d


def test_another_units_live_lock_is_not_cleared(tmp_path):
    cli, book, d = _setup(tmp_path)
    assert cli.clear_stale_lock(book, fx.CODEX, 19, d, d.procs()) is False
    assert (d.root / "gpu.lock").exists()
    assert cli.other_unit_running(d, fx.CODEX, 19, d.procs()) == 20


def test_the_tick_for_the_other_unit_waits_instead_of_launching(tmp_path):
    cli, book, d = _setup(tmp_path)
    signals = SimpleNamespace(engine_up=True, lock={"drive_pid": 777, "episode": 20}, proc_alive=False, drive_rows=[])
    got = cli.act_idle(book, fx.CODEX, 19, SimpleNamespace(order=None), signals, d)
    assert got["action"] == "wait" and got.get("other") == 20
    assert d.calls["popen"] == []


def test_a_dead_other_drive_still_reads_as_stale(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "IDLE", procs=[])
    d.root.mkdir(parents=True, exist_ok=True)
    (d.root / "gpu.lock").write_text(json.dumps({"drive_pid": 777, "episode": 20}), encoding="utf-8")
    assert cli.other_unit_running(d, fx.CODEX, 19, d.procs()) is None
    assert cli.clear_stale_lock(book, fx.CODEX, 19, d, d.procs()) is True
