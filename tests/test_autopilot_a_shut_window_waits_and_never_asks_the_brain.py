"""A shut usage window is a wait, never a stop the brain reads (group R ruling A1,
2026-10-22).  Before: a step's RateLimited ended the drive on a Traceback, the
hand-back table sent it to the brain, the brain's own session hit the same shut
window three times, and the episode parked `brain_exhausted` -- on a day the weekly
window was projected full at about 09:20 PDT with a Monday 09:00 reset (skeptic M1).

Now the drive's `usage window <w> shut until <epoch>` line is the state WAIT_QUOTA:
not a stop on the relaunch cap, no brain call while it lasts, one global
library/.autopilot/quota.json (one login is one pool, so three books never each
probe it), one Telegram with the wake time in Seattle time, and a relaunch on the
first tick past resets_at + 90 s.  An unsaid reset re-checks in 30 min; a wait
past 8 days (the weekly window's reach, skeptic m4) parks with the raw line."""
from __future__ import annotations

import json
from types import SimpleNamespace

from studio import autopilot as ap
from studio import brain
from studio.autopilot import State
from tests import autopilot_cli_fixtures as fx
from tests.test_autopilot_derives_state_from_disk import SHA, rows, signals

NOW = 1_793_000_000.0
RESETS = NOW + 3600
TAIL = ("Traceback (most recent call last):\n  File \"episode.py\", line 9, in <module>\n"
        f"studio.brain.RateLimited: {brain.RateLimited(RESETS, 'seven_day')}")
UNSAID = f"studio.brain.RateLimited: {brain.RateLimited(None, 'said')}"


def quota_rows(error: str = "studio.brain.RateLimited") -> list[dict]:
    return [{"event": "start", "sha": SHA}, {"event": "run", "n": 1, "sha": SHA, "outcome": "failed", "error": error},
            {"event": "end", "code": 1, "sha": SHA}]


# --- the pure core -------------------------------------------------------------

def test_the_drive_line_is_a_quota_hand_back_before_the_traceback_row():
    kind, reason, order = ap.classify(TAIL, {"plan.json"})
    assert kind == "quota" and "usage window seven_day shut until" in reason and order is None


def test_the_line_reads_back_its_window_and_epoch():
    assert ap.quota_of(TAIL) == ("seven_day", RESETS)
    assert ap.quota_of(UNSAID) == ("said", None)
    assert ap.quota_of("KeyError: 0") is None


def test_a_quota_stop_derives_wait_quota_never_the_brain():
    got = ap.derive(signals(drive_rows=quota_rows(), log_tail=TAIL), 20)
    assert got.state is State.WAIT_QUOTA and "seven_day" in got.reason


def test_a_quota_stop_is_not_counted_against_the_relaunch_cap():
    assert ap.stops(quota_rows()) == 0
    assert ap.stops(quota_rows("KeyError")) == 1
    assert ap.stops(quota_rows() * 3 + quota_rows("KeyError")) == 1


# --- the supervisor --------------------------------------------------------------

def _act(tmp_path, now: float, tail: str = TAIL, drive_rows=None, d=None):
    cli, book = fx.load(), fx.book(tmp_path)
    d = d or fx.deps(tmp_path, "WAIT_QUOTA", now=lambda: now)
    d.now = lambda: now
    sig = SimpleNamespace(log_tail=tail, drive_rows=drive_rows or quota_rows(), engine_up=True, lock=None,
                          proc_alive=False, brain_attempts=0)
    return cli.act(book, fx.CODEX, 20, fx.derived("WAIT_QUOTA", "quota: x"), sig, d), d, cli


def _quota(d) -> dict:
    return json.loads((d.root / "quota.json").read_text(encoding="utf-8"))


def test_a_shut_window_waits_in_one_global_file_and_tells_once(tmp_path):
    out, d, _ = _act(tmp_path, NOW)
    assert out["state"] == "WAIT_QUOTA" and d.calls["popen"] == []
    assert _quota(d)["not_before"] == RESETS + 90 and d.root.name == ".autopilot"
    assert len(d.calls["notify"]) == 1 and "Seattle" in d.calls["notify"][0]
    out, d, _ = _act(tmp_path, NOW + 600, d=d)
    assert out["state"] == "WAIT_QUOTA" and d.calls["popen"] == [] and len(d.calls["notify"]) == 1


def test_past_the_reset_the_episode_relaunches_once(tmp_path):
    _, d, cli = _act(tmp_path, NOW)
    out, d, cli = _act(tmp_path, RESETS + 91, d=d)
    assert out["state"] == "RUNNING" and len(d.calls["popen"]) == 1
    events = [r["event"] for r in cli.rows_of(fx.book(tmp_path) / "autopilot" / "events.jsonl")]
    assert "quota_wait" in events and "quota_open" in events


def test_an_unsaid_reset_rechecks_in_thirty_minutes(tmp_path):
    _, d, _ = _act(tmp_path, NOW, tail=UNSAID)
    assert _quota(d)["not_before"] == NOW + 1800


def test_a_wait_past_eight_days_parks_with_the_line(tmp_path):
    far = f"studio.brain.RateLimited: {brain.RateLimited(NOW + 9 * 86400, 'seven_day')}"
    out, d, cli = _act(tmp_path, NOW, tail=far)
    assert out["state"] == "PARKED"
    parked = cli.rows_of(fx.book(tmp_path) / "autopilot" / "parked.jsonl")
    assert parked[0]["reason"].startswith("quota_wait_too_long")


def test_a_shut_brain_session_burns_no_attempt_and_waits(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)

    def shut(*a):
        raise brain.RateLimited(RESETS, "five_hour")
    d = fx.deps(tmp_path, "NEEDS_BRAIN", brain=shut, now=lambda: NOW)
    sig = SimpleNamespace(log_tail="KeyError: 0", drive_rows=quota_rows("KeyError"), brain_attempts=0, failed_sha=None)
    out = cli.act(book, fx.CODEX, 20, fx.derived("NEEDS_BRAIN", "failed: KeyError: 0"), sig, d)
    assert out["state"] == "WAIT_QUOTA"
    assert not (book / "episodes" / "ep20" / "brain").exists() or not list((book / "episodes" / "ep20" / "brain").iterdir())
    assert _quota(d)["not_before"] == RESETS + 90 and len(d.calls["notify"]) == 1


def test_no_brain_is_asked_while_the_window_is_shut(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    asked = []
    d = fx.deps(tmp_path, "NEEDS_BRAIN", brain=lambda *a: asked.append(a) or {"verdict": "park"}, now=lambda: NOW)
    (d.root).mkdir(parents=True, exist_ok=True)
    (d.root / "quota.json").write_text(json.dumps({"not_before": RESETS, "stop": "other"}), encoding="utf-8")
    sig = SimpleNamespace(log_tail="KeyError: 0", drive_rows=quota_rows("KeyError"), brain_attempts=0, failed_sha=None)
    out = cli.act(book, fx.CODEX, 20, fx.derived("NEEDS_BRAIN", "failed: KeyError: 0"), sig, d)
    assert out["state"] == "WAIT_QUOTA" and asked == []
