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


def test_a_row_only_summed_into_its_step_wall_caps_no_rounds(tmp_path):
    """Window 3: every scenario failed A-caps on `lines 7 > 1`.  The `lines` row is `read: step`
    (stages.yaml: a wall, no reader of its rounds); say_lines' own TERMINAL_TRIES (8) gave l19 eight
    tries in 17.6 s.  A step-read row's `rounds` is no cap, so it never fails A-caps."""
    from studio import step_caps
    book, home = book_at(tmp_path)
    (home / "attempts.json").write_text(json.dumps({"lines": {"rounds": 7, "seconds": 17.6}}))
    assert asserts.a_caps(book, 2)["passed"] is True
    table = {"lines": step_caps.Cap("lines", "04", 1, "episode", 600.0, read="step"),
             "voice": step_caps.Cap("voice", "04", 2, "episode", 1800.0)}
    assert asserts.counter_faults({"lines": {"rounds": 7}, "voice": {"rounds": 3}}, table) == ["voice 3 > 2"]


def test_a_row_only_summed_into_its_step_wall_is_held_to_that_wall_by_its_seconds():
    """Window 3 review: ebfdb49 left five `read: step` rows with no check at all, so a runaway re-say
    loop passed A-caps.  Production cuts such a row by its seconds (say_lines.lines_wall_s), and the
    step wall is its rows' walls summed: a row past the whole step wall is a runaway."""
    from studio import step_caps
    table = {"say": step_caps.Cap("say", "04", 1, "episode", 900.0, read="step"),
             "lines": step_caps.Cap("lines", "04", 1, "episode", 600.0, read="step"),
             "voice": step_caps.Cap("voice", "04", 2, "episode", 1800.0)}
    assert asserts.counter_faults({"lines": {"rounds": 7, "seconds": 17.6}}, table) == []
    assert asserts.counter_faults({"lines": {"rounds": 900, "seconds": 3400.0}}, table) == \
        ["lines 3400 s > step 04 wall 3300 s"]


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


def test_an_unclassified_park_is_a_crash_never_a_named_stop(tmp_path):
    """S0a, 2026-10-21: `unclassified: FileNotFoundError ... plan.json` passed A-named; only S0a's own
    n=0 row caught the crash.  The classifier's 'I do not know' names nothing."""
    book, _ = book_at(tmp_path)
    (book / "autopilot").mkdir()
    status = {"episode": {"n": 2, "state": "PARKED", "reason": "unclassified: FileNotFoundError: plan.json"}}
    (book / "autopilot" / "status.json").write_text(json.dumps(status))
    r = asserts.a_named(book, 2, ["ep02 PARKED (unclassified)"])
    assert r["passed"] is False and "unclassified" in r["detail"]


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


def test_a_canned_reply_no_consumer_judged_is_an_instrument_failure_never_a_failed_pipeline_row():
    from scripts.proof import confidence
    log = [{"call": "prompt", "class": "canned", "prompt_id": "b"}, {"call": "prompt", "class": "canned", "prompt_id": "m"}]
    r = asserts.a_canned(log, [{"prompt_id": "b", "ask": "x", "caller": "y"}])     # m: a canned take no VL read
    assert r["instrument_state"] == "failed" and confidence.instrument_failed(r)
    assert "INSTRUMENT FAILED" in r["detail"] and "b" in r["detail"] and "m" in r["detail"]
    assert asserts.instrument_failed(r) and not asserts.instrument_failed(asserts.row("A-real", False, []))


def test_a_gate_that_passed_on_a_canned_reply_still_fails_when_another_is_unjoined():
    log = [{"call": "prompt", "class": "canned", "prompt_id": "b"}, {"call": "prompt", "class": "canned", "prompt_id": "m"}]
    r = asserts.a_canned(log, [{"prompt_id": "b", "ask": "panel_content", "caller": "y", "passed": True}])
    assert r["passed"] is False and not asserts.instrument_failed(r) and "panel_content" in r["detail"]


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


