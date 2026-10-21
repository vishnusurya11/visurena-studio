"""The common asserts (2026-10-21_ep02_proof DESIGN 3.1) and S0b's pre-registered outcome (R2).

Every assert reads the files a rehearsal leaves and returns ONE counted row of the section-5 schema;
a row whose evidence rests on a canned answer is `mechanism`, never `quality`.  S0b passes on a
named park, or on HELD_PUBLISH with every unresolved content refusal on the publish card AND a lock
that is not auto-clearable; HELD_PUBLISH with k > 0 unresolved refusals and an auto-clearable lock
is FAILING under Q6."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio.rehearsal import asserts


def write_rows(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def book_at(tmp_path: Path) -> tuple[Path, Path]:
    book = tmp_path / "library" / "9999_book"
    home = book / "episodes" / "ep02"
    home.mkdir(parents=True)
    return book, home


def test_a_row_carries_every_schema_key():
    r = asserts.row("A-real", True, ["tripwire.jsonl"])
    assert set(asserts.ROW_KEYS) <= set(r) and r["kind"] == "mechanism" and r["n_points"] == 1


def test_a_row_resting_on_a_canned_answer_is_mechanism_never_quality():
    r = asserts.row("graph", True, [], kind="quality", match_classes={"exact": 3, "canned": 1})
    assert r["kind"] == "mechanism"
    assert asserts.row("graph", True, [], kind="quality", match_classes={"exact": 3})["kind"] == "quality"


def test_caps_hold_when_every_counter_is_within_its_cap_table_row(tmp_path):
    book, home = book_at(tmp_path)
    (home / "attempts.json").write_text(json.dumps({"retakes": {"rounds": 2}, "relaunch.09": {"rounds": 3},
                                                   "plan.climbs": {"rounds": 2}, "wall.09": {"rounds": 8}}))
    assert asserts.a_caps(book, 2)["passed"] is True


def test_a_counter_past_its_cap_fails_and_is_named(tmp_path):
    book, home = book_at(tmp_path)
    (home / "attempts.json").write_text(json.dumps({"retakes": {"rounds": 3}}))
    write_rows(book / "autopilot" / "events.jsonl", [{"event": "engine_restart", "episode": 2}] * 3)
    r = asserts.a_caps(book, 2)
    assert r["passed"] is False and "retakes 3 > 2" in r["detail"] and "engine restarts 3 > 2" in r["detail"]


def test_a_finished_take_submitted_again_without_a_gate_retake_is_a_rerender():
    rows = [{"call": "prompt", "kind": "take", "index": 1, "ts": 1.0}, {"call": "prompt", "kind": "take", "index": 2, "ts": 2.0},
            {"call": "prompt", "kind": "take", "index": 1, "ts": 5.0}]
    assert asserts.a_norerender(rows, {"rounds": []}, fault_at=3.0, in_flight=None)["passed"] is False
    ladder = {"rounds": [{"at": 4.0, "faults": {"1": ["warp"]}}]}
    assert asserts.a_norerender(rows, ladder, fault_at=3.0, in_flight=None)["passed"] is True
    assert asserts.a_norerender(rows, {"rounds": []}, fault_at=3.0, in_flight=1)["passed"] is True   # the take in flight, once


def test_no_upload_means_uploads_unchanged_and_no_youtube_trip(tmp_path):
    book, _ = book_at(tmp_path)
    assert asserts.a_noupload(book, before=[], tripwire=[])["passed"] is True
    write_rows(book / "uploads.jsonl", [{"episode": 2, "privacy": "public", "video_id": "x"}])
    assert asserts.a_noupload(book, before=[], tripwire=[])["passed"] is False
    trip = [{"event": "socket.connect", "why": "www.googleapis.com:443"}]
    assert asserts.a_noupload(book, before=asserts.jsonl(book / "uploads.jsonl"), tripwire=trip)["passed"] is False


def test_the_ledger_is_kept_never_a_duration(tmp_path):
    book, home = book_at(tmp_path)
    write_rows(home / "drive.jsonl", [{"ts": "2026-10-21T10:00:00+00:00", "event": "start"},
                                      {"ts": "2026-10-21T10:10:00+00:00", "event": "end", "code": 0}])
    write_rows(home / "clock.jsonl", [{"started": 1792576800.0 + 5, "ended": 1792576800.0 + 590, "seconds": 585}])
    write_rows(home / "timing.jsonl", [{"stage": "step_09", "event": "started"}])
    good = asserts.a_ledger(home, steps_ran=["09"], spent=[0.0, 10.0, 10.0])
    assert good["passed"] is True and good["question"] == asserts.LEDGER_QUESTION
    assert asserts.a_ledger(home, steps_ran=["09", "10"], spent=[0.0])["passed"] is False      # no step_10 row
    assert asserts.a_ledger(home, steps_ran=["09"], spent=[10.0, 5.0])["passed"] is False      # spent went back


def test_a_named_terminal_has_a_state_a_reason_and_a_notify_line(tmp_path):
    book, _ = book_at(tmp_path)
    (book / "autopilot").mkdir()
    status = {"episode": {"n": 2, "state": "PARKED", "reason": "parked: engine"}}
    (book / "autopilot" / "status.json").write_text(json.dumps(status))
    write_rows(book / "autopilot" / "parked.jsonl", [{"episode": 2, "reason": "engine"}])
    assert asserts.a_named(book, 2, ["ep02 PARKED (engine) on abc; the series moves on"])["passed"] is True
    assert asserts.a_named(book, 2, [])["passed"] is False
    write_rows(book / "autopilot" / "parked.jsonl", [{"episode": 2, "reason": "a reason nobody wrote"}])
    assert asserts.a_named(book, 2, ["ep02 PARKED (a reason nobody wrote)"])["passed"] is False


def test_the_park_vocabulary_is_read_from_the_code():
    words = asserts.vocabulary()
    assert {"engine", "step_cap", "brain_exhausted", "over_budget", "youtube_token_expired"} <= words


def test_real_is_an_empty_tripwire_and_a_clean_guard():
    assert asserts.a_real([], [])["passed"] is True
    assert asserts.a_real([{"event": "open"}], [])["passed"] is False
    assert asserts.a_real([], ["REAL LIBRARY TOUCHED: x"])["passed"] is False
    assert asserts.a_real([{"event": "open"}], [], expect_trip=True)["passed"] is True


def test_honest_counts_answers_by_class_and_names_each_canned_consumer():
    log = [{"call": "prompt", "class": "exact", "prompt_id": "a"}, {"call": "prompt", "class": "canned", "prompt_id": "b"}]
    consumers = [{"prompt_id": "b", "ask": "panel_content", "caller": "studio.panel_checks.read"}]
    r = asserts.a_honest(log, consumers, shape="uncalibrated")
    assert r["match_classes"] == {"exact": 1, "canned": 1} and r["instrument_state"] == "shape: uncalibrated"
    assert "studio.panel_checks.read" in r["detail"] and r["kind"] == "mechanism"


def test_a_gate_that_passed_on_a_canned_reply_is_a_failing_q6_row():
    log = [{"call": "prompt", "class": "canned", "prompt_id": "b"}]
    consumers = [{"prompt_id": "b", "ask": "panel_content", "caller": "studio.panel_checks.read", "passed": True}]
    r = asserts.a_canned(log, consumers)
    assert r["passed"] is False and r["question"] == "Q6" and "panel_content" in r["detail"]
    consumers[0]["passed"] = False
    assert asserts.a_canned(log, consumers)["passed"] is True


def test_a_canned_reply_no_consumer_judged_cannot_be_proven_clean():
    log = [{"call": "prompt", "class": "canned", "prompt_id": "b"}]
    r = asserts.a_canned(log, [{"prompt_id": "b", "ask": "x", "caller": "y"}])
    assert r["passed"] is False and r["instrument_state"] == "unjoined"


def test_torn_passes_when_every_record_parses_or_the_resume_named_it(tmp_path):
    good, bad = tmp_path / "attempts.json", tmp_path / "clock.jsonl"
    good.write_text("{}")
    bad.write_text('{"run_id": "a"}\n{"run_')
    assert asserts.a_torn([good], resume_log="")["passed"] is True
    assert asserts.a_torn([good, bad], resume_log="")["passed"] is False
    assert asserts.a_torn([good, bad], resume_log="clock.jsonl is torn: rebuilt")["passed"] is True


@pytest.mark.parametrize("state,refusals,card,clearable,passed,word", [
    ("PARKED", [], "", False, True, "named park"),
    ("HELD_PUBLISH", ["G-PANEL_CONTENT ended flag"], "held: G-PANEL_CONTENT ended flag", False, True, "carried"),
    ("HELD_PUBLISH", ["G-PANEL_CONTENT ended flag"], "held", True, False, "FAILING"),
    ("HELD_PUBLISH", ["G-PANEL_CONTENT ended flag"], "held", False, False, "not carried"),
    ("HELD_PUBLISH", [], "held", True, False, "unregistered"),
    ("RUNNING", [], "", False, False, "no terminal"),
])
def test_s0b_has_one_pre_registered_correct_outcome(state, refusals, card, clearable, passed, word):
    r = asserts.s0b_outcome(state, "parked: voice" if state == "PARKED" else "", refusals, card, clearable)
    assert r["passed"] is passed and word in r["detail"] and r["question"] == "Q6"


def test_content_refusals_and_the_lock_are_read_by_the_real_publish_lock(tmp_path):
    home = tmp_path / "ep02"
    home.mkdir()
    row = {"step": "09", "gate": "G-NOT-A-REGISTRY-GATE", "action": "flag", "note": "two faces", "terminal": True}
    (home / "learnings.jsonl").write_text(json.dumps(row) + "\n")
    refusals, clearable = asserts.publish_refusals(home)
    assert refusals and refusals[0].startswith("G-NOT-A-REGISTRY-GATE") and clearable is False


# ---- the scenarios' own pre-registered checks ----------------------------------------------

def graph(seed: int) -> dict:
    return {"12": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}}}


def test_s0a_diffs_every_built_take_against_the_recorded_room_and_lists_the_unexplained(tmp_path):
    rec, book = tmp_path / "ep01", tmp_path / "library" / "b"
    room, built = rec / "takes" / "r2v", book / "episodes" / "ep01" / "takes" / "r2v"
    for folder in (room, built):
        folder.mkdir(parents=True)
        (folder / "shots.json").write_text(json.dumps([{"index": 0, "tries": 0}, {"index": 1, "tries": 0}]))
    for i, (old, new) in enumerate([(82000, 82000), (82001, 99999)]):
        (room / f"T{i:02d}.graph.json").write_text(json.dumps(graph(old)))
        (built / f"T{i:02d}.graph.json").write_text(json.dumps(graph(new)))
    rows = asserts.s0a_rows(book, recorded=rec, git=lambda *a: "")
    assert rows[0]["check"] == "S0a" and rows[0]["n_points"] == 2 and rows[0]["passed"] is False
    assert "1 unexplained over n=2" in rows[0]["detail"] and "noise_seed" in rows[0]["detail"]


def test_s0a_with_no_built_take_is_never_a_pass(tmp_path):
    rows = asserts.s0a_rows(tmp_path / "book", recorded=tmp_path / "ep01", git=lambda *a: "")
    assert rows[0]["passed"] is False and rows[0]["n_points"] == 0


def test_s0b_reads_the_status_the_events_the_notify_and_the_real_publish_lock(tmp_path):
    book, home = book_at(tmp_path)
    (book / "autopilot").mkdir()
    (book / "autopilot" / "status.json").write_text(json.dumps({"episode": {"n": 2, "state": "HELD_PUBLISH", "reason": "held"}}))
    learn = {"step": "09", "gate": "G-NOT-A-REGISTRY-GATE", "action": "flag", "note": "", "terminal": True}
    (home / "learnings.jsonl").write_text(json.dumps(learn) + "\n")
    rows = asserts.s0b_rows(book, tmp_path)
    assert rows[0]["passed"] is False and "not carried" in rows[0]["detail"]
    write_rows(tmp_path / "notify.jsonl", [{"text": "ep02 HELD: G-NOT-A-REGISTRY-GATE ended flag"}])
    assert asserts.s0b_rows(book, tmp_path)[0]["passed"] is True


def test_a_transient_error_is_resubmitted_once_and_a_fatal_one_never():
    log = [{"call": "prompt", "workflow": "t", "index": 3, "fault": "exec_error"},
           {"call": "prompt", "workflow": "t", "index": 3, "fault": None}, {"call": "prompt", "workflow": "t", "index": 4}]
    assert asserts.resubmits(log) == 1
    assert asserts.resubmits(log[:1]) == 0 and asserts.resubmits([]) == -1


def test_the_specific_checks_are_keyed_by_scenario(tmp_path):
    book, _ = book_at(tmp_path)
    write_rows(tmp_path / "engine_log.jsonl", [{"call": "prompt", "workflow": "t", "index": 3, "fault": "exec_fatal"}])
    assert asserts.specific("F16", tmp_path, book, {})[0]["passed"] is True
    assert asserts.specific("F10", tmp_path, book, {})[0]["passed"] is False
    assert asserts.specific("F2", tmp_path, book, {"drives_alive": [1, 2, 1]})[0]["passed"] is False
    write_rows(book / "autopilot" / "events.jsonl", [{"event": "stale_lock"}, {"event": "supervisor_died_at"}])
    assert asserts.specific("F4", tmp_path, book, {})[0]["passed"] is True
    assert asserts.specific("smoke", tmp_path, book, {}) == []
