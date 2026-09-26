"""Both doors to the channel ask the publish lock (root cause 2026-09-26, A1/C8).

ep12 went through `youtube_upload.py` and then `youtube_privacy.py public` with
four taste gates ended in terminals; neither door read them."""
from __future__ import annotations

import json

from scripts.publish import youtube_privacy, youtube_upload
from studio import episode_home, youtube_publish as yp
from studio.learnings import Learning, record


def unit(tmp_path, monkeypatch):
    book = tmp_path / "book"
    home = episode_home.home(book, 13)
    (home / "cut").mkdir(parents=True)
    master = home / "cut" / "master_r2v.mp4"
    master.write_bytes(b"cut")
    qc = home / "qc_r2v.json"
    qc.write_text(json.dumps({"passed": True}), encoding="utf-8")
    monkeypatch.setattr(yp, "deliverable", lambda h, e: ("r2v", master, qc))
    monkeypatch.setattr(youtube_upload, "failed_takes", lambda h, e="r2v": [])
    record(home / "learnings.jsonl", Learning(step="11", gate="MASTER", action="flag", terminal=True))
    return book, home, master


def test_the_privacy_flip_is_refused_by_an_open_terminal(tmp_path, monkeypatch):
    book, _home, master = unit(tmp_path, monkeypatch)
    stops = youtube_privacy.public_gates(book, 13, {"sha8": yp.sha8(master)})
    assert any(s.startswith("MASTER ended flag") for s in stops)
    assert any("director_signoff.md is missing" in s for s in stops)


def test_the_upload_lists_the_lock_stops(tmp_path, monkeypatch):
    _book, home, master = unit(tmp_path, monkeypatch)
    stops = youtube_upload.lock_stops(home, yp.sha8(master))
    assert any(s.startswith("MASTER ended flag") for s in stops)
