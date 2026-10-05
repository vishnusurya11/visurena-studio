"""The episode progress card's server side (progress tracker spec §3, §6):
`progress_view.progress()` over a tmp library, the `/api/progress` JSON twin,
and the `/thumb` route with its in-process LRU.  No network, no GPU; the
process table is injected."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from command_center_fixtures import CODEX, RUN, make_app, make_db, make_library, make_logs
from studio.command_center import app as cc_app, models, procs, progress_view, thumbs

FIX = Path(__file__).resolve().parent / "fixtures" / "progress"


def _drive(started: float) -> list[procs.ProcInfo]:
    return [procs.ProcInfo(41, started, f"python scripts/episode/drive.py {CODEX}_a-book 4")]


def _shoot(library: Path, n_takes: int = 3, landed: int = 1) -> Path:
    """ep04 mid-shoot: a drive log at step 09, take cards, panels, `landed` takes on disk."""
    home = library / f"{CODEX}_a-book" / "episodes" / "ep04"
    rows = json.loads((FIX / "ep16_shots.json").read_text(encoding="utf-8"))[:n_takes]
    (home / "takes" / "r2v").mkdir(parents=True, exist_ok=True)
    (home / "takes" / "r2v" / "prompts.json").write_text(json.dumps(rows), encoding="utf-8")
    (home / "storyboard" / "h3").mkdir(parents=True, exist_ok=True)
    for r in rows:
        Image.new("RGB", (64, 64), (90, 80, 70)).save(home / "storyboard" / "h3" / f"shot_{r['index']:02d}.png")
    lines = [f"=== EPISODE start | {CODEX} episode/ep04 | run {RUN} ===", "--- step 09 (shoot) | x ---",
             f"  queueing {n_takes} takes in one go: " + ", ".join(f"T{r['index']:02d}" for r in rows)]
    for r in rows[:landed]:
        (home / "takes" / "r2v" / f"T{r['index']:02d}.mp4").write_bytes(b"mp4")
        lines.append(f"  T{r['index']:02d} shots [{r['index']}] {r['frames']}f {r['seconds']:.2f}s in {r['render_s']:.0f}s")
    (home / "drive_run01.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return home


@pytest.fixture()
def board(tmp_path, monkeypatch):
    library = make_library(tmp_path, monkeypatch)
    logs = make_logs(tmp_path)
    path = make_db(tmp_path, library)
    home = _shoot(library)
    app = cc_app.make_app(cc_app.readonly_factory(path), library, logs=logs)
    return {"app": app, "library": library, "logs": logs, "db": path, "home": home}


def _progress(board, procs_rows=None, now=None):
    conn = board["app"].state.conn_factory()
    try:
        return progress_view.progress(board["library"], conn, CODEX, "ep04", now=now or time.time() + 5,
                                      logs=board["logs"], proc_rows=procs_rows if procs_rows is not None else [])
    finally:
        conn.close()


def test_progress_validates_and_counts_the_shoot(board):
    got = models.Progress.model_validate(_progress(board, _drive(time.time() - 3600)))
    assert got.now_step.id == "09" and got.now_step.kind == "counted"
    assert (got.now_step.done, got.now_step.total) == (1, 3)
    assert [i.state for i in got.items] == ["landed", "rendering", "waiting"]
    assert got.items[0].panel.startswith("storyboard/h3/shot_00.png?v=")
    assert got.items[0].video.startswith("takes/r2v/T00.mp4?v=")
    assert got.media_base == f"/thumb/{CODEX}/160/episodes/ep04/"


def test_a_live_drive_is_live_and_no_drive_is_dead(board):
    assert _progress(board, _drive(time.time() - 3600))["vital"] in ("live", "quiet")
    dead = _progress(board, [])
    assert dead["vital"] == "dead" and dead["vital_reason"] == "no drive process"


def test_the_eta_is_a_rounded_finish_with_a_basis(board):
    got = _progress(board, _drive(time.time() - 3600))
    assert got["eta"]["finish_at"] % 300 == 0 and got["eta"]["basis"] == "norm"
    assert ":" in got["eta"]["finish"] and "–" in got["eta"]["range"]


def test_the_title_names_the_step_the_count_and_the_unit(board):
    title = _progress(board, _drive(time.time() - 3600))["title"]
    assert title.startswith("● 09 shoot 1/3") and title.endswith("ep04")


def test_the_rail_has_every_step_and_the_running_one(board):
    steps = _progress(board, _drive(time.time() - 3600))["steps"]
    assert [s["id"] for s in steps] == [f"{i:02d}" for i in range(1, 13)]
    assert [s["id"] for s in steps if s["state"] == "running"] == ["09"]
    assert {s["state"] for s in steps if s["id"] in ("01", "02")} == {"done"}


def test_a_completed_episode_hands_over_to_the_master(board):
    home = board["home"]
    (home / "drive_run01.log").write_text(
        (home / "drive_run01.log").read_text(encoding="utf-8") + f"=== EPISODE completed | {CODEX} episode/ep04 ===\n",
        encoding="utf-8")
    (home / "cut").mkdir(exist_ok=True)
    (home / "cut" / "master_r2v.mp4").write_bytes(b"m")
    (home / "qc_r2v.json").write_text(json.dumps({"seconds": 170.2, "lufs": -14.2, "lufs_ok": True,
                                                  "true_peak": -1.8, "tp_ok": True}), encoding="utf-8")
    got = _progress(board, [])
    assert got["vital"] == "done" and got["master"] == f"/lib/{CODEX}/episodes/ep04/cut/master_r2v.mp4"
    assert got["qc"]["lufs_ok"] is True


def test_the_json_is_small_and_fast(board):
    _shoot(board["library"], n_takes=26, landed=11)
    _progress(board, [])                                     # warm the caches
    took = []
    for _ in range(5):
        t = time.perf_counter()
        body = _progress(board, [])
        took.append(time.perf_counter() - t)
    size = len(models.Progress.model_validate(body).model_dump_json(exclude_none=True))
    assert size < 6 * 1024, size
    assert sorted(took)[2] < 0.030, took


def test_the_route_answers_the_model(board):
    client = TestClient(board["app"])
    board["app"].state.procs = lambda: _drive(time.time() - 3600)
    r = client.get(f"/api/progress/episode/{CODEX}/ep04.json")
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"
    assert models.Progress.model_validate(r.json()).now_step.id == "09"


def test_the_route_404s_a_unit_without_a_row(board):
    assert TestClient(board["app"]).get(f"/api/progress/episode/{CODEX}/ep99.json").status_code == 404


# --- /thumb ---


def test_a_thumb_is_a_small_webp_cached_forever(board):
    client = TestClient(board["app"])
    r = client.get(f"/thumb/{CODEX}/160/episodes/ep04/storyboard/h3/shot_00.png?v=1")
    assert r.status_code == 200 and r.headers["content-type"] == "image/webp"
    assert r.headers["cache-control"] == "public,max-age=31536000,immutable"
    assert r.content[:4] == b"RIFF" and r.content[8:12] == b"WEBP"


def test_a_thumb_refuses_another_width_another_book_and_a_non_image(board):
    client = TestClient(board["app"])
    assert client.get(f"/thumb/{CODEX}/999/episodes/ep04/storyboard/h3/shot_00.png").status_code == 404
    assert client.get(f"/thumb/{CODEX}/160/episodes/%2E%2E/%2E%2E/%2E%2E/20260901000002_other-book/secret.png").status_code == 404
    assert client.get(f"/thumb/{CODEX}/160/episodes/ep04/learnings.jsonl").status_code == 404


def test_the_lru_key_changes_with_the_mtime(tmp_path):
    p = tmp_path / "a.png"
    Image.new("RGB", (8, 8)).save(p)
    k1 = thumbs.key("a.png", p, 160)
    os.utime(p, (1, 1))
    assert thumbs.key("a.png", p, 160) != k1


def test_the_lru_evicts_the_oldest_past_its_budget():
    lru = thumbs.Lru(cap_bytes=10)
    lru.put("a", b"12345")
    lru.put("b", b"12345")
    lru.get("a")
    lru.put("c", b"12345")
    assert lru.get("b") is None and lru.get("a") == b"12345" and lru.size <= 10


def test_webp_is_an_artefact_suffix():
    from studio.command_center import library_paths
    assert ".webp" in library_paths.SUFFIXES
