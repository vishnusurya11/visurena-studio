"""The proof report counts only what a check measured, by the rules of 2026-10-21_ep02_proof DESIGN 5.1,
each enforced in code: n is distinct points; a canned dependency makes a row mechanism; a row measured by a
failed instrument contributes nothing; a Q5/Q7 time measure counts only with a measured clock and absolute
evidence outside any sandbox (fail closed), while a mechanism row still counts and still fails; Q6 is capped at
PARTIAL until the transcript holds every contract route; P2's summaries are adapted into rows; failed points
with unknown passes print beside the count; Q8-compliance prints apart and Q8 is REAL-RUN; a percentage is
never printed.  Fixture rows (tests/fixtures/proof/results/) stand in for
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
    got = cf.status(spec, [row(n=3, evidence=[boxed], clock="measured"), row(n=3, clock="recorded")], shape_ok=True)
    assert got["n"] == 0 and len(got["refused"]) == 2
    assert boxed in got["refused"][0][1] and "recorded" in got["refused"][1][1]
    assert cf.status(SPEC, [row(n=3, clock="recorded")], shape_ok=True)["n"] == 3


def test_a_time_measure_counts_only_with_a_measured_clock_and_absolute_real_evidence(tmp_path):
    """R15 fails closed: no clock key, no evidence, or a relative path is refused, never counted."""
    spec = SPEC | {"time": True}
    real = str(tmp_path / "real" / "episodes" / "ep01" / "timing.jsonl")
    assert cf.contribution(row(n=3, evidence=[real], clock="measured"), spec) == ("quality", "")
    relative = "episodes/ep02/timing.jsonl"
    for bad, why in ((row(evidence=[real]), "clock"), (row(evidence=[], clock="measured"), "no evidence"),
                     (row(evidence=[relative], clock="measured"), relative),
                     (row(kind="baseline", evidence=[relative], clock="measured"), relative)):
        kind, said = cf.contribution(bad, spec)
        assert kind == "refused" and why in said, (bad, said)


def test_a_failing_sandbox_mechanism_row_still_fails_its_time_question(tmp_path):
    """A-caps counts whether a cap fired, never a duration: its sandbox evidence is no refusal, so a loop
    past its cap turns Q5 FAILING and a passing one meets Q5's mechanism check."""
    spec = {"title": "t", "time": True, "checks": [{"check": "A-caps", "min_n": 1, "kind": "mechanism"}]}
    boxed = [str(tmp_path / "visurena_rehearsal" / "r1" / n) for n in ("attempts.json", "events.jsonl")]
    caps = row(check="A-caps", q="Q5", kind="mechanism", passed=False, evidence=boxed, match_classes={})
    assert cf.contribution(caps, spec)[0] == "mechanism"
    got = cf.status(spec, [caps], shape_ok=True)
    assert got["status"] == "FAILING" and "A-caps" in got["why"]
    ok = cf.status(spec, [caps | {"passed": True, "n_pass": 1}], shape_ok=True)
    assert ok["mechanism"] == (1, 1) and "A-caps" not in ok["why"] and ok["why"] == "no quality row"
    gap = row(check="unmeasured:x", kind="gap", passed=False, evidence=["rel.json"])
    assert cf.contribution(gap, spec)[0] == "gap"


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
    refused = [r["check"] for r, _ in got["Q5"]["refused"]]
    assert sorted(refused) == ["F12", "base_rate_under_6h", "time_backtest_loo"], refused
    assert len(got["Q7"]["refused"]) == 1
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


def test_the_engine_shape_is_calibrated_only_by_a_full_recorded_transcript(tmp_path):
    """One pair per contract route: a partial SR-5 capture or a stray .gitkeep never lifts the Q6 cap."""
    from studio.rehearsal.fake_comfy import CONTRACT_ROUTES
    folder = tmp_path / "t"
    assert not cf.shape_calibrated(tmp_path / "absent")
    folder.mkdir()
    (folder / ".gitkeep").write_text("", encoding="utf-8")
    assert not cf.shape_calibrated(folder)
    for route in CONTRACT_ROUTES[:-1]:
        (folder / f"{route}.json").write_text(json.dumps({}), encoding="utf-8")
    assert not cf.shape_calibrated(folder)
    (folder / f"{CONTRACT_ROUTES[-1]}.json").write_text(json.dumps({}), encoding="utf-8")
    assert cf.shape_calibrated(folder)


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
    """face_replay keeps its per-face data under `rows` beside `proof_rows`: only the proof rows are rows."""
    gate = {"label_files": [], "rows": [{"take": "T00", "px": 94.6}], "proof_rows": [row(check="g", q="Q1")]}
    (tmp_path / "gate.json").write_text(json.dumps(gate), encoding="utf-8")
    (tmp_path / "summary.json").write_text(json.dumps({"classes": {}}), encoding="utf-8")
    assert [r["check"] for r in cf.load_results(tmp_path)] == ["g"]
    assert cf.rowless_files(tmp_path) == ["summary.json"]
    argv = ["--results", str(tmp_path), "--out-dir", str(tmp_path / "out"), "--transcript", str(tmp_path / "none")]
    assert cf.main(argv) == 0
    assert "summary.json" in (tmp_path / "out" / "CONFIDENCE_iter1.md").read_text(encoding="utf-8")


