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


def make_writable_app(tmp_path: Path, monkeypatch):
    """(app, db path): the board with its write factory on the same tmp DB --
    reads stay `mode=ro`, the action routes write through the second factory."""
    library = make_library(tmp_path, monkeypatch)
    logs = make_logs(tmp_path)
    path = make_db(tmp_path, library)
    app = cc_app.make_app(cc_app.readonly_factory(path), library, logs=logs,
                          write_factory=cc_app.writable_factory(path))
    return app, path


# --- a looping unit (the unit page redesign, research F/G) ---

LOOP_RUN = f"{CODEX}__episode__20260926040000"
EYE = "episodes/ep08/storyboard/eye_aaaa1111.json"
FRAME_1 = "A medium close at dusk on the curate's face beside the hedge, the smoke low behind him."
BIG_NOTE = "; ".join(f"battery at plan:     G-SIZE shot {i % 25}: a close whose at_rest names no head"
                     f" fraction; the size is 'half the frame's height', not the span, measured none"
                     for i in range(300))


def _clock(monkeypatch, start: str = "2026-09-26T01:00:00+00:00") -> None:
    """db.utc_now advances ten minutes a call, so each run is its own window."""
    from datetime import datetime, timedelta
    t = [datetime.fromisoformat(start)]

    def tick():
        t[0] += timedelta(minutes=10)
        return t[0]
    monkeypatch.setattr(db, "utc_now", tick)


def _loop_files(library: Path) -> None:
    """ep08's plan (3 shots), its panels, the eye that faults them, dq, learnings."""
    home = library / f"{CODEX}_a-book" / "episodes" / "ep08"
    shots = [{"index": str(i), "section": "hook", "size": s, "frame": f, "motion": "The camera pushes in a hand's breadth.",
              "camera": "eye level, a 50mm lens"} for i, (s, f) in
             enumerate([("wide", "A wide of the common at dusk."), ("medium_close", FRAME_1), ("full", "A full of the road.")])]
    episode_home.write_json(home / "plan.json", {"number": 8, "title": "The Loop Chapter",
                                                 "question": "Will it ever leave the panels?", "shots": shots})
    for i in range(3):
        (home / "storyboard").mkdir(parents=True, exist_ok=True)
        (home / "storyboard" / f"shot_{i:02d}.png").write_bytes(b"png")
    faults = [{"kind": "missing", "where": "shot_00", "evidence": {"source": "panel_dq", "sharp": 0.5}, "note": ""},
              {"kind": "framing", "where": "shot_01", "note": "framing 'full': the shot asks for 'medium_close'"},
              {"kind": "framing", "where": "shot_01", "note": "framing 'full': the shot asks for 'medium_close'"},
              {"kind": "posture", "where": "shot_02", "note": "posture 'standing': the shot asks for lying"}]
    episode_home.write_json(home / "storyboard" / "eye_aaaa1111.json",
                            {"sha8": "aaaa1111", "verdict": "flagged", "signed_by": "judge:panel_eye@1",
                             "signed_at": "2026-09-26T01:55:00Z", "terminal": "keep_best", "faults": faults})
    episode_home.write_json(home / "storyboard" / "panel_dq.json",
                            [{"shot": 0, "flags": ["blur"], "passed": False}, {"shot": 1, "flags": [], "passed": True}])
    rows = [{"ts": f"2026-09-26T0{m}:15:00Z", "gate": "EYE_PANELS", "action": a, "measured": v, "terminal": a == "keep_best",
             "note": "framing at shot_01: framing 'full'"} for m, a, v in ((1, "redraw_grid_seed", 24.0),
                                                                            (2, "reprose", 20.0), (3, "keep_best", 17.0))]
    rows.append({"ts": "2026-09-26T03:20:00Z", "gate": "PLAN", "action": "improve", "measured": 61.0, "note": BIG_NOTE})
    (home / "learnings.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _loop_events(conn) -> None:
    """Three runs that end on 09 refused at the panels, then the live run in 08."""
    for n in range(3):
        rid = f"{CODEX}__episode__2026092601{n}000"
        db.add_event(conn, CODEX, "episode", "08", "started", run_id=rid, unit="ep08")
        db.add_event(conn, CODEX, "episode", "09", "started", run_id=rid, unit="ep08")
        db.add_event(conn, CODEX, "episode", "09", "failed", run_id=rid, unit="ep08",
                     detail="REFUSED: the takes wait on the panels: panels failed the panel gate: shots [0]")
    db.add_event(conn, CODEX, "episode", "08", "started", run_id=LOOP_RUN, unit="ep08")
    db.upsert_work_order(conn, CODEX, "episode", "ep08", sequence=8, lease_until="2099-01-01T00:00:00Z",
                         verdicts=json.dumps({"EYE_PANELS": {"by": "judge:panel_eye@1", "faults": 4, "path": EYE,
                                                             "sha8": "aaaa1111", "terminal": "keep_best",
                                                             "word": "flagged"}}))


def _loop_log(logs: Path) -> None:
    """The live run's log: a ladder line and a refusal body."""
    refusal = (Path(__file__).resolve().parent / "fixtures" / "unit_parse" / "refusal.txt").read_text(encoding="utf-8")
    rows = [{"ts": "2026-09-26T04:00:01Z", "level": "WARNING", "step_id": "ladders", "msg": "PLAN: measured 61.0 vs None -> improve"},
            {"ts": "2026-09-26T04:00:02Z", "level": "WARNING", "step_id": "02", "msg": refusal}]
    (logs / CODEX / "episode" / f"{LOOP_RUN}.log").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def make_looping_app(tmp_path: Path, monkeypatch):
    """The board with ep08 looping on the panel gate (4 runs, 3 refused at 09)."""
    library = make_library(tmp_path, monkeypatch)
    logs = make_logs(tmp_path)
    path = make_db(tmp_path, library)
    _loop_files(library)
    _loop_log(logs)
    _clock(monkeypatch)
    conn = db.get_connection(path)
    _loop_events(conn)
    conn.close()
    return cc_app.make_app(cc_app.readonly_factory(path), library, logs=logs)
