"""The planned move against the rendered move is a row that BINDS.

Jekyll ep01 (2026-10-13, MOTION.md cause 5): `camera_ok` read False on 23 of
27 takes and every one of them passed -- it is a stillness meter (see
test_camera_ok_is_a_stillness_meter.py), not a mismatch verdict, and its
zoom curve was clamped at 1.25x, so T13's 2.5x and T14's 4.75x both read 1.25.
T14's TILT rendered as a 4.75x push into a caricature and shipped.

CALIBRATED on the owner-liked WotW ep01-03 (69 takes, subject zoom ratios in
their DQ records):
    a move that plans no scale change (pan, tilt, track, locked, rise):
        max travel 2.68x (ep01 T05, a pan)            -> wall 3.0x, HARD
    a planned push: max 3.29x (ep02 T16)              -> wall 3.5x, HARD
    a planned pull-back: up to 9.1x (ep02 T10)        -> no wall
0 of 69 owner-liked takes fire; Jekyll T14 (tilt, 4.75x) fires.  T13 (push,
2.54x) does NOT: WotW pushed further and the owner liked it, so scale alone
cannot call it -- the zoom row's advisory points stay its only price.
"""
from __future__ import annotations

from studio import take_zoom as tz


def seg(ratio: float, measured: bool = True) -> dict:
    return {"ratio": ratio, "measured": measured, "camera": ratio}


def test_a_tilt_that_became_a_big_push_fails_hard():
    g = tz.move_row({"segments": [seg(4.75)]}, "The camera tilts up from the two frosted stone steps")
    assert g.name == "camera-move" and g.hard and not g.ok


def test_the_owner_liked_pan_overrun_passes():
    g = tz.move_row({"segments": [seg(2.68)]}, "The camera pans left across the whole shot")
    assert g.ok


def test_a_planned_push_is_walled_further_out():
    assert tz.move_row({"segments": [seg(3.29)]}, "The camera pushes in toward Ogilvy's face").ok
    assert not tz.move_row({"segments": [seg(3.6)]}, "The camera pushes in toward his face").ok


def test_a_pull_back_has_no_wall():
    assert tz.move_row({"segments": [seg(0.11)]}, "The camera pulls back from Ogilvy's outstretched hands").ok


def test_an_unplanned_pull_of_the_same_size_fires():
    assert not tz.move_row({"segments": [seg(1 / 3.2)]}, "The camera holds a locked-off frame").ok


def test_an_unmeasured_zoom_fails_nothing():
    g = tz.move_row({"segments": [seg(9.0, measured=False)]}, "The camera pans right")
    assert g.ok and g.value is None


def test_each_segment_is_judged_by_its_own_plan():
    z = {"segments": [seg(1.0), seg(3.2)]}
    assert not tz.move_row(z, ["The camera pushes in on him", "The camera tilts up to the roof"]).ok
    assert tz.move_row(z, ["The camera tilts up to the roof", "The camera pushes in on him"]).ok


def test_no_zoom_read_is_not_measured():
    assert tz.move_row({}, "The camera pans").value is None


# ---- the calibration, held against the records on disk -------------------------------

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WOTW = ROOT / "library" / "20260827135508_the-war-of-the-worlds" / "episodes"
JEKYLL = ROOT / "library" / "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde" / "episodes"


def fired(home: Path) -> list[int]:
    plan = json.loads((home / "plan.json").read_text(encoding="utf-8"))
    motion = {s["index"]: s.get("motion", "") for s in plan["shots"]}
    out = []
    for p in sorted((home / "takes" / "r2v").glob("T??.dq.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        shots = [motion.get(r["take"], "")]
        if not tz.move_row(r.get("zoom") or {}, shots).ok:
            out.append(r["take"])
    return out


def test_no_owner_liked_wotw_take_fires():
    homes = [WOTW / f"ep0{n}" for n in (1, 2, 3)]
    if not all((h / "plan.json").exists() for h in homes):
        pytest.skip("WotW ep01-03 records are not on disk")
    assert [fired(h) for h in homes] == [[], [], []]


def test_jekyll_t14_fires():
    home = JEKYLL / "ep01"
    if not (home / "takes" / "r2v" / "T14.dq.json").exists():
        pytest.skip("Jekyll ep01 records are not on disk")
    assert 14 in fired(home)


def test_the_ladder_cures_it_with_another_move_type():
    from studio import take_ladder
    from studio.judges.verdict import Fault
    fault = Fault(kind="camera-move", where="T14", note="4.75x over the 3.0x wall", severity="high")
    assert take_ladder.cure_of([fault]) == "move_type"
    assert take_ladder.substitute_id("camera-move", "The camera tilts up from the steps") == "locked"
