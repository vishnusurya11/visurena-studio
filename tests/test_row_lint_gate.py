"""G-ROWTEXT: the row lint runs where the data is WRITTEN, not only where it
is consumed.  `pack_refs.rows_for` refuses a dirty physical at bind time --
'revolver held at her lap' can never be filed again -- and the one-time
migration CLI cures what earlier chapters already filed, dry by default."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from studio import pack_refs, row_lint

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "migrate_row_words", ROOT / "scripts" / "episode" / "migrate_row_words.py")
mig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mig)


def test_row_faults_names_each_family_and_passes_a_clean_row():
    assert any("L2" in f for f in row_lint.row_faults("a revolver held at her lap"))
    assert any("L8" in f for f in row_lint.row_faults("she walks the yard"))
    assert any("L3" in f for f in row_lint.row_faults("a slow deliberate manner"))
    assert any("L1" in f for f in row_lint.row_faults("no hat, a bare head"))
    assert row_lint.row_faults("A lean man of thirty, dark hair, a service revolver "
                               "worn at the hip.") == []


def dossier(book: Path, who: str, physical: str) -> None:
    folder = book / "analysis" / "characters"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{who}.json").write_text(
        json.dumps({"name": who.title(), "profile": {"physical": physical}}), encoding="utf-8")


def test_rows_for_refuses_every_dirty_row_at_once(tmp_path):
    book = tmp_path / "book"
    dossier(book, "hall", "A revolver held at her lap.")
    dossier(book, "page", "He waits by the stair.")
    dossier(book, "finn", "A lean man of thirty.")
    with pytest.raises(SystemExit) as refused:
        pack_refs.rows_for(book, 3, ["hall", "page", "finn"], [])
    said = str(refused.value)
    assert "G-ROWTEXT" in said and "row hall" in said and "row page" in said
    assert "finn" not in said


def test_rows_for_files_a_clean_cast(tmp_path):
    book = tmp_path / "book"
    dossier(book, "finn", "A lean man of thirty.")
    rows = pack_refs.rows_for(book, 3, ["finn"], [])
    assert rows[0]["entity_id"] == "finn"


def world(tmp_path) -> Path:
    book = tmp_path / "book"
    (book / "refs").mkdir(parents=True)
    (book / "refs" / "refs.json").write_text(json.dumps(
        {"refs": [{"entity_id": "hall", "kind": "character",
                   "physical": "A revolver held at her lap."}]}, indent=1), encoding="utf-8")
    props = book / "analysis" / "props"
    props.mkdir(parents=True)
    (props / "revolver.json").write_text(json.dumps(
        {"name": "service revolver",
         "profile": {"physical": "She holds her fire.", "scale": "a hand-long revolver"}},
        indent=1), encoding="utf-8")
    return book


def test_the_migration_dry_run_leaves_every_file_byte_identical(tmp_path):
    book = world(tmp_path)
    before = {p: p.read_bytes() for p in (book / "refs" / "refs.json",
                                          book / "analysis" / "props" / "revolver.json")}
    fixes = mig.migrate(book, write=False)
    assert len(fixes) == 2
    for path, said in before.items():
        assert path.read_bytes() == said, path


def test_the_migration_write_cures_and_a_second_run_reports_nothing(tmp_path):
    book = world(tmp_path)
    assert len(mig.migrate(book, write=True)) == 2
    refs = json.loads((book / "refs" / "refs.json").read_text(encoding="utf-8"))
    assert refs["refs"][0]["physical"] == "A revolver resting at her lap."
    card = json.loads((book / "analysis" / "props" / "revolver.json").read_text(encoding="utf-8"))
    assert "holds her fire" not in card["profile"]["physical"]
    assert mig.migrate(book, write=True) == []
