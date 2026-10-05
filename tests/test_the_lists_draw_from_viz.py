"""viz.py (panel ruling 4.4, 4.5, 4.8, 4.9): the lists' and Home's pictures and
charts as pure functions -- gate chips by severity with a capped count, the
department's state groups, GPU spans paired from events, the day columns with
today's ceiling at the hours elapsed, tick labels kept clear of now, a
sparkline, the burn line -- plus the posters a tile opens in the Viewer.
Nothing here touches a GPU, a model or a paid API."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from studio.command_center import viz

UTC = timezone.utc


def chip(gate, css, faults=0, word=""):
    return {"gate": gate, "css": css, "faults": faults, "word": word, "glyph": "⚑", "by": ""}


# --- chips ---


def test_a_count_over_the_cap_reads_99_plus():
    assert viz.cap(531) == "99+" and viz.cap(99) == "99" and viz.cap(0) == ""


def test_gate_chips_keep_only_non_pass_gates_failures_first():
    strip = [chip("PLAN", "green", word="pass"), chip("EYE_PANELS", "amber", 531, "flagged"),
             chip("MASTER", "red", word="reject"), chip("EYE_TAKES", "amber", 2), chip("QC", "grey")]
    out = viz.gate_chips(strip)
    assert [c["gate"] for c in out] == ["MASTER", "EYE_PANELS", "EYE_TAKES"]
    assert out[1]["count"] == "99+" and out[1]["label"] == "panels"
    assert out[1]["title"] == "531 panels faults, flagged"


def test_a_chip_title_names_one_fault_in_the_singular():
    assert viz.chip_title("takes", 1, "") == "1 takes fault"
    assert viz.chip_title("master", 0, "reject") == "master: reject"


# --- the department's state groups ---


def row(unit, shown):
    return {"unit": unit, "shown": shown}


def test_rows_group_running_needs_you_queued_blocked_done_in_that_order():
    rows = [row("a", "done"), row("b", "flagged"), row("c", "running"), row("d", "queued"),
            row("e", "blocked"), row("f", "failed")]
    groups = viz.state_groups(rows)
    assert [g["key"] for g in groups] == ["running", "needs", "queued", "blocked", "done"]
    assert [r["unit"] for r in groups[1]["rows"]] == ["b", "f"]


def test_done_starts_collapsed_and_every_other_group_open():
    groups = viz.state_groups([row("a", "done"), row("c", "running")])
    assert {g["key"]: g["open"] for g in groups} == {"running": True, "done": False}


def test_a_state_outside_the_groups_falls_into_needs_you_or_queued():
    assert viz.group_of("escalated") == "needs" and viz.group_of("held") == "blocked"
    assert viz.group_of("skipped") == "done"


# --- spans from events ---


def ev(ts, step, event, run="r1"):
    return {"event_ts": ts, "step_id": step, "event": event, "run_id": run}


def test_a_span_pairs_a_start_with_its_end_in_the_same_run():
    rows = [ev("2026-10-04T10:00:00Z", "09", "started"), ev("2026-10-04T10:00:00Z", "02", "started", "r2"),
            ev("2026-10-04T11:00:00Z", "09", "failed"), ev("2026-10-04T10:30:00Z", "02", "completed", "r2")]
    spans = viz.spans(rows, now=0)
    assert ("09", 3600.0, "burn") in [(s["step"], s["end"] - s["start"], s["kind"]) for s in spans]
    assert ("02", 1800.0, "ok") in [(s["step"], s["end"] - s["start"], s["kind"]) for s in spans]


def test_an_open_start_of_the_newest_run_is_live_until_now():
    now = datetime(2026, 10, 4, 12, tzinfo=UTC).timestamp()
    spans = viz.spans([ev("2026-10-04T11:30:00Z", "08", "started")], now=now, live_runs={"r1"})
    assert spans == [{"step": "08", "start": now - 1800, "end": now, "kind": "live"}]


def test_an_open_start_of_a_dead_run_is_not_counted():
    assert viz.spans([ev("2026-10-04T11:30:00Z", "08", "started")], now=1e10, live_runs=set()) == []


def test_day_totals_put_hours_on_the_local_day_the_step_started():
    now = datetime(2026, 10, 4, 12, tzinfo=UTC).timestamp()
    spans = [{"step": "09", "start": now - 3600, "end": now, "kind": "burn"},
             {"step": "02", "start": now - 86400, "end": now - 86400 + 7200, "kind": "ok"}]
    days = viz.day_totals(spans, now, days=2, tz=UTC)
    assert [(d["ok"], d["burn"], d["today"]) for d in days] == [(2.0, 0.0, False), (0.0, 1.0, True)]


def test_steps_rank_by_hours_burned_with_their_share():
    spans = [{"step": "09", "start": 0, "end": 7200, "kind": "burn"},
             {"step": "09", "start": 0, "end": 3600, "kind": "ok"},
             {"step": "02", "start": 0, "end": 3600, "kind": "burn"}]
    out = viz.step_burn(spans)
    assert [(s["step"], s["burn"], s["total"], s["share"]) for s in out] == [("09", 2.0, 3.0, 67), ("02", 1.0, 1.0, 100)]


def test_the_burn_line_names_the_lever():
    days = [{"ok": 41.0, "burn": 34.0, "live": 0.0}]
    steps = [{"step": "09", "name": "shoot", "burn": 21.0, "total": 38.1, "share": 55}]
    assert viz.burn_line(days, steps) == "34 of 75 GPU-h burned · lever: 09 shoot 55 %"
    assert viz.burn_line([{"ok": 0.0, "burn": 0.0, "live": 0.0}], []) == ""


# --- the column chart ---


def test_columns_carry_keyed_ids_and_stack_ok_live_burn_bottom_up():
    days = [{"key": "2026-10-03", "label": "Sat 3", "ok": 12.0, "burn": 6.0, "live": 0.0, "today": False}]
    chart = viz.column_chart(days, elapsed_h=10, width=200, height=120)
    col = chart["cols"][0]
    assert col["id"] == "went-2026-10-03" and [s["kind"] for s in col["segs"]] == ["ok", "burn"]
    assert col["segs"][0]["y"] > col["segs"][1]["y"] and col["ceiling"] is None


def test_todays_column_is_drawn_under_an_elapsed_so_far_ceiling():
    days = [{"key": "2026-10-04", "label": "today", "ok": 1.0, "burn": 0.0, "live": 0.5, "today": True}]
    chart = viz.column_chart(days, elapsed_h=12, width=200, height=120)
    assert chart["cols"][0]["ceiling"] == pytest.approx(chart["y"](12))


def test_a_tick_label_within_36_px_of_now_is_dropped():
    ticks = [{"x": 0, "label": "19:00"}, {"x": 105, "label": "20:00"}, {"x": 210, "label": "21:00"}]
    assert [t["label"] for t in viz.clear_of_now(ticks, now_x=80)] == ["19:00", "21:00"]


def test_a_sparkline_runs_from_left_to_right_and_scales_to_the_max():
    d = viz.spark([0, 12, 24], width=100, height=20, vmax=24)
    assert d.startswith("M0.0 22.0") and d.endswith("L100.0 2.0")
    assert viz.spark([], 100, 20, 24) == ""


# --- posters ---


def test_a_poster_prefers_the_pipeline_poster_then_a_middle_panel(tmp_path):
    home = tmp_path / "20260901000001_a" / "episodes" / "ep04"
    (home / "storyboard").mkdir(parents=True)
    for i in range(5):
        (home / "storyboard" / f"shot_{i:02d}.png").write_bytes(b"x")
    assert viz.poster_file(home).name == "shot_02.png"
    (home / "poster.jpg").write_bytes(b"x")
    assert viz.poster_file(home).name == "poster.jpg"


def test_a_unit_with_no_picture_has_no_poster(tmp_path):
    assert viz.poster_file(tmp_path / "nothing") is None


def test_a_poster_is_a_viewer_opener_with_a_thumb_and_the_full_file(tmp_path):
    codex = "20260901000001"
    home = tmp_path / f"{codex}_a" / "episodes" / "ep04" / "storyboard"
    home.mkdir(parents=True)
    (home / "shot_00.png").write_bytes(b"x")
    p = viz.poster(tmp_path, codex, "episodes/ep04", 320)
    assert p["rel"] == "episodes/ep04/storyboard/shot_00.png"
    assert p["thumb"].startswith(f"/thumb/{codex}/320/episodes/ep04/storyboard/shot_00.png?v=")
    assert p["src"] == f"/lib/{codex}/episodes/ep04/storyboard/shot_00.png"
    assert viz.poster(tmp_path, codex, None, 320) is None
