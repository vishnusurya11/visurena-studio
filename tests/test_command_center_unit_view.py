"""The unit page's bands (research F): pure-ish reads composed over the rows the
runners wrote and the files the verdict row names.  Every file read stays under
the unit's own book folder; every band tolerates a unit with nothing on disk."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from command_center_fixtures import CODEX, OTHER, make_library
from studio.command_center import unit_view as uv

NOW = datetime(2026, 9, 27, 5, 0, tzinfo=timezone.utc)


@pytest.fixture()
def library(tmp_path, monkeypatch):
    return make_library(tmp_path, monkeypatch)


def test_read_doc_stays_in_the_book(library):
    assert uv.read_doc(library, CODEX, "episodes/ep03/youtube.json") == {}
    assert uv.read_doc(library, CODEX, "../" + f"{OTHER}_other-book/secret.png") is None
    assert uv.read_doc(library, CODEX, "episodes/ep04/plan.py") is None
    assert uv.read_doc(library, CODEX, None) is None


def test_span_and_clock():
    assert (uv.span(0), uv.span(40), uv.span(1080), uv.span(6120)) == ("", "40s", "18m", "1h42")
    assert uv.hhmm("2026-09-27T04:02:16.8Z") == "04:02" and uv.hhmm("junk") == ""
    assert uv.day_hhmm("2026-09-27T04:02:16Z") == "27 Sep 04:02"


def test_run_short_is_the_runs_clock():
    assert uv._run_short({"run_id": f"{CODEX}__episode__20260927040215"}) == "04:02"
    assert uv._run_short({"run_id": "r5"}) == "r5" and uv._run_short({}) == ""


def test_lease_ok_stale_or_none():
    running = {"state": "running", "lease_until": "2026-09-27T05:30:00Z"}
    assert uv.lease(running, NOW) == {"state": "ok", "until": "05:30"}
    assert uv.lease({**running, "lease_until": "2026-09-27T04:30:00Z"}, NOW)["state"] == "stale"
    assert uv.lease({"state": "done", "lease_until": None}, NOW)["state"] == "none"


def test_worth_showing_keeps_warnings_and_ladders():
    assert uv.worth_showing({"level": "WARNING"}) and uv.worth_showing({"level": "INFO", "step_id": "ladders"})
    assert not uv.worth_showing({"level": "INFO", "step_id": "08"})


def test_merged_folds_repeated_rungs_newest_first():
    rows = [{"gate": "PLAN", "rung": "improve"}, {"gate": "PLAN", "rung": "improve"}, {"gate": "EYE", "rung": "x"}]
    got = uv.merged(rows)
    assert [(r["gate"], r["times"]) for r in got] == [("EYE", 1), ("PLAN", 2)]


def test_dq_flags_read_the_list():
    assert uv.dq_flags([{"shot": 5, "flags": ["blur"]}, {"shot": 6, "flags": []}, "junk"]) == {5: ["blur"]}
    assert uv.dq_flags(None) == {}


def test_slots_one_per_planned_shot():
    plan = {"shots": [{"index": "0"}, {"index": "1"}, "junk"]}
    assert uv.slots(plan, "waits") == [{"label": "T00", "reason": "waits"}, {"label": "T01", "reason": "waits"}]


def test_take_wait_names_the_failing_step():
    steps = [{"step_id": "08", "state": "running", "reason": ""},
             {"step_id": "09", "state": "failed", "reason": "REFUSED: the takes wait"}]
    assert uv.take_wait(steps) == "09 failed: REFUSED: the takes wait" and uv.take_wait([]) == "not shot yet"


def test_qc_line_counts_cuts_and_lines():
    qc = {"seconds": 160.25, "planned_cuts": [1, 2, 3], "missing_cuts": [2],
          "lines": [{"passed": True}, {"passed": False}], "lufs": -14.15, "lufs_ok": True}
    got = uv.qc_line(qc)
    assert got["cuts"] == "2/3" and got["heard"] == "1/2" and got["lufs_ok"] is True


def _gates():
    return [{"gate": "PLAN", "step": "02", "faults": 1, "shots": {2: []}, "kinds": [{"kind": "invented", "n": 1}]},
            {"gate": "EYE_PANELS", "step": "08", "faults": 17, "shots": {3: [], 11: [], "plan": []},
             "kinds": [{"kind": "framing", "n": 7}, {"kind": "posture", "n": 9}]}]


def test_holding_gate_is_the_current_steps_else_the_most_faults():
    assert uv.holding_gate({"step_id": "02"}, _gates())["gate"] == "PLAN"
    assert uv.holding_gate({"step_id": "12"}, _gates())["gate"] == "EYE_PANELS"
    assert uv.holding_gate({"step_id": "08"}, []) is None


def test_suggest_prefills_the_redo():
    got = uv.suggest({"step_id": "08"}, _gates(), "episode", "episodes/ep13")
    assert got["step_id"] == "08" and got["shots"] == [3, 11] and got["artefact"] == ""
    assert got["note"] == "EYE_PANELS: framing ×7 · posture ×9; shots 03, 11"
    one = uv.suggest({"step_id": "08"}, [{**_gates()[1], "shots": {4: []}}], "episode", "episodes/ep13")
    assert one["artefact"] == "episodes/ep13/storyboard/shot_04.png"
    assert uv.suggest({"step_id": "05"}, [], "episode", "x") == {"step_id": "05", "shots": [], "artefact": "", "note": ""}


def test_gate_steps_come_from_the_manifest():
    steps = uv.gate_steps("episode")
    assert steps["PLAN"] == "02" and steps["EYE_PANELS"] == "08" and uv.gate_steps("nowhere") == {}


def test_a_chip_without_a_row_reads_the_cursor():
    queued = {"step_id": "03", "state": "queued", "run_id": None, "ended_at": None, "glyph": "○", "css": "grey"}
    assert uv.chip_state(queued, {"state": "done", "step_id": "12"})["state"] == "done"
    assert uv.chip_state(queued, {"state": "running", "step_id": "02"})["state"] == "queued"
    ran = {**queued, "run_id": "r"}
    assert uv.chip_state(ran, {"state": "done", "step_id": "12"}) is ran


def test_book_files_are_book_relative(library):
    book = library / f"{CODEX}_a-book"
    got = uv.book_files(book, book / "episodes" / "ep04", "storyboard/shot_*.png")
    assert got == ["episodes/ep04/storyboard/shot_00.png", "episodes/ep04/storyboard/shot_01.png"]
    assert uv.book_files(None, None, "x") == []


def test_pictures_band_on_a_unit_with_nothing_on_disk(library):
    book = library / f"{CODEX}_a-book"
    got = uv.pictures_band(library, CODEX, "episode", book, book / "episodes" / "ep99", {}, [], [])
    assert got["panels"] == [] and got["takes"] == [] and got["slots"] == []
    assert uv.pictures_band(library, CODEX, "refs", book, book, {}, [], [])["panels"] == []


def test_master_band_plays_the_newest_iteration_without_qc(library):
    book = library / f"{CODEX}_a-book"
    thumbs = [{"kind": "master", "rel": "episodes/ep04/cut/master_iter2.mp4"}]
    got = uv.master_band(library, CODEX, "episode", book, book / "episodes" / "ep04", thumbs)
    assert got["rel"].endswith("master_iter2.mp4") and got["qc"] is None
    assert [i["name"] for i in got["iterations"]] == ["iter1"]
    assert uv.master_band(library, CODEX, "episode", book, book / "episodes" / "ep99", []) is None


def test_learning_band_caps_and_tallies():
    rows = [{"ts": "2026-09-27T04:00:00Z", "gate": "PLAN", "action": "improve",
             "note": "; ".join(f"battery at plan:     G-SIZE shot {i}: t" for i in range(60))}]
    got = uv.learning_band(rows)
    assert got["total"] == 1 and got["by_gate"] == {"PLAN": 1}
    assert len(got["rows"][0]["faults"]) == uv.FAULT_ITEMS and got["rows"][0]["more"] == 20


def test_a_read_connection_may_be_used_on_another_pool_thread(tmp_path):
    import sqlite3
    import threading

    from studio.command_center import app as cc_app
    sqlite3.connect(tmp_path / "t.db").close()
    conn, got = cc_app.readonly_factory(tmp_path / "t.db")(), []
    worker = threading.Thread(target=lambda: got.append(conn.execute("SELECT 1").fetchone()[0]))
    worker.start()
    worker.join()
    assert got == [1]