def test_the_headline_rows_standing_on_a_canned_answer_are_mechanism(tmp_path):
    rec, book = tmp_path / "ep01", tmp_path / "library" / "b"
    for folder in (rec / "takes" / "r2v", book / "episodes" / "ep01" / "takes" / "r2v"):
        folder.mkdir(parents=True)
        (folder / "T00.graph.json").write_text(json.dumps(graph(1)))
    rows = asserts.s0a_rows(book, recorded=rec, git=lambda *a: "", classes={"exact": 4, "canned": 1})
    assert rows[0]["kind"] == "mechanism" and rows[0]["match_classes"] == {"exact": 4, "canned": 1}
    assert asserts.s0a_rows(book, recorded=rec, git=lambda *a: "", classes={"exact": 4})[0]["kind"] == "quality"
    _, home = book_at(tmp_path / "s0b")
    book2 = home.parent.parent
    (book2 / "autopilot").mkdir()
    (book2 / "autopilot" / "status.json").write_text(json.dumps({"episode": {"n": 2, "state": "PARKED", "reason": "x"}}))
    write_rows(tmp_path / "engine_log.jsonl", [{"call": "prompt", "class": "canned", "prompt_id": "c"}])
    assert asserts.s0b_rows(book2, tmp_path)[0]["kind"] == "mechanism"


@pytest.mark.parametrize("classes", [{"exact": 3, "substituted": 1}, {"exact": 3, "worker_canned": 1},
                                     {"exact": 3, "sdk_canned": 1}, {"exact": 3, "sdk_scripted": 2},
                                     {"exact": 3, "sdk_substituted": 6}])
def test_a_row_resting_on_a_substituted_take_or_a_canned_worker_or_claude_answer_is_mechanism(classes):
    """AUDIT A2, A4: ep01's KEPT takes served to ep02's graphs, an empty detection, a silent transcript,
    a canned or scripted Claude reply: none of them is the real component answering this ask."""
    assert asserts.row("S0b", True, [], kind="quality", match_classes=classes)["kind"] == "mechanism"
    assert asserts.row("S0b", True, [], kind="quality", match_classes={"exact": 3, "sdk_exact": 2})["kind"] == "quality"


def test_the_run_classes_fold_the_workers_and_the_sdk_log_into_the_engines(tmp_path):
    write_rows(tmp_path / "engine_log.jsonl", [{"header": True}, {"call": "prompt", "class": "exact", "prompt_id": "a"}])
    write_rows(tmp_path / "workers.jsonl", [{"worker": "detect", "event": "answer", "label": "canned"},
                                            {"worker": "whisper", "event": "answer", "label": "exact"},
                                            {"worker": "detect", "event": "died", "line": 2}])
    write_rows(tmp_path / "sdk_log.jsonl", [{"n": 1, "label": "canned"}, {"n": 2, "label": "scripted"}])
    assert asserts.run_classes(tmp_path) == {"exact": 1, "worker_canned": 1, "worker_exact": 1, "sdk_canned": 1,
                                             "sdk_scripted": 1}


def test_a_scenario_row_that_read_an_empty_detection_never_counts_as_quality(tmp_path):
    """AUDIT A2's red test: every engine answer exact, one face detection a memo miss (`{"dets": {}}`)."""
    rec, book = tmp_path / "ep01", tmp_path / "library" / "b"
    for folder in (rec / "takes" / "r2v", book / "episodes" / "ep01" / "takes" / "r2v"):
        folder.mkdir(parents=True)
        (folder / "T00.graph.json").write_text(json.dumps(graph(1)))
    box = tmp_path / "box"
    write_rows(box / "engine_log.jsonl", [{"call": "prompt", "class": "exact", "prompt_id": "a"}])
    write_rows(box / "workers.jsonl", [{"worker": "detect", "event": "answer", "label": "canned"}])
    rows = asserts.s0a_rows(book, recorded=rec, git=lambda *a: "", classes=asserts.run_classes(box))
    assert rows[0]["passed"] is True and rows[0]["kind"] == "mechanism"


def test_s0b_takes_its_classes_from_the_engine_the_workers_and_the_sdk(tmp_path):
    _, home = book_at(tmp_path / "s0b")
    book = home.parent.parent
    (book / "autopilot").mkdir()
    (book / "autopilot" / "status.json").write_text(
        json.dumps({"episode": {"n": 2, "state": "PARKED", "reason": "escalated: EYE_TAKES"}}))
    write_rows(tmp_path / "engine_log.jsonl", [{"call": "prompt", "class": "exact", "prompt_id": "c"}])
    write_rows(tmp_path / "sdk_log.jsonl", [{"n": 1, "label": "scripted"}])
    row = asserts.s0b_rows(book, tmp_path)[0]
    assert row["kind"] == "mechanism" and row["match_classes"]["sdk_scripted"] == 1


