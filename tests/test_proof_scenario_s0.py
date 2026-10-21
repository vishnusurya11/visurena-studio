"""S0a and S0b (2026-10-21_ep02_proof DESIGN 3.2): the real pipeline on the real book's sandbox,
answered by the fakes.  Marked `rehearsal` (excluded by default): each runs minutes, needs the
fake ComfyUI (P3), the fakes and SDK transport (P4) and the recordings index (P2), and refuses to
start while the real Task Scheduler entry is enabled or a real series is unpaused.

S0a's pre-registered prediction (section 0, R1): every built take's field diff against ep01's
recorded graph of the same index and try count has ZERO unexplained differences, each one listed.
S0b's (R2): a named park, OR HELD_PUBLISH with every unresolved content refusal on the publish card
AND a lock that is not auto-clearable; upload-ready with an auto-clearable lock is FAILING (Q6)."""
from __future__ import annotations

import json

import pytest

from scripts.proof import rehearse

pytestmark = pytest.mark.rehearsal


def run(sid: str, tmp_path) -> tuple[dict, dict]:
    missing = rehearse.missing_packages(sid)
    if missing:
        pytest.skip(f"{sid} stands on {', '.join(missing)}, not on disk yet")
    out = rehearse.run_scenario(sid, results=tmp_path / "results", wall=4 * 3600.0)
    if out.get("blocked"):
        pytest.skip(f"{sid} did not run: {out['blocked']}")
    doc = json.loads((tmp_path / "results" / f"{sid}.json").read_text(encoding="utf-8"))
    return out, {r["check"]: r for r in doc["rows"]}


def test_s0a_replays_ep01_to_held_publish_with_no_unexplained_take_difference(tmp_path):
    out, rows = run("S0a", tmp_path)
    assert out["supervisor"]["terminal"] == "HELD_PUBLISH", out
    assert rows["S0a"]["n_points"] > 0
    assert rows["S0a"]["passed"], rows["S0a"]["detail"]


def test_s0a_leaves_a_checkpoint_at_every_between_steps_boundary_it_reached(tmp_path):
    out, _ = run("S0a", tmp_path)
    made = out["supervisor"].get("checkpoints") or []
    assert "after_08" in made, made


def test_s0b_ends_in_its_one_pre_registered_outcome(tmp_path):
    _, rows = run("S0b", tmp_path)
    assert rows["S0b"]["question"] == "Q6"
    assert rows["S0b"]["passed"], rows["S0b"]["detail"]
