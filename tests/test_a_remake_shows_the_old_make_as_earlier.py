"""A unit re-made from an early step shows the old make as EARLIER, not as current (page
experts 2026-10-18, A3/B3/B4).  Jekyll ep01 re-ran 02 plan while the head's bar ticked
06-12 done from the run before, step 13's old publish park was quoted as the head's reason
and as the Shots empty state, four signed gates were counted 'not passing' though their files
were gone (links 404), and a gate getting worse printed '→ stuck'."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from studio.command_center import unit_view as uv

NOW = datetime(2026, 10, 18, 21, 0, tzinfo=timezone.utc)
UNIT = Path(uv.__file__).resolve().parent / "templates" / "unit.html"
ROW = {"step_id": "02", "state": "running", "run_id": "R2"}


def chip(sid: str, state: str, run: str, detail=None) -> dict:
    return {"step_id": sid, "state": state, "css": "green", "glyph": "✓", "run_id": run,
            "ended_at": "2026-10-12T10:00:00Z", "detail": detail}


def bar(*chips) -> dict:
    return {s["step_id"]: s for s in uv.step_band(list(chips), ROW, [], [], NOW, timezone.utc)}


def test_a_later_step_from_another_run_reads_earlier():
    got = bar(chip("01", "done", "R1"), chip("02", "running", "R2"), chip("06", "done", "R1"))
    assert got["06"]["state"] == "earlier" and "earlier" in got["06"]["css"]
    assert got["01"]["state"] == "done" and got["02"]["state"] == "running"


def test_an_earlier_steps_reason_is_not_the_units_reason():
    got = bar(chip("13", "escalated", "R1", detail="OWNER G-STANDING: write the standing approval"))
    assert got["13"]["reason"] == ""
    # the Shots empty state may still say why, named as the earlier run's (ep08's 09 refusals)
    assert uv.take_wait(list(got.values())) == "an earlier run's 13 escalated: OWNER G-STANDING: write the standing approval"


def test_this_runs_reason_wins_over_an_earlier_ones():
    steps = [{"step_id": "08", "state": "failed", "reason": "panels refused"},
             {"step_id": "13", "state": "earlier", "reason": "", "was": "escalated", "was_reason": "old park"}]
    assert uv.take_wait(steps) == "08 failed: panels refused"


def test_a_finished_unit_keeps_its_runs_as_they_were():
    seg = uv.step_band([chip("06", "done", "R1")], {**ROW, "state": "done"}, [], [], NOW, timezone.utc)[0]
    assert seg["state"] == "done"


def test_a_signed_gate_whose_file_is_gone_is_earlier_not_failing():
    g = uv.gate_block({"gate": "MASTER", "state": "flagged", "path": "episodes/ep01/qc/master_eye.json",
                       "faults": 3}, None, "11")
    assert g["state"] == "earlier" and g["path"] is None and g["faults"] == 0
    assert "earlier make" in g["word"]


def test_a_readable_gate_is_untouched():
    g = uv.gate_block({"gate": "PLAN", "state": "passed", "path": "episodes/ep01/plan.verdict.json"},
                      {"verdict": "pass"}, "02")
    assert g["state"] == "passed" and g["path"]


def test_a_worsening_gate_reads_worse_not_stuck():
    html = UNIT.read_text(encoding="utf-8")
    assert "t.direction == 'worse'" in html and "↗ worse" in html
