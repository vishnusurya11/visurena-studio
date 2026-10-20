"""The face contact strip at QC (retro 2026-10-20 item 4, package D; owner veto list V3 not vetoed).

Step 11 cuts 4 face crops per face-size tier out of the master (CPU: ffmpeg and the detector), lays
them in one strip, and keeps a labels file the owner fills in 2-3 min (good / bad per crop).  The
tiers are cut-scale px, the face list's own scale; 120 is the refine's LIST_PX.  A listed take (a
soft face no paste covered) is shown first in its tier.  Nothing here is a wall.

Records (copies, tests/fixtures/): ep01's delivered timeline and take records
(ep01_face_strip/cut.json), and the face list as C's fixtures give it at the first master
(ep01_replay/P07/refine.json: only T08 and T18 pasted) and at iter3 (ep01_face_list/refine_iter3.json),
with the repair's 12 refined takes (ep01_face_list/repair_refine_row.json).  Frames and the detector
are fakes, $0.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image

from scripts.episode import step_11_qc as s11
from studio import face_refine as fr
from studio import face_strip as fs

FIX = Path(__file__).parent / "fixtures"


def load(rel: str):
    return json.loads((FIX / rel).read_text(encoding="utf-8"))


CUT = load("ep01_face_strip/cut.json")
PLACED, RECORDS = CUT["placed"], CUT["records"]
DQS = {int(k[1:]): v for k, v in load("ep01_face_list/dq_tracks.json")["takes"].items()}
SHAS = {i: d["take_sha8"] for i, d in DQS.items()}
CARDS = load("ep01_replay/face_blur/cards.json")
SIZES = {int(c["index"]): c["sizes"][0] for c in CARDS}
REPAIRED = {int(t) for t in load("ep01_face_list/repair_refine_row.json")["note"].split()}
SIDE = 96
"""The fake master's side: a 768 cut shown at 96 px, so one master px is 8 cut px."""


def face_list(rel: str) -> dict:
    return fr.face_list(fr.face_rows(CARDS, SIZES, DQS, load(rel), SHAS))


FIRST, ITER3 = face_list("ep01_replay/P07/refine.json"), face_list("ep01_face_list/refine_iter3.json")


def frames(master, times):
    return [np.full((SIDE, SIDE, 3), 40 + (int(t * 7) % 200), np.uint8) for t in times]


def no_faces(frame):
    return []


def one_face(frame):
    return [[40.0, 30.0, 52.0, 42.0], [10.0, 10.0, 40.0, 40.0]]


def build(tmp_path, face, detect=no_faces, sha8="abcd1234"):
    return fs.build(tmp_path, tmp_path / "m.mp4", sha8, face, PLACED, RECORDS, frames, detect)


def tier_takes(rows, tier):
    return [r["index"] for r in rows if r["tier"] == tier]


def test_the_tiers_meet_at_the_refines_list_constant():
    assert [fs.tier_of(px) for px in (10.7, 59.9, 60.0, 119.9, 120.0, 239.9, 240.0)] == \
        ["tiny", "tiny", "small", "small", "medium", "medium", "large"]
    assert fs.tier_of(None) is None and fs.TIERS[1][2] == fr.LIST_PX


def test_each_take_is_shown_at_the_middle_of_its_window_in_the_master():
    times = fs.take_times(PLACED, RECORDS)
    assert times[0] == round(4.166667 / 2, 3) and len(times) == 28
    assert all(0 < t < PLACED["duration_s"] for t in times.values())


def test_at_the_first_master_the_two_small_rows_are_the_faces_the_repair_refined(tmp_path):
    """iter1: the tiny and small rows hold 8 takes, every one listed and later refined by the repair."""
    rows = build(tmp_path, FIRST)
    assert tier_takes(rows, "tiny") == [1, 6, 13, 26]
    assert tier_takes(rows, "small") == [9, 10, 15, 5]
    assert set(tier_takes(rows, "tiny") + tier_takes(rows, "small")) <= REPAIRED
    assert all(len(tier_takes(rows, t)) <= fs.PER_TIER for t, _lo, _hi in fs.TIERS)


def test_a_listed_take_with_no_measure_still_reaches_the_strip(tmp_path):
    """iter3 lists T08 with no measured face; with no detection it gets its own row, never dropped."""
    rows = build(tmp_path, ITER3)
    assert 8 in tier_takes(rows, fs.UNMEASURED)
    assert {1, 9, 26} <= {r["index"] for r in rows if r["listed"]}


def test_a_face_the_list_never_measured_is_tiered_by_the_master_detector(tmp_path):
    """The smallest detected box, in cut px: 12 master px x 768/96 = 96 cut px, the small tier."""
    rows = build(tmp_path, ITER3, detect=one_face)
    t08 = next(r for r in rows if r["index"] == 8)
    assert t08["tier"] == "small" and t08["px"] == 96.0 and t08["master_px"] == 12.0
    assert t08["shown_px"] == 96.0


def test_the_crop_is_never_shrunk_below_the_face_it_shows():
    """ep01 replay 2026-10-20: a 192 cell shrank a 300 px master face 3x and hid the blur it was
    made to show.  The cell is CELL wide and the crop only MARGIN around the face, so a face under
    CELL / (1 + 2 MARGIN) master px is shown larger than it is, never smaller."""
    frame = np.zeros((3072, 3072, 3), np.uint8)
    assert fs.crop(frame, [1000.0, 1000.0, 1250.0, 1250.0]).size == (fs.CELL, fs.CELL)
    assert 250 * (1 + 2 * fs.MARGIN) <= fs.CELL


