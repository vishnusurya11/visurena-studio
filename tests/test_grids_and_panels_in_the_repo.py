"""The storyboard stage lives in the repo and names, files and cuts its own grids.

Audit items 9, 12, 16, 22, 2026-09-22: the grid driver and the panel exporter
were session scripts; grid names carried no episode (ep10's "pit" would
overwrite ep09's in ComfyUI's shared output); manifests lived in a session
folder; and the driver asked for the place's BOOK anchor instead of the
setup's own view.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))

import grids  # noqa: E402
import panels  # noqa: E402


def test_a_grid_name_carries_its_episode():
    assert grids.grid_name(9, "pit", 2, 1, "empty") == "ep09_grid_pit_2x1_empty"
    assert grids.grid_name(10, "pit", 2, 1, "empty") != grids.grid_name(9, "pit", 2, 1, "empty")


def test_the_place_picture_is_the_setups_own_view(tmp_path):
    loc = tmp_path / "analysis" / "locations"
    loc.mkdir(parents=True)
    (loc / "common.json").write_text(json.dumps(
        {"profile": {"design": {"views": [{"id": "wide_establishing"}]}}}))
    folder = tmp_path / "refs" / "locations" / "common"
    folder.mkdir(parents=True)
    for n in ("wide_establishing", "wide_pit_day"):
        (folder / f"{n}.png").write_bytes(b"png")

    class Setup:
        location, view = "common", "wide_pit_day"
    assert grids.wide_for(tmp_path, Setup()).name == "wide_pit_day.png"


def grid(name, shots, plan="p1"):
    return {"name": name, "cols": len(shots), "rows": 1, "shots": shots, "plan": plan}


def test_every_shot_comes_from_exactly_one_grid():
    owner = panels.owner_of([grid("a", [0, 1]), grid("b", [2])], [0, 1, 2])
    assert owner[2][0]["name"] == "b" and owner[1][1] == 1


def test_a_shot_drawn_twice_refuses():
    with pytest.raises(SystemExit, match="two grids"):
        panels.owner_of([grid("a", [0, 1]), grid("b", [1])], [0, 1])


def test_a_shot_drawn_by_none_refuses():
    with pytest.raises(SystemExit, match="no grid"):
        panels.owner_of([grid("a", [0])], [0, 1])


def test_a_grid_from_an_older_plan_is_named():
    assert panels.stale_grids([grid("a", [0], "p1"), grid("b", [1], "p0")], "p1") == ["b"]


def test_manifests_are_read_from_the_episode(tmp_path):
    folder = tmp_path / "episodes" / "ep09" / "storyboard" / "grids"
    folder.mkdir(parents=True)
    (folder / "ep09_grid_pit_2x1.json").write_text(json.dumps(grid("ep09_grid_pit_2x1", [9, 10])))
    assert [r["name"] for r in panels.manifests(tmp_path, 9)] == ["ep09_grid_pit_2x1"]


# ---- a grid is stale only when ITS shots change (2026-09-23) ----------------
# ep09: a hat worded twice in shot 11's plan text could not be fixed without
# redrawing all 23 panels, because every grid carried one hash of the whole
# plan. A grid is drawn from its own shots and their setups, and that is what
# it is fingerprinted by.

from studio import episode_home  # noqa: E402

WOTW = "20260827135508_the-war-of-the-worlds"


@pytest.fixture(scope="module")
def ep09():
    return episode_home.load_plan(episode_home.book_dir(WOTW), 9)


def edited(ep, index, frame):
    shots = [s.model_copy(update={"frame": frame}) if s.index == index else s for s in ep.shots]
    return ep.model_copy(update={"shots": shots})


def test_a_grid_is_fingerprinted_by_its_own_shots(ep09):
    before = grids.shots_sha(ep09, [9, 10, 11])
    assert grids.shots_sha(edited(ep09, 3, "a different haze"), [9, 10, 11]) == before
    assert grids.shots_sha(edited(ep09, 10, "a different flag"), [9, 10, 11]) != before


def test_only_the_grid_whose_shot_changed_is_stale(ep09):
    rows = [{**grid("pit", [9, 10, 11], "old"), "drawn_from": grids.shots_sha(ep09, [9, 10, 11])},
            {**grid("haze", [3], "old"), "drawn_from": grids.shots_sha(ep09, [3])}]
    assert panels.stale_grids(rows, "new", edited(ep09, 3, "a different haze")) == ["haze"]


def test_a_manifest_without_a_fingerprint_falls_back_to_the_plan_hash(ep09):
    assert panels.stale_grids([grid("a", [0], "p0")], "p1", ep09) == ["a"]


def test_a_camera_move_is_not_what_a_grid_is_drawn_from(ep09):
    """The grid prompt never reads `motion`. ep09's take retakes needed three
    camera moves changed; with motion in the hash, three good grids would have
    been redrawn for words they never saw."""
    moved = ep09.model_copy(update={"shots": [
        s.model_copy(update={"motion": "The camera pushes in on it; it goes on burning."})
        if s.index == 14 else s for s in ep09.shots]})
    assert grids.shots_sha(moved, [13, 14, 21]) == grids.shots_sha(ep09, [13, 14, 21])


# ---- re-cutting an unchanged panel leaves its file alone (2026-09-23) --------
# Re-running panels.py after a plan edit rewrote all 23 ep09 panels with the
# same pixels; the takes then refused every verdict as older than its picture.

from PIL import Image  # noqa: E402


def test_an_unchanged_panel_is_not_rewritten(tmp_path):
    img = Image.new("RGB", (8, 8), (10, 20, 30))
    out = tmp_path / "shot_00.png"
    assert panels.save_if_changed(img, out) is True
    stamp = out.stat().st_mtime_ns
    assert panels.save_if_changed(img, out) is False
    assert out.stat().st_mtime_ns == stamp


def test_a_changed_panel_is_rewritten(tmp_path):
    out = tmp_path / "shot_00.png"
    panels.save_if_changed(Image.new("RGB", (8, 8), (10, 20, 30)), out)
    assert panels.save_if_changed(Image.new("RGB", (8, 8), (99, 20, 30)), out) is True
