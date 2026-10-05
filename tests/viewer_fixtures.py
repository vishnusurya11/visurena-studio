"""A tmp book for the Viewer's tests: one finished episode (ep04: three shots, two
takes, a failed attempt, a still, a live and a superseded grid, two masters of
which the newest equals master_r2v) and one running episode (ep05: a plan and
panels, no take).  Derived from the shapes V03 read on the live library; never
the live library itself."""
from __future__ import annotations

import json
from pathlib import Path

CODEX = "20260901000001"
UNIT = "ep04"
RUN = f"{CODEX}__episode__20260926010203"


def put(path: Path, data) -> Path:
    """Write bytes, text or JSON (dict/list) to path, making its folders."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, (dict, list)):
        path.write_text(json.dumps(data), encoding="utf-8")
    elif isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_bytes(data)
    return path


PLAN = {"shots": [{"index": i, "setup": "woods", "size": "medium", "faces": ["captain"] if i == 2 else [],
                   "frame": f"Medium through the pine stems on shot {i}", "motion": "slow push in"}
                  for i in range(3)],
        "lines": []}
CARDS = [{"index": 0, "shots": [0, 1], "setup": "woods", "refs": [f"episodes/{UNIT}/storyboard/h3/shot_00.png"],
          "seed": 93000, "prompt": "detailed_description:\n<Picture 1> medium through the pine stems"},
         {"index": 2, "shots": [2], "setup": "woods", "refs": [], "seed": 93002, "prompt": "p"}]
QC = {"sha8": "abcd1234", "seconds": 20.0, "edit": {"segments": [
    {"take": 0, "shots": [0, 1], "start": 0, "n": 240}, {"take": 2, "shots": [2], "start": 240, "n": 120}]}}


def finished_episode(home: Path) -> None:
    """ep04's files: the plan, panels, grids, takes, verdicts and masters."""
    put(home / "plan.json", PLAN)
    put(home / "plan.verdict.json", {"faults": [{"kind": "story", "where": "shot_01"}]})
    put(home / "storyboard/layout.json", [{"setup": "woods", "cols": 3, "rows": 1, "shots": [0, 1, 2]}])
    for i in range(3):
        put(home / f"storyboard/shot_{i:02d}.png", b"png")
        put(home / f"storyboard/h3/shot_{i:02d}.png", b"png")
    for ext, body in ((".png", b"grid"), (".json", {"shots": [0, 1, 2], "seed": 7}), (".txt", "PANEL 1 (row 1)")):
        put(home / f"storyboard/grids/{UNIT}_grid_woods_3x1{ext}", body)
    put(home / f"storyboard/superseded/r1/{UNIT}_grid_woods_3x1.png", b"old")
    put(home / "storyboard/eye_aaaa1111.json", {"signed_at": "2026-09-25T07:00:00Z", "signed_by": "judge:panel_eye@1",
                                               "faults": [{"kind": "landmark", "where": "shot_00"}]})
    put(home / "takes/r2v/prompts.json", CARDS)
    put(home / "takes/r2v/shots.json", [dict(CARDS[0], measured_seconds=10.0)])
    put(home / "takes/r2v/stills.json", {"2": {"panel": f"episodes/{UNIT}/storyboard/shot_02.png", "why": "cut"}})
    put(home / "takes/r2v/eye_bbbb2222.json", {"signed_at": "2026-09-26T00:00:00Z", "faults": [{"kind": "lag", "where": "T02"}]})
    for rel in ("takes/r2v/T00.mp4", "takes/r2v/T02.mp4", "takes/r2v/attempts/T00_fail1.mp4", "takes/work/content/T00_1.png"):
        put(home / rel, b"media")
    put(home / "qc_r2v.json", QC)
    put(home / "cut/master_iter1.mp4", b"m" * 10)
    put(home / "cut/master_iter2.mp4", b"m" * 20)
    put(home / "cut/master_r2v.mp4", b"m" * 20)
    put(home / "learnings.jsonl", "".join(json.dumps({"attempt": i}) + "\n" for i in range(5)))
    put(home / "drive_run01.log", "".join(f"line {i}\n" for i in range(30)))
    put(home / "plan.py", "print('session leftover')")
    put(home / "__pycache__/x.pyc", b"pyc")


def running_episode(home: Path) -> None:
    """ep05: a plan and one panel, nothing rendered."""
    put(home / "plan.json", {"shots": [{"index": 0, "setup": "road", "size": "wide"}]})
    put(home / "storyboard/shot_00.png", b"png")


def make_book(tmp_path: Path) -> tuple[Path, Path]:
    """(library root, logs root) with the book, a big JSON, a foreign book and two run logs."""
    library = tmp_path / "library"
    book = library / f"{CODEX}_a-book"
    finished_episode(book / "episodes" / UNIT)
    running_episode(book / "episodes" / "ep05")
    put(book / "refs/pack.jsonl", "".join(json.dumps({"path": f"refs/p{i}.png", "seed": i}) + "\n" for i in range(50)))
    put(book / "episodes" / UNIT / "big.json", {"pad": "x" * (2 * 1024 * 1024 + 10)})
    put(library / "20260901000002_other/secret.json", {"secret": True})
    logs = tmp_path / "logs"
    put(logs / CODEX / "episode" / f"{RUN}.log",
        "".join(json.dumps({"level": "INFO", "msg": f"row {i}"}) + "\n" for i in range(1200)))
    put(logs / CODEX / "episode" / f"{CODEX}__episode__20260926090000.log", "x" * 5000 + "\n")
    return library, logs
