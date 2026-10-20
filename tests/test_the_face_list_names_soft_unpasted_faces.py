"""The face list at the first master (retro 2026-10-20 item 2, package C; owner veto list V3 not vetoed).

For every take: the smallest tracked face (render px, which is cut scale: the paste is made on the
768 cut before the one upscale) and whether a paste was accepted.  A take with a face under
fr.LIST_PX (= SMALL_FACE_PX, 120) and no accepted paste is LISTED: written to refine.json for step 11
QC, routed to the refine, never a wall on the master (log only until the owner labels faces).  The
refine's own tracker decides wherever it decided on these bytes; the warp gate's tracks elsewhere.

Records (copies, tests/fixtures/): ep01's dq warp tracks as HEAD measured the delivered takes
(ep01_face_list/dq_tracks.json), the iter1-era refine.json (ep01_replay/P07/refine.json: the 60 px
wall, only T08 and T18 pasted), the iter3 refine.json (ep01_face_list/refine_iter3.json), the cards
(ep01_replay/face_blur/cards.json) and the repair's refine timing row (ep01_face_list/repair_refine_row.json:
the 12 takes the repair refined).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

from scripts.episode import face_refine as cli
from scripts.episode import step_09_shoot as step
from studio import face_refine as fr

FIX = Path(__file__).parent / "fixtures"


def load(rel: str):
    return json.loads((FIX / rel).read_text(encoding="utf-8"))


DQS = {int(k[1:]): v for k, v in load("ep01_face_list/dq_tracks.json")["takes"].items()}
SHAS = {i: d["take_sha8"] for i, d in DQS.items()}
CARDS = load("ep01_replay/face_blur/cards.json")
SIZES = {int(c["index"]): c["sizes"][0] for c in CARDS}
REPAIRED = {int(t) for t in load("ep01_face_list/repair_refine_row.json")["note"].split()}


def listing(doc: dict, owed=frozenset()) -> dict:
    return fr.face_list(fr.face_rows(CARDS, SIZES, DQS, doc, SHAS, owed))


def listed(doc: dict) -> set[int]:
    return {int(t[1:]) for t in listing(doc)["listed"]}


def test_the_list_constant_is_the_refines_own_eligibility_constant():
    assert fr.LIST_PX == fr.SMALL_FACE_PX == 120.0


def test_the_repair_refined_twelve_takes():
    assert REPAIRED == {0, 1, 5, 6, 9, 10, 13, 15, 19, 21, 23, 26}


def test_at_the_first_master_the_list_names_every_take_the_repair_found_soft():
    """iter1's refine pasted T08 and T18 only.  The list names 10 of the repair's 12: T00 (166 px) and
    T19 (120.3 px) are over 120 by the warp tracks, and the repair's own tracker read both all_readable."""
    first = listed(load("ep01_replay/P07/refine.json"))
    assert first & REPAIRED == REPAIRED - {0, 19}
    assert {8, 18}.isdisjoint(first), "pasted at iter1"


def test_an_insert_or_a_take_with_no_planned_face_is_never_listed():
    """The refine never reaches them (fr.NEVER, no cast): ep01 T07 / T12 / T17 are inserts, T27 has no face."""
    first = listed(load("ep01_replay/P07/refine.json"))
    assert {7, 12, 17, 27}.isdisjoint(first)


def test_at_iter3_only_the_refused_pastes_are_listed():
    """Every take whose soft faces were all pasted drops off; T01 (both refused), T08 (the child, turned),
    T09 (Hyde, turned) and T26 (Enfield, turned; Utterson pasted) stay listed, as the master shipped."""
    assert listed(load("ep01_face_list/refine_iter3.json")) == {1, 8, 9, 26}


def test_a_row_says_its_smallest_face_and_whether_a_paste_was_accepted():
    row = listing(load("ep01_face_list/refine_iter3.json"))["takes"]["T26"]
    assert row["smallest_px"] == 61.7 and row["pasted"] is True and row["by"] == "refine"
    assert row["unpasted"] == [{"who": "richard_enfield", "px": 61.7}]