@pytest.mark.parametrize("reason,passed", [("escalated: EYE_TAKES", True), ("speech_gap_rendered", True),
                                           ("parked: voice", True), ("split_voice", True),
                                           ("brain_exhausted", False), ("parked: tick_error", False),
                                           ("over_budget", False)])
def test_s0b_passes_on_a_park_only_when_a_content_or_voice_gate_parked_it(reason, passed):
    """AUDIT A4: a park caused by a memo miss or a harness fault must not score as the pre-registered
    outcome; DESIGN 3.2 names it: a content or voice gate PARKS with its reason named."""
    r = asserts.s0b_outcome("PARKED", reason, [], "", False)
    assert r["passed"] is passed and (passed or "not a content or voice gate" in r["detail"])


def test_a_take_in_flight_when_its_drive_died_may_render_once_more_after_the_death():
    rows = [{"call": "prompt", "kind": "take", "index": 1, "ts": "2026-10-21T10:00:01+00:00"},
            {"call": "prompt", "kind": "take", "index": 2, "ts": "2026-10-21T10:00:02+00:00"},
            {"call": "prompt", "kind": "take", "index": 2, "ts": "2026-10-21T10:00:09+00:00"}]
    death = asserts.epoch("2026-10-21T10:00:05+00:00")
    assert asserts.a_norerender(rows, {}, fault_at=0.0, in_flight=None)["passed"] is False
    assert asserts.a_norerender(rows, {}, fault_at=0.0, in_flight=None, deaths=[death])["passed"] is True
    twice = rows + [{"call": "prompt", "kind": "take", "index": 2, "ts": "2026-10-21T10:00:12+00:00"}]
    assert asserts.a_norerender(twice, {}, fault_at=0.0, in_flight=None, deaths=[death])["passed"] is False


def test_a_take_collected_before_the_death_and_rendered_again_after_it_is_a_rerender():
    rows = [{"call": "prompt", "kind": "take", "index": 2, "ts": 2.0}, {"call": "prompt", "kind": "take", "index": 2, "ts": 9.0}]
    lost = [{"take": 2, "video": "T02.mp4"}]                                    # in flight: saved once, after the resume
    kept = [{"take": 2, "video": "T02.mp4"}, {"take": 2, "video": "T02.mp4"}]   # finished, then rendered again
    assert asserts.a_norerender(rows, {}, 0.0, None, deaths=[5.0], collected=lost)["passed"] is True
    r = asserts.a_norerender(rows, {}, 0.0, None, deaths=[5.0], collected=kept)
    assert r["passed"] is False and "T02 saved x2" in r["detail"]
    named = {"rounds": [{"at": 1.0, "faults": {"2": ["warp"]}}]}
    assert asserts.a_norerender(rows, named, 0.0, None, deaths=[5.0], collected=kept)["passed"] is True


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


# ---- a status doc that never came, and a fault that never fired -------------------------------

def test_a_run_that_ends_with_no_status_doc_fails_named(tmp_path):
    book, _ = book_at(tmp_path)
    r = asserts.a_named(book, 2, ["ep02 PARKED (engine)"])
    assert r["passed"] is False and "no status" in r["detail"]


