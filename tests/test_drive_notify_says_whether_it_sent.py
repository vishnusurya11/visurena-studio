"""Jekyll ep07 retro S3: `youtube_token_told` was written before a send whose outcome nobody read
(check=False, no return).  notify answers True only when the Telegram script exited 0."""
from __future__ import annotations

import subprocess
from types import SimpleNamespace

from scripts.episode import drive


def _run(code):
    return lambda *a, **k: SimpleNamespace(returncode=code)


def test_a_send_that_exits_zero_is_sent(monkeypatch):
    monkeypatch.delenv("DRIVE_QUIET", raising=False)
    monkeypatch.setattr(drive.subprocess, "run", _run(0))
    assert drive.notify("ep07 x") is True


def test_a_send_that_exits_non_zero_is_not_sent(monkeypatch):
    monkeypatch.delenv("DRIVE_QUIET", raising=False)
    monkeypatch.setattr(drive.subprocess, "run", _run(1))
    assert drive.notify("ep07 x") is False


def test_a_send_that_raises_is_not_sent(monkeypatch):
    monkeypatch.delenv("DRIVE_QUIET", raising=False)

    def boom(*a, **k):
        raise subprocess.TimeoutExpired("uv", 120)
    monkeypatch.setattr(drive.subprocess, "run", boom)
    assert drive.notify("ep07 x") is False


def test_a_quiet_run_sends_nothing(monkeypatch):
    monkeypatch.setenv("DRIVE_QUIET", "1")
    assert drive.notify("ep07 x") is False
