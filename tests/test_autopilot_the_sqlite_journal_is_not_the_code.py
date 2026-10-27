"""Jekyll ep03 retro #8: SQLite's transient journal held a launch at WAIT_TREE and logged
code_dirty_during_run; it is not the code, even with .gitignore bypassed.  $0."""
from __future__ import annotations

from tests import autopilot_cli_fixtures as fx


def test_the_sqlite_journal_is_not_a_dirty_tree(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    journal = "?? db/visurena_studio.db-journal\n?? db/x.db-wal\n?? db/x.db-shm\n"
    assert cli.episode_drive_dirty(journal) is False
    assert cli.episode_drive_dirty(journal + " M studio/brain.py\n") is True
    d = fx.deps(tmp_path)
    d.git = lambda *a: journal if a[0] == "status" else "abc123def\n"
    assert cli.judge_verdict(book, fx.CODEX, 3, {"verdict": "retry"}, d)["state"] == "IDLE"
