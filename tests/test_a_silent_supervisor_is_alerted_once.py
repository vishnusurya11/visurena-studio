"""Retro 2026-10-20 item 7 (ops skeptic #1, #9): the supervisor's heartbeat stopped
for 4.68 h on ep01 (events.jsonl 2026-10-19T12:39:32Z: `supervisor_died_at`,
heartbeat_age_s 16840, tick 12) and nothing said so until a new instance adopted
the old heartbeat at 05:39 PDT.  The cause, read from the Windows System log:
Windows Update restarted the PC at 00:59 and 01:03 PDT (outside active hours
06-00), and the task's Interactive logon could not run again until the owner
logged on at 05:40.

A second scheduled task reads heartbeat.json's age: past ten minutes of silence
it writes ONE `supervisor_silent` row and sends ONE message per silence."""
from __future__ import annotations

import json
from pathlib import Path

from tests import autopilot_cli_fixtures as fx

EP01_GAP_S = 16_840
"""heartbeat_age_s of the 2026-10-19T12:39:32Z `supervisor_died_at` row."""


def _beat(d, age: float, tick: int = 12) -> None:
    d.root.mkdir(parents=True, exist_ok=True)
    body = {"ts": 1_000_000.0 - age, "tick": tick, "state": "PAUSED", "episode": 1}
    (d.root / "heartbeat.json").write_text(json.dumps(body), encoding="utf-8")


def _silent(cli, book) -> list[dict]:
    return [r for r in cli.rows_of(book / "autopilot" / "events.jsonl") if r["event"] == "supervisor_silent"]


def test_the_ep01_gap_writes_one_alert_row_and_one_message(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    _beat(d, EP01_GAP_S)
    cli.watchdog(book, d)
    cli.watchdog(book, d)
    rows = _silent(cli, book)
    assert len(rows) == 1 and rows[0]["heartbeat_age_s"] == EP01_GAP_S and rows[0]["tick"] == 12
    assert len(d.calls["notify"]) == 1 and "silent" in d.calls["notify"][0]


def test_a_beat_ten_minutes_old_or_younger_is_quiet(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    for age in (30, 600):
        _beat(d, age)
        assert cli.watchdog(book, d)["silent"] is False
    assert not _silent(cli, book) and not d.calls["notify"]


def test_a_new_silence_after_a_recovery_alerts_again(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    _beat(d, 1200, tick=3)
    cli.watchdog(book, d)
    _beat(d, 900, tick=9)                       # it beat again, then went quiet again
    cli.watchdog(book, d)
    assert [r["tick"] for r in _silent(cli, book)] == [3, 9] and len(d.calls["notify"]) == 2


def test_no_heartbeat_at_all_is_not_a_silence(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    assert cli.watchdog(book, d)["silent"] is False and not d.calls["notify"]


def test_the_watchdog_is_its_own_scheduled_task():
    cli = fx.load()
    cmd = cli.watchdog_command(Path("D:/r"), "2099", logon="Interactive", uv="C:/uv.exe")
    for word in ("visurena-autopilot-watchdog", "autopilot.py watchdog --book 2099", "PT5M", "AtLogOn",
                 "IgnoreNew", "Interactive", "Register-ScheduledTask", "C:/uv.exe"):
        assert word in cmd, word
    assert "-TaskName 'visurena-autopilot' " not in cmd, "the watchdog never re-registers the supervisor"


def test_install_registers_the_watchdog_beside_the_supervisor():
    cli, ran = fx.load(), []
    assert cli.install(Path("D:/r"), 5, "2099", run=lambda c: ran.append(c) or 0, which=lambda n: "C:/uv.exe") == 0
    assert len(ran) == 2 and "visurena-autopilot-watchdog" in ran[1] and "autopilot.py run" in ran[0]


def test_uninstall_removes_both_tasks():
    cmd = fx.load().uninstall_command()
    assert "'visurena-autopilot'" in cmd and "'visurena-autopilot-watchdog'" in cmd


def test_the_cli_has_a_watchdog_command():
    assert fx.load().parser().parse_args(["watchdog", "--book", "x"]).cmd == "watchdog"
