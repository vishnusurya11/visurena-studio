"""Board review 2026-10-12 (03 A2, A24): a published episode's page links the video
itself ("Watch on YouTube" and its privacy), and a done unit's master QC line is
not drawn as a red failure ("✕ takes 17/22" read as "failed").  $0."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app
from studio import episode_home
from studio.youtube_publish import sha8

QC_SHORT = {"lufs": -14.0, "lufs_ok": True, "true_peak": -1.5, "tp_ok": True, "planned_cuts": [1], "missing_cuts": [],
            "lines": [{"passed": True}], "takes": {"pass": 17, "of": 22}}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    app = make_app(tmp_path, monkeypatch)
    home = tmp_path / "library" / f"{CODEX}_a-book" / "episodes" / "ep03"
    (home / "cut").mkdir(parents=True)
    (home / "cut" / "master_iter1.mp4").write_bytes(b"the uploaded cut")
    episode_home.write_json(home / "qc_r2v.json", {**QC_SHORT, "master": "episodes/ep03/cut/master_iter1.mp4",
                                                   "sha8": sha8(home / "cut" / "master_iter1.mp4")})
    return TestClient(app), home


def _upload(home, video="abc123"):
    row = {"episode": 3, "video_id": video, "sha8": sha8(home / "cut" / "master_iter1.mp4"), "privacy": "public"}
    (home.parents[1] / "uploads.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")


def test_a_published_unit_links_its_video(client):
    c, home = client
    _upload(home)
    html = c.get(f"/d/episode/{CODEX}/ep03").text
    assert 'href="https://youtu.be/abc123"' in html and "Watch on YouTube" in html and 'rel="noopener"' in html


def test_an_unpublished_unit_has_no_video_link(client):
    c, _ = client
    assert "youtu.be" not in c.get(f"/d/episode/{CODEX}/ep03").text


def test_a_done_units_qc_shortfall_is_not_red(client):
    c, home = client
    _upload(home)
    html = c.get(f"/d/episode/{CODEX}/ep03").text
    assert "q bad" not in html and "QC 4 of 5 checks passed" in html
