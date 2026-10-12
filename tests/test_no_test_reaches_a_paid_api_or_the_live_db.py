"""2026-10-12 board review: 33 `stage='brain'` rows for the fake codex 20990101000000
sat in the LIVE usage table.  `test_run_brain_briefs_from_disk_and_maps_the_verdict`
faked the brain's turn but not `ledger_conn`, so `db.get_connection()` opened
db/visurena_studio.db from the repo root.  The session guard in conftest refuses,
for every test: a write-capable open of the live DB, a name lookup of any host
that is not this machine (OpenRouter, Anthropic, OpenAI, Higgsfield), and the
spawn of the `claude` CLI.  $0: nothing here leaves the process."""
from __future__ import annotations

import asyncio
import socket
import sqlite3

import pytest

from studio import db
from tests import guards
from tests.autopilot_cli_fixtures import load


def test_the_live_db_is_refused_by_its_default_path():
    with pytest.raises(guards.LiveDbRefused):
        db.get_connection()


def test_the_live_db_is_refused_by_any_spelling(tmp_path):
    with pytest.raises(guards.LiveDbRefused):
        sqlite3.connect(str(guards.LIVE_DB))
    with pytest.raises(guards.LiveDbRefused):
        sqlite3.connect(f"file:{guards.LIVE_DB.as_posix()}?mode=rwc", uri=True)
    sqlite3.connect(tmp_path / "scratch.db").close()


def test_a_read_only_open_of_the_live_db_is_allowed():
    assert guards.writes_live_db(f"file:{guards.LIVE_DB.as_posix()}?mode=ro", uri=True) is False
    assert guards.writes_live_db(":memory:") is False


def test_the_brain_ledger_cannot_reach_the_live_db():
    assert load().ledger_conn() is None


@pytest.mark.parametrize("host", ["openrouter.ai", "api.anthropic.com", "api.openai.com", "higgsfield.ai"])
def test_a_remote_host_is_refused(host):
    with pytest.raises(guards.PaidCallRefused, match=host):
        socket.getaddrinfo(host, 443)


def test_this_machine_still_resolves():
    assert socket.getaddrinfo("127.0.0.1", 8188)
    assert guards.is_local("localhost") and not guards.is_local("openrouter.ai")


def test_the_claude_cli_is_never_spawned():
    from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport
    with pytest.raises(guards.PaidCallRefused, match="claude CLI"):
        asyncio.run(SubprocessCLITransport.connect(object()))


def test_a_windows_file_uri_names_the_live_db():
    assert guards.writes_live_db(f"file:///{guards.LIVE_DB.as_posix()}", uri=True) is True
    assert guards.writes_live_db(guards.LIVE_DB.parent / "other.db") is False
