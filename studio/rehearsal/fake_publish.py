"""YouTube, Telegram and the engine launch in a rehearsal (2026-10-21_ep02_proof 2.3).

YouTube (`youtube_upload.send`, `youtube_privacy._build_api`, `youtube_auth.refresh_fails` under
the REAL token_note, step 13's `urllib_get`) answers by the manifest's `youtube`:
  refuse         (default) every call raises PublishRefused: an upload in S0 fails it
  invalid_grant  the recorded ep19 RefreshError (2026-10-07 19:14Z) from the send, the API and the refresh
  permit         a would_upload / would_flip row and an answer in the API's shape; nothing leaves
Each call is a <sandbox>/youtube.jsonl row.  The defaults bound at def time (step 13's run and
poll_shorts, youtube_upload.main, token_note) are rebound with the module attributes.
drive.notify and the autopilot's Deps.notify are captured to <sandbox>/notify.jsonl (the
sibling notify_bench.py is refused at launch by the fence besides).  engine_ops.restart and
kill_engine reach fake_comfy.restart() (package P3), imported when first called."""
from __future__ import annotations

import importlib
import itertools
from pathlib import Path
from typing import Any, Callable, Mapping

from studio.rehearsal import fakes

INVALID_GRANT = ("invalid_grant: Token has been expired or revoked.", {"error": "invalid_grant"})
"""The RefreshError args step 13's upload died on (ep19; tests/test_an_expired_youtube_token_parks_with_the_mint_command)."""
MODES = ("refuse", "invalid_grant", "permit")


class PublishRefused(RuntimeError):
    """A YouTube call in a rehearsal that does not permit one."""


def mode(manifest: Mapping) -> str:
    got = str(manifest.get("youtube") or "refuse")
    if got not in MODES:
        raise ValueError(f"manifest youtube: {got!r} is none of {MODES}")
    return got


def refresh_error() -> Exception:
    """The recorded RefreshError (google-auth's own class when it is importable)."""
    try:
        from google.auth.exceptions import RefreshError
    except ImportError:
        return RuntimeError(f"RefreshError: {INVALID_GRANT}")
    return RefreshError(*INVALID_GRANT)


def gate(manifest: Mapping, box: Path, call: str) -> None:
    """Raise unless the rehearsal permits YouTube; the refusal is a row first."""
    how = mode(manifest)
    if how == "permit":
        return
    fakes.log(box, "youtube", {"event": "refused" if how == "refuse" else "invalid_grant", "call": call})
    if how == "invalid_grant":
        raise refresh_error()
    raise PublishRefused(f"youtube {call} refused in a rehearsal (an upload in S0 fails it)")


class FakeYouTube:
    """The videos() calls youtube_privacy makes, answered from what this rehearsal uploaded."""

    def __init__(self, box: Path, status: dict):
        self.box, self.status = box, status

    def videos(self) -> "FakeYouTube":
        return self

    def list(self, part: str = "", id: str = "") -> "_Done":
        found = self.status.get(id)
        return _Done({"items": [{"id": id, "status": dict(found)}] if found else []})

    def update(self, part: str = "", body: dict | None = None) -> "_Done":
        body = body or {}
        self.status[body.get("id", "")] = dict(body.get("status") or {})
        fakes.log(self.box, "youtube", {"event": "would_flip", "video_id": body.get("id"), "status": body.get("status")})
        return _Done({"id": body.get("id"), "status": dict(body.get("status") or {})})


class _Done:
    def __init__(self, answer: dict):
        self.answer = answer

    def execute(self) -> dict:
        return self.answer


# ---- the fakes of one install --------------------------------------------------------------

