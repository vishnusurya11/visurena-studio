"""The first real `autopilot.py install` (2026-10-06) was refused by Windows
with 0x80070005: an S4U principal needs elevation this account does not have
from a shell.  The install tries S4U first and, refused, registers the same task
with an Interactive logon (the box is always logged on), saying which one it
got.  $0: the PowerShell runner is injected."""
from __future__ import annotations

from pathlib import Path

from tests import autopilot_cli_fixtures as fx


def test_install_command_takes_the_logon_type_and_fails_loudly():
    cli = fx.load()
    cmd = cli.install_command(Path("x"), 5)
    assert "LogonType S4U" in cmd and "AtStartup" in cmd
    assert "-ErrorAction Stop" in cmd and "exit 5" in cmd, "a refused registration must not exit 0"
    limited = cli.install_command(Path("x"), 5, logon="Interactive", startup=False)
    assert "LogonType Interactive" in limited and "AtStartup" not in limited and "AtLogOn" in limited


def test_install_retries_with_an_interactive_logon_when_s4u_is_refused():
    cli = fx.load()
    seen = []

    def run(cmd):
        seen.append(cmd)
        return 1 if "S4U" in cmd else 0

    assert cli.install(Path("x"), 5, None, run=run) == 0
    assert len(seen) == 2 and "LogonType Interactive" in seen[1] and "AtStartup" not in seen[1]


def test_install_names_uv_by_its_full_path():
    """The task's first start failed 0x80070002: Task Scheduler has no user PATH
    (2026-10-06), so the action carries uv.exe resolved at install time."""
    cli = fx.load()
    cmd = cli.install_command(Path("x"), 5, uv="C:/Users/me/.local/bin/uv.exe")
    assert "-Execute 'C:/Users/me/.local/bin/uv.exe'" in cmd
    seen = []
    cli.install(Path("x"), 5, None, run=lambda c: seen.append(c) or 0, which=lambda name: "D:/tools/uv.exe")
    assert "-Execute 'D:/tools/uv.exe'" in seen[0]


def test_install_stops_at_s4u_when_it_is_accepted():
    cli = fx.load()
    seen = []
    assert cli.install(Path("x"), 5, "2099", run=lambda cmd: seen.append(cmd) or 0) == 0
    assert len(seen) == 1 and "S4U" in seen[0]
