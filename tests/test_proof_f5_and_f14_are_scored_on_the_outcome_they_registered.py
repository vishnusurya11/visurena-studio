"""F5 and F14 are scored on their own pre-registered outcomes (DESIGN 3.2), never on the common rows alone.

The first window (2026-10-21 17:45 PDT) scored both PASS while each died at step 01 on a harness
bug (`no book matching '99991021000000'` -> `REFUSED: scripts/refs/cast_rows.py exit 1`): CHECKS
had no row for them, so any named park passed.  F5 must reach step 02, set the draft aside and stop
named `plan` with nothing from step 03 on; F14 must meet every planted gap, drawn again by its
just-in-time step or named by the stop."""
from __future__ import annotations

import json
from pathlib import Path

from studio.rehearsal import asserts

STEP_01_DEATH = "--- step 01 (bind) | t ---\nREFUSED: scripts/refs/cast_rows.py exit 1\n"
DEFERRED = "--- step 01 (bind) skipped: output exists\n--- step 02 (plan) | t ---\nDEFERRED PLAN | G-DIAL\n"


def episode(tmp_path: Path, log: str, state: str, reason: str) -> Path:
    book = tmp_path / "library" / "9999_book"
    home = book / "episodes" / "ep02"
    home.mkdir(parents=True)
    (home / "drive_run01.log").write_text(log, encoding="utf-8")
    (book / "autopilot").mkdir()
    (book / "autopilot" / "status.json").write_text(json.dumps({"episode": {"n": 2, "state": state, "reason": reason}}))
    return book


def f5(tmp_path: Path, book: Path) -> dict:
    return asserts.CHECKS["F5"]("F5", tmp_path, book, [], {})


def test_f5_that_died_at_step_01_fails_named(tmp_path):
    book = episode(tmp_path, STEP_01_DEATH, "PARKED", "refused: REFUSED: scripts/refs/cast_rows.py exit 1")
    r = f5(tmp_path, book)
    assert r["passed"] is False and "step 02 never ran" in r["detail"]


def test_f5_passes_when_the_plan_is_set_aside_and_the_stop_names_it(tmp_path):
    book = episode(tmp_path, DEFERRED, "PARKED", "safety: plan_builder: the best plan still carries a line")
    (book / "episodes" / "ep02" / "plan.deferred.json").write_text("{}", encoding="utf-8")
    assert f5(tmp_path, book)["passed"] is True


def test_f5_fails_when_a_step_past_the_plan_started(tmp_path):
    book = episode(tmp_path, DEFERRED + "--- step 03 (places) | t ---\n", "PARKED", "plan_deferred")
    (book / "episodes" / "ep02" / "plan.deferred.json").write_text("{}", encoding="utf-8")
    r = f5(tmp_path, book)
    assert r["passed"] is False and "step 03" in r["detail"]


def test_f5_fails_with_no_draft_set_aside(tmp_path):
    r = f5(tmp_path, episode(tmp_path, DEFERRED, "PARKED", "plan_deferred"))
    assert r["passed"] is False and "plan.deferred.json" in r["detail"]


GAP = {"kind": "place_picture", "what": "utterson_house/bedroom", "planted": True, "present": True}


def f14(tmp_path: Path, book: Path, gaps: list[dict]) -> dict:
    (tmp_path / asserts.GAPS).write_text(json.dumps(gaps), encoding="utf-8")
    return asserts.CHECKS["F14"]("F14", tmp_path, book, [], {})


def test_f14_that_stopped_before_its_gaps_fails_named(tmp_path):
    book = episode(tmp_path, DEFERRED, "PARKED", "safety: plan_builder: no draft reached plan.json")
    r = f14(tmp_path, book, [GAP])
    assert r["passed"] is False and "utterson_house/bedroom" in r["detail"]


def test_f14_passes_when_the_just_in_time_step_drew_the_gap_again(tmp_path):
    book = episode(tmp_path, DEFERRED, "HELD_PUBLISH", "held_publish")
    picture = book / "refs" / "locations" / "utterson_house" / "bedroom.png"
    picture.parent.mkdir(parents=True)
    picture.write_bytes(b"png")
    assert f14(tmp_path, book, [GAP])["passed"] is True


def test_f14_passes_when_the_park_names_the_missing_field(tmp_path):
    book = episode(tmp_path, DEFERRED, "PARKED", "refused: REFUSED: no master for utterson_house/bedroom")
    assert f14(tmp_path, book, [GAP])["passed"] is True


def test_f14_with_nothing_planted_fails(tmp_path):
    book = episode(tmp_path, DEFERRED, "HELD_PUBLISH", "held_publish")
    assert asserts.CHECKS["F14"]("F14", tmp_path, book, [], {})["passed"] is False


def test_planting_the_gaps_leaves_their_list_in_the_sandbox(tmp_path, monkeypatch):
    from scripts.proof import rehearse
    report = tmp_path / "preconditions_ch2.json"
    report.write_text(json.dumps({"gaps": [{"kind": "place_picture", "what": "utterson_house/bedroom"}]}))
    monkeypatch.setitem(rehearse.FILES, "preconditions", report)
    book = tmp_path / "library" / "9999_book"
    book.mkdir(parents=True)
    rehearse.plant_row(tmp_path, book, rehearse.TABLE["F14"])
    kept = json.loads((tmp_path / asserts.GAPS).read_text(encoding="utf-8"))
    assert [g["what"] for g in kept] == ["utterson_house/bedroom"] and kept[0]["present"] is True
