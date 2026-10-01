"""ep15 (2026-10-01): the master passed QC, every taste-gate terminal was
judge-signed under gates.yaml `auto` (decision 2026-09-24-automate-the-taste-
gates) -- and the publish lock still demanded an owner-hand waiver.json per
episode, the pre-judges design from the ep12 root cause (2026-09-26).  ep13
and ep14 masked the gap with per-episode owner orders.  The owner's explicit
ruling (2026-10-01, "Remove that human waiver .. we need automation"): a
terminal on an `auto` gate clears the lock under its decision id, recorded in
the upload ledger with the judge's name; a terminal on a gate that is NOT
auto (or unknown to gates.yaml) still needs the owner's hand -- the ep12
lesson stays.  $0: yaml and json on tmp paths."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from studio import publish_lock
from studio.learnings import Learning, record


def home_with(tmp_path: Path, gates: list[str]) -> Path:
    for g in gates:
        record(tmp_path / "learnings.jsonl",
               Learning(step="x", gate=g, action="keep_best", terminal=True, note="flagged"))
    (tmp_path / "review").mkdir(exist_ok=True)
    return tmp_path


def test_an_auto_gates_terminal_is_waived_by_its_judge(tmp_path):
    home = home_with(tmp_path, ["MASTER", "EYE_TAKES"])
    got = publish_lock.judge_waivers(home)
    assert set(got) == {"MASTER", "EYE_TAKES"}
    assert "judge:master_eye@1" in got["MASTER"]
    assert "2026-09-24-automate-the-taste-gates" in got["MASTER"]


def test_a_gate_outside_the_registry_still_needs_the_owner(tmp_path):
    home = home_with(tmp_path, ["SOME_NEW_GATE"])
    assert publish_lock.judge_waivers(home) == {}          # not auto = not cleared
    held = [s for s in publish_lock.stops(home, "abcd1234") if s.startswith("SOME_NEW_GATE")]
    assert held                                            # the ep12 lesson stays


def test_stops_clears_judge_signed_terminals_but_keeps_the_signoff(tmp_path):
    home = home_with(tmp_path, ["MASTER"])
    stops = publish_lock.stops(home, "abcd1234")
    assert not any(s.startswith("MASTER") for s in stops)  # judge-cleared
    assert any("director_signoff" in s for s in stops)     # watching is still required


def test_the_upload_auto_override_covers_judged_takes_only():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "ytu", root / "scripts" / "publish" / "youtube_upload.py")
    ytu = importlib.util.module_from_spec(spec)
    sys.modules["ytu"] = ytu
    spec.loader.exec_module(ytu)
    judged = ["T00", "T03 (content: someone missing)"]
    assert "2026-10-01" in ytu.auto_override(judged)
    assert ytu.auto_override(judged + ["T09 (never judged)"]) == ""   # unjudged still stops
    assert ytu.auto_override([]) == ""                                # nothing to waive
