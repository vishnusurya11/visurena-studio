"""G-LINEAGE, advisory (C2_verdict #9).

A same-man redraw on one cast row was a different man twice in Scarlet:
Brigham Young ep08 against ep10 scores a head cosine of 0.16-0.24 (near the
cross-person median) and Jefferson Hope ep07 against ep09-14 0.45.  Same-man
versions score 0.80-0.96; a separate `_young` row redrawn from a shared
description holds about 0.6.  On every new sheet version of a row the head
crop is scored against every earlier staged version; a pair under 0.60 writes
an audit line -- never a refusal: the line is calibrated on Scarlet's
photoreal sheets only."""
from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np

from studio import lineage


def test_a_full_body_sheet_is_cut_to_its_head_and_scaled():
    tall = np.zeros((1536, 1024, 3), np.uint8)
    assert lineage.head_crop(tall).shape[:2] == (int(1536 * 0.35), 1024)      # the top 35 %, 1024 wide
    bust = np.zeros((512, 512, 3), np.uint8)
    assert lineage.head_crop(bust).shape[:2] == (1024, 1024)


def test_the_staged_versions_are_the_rows_own_hashed_names(tmp_path):
    for name in ["char-jefferson_hope_indoor_8826eb07.png", "char-jefferson_hope_outdoor_102857b4.png",
                 "char-jefferson_hope_dd298c29.png", "char-jefferson_hope_cabman_outdoor_0c68eeba.png",
                 "char-jefferson_hope_indoor.png", "char-enoch_drebber_young_indoor_44af0653.png"]:
        (tmp_path / name).write_bytes(b"x")
    got = sorted(p.name for p in lineage.versions(tmp_path, "jefferson_hope"))
    assert got == ["char-jefferson_hope_dd298c29.png", "char-jefferson_hope_indoor_8826eb07.png",
                   "char-jefferson_hope_outdoor_102857b4.png"]
    assert [p.name for p in lineage.versions(tmp_path, "enoch_drebber")] == []


def test_a_pair_under_the_line_is_an_advisory_and_an_age_up_is_only_noted():
    scores = {"char-x_old_11111111.png": 0.24, "char-x_aaaaaaaa.png": 0.91}
    lines = lineage.advisories("brigham_young", "char-x_new_22222222.png", scores, age_up=False)
    assert len(lines) == 1 and "0.24" in lines[0] and "different man" in lines[0]
    noted = lineage.advisories("john_ferrier", "char-x_new_22222222.png", {"char-x_11111111.png": 0.56}, age_up=True)
    assert len(noted) == 1 and "age-up" in noted[0]


def test_a_young_row_or_a_declared_age_up_is_an_age_up():
    assert lineage.age_up("enoch_drebber_young", {"name": "Enoch Drebber, young"})
    assert lineage.age_up("lucy_ferrier_child", {"name": "Little Lucy Ferrier"})
    assert lineage.age_up("john_ferrier", {"name": "John Ferrier", "age_up": True})
    assert not lineage.age_up("brigham_young", {"name": "Brigham Young"})       # a surname, not a marker
    assert not lineage.age_up("jefferson_hope", {"name": "Jefferson Hope"})


def test_check_writes_the_audit_line_and_never_refuses(tmp_path):
    vectors = {"new.png": np.array([1.0, 0.0]), "old.png": np.array([0.2, 1.0])}
    embed = SimpleNamespace(vector=lambda path: vectors[path.name])
    (tmp_path / "audit").mkdir()
    lines = lineage.check(tmp_path, "brigham_young", tmp_path / "new.png", [tmp_path / "old.png"],
                          {"name": "Brigham Young"}, embed.vector)
    assert lines and "different man" in lines[0]
    rows = [json.loads(l) for l in (tmp_path / "audit" / "lineage.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[0]["who"] == "brigham_young" and rows[0]["cos"] < lineage.MATCH and rows[0]["advisory"] is True


def test_an_unreadable_head_is_skipped_not_refused(tmp_path):
    lines = lineage.check(tmp_path, "x", tmp_path / "new.png", [tmp_path / "old.png"], {}, lambda path: None)
    assert lines == []


def test_the_refs_sheets_step_scores_a_new_character_sheet_against_its_staged_versions(tmp_path, monkeypatch):
    """refs 02 (sheets): every newly drawn character sheet is read against its row's
    earlier staged versions; a line under MATCH is a WARNING in the run log only."""
    from PIL import Image
    from scripts.refs import step_02_sheets as sheets
    from studio import comfy
    from studio.refs_pack import Job
    book, staged = tmp_path / "book", tmp_path / "input"
    (book / "refs" / "characters" / "brigham_young").mkdir(parents=True)
    staged.mkdir()
    Image.new("RGB", (8, 8)).save(book / "refs" / "characters" / "brigham_young" / "sheet.png")
    Image.new("RGB", (8, 8), "white").save(staged / "char-brigham_young_c9192677.png")
    (book / "refs" / "refs.json").write_text(json.dumps({"refs": [{"entity_id": "brigham_young", "kind": "character",
                                                                   "name": "Brigham Young"}]}), encoding="utf-8")
    monkeypatch.setattr(comfy, "COMFY_ROOT", tmp_path)
    said = []
    ctx = SimpleNamespace(book_dir=book, log=lambda line, **kw: said.append((line, kw.get("level"))))
    vectors = lambda path: np.array([1.0, 0.0]) if path.name == "sheet.png" else np.array([0.2, 1.0])  # noqa: E731
    job = Job("characters", "brigham_young", "sheet", "t2i", "A man. Sheet.", 1536, 1024)
    lines = sheets.lineage(ctx, [job], vector=vectors)
    assert lines and "different man" in lines[0] and said[0][1] == "WARNING"
