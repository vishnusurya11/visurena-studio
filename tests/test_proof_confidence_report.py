"""The proof report counts only what a check measured, by the rules of 2026-10-21_ep02_proof DESIGN 5.1,
each enforced in code: n is distinct points; a canned dependency makes a row mechanism; a row measured by a
failed instrument contributes nothing; a Q5/Q7 row from a sandbox or a recorded clock is refused with its
path; Q6 is capped at PARTIAL while the fake ComfyUI's shape is uncalibrated; Q8-compliance prints apart and
Q8 is REAL-RUN; a percentage is never printed.  Fixture rows (tests/fixtures/proof/results/) stand in for
P5/P6's results, so this package never waits for them (DESIGN 7)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.proof import confidence as cf

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "proof" / "results"


def row(check="c", q="Q6", passed=True, n=1, kind="quality", **kw) -> dict:
    base = {"check": check, "question": q, "passed": passed, "n_points": n, "n_distinct": n,
            "n_pass": n if passed else 0, "evidence": ["x.json"], "match_classes": ["exact"],
            "instrument": "none", "instrument_state": "n/a", "kind": kind}
    return base | kw


SPEC = {"title": "t", "checks": [{"check": "c", "min_n": 3}]}


def test_the_wilson_bound_matches_the_design_gate():
    assert cf.wilson_lb(26, 30) == pytest.approx(0.703, abs=0.001)
    assert cf.wilson_lb(25, 30) == pytest.approx(0.664, abs=0.001)
    assert cf.wilson_lb(0, 0) == 0.0


def test_every_fixture_row_carries_the_row_schema():
    rows = cf.load_results(FIXTURES)
    assert rows and all(cf.ROW_KEYS - {"n_distinct"} <= set(r) for r in rows)
    assert {r["_file"] for r in rows} == {"face.json", "scenarios.json", "time.json", "story.json"}


def test_n_is_distinct_points_and_a_row_without_them_counts_nothing():
    got = cf.status(SPEC, [row(n_points=28, n_distinct=3, n_pass=3)], shape_ok=True)
    assert (got["k"], got["n"], got["status"]) == (3, 3, "PROVEN")
    bare = row()
    del bare["n_distinct"]
    got = cf.status(SPEC, [bare], shape_ok=True)
    assert got["n"] == 0 and got["status"] == "PARTIAL" and "no n_distinct" in got["refused"][0][1]


def test_a_canned_dependency_makes_a_quality_row_mechanism():
    canned = row(n=3, match_classes=["exact", "canned"])
    assert cf.contribution(canned, SPEC)[0] == "mechanism"
    got = cf.status(SPEC, [canned], shape_ok=True)
    assert got["n"] == 0 and got["status"] == "PARTIAL" and got["mechanism"] == (3, 3)


def test_a_row_from_a_failed_instrument_contributes_nothing():
    failed = row(n=30, instrument="face_eye", instrument_state="failed")
    got = cf.status(SPEC, [failed], shape_ok=True)
    assert got["n"] == 0 and got["instrument_failed"] == [failed]


def test_a_time_row_from_a_sandbox_or_a_recorded_clock_is_refused_with_its_path(tmp_path):
    spec = SPEC | {"time": True}
    boxed = str(tmp_path / "visurena_rehearsal" / "r1" / "clock.jsonl")
    got = cf.status(spec, [row(n=3, evidence=[boxed]), row(n=3, clock="recorded")], shape_ok=True)
    assert got["n"] == 0 and len(got["refused"]) == 2
    assert boxed in got["refused"][0][1] and "recorded" in got["refused"][1][1]
    assert cf.status(SPEC, [row(n=3, clock="recorded")], shape_ok=True)["n"] == 3


def test_q6_is_capped_at_partial_while_the_engine_shape_is_uncalibrated():
    spec = SPEC | {"cap_uncalibrated_shape": True}
    assert cf.status(spec, [row(n=3)], shape_ok=True)["status"] == "PROVEN"
    got = cf.status(spec, [row(n=3)], shape_ok=False)
    assert got["status"] == "PARTIAL" and "uncalibrated" in got["why"]


def test_any_failing_counted_row_fails_the_question_but_a_failing_gate_is_real_run():
    assert cf.status(SPEC, [row(n=3), row(passed=False)], shape_ok=True)["status"] == "FAILING"
    gated = SPEC | {"gates": ["g"], "staged": ["SR-1"]}
    got = cf.status(gated, [row(n=3), row(check="g", passed=False)], shape_ok=True)
    assert got["status"] == "REAL-RUN" and "g" in got["why"]
    assert cf.status(gated, [row(n=3)], shape_ok=True)["status"] == "REAL-RUN"


def test_an_open_gap_blocks_proof_and_a_baseline_never_counts():
    rows = [row(n=3), row(check="unmeasured:x", kind="gap", passed=False), row(check="b", kind="baseline", passed=False)]
    got = cf.status(SPEC, rows, shape_ok=True)
    assert got["status"] == "PARTIAL" and (got["k"], got["n"]) == (3, 3) and "unmeasured:x" in got["why"]


def test_a_required_check_short_of_its_minimum_is_partial():
    got = cf.status(SPEC, [row(n=2)], shape_ok=True)
    assert got["status"] == "PARTIAL" and "c 2 of 3" in got["why"]


def test_q8_is_real_run_and_its_compliance_prints_apart():
    spec = {"title": "story", "real_run": True, "compliance_apart": True, "staged": ["SR-4"],
            "checks": [{"check": "c", "min_n": 1, "kind": "compliance"}]}
    got = cf.status(spec, [row(n=1, kind="compliance")], shape_ok=True)
    assert got["status"] == "REAL-RUN" and got["compliance"] == (1, 1) and got["n"] == 0


def test_the_question_map_names_q1_to_q8_and_every_staged_run_it_cites():
    qmap = cf.load_questions(cf.QUESTIONS)
    assert sorted(qmap["questions"]) == [f"Q{i}" for i in range(1, 9)]
    runs = qmap["staged_runs"]
    assert sorted(runs) == [f"SR-{i}" for i in range(6)]
    assert all("machine_min" in r and r["owner_go"] is True for r in runs.values())
    cited = {s for q in qmap["questions"].values() for s in q.get("staged", [])}
    assert cited <= set(runs)
    assert all(qmap["questions"][q].get("real_run") for q in ("Q4", "Q7", "Q8"))


def test_the_fixture_results_give_the_pre_registered_statuses():
    qmap = cf.load_questions(cf.QUESTIONS)
    got = cf.evaluate(qmap, cf.load_results(FIXTURES), shape_ok=False)
    assert {q: v["status"] for q, v in got.items()} == {
        "Q1": "REAL-RUN", "Q2": "REAL-RUN", "Q3": "REAL-RUN", "Q4": "REAL-RUN",
        "Q5": "PARTIAL", "Q6": "FAILING", "Q7": "REAL-RUN", "Q8": "REAL-RUN"}
    assert len(got["Q5"]["refused"]) == 1 and len(got["Q7"]["refused"]) == 1
    assert (got["Q6"]["k"], got["Q6"]["n"]) == (1, 2)


def test_the_report_leads_with_its_path_never_overwrites_and_prints_no_percentage(tmp_path):
    argv = ["--results", str(FIXTURES), "--out-dir", str(tmp_path), "--transcript", str(tmp_path / "none")]
    assert cf.main(argv) == 0 and cf.main(argv) == 0
    first, second = tmp_path / "CONFIDENCE_iter1.md", tmp_path / "CONFIDENCE_iter2.md"
    text = first.read_text(encoding="utf-8")
    assert text.splitlines()[0] == str(first) and second.exists()
    assert "%" not in text
    for needle in ("INSTRUMENT FAILED", "REFUSED", "SR-1", "owner go", "Q8-compliance", "uncalibrated",
                   "30.85 h wall", "0 of 1 episodes under 6 h", "Wilson"):
        assert needle in text, needle


def test_the_engine_shape_is_calibrated_only_by_a_recorded_transcript(tmp_path):
    assert not cf.shape_calibrated(tmp_path / "absent")
    (tmp_path / "t").mkdir()
    assert not cf.shape_calibrated(tmp_path / "t")
    (tmp_path / "t" / "prompt.json").write_text(json.dumps({}), encoding="utf-8")
    assert cf.shape_calibrated(tmp_path / "t")


def test_the_sibling_suites_row_forms_are_read_as_written():
    """asserts.row and instrument_gate.proof_row write match_classes as a count map and the gate's state
    as 'INSTRUMENT FAILED' / 'CALIBRATED'; a zero canned count is no canned dependency."""
    assert cf.contribution(row(match_classes={"exact": 3, "canned": 1}), SPEC)[0] == "mechanism"
    assert cf.contribution(row(match_classes={"exact": 3, "canned": 0}), SPEC)[0] == "quality"
    assert cf.contribution(row(instrument_state="INSTRUMENT FAILED"), SPEC)[0] == "instrument_failed"
    assert cf.contribution(row(instrument_state="CALIBRATED"), SPEC)[0] == "quality"
    got = cf.status(SPEC, [row(n=3, instrument_state="shape: uncalibrated")], shape_ok=True)
    assert got["status"] == "PARTIAL" and "uncalibrated instrument" in got["why"]
    assert cf.engine_shape_ok(True, [row(instrument_state="shape: uncalibrated")]) is False
    assert cf.engine_shape_ok(True, [row()]) is True and cf.engine_shape_ok(False, [row()]) is False
    assert "a named park" in cf.row_line(row(detail="a named park"))


def test_a_suites_proof_rows_are_read_and_a_file_without_rows_is_named(tmp_path):
    (tmp_path / "gate.json").write_text(json.dumps({"label_files": [], "proof_rows": [row(check="g", q="Q1")]}),
                                        encoding="utf-8")
    (tmp_path / "summary.json").write_text(json.dumps({"classes": {}}), encoding="utf-8")
    assert [r["check"] for r in cf.load_results(tmp_path)] == ["g"]
    assert cf.rowless_files(tmp_path) == ["summary.json"]
    argv = ["--results", str(tmp_path), "--out-dir", str(tmp_path / "out"), "--transcript", str(tmp_path / "none")]
    assert cf.main(argv) == 0
    assert "summary.json" in (tmp_path / "out" / "CONFIDENCE_iter1.md").read_text(encoding="utf-8")


def test_the_map_names_the_ids_the_face_suite_emits():
    qmap = cf.load_questions(cf.QUESTIONS)["questions"]
    assert all("instrument_gate.face_eye.cel" in qmap[q]["gates"] for q in ("Q1", "Q2", "Q3"))
    assert "panel_take_size" in [c["check"] for c in qmap["Q3"]["checks"]]


def test_a_failed_row_without_per_point_passes_fails_the_question_but_invents_no_count():
    agg = row(n=21, passed=False)
    del agg["n_pass"]
    got = cf.status(SPEC, [agg, row(n=3)], shape_ok=True)
    assert got["status"] == "FAILING" and (got["k"], got["n"]) == (3, 3)
    assert "passes per point not reported" in cf.row_line(agg)
    whole = row(n=4)
    del whole["n_pass"]
    assert cf.tally([whole]) == (4, 4)
