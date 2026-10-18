"""Two autopilot faults of 2026-10-18 (Jekyll Kawajiri ep01):

(a) WAIT_TREE never re-checked once the tree was clean: the last drive's end row said
    "REFUSED to start: the working tree is dirty", and `derive` read that row every tick, so the
    series sat about an hour on a clean tree.  The tree is re-read every tick; a clean one launches.
(b) `autopilot.py pause --book <codex>` exited 0 while status still said RUNNING with no paused
    field: status.json is written by the tick, and the pause never touched it.  A pause now
    rewrites status at once, `status` reads the live flag, and the next tick launches nothing.
"""
from __future__ import annotations

import json
from dataclasses import replace

from studio import autopilot as ap
from studio.autopilot import State
from tests import autopilot_cli_fixtures as fx
from tests.test_autopilot_derives_state_from_disk import rows, signals

REFUSED_DIRTY = "ep20: REFUSED to start: the working tree is dirty; commit the code first (fix #2)"


def test_a_clean_tree_after_a_dirty_refusal_launches():
    s = signals(drive_rows=rows(("start",), ("end", 2)), log_tail=REFUSED_DIRTY, porcelain="")
    got = ap.derive(s, 20)
    assert got.state is State.IDLE and got.reason == "tree_clean"


def test_a_tree_still_dirty_still_waits():
    s = signals(drive_rows=rows(("start",), ("end", 2)), log_tail=REFUSED_DIRTY, porcelain=" M studio/x.py\n")
    assert ap.derive(s, 20).state is State.WAIT_TREE


def _status(book):
    return json.loads((book / "autopilot" / "status.json").read_text(encoding="utf-8"))


def test_a_pause_shows_in_status_at_once_and_the_tick_honours_it(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "IDLE")
    cli.tick(book, fx.CODEX, d, 1)
    assert _status(book)["series"]["paused"] is False
    cli.set_paused(book, fx.CODEX, True)
    now = _status(book)
    assert now["series"]["paused"] is True and now["series"]["state"] == "paused"
    assert cli.status_now(book)["series"]["paused"] is True
    launched = len(d.calls["popen"])
    doc = cli.tick(book, fx.CODEX, d, 2)
    assert doc["episode"]["state"] == "PAUSED" and doc["series"]["paused"] is True
    assert len(d.calls["popen"]) == launched, "a paused series launches nothing"


def test_status_reads_the_live_flag_over_a_stale_file(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    cli.tick(book, fx.CODEX, fx.deps(tmp_path, "RUNNING"), 1)
    series = book / "autopilot" / "series.json"
    doc = json.loads(series.read_text(encoding="utf-8"))
    series.write_text(json.dumps({**doc, "paused": True}), encoding="utf-8")   # paused behind the file
    assert cli.status_now(book)["series"]["state"] == "paused"
    cli.set_paused(book, fx.CODEX, False)
    assert cli.status_now(book)["series"]["paused"] is False


def test_a_stop_file_pauses_and_launches_nothing_and_resume_clears_it(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    stop = book / "autopilot" / "STOP"
    stop.parent.mkdir(parents=True, exist_ok=True)
    stop.write_text("", encoding="utf-8")
    d = fx.deps(tmp_path, "IDLE")
    doc = cli.tick(book, fx.CODEX, d, 1)
    assert doc["series"]["paused"] is True and not d.calls["popen"]
    assert cli.launch(book, fx.CODEX, 1, d, "launch")["action"] == "paused"
    assert not d.calls["popen"]
    cli.set_paused(book, fx.CODEX, False)
    assert not stop.exists() and cli.status_now(book)["series"]["paused"] is False


def test_a_step_relaunched_past_its_cap_goes_to_its_terminal(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "IDLE")
    for _ in range(cli.relaunch_allowed("09")):
        assert cli.step_guard(book, 1, "step 09 takes", d) is None
    assert cli.step_guard(book, 1, "step 09 takes", d) == "step_cap"
    assert cli.step_guard(book, 1, "no step named", d) is None
