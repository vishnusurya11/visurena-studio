"""The unit page's parsers (research G): every line the page shows is a Fault
serialised by one of two writers -- `verdict.summary()` (learning notes, events
detail) and `plan_check.py` (a refusal body, a battery fault's note).  One parser
per writer, composed.  Fixtures are real ep13/ep12 rows copied into
tests/fixtures/unit_parse/, trimmed.  No parser raises on junk: it returns a raw row."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from studio.command_center import unit_parse as up

FIX = Path(__file__).resolve().parent / "fixtures" / "unit_parse"
LIVE = "20260827135508__episode__20260927040215"
NOW = datetime(2026, 9, 27, 5, 0, tzinfo=timezone.utc)
PDT = timezone(timedelta(hours=-7))


def _jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (FIX / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def _json(name: str) -> dict:
    return json.loads((FIX / name).read_text(encoding="utf-8"))


# --- split_note / battery_item / learning_row ---


def test_split_note_keeps_semicolons_inside_a_note():
    note = _jsonl("learnings_ep13.jsonl")[2]["note"]          # the row-14 shape: "('slowly'); the owner's rule"
    faults, terminal = up.split_note(note)
    assert terminal == "defer" and all(f["kind"] == "battery" for f in faults)
    assert any("('slowly'); the owner's rule" in f["text"] for f in faults)
    assert len(faults) == note.count("battery at plan")


def test_split_note_reads_the_terminal():
    assert up.split_note("battery at plan -> defer") == ([{"kind": "battery", "where": "plan", "text": ""}], "defer")
    faults, terminal = up.split_note("invented at shot_02: place 'the crater rim' is not in the chapter -> keep_best")
    assert terminal == "keep_best" and faults[0]["where"] == "shot_02" and faults[0]["text"].startswith("place")


def test_split_note_on_the_bare_battery_rows():
    faults, _ = up.split_note(_jsonl("learnings_ep13.jsonl")[0]["note"])
    assert [f["text"] for f in faults] == [""] * 5


def test_split_note_tolerates_junk():
    assert up.split_note(None) == ([], "")
    assert up.split_note("no fault grammar here at all") == ([{"kind": "", "where": "", "text": "no fault grammar here at all"}], "")


@pytest.mark.parametrize("line, want", [
    ("    G-SIZE shot 4: a medium_close whose at_rest names no head fraction",
     {"code": "G-SIZE", "where": "shot 4", "text": "a medium_close whose at_rest names no head fraction"}),
    ("    G-FIRSTFRAME plan: median at_rest per shot is under the floor",
     {"code": "G-FIRSTFRAME", "where": "plan", "text": "median at_rest per shot is under the floor"}),
    ("    G-SYNC line 14: a dialogue line must be the first line on its shot",
     {"code": "G-SYNC", "where": "line 14", "text": "a dialogue line must be the first line on its shot"}),
    ("  advisory shot 12 M6: the LAST clause moves a face part too small to measure",
     {"code": "M6", "where": "shot 12", "text": "the LAST clause moves a face part too small to measure", "advisory": True}),
    ("  advisory: G-AIM shot 3: the aim is soft",
     {"code": "G-AIM", "where": "shot 3", "text": "the aim is soft", "advisory": True}),
    ("    not applicable: this book draws storyboard grids, not seq_boards sheets",
     {"code": "info", "where": "plan", "text": "not applicable: this book draws storyboard grids, not seq_boards sheets", "info": True}),
    ("CONTRACT shots.8: Value error, 'motion' asks for a slow shot",
     {"code": "CONTRACT", "where": "shots.8", "text": "Value error, 'motion' asks for a slow shot"}),
    ("CONTRACT OK: The Path Northward | 25 shots | 158s projected",
     {"code": "CONTRACT", "where": "plan", "text": "The Path Northward | 25 shots | 158s projected", "ok": True}),
    ("CONTRACT : a line's shot never precedes an earlier line's shot",
     {"code": "CONTRACT", "where": "plan", "text": "a line's shot never precedes an earlier line's shot"}),
    ("G-LIGHT      : clean", {"section": "G-LIGHT", "head": "clean"}),
    ("MOVES/SOURCE : 5", {"section": "MOVES/SOURCE", "head": "5"}),
])
def test_battery_item_reads_each_form(line, want):
    assert up.battery_item(line) == want


def test_battery_item_on_junk_is_none():
    assert up.battery_item("") is None and up.battery_item("   ...   ") is None


def test_learning_row_prefers_the_note_suffix():
    row = _jsonl("learnings_ep13.jsonl")[1]                   # action keep_best, note "-> defer"
    got = up.learning_row(row)
    assert (got["rung"], got["ended_as"], got["terminal"]) == ("keep_best", "defer", True)
    assert "note" not in got and got["faults"] == [{"code": "", "kind": "battery", "where": "plan", "text": ""}]


def test_learning_row_reads_a_full_refusal_row():
    got = up.learning_row(_jsonl("learnings_ep13.jsonl")[3])  # 11 KB: G-LIGHT hyphen, advisory M6, not applicable
    codes = up.count_codes(got["faults"])
    assert codes["G-SIZE"] >= 5 and "M6" in codes and "info" not in codes and "G-LIGHT" not in codes
    heads = [f for f in got["faults"] if f.get("head")]
    assert any(h["code"] == "G-LIGHT" for h in heads)
    assert all(f["code"] for f in got["faults"])
    assert len(got["digest"]) <= 160 and "G-SIZE" in got["digest"]


def test_learning_row_on_a_raw_row():
    assert up.learning_row({"raw": "not json"})["faults"] == [] and up.learning_row({})["rung"] is None


def test_count_codes_orders_by_count_and_skips_heads():
    faults = [{"code": "A"}, {"code": "B"}, {"code": "B"}, {"code": "S", "head": True}, {"code": "info", "info": True}]
    assert list(up.count_codes(faults).items()) == [("B", 2), ("A", 1)]


def test_digest_is_one_line_with_a_tail():
    counts = {f"C{i}": 10 - i for i in range(9)}
    line = up.digest(counts, n=3)
    assert line == "C0 10 · C1 9 · C2 8 · +6" and "\n" not in line


def test_clip_cuts_to_one_line():
    assert up.clip("a\nb") == "a" and up.clip("x" * 400).endswith("…") and len(up.clip("x" * 400)) == 160


# --- a refusal body ---


def test_refusal_sections_reads_a_full_body():
    sections = up.refusal_sections((FIX / "refusal.txt").read_text(encoding="utf-8"))
    names = [s["name"] for s in sections]
    assert names[:3] == ["CONTRACT", "G-LIGHT", "PLAN GATES"] and "TAKE BUILDER" in names and names[-1] == "VERDICT"
    gates = next(s for s in sections if s["name"] == "PLAN GATES")
    assert gates["count"] == 20 and gates["items"][0]["code"] == "G-FIRSTFRAME"
    assert not any(i["code"] == "" for s in sections for i in s["items"])


def test_a_head_with_a_list_counts_its_length():
    assert up.head_count("[(9, 'M2'), (21, 'M2')]") == 2
    assert up.head_count("20") == 20 and up.head_count("clean") == 0 and up.head_count("all bound") == 0
    assert up.head_count("[(13, 11.04)] (at 2.60 words/s, budget 8.0 s)") == 1


def test_refusal_counts_skip_info():
    sections = up.refusal_sections((FIX / "refusal.txt").read_text(encoding="utf-8"))
    counts = up.refusal_counts(sections)
    assert "info" not in counts and counts["G-SIZE"] >= 5 and counts["M6"] == 6 and counts["G-LIGHT"] == 3


def test_refusal_title_reads_the_contract_line():
    sections = up.refusal_sections((FIX / "refusal.txt").read_text(encoding="utf-8"))
    assert up.refusal_title(sections) == {"title": "The Destruction of Weybridge", "shots": 26,
                                          "projected_s": 157, "verdict": "REFUSED"}


def test_refusal_sections_on_junk_keep_raw_rows():
    assert up.refusal_sections("") == []
    got = up.refusal_sections("VERDICT      : REFUSED\n   ??? stray")
    assert got[0]["items"] == [{"code": "", "where": "", "text": "??? stray"}]


# --- passes ---


def _passes():
    return up.passes(_jsonl("events_ep13.jsonl"), _jsonl("learnings_ep13.jsonl"),
                     _jsonl("timing_ep13.jsonl"), LIVE, now=NOW, tz=PDT)


def test_passes_are_one_row_per_run_in_order():
    got = _passes()
    assert len(got) == 8 and got[-1]["run_id"] == LIVE
    assert [p["how"] for p in got[:3]] == ["failed", "deferred", "killed"]


def test_passes_close_an_open_run_at_the_next_start():
    got = _passes()
    assert got[2]["how"] == "killed" and got[2]["ended"] == got[3]["started"]


def test_passes_mark_the_live_run_running():
    live = _passes()[-1]
    assert live["how"] == "running" and live["ended_on"] == "08" and live["ended"] == NOW.isoformat()
    assert "02" in live["done"] and "07" in live["done"]


def test_passes_read_the_reason_class():
    got = _passes()
    assert [p["reason"] for p in got[-4:-1]] == ["deferred", "refused", "refused"]
    assert got[-2]["detail"].startswith("REFUSED: the takes wait on the panels")


def test_ladder_skips_pass_rows():
    rows = [{"ts": "2026-09-27T04:05:00Z", "gate": "PLAN", "action": "improve"},
            {"ts": "2026-09-27T04:06:00Z", "gate": "PLAN", "action": "pass"}]
    events = [{"event_ts": "2026-09-27T04:00:00Z", "step_id": "02", "event": "started", "run_id": "r", "detail": None},
              {"event_ts": "2026-09-27T04:10:00Z", "step_id": "02", "event": "completed", "run_id": "r", "detail": None}]
    assert up.passes(events, rows, [], None, now=NOW)[0]["ladder"] == ["PLAN:improve"]


def test_timing_joins_in_utc():
    events = [{"event_ts": "2026-09-27T04:00:00Z", "step_id": "08", "event": "started", "run_id": "r", "detail": None},
              {"event_ts": "2026-09-27T05:00:00Z", "step_id": "08", "event": "completed", "run_id": "r", "detail": None}]
    timing = [{"stage": "panels", "started": "2026-09-26T21:30:00", "seconds": 60.0},   # 04:30 UTC at -7h
              {"stage": "panels", "started": "2026-09-27T04:30:00", "seconds": 99.0}]   # 11:30 UTC: outside
    assert up.passes(events, [], timing, None, now=NOW, tz=PDT)[0]["script_s"] == 60.0


def test_passes_on_no_events():
    assert up.passes([], [], [], None) == []


def test_loop_state_sees_three_same_endings_in_the_last_four():
    got = up.loop_state(_passes())                            # 09 refused, 08 deferred, 09 refused, 09 refused
    assert got == {"looping": True, "step": "09", "reason": "refused", "n": 3, "of": 4}


def test_loop_state_on_the_last_three_alike():
    same = [{"how": "failed", "ended_on": "09", "reason": "refused"}] * 3
    assert up.loop_state(same)["looping"] is True


def test_loop_state_on_a_healthy_history():
    done = [{"how": "completed", "ended_on": "12", "reason": "done"}]
    assert up.loop_state(done)["looping"] is False
    fails = [{"how": "failed", "ended_on": s, "reason": "error"} for s in ("04", "06", "07")]
    assert up.loop_state(fails)["looping"] is False


def test_ended_on_counts_read_the_last_ten():
    got = up.ended_on_counts(_passes())
    assert got[0] == {"step": "09", "reason": "refused", "n": 3}


def test_gate_trend_is_the_last_measured_per_pass():
    passes = [{"started": "2026-09-27T01:00:00+00:00", "ended": "2026-09-27T02:00:00+00:00"},
              {"started": "2026-09-27T02:00:00+00:00", "ended": "2026-09-27T03:00:00+00:00"}]
    rows = [{"ts": "2026-09-27T01:10:00Z", "gate": "EYE_PANELS", "measured": 24.0},
            {"ts": "2026-09-27T01:20:00Z", "gate": "EYE_PANELS", "measured": 20.0},
            {"ts": "2026-09-27T02:30:00Z", "gate": "EYE_PANELS", "measured": 17.0},
            {"ts": "2026-09-27T02:40:00Z", "gate": "PLAN", "measured": None}]
    assert up.gate_trend(rows, passes) == [{"gate": "EYE_PANELS", "series": [20.0, 17.0], "direction": "improving"}]


def test_plan_titles_in_order_of_first_seen():
    assert up.plan_titles(_jsonl("learnings_ep13.jsonl")) == ["The Path Northward", "The Destruction of Weybridge"]


# --- faults per shot ---


def test_shot_faults_key_by_index():
    got = up.shot_faults(_json("eye_panels_ep13.json"))
    assert got[4] == [{"kind": "missing", "text": "sharp 0.58, ink 0.0, tiled 0.0, cast_faces 0 (panel_dq)", "n": 1}]
    assert {f["kind"] for f in got[11]} == {"framing", "posture"}


def test_repeated_kind_collapses():
    got = up.shot_faults(_json("eye_panels_ep12.json"))
    assert len(got[0]) == 1 and got[0][0]["kind"] == "landmark" and got[0][0]["n"] > 3


def test_non_shot_where_stays_a_string():
    got = up.shot_faults(_json("eye_master_ep12.json"))
    assert "master" in got and "artilleryman" in got
    takes = up.shot_faults(_json("eye_takes_ep12.json"))
    assert {f["kind"] for f in takes[19]} == {"cut", "jump", "cut-vote"}


def test_shot_faults_on_junk():
    assert up.shot_faults({}) == {} and up.shot_faults({"faults": ["x", {"kind": "k"}]}) == {"": [{"kind": "k", "text": "", "n": 1}]}


def test_fault_kinds_group_shots_under_each_kind():
    got = up.fault_kinds(_json("eye_panels_ep13.json"))
    framing = next(k for k in got if k["kind"] == "framing")
    assert framing["n"] == len([f for f in _json("eye_panels_ep13.json")["faults"] if f["kind"] == "framing"])
    assert framing["shots"] == sorted(framing["shots"]) and 3 in framing["shots"]


def test_panel_shot_reads_the_plan_row():
    plan = _json("plan_ep13.json")
    got = up.panel_shot("storyboard/shot_03.png", plan)
    assert got["index"] == 3 and got["size"] == "insert" and got["frame"].startswith("Insert")
    assert up.panel_shot("takes/r2v/T03.mp4", plan)["index"] == 3
    assert up.panel_shot("storyboard/shot_99.png", plan) is None and up.panel_shot("contact.png", plan) is None


# --- timing per step ---


def test_step_timing_groups_by_window():
    events = [{"event_ts": "2026-09-27T04:00:00Z", "step_id": "07", "event": "started", "run_id": "r", "detail": None},
              {"event_ts": "2026-09-27T04:10:00Z", "step_id": "07", "event": "completed", "run_id": "r", "detail": None},
              {"event_ts": "2026-09-27T04:10:01Z", "step_id": "08", "event": "started", "run_id": "r", "detail": None}]
    timing = [{"stage": "grids", "started": "2026-09-26T21:05:00", "seconds": 300.0},
              {"stage": "panels", "started": "2026-09-26T21:20:00", "seconds": 40.0}]
    got = {s["id"]: s for s in up.step_timing([{"id": "07"}, {"id": "08"}, {"id": "09"}], events, timing,
                                                now=NOW, tz=PDT)}
    assert got["07"]["runs"] == 1 and got["07"]["total_s"] == 300.0 and got["07"]["last_wall_s"] == 600.0
    assert got["08"]["scripts"] == {"panels": 1} and got["08"]["open"] is True
    assert got["09"]["runs"] == 0 and got["09"]["total_s"] == 0.0


def test_a_row_outside_every_window_is_counted_unplaced():
    events = [{"event_ts": "2026-09-27T04:00:00Z", "step_id": "07", "event": "started", "run_id": "r", "detail": None},
              {"event_ts": "2026-09-27T04:10:00Z", "step_id": "07", "event": "completed", "run_id": "r", "detail": None}]
    timing = [{"stage": "bind", "started": "2026-09-20T10:00:00", "seconds": 1.0}, {"raw": "junk"}]
    assert up.unplaced(events, timing, now=NOW, tz=PDT) == 2


def test_timing_by_stage_folds_rows():
    got = up.timing_by_stage(_jsonl("timing_ep13.jsonl"))
    assert sum(g["count"] for g in got) == 12 and got == sorted(got, key=lambda g: -g["total_s"])


# --- the log ---


def test_log_rows_summarise_a_refusal():
    rows = up.log_rows(_jsonl("log_ep13.jsonl"))
    refusal = next(r for r in rows if r["kind"] == "refusal")
    assert refusal["line"].startswith("REFUSED · How I Fell in with the Curate · ") and len(refusal["line"]) <= 160
    assert refusal["items"] and "msg" not in refusal


def test_plain_line_keeps_first_line():
    rows = up.log_rows([{"ts": "t", "level": "WARNING", "msg": "PLAN: measured 1.0 vs None -> improve\nmore"}, {"raw": "x"}])
    assert rows[0]["line"] == "PLAN: measured 1.0 vs None -> improve" and rows[1]["line"] == "x"


def test_dedupe_marks_still_and_gone():
    a = {"kind": "refusal", "items": [{"code": "G-SIZE", "where": "shot 4", "text": "t"},
                                      {"code": "G-AIM", "where": "shot 2", "text": "t"}]}
    b = {"kind": "refusal", "items": [{"code": "G-SIZE", "where": "shot 4", "text": "t"},
                                      {"code": "M2", "where": "shot 9", "text": "t"}]}
    got = up.dedupe_refusals([a, {"kind": "line"}, b])
    marks = {(i["code"], i["mark"]) for i in got[2]["items"]}
    assert marks == {("G-SIZE", "still ×2"), ("M2", "new")} and got[2]["gone"] == [{"code": "G-AIM", "where": "shot 2"}]
