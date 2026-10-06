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
    assert [(r["episode"], r["reason"]) for r in rows] == [(1, "over_budget"), (2, "over_budget"), (3, "over_budget")]
    assert len(d.calls["notify"]) == 3 and all("PARKED" in t for t in d.calls["notify"])
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