def test_the_map_names_the_ids_the_face_suite_emits():
    qmap = cf.load_questions(cf.QUESTIONS)["questions"]
    assert all("instrument_gate.face_eye.cel" in qmap[q]["gates"] for q in ("Q1", "Q2", "Q3"))
    assert all("face_replay.unrecorded_kill" in qmap[q]["gates"] for q in ("Q1", "Q2"))
    assert "face_replay.outside_invariant" in [c["check"] for c in qmap["Q1"]["checks"]]
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


def test_failed_points_with_unknown_passes_print_beside_the_count_and_no_bound_hides_them():
    """tally([failed n=30 no n_pass, passed n=12]) is 12/12 over the known rows; the 30 failed points
    print beside it and no Wilson bound is printed over a subset of the points."""
    agg = row(n=30, passed=False)
    del agg["n_pass"]
    got = cf.status(SPEC, [agg, row(n=12)], shape_ok=True)
    assert got["unknown"] == 30 and cf.unknown_points([agg, row(n=12)]) == 30
    text = cf.count(got["k"], got["n"], got["unknown"])
    assert "12/12" in text and "30 failed points with unknown passes" in text and "Wilson" not in text
    assert "Wilson" in cf.count(12, 12) and cf.count(0, 0, 30).startswith("no counted points")


def test_the_incident_summary_becomes_a_coverage_row_and_its_open_gaps(tmp_path):
    """DESIGN 4.5: a class counts as handled only when its scenario ran and PASSED; a class no scenario
    reproduces, or whose scenario has not run, is an open gap, never a failure."""
    summary = {"recorded": 4, "classes": {"a": {"scenario": "F2"}, "b": {"scenario": "F9"},
                                          "c": {"scenario": "F13"}, "d": {"scenario": "UNCOVERED"}},
               "not_faults": {"owner_order": {"scenario": "NOT_A_FAULT"}}}
    ran = [row(check="F2", kind="mechanism"), row(check="F9", kind="mechanism", passed=False)]
    rows = cf.incident_rows(summary, ran)
    cov = next(r for r in rows if r["check"] == "incident_coverage")
    assert (cov["n_distinct"], cov["n_pass"], cov["n_points"], cov["passed"]) == (2, 1, 4, False)
    assert cov["question"] == "Q6" and cov["kind"] == "mechanism" and "b" in cov["detail"]
    gaps = {r["check"]: r for r in rows if r["kind"] == "gap"}
    assert "d" in gaps["unmeasured:incident classes no scenario reproduces"]["detail"]
    assert "c (F13)" in gaps["unmeasured:incident classes whose scenario has not run"]["detail"]
    assert all(not g["passed"] for g in gaps.values())


def test_the_precondition_audit_becomes_a_named_outcome_row_and_its_unknowns_are_gaps():
    audit = {"gaps": [{"kind": "base_sheet", "what": "poole", "outcome": "jit"},
                      {"kind": "voice", "what": "x", "outcome": "park"},
                      {"kind": "unresolved_name", "what": "a servant", "outcome": "unknown"}],
             "props": {"status": "REAL-RUN", "why": "named by the step-02 plan"}}
    rows = cf.precondition_rows(audit)
    named = next(r for r in rows if r["check"] == "preconditions_ch2")
    assert (named["n_distinct"], named["n_pass"], named["n_points"], named["passed"]) == (2, 2, 3, True)
    assert named["kind"] == "mechanism" and named["question"] == "Q6"
    gap = next(r for r in rows if r["kind"] == "gap")
    assert not gap["passed"] and "a servant" in gap["detail"] and "props" in gap["detail"]


def test_a_check_two_results_files_hold_counts_once_from_the_newest_and_the_rerun_is_named(tmp_path):
    """n is distinct points, never reruns: face_rows_run1.json beside face_rows.json is the same suite's
    earlier run, so its rows are superseded, never added."""
    import os
    (tmp_path / "face_rows_run1.json").write_text(json.dumps([row(check="c", n=3), row(check="d", n=3)]),
                                                  encoding="utf-8")
    (tmp_path / "face_rows.json").write_text(json.dumps([row(check="c", n=3, passed=False)]), encoding="utf-8")
    os.utime(tmp_path / "face_rows_run1.json", (1_000_000, 1_000_000))
    got = cf.load_results(tmp_path)
    assert sorted((r["check"], r["_file"]) for r in got) == [("c", "face_rows.json"), ("d", "face_rows_run1.json")]
    assert cf.superseded_names(tmp_path) == ["c (face_rows_run1.json)"]
    argv = ["--results", str(tmp_path), "--out-dir", str(tmp_path / "out"), "--transcript", str(tmp_path / "none")]
    assert cf.main(argv) == 0
    assert "c (face_rows_run1.json)" in (tmp_path / "out" / "CONFIDENCE_iter1.md").read_text(encoding="utf-8")


def test_a_summary_file_with_an_adapter_is_read_as_rows_and_never_named_rowless(tmp_path):
    (tmp_path / "incidents.json").write_text(json.dumps({"recorded": 1, "classes": {"a": {"scenario": "F2"}}}),
                                             encoding="utf-8")
    (tmp_path / "scenarios.json").write_text(json.dumps([row(check="F2", kind="mechanism")]), encoding="utf-8")
    got = cf.load_results(tmp_path)
    cov = next(r for r in got if r["check"] == "incident_coverage")
    assert cov["_file"] == "incidents.json" and cov["n_pass"] == 1
    assert cf.rowless_files(tmp_path) == []
