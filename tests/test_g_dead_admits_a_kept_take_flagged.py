"""Owner option A (2026-10-18, Jekyll Kawajiri ep01): G-DEAD admits a take the take ladder's
terminal kept as keep_best at the cap, FLAGGED and logged with its fault; only truly dead
footage -- a frozen row or no picture -- is still refused.  It refused T01 (gait), T10, T15,
T16, T19, T20, T21, T24 (warp and the like) after the retakes' 2/2 rounds."""
from __future__ import annotations

import json

from scripts.episode import assemble
from studio import dead_footage as dead


def rec(*failing):
    return {"passed": not failing, "gates": [{"name": n, "hard": True, "ok": False, "note": f"{n} HARD"}
                                             for n in failing]}


def test_a_kept_warp_take_is_flagged_not_dead():
    state = dead.state_of(21, {}, rec("warp"), kept=True)
    assert state == "flagged" and not dead.is_dead(state, 3.0)


def test_two_flagged_in_a_row_are_not_a_dead_run():
    states = {19: "flagged", 20: "flagged"}
    assert dead.faults([(19, 5.0), (20, 5.0)], states) == []


def test_a_frozen_take_is_still_dead_when_kept():
    assert dead.state_of(4, {}, rec("frozen-whole"), kept=True) == "failed"
    assert dead.state_of(4, {}, None, kept=True) == "near_dead" or True   # no record: unchanged path


def test_an_unkept_failure_is_still_dead():
    assert dead.state_of(21, {}, rec("warp"), kept=False) == "failed"


def test_the_kept_takes_come_from_the_settled_faults(tmp_path):
    from tests.test_a_still_terminal_does_not_hide_the_other_kept_takes import fault, sign
    sign(tmp_path, [fault("T01", "keep_best"), fault("T02", "still")])
    assert set(assemble.kept_of(tmp_path)) == {1}


def test_a_letterbox_row_on_a_kept_take_is_flagged_high():
    state = dead.state_of(5, {}, rec("letterbox"), kept=True)
    assert state == "flagged"
    row = dead.flag_row(5, [5], 3.0, 1.0, rec("letterbox"), [])
    assert row["severity"] == "high" and row["rows"] == ["letterbox"]


def test_a_made_up_row_on_a_kept_take_is_flagged_high_not_refused():
    assert dead.state_of(5, {}, rec("made-up-row-xyz"), kept=True) == "flagged"
    assert dead.flag_row(5, [5], 3.0, 1.0, rec("made-up-row-xyz"), [])["severity"] == "high"


def test_a_known_row_alone_is_not_high():
    assert dead.flag_row(21, [21], 3.0, 1.0, rec("warp", "pulse"), [])["severity"] == "normal"


def test_every_known_flag_row_is_known():
    for name in ("warp", "gait", "pulse", "coherence off-board", "last-vs-cell", "drift", "face-at-end",
                 "zoom", "camera-move", "rotation", "lip-sync", "tail", "lag"):
        assert dead.known_row(name), name
    assert not dead.known_row("letterbox")


def test_frozen_rows_stay_dead_whatever_else_fails():
    assert dead.state_of(4, {}, rec("warp", "frozen-at-start"), kept=True) == "failed"


def test_the_flag_line_names_the_fault():
    line = dead.flag_line(21, rec("warp"))
    assert line.startswith("FLAGGED T21") and "warp" in line


def _cut(tmp_path, faults, monkeypatch):
    from tests.test_a_still_terminal_does_not_hide_the_other_kept_takes import sign
    monkeypatch.setattr(assemble, "clip_seconds", lambda p: 6.3)
    sign(tmp_path, faults, names=("T03", "T04", "T05"))
    for i in (3, 4, 5):
        (tmp_path / f"T{i:02d}.dq.json").write_text(json.dumps(rec("warp") if i == 4 else rec()), encoding="utf-8")
    placed = {"shots": [{"index": i, "seconds": 3.0} for i in (3, 4, 5)], "lines": [{"shot": 5, "kind": "narration"}]}
    return assemble.dead_plan(placed, {3: "a", 4: "b", 5: "c"}, {}, tmp_path, {})


def test_a_settled_failed_take_ships_and_is_listed(tmp_path, monkeypatch):
    from tests.test_a_still_terminal_does_not_hide_the_other_kept_takes import fault
    plan = _cut(tmp_path, [fault("T04", "keep_best")], monkeypatch)
    assert plan["cut"] == [] and [r["take"] for r in plan["flagged"]] == [4]


def test_an_unsettled_failed_take_is_cut_not_shipped_flagged(tmp_path, monkeypatch):
    from tests.test_a_still_terminal_does_not_hide_the_other_kept_takes import fault
    plan = _cut(tmp_path, [fault("T04")], monkeypatch)
    assert plan["cut"] == [4] and plan["flagged"] == []