def test_a_take_the_refine_did_not_decide_reads_the_warp_tracks():
    row = listing(load("ep01_face_list/refine_iter3.json"))["takes"]["T02"]
    assert row["by"] == "warp" and row["smallest_px"] == 211.2 and not row["unpasted"]


def test_a_cut_or_owed_take_is_routed_to_the_refine_and_a_refused_one_is_logged():
    doc = load("ep01_face_list/refine_iter3.json")
    doc["T05"] = {"status": "cut", "take_sha8": SHAS[5], "people": []}
    rows = listing(doc, owed=frozenset({5}))["takes"]
    assert rows["T05"]["status"] == "cut" and rows["T05"]["route"] == "refine"
    assert rows["T01"]["route"] == "logged"


def test_the_list_never_fails_anything():
    """No verdict, no wall: the doc holds rows and names, nothing a gate reads as a fail."""
    doc = listing(load("ep01_face_list/refine_iter3.json"))
    assert set(doc) == {"px", "listed", "takes", "note"} and "never" in doc["note"]


# ---- refine.json and step 09 -------------------------------------------------------------------

def test_the_list_is_written_into_refine_json_once(tmp_path):
    """refine.json is an input of step 10: an unchanged list is not written again (no needless recut)."""
    (tmp_path / cli.DOC).write_text(json.dumps({"T01": {"status": "unrefined"}}), encoding="utf-8")
    face = listing(load("ep01_face_list/refine_iter3.json"))
    assert cli.write_face_list(tmp_path, face)
    os.utime(tmp_path / cli.DOC, (1, 1))
    assert not cli.write_face_list(tmp_path, face) and (tmp_path / cli.DOC).stat().st_mtime == 1
    doc = json.loads((tmp_path / cli.DOC).read_text(encoding="utf-8"))
    assert doc["T01"] == {"status": "unrefined"} and doc[cli.FACE_LIST]["listed"] == ["T01", "T08", "T09", "T26"]


def test_step_11_reads_the_listed_faces_as_one_line(tmp_path):
    cli.write_face_list(tmp_path, listing(load("ep01_face_list/refine_iter3.json")))
    line = cli.face_list_line(cli.read_face_list(tmp_path))
    assert line.startswith("FACE LIST") and "T01" in line and "T26 61.7 px" in line and "log only" in line
    assert cli.face_list_line(cli.read_face_list(tmp_path / "nowhere")) == ""


def test_step_09_writes_and_logs_the_list_and_never_raises(tmp_path, monkeypatch):
    face = listing(load("ep01_face_list/refine_iter3.json"))
    monkeypatch.setattr(cli, "face_list", lambda book, n: face)
    logged = []
    ctx = SimpleNamespace(home=tmp_path / "home", book_dir=tmp_path, number=1,
                          log=lambda msg, **k: logged.append((msg, k.get("level"))), learn=lambda row: None)
    (ctx.home / step.TAKES).mkdir(parents=True)
    step.face_list_note(ctx)
    assert json.loads((ctx.home / step.TAKES / cli.DOC).read_text(encoding="utf-8"))[cli.FACE_LIST] == face
    assert any(msg.startswith("FACE LIST") and level == "WARNING" for msg, level in logged)


def test_step_09_writes_the_list_after_the_tiny_face_rung(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(step, "panel_refusals", lambda home: [])
    monkeypatch.setattr(step, "approved", lambda policy: "--approved=render")
    monkeypatch.setattr(step.gate_policy, "of", lambda stage, row: None)
    monkeypatch.setattr(step, "affordable", lambda ctx: (True, 0.0, 0.0))
    monkeypatch.setattr(step, "takes_of", lambda room: [room / "T01.mp4"])
    for name in ("say_reserve", "shoot", "say_first_wall", "gpu_window", "judge_takes", "inputs_wall",
                 "refine_rest", "tiny_face_rung", "face_list_note"):
        monkeypatch.setattr(step, name, lambda *a, n=name: calls.append(n))
    ctx = SimpleNamespace(home=tmp_path, book_dir=tmp_path, number=1, stage="episode", log=lambda *a, **k: None,
                          run_script=lambda *a, **k: 0)
    step.run(ctx)
    assert calls[-2:] == ["tiny_face_rung", "face_list_note"]
