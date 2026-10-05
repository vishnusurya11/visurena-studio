"""The unit page's media data (panel ruling 2026-10-04, PKG-5): a take tile is drawn
with its own first frame, the master with its title card, a missing picture says
why; the shot cards join panel and take by shot number; QC collapses to one chip
when it passes; the display question loses its appearance parentheticals; the
Files section groups the unit folder by kind with repeated names folded; the
sibling units are the neighbours in the department's order.  Pure reads, $0."""
from __future__ import annotations

import os
import sqlite3

import pytest

from studio.command_center import unit_view as uv

CODEX = "20260901000001"


def touch(path, data=b"x", mtime=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path


# --- 5.6 the display question ---


def test_the_display_question_drops_appearance_parentheticals():
    q = "Today, can the brother (grey eyes, Brown herringbone Norfolk jacket) get the women aboard?"
    assert uv.display_question(q) == "Today, can the brother get the women aboard?"
    assert uv.display_question("Can the guns stop them?") == "Can the guns stop them?"
    assert uv.display_question("") == "" and uv.display_question(None) == ""


# --- 5.6 QC collapses when it passes ---


QC_OK = {"lufs": -14.15, "lufs_ok": True, "true_peak": -1.5, "tp_ok": True, "planned_cuts": [1, 2],
         "missing_cuts": [], "lines": [{"passed": True}, {"passed": True}], "takes": {"pass": 24, "of": 24}}


def test_qc_checks_are_five_named_measures():
    checks = uv.qc_checks(QC_OK)
    assert [c["name"] for c in checks] == ["LUFS", "peak", "cuts", "lines", "takes"]
    assert all(c["ok"] for c in checks) and checks[0]["text"] == "LUFS -14.15"


def test_qc_summary_collapses_a_pass_and_spells_out_failures():
    assert uv.qc_summary(QC_OK) == {"n_ok": 5, "n": 5, "all_ok": True, "fails": []}
    bad = uv.qc_summary({**QC_OK, "tp_ok": False, "missing_cuts": [2]})
    assert (bad["n_ok"], bad["all_ok"]) == (3, False)
    assert [f["name"] for f in bad["fails"]] == ["peak", "cuts"] and bad["fails"][1]["text"] == "cuts 1/2"
    assert uv.qc_summary({}) is None


# --- 5.5 truthful posters ---


def test_a_take_poster_is_its_own_first_frame(tmp_path):
    home = tmp_path / "episodes" / "ep12"
    assert uv.take_poster(home, "T05") is None
    touch(home / "takes/work/content/T05_1.png")
    assert uv.take_poster(home, "T05") == "takes/work/content/T05_1.png"
    touch(home / "takes/work/content/T05_0.png")
    assert uv.take_poster(home, "T05") == "takes/work/content/T05_0.png"


def test_the_master_poster_is_the_publish_thumbnail_then_the_title_card(tmp_path):
    assert uv.master_poster(tmp_path, "ep12") is None
    touch(tmp_path / "title/ep12.png")
    assert uv.master_poster(tmp_path, "ep12") == "title/ep12.png"
    touch(tmp_path / "publish/ep12.png")
    assert uv.master_poster(tmp_path, "ep12") == "publish/ep12.png"
    assert uv.master_poster(None, "ep12") is None


def test_the_latest_master_is_the_newest_file(tmp_path):
    home = tmp_path / "episodes" / "ep12"
    assert uv.latest_master(home) is None
    touch(home / "cut/master_iter7.mp4", mtime=100)
    touch(home / "cut/master_iter8.mp4", mtime=200)
    touch(home / "cut/master_r2v.mp4", mtime=150)
    assert uv.latest_master(home) == {"rel": "cut/master_iter8.mp4", "name": "iter8", "short": "v8"}


def test_unit_rel_strips_the_home():
    assert uv.unit_rel("episodes/ep12/storyboard/shot_01.png", "episodes/ep12") == "storyboard/shot_01.png"
    assert uv.unit_rel("title/ep12.png", "episodes/ep12") == "title/ep12.png"


# --- the shot cards: panel + take joined by shot number ---


def tile(index, rel, faults=()):
    return {"index": index, "rel": rel, "label": f"{index:02d}", "size": "wide", "frame": "a road",
            "faults": list(faults), "dq": [], "flagged": bool(faults), "thumb": f"/thumb/{rel}"}


def test_a_shot_card_draws_the_take_poster_with_the_panel_inset(tmp_path):
    home = tmp_path / "episodes" / "ep12"
    touch(home / "takes/work/content/T01_0.png")
    panels = [tile(0, "episodes/ep12/storyboard/shot_00.png"), tile(1, "episodes/ep12/storyboard/shot_01.png")]
    takes = [tile(1, "episodes/ep12/takes/r2v/T01.mp4", [{"kind": "faces", "n": 1, "text": "x"}])]
    cards = uv.shot_cards(CODEX, tmp_path, "episodes/ep12", panels, takes)
    assert [c["index"] for c in cards] == [0, 1]
    assert cards[0]["take"] is None and cards[0]["main"]["rel"] == "storyboard/shot_00.png"
    one = cards[1]
    assert one["take"]["rel"] == "takes/r2v/T01.mp4" and one["main"]["rel"] == "takes/r2v/T01.mp4"
    assert one["main"]["poster"].startswith(f"/thumb/{CODEX}/320/episodes/ep12/takes/work/content/T01_0.png")
    assert one["panel"]["rel"] == "storyboard/shot_01.png" and one["flagged"]


def test_a_take_without_a_frame_says_why(tmp_path):
    takes = [tile(2, "episodes/ep12/takes/r2v/T02.mp4")]
    [card] = uv.shot_cards(CODEX, tmp_path, "episodes/ep12", [], takes)
    assert card["main"]["poster"] == "" and card["main"]["why"] == "no frame of T02 on disk"


# --- grids ---


def test_grids_are_newest_first_with_their_name(tmp_path):
    home = tmp_path / "episodes" / "ep17"
    touch(home / "storyboard/grids/ep17_beach_2x2.png", mtime=100)
    touch(home / "storyboard/grids/ep17_stern_3x1.png", mtime=300)
    touch(home / "storyboard/grids/grid_beach_1x1_b.png", mtime=50)
    grids = uv.grid_tiles(CODEX, tmp_path, home)
    assert [g["rel"] for g in grids][:2] == ["storyboard/grids/ep17_stern_3x1.png", "storyboard/grids/ep17_beach_2x2.png"]
    assert grids[2]["name"] == "beach 1x1 b"
    assert grids[0]["name"] == "stern 3x1" and grids[0]["thumb"].startswith(f"/thumb/{CODEX}/320/episodes/ep17/")


# --- files: grouped by kind, repeats folded ---


def test_a_file_pattern_replaces_digit_runs():
    assert uv.file_pattern("storyboard/shot_05.png") == "storyboard/shot_NN.png"
    assert uv.file_pattern("plan.json") == "plan.json"
    assert uv.file_pattern("review/eye_faf11c8f.json") == "review/eye_faf11c8f.json"
    assert uv.file_pattern("_logs/x__20261005055609.log") == "_logs/x__20261005055609.log"


@pytest.mark.parametrize(("rel", "bucket"), [
    ("plan.json", "Plan and verdicts"), ("storyboard/shot_00.png", "Storyboard"), ("takes/r2v/T00.mp4", "Takes"),
    ("cut/master_r2v.mp4", "Master"), ("review/eye_a.json", "Master"), ("audio/bed.wav", "Audio"),
    ("learnings.jsonl", "Run records and logs"), ("_logs/x.log", "Run records and logs"), ("reports/s.png", "Reports")])
def test_every_file_has_one_bucket(rel, bucket):
    assert uv.file_bucket(rel) == bucket


def test_file_groups_fold_three_or_more_like_names():
    files = [{"rel": f"storyboard/shot_{i:02d}.png", "size": 1024, "kind": "image"} for i in range(3)]
    files += [{"rel": "plan.json", "size": 2048, "kind": "doc"}]
    groups = uv.file_groups(files)
    assert [g["name"] for g in groups] == ["Plan and verdicts", "Storyboard"]
    folded = groups[1]["rows"][0]
    assert (folded["label"], folded["n"], folded["rel"], folded["set"]) == \
        ("storyboard/shot_NN.png", 3, "storyboard/shot_00.png", "shots")
    assert folded["size"] == "3.0 KB" and groups[0]["rows"][0]["set"] == "files"


def test_a_folder_of_many_unlike_files_folds_into_one_row():
    files = [{"rel": f"storyboard/grids/{name}/g.png" if name in "ab" else f"storyboard/grids/{name}.png",
              "size": 10, "kind": "image"} for name in "abcdefgh"]
    files += [{"rel": "storyboard/layout.json", "size": 10, "kind": "doc"}]
    rows = uv.file_rows(files)
    assert [(r["label"], r["n"], r["set"]) for r in rows] ==         [("storyboard/grids/…", 8, "grids"), ("storyboard/layout.json", 1, "files")]
    assert uv.fold_folder("storyboard/shot_00.png") == "" and uv.fold_folder("a/b/c/d.png") == "a/b"


# --- 5.4 siblings ---


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE work_orders (codex_id TEXT, stage TEXT, unit TEXT, sequence INTEGER)")
    for n in (1, 11, 12, 13):
        c.execute("INSERT INTO work_orders VALUES (?, 'episode', ?, ?)", (CODEX, f"ep{n:02d}", n))
    c.execute("INSERT INTO work_orders VALUES (?, 'refs', 'ep12', 1)", (CODEX,))
    return c


def test_natural_order_reads_numbers_as_numbers():
    assert sorted(["ep10", "ep9", "ep1"], key=uv.natural) == ["ep1", "ep9", "ep10"]


def test_siblings_are_the_neighbours_in_order(conn):
    assert uv.siblings(conn, CODEX, "episode", "ep12") == {"prev": "ep11", "next": "ep13"}
    assert uv.siblings(conn, CODEX, "episode", "ep01") == {"prev": None, "next": "ep11"}
    assert uv.siblings(conn, CODEX, "episode", "ep13") == {"prev": "ep12", "next": None}


# --- one state word per gate ---


@pytest.mark.parametrize(("chip", "word"), [
    ({"by": "", "word": "", "faults": 0, "css": "grey"}, "not signed"),
    ({"by": "j", "word": "flagged", "faults": 3, "css": "amber"}, "flagged"),
    ({"by": "j", "word": "pass", "faults": 0, "css": "green"}, "passed"),
    ({"by": "j", "word": "defer", "faults": 0, "css": "purple"}, "deferred"),
    ({"by": "j", "word": "rejected", "faults": 0, "css": "red"}, "failed")])
def test_one_state_word_per_gate(chip, word):
    assert uv.gate_state(chip) == word


def test_the_master_poster_is_drawn_from_the_1024_thumbnail(tmp_path):
    (tmp_path / "publish").mkdir()
    (tmp_path / "publish" / "ep12.png").write_bytes(b"x")
    url = uv.master_poster_url(CODEX, tmp_path, "publish/ep12.png")
    assert url.startswith(f"/thumb/{CODEX}/1024/publish/ep12.png")
    assert uv.master_poster_url(CODEX, tmp_path, None) == ""


@pytest.mark.parametrize("px, width", [(80, 160), (120, 320), (320, 320), (1024, 1024)])
def test_a_drawn_width_maps_to_one_served_thumb_width(px, width):
    from studio.command_center import library_paths
    assert library_paths.thumb_width(px) == width
