"""Integration of lanes C and D (2026-10-06): the CLI's `run_brain` builds its
prompt through `studio.brain.brief` from the disk evidence (deferred faults,
learnings tail, spend) and maps the brain's `Verdict` (response, reason, order,
commit, finding_row) onto the dict the supervisor judges (verdict, why, ...);
`judge_verdict` honours every triage answer -- retry relaunches on a clean tree,
cure places the order then relaunches, park parks -- not only relaunch.  $0."""
from __future__ import annotations

import json

from studio import brain
from tests.autopilot_cli_fixtures import CODEX, book, deps, load


def _home(root, n=2):
    home = root / "episodes" / f"ep{n:02d}"
    home.mkdir(parents=True)
    (home / "plan.deferred.json").write_text(json.dumps(
        {"faults": [{"note": "G-STORY shots 2-10: narration-only run"}, {"note": "G-SYNC line 3"}]}), encoding="utf-8")
    (home / "learnings.jsonl").write_text(json.dumps({"gate": "PLAN", "action": "keep_best"}) + "\n", encoding="utf-8")
    return home


def test_run_brain_briefs_from_disk_and_maps_the_verdict(tmp_path, monkeypatch):
    cli = load()
    root = book(tmp_path)
    home = _home(root)
    seen = {}

    async def fake_turn(prompt, options, *, transport=None):
        seen["prompt"] = prompt
        return brain.Verdict(response="cure", order={"kind": "redo", "step_id": "02"}, reason="speech hole",
                             finding_row="| F? | hole | 0 | redo 02 | open |"), {"session_id": "s1", "total_cost_usd": 0.2}

    monkeypatch.setattr(brain, "turn", fake_turn)
    monkeypatch.setattr(brain, "triage_options", lambda repo: None)
    packet = {"home": "episodes/ep02", "last_line": "DEFERRED PLAN | x", "media_spent_usd": 3.1}
    doc = cli.run_brain(root, CODEX, 2, packet, home / "brain" / "attempt_01.json")
    assert "G-STORY shots 2-10" in seen["prompt"] and "keep_best" in seen["prompt"] and "$3.10" in seen["prompt"]
    assert "D:\\" not in seen["prompt"] and "C:\\" not in seen["prompt"]
    assert doc["verdict"] == "cure" and doc["why"] == "speech hole" and doc["order"] == {"kind": "redo", "step_id": "02"}
    assert doc["finding_row"].startswith("| F?") and doc["meta"]["session_id"] == "s1"


def test_judge_verdict_honours_retry_and_cure(tmp_path):
    cli = load()
    root = book(tmp_path)
    d = deps(tmp_path)
    assert cli.judge_verdict(root, CODEX, 2, {"verdict": "retry", "why": "transient"}, d)["state"] == "IDLE"
    out = cli.judge_verdict(root, CODEX, 2, {"verdict": "cure", "order": {"kind": "redo", "step_id": "08"}}, d)
    assert out["state"] == "IDLE" and d.calls["orders"] == [(CODEX, 2, {"kind": "redo", "step_id": "08"})]


def test_judge_verdict_still_rejects_a_relaunch_off_head(tmp_path):
    cli = load()
    root = book(tmp_path)
    d = deps(tmp_path)
    assert cli.judge_verdict(root, CODEX, 2, {"verdict": "relaunch", "commit": "not-head"}, d)["state"] == "NEEDS_BRAIN"
