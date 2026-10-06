"""The Task Scheduler registration is a PURE string (ops engineer §2): the
settings the survival matrix rests on are asserted here, and `install` only
hands that string to PowerShell."""
from __future__ import annotations

import json
from pathlib import Path

from tests import autopilot_cli_fixtures as fx


def test_install_command_has_the_contract_settings():
    cli = fx.load()
    cmd = cli.install_command(Path("D:/somewhere/repo"), 5)
    for word in ("IgnoreNew", "PT0S", "AtStartup", "AtLogOn", "PT5M", "RestartCount 3",
                 "StartWhenAvailable", "WakeToRun", "S4U", "RunLevel Limited", "visurena-autopilot",
                 "scripts/episode/autopilot.py run", "Register-ScheduledTask"):
        assert word in cmd, word
    assert "D:/somewhere/repo" in cmd
    assert cli.install_command(Path("x"), 7).count("PT7M") == 1


def test_install_command_carries_the_book_when_given():
    cli = fx.load()
    assert "run --book 2099" in cli.install_command(Path("x"), 5, "2099")
    assert "--book" not in cli.install_command(Path("x"), 5)


def test_uninstall_command_names_the_task_and_never_prompts():
    cli = fx.load()
    cmd = cli.uninstall_command()
    assert "Unregister-ScheduledTask" in cmd and "visurena-autopilot" in cmd and "-Confirm:$false" in cmd


def test_main_hands_install_and_uninstall_to_powershell_only(monkeypatch, tmp_path):
    cli = fx.load()
    ran = []
    monkeypatch.setattr(cli, "powershell", lambda cmd: ran.append(cmd) or 0)
    assert cli.main(["install", "--every", "3", "--book", "2099"]) == 0
    assert cli.main(["uninstall"]) == 0
    assert "PT3M" in ran[0] and "Unregister" in ran[1]


def test_main_dispatches_the_owner_acts(monkeypatch, tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    monkeypatch.setattr(cli, "book_of", lambda codex: book)
    monkeypatch.setattr(cli, "default_deps", lambda: fx.deps(tmp_path, "IDLE"))
    assert cli.main(["park", "2", "--book", fx.CODEX, "--why", "owner says so"]) == 0
    assert cli.main(["retry", "2", "--book", fx.CODEX]) == 0
    assert cli.main(["pause", "--book", fx.CODEX]) == 0
    assert json.loads((book / "autopilot" / "series.json").read_text(encoding="utf-8"))["paused"] is True
    assert cli.main(["resume", "--book", fx.CODEX]) == 0
    assert cli.main(["tick", "--book", fx.CODEX]) == 0
    assert cli.main(["status", "--book", fx.CODEX]) == 0


def test_book_of_finds_the_folder_under_its_library(tmp_path, monkeypatch):
    cli, book = fx.load(), fx.book(tmp_path)
    monkeypatch.setattr(cli, "LIBRARY", tmp_path / "library")
    assert cli.book_of(fx.CODEX) == book
    assert cli.book_of(None) is None
    (book / "autopilot").mkdir()
    (book / "autopilot" / "series.json").write_text("{}", encoding="utf-8")
    assert cli.book_of(None) == book


def test_default_argv_is_the_uv_drive_line():
    cli = fx.load()
    assert cli.drive_argv("2099", 7) == ["uv", "run", "--no-sync", "python", "scripts/episode/drive.py", "2099", "7"]


def test_scrub_strips_the_repo_root_in_both_slash_styles():
    cli = fx.load()
    root = str(cli.ROOT)
    assert cli.scrub(f"at {root}\\studio\\x.py and {root.replace(chr(92), '/')}/y") == "at .\\studio\\x.py and ./y"


def test_series_is_created_from_the_chapters_once(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    series = cli.load_series(book, fx.CODEX, lambda b: [1, 2, 3])
    assert series == {"book": fx.CODEX, "first": 1, "last": 3, "paused": False}
    cli.set_paused(book, fx.CODEX, True)
    assert cli.load_series(book, fx.CODEX, lambda b: [1])["paused"] is True


def test_rows_of_skips_blank_and_broken_lines(tmp_path):
    cli = fx.load()
    path = tmp_path / "x.jsonl"
    assert cli.rows_of(path) == []
    path.write_text('{"a": 1}\n\nnot json\n{"b": 2}\n', encoding="utf-8")
    assert cli.rows_of(path) == [{"a": 1}, {"b": 2}]