@pytest.mark.parametrize("planted, files, served", [
    ({"kind": "exec_error"}, {"engine_log.jsonl": [{"call": "prompt", "fault": "exec_error"}]}, True),
    ({"kind": "exec_error"}, {"engine_log.jsonl": [{"call": "prompt", "fault": None}]}, False),
    ({"kind": "rate_limit"}, {"sdk_log.jsonl": [{"n": 1, "label": "fault", "row": "rate_limit"}]}, True),
    ({"kind": "rate_limit"}, {"sdk_log.jsonl": [{"n": 1, "label": "canned"}]}, False),
    ({"kind": "worker_death"}, {"workers.jsonl": [{"worker": "whisper", "event": "died", "line": 2}]}, True),
    ({"kind": "worker_death"}, {}, False),
    ({"kind": "oauth"}, {"youtube.jsonl": [{"event": "invalid_grant", "call": "send"}]}, True),
    ({"kind": "oauth"}, {"youtube.jsonl": [{"event": "refused", "call": "send"}]}, False),
    ({"kind": "kill"}, {"kill.done": None}, True),
    ({"kind": "kill"}, {}, False),
])
def test_a_planted_fault_that_never_fired_fails_the_point(tmp_path, planted, files, served):
    for name, rows in files.items():
        (tmp_path / name).write_text("" if rows is None else "".join(json.dumps(r) + "\n" for r in rows))
    r = asserts.a_served(planted, tmp_path, {})
    assert r["check"] == "A-served" and r["passed"] is served, r["detail"]


def test_a_fault_with_nothing_to_serve_is_no_row():
    assert asserts.a_served({"kind": "none"}, Path("."), {}) is None


def test_a_commit_and_a_tear_are_served_by_what_was_planted(tmp_path):
    assert asserts.a_served({"kind": "commit"}, tmp_path, {"commits": ["abc"]})["passed"] is True
    assert asserts.a_served({"kind": "commit"}, tmp_path, {"commits": []})["passed"] is False
    assert asserts.a_served({"kind": "tear"}, tmp_path, {}, planted={"torn": "x", "kept": 3})["passed"] is True
    assert asserts.a_served({"kind": "tear"}, tmp_path, {}, planted={"torn": None})["passed"] is False


# ---- the pre-registered specific checks of 3.2 ------------------------------------------------

def status(book: Path, state: str, reason: str = "x") -> None:
    (book / "autopilot").mkdir(parents=True, exist_ok=True)
    (book / "autopilot" / "status.json").write_text(json.dumps({"episode": {"n": 1, "state": state, "reason": reason}}))


def take_rows(*faults_) -> list[dict]:
    return [{"call": "prompt", "workflow": "ref2v_take", "index": i, "fault": f} for i, f in faults_]


def test_f1_renders_the_take_in_flight_again_exactly_once(tmp_path):
    book, _ = book_at(tmp_path)
    write_rows(tmp_path / "engine_log.jsonl", take_rows((3, "crash"), (3, None), (4, None)))
    assert asserts.specific("F1", tmp_path, book, {})[0]["passed"] is True
    write_rows(tmp_path / "engine_log.jsonl", take_rows((3, "crash"), (4, None)))
    assert asserts.specific("F1", tmp_path, book, {})[0]["passed"] is False


def test_f1b_and_f9_park_on_the_engine_and_rerender_the_hung_take_at_most_once(tmp_path):
    book, _ = book_at(tmp_path)
    write_rows(tmp_path / "engine_log.jsonl", take_rows((3, "lost"), (3, None)))
    status(book, "PARKED", "engine: no answer after 2 restarts")
    assert asserts.specific("F1b", tmp_path, book, {})[0]["passed"] is True
    assert asserts.specific("F9", tmp_path, book, {})[0]["passed"] is True
    status(book, "HELD_PUBLISH")
    assert asserts.specific("F1b", tmp_path, book, {})[0]["passed"] is False
    write_rows(tmp_path / "engine_log.jsonl", take_rows((3, "hang"), (3, None), (3, None)))
    assert asserts.specific("F9", tmp_path, book, {})[0]["passed"] is False


def test_f13_retakes_the_corrupt_take_or_parks_named(tmp_path):
    book, _ = book_at(tmp_path)
    write_rows(tmp_path / "engine_log.jsonl", take_rows((2, "corrupt"), (2, None)))
    assert asserts.specific("F13", tmp_path, book, {})[0]["passed"] is True
    write_rows(tmp_path / "engine_log.jsonl", take_rows((2, "corrupt")))
    status(book, "HELD_PUBLISH")
    assert asserts.specific("F13", tmp_path, book, {})[0]["passed"] is False
    status(book, "PARKED", "take: refused")
    assert asserts.specific("F13", tmp_path, book, {})[0]["passed"] is True