class Channel:
    """One rehearsal's YouTube: send, build_api, get and refresh, sharing the statuses it uploaded."""

    def __init__(self, manifest: Mapping, box: Path):
        self.manifest, self.box, self.status, self.serial = manifest, box, {}, itertools.count(1)

    def send(self, path, body: dict, creds) -> dict:
        gate(self.manifest, self.box, "send")
        video_id = f"rehearsal{next(self.serial):04d}"
        self.status[video_id] = dict((body or {}).get("status") or {})
        fakes.log(self.box, "youtube", {"event": "would_upload", "video_id": video_id, "path": str(path), "body": body})
        return {"id": video_id, "status": dict(self.status[video_id])}

    def build_api(self) -> FakeYouTube:
        gate(self.manifest, self.box, "build_api")
        return FakeYouTube(self.box, self.status)

    def get(self, url: str) -> tuple[int, str]:
        gate(self.manifest, self.box, "urllib_get")
        fakes.log(self.box, "youtube", {"event": "would_get", "url": url})
        return 200, url

    def refresh(self, env) -> str | None:
        """refresh_fails' answer: None (a good token) only when YouTube is permitted."""
        how = mode(self.manifest)
        if how == "permit":
            return None
        if how == "invalid_grant":
            return f"RefreshError: {str(refresh_error())[:160]}"
        return "RehearsalRefused: no YouTube token refresh in a rehearsal"


def youtube_fakes(manifest: Mapping, box: Path) -> dict[str, Callable]:
    """The bound methods, made once, so a module attribute and a default are the same object."""
    channel = Channel(manifest, box)
    return {"send": channel.send, "build_api": channel.build_api, "get": channel.get, "refresh": channel.refresh}


def captured(box: Path, source: str) -> Callable[[str], None]:
    """A notify that prints as drive's does and keeps the text in <sandbox>/notify.jsonl."""
    def notify(text: str) -> None:
        print(f"[{source}] {text}", flush=True)
        fakes.log(box, "notify", {"source": source, "text": text})
    return notify


def engine_call(box: Path, call: str, answer: Callable[[Any], Any]) -> Callable:
    """engine_ops.<call> -> fake_comfy.restart() (P3's module, imported at the first call)."""
    def fake(*_args, **_kwargs):
        fakes.log(box, "engine_ops", {"call": call})
        return answer(importlib.import_module("studio.rehearsal.fake_comfy").restart())
    return fake


def step_13(fns: Mapping[str, Callable]) -> Callable:
    def patch(mod) -> Callable[[], None]:
        undo = [fakes.set_attr(mod, "urllib_get", fns["get"]), fakes.set_default(mod.run, "send", fns["send"]),
                fakes.set_default(mod.run, "http", fns["get"]), fakes.set_default(mod.poll_shorts, "http", fns["get"])]
        return lambda: [u() for u in reversed(undo)]
    return patch


def install(manifest: Mapping, box: Path) -> None:
    mode(manifest)
    fns = youtube_fakes(manifest, box)
    fakes.rebind("scripts.publish.youtube_upload", "send", lambda _old: fns["send"])
    fakes.on_import("scripts.publish.youtube_upload", lambda m: fakes.set_default(m.main, "send", fns["send"]))
    fakes.rebind("scripts.publish.youtube_privacy", "_build_api", lambda _old: fns["build_api"])
    fakes.rebind("scripts.publish.youtube_auth", "refresh_fails", lambda _old: fns["refresh"])
    fakes.on_import("scripts.publish.youtube_auth", lambda m: fakes.set_default(m.token_note, "refresh", fns["refresh"]))
    fakes.on_import("scripts.episode.step_13_publish", step_13(fns))
    fakes.rebind("scripts.episode.drive", "notify", lambda _old: captured(box, "drive.notify"))
    deps = captured(box, "autopilot.Deps.notify")
    fakes.on_import("scripts.episode.autopilot", lambda m: fakes.set_default(m.Deps.__init__, "notify", deps))
    fakes.rebind("studio.engine_ops", "restart", lambda _old: engine_call(box, "restart", lambda up: up))
    fakes.rebind("studio.engine_ops", "kill_engine", lambda _old: engine_call(box, "kill_engine", lambda _up: []))
