"""The session guards conftest installs for every test (board review 2026-10-12).

A test may not: open the live studio DB for writing, resolve a host that is not
this machine (every paid API -- OpenRouter, Anthropic, OpenAI, Higgsfield -- is
one), or spawn the `claude` CLI (the brain's subscription turns).  Each refusal
raises with a reason that names what was reached."""
from __future__ import annotations

import os
import re
import socket
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE_DB = ROOT / "db" / "visurena_studio.db"
LOCAL_HOSTS = {"", "localhost", "testserver", "::1", "0.0.0.0"}


class LiveDbRefused(RuntimeError):
    """A test opened db/visurena_studio.db for writing."""


class PaidCallRefused(RuntimeError):
    """A test reached the network beyond this machine, or the claude CLI."""


def _db_target(database, uri: bool) -> tuple[str, str]:
    """(file path, URI query) of what sqlite3.connect was asked to open."""
    text = os.fspath(database) if not isinstance(database, str) else database
    if not (uri and text.startswith("file:")):
        return text, ""
    path, _, query = text[len("file:"):].partition("?")
    return (path.lstrip("/") if re.match(r"/+[A-Za-z]:", path) else path), query


def writes_live_db(database, uri: bool = False) -> bool:
    """True when the open could write the live DB (a `mode=ro` URI cannot)."""
    path, query = _db_target(database, uri)
    if path in ("", ":memory:") or "mode=ro" in query or "mode=memory" in query:
        return False
    same = os.path.normcase(os.path.abspath(path)) == os.path.normcase(str(LIVE_DB))
    return same


def guarded_connect(real):
    """sqlite3.connect that refuses a write-capable open of the live DB."""
    def connect(database, *args, **kwargs):
        if writes_live_db(database, bool(kwargs.get("uri", False))):
            raise LiveDbRefused(f"a test opened the live DB {LIVE_DB} for writing")
        return real(database, *args, **kwargs)
    return connect


def is_local(host) -> bool:
    """This machine (or Starlette's TestClient), never a remote API."""
    name = (host.decode() if isinstance(host, bytes) else str(host or "")).strip("[]").lower()
    return name in LOCAL_HOSTS or name.startswith("127.")


def guarded_getaddrinfo(real):
    """socket.getaddrinfo that refuses any host but this machine."""
    def getaddrinfo(host, *args, **kwargs):
        if not is_local(host):
            raise PaidCallRefused(f"a test reached the network: {host}")
        return real(host, *args, **kwargs)
    return getaddrinfo


async def refuse_claude_cli(*_args, **_kwargs):
    raise PaidCallRefused("a test spawned the claude CLI (a brain turn on the owner's login)")


def install(monkeypatch) -> None:
    """All three guards, undone by monkeypatch at the end of the test."""
    from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport
    monkeypatch.setattr(sqlite3, "connect", guarded_connect(sqlite3.connect))
    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo(socket.getaddrinfo))
    monkeypatch.setattr(SubprocessCLITransport, "connect", refuse_claude_cli)
