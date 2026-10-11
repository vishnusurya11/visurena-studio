"""C3_verdict #5 (D3): at the 5 h ceiling, take the best, flag it and continue.

(i)   Firsts are never refused, only repeats: a spent clock with 10 of 24
      takes on disk raised "REFUSED: the takes want ..." and the episode could
      never finish (step_09_shoot.round_zero meant "no take at all").
(ii)  The autopilot never parks on the clock; a dead drive relaunches into
      terminal mode.  A third spent-clock stop in a row parks `clock_loop`
      (a backstop, not a policy).
(iii) The driver resumes a deferral whatever the clock says.
(iv)  The plan battery's lines are BUILDER (a downstream script repeats the
      refusal) or JUDGED.  At a spent clock a JUDGED-only best draft signs
      keep_best flagged; a BUILDER line climbs once more (<= 3 rungs) and then
      stops as a SAFETY refusal.
(v)   Only the closed SAFETY list (gate_policy.SAFETY) stops a spent-clock
      episode; a QC fail on a sound cue ships flagged, a line not heard stops."""
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from studio import episode_drive, gate_policy, plan_tags
from studio.run_budget import EPISODE_CEILING_SECONDS

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


step09 = _load("step09_c3", "scripts/episode/step_09_shoot.py")
qc = _load("qc_c3", "scripts/episode/qc.py")


# ---- (i) firsts render, repeats stop --------------------------------------------------

def _spent_ctx(tmp_path, on_disk: int, of: int, ran: list):
    home = tmp_path / "ep20"
    room = home / step09.TAKES
    room.mkdir(parents=True)
    (home / "plan.json").write_text(json.dumps({"shots": [{"index": i} for i in range(of)]}), encoding="utf-8")
    for i in range(on_disk):
        (room / f"T{i:02d}.mp4").write_bytes(b"take")
    return SimpleNamespace(home=home, book_dir=tmp_path, number=20, stage="episode", extra=[],
                           log=lambda *a, **k: None,
                           run_script=lambda script, *a, **k: ran.append((script, a)))


def test_a_spent_clock_renders_the_missing_takes_and_no_retake(tmp_path, monkeypatch):
    ran = []
    ctx = _spent_ctx(tmp_path, on_disk=10, of=24, ran=ran)
    monkeypatch.setattr(step09, "panel_refusals", lambda home: [])
    monkeypatch.setattr(step09, "approved", lambda policy: "--approved=x")
    monkeypatch.setattr(step09.gate_policy, "of", lambda stage, gate: None)
    monkeypatch.setattr(step09, "affordable", lambda ctx: (False, 4000.0, -60.0))
    monkeypatch.setattr(step09.take_ladder, "measured", lambda *a, **k: None)
    judged = []
    monkeypatch.setattr(step09, "judge_takes", lambda ctx, flag: judged.append(flag))
    step09.run(ctx)                                   # today: REFUSED: the takes want 4000 s ...
    assert ran[0][0] == "scripts/episode/takes_r2v.py" and "--retake" not in " ".join(ran[0][1])
    assert judged == ["--approved=x"]                 # the take ladder at a spent clock is terminal


def test_step_09_never_refuses_on_the_clock():
    import inspect
    assert "REFUSED: the takes want" not in inspect.getsource(step09.run)


# ---- (ii) and (e): the autopilot -------------------------------------------------------

ap = _load("ap_core_c3", "studio/autopilot.py")


def _signals(**kw):
    from tests.test_autopilot_derives_state_from_disk import signals
    return signals(**kw)


def _rows(*events):
    from tests.test_autopilot_derives_state_from_disk import rows
    return rows(*events)


def test_a_dead_drive_on_a_spent_clock_relaunches():
    got = ap.derive(_signals(drive_rows=_rows(("start",)), clock_spent_s=EPISODE_CEILING_SECONDS + 1), 20)
    assert got.state is ap.State.IDLE and got.reason == "relaunch"


def test_a_spent_clock_stop_is_read_like_any_other():
    got = ap.derive(_signals(drive_rows=_rows(("start",), ("run", "refused"), ("end", 1)),
                             clock_spent_s=EPISODE_CEILING_SECONDS, log_tail="REFUSED: qc FAIL"), 20)
    assert (got.state, got.reason) != (ap.State.PARKED, "clock_spent")