def test_the_crops_the_strip_and_a_blank_labels_file_are_written(tmp_path):
    rows = build(tmp_path, FIRST, detect=one_face)
    for row in rows:
        assert Image.open(tmp_path / "review" / row["crop"]).size == (fs.CELL, fs.CELL)
    strip = Image.open(tmp_path / "review" / "faces_abcd1234.png")
    assert strip.size[0] == fs.CELL * fs.PER_TIER
    doc = fs.write_labels(tmp_path, "abcd1234", rows)
    labels = json.loads(doc.read_text(encoding="utf-8"))
    assert labels["strip"] == "faces_abcd1234.png" and len(labels["crops"]) == len(rows)
    assert all(c["owner"] == "" for c in labels["crops"]) and "good" in labels["how"]


def test_no_face_found_shows_the_whole_frame(tmp_path):
    rows = build(tmp_path, FIRST)
    assert all(r["kind"] == "frame" and r["box"] is None for r in rows)
    assert build(tmp_path, FIRST, detect=one_face)[0]["kind"] == "face"


def test_the_owners_labels_survive_a_rewrite_and_score_the_eye(tmp_path):
    rows = [{**r, "eye": "soft"} for r in build(tmp_path, FIRST)]
    path = fs.write_labels(tmp_path, "abcd1234", rows)
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["crops"][0]["owner"], doc["crops"][1]["owner"] = "bad", "good"
    path.write_text(json.dumps(doc), encoding="utf-8")
    again = json.loads(fs.write_labels(tmp_path, "abcd1234", rows).read_text(encoding="utf-8"))
    assert [c["owner"] for c in again["crops"][:2]] == ["bad", "good"]
    assert again["agreement"] == {"labelled": 2, "agree": 1}


def test_a_crop_is_a_square_around_the_face_kept_inside_the_frame():
    assert fs.square([40.0, 30.0, 52.0, 42.0], 96, 96) == (37, 27, 55, 45)
    assert fs.square([0.0, 0.0, 12.0, 12.0], 96, 96) == (0, 0, 18, 18)
    assert fs.smallest_box([]) is None and fs.cut_height([{"index": 0}]) == fs.CUT_HEIGHT


def test_the_log_line_names_the_soft_and_warped_crops_and_the_labels_file():
    strip = {"crops": [{}, {}], "soft": ["T01", "T26"], "warped": []}
    said = fs.line(strip, "abcd1234")
    assert said.startswith("FACE STRIP (log only): 2 crops, eye soft T01 T26, warped none")
    assert "review/face_labels_abcd1234.json" in said and "review/faces_abcd1234.png" in said
    assert fs.line({}, "abcd1234").startswith("FACE STRIP: no crops")


def test_no_face_list_falls_back_to_every_take(tmp_path):
    rows = build(tmp_path, {}, detect=one_face)
    assert rows and all(r["tier"] == "small" and not r["listed"] for r in rows)
    assert len(rows) == fs.PER_TIER


# ---- step 11 -----------------------------------------------------------------------------

def a_home(tmp_path, face: dict) -> Path:
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "shots.json").write_text(json.dumps(RECORDS), encoding="utf-8")
    (room / "refine.json").write_text(json.dumps({"face_list": face}), encoding="utf-8")
    (tmp_path / "cut").mkdir()
    (tmp_path / "cut" / "m.mp4").write_bytes(b"a master")
    return tmp_path


def test_step_11_writes_the_strip_and_the_labels_beside_the_master_eye(tmp_path, monkeypatch):
    home = a_home(tmp_path, FIRST)
    seen = {}

    def read(home_, master, plan, placed, **kit):
        seen.update(kit)
        return "verdict", {"face_strip": {"crops": [{**r, "eye": "soft"} for r in kit["strip"]]}}
    monkeypatch.setattr(s11.master_eye, "read", read)
    kit = {"frames": frames, "reader": str, "embed": no_faces, "detect": one_face, "face_reader": str}
    s11.read_master(home, home / "cut" / "m.mp4", {}, PLACED, kit)
    assert len(seen["strip"]) == 13 and seen["face_reader"] is str and "detect" not in seen
    sha8 = s11.yp.sha8(home / "cut" / "m.mp4")
    labels = json.loads((home / "review" / f"face_labels_{sha8}.json").read_text(encoding="utf-8"))
    assert {c["eye"] for c in labels["crops"]} == {"soft"}


def test_a_kit_with_no_detector_makes_no_strip(tmp_path, monkeypatch):
    home = a_home(tmp_path, FIRST)
    monkeypatch.setattr(s11.master_eye, "read", lambda *a, **kit: ("v", {"strip": kit["strip"]}))
    _v, m = s11.read_master(home, home / "cut" / "m.mp4", {}, PLACED, {"frames": frames})
    assert m["strip"] == [] and not (home / "review").exists()


def test_step_11_logs_the_face_list_and_never_fails_on_it(tmp_path):
    home, said = a_home(tmp_path, FIRST), []
    ctx = SimpleNamespace(home=home, log=lambda msg, **kw: said.append((msg, kw)))
    s11.face_list_note(ctx)
    assert said[0][0].startswith("FACE LIST (log only") and said[0][1]["level"] == "WARNING"
    (home / "takes" / "r2v" / "refine.json").write_text("{}", encoding="utf-8")
    said.clear()
    s11.face_list_note(ctx)
    assert said == []
