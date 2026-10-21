"""The time model's back-test: a predictor from an episode's inputs only, scored leave-one-out on
measured timing.jsonl step totals, with the steps no record measures listed apart (2026-10-21_ep02_proof
DESIGN 4.7, package P7; skeptic R15, R16).

Rows are written by `episode_clock.stamp` into a tmp book, so every fixture row has the contract's shape.
No test reads library/: the script test builds a tiny library in tmp_path."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from studio import episode_clock, eta, face_refine, step_caps
from studio.rehearsal import time_model as tm

DAY = datetime(2026, 10, 18, 15, 0, 0).timestamp()


def stamp(book: Path, stage: str, at: float, seconds: float, **kw) -> dict:
    return episode_clock.stamp(book, 1, stage, DAY + at, DAY + at + seconds, **kw)


def ep_rows(tmp_path: Path, name: str = "b") -> tuple[Path, list[dict]]:
    book = tmp_path / name
    stamp(book, "step_02", 0, 0, note="started")
    stamp(book, "plan", 0, 600)
    stamp(book, "places", 600, 100)
    stamp(book, "take_dq", 1000, 300, within="takes")
    stamp(book, "takes", 900, 500, net_of=300)
    stamp(book, "qc", 1500, 200)
    stamp(book, "dossier", 1800, 1)
    stamp(book, "master_eye", 4000, 50)
    return book, episode_clock.rows(book, 1)


# ---- the sandbox refusal (R15) ----

def test_a_path_under_any_sandbox_is_refused_and_a_real_one_is_not(tmp_path):
    marked = tmp_path / "box"
    (marked / "library").mkdir(parents=True)
    (marked / "rehearsal.json").write_text("{}", encoding="utf-8")
    bad = [tmp_path / "visurena_rehearsal" / "r1" / "library" / "timing.jsonl",
           marked / "library" / "ep02" / "timing.jsonl", tm.PROOF_SANDBOX / "library" / "timing.jsonl"]
    for path in bad:
        assert tm.under_sandbox(path), path
        with pytest.raises(tm.SandboxInput, match="sandbox"):
            tm.refuse_sandbox([tmp_path / "real.jsonl", path])
    assert not tm.under_sandbox(tmp_path / "real" / "timing.jsonl")
    tm.refuse_sandbox([tmp_path / "real" / "timing.jsonl"])


# ---- the reviewed per-era step map ----

def test_the_era_is_chosen_by_the_first_row_and_an_unreviewed_date_refuses():
    assert tm.era_for([{"started": "2026-10-08T21:15:11"}]).name == "wotw-self-curing"
    assert tm.era_for([{"started": "2026-10-18T15:00:06"}]).name == "grammar-face-refine"
    with pytest.raises(tm.UnmappedStage, match="no reviewed era"):
        tm.era_for([{"started": "2026-09-01T00:00:00"}])


def test_every_stage_maps_to_one_step_a_mark_to_none_and_an_unknown_stage_refuses():
    grammar = tm.era_for([{"started": "2026-10-18T15:00:06"}])
    assert tm.step_of("take_dq", grammar) == "09" and tm.step_of("upscale", grammar) == "10"
    assert tm.step_of("step_09", grammar) == tm.MARK
    with pytest.raises(tm.UnmappedStage, match="brand_new_stage"):
        tm.step_of("brand_new_stage", grammar)
    assert tm.unmapped([{"stage": "brand_new_stage"}, {"stage": "plan"}], grammar) == ["brand_new_stage"]


def test_the_current_era_maps_every_stage_the_clock_and_the_eta_name():
    """A stage the runner stamps today that the map does not name would vanish from the measure."""
    grammar = tm.ERAS[-1]
    named = set(episode_clock.NORMS) | set(eta.SUB_STEP) | set(episode_clock.RENDERS)
    assert sorted(s for s in named if s not in grammar.stages) == []
    assert grammar.refine and not tm.ERAS[0].refine


# ---- the measure ----

def test_first_pass_ends_at_the_first_dossier_and_repair_windows_are_apart(tmp_path):
    _, rows = ep_rows(tmp_path)
    keep, apart = tm.first_pass(rows, [])
    assert [r["stage"] for r in apart] == ["master_eye"]
    window = [(DAY + 1400, DAY + 1600)]
    keep, apart = tm.first_pass(rows, window)
    assert "qc" in [r["stage"] for r in apart] and "dossier" in [r["stage"] for r in keep]
    assert tm.repair_windows([{"opened_at": 5.0, "closed_at": 9.0}, {"opened_at": 12.0}])[1][1] == float("inf")


def test_a_netted_step_keeps_its_wall_and_marks_are_not_time(tmp_path):
    _, rows = ep_rows(tmp_path)
    keep, _ = tm.first_pass(rows, [])
    got = tm.measured(keep, tm.era_for(keep))
    assert got["09"] == pytest.approx(500.0) and got["02"] == pytest.approx(600.0)
    assert got["13"] == 0.0 and set(got) == set(tm.STEPS)


def test_a_contended_row_is_marked_under_its_step(tmp_path):
    book = tmp_path / "c"
    stamp(book, "plan", 0, 600)
    stamp(book, "places", 300, 100)
    rows = episode_clock.rows(book, 1)
    assert tm.contended(rows, tm.era_for(rows)) == {"02": [600.0], "03": [100.0]}


def test_the_clock_to_the_first_master_sums_its_non_repair_runs_and_names_the_uncovered(tmp_path):
    _, rows = ep_rows(tmp_path)
    end = tm.first_master_end(rows)
    runs = [{"started": DAY, "ended": DAY + 2000, "seconds": 2000.0},
            {"started": DAY + 1500, "ended": DAY + 1900, "seconds": 400.0, "repair": True},
            {"started": DAY + 5000, "ended": DAY + 5100, "seconds": 100.0}]
    assert tm.clock_to_first_master(runs, end) == pytest.approx(2000.0)
    assert tm.uncovered_s(runs, rows, end) == pytest.approx(2000.0 - 1401.0, abs=1.0)
    assert tm.clock_to_first_master([], end) is None


# ---- the inputs and the priors ----

def test_inputs_come_from_the_plan_the_shots_and_the_placed_lines_only():
    plan = {"shots": [{"index": 0}, {"index": 1}, {"index": 2}], "omit": [2], "setups": {"a": {}, "b": {}}}
    shots = [{"index": 0, "frames": 141, "faces": ["x"]}, {"index": 1, "frames": 90, "faces": []}]
    got = tm.inputs_from(shots, {"lines": [{}] * 5}, plan)
    assert got == tm.Inputs(shots=2, setups=2, lines=5, frames=(141, 90), faces=(1, 0))


def test_the_vl_fit_is_least_squares_on_the_reply_tokens():
    calls = [{"seconds": 2.0 + 0.5 * t, "answer_tokens": t} for t in (10, 20, 30, 40)]
    fit = tm.vl_fit(calls)
    assert fit["a"] == pytest.approx(2.0) and fit["b"] == pytest.approx(0.5) and fit["n"] == 4
    assert tm.vl_read_s(fit) == pytest.approx(2.0 + 0.5 * 25)
    assert tm.vl_fit([])["n"] == 0


def test_the_priors_are_the_studio_models_of_each_step():
    inp = tm.Inputs(shots=3, setups=2, lines=4, frames=(141, 90, 175), faces=(1, 0, 2))
    got = tm.priors(inp, read_s=5.0, refine=True)
    render = episode_clock.norm_for("takes", frames=[141, 90, 175])
    checks = episode_clock.norm_for("take_dq", count=3) + 3 * 5.0
    priced = face_refine.price(1, 141) + face_refine.price(2, 175)
    assert got["09"] == pytest.approx(render + checks + priced)
    assert tm.priors(inp, read_s=5.0, refine=False)["09"] == pytest.approx(render + checks)
    assert got["04"] == episode_clock.norm_for("lines", count=4) and got["08"] == pytest.approx(15.0)
    assert set(got) == set(tm.PREDICTED)


# ---- leave one out ----

def episode(name: str, scale: float, shots: int = 10, clock: float | None = None) -> tm.Episode:
    inp = tm.Inputs(shots=shots, setups=3, lines=10, frames=(141,) * shots, faces=(1,) * shots)
    pri = tm.priors(inp, 5.0, refine=False)
    got = {s: scale * pri[s] for s in tm.PREDICTED} | {"13": 0.0}
    return tm.Episode(name=name, era="wotw-self-curing", refine=False, inputs=inp, measured=got,
                      clock_s=clock, evidence=(f"{name}/timing.jsonl",))


def test_leave_one_out_never_fits_on_the_episode_it_predicts():
    eps = [episode("a", 1.0), episode("b", 1.0), episode("c", 1.0), episode("d", 2.0)]
    res = tm.leave_one_out(eps, read_s=5.0)
    assert [r["episode"] for r in res] == ["a", "b", "c", "d"]
    assert res[3]["error"] == pytest.approx(-0.5)
    assert res[0]["error"] == pytest.approx(0.0)
    assert res[0]["p90_s"] >= res[0]["pred_s"]


def test_the_pass_is_three_of_four_within_fifteen_hundredths_and_needs_four():
    def res(*errs):
        return [{"episode": str(i), "error": e} for i, e in enumerate(errs)]
    assert tm.verdict(res(0.1, -0.14, 0.2, 0.05)) == {"passed": True, "within": 3, "n": 4}
    assert tm.verdict(res(0.1, 0.2, -0.3, 0.05))["passed"] is False
    assert tm.verdict(res(0.0, 0.0, 0.0))["passed"] is False


def test_the_step_error_is_a_mean_absolute_in_minutes():
    res = [{"pred": {"02": (600.0, 700.0)}, "measured": {"02": 1200.0}},
           {"pred": {"02": (600.0, 700.0)}, "measured": {"02": 600.0}}]
    assert tm.step_mae(res, steps=("02",)) == {"02": pytest.approx(5.0)}


# ---- the unmeasured steps (R16) ----

def test_an_unmeasured_share_over_five_hundredths_or_unknown_blocks_proof():
    small = tm.Gap("publish", "13", "capped", measured=False, p90_s=100.0, source="cap")
    big = tm.Gap("refine", "09", "priced", measured=False, p90_s=1000.0, source="price")
    unknown = tm.Gap("whisper", "11", "no row", measured=False, p90_s=None, source="none")
    assert tm.provable(tm.shares([small], p90_total=9900.0))
    assert not tm.provable(tm.shares([small, big], p90_total=9900.0))
    assert not tm.provable(tm.shares([unknown], p90_total=9900.0))
    assert tm.shares([small, big], 8900.0)[1][1] == pytest.approx(0.1)


def test_the_gaps_name_the_declared_unmeasured_steps_on_ep01_shaped_rows(tmp_path):
    book = tmp_path / "e"
    stamp(book, "face_refine", 0, 400, within="takes")
    stamp(book, "takes", 1000, 150, note="--from-refs --tiny-face")
    stamp(book, "take_dq", 1150, 50, note="1")
    stamp(book, "step_10", 1300, 0, note="started")
    stamp(book, "master_eye", 2000, 900)
    stamp(book, "dossier", 3000, 1)
    rows = episode_clock.rows(book, 1)
    inp = tm.Inputs(shots=2, setups=1, lines=3, frames=(192, 90), faces=(1, 0))
    gaps = {g.name: g for g in tm.gaps(first=rows[:1], every=rows, target=inp, uncovered=[700.0])}
    assert not gaps["first-pass face refine"].measured
    assert gaps["first-pass face refine"].p90_s == pytest.approx(face_refine.price(1, 192))
    assert gaps["tiny-face 1024 rung"].p90_s == pytest.approx(200.0) and not gaps["tiny-face 1024 rung"].measured
    assert not gaps["master eye (b008100)"].measured and gaps["master eye (b008100)"].p90_s == pytest.approx(900.0)
    assert gaps["GPU whisper worker"].p90_s is None
    assert gaps["publish (step 13)"].p90_s == step_caps.step_wall_s("13")
    assert gaps["uncovered clock (drive overhead + killed runs)"].p90_s == 700.0


def test_a_refine_row_with_its_gpu_clock_measures_the_first_pass_refine(tmp_path):
    book = tmp_path / "f"
    stamp(book, "face_refine", 0, 400, extra={"gpu_busy_s": 300.0})
    rows = episode_clock.rows(book, 1)
    inp = tm.Inputs(shots=1, setups=1, lines=1, frames=(90,), faces=(1,))
    gaps = {g.name: g for g in tm.gaps(first=rows, every=rows, target=inp, uncovered=[])}
    assert gaps["first-pass face refine"].measured


def test_a_predicted_step_no_training_episode_measured_is_unmeasured_too():
    eps = [episode("a", 1.0), episode("b", 1.0)]
    eps[0].measured["10"] = eps[1].measured["10"] = 0.0
    assert [g.name for g in tm.unseen_steps(eps)] == ["step 10 (no training row)"]


# ---- the base rate and the result rows ----

def test_the_base_rate_counts_clocked_episodes_under_six_hours():
    eps = [episode("ep01", 1.0, clock=6.02 * 3600), episode("w", 1.0)]
    assert tm.base_rate(eps) == (0, 1)


def test_the_result_rows_carry_the_row_schema_with_a_measured_clock():
    eps = [episode("a", 1.0, clock=5 * 3600), episode("b", 1.0), episode("c", 1.0), episode("d", 1.1)]
    res = tm.leave_one_out(eps, read_s=5.0)
    gap = tm.Gap("whisper", "11", "no row", measured=False, p90_s=None, source="none")
    rows = tm.result_rows(res, tm.shares([gap], 1000.0), tm.base_rate(eps), eps)
    keys = {"check", "question", "passed", "n_points", "n_distinct", "evidence", "match_classes",
            "instrument", "instrument_state", "kind"}
    assert all(keys <= set(r) and r["question"] == "Q5" and r["clock"] == "measured" for r in rows)
    loo = rows[0]
    assert loo["check"] == "time_backtest_loo" and loo["kind"] == "quality" and loo["n_distinct"] == 4
    assert loo["n_pass"] == 4 and loo["passed"] is True
    assert [r["kind"] for r in rows[1:]] == ["gap", "baseline"]
    assert rows[1]["passed"] is False and rows[2]["n_pass"] == 1


# ---- the script, on a tiny library in tmp_path ----

def write_episode(library: Path, book: str, n: int, start: float, scale: float) -> None:
    home = library / book / "episodes" / f"ep{n:02d}"
    home.mkdir(parents=True)
    shots = [{"index": i, "frames": 141, "faces": ["x"]} for i in range(6)]
    (home / "takes" / "r2v").mkdir(parents=True)
    (home / "takes" / "r2v" / "shots.json").write_text(json.dumps(shots), encoding="utf-8")
    (home / "placed.json").write_text(json.dumps({"lines": [{}] * 8}), encoding="utf-8")
    (home / "plan.json").write_text(json.dumps({"shots": shots, "setups": {"a": {}}}), encoding="utf-8")
    for i, (stage, secs) in enumerate([("plan", 1800), ("places", 200), ("lines", 300), ("grids", 400),
                                       ("panels", 300), ("takes", 3000 * scale), ("assemble", 200),
                                       ("qc", 300), ("dossier", 1)]):
        episode_clock.stamp(library / book, n, stage, start + i * 4000, start + i * 4000 + secs)


def test_the_script_writes_numbered_reports_and_rows_and_refuses_a_sandbox_library(tmp_path):
    from scripts.proof import time_backtest as tb
    lib = tmp_path / "library"
    (lib).mkdir()
    (lib / "vlm_calls.jsonl").write_text(json.dumps({"seconds": 5.0, "answer_tokens": 40}) + "\n", encoding="utf-8")
    start = datetime(2026, 10, 8, 9, 0, 0).timestamp()
    for n, scale in ((24, 1.0), (25, 1.0), (26, 1.1)):
        write_episode(lib, "w", n, start + (n - 24) * 86400, scale)
    write_episode(lib, "j", 1, datetime(2026, 10, 18, 9, 0, 0).timestamp(), 1.0)
    out = tmp_path / "proof"
    argv = ["--library", str(lib), "--out-dir", str(out), "--episodes", "j:1", "w:24", "w:25", "w:26"]
    assert tb.main(argv) == 0 and tb.main(argv) == 0
    first = (out / "TIME_BACKTEST_iter1.md").read_text(encoding="utf-8").splitlines()[0]
    assert first == str(out / "TIME_BACKTEST_iter1.md") and (out / "TIME_BACKTEST_iter2.md").exists()
    text = (out / "TIME_BACKTEST_iter1.md").read_text(encoding="utf-8")
    assert "0 of 0 clocked episodes under 6 h" in text and "UNMEASURED" in text and "%" not in text
    rows = json.loads((out / "results" / "time_backtest.json").read_text(encoding="utf-8"))
    assert rows[0]["check"] == "time_backtest_loo" and rows[0]["n_distinct"] == 4
    boxed = tmp_path / "visurena_rehearsal" / "library"
    assert tb.main(["--library", str(boxed), "--out-dir", str(out), "--episodes", "j:1"]) == 2
