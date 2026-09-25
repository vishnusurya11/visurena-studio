"""scripts/audit/note.py: one finding of the owner's becomes one row on the
end of library/<book>/casebook/owner.jsonl, through studio.casebook.append_owner:
the closed class, the artefact's kind from its path, its sha8, weight 1."""
from __future__ import annotations

import pytest
from PIL import Image

from scripts.audit import note
from studio import casebook, episode_home

CODEX = "20260901000001"


@pytest.fixture()
def book(tmp_path, monkeypatch):
    home = tmp_path / "book"
    panel = home / "episodes" / "ep01" / "storyboard" / "shot_02.png"
    panel.parent.mkdir(parents=True)
    Image.new("RGB", (8, 8)).save(panel)
    monkeypatch.setattr(episode_home, "book_dir", lambda _id: home)
    return home


def test_a_note_appends_an_owner_row(book, capsys):
    assert note.main(["note.py", CODEX, "ep01", "episodes/ep01/storyboard/shot_02.png", "copies", "two of him"]) == 0
    rows = casebook.read_rows(book / "casebook" / casebook.OWNER)
    assert len(rows) == 1
    row = rows[0]
    assert row.codex == CODEX and row.unit == "ep01" and row.kind == "panel"
    assert row.verdict == "fault" and row.fault_class == "copies" and row.verdict_by == "owner"
    assert row.sha8 == casebook.sha8_of(book / "episodes" / "ep01" / "storyboard" / "shot_02.png")
    assert row.source.endswith(": two of him") and casebook.weight(row) == 1.0
    assert str(book / "casebook" / "owner.jsonl") in capsys.readouterr().out


def test_a_pass_note_is_a_pass_row_and_the_file_is_append_only(book):
    note.main(["note.py", CODEX, "ep01", "episodes/ep01/storyboard/shot_02.png", "copies", "two"])
    note.main(["note.py", CODEX, "ep01", "episodes/ep01/takes/r2v/T03.mp4", "pass", "fine"])
    rows = casebook.read_rows(book / "casebook" / casebook.OWNER)
    assert [(r.kind, r.verdict, r.fault_class) for r in rows] == [("panel", "fault", "copies"), ("take", "pass", None)]
    assert rows[1].sha8 == ""


def test_a_class_outside_the_closed_list_is_refused(book):
    with pytest.raises(SystemExit, match="not a fault class"):
        note.main(["note.py", CODEX, "ep01", "episodes/ep01/storyboard/shot_02.png", "ugly", "no"])
    with pytest.raises(SystemExit, match="say what was seen"):
        note.main(["note.py", CODEX, "ep01", "episodes/ep01/storyboard/shot_02.png", "copies", " "])


def test_the_kind_is_read_off_the_path():
    assert note.kind_of("episodes/ep01/storyboard/grids/ep01_grid_x_2x2.png") == "grid"
    assert note.kind_of("episodes/ep01/cut/master_r2v.mp4") == "master"
    assert note.kind_of("episodes/ep01/review/eye_abc12345.json") == "master"
    assert note.kind_of("refs/sheets/x.png") == "sheet"
    assert note.kind_of("episodes/ep01/plan.json") == "plan"
    with pytest.raises(SystemExit):
        note.kind_of("episodes/ep01/audio/lines/l01.wav")
