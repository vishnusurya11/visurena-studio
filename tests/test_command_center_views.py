"""The board's view layer (decision 2026-09-25, C10): pure functions over the
rows the runners wrote, each returning what one template renders.  The rows
come from db.add_event's projection, never typed; the vocabulary is report D's
(glyph and colour per state, the one-glance rule); every path is book-relative."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from command_center_fixtures import CODEX, RUN, make_library, make_logs, seed
from studio import db, registry
from studio.command_center import views


@pytest.fixture()
def library(tmp_path, monkeypatch):
    return make_library(tmp_path, monkeypatch)


@pytest.fixture()
def logs(tmp_path):
    return make_logs(tmp_path)


@pytest.fixture()
def conn(tmp_path, library):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "A Book", codex_id=CODEX)
    seed(connection, library)
    return connection


def test_the_glyphs_are_ds_vocabulary():
    assert [views.glyph(s) for s in ("queued", "blocked", "running", "done", "deferred",
                                     "failed", "escalated", "held", "stale")] == list("○◌●✓↩✕✋⏸~")
    assert views.glyph("done", flags=3) == "⚑3"


def test_the_colour_is_who_it_needs():
    assert views.colour_class("failed") == views.colour_class("stale") == "red"
    assert views.colour_class("escalated") == "black"
    assert views.colour_class("flagged") == "amber" and views.colour_class("deferred") == "purple"
    assert views.colour_class("running") == "blue" and views.colour_class("done") == "green"
    assert views.colour_class("queued") == views.colour_class("blocked") == "grey"
    assert views.display_state("done", 2) == "flagged" and views.display_state("done", 0) == "done"


def test_the_floor_is_the_running_gpu_row_and_the_next_four(conn):
    floor = views.floor(conn)
    (row,) = floor["running"]
    assert (row["unit"], row["step_id"], row["step_name"], row["progress"]) == ("ep04", "09", "shoot", "18/25")
    assert row["run_id"] == RUN and row["started_at"] and row["gpu"] == 1
    assert [r["unit"] for r in floor["next"]] == ["ep06"]
    for n in range(10, 16):
        db.upsert_work_order(conn, CODEX, "episode", f"ep{n}", state="queued", sequence=n)
    assert len(views.floor(conn)["next"]) == 4


def test_attention_is_what_needs_a_person_oldest_first(conn):
    got = views.attention(conn)
    assert [(r["unit"], r["state"], r["glyph"], r["css"]) for r in got] == [
        ("ep05", "failed", "✕", "red"), ("ep07", "deferred", "↩", "purple")]
    assert got[0]["detail"] == "KeyError"


def test_lanes_count_every_registered_department(conn):
    lanes = views.lanes(conn)
    assert [l["stage"] for l in lanes] == registry.stage_names()
    episode = next(l for l in lanes if l["stage"] == "episode")
    assert episode["total"] == 5
    assert episode["counts"] == {"running": 1, "failed": 1, "deferred": 1, "flagged": 1, "queued": 1}
    assert [r["unit"] for r in episode["rows"]] == ["ep05", "ep04", "ep07", "ep03", "ep06"]
    assert ("⚑", 1) in episode["tally"] and ("●", 1) in episode["tally"]


def test_lanes_show_six_rows_at_most(conn):
    for n in range(10, 20):
        db.upsert_work_order(conn, CODEX, "episode", f"ep{n}", state="queued", sequence=n)
    episode = next(l for l in views.lanes(conn) if l["stage"] == "episode")
    assert len(episode["rows"]) == 6 and episode["total"] == 15


def test_today_lists_the_steps_that_ended_today_newest_first(conn):
    rows = views.today(conn)
    assert rows and rows[0]["ended_at"] >= rows[-1]["ended_at"]
    assert {(r["stage"], r["unit"]) for r in rows} >= {("episode", "ep04"), ("episode", "ep05"), ("refs", "main")}
    assert all(r["ended_at"][:10] == datetime.now(timezone.utc).strftime("%Y-%m-%d") for r in rows)
    assert rows[0]["step_name"] and rows[0]["state"]


def test_today_is_capped_at_thirty(conn):
    for n in range(40):
        db.add_event(conn, CODEX, "analysis", "01", "completed", run_id=f"a{n}", unit=f"u{n}")
    assert len(views.today(conn)) == 30


def test_the_gate_order_is_gates_yaml_with_unknown_gates_appended():
    assert views.gate_order("episode")[:3] == ["PLAN", "LAYOUT", "EYE_PANELS"]
    assert views.gate_order("refs") == ["LOOK"]
    assert views.gate_order("analysis") == []
    strip = views.verdict_strip({"EYE_TAKES": {"word": "flagged", "faults": 5},
                                 "PLAN": {"word": "APPROVE", "faults": 0}, "ODD": {"word": "pass"}},
                                ["PLAN", "EYE_PANELS", "EYE_TAKES"])
    assert [(c["gate"], c["glyph"]) for c in strip] == [
        ("PLAN", "✓"), ("EYE_PANELS", "○"), ("EYE_TAKES", "⚑5"), ("ODD", "✓")]


def test_a_departments_rows_carry_their_verdict_strip_and_sort_by_attention(conn):
    dept = views.department(conn, "episode")
    assert [r["unit"] for r in dept["rows"]] == ["ep05", "ep04", "ep07", "ep03", "ep06"]
    ep04 = dept["rows"][1]
    assert [c["gate"] for c in ep04["strip"]] == views.gate_order("episode")
    assert ep04["strip"][0] == {"gate": "PLAN", "word": "APPROVE", "glyph": "⚑1", "css": "amber",
                                "by": "judge:plan@1", "faults": 1, "sha8": ep04["verdicts"]["PLAN"]["sha8"],
                                "path": "episodes/ep04/plan.verdict.json", "terminal": ""}
    assert dept["gates"] == views.gate_order("episode") and dept["books"] == {CODEX: "A Book"}


def test_a_department_filters_by_book_and_state(conn):
    assert [r["unit"] for r in views.department(conn, "episode", state="failed")["rows"]] == ["ep05"]
    assert [r["unit"] for r in views.department(conn, "episode", state="flagged")["rows"]] == ["ep03"]
    assert views.department(conn, "episode", book="20260901000009")["rows"] == []
    with pytest.raises(ValueError):
        views.department(conn, "publish")


def test_a_unit_lists_its_steps_in_registry_order(conn, library, logs):
    unit = views.unit(conn, library, CODEX, "episode", "ep04", logs=logs)
    steps = unit["steps"]
    assert [s["step_id"] for s in steps] == [e["id"] for e in registry.steps("episode")]
    by_id = {s["step_id"]: s["state"] for s in steps}
    assert (by_id["01"], by_id["02"], by_id["03"], by_id["09"]) == ("done", "done", "queued", "running")
    assert steps[1]["verdict_by"] == "judge:plan@1" and steps[3]["state"] == "queued"
    assert unit["running"] is True and unit["row"]["unit"] == "ep04"
    assert views.unit(conn, library, CODEX, "episode", "ep99", logs=logs) is None


def test_a_units_thumbnails_are_the_files_the_steps_wrote(conn, library, logs):
    thumbs = views.thumbnails(library / f"{CODEX}_a-book" / "episodes" / "ep04", "episode", CODEX)
    assert [(t["kind"], t["rel"]) for t in thumbs] == [
        ("panels", "episodes/ep04/storyboard/shot_00.png"), ("panels", "episodes/ep04/storyboard/shot_01.png"),
        ("takes", "episodes/ep04/reports/strip_T00_T05.png"), ("master", "episodes/ep04/cut/master_iter2.mp4")]
    assert thumbs[0]["url"] == f"/lib/{CODEX}/episodes/ep04/storyboard/shot_00.png"
    assert views.thumbnails(library / f"{CODEX}_a-book" / "refs", "refs", CODEX) == []


def test_a_units_tails_are_bounded(conn, library, logs):
    unit = views.unit(conn, library, CODEX, "episode", "ep04", logs=logs)
    assert len(unit["learnings"]) == 8 and unit["learnings"][-1]["attempt"] == 9
    assert [l["level"] for l in unit["log"]] == ["WARNING", "ERROR"]
    assert unit["log_name"] == f"{RUN}.log"
    assert [t["stage"] for t in unit["timing"]] == ["plan", "qc"]
    assert unit["deliverable"] is None


def test_the_log_tail_falls_back_to_the_newest_log_and_reads_the_last_64k(conn, logs):
    folder = logs / CODEX / "episode"
    name, rows = views.log_tail(folder, "no-such-run")
    assert name == f"{CODEX}__episode__20260926090000.log" and rows[0]["msg"] == "newer run"
    big = folder / f"{CODEX}__episode__20260926100000.log"
    big.write_text("".join('{"level": "WARNING", "msg": "%d"}\n' % i for i in range(5000)), encoding="utf-8")
    name, rows = views.log_tail(folder, "20260926100000")
    assert name == big.name and len(rows) == 20 and rows[-1]["msg"] == "4999"
    assert views.log_tail(logs / "nowhere", None) == (None, [])


def test_a_units_deliverable_is_a_lib_url_when_the_file_exists(conn, library, logs):
    db.upsert_work_order(conn, CODEX, "episode", "ep04", deliverable="episodes/ep04/cut/master_iter2.mp4")
    unit = views.unit(conn, library, CODEX, "episode", "ep04", logs=logs)
    assert unit["deliverable"] == {"rel": "episodes/ep04/cut/master_iter2.mp4", "exists": True,
                                   "url": f"/lib/{CODEX}/episodes/ep04/cut/master_iter2.mp4"}


def test_a_book_is_units_across_stages_down(conn, library):
    book = views.book(conn, library, CODEX)
    assert book["name"] == "A Book" and book["stages"] == registry.stage_names()
    assert book["units"] == ["main", "ep03", "ep04", "ep05", "ep06", "ep07"]
    assert book["cells"]["episode"]["ep04"]["glyph"] == "●"
    assert book["cells"]["refs"]["main"]["glyph"] == "✓" and "ep04" not in book["cells"]["refs"]
    assert views.book(conn, library, "20260901000009") is None


def test_a_books_published_column_names_its_source(conn, library):
    db.upsert_work_order(conn, CODEX, "publish", "ep04", state="done")
    published = views.book(conn, library, CODEX)["published"]
    assert published["ep04"] == "row" and published["ep03"] == "file"
    assert "ep05" not in published
