"""ep27 (2026-10-10 19:25Z): step 05 died on `sqlite3.OperationalError: database
is locked` -- another process held the studio database for a moment -- and the
table, knowing no row for it, handed it to the brain.  A lock is transient: retry."""
from __future__ import annotations

from studio import autopilot


def test_a_locked_database_is_retried():
    tail = ("Traceback (most recent call last):\nsqlite3.OperationalError: database is locked\n"
            "During handling of the above exception, another exception occurred:\n"
            "sqlite3.OperationalError: database is locked\n")
    assert autopilot.classify(tail, set())[:2] == ("retry", "db_locked")
