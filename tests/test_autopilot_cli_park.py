"""PARKED is a record, never a wait: one row, one Telegram, and the series
moves on; Telegram speaks only on PUBLISHED, PARKED, SERIES_COMPLETE and a
tree dirty past six hours (decision 2026-10-06 §Layer 1)."""
from __future__ import annotations

import json

from tests import autopilot_cli_fixtures as fx


def _events(cli, book):
    return [r["event"] for r in cli.rows_of(book / "autopilot" / "events.jsonl")]


def test_parked_row_is_written_once_and_telegram_once(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "PARKED", reason="over_budget")
    for i in (1, 2, 3):
        cli.tick(book, fx.CODEX, d, i)
    rows = cli.rows_of(book / "autopilot" / "parked.jsonl")
    # the drift brake pauses the series after two consecutive parks; ep3 never launches
    assert [(r["episode"], r["reason"]) for r in rows] == [(1, "over_budget"), (2, "over_budget")]
    assert [("PARKED" in t) for t in d.calls["notify"]] == [True, True, False]
    assert set(rows[0]) >= {"ts", "episode", "sha", "reason", "evidence"}


def test_telegram_only_on_published_parked_complete(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    for state in ("IDLE", "RUNNING", "WAIT_TREE", "BRAIN_RUNNING", "NEEDS_BRAIN"):
        d = fx.deps(tmp_path, state, reason="x", brain=lambda *a: {"verdict": "none"})
        cli.tick(book, fx.CODEX, d, 1)
        assert d.calls["notify"] == [], state
    (book / "uploads.jsonl").write_text(json.dumps({"episode": 1, "privacy": "public", "video_id": "abc"}) + "\n",
                                        encoding="utf-8")
    d = fx.deps(tmp_path, "PUBLISHED")
    d.next_unit = lambda *a: 1
    cli.tick(book, fx.CODEX, d, 1)
    cli.tick(book, fx.CODEX, d, 2)
    assert d.calls["notify"] == ["ep01 PUBLISHED https://youtu.be/abc"]


def test_a_tree_dirty_past_six_hours_is_told_once(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    clock = [1_000_000.0]
    d = fx.deps(tmp_path, "WAIT_TREE", now=lambda: clock[0])
    for _ in range(3):
        cli.tick(book, fx.CODEX, d, 1)
        clock[0] += 4 * 3600
    assert len(d.calls["notify"]) == 1 and "dirty" in d.calls["notify"][0]


def test_retry_clears_the_parked_row(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "PARKED", reason="clock_spent")
    cli.tick(book, fx.CODEX, d, 1)
    cli.tick(book, fx.CODEX, d, 2)
    assert [r["episode"] for r in cli.rows_of(book / "autopilot" / "parked.jsonl")] == [1, 2]
    assert cli.retry(book, 1) == 1
    assert [r["episode"] for r in cli.rows_of(book / "autopilot" / "parked.jsonl")] == [2]
    assert _events(cli, book)[-1] == "retry"
    assert cli.retry(book, 1) == 0


def test_park_cli_writes_the_row_with_the_owners_reason(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "IDLE")
    cli.park(book, fx.CODEX, 2, "owner: wait for the cast fix", {}, d)
    cli.park(book, fx.CODEX, 2, "owner: again", {}, d)
    rows = cli.rows_of(book / "autopilot" / "parked.jsonl")
    assert len(rows) == 1 and rows[0]["reason"] == "owner: wait for the cast fix"
    assert len(d.calls["notify"]) == 1


def test_pause_and_resume_flip_the_series_flag(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "IDLE")
    cli.set_paused(book, fx.CODEX, True)
    assert cli.tick(book, fx.CODEX, d, 1)["episode"]["state"] == "PAUSED" and d.calls["popen"] == []
    cli.set_paused(book, fx.CODEX, False)
    assert cli.tick(book, fx.CODEX, d, 2)["episode"]["state"] == "RUNNING"


def test_a_cure_order_is_placed_then_the_run_relaunched(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "NEEDS_BRAIN", reason="panels", order="redo 08")
    doc = cli.tick(book, fx.CODEX, d, 1)
    assert d.calls["orders"] == [(fx.CODEX, 1, "redo 08")]
    assert len(d.calls["popen"]) == 1 and doc["episode"]["state"] == "RUNNING"


def test_parse_order_reads_a_string_or_a_dict():
    cli = fx.load()
    assert cli.parse_order("redo 08") == ("redo", "08")
    assert cli.parse_order({"kind": "retry"}) == ("retry", None)
    assert cli.parse_order("requeue") == ("requeue", None)


def test_the_brain_is_trusted_by_its_file_and_git_not_its_prose(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    home = book / "episodes" / "ep01"

    def liar(book_, codex, n, packet, path):
        return {"verdict": "relaunch", "commit": "not-the-head", "why": "trust me"}
    d = fx.deps(tmp_path, "NEEDS_BRAIN", reason="failed: KeyError", brain=liar)
    doc = cli.tick(book, fx.CODEX, d, 1)
    assert (home / "brain" / "attempt_01.json").exists()
    assert d.calls["popen"] == [] and doc["episode"]["state"] == "NEEDS_BRAIN"
    assert doc["episode"]["brain_attempts"] == 1

    def honest(book_, codex, n, packet, path):
        return {"verdict": "relaunch", "commit": "abc123def", "why": "fixed"}
    d.brain = honest
    doc = cli.tick(book, fx.CODEX, d, 2)
    assert doc["episode"]["state"] == "IDLE" and doc["episode"]["brain_attempts"] == 2


def test_brain_attempts_past_the_cap_park_the_episode(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    home = book / "episodes" / "ep01" / "brain"
    home.mkdir(parents=True)
    for i in range(1, cli.BRAIN_ATTEMPTS + 1):
        (home / f"attempt_{i:02d}.json").write_text(json.dumps({"verdict": "none"}), encoding="utf-8")
    d = fx.deps(tmp_path, "NEEDS_BRAIN", reason="failed")
    doc = cli.tick(book, fx.CODEX, d, 1)
    assert doc["episode"]["state"] == "PARKED"
    assert cli.rows_of(book / "autopilot" / "parked.jsonl")[0]["reason"] == "brain_exhausted"


def test_retry_retires_the_episodes_brain_attempts(tmp_path):
    """ep20 (2026-10-06): a retry cleared the parked row, the next tick re-read the
    old attempt_01 (park) as the current verdict and asked the brain again."""
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path, "PARKED", reason="over_budget")
    cli.tick(book, fx.CODEX, d, 1)
    home = book / "episodes" / "ep01"
    (home / "brain").mkdir(parents=True)
    (home / "brain" / "attempt_01.json").write_text('{"verdict": "park"}', encoding="utf-8")
    assert cli.retry(book, 1) == 1
    assert cli.brain_attempts_of(home) == []
    assert (home / "brain_retired_01" / "attempt_01.json").exists()


def test_after_a_retry_the_next_tick_launches_instead_of_judging_the_old_ledger(tmp_path):
    """ep20 (2026-10-06): retry cleared the row, the tick re-derived the OLD end
    row (failed) and asked the brain again.  A retry newer than the last end row
    reads as a fresh launch; drive.py's resume skips the steps already done."""
    cli, book = fx.load(), fx.book(tmp_path)
    home = book / "episodes" / "ep01"
    home.mkdir(parents=True)
    (home / "drive.jsonl").write_text(
        '{"ts": "2026-10-06T10:00:00+00:00", "event": "start", "sha": "abc"}\n'
        '{"ts": "2026-10-06T10:00:30+00:00", "event": "run", "n": 1, "sha": "abc", "outcome": "failed"}\n'
        '{"ts": "2026-10-06T10:00:31+00:00", "event": "end", "code": 1, "sha": "abc"}\n', encoding="utf-8")
    cli.park(book, fx.CODEX, 1, "brain: x", {}, fx.deps(tmp_path))
    assert cli.retry(book, 1) == 1
    signals = cli.gather(book, fx.CODEX, 1, fx.deps(tmp_path), {})
    assert signals.drive_rows == [] and signals.exit_code is None


def test_two_parks_in_a_row_pause_the_series_and_tell_once(tmp_path):
    """The approved design's drift brake (2026-10-06): ep20 and ep21 parked back
    to back on one bug and nothing stopped ep22 from following.  Two consecutive
    parked chapters mean the fault is the code, not the chapters: the series
    pauses itself, one Telegram, and the next tick is PAUSED, not a launch."""
    cli, book = fx.load(), fx.book(tmp_path, chapters=4)
    d = fx.deps(tmp_path, "PARKED", reason="brain: same 400")
    cli.tick(book, fx.CODEX, d, 1)
    assert cli.read_json(book / "autopilot" / "series.json").get("paused") is not True
    cli.tick(book, fx.CODEX, d, 2)
    assert cli.read_json(book / "autopilot" / "series.json")["paused"] is True
    assert "two_parked_in_a_row" in _events(cli, book)
    assert sum("two chapters parked in a row" in t for t in d.calls["notify"]) == 1
    before = len(cli.rows_of(book / "autopilot" / "parked.jsonl"))
    out = cli.tick(book, fx.CODEX, d, 3)
    assert out["episode"]["state"] == "PAUSED" and len(cli.rows_of(book / "autopilot" / "parked.jsonl")) == before


def test_retry_of_an_unparked_episode_still_retires_attempts_and_reads_as_a_launch(tmp_path):
    """ep21 (2026-10-07): `retry 21` on an episode that had failed but not parked
    returned early ('0 parked rows cleared'); the next tick re-judged the old
    end row and paid the brain.  A retry is a launch order, parked or not."""
    cli, book = fx.load(), fx.book(tmp_path)
    home = book / "episodes" / "ep01"
    (home / "brain").mkdir(parents=True)
    (home / "brain" / "attempt_01.json").write_text('{"verdict": "park"}', encoding="utf-8")
    (home / "drive.jsonl").write_text(
        '{"ts": "2026-10-06T10:00:00+00:00", "event": "start", "sha": "abc"}\n'
        '{"ts": "2026-10-06T10:00:31+00:00", "event": "end", "code": 1, "sha": "abc"}\n', encoding="utf-8")
    assert cli.retry(book, 1) == 0
    assert cli.brain_attempts_of(home) == [] and _events(cli, book)[-1] == "retry"
    assert cli.gather(book, fx.CODEX, 1, fx.deps(tmp_path), {}).drive_rows == []