def _spent_end(code=1):
    return {"event": "end", "code": code, "sha": "x", "clock_spent": True}


def test_a_third_spent_clock_stop_in_a_row_parks_clock_loop():
    start = {"event": "start", "sha": "x"}
    drive = [start, _spent_end(), start, _spent_end(), start, _spent_end()]
    got = ap.derive(_signals(drive_rows=drive, clock_spent_s=EPISODE_CEILING_SECONDS + 1,
                             log_tail="REFUSED: qc FAIL"), 20)
    assert (got.state, got.reason) == (ap.State.PARKED, "clock_loop")
    two = ap.derive(_signals(drive_rows=drive[2:], clock_spent_s=EPISODE_CEILING_SECONDS + 1,
                             log_tail="REFUSED: qc FAIL"), 20)
    assert two.reason != "clock_loop"


def test_a_safety_stop_parks_by_its_own_name():
    got = ap.derive(_signals(drive_rows=_rows(("start",), ("run", "refused"), ("end", 1)),
                             clock_spent_s=EPISODE_CEILING_SECONDS + 1,
                             log_tail="SAFETY: line_unheard: qc_r2v.json lines 3, 7 not heard"), 20)
    assert got.state is ap.State.PARKED and got.reason.startswith("safety")


# ---- (iii) the driver -------------------------------------------------------------------

def test_the_driver_resumes_a_deferral_whatever_the_clock():
    ran = []
    logs = iter(["DEFERRED: EYE_TAKES needs 565 s for its rung", "=== EPISODE completed | ep20 ==="])
    code = episode_drive.drive(lambda: ran.append(1) or next(logs), lambda text: None)
    assert code == 0 and len(ran) == 2


# ---- (iv) the plan battery's tags ---------------------------------------------------------

OUT = """CONTRACT OK: The Yard | 24 shots | 140s projected
G-LIGHT      : clean
PLAN GATES   : clean
G-CROWD      : ['shot 4: seven walk-ons']
    shot 4: seven walk-ons
G-ARTICLE    : 1
    shot 2: 'a the'
CAST BOUND   : all bound
ONE PER TAKE : [(3, 4)]
TAKE LENGTH  : every shot inside a take (at 2.90 words/s, budget 8.0 s)
G-TAKELINT   : 1
    G-TAKELINT shot 9: 'slowly' [plan]
VERDICT      : REFUSED"""


def test_battery_lines_are_tagged_builder_or_judged():
    lines = [line for line in OUT.splitlines() if line.strip()]
    assert plan_tags.builder_lines(lines) == ["G-TAKELINT   : 1", "    G-TAKELINT shot 9: 'slowly' [plan]"]
    judged = [line for line in lines if line not in plan_tags.builder_lines(lines)]
    assert not plan_tags.builder_lines(judged)


def test_every_builder_label_cites_its_downstream_refusal():
    for label, cite in plan_tags.BUILDER.items():
        assert cite and "." in cite, label
    assert "ONE PER TAKE" not in plan_tags.BUILDER          # no downstream script refuses a packed run
    assert {"CONTRACT", "TAKE BUILDER", "G-TAKELINT", "TAKE LENGTH", "CAST BOUND"} <= set(plan_tags.BUILDER)


def test_a_contract_line_is_builder_and_contract_ok_is_not():
    assert plan_tags.builder_lines(["CONTRACT shots.3.line: no button"]) == ["CONTRACT shots.3.line: no button"]
    assert plan_tags.builder_lines(["CONTRACT: x :: y"]) == ["CONTRACT: x :: y"]
    assert plan_tags.builder_lines(["CONTRACT OK: The Yard | 24 shots"]) == []


# ---- (v) the SAFETY list and QC at a spent clock ------------------------------------------

def test_the_safety_list_is_closed():
    assert gate_policy.SAFETY == ("short_length", "title_card", "line_unheard", "takes_unjudged", "takes_stale",
                                  "loudness", "plan_builder", "money", "publish_auth", "gpu_lost")


