"""The work grid: one row per shot, a cell per stage -- board (its grid), panel, take -- with the
round each is on (timeline debate 2026-10-18, D3; owner go).  A loop is a shot's round, never an
arrow: a grid redrawn twice reads r3, a take on its second attempt r2, a take a cure round named
reads its fault.  Clean rows fold into one line.  Read from files now, one reader."""
from __future__ import annotations

import json

from studio.command_center import workgrid
from test_progress_card_api import board  # noqa: F401  (the fixture)

LAYOUT = [{"setup": "corner", "cols": 1, "rows": 1, "shots": [0], "tag": "a"},
          {"setup": "door", "cols": 2, "rows": 1, "shots": [1, 2]}]


def home_with(tmp_path):
    h = tmp_path / "ep01"
    sb, tk = h / "storyboard", h / "takes" / "r2v"
    for d in (sb / "grids", sb / "superseded" / "r1", tk / "attempts"):
        d.mkdir(parents=True)
    (sb / "layout.json").write_text(json.dumps(LAYOUT), encoding="utf-8")
    (sb / "ladder.json").write_text(json.dumps({"climbed": ["ep01_grid_door_2x1"]}), encoding="utf-8")
    for name in ("ep01_grid_corner_1x1_a", "ep01_grid_door_2x1"):
        (sb / "grids" / f"{name}.png").write_bytes(b"p")
    (sb / "superseded" / "r1" / "ep01_grid_door_2x1_v1.png").write_bytes(b"p")
    (sb / "superseded" / "ep01_grid_door_2x1_v2.png").write_bytes(b"p")
    for n in (0, 1, 2):
        (sb / f"shot_{n:02d}.png").write_bytes(b"p")
    (sb / "panel_dq.json").write_text(json.dumps([{"shot": 2, "flags": ["blur"]}]), encoding="utf-8")
    (tk / "T00.mp4").write_bytes(b"m")
    (tk / "T00.dq.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    (tk / "T01.mp4").write_bytes(b"m")
    (tk / "T01.dq.json").write_text(json.dumps({"passed": False}), encoding="utf-8")
    (tk / "attempts" / "T01_fail1.mp4").write_bytes(b"m")
    (tk / "ladder.json").write_text(json.dumps({"rounds": [{"why": "batched_cures: warp",
                                                            "faults": {"1": ["warp"]}}]}), encoding="utf-8")
    return h


def test_each_shot_gets_a_board_panel_and_take_cell(tmp_path):
    rows = {r["shot"]: r for r in workgrid.grid(workgrid.read(home_with(tmp_path), "ep01"))}
    assert rows[0]["board"] == {"state": "done", "round": 1, "note": ""}
    assert rows[1]["board"]["round"] == 3 and rows[1]["board"]["note"] == "climbed"
    assert rows[2]["panel"]["state"] == "flag" and rows[2]["panel"]["note"] == "blur"
    assert rows[0]["take"] == {"state": "done", "round": 1, "note": ""}
    assert rows[1]["take"] == {"state": "fail", "round": 2, "note": "warp"}
    assert rows[2]["take"]["state"] == "waiting"


def test_a_cut_panel_means_its_grid_was_drawn(tmp_path):
    # WotW ep20 replay: shot 5's grid name moved after a later layout; the shipped shot read 'waiting'
    h = home_with(tmp_path)
    (h / "storyboard" / "grids" / "ep01_grid_corner_1x1_a.png").unlink()
    rows = {r["shot"]: r for r in workgrid.grid(workgrid.read(h, "ep01"))}
    assert rows[0]["board"]["state"] == "done"


def test_rows_run_in_shot_order_not_layout_order(tmp_path):
    # live Jekyll ep01: layout order read 06 07 08 09 00 10 ... -- the owner reads shots in order
    h = home_with(tmp_path)
    (h / "storyboard" / "layout.json").write_text(json.dumps(list(reversed(LAYOUT))), encoding="utf-8")
    assert [r["shot"] for r in workgrid.grid(workgrid.read(h, "ep01"))] == [0, 1, 2]


def test_clean_rows_fold_into_one_line(tmp_path):
    folded = workgrid.fold(workgrid.grid(workgrid.read(home_with(tmp_path), "ep01")))
    assert folded[0] == {"clean": "00", "n": 1} and [r["shot"] for r in folded[1:]] == [1, 2]


def test_a_run_of_clean_shots_reads_as_a_range():
    clean = {"board": {"state": "done", "round": 1, "note": ""}, "panel": {"state": "done", "round": 1, "note": ""},
             "take": {"state": "done", "round": 1, "note": ""}}
    rows = [{"shot": n, **clean} for n in (0, 1, 2)] + [{"shot": 3, **clean, "take": {"state": "waiting", "round": 0, "note": ""}}]
    assert workgrid.fold(rows)[0] == {"clean": "00–02", "n": 3}


def test_the_unit_page_draws_the_grid_under_the_live_card(board):  # noqa: F811
    import re
    import time
    from fastapi.testclient import TestClient
    from command_center_fixtures import CODEX
    from test_progress_card_api import _drive
    sb = board["home"] / "storyboard"
    sb.mkdir(exist_ok=True)
    (sb / "layout.json").write_text(json.dumps([{"setup": "s", "cols": 1, "rows": 1, "shots": [0, 1, 2]}]),
                                    encoding="utf-8")
    board["app"].state.procs = lambda: _drive(time.time() - 3600)
    html = TestClient(board["app"]).get(f"/d/episode/{CODEX}/ep04").text
    grid = re.search(r'<details class="lv-work".*?</details>', html, re.S)
    assert grid and grid.group(0).count('class="wrow"') >= 1 and "board" in grid.group(0)


def test_an_episode_before_the_board_has_no_grid(tmp_path):
    (tmp_path / "ep02").mkdir()
    assert workgrid.grid(workgrid.read(tmp_path / "ep02", "ep02")) == []
