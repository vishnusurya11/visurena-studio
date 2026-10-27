"""Jekyll ep03 retro #4: the brain ordered `redo 06` with a correct one-line diff and no
commit; the autopilot relaunched the unchanged code and paid a second attempt.  A verdict
that carries a proposed_diff and no commit is a CODE fault: park it for the fixer rung.
$0."""
from __future__ import annotations

import json

from tests import autopilot_cli_fixtures as fx

FIXTURE = fx.ROOT / "tests" / "fixtures" / "brain_cure_with_diff.json"


def test_a_cure_with_a_diff_and_no_commit_parks_with_the_diff(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    verdict = json.loads(FIXTURE.read_text(encoding="utf-8"))
    out = cli.judge_verdict(book, fx.CODEX, 3, verdict, d)
    rows = cli.rows_of(book / "autopilot" / "parked.jsonl")
    assert out["state"] == "PARKED" and d.calls["orders"] == []
    assert rows[0]["reason"].startswith("brain:") and "leans" in rows[0]["evidence"]["proposed_diff"]


def test_a_cure_without_a_diff_still_places_its_order(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    out = cli.judge_verdict(book, fx.CODEX, 3, {"verdict": "cure", "order": {"kind": "redo", "step_id": "06"},
                                                "proposed_diff": ""}, d)
    assert out["state"] == "IDLE" and len(d.calls["orders"]) == 1


def test_a_cure_with_a_diff_and_a_commit_is_a_landed_fix(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    verdict = {"verdict": "cure", "commit": "abc123", "order": {"kind": "redo", "step_id": "06"}, "proposed_diff": "--- a"}
    assert cli.judge_verdict(book, fx.CODEX, 3, verdict, d)["state"] == "IDLE"