def test_f3_submits_no_take(tmp_path):
    book, _ = book_at(tmp_path)
    write_rows(tmp_path / "engine_log.jsonl", [{"call": "prompt", "workflow": "tts", "fault": None}])
    assert asserts.specific("F3", tmp_path, book, {})[0]["passed"] is True
    write_rows(tmp_path / "engine_log.jsonl", take_rows((1, None)))
    assert asserts.specific("F3", tmp_path, book, {})[0]["passed"] is False


def test_f6_parks_on_the_token_without_an_upload_and_says_the_consent(tmp_path):
    book, _ = book_at(tmp_path)
    (tmp_path / "library").mkdir(exist_ok=True)
    (tmp_path / "library" / ".youtube_consent.json").write_text("{}")
    write_rows(tmp_path / "youtube.jsonl", [{"event": "invalid_grant", "call": "send"}])
    write_rows(tmp_path / "notify.jsonl", [{"text": "ep01: YouTube token refresh fails: open https://x , approve"}])
    status(book, "PARKED", "youtube_token_expired: run youtube_auth.py")
    assert asserts.specific("F6", tmp_path, book, {})[0]["passed"] is True
    write_rows(tmp_path / "youtube.jsonl", [{"event": "would_upload", "call": "send"}])
    assert asserts.specific("F6", tmp_path, book, {})[0]["passed"] is False


def test_f7_hands_over_and_the_resume_names_the_moved_code(tmp_path):
    book, home = book_at(tmp_path)
    (home.parent / "ep01").mkdir()
    (home.parent / "ep01" / "drive_run02.log").write_text("WARNING code moved mid-episode: started on a")
    assert asserts.specific("F7", tmp_path, book, {"handovers": ["def"]})[0]["passed"] is True
    assert asserts.specific("F7", tmp_path, book, {"handovers": []})[0]["passed"] is False
    write_rows(book / "autopilot" / "events.jsonl", [{"event": "code_moved_during_run", "episode": 1}] * 2)
    assert asserts.specific("F7b", tmp_path, book, {"handovers": ["def"]})[0]["passed"] is False


def test_f8_closes_the_window_and_submits_no_take(tmp_path):
    book, _ = book_at(tmp_path)
    home = book / "episodes" / "ep01"
    home.mkdir()
    from studio import repair_clock
    write_rows(home / "repair.jsonl", [{"opened_at": 1.0, "closed_by": repair_clock.UNBACKED}])
    write_rows(home / "drive.jsonl", [{"event": "end", "code": 2, "refused": "dry_check"}])
    status(book, "PARKED", "drive_refused")
    assert asserts.specific("F8", tmp_path, book, {})[0]["passed"] is True
    (home / "repair.json").write_text("{}")
    assert asserts.specific("F8", tmp_path, book, {})[0]["passed"] is False


def test_f15_serves_its_fault_and_never_retries_the_ask_past_its_cap(tmp_path):
    book, _ = book_at(tmp_path)
    write_rows(tmp_path / "sdk_log.jsonl", [{"n": 1, "label": "fault", "row": "rate_limit", "prompt_sha": "a"},
                                            {"n": 2, "label": "canned", "prompt_sha": "a"}])
    status(book, "PARKED", "brain: rate limited until 12:00")
    assert asserts.specific("F15", tmp_path, book, {})[0]["passed"] is True
    write_rows(tmp_path / "sdk_log.jsonl", [{"n": i, "label": "fault" if i == 1 else "canned", "prompt_sha": "a"}
                                            for i in range(1, 13)])
    assert asserts.specific("F15", tmp_path, book, {})[0]["passed"] is False


def test_f17_restarts_the_worker_within_its_spawns(tmp_path):
    book, _ = book_at(tmp_path)
    write_rows(tmp_path / "workers.jsonl", [{"worker": "whisper", "pid": 1, "event": "died", "line": 2},
                                            {"worker": "whisper", "pid": 2, "event": "answer", "line": 1}])
    assert asserts.specific("F17", tmp_path, book, {})[0]["passed"] is True
    write_rows(tmp_path / "workers.jsonl", [{"worker": "whisper", "pid": p, "event": "died", "line": 2} for p in (1, 2, 3)])
    assert asserts.specific("F17", tmp_path, book, {})[0]["passed"] is False
