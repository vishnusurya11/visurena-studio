"""Jekyll ep07 retro S3, the tick's half: every tick looks at the parked episodes, and one the chain
carried to step 13 with standing approval is told 'FINISHED, NOT PUBLISHED' with its reason and the
retry command; the event records whether the send went out (ep07's `youtube_token_told` did not)."""
from __future__ import annotations

import json

from studio import standing_approval
from tests import autopilot_cli_fixtures as fx

H = 3600.0


def _setup(tmp_path, step="13"):
    cli, book = fx.load(), fx.book(tmp_path)
    home = book / "episodes" / "ep07"
    home.mkdir(parents=True)
    (home / "drive.jsonl").write_text("\n".join(json.dumps(r) for r in (
        {"event": "start"}, {"event": "run", "n": 19, "outcome": "failed", "step": step},
        {"event": "end", "code": 1})) + "\n", encoding="utf-8")
    (book / "publish").mkdir()
    (book / "publish" / "standing.json").write_text(json.dumps(
        {"kind": "publish", "decision": standing_approval.DECISION, "by": "owner", "episodes": [7]}), encoding="utf-8")
    parked = [{"episode": 7, "reason": "youtube_token_expired: run youtube_auth.py"}]
    return cli, book, parked


def test_a_parked_master_at_publish_is_told_with_reason_and_retry(tmp_path):
    cli, book, parked = _setup(tmp_path)
    clock = [100 * H]
    d = fx.deps(tmp_path, now=lambda: clock[0])
    d.notify = lambda text: d.calls["notify"].append(text) or True
    assert cli.nudge_parked(book, parked, [], d) == [7]
    said = d.calls["notify"][-1]
    assert said.startswith("ep07 FINISHED, NOT PUBLISHED: youtube_token_expired") and "retry 7" in said
    rows = [r for r in cli.rows_of(book / "autopilot" / "events.jsonl") if r["event"] == "owner_nudge"]
    assert rows[-1]["episode"] == 7 and rows[-1]["sent"] is True
    clock[0] += 3 * H
    assert cli.nudge_parked(book, parked, [], d) == []
    clock[0] += 4 * H
    assert cli.nudge_parked(book, parked, [], d) == [7]


def test_an_episode_parked_before_publish_is_not_nudged(tmp_path):
    cli, book, parked = _setup(tmp_path, step="11")
    d = fx.deps(tmp_path, now=lambda: 100 * H)
    assert cli.nudge_parked(book, parked, [], d) == []
    assert d.calls["notify"] == []


def test_a_failed_send_is_logged_unsent(tmp_path):
    cli, book, parked = _setup(tmp_path)
    d = fx.deps(tmp_path, now=lambda: 100 * H)
    d.notify = lambda text: False
    cli.nudge_parked(book, parked, [], d)
    rows = [r for r in cli.rows_of(book / "autopilot" / "events.jsonl") if r["event"] == "owner_nudge"]
    assert rows[-1]["sent"] is False