GOOD = {"title_card": True, "lufs_ok": True, "tp_ok": True, "missing_cuts": [], "lines": [{"passed": True}],
        "edit": {"ok": True, "measured": True}, "seconds": 160.0, "sound": [{"ok": True}], "longest_gap_s": 1.0}


def test_failed_rows_name_every_verdict_condition():
    assert qc.failed_rows(GOOD) == [] and qc.verdict(GOOD)
    cases = {"sound": {"sound": [{"ok": False}]}, "line_unheard": {"lines": [{"passed": False}]},
             "missing_cuts": {"missing_cuts": [5.0]}, "loudness": {"lufs_ok": False},
             "title_card": {"title_card": False}, "short_length": {"seconds": 190.0},
             "gap": {"longest_gap_s": 99.0}, "takes_unjudged": {"takes": {"unjudged": ["T01"]}},
             "takes_stale": {"edit": {"ok": False, "measured": False}}, "edit": {"edit": {"ok": False, "measured": True}}}
    for name, patch in cases.items():
        report = {**GOOD, **patch}
        assert name in qc.failed_rows(report) and not qc.verdict(report), name


def test_a_spent_clock_hears_the_lines_past_a_flaggable_fail():
    calls = []
    cue_fail = {**GOOD, "sound": [{"ok": False}]}
    assert qc.with_lines(cue_fail, lambda: calls.append(1) or [], spent=False)["lines_measured"] is False
    assert qc.with_lines(cue_fail, lambda: calls.append(1) or [{"passed": True}], spent=True)["lines_measured"]
    assert qc.with_lines({**GOOD, "lufs_ok": False}, lambda: calls.append(1) or [], spent=True)["lines"] is None
    assert len(calls) == 1


step11 = _load("step11_c3", "scripts/episode/step_11_qc.py")


def _qc_ctx(tmp_path, report: dict, spent: bool):
    from studio import youtube_publish as yp
    from studio.run_budget import EPISODE_SHARES, Budget
    home = tmp_path / "ep20"
    (home / "cut").mkdir(parents=True)
    master, path = step11.pair(home, "r2v")
    master.write_bytes(b"master bytes")
    path.write_text(json.dumps(report | {"sha8": yp.sha8(master), "measures_sha8": step11.qc_measures_sha8()}),
                    encoding="utf-8")
    budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
    budget.charge(18001.0 if spent else 0.0)
    return SimpleNamespace(home=home, book_dir=tmp_path, unit="ep20", budget=budget, log=lambda *a, **k: None,
                           run_script=lambda *a, **k: None), path


def test_a_cue_fail_at_a_spent_clock_ships_flagged(tmp_path, monkeypatch):
    rows = []
    monkeypatch.setattr(step11.audit_rows, "append", lambda book, row: rows.append(row))
    ctx, path = _qc_ctx(tmp_path, {**GOOD, "sound": [{"ok": False}], "passed": False}, spent=True)
    report = step11.qc_report(ctx, ["--engine=r2v"])
    assert report["passed"] is True and report["ceiling_flagged"] == ["sound"]
    assert json.loads(path.read_text(encoding="utf-8"))["passed"] is True
    assert rows and rows[0]["terminal"] == "ceiling" and rows[0]["gate"] == "QC"


def test_a_line_not_heard_at_a_spent_clock_stops(tmp_path):
    ctx, _ = _qc_ctx(tmp_path, {**GOOD, "lines": [{"passed": False}], "passed": False}, spent=True)
    with pytest.raises(SystemExit, match="SAFETY: line_unheard"):
        step11.qc_report(ctx, ["--engine=r2v"])


def test_below_the_ceiling_a_cue_fail_is_still_refused(tmp_path):
    ctx, _ = _qc_ctx(tmp_path, {**GOOD, "sound": [{"ok": False}], "passed": False}, spent=False)
    with pytest.raises(SystemExit, match="REFUSED: qc FAIL"):
        step11.qc_report(ctx, ["--engine=r2v"])


def test_soft_motions_under_a_clean_header_are_not_builder():
    lines = ["MOTION hard  : clean", "    soft shot 3: a slow drift", "G-TAKELINT   : clean"]
    assert plan_tags.builder_lines(lines) == []
