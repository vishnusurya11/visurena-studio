"""Retro 2026-10-20 item 8 (ops #6): ep01 was upload-ready at 10-19 21:51 PDT and
still blocked on 10-20 by "Token has been expired or revoked": the consent
screen is in Testing, so a refresh token dies after 7 days, and .env's token was
written 10-07.  The wait was unbounded because nobody asked for the click until
the upload failed.

Now the token's age (the stamp youtube_auth writes beside it, else .env's mtime)
is read at launch and at render start; at 5 days or more, or when a refresh
fails, the owner gets the consent paste link while the episode renders.  The
link reuses a verifier already pending, so an owner mid-paste keeps his link.
No test here reaches Google: the refresh and the messenger are fakes."""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

from tests import autopilot_cli_fixtures as fx

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("youtube_auth_age", ROOT / "scripts/publish/youtube_auth.py")
auth = importlib.util.module_from_spec(_spec)
sys.modules["youtube_auth_age"] = auth
_spec.loader.exec_module(auth)

DAY = 86_400.0
NOW = 1_800_000_000.0


def _env(tmp_path, stamp: float | None = None) -> Path:
    env = tmp_path / ".env"
    lines = ["YOUTUBE_CLIENT_ID=id.apps.googleusercontent.com", "YOUTUBE_CLIENT_SECRET=s3cret",
             "YOUTUBE_REFRESH_TOKEN=1//fake"]
    if stamp is not None:
        lines.append(f"{auth.MINTED}={stamp}")
    env.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return env


def test_the_age_reads_the_stamp_beside_the_token(tmp_path):
    assert auth.token_age_days(_env(tmp_path, NOW - 6 * DAY), NOW) == 6.0


def test_without_a_stamp_the_age_is_the_env_files_mtime(tmp_path):
    env = _env(tmp_path)
    os.utime(env, (NOW - 13 * DAY, NOW - 13 * DAY))            # ep01: .env last written 10-07
    assert round(auth.token_age_days(env, NOW)) == 13


def test_storing_a_token_stamps_when(tmp_path):
    env = _env(tmp_path)
    auth.store_token(env, "1//new", now=NOW)
    text = env.read_text(encoding="utf-8")
    assert "YOUTUBE_REFRESH_TOKEN=1//new" in text and f"{auth.MINTED}={NOW}" in text


def test_an_old_token_sends_the_link_and_a_young_good_one_is_quiet(tmp_path):
    env = _env(tmp_path, NOW - 6 * DAY)
    note = auth.token_note(env, None, NOW, refresh=lambda e: None, link=lambda e, b: "https://consent.example/x")
    assert note and "6.0 days" in note and "https://consent.example/x" in note and "--paste=" in note
    young = _env(tmp_path, NOW - 1 * DAY)
    assert auth.token_note(young, None, NOW, refresh=lambda e: None, link=lambda e, b: "L") is None


def test_a_failing_refresh_sends_the_link_whatever_the_age(tmp_path):
    env = _env(tmp_path, NOW - 1 * DAY)
    note = auth.token_note(env, None, NOW, refresh=lambda e: "RefreshError: invalid_grant", link=lambda e, b: "L")
    assert note and "invalid_grant" in note and " L " in note


def test_the_link_reuses_the_verifier_already_pending(tmp_path, monkeypatch):
    pending = tmp_path / "library" / ".youtube_consent.json"
    pending.parent.mkdir(parents=True)
    verifier = "v" * 64
    pending.write_text(json.dumps({"verifier": verifier}), encoding="utf-8")
    monkeypatch.setattr(auth, "PENDING", pending)
    url = auth.pending_link(_env(tmp_path), None)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    assert f"code_challenge={challenge}" in url
    assert json.loads(pending.read_text(encoding="utf-8")) == {"verifier": verifier}, "the owner's link still works"


def test_with_nothing_pending_the_link_is_fresh_and_kept(tmp_path, monkeypatch):
    pending = tmp_path / "library" / ".youtube_consent.json"
    pending.parent.mkdir(parents=True)
    monkeypatch.setattr(auth, "PENDING", pending)
    url = auth.pending_link(_env(tmp_path), None)
    assert "code_challenge=" in url and json.loads(pending.read_text(encoding="utf-8"))["verifier"]


def _told(cli, book):
    return [r for r in cli.rows_of(book / "autopilot" / "events.jsonl") if r["event"] == "youtube_token_told"]


def test_the_launch_sends_the_note_once(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    d.token_note = lambda: "YouTube token 13.0 days old: open L"
    cli.launch(book, fx.CODEX, 1, d, "launch")
    assert d.calls["notify"] == ["ep01: YouTube token 13.0 days old: open L"]
    assert [r["at"] for r in _told(cli, book)] == ["launch"]


def test_a_good_token_sends_nothing_at_launch(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    d.token_note = lambda: None
    cli.launch(book, fx.CODEX, 1, d, "launch")
    assert not d.calls["notify"] and not _told(cli, book)


def test_render_start_sends_the_note_once_per_drive(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "RUNNING")
    d.token_note = lambda: "YouTube token 6.0 days old: open L"
    cli.launch(book, fx.CODEX, 1, d, "launch")
    home = book / "episodes" / "ep01"
    (home / "timing.jsonl").write_text(json.dumps({"stage": "step_09", "event": "started"}) + "\n", encoding="utf-8")
    cli.tick(book, fx.CODEX, d, 1)
    cli.tick(book, fx.CODEX, d, 2)
    assert [r["at"] for r in _told(cli, book)] == ["launch", "render"] and len(d.calls["notify"]) == 2
