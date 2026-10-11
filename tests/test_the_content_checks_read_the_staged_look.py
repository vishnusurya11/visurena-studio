"""The panel and take content checks hand the bound row's LOOK markers to the
judge: a beard on a clean-shaven look fails, the panel's look mismatch rides
as an advisory (G-LOOK-PANEL) and the take's as a log (G-LOOK-TAKE), never a
fault (verdict 2026-10-10)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from studio import cast_refs, episode_home, panel_content as pc

from scripts.episode import panel_content_check as pcc, take_content_check as tcc

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "tests" / "fixtures" / "episodes" / "ep05_plan.json"
LOOK = {"headwear": "felt_hat", "hair_colour": "grey", "facial_hair": "none", "top": "shirt", "dirt": ""}


def book_of(tmp_path: Path):
    book = tmp_path / "book"
    (book / "episodes" / "ep05").mkdir(parents=True)
    shutil.copy(PLAN, book / "episodes" / "ep05" / "plan.json")
    (book / "refs").mkdir()
    (book / "refs" / "refs.json").write_text(json.dumps({"chapter": 5, "refs": [
        {"entity_id": "john_watson", "kind": "character", "markers": LOOK,
         "physical": "Man of 32 with a thin waxed moustache."}]}), encoding="utf-8")
    ep = episode_home.load_plan(book, 5)
    shot = ep.shot(9)
    return book, shot, ep.setups[shot.setup]


def test_the_rows_markers_reach_the_panel_judge(tmp_path):
    book, shot, setup = book_of(tmp_path)
    assert cast_refs.look_markers(book, list(shot.faces)) == [LOOK]
    got = pcc.judge(book, shot, setup, pc.Seen(people=1, subjects=["man", "moustache"]))
    assert "moustache on a clean-shaven look" in got


def test_a_panel_off_its_look_is_an_advisory_not_a_fault(tmp_path, monkeypatch):
    book, shot, setup = book_of(tmp_path)
    monkeypatch.setattr(pcc, "read", lambda path, seed=11: pc.Seen(people=1, subjects=["man", "straw hat"]))
    monkeypatch.setattr(pcc, "read_twins", lambda path, seed=17: pc.Twins(1, 1, []))
    row = pcc.row_for(book, shot, setup, Path("shot_09.png"))
    assert any("headwear" in n for n in row["look_advisory"])
    assert not any("headwear" in f for f in row["faults"])


def test_a_take_off_its_look_is_logged_not_failed(tmp_path):
    book, shot, setup = book_of(tmp_path)
    reads = [pc.Seen(people=1, subjects=["dark hair"]) for _ in range(3)]
    row = tcc.verdict_for(book, shot, setup, reads)
    assert row["look_log"] and any("dark hair" in f for f in row["faults"])
