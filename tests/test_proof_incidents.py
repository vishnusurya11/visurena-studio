"""The incident tally (DESIGN 2026-10-21_ep02_proof 4.5; package P2).

Error class, step and park reason are tallied from NAMED records of an episode (drive.jsonl,
drive_run<NN>.log / drive_launch<NN>.log probed by number, the book's autopilot/events.jsonl
and parked.jsonl), one file at a time, never a walk.  Each class maps to a scenario id in
scripts/proof/incidents_map.yaml or is listed UNCOVERED.  The fixtures are copies of Jekyll
ep01's own drive.jsonl, the head and tail of drive_run02.log and drive_run08.log, and a few
real rows of the book's events.jsonl."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from studio.rehearsal import incidents

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "proof" / "incidents" / "jekyll"
MAP = Path(__file__).resolve().parents[1] / "scripts" / "proof" / "incidents_map.yaml"


@pytest.fixture
def book(tmp_path):
    dest = tmp_path / "library" / "jekyll"
    shutil.copytree(FIXTURE, dest)
    return dest


@pytest.fixture
def rules():
    return incidents.load_rules(MAP)


def test_the_ep01_drive_ledger_reads_21_starts_17_ends_and_the_named_outcomes(book):
    summary = incidents.drive_summary(incidents.read_rows(book / "episodes" / "ep01" / "drive.jsonl"))
    assert (summary["start"], summary["end"]) == (21, 17)
    assert summary["outcomes"]["refused|-|RuntimeError"] == 6
    assert summary["outcomes"]["failed|11|-"] == 1
    assert summary["outcomes"]["failed|13|RuntimeError"] == 1
    assert summary["outcomes"]["escalated|13|-"] == 2


def test_a_start_with_no_end_before_the_next_start_is_a_drive_that_died(book):
    rows = incidents.read_rows(book / "episodes" / "ep01" / "drive.jsonl")
    died = incidents.died_runs(rows, "jekyll/episodes/ep01/drive.jsonl")
    assert len(died) == 21 - 17
    assert all(i["text"].startswith("drive_died") and i["kind"] == "drive" for i in died)


def test_run_logs_are_probed_by_number_and_stop_at_the_first_gap(tmp_path):
    for n in (1, 2, 4):
        (tmp_path / f"drive_run{n:02d}.log").write_text("x\n", encoding="utf-8")
    assert [p.name for p in incidents.numbered(tmp_path, "drive_run")] == ["drive_run01.log", "drive_run02.log"]


def test_a_log_that_stops_mid_run_is_cut_off_never_an_unclassified_line(book, rules):
    found = incidents.log_incident(book / "episodes" / "ep01" / "drive_run03.log", book.parent)
    assert found["text"].startswith("log_cut_off")
    assert incidents.classify(found, rules) == ("log_cut_off", "F2")


def test_a_standing_approval_hold_is_the_held_publish_class(book, rules):
    found = incidents.log_incident(book / "episodes" / "ep01" / "drive_run01.log", book.parent)
    assert incidents.classify(found, rules) == ("held_publish", "S0a")


def test_the_ffmpeg_bad_take_death_is_read_from_drive_run02_at_step_09(book, rules):
    found = incidents.log_incident(book / "episodes" / "ep01" / "drive_run02.log", book.parent)
    assert found["step"] == "09"
    assert "CalledProcessError" in found["text"] and "ffmpeg" in found["text"]
    assert incidents.classify(found, rules) == ("ffmpeg_bad_take", "F13")


def test_the_book_json_precondition_death_is_read_from_drive_run08_at_step_13(book, rules):
    found = incidents.log_incident(book / "episodes" / "ep01" / "drive_run08.log", book.parent)
    assert found["step"] == "13"
    assert incidents.classify(found, rules) == ("book_json_precondition", "F14")


def test_a_completed_log_is_no_incident(tmp_path):
    log = tmp_path / "drive_run01.log"
    log.write_text("--- step 13 (publish) | x ---\n=== EPISODE completed | x ===\n", encoding="utf-8")
    assert incidents.log_incident(log, tmp_path) is None


def test_only_the_episodes_own_fault_events_are_read(book):
    rows = incidents.read_rows(book / "autopilot" / "events.jsonl")
    mine = incidents.episode_events(rows, 1, "jekyll/autopilot/events.jsonl")
    assert mine and all(i["kind"] == "event" for i in mine)
    assert not any("launch" in i["text"] or "code_moved" in i["text"] for i in mine)
    assert len(mine) < len(incidents.episode_events(rows, 1, "x") + incidents.episode_events(rows, 2, "x"))


def test_an_unknown_text_is_an_uncovered_class_named_from_its_words(rules):
    found = {"kind": "event", "step": None, "text": "brain unclassified: KeyError: 'host' at 12:30", "source": "s"}
    cid, scenario = incidents.classify(found, rules)
    assert scenario == "UNCOVERED"
    assert cid == "event:brain unclassified: KeyError: 'host' at #:#"


def test_every_rule_names_a_scenario_of_the_design_or_uncovered(rules):
    assert rules and all(r["scenario"] in incidents.SCENARIOS for r in rules)
    assert len({r["id"] for r in rules}) == len(rules)


def test_the_tally_counts_classes_recorded_mapped_and_uncovered(book, rules):
    found = incidents.episode_incidents(book, 1, book.parent)
    out = incidents.tally(found["incidents"], rules)
    assert out["recorded"] == len(out["classes"])
    assert out["mapped"] + len(out["uncovered"]) == out["recorded"]
    assert out["classes"]["ffmpeg_bad_take"]["steps"] == {"09": 1}
    assert out["classes"]["drive_died"]["count"] == 4
    assert set(out["uncovered"]) == {c for c, v in out["classes"].items() if v["scenario"] == "UNCOVERED"}


def test_an_episode_read_names_every_file_it_opened_and_every_named_file_absent(book):
    found = incidents.episode_incidents(book, 1, book.parent)
    assert "jekyll/episodes/ep01/drive.jsonl" in found["sources"]
    assert "jekyll/episodes/ep01/drive_run08.log" in found["sources"]
    assert "jekyll/autopilot/parked.jsonl" in found["sources"]
    assert "jekyll/episodes/ep01/drive_launch01.log" in found["missing"]
    assert all(not Path(s).is_absolute() for s in found["sources"] + found["missing"])


def test_a_parked_row_counts_its_reason(book, rules):
    (book / "autopilot" / "parked.jsonl").write_text(
        json.dumps({"episode": 1, "reason": "youtube_token_expired: run it"}) + "\n", encoding="utf-8")
    found = incidents.episode_incidents(book, 1, book.parent)
    out = incidents.tally(found["incidents"], rules)
    assert out["classes"]["oauth_expired"]["scenario"] == "F6"
    assert out["park_reasons"]["youtube_token_expired: run it"] == 1


def test_a_torn_jsonl_line_is_counted_never_a_crash(tmp_path):
    path = tmp_path / "drive.jsonl"
    path.write_text('{"event": "start"}\n{"event": "en\n', encoding="utf-8")
    assert incidents.read_rows(path) == [{"event": "start"}, {"torn": 2}]


def test_book_level_supervisor_faults_are_read_once_per_book(book, rules):
    events = book / "autopilot" / "events.jsonl"
    with open(events, "a", encoding="utf-8") as f:
        f.write(json.dumps({"event": "tick_error", "error": "ValueError('compilation')"}) + "\n")
    found = incidents.book_incidents(book, book.parent)
    assert [i["text"] for i in found["incidents"]] == ["supervisor_died_at", "tick_error ValueError('compilation')"]
    assert [incidents.classify(i, rules)[1] for i in found["incidents"]] == ["F4", "UNCOVERED"]
    assert not any(i["text"].startswith("tick_error") for i in incidents.episode_incidents(book, 1, book.parent)["incidents"])


def test_episode_numbers_are_probed_by_name_and_the_last_few_kept(tmp_path):
    for n in (1, 2, 3, 5):
        (tmp_path / "episodes" / f"ep{n:02d}").mkdir(parents=True)
    (tmp_path / "episodes" / "ep01_short").mkdir()
    assert incidents.episode_numbers(tmp_path) == [1, 2, 3, 5]
    assert incidents.episode_numbers(tmp_path, last=2) == [3, 5]


def test_a_survey_tallies_every_named_book_once_and_keeps_each_episodes_ledger(book, rules):
    out = incidents.survey([("jekyll", [1])], book.parent, rules)
    assert out["episodes"]["jekyll/ep01"]["drive"]["start"] == 21
    assert out["books"]["jekyll"]["book_incidents"] == 1
    assert out["classes"]["supervisor_died"]["count"] == 1
    assert out["classes"]["book_json_precondition"]["scenario"] == "F14"


def test_the_script_writes_the_tally_and_prints_its_path_first(book, tmp_path, capsys):
    from scripts.proof import incidents as script
    out = tmp_path / "results" / "incidents.json"
    books = (("jekyll", [1]),)
    assert script.plan_of(book.parent, books) == [("jekyll", [1])]
    script.BOOKS = books
    try:
        assert script.main(["--out", str(out), "--root", str(book.parent)]) == 0
    finally:
        import importlib
        importlib.reload(script)
    said = capsys.readouterr().out.splitlines()
    assert said[0] == str(out.resolve())
    assert "jekyll/ep01: start 21 end 17" in said[1]
    assert json.loads(out.read_text(encoding="utf-8"))["classes"]["ffmpeg_bad_take"]["scenario"] == "F13"


def test_a_pause_at_a_boundary_is_no_incident_and_a_refusal_without_a_traceback_keeps_its_class(tmp_path, rules):
    log = tmp_path / "drive_launch01.log"
    log.write_text("[drive] 20260827135504 ep01: episode paused at a boundary on run 1\n", encoding="utf-8")
    assert incidents.log_incident(log, tmp_path) is None
    log.write_text("RuntimeError: REFUSED: scripts/episode/say_lines.py exit 1\n", encoding="utf-8")
    assert incidents.classify(incidents.log_incident(log, tmp_path), rules) == ("bare_step_refusal", "UNCOVERED")


def test_an_owners_order_park_is_counted_apart_never_a_recorded_class(rules):
    found = [{"kind": "parked", "text": "parked owner: order: 19-22 publish first", "source": "s", "step": None,
              "episode": 19},
             {"kind": "parked", "text": "parked youtube_token_expired: run it", "source": "s", "step": None,
              "episode": 19}]
    out = incidents.tally(found, rules)
    assert list(out["classes"]) == ["oauth_expired"] and out["recorded"] == 1
    assert out["not_faults"]["owner_order"]["count"] == 1


def test_a_code_move_hand_over_is_the_commit_class_even_in_a_cut_off_log(tmp_path, rules):
    log = tmp_path / "drive_launch01.log"
    log.write_text("[drive] x ep01: WARNING code moved mid-episode: started on 69fcdea2, resuming on 0ee5e95b\n",
                   encoding="utf-8")
    assert incidents.classify(incidents.log_incident(log, tmp_path), rules) == ("code_moved_hold", "F7")
    log.write_text("[drive] x ep22: episode completed after 1 run(s)\n", encoding="utf-8")
    assert incidents.log_incident(log, tmp_path) is None


def test_an_episode_with_no_drive_records_is_absent_never_zero_incidents(book, rules, tmp_path):
    """AUDIT A9: the Scarlet episodes predate drive.jsonl and printed 'start 0 end 0 | incidents 0'
    as if they had run clean; their sample is absent, and the survey counts them apart."""
    (book / "episodes" / "ep02").mkdir(parents=True)
    out = incidents.survey([("jekyll", [1, 2])], book.parent, rules)
    assert out["episodes"]["jekyll/ep02"]["records"] == "absent"
    assert out["episodes"]["jekyll/ep01"]["records"] == "read"
    assert out["sample"] == {"read": 1, "absent": 1}
    from scripts.proof import incidents as script
    lines = script.report_lines(out, tmp_path / "x.json")
    assert any(line.startswith("jekyll/ep02: drive records absent") for line in lines)
    assert not any(line.startswith("jekyll/ep02: start 0") for line in lines)
