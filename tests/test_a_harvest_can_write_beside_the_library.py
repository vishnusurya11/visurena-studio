"""The harvest can write its rows anywhere but the library (fleet H ruling A18, the --out half).

While the library is read-only (a fleet, a rehearsal), a re-harvest must not
touch library/<book>/casebook/: `--out <dir>` writes labels.jsonl into <dir>
and nowhere else.  Without it the harvest writes the book's casebook, as before.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.calibration import harvest_labels as hl  # noqa: E402
from studio import casebook, episode_home  # noqa: E402

CODEX = "20260901000001"


def book(tmp_path, monkeypatch):
    home = tmp_path / f"{CODEX}_book"
    room = home / "episodes" / "ep01" / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "T01.mp4").write_bytes(b"take")
    (room / "T01.dq.json").write_text(json.dumps({"take": 1, "file": "T01.mp4", "passed": True, "gates": []}),
                                      encoding="utf-8")
    monkeypatch.setattr(episode_home, "book_dir", lambda _id: home)
    monkeypatch.setattr(hl, "prose_sources", lambda b, root=hl.ROOT: [])
    return home


def test_out_writes_the_rows_there_and_leaves_the_book_alone(tmp_path, monkeypatch):
    home = book(tmp_path, monkeypatch)
    out = tmp_path / "fleet" / "H"
    assert hl.main([CODEX, "--out", str(out)]) == 0
    rows = casebook.read_rows(out / casebook.LABELS)
    assert [r.path for r in rows] == ["episodes/ep01/takes/r2v/T01.mp4"]
    assert not (home / "casebook").exists()


def test_without_out_the_book_casebook_is_written(tmp_path, monkeypatch):
    home = book(tmp_path, monkeypatch)
    assert hl.main([CODEX]) == 0
    assert (home / "casebook" / casebook.LABELS).is_file()
