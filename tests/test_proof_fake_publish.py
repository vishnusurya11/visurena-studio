"""YouTube, Telegram and the engine launch in a rehearsal (DESIGN 2.3; 2026-10-21_ep02_proof P4).

YouTube refuses by default (an upload in S0 fails it); `youtube: invalid_grant` raises the
recorded ep19 RefreshError through the REAL token_note; `youtube: permit` writes a would_upload
row and answers like the API.  Every call is a <sandbox>/youtube.jsonl row.  drive.notify and
the autopilot's Deps.notify are captured to <sandbox>/notify.jsonl.  engine_ops.restart and
kill_engine reach fake_comfy.restart().  $0: no Google, no Telegram, no process killed."""
from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path

import pytest

from scripts.episode import autopilot, drive, step_13_publish
from scripts.publish import youtube_auth, youtube_privacy, youtube_upload
from studio import engine_ops
from studio.rehearsal import fake_publish, fakes


@pytest.fixture
def box(tmp_path):
    yield tmp_path
    fakes.uninstall()


def rows(box: Path, name: str) -> list[dict]:
    path = box / f"{name}.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def test_an_upload_is_refused_by_default_and_logged(box):
    fakes.install({}, box)
    with pytest.raises(fake_publish.PublishRefused, match="upload"):
        youtube_upload.send(Path("m.mp4"), {"status": {"privacyStatus": "private"}}, None)
    assert rows(box, "youtube")[-1]["event"] == "refused" and rows(box, "youtube")[-1]["call"] == "send"


def test_the_defaults_bound_at_def_time_are_rebound_too(box):
    fakes.install({}, box)
    assert step_13_publish.run.__defaults__[0] is youtube_upload.send
    assert step_13_publish.run.__defaults__[2] is step_13_publish.urllib_get
    assert youtube_upload.main.__defaults__[0] is youtube_upload.send
    with pytest.raises(fake_publish.PublishRefused):
        step_13_publish.urllib_get("https://www.youtube.com/shorts/x")
    with pytest.raises(fake_publish.PublishRefused):
        youtube_privacy._build_api()
    fakes.uninstall()
    assert step_13_publish.run.__defaults__[0].__module__ == "scripts.publish.youtube_upload"


def test_a_permitted_upload_writes_a_would_upload_row_and_answers_like_the_api(box):
    fakes.install({"youtube": "permit"}, box)
    got = youtube_upload.send(Path("m.mp4"), {"status": {"privacyStatus": "private"}}, None)
    assert got["id"].startswith("rehearsal") and got["status"]["privacyStatus"] == "private"
    assert rows(box, "youtube")[-1]["event"] == "would_upload"
    api = youtube_privacy._build_api()
    assert youtube_privacy.live_status(api, got["id"])["privacyStatus"] == "private"
    assert youtube_privacy.set_privacy(api, got["id"], {"privacyStatus": "private"}, "public")["privacyStatus"] == "public"
    assert rows(box, "youtube")[-1]["event"] == "would_flip"


def test_invalid_grant_is_the_recorded_refresh_error_through_the_real_token_note(box):
    fakes.install({"youtube": "invalid_grant"}, box)
    env = box / ".env"
    env.write_text("", encoding="utf-8")
    note = youtube_auth.token_note(env, None, 0.0, link=lambda e, b: "LINK")
    assert "invalid_grant: Token has been expired or revoked." in note and "LINK" in note
    with pytest.raises(Exception, match="invalid_grant"):
        youtube_upload.send(Path("m.mp4"), {}, None)


def test_the_token_refresh_refuses_by_default(box):
    fakes.install({}, box)
    assert "rehearsal" in youtube_auth.refresh_fails(Path("x"))
    fakes.uninstall()
    fakes.install({"youtube": "permit"}, box)
    assert youtube_auth.refresh_fails(Path("x")) is None


def test_telegram_from_drive_and_from_the_autopilot_is_captured(box, monkeypatch):
    monkeypatch.setenv("DRIVE_QUIET", "0")
    fakes.install({}, box)
    drive.notify("ep02: parked")
    autopilot.Deps().notify("ep02: published")
    assert [(r["source"], r["text"]) for r in rows(box, "notify")] == [("drive.notify", "ep02: parked"),
                                                                     ("autopilot.Deps.notify", "ep02: published")]


def test_the_engine_restart_and_kill_reach_the_fake_comfy(box, monkeypatch):
    calls = []
    fake = types.ModuleType("studio.rehearsal.fake_comfy")
    fake.restart = lambda: calls.append("restart") or True
    monkeypatch.setitem(sys.modules, "studio.rehearsal.fake_comfy", fake)
    fakes.install({}, box)
    assert engine_ops.restart() is True
    assert engine_ops.kill_engine([types.SimpleNamespace(pid=999_999_999, cmdline="ComfyUI/main.py")]) == []
    assert calls == ["restart", "restart"]
    assert [r["call"] for r in rows(box, "engine_ops")] == ["restart", "kill_engine"]


def test_the_master_upscale_is_the_cpu_lanczos_path(box, monkeypatch):
    monkeypatch.delenv("VISURENA_MASTER_UPSCALE", raising=False)
    fakes.install({}, box)
    assert os.environ["VISURENA_MASTER_UPSCALE"] == "lanczos"
    fakes.uninstall()
    assert "VISURENA_MASTER_UPSCALE" not in os.environ
