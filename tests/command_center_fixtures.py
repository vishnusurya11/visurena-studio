"""The board's fixtures: a tmp DB whose rows come from the real projection
(db.init_db + db.add_event), a tmp library with one book folder and the
artefact files the steps already write, and a tmp logs root.  Nothing here
runs a step, a model or a server."""
from __future__ import annotations

import json
from pathlib import Path

from studio import db, episode_home, plan_verdict
from studio.command_center import app as cc_app

CODEX = "20260901000001"
OTHER = "20260901000002"
RUN = f"{CODEX}__episode__20260926010203"


def make_library(tmp_path: Path, monkeypatch) -> Path:
    """A library with the book's folder, one episode's artefacts, a second book."""
    root = tmp_path / "library"
    home = root / f"{CODEX}_a-book" / "episodes" / "ep04"
    for rel in ("storyboard/shot_00.png", "storyboard/shot_01.png", "reports/strip_T00_T05.png",
                "cut/master_iter1.mp4", "cut/master_iter2.mp4", "plan.py"):
        (home / rel).parent.mkdir(parents=True, exist_ok=True)
        (home / rel).write_bytes(b"x" * 16)
    (home / "learnings.jsonl").write_text(
        "".join(json.dumps({"ts": f"2026-09-26T01:00:{i:02d}Z", "gate": "EYE_TAKES",
                            "action": "keep_best", "attempt": i}) + "\n" for i in range(10)),
        encoding="utf-8")
    (home / "timing.jsonl").write_text(
        json.dumps({"stage": "plan", "seconds": 31.0, "ok": True}) + "\n"
        + json.dumps({"stage": "qc", "seconds": 412.0, "ok": True}) + "\n", encoding="utf-8")
    (root / f"{CODEX}_a-book" / "episodes" / "ep03").mkdir(parents=True)
    (root / f"{CODEX}_a-book" / "episodes" / "ep03" / "youtube.json").write_text("{}", encoding="utf-8")
    (root / f"{OTHER}_other-book").mkdir()
    (root / f"{OTHER}_other-book" / "secret.png").write_bytes(b"other")
    monkeypatch.setattr(episode_home, "LIBRARY", root)
    return root


def make_logs(tmp_path: Path) -> Path:
    """A logs root with two runs of the book's episode stage; RUN's is the older."""
    folder = tmp_path / "logs" / CODEX / "episode"
    folder.mkdir(parents=True)
    lines = [{"ts": "2026-09-26T01:00:00Z", "level": "INFO", "msg": "quiet"},
             {"ts": "2026-09-26T01:00:01Z", "level": "WARNING", "msg": "MASTER: measured 3.0 -> recut"},
             {"ts": "2026-09-26T01:00:02Z", "level": "ERROR", "msg": "budget: flag (terminal)"}]
    (folder / f"{RUN}.log").write_text("".join(json.dumps(l) + "\n" for l in lines), encoding="utf-8")
    (folder / f"{CODEX}__episode__20260926090000.log").write_text(
        json.dumps({"ts": "2026-09-26T09:00:00Z", "level": "WARNING", "msg": "newer run"}) + "\n",
        encoding="utf-8")
    return tmp_path / "logs"


def _sign_plan(library: Path) -> None:
    plan = episode_home.write_json(library / f"{CODEX}_a-book" / "episodes" / "ep04" / "plan.json",
                                   {"number": 4})
    plan_verdict.sign(plan, "the plan holds", signed_by="judge:plan@1",
                      faults=[{"kind": "story", "where": "shot_03"}], flagged=True)


def seed(conn, library: Path) -> None:
    """Rows from events alone: ep04 running at 09 on the GPU with a signed plan,
    ep05 failed, ep07 deferred, ep03 done and flagged, ep06 queued, refs done."""
    _sign_plan(library)
    for step in ("01", "02"):
        db.add_event(conn, CODEX, "episode", step, "started", run_id=RUN, unit="ep04")
        db.add_event(conn, CODEX, "episode", step, "completed", run_id=RUN, unit="ep04")
    db.add_event(conn, CODEX, "episode", "09", "started", run_id=RUN, unit="ep04")
    db.upsert_work_order(conn, CODEX, "episode", "ep04", progress="18/25", gpu=1, sequence=4)
    db.add_event(conn, CODEX, "episode", "09", "started", run_id="r5", unit="ep05")
    db.add_event(conn, CODEX, "episode", "09", "failed", run_id="r5", unit="ep05", detail="KeyError")
    db.add_event(conn, CODEX, "episode", "02", "deferred", run_id="r7", unit="ep07")
    db.add_event(conn, CODEX, "episode", "12", "completed", run_id="r3", unit="ep03")
    db.upsert_work_order(conn, CODEX, "episode", "ep03", flags=2, sequence=3,
                         deliverable="episodes/ep03/manifest.json")
    db.upsert_work_order(conn, CODEX, "episode", "ep06", state="queued", sequence=6)
    db.add_event(conn, CODEX, "refs", "04", "completed", run_id="rr", unit="main")


def make_db(tmp_path: Path, library: Path) -> Path:
    """The seeded DB on disk; the app reopens it read-only per request."""
    path = tmp_path / "t.db"
    conn = db.get_connection(path)
    db.init_db(conn)
    db.insert_codex(conn, "A Book", codex_id=CODEX)
    db.insert_codex(conn, "Other Book", codex_id=OTHER)
    seed(conn, library)
    conn.close()
    return path


def make_app(tmp_path: Path, monkeypatch):
    """The board over the seeded tmp DB, tmp library and tmp logs."""
    library = make_library(tmp_path, monkeypatch)
    logs = make_logs(tmp_path)
    path = make_db(tmp_path, library)
    return cc_app.make_app(cc_app.readonly_factory(path), library, logs=logs)
