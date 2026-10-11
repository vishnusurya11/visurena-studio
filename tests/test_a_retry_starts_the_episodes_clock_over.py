"""REWRITTEN to the new rule (C3_verdict #4, D2, 2026-10-11): a retry stamps
an ATTEMPT; it never resets the ceiling.

The old rule (ep19, 2026-10-07: "a retry is the owner's fresh launch: the
clock starts over at it") let 67 retries each open a fresh 5 h -- all four
over_budget parks were retried into a new ceiling, so the 6 h could not be
measured.  Under D3 a spent clock no longer stops an episode (it only removes
rescue rungs), so the reason for the reset is gone.  `retry` still retires
the brain folder and writes clock_reset.json as `{"attempt_at": ...}` for the
audit and for the ladders' own round counters (A55-A57: a retry's fresh take
rounds, a keep_best signed before the retry is re-judged); `spent_before`
ignores it.  $0."""
from __future__ import annotations

import json
from pathlib import Path

from studio import run_budget


def rows(tmp: Path, ended: list[str], seconds: float = 1000.0) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "timing.jsonl").write_text("".join(
        json.dumps({"stage": "s", "started": e, "ended": e, "seconds": seconds, "ok": True}) + "\n"
        for e in ended), encoding="utf-8")
    return tmp


def test_an_attempt_stamp_never_lowers_what_was_spent(tmp_path):
    home = rows(tmp_path, ["2026-10-07T10:00:00", "2026-10-07T12:00:00", "2026-10-07T14:00:00"])
    assert run_budget.spent_before(home) == 3000.0
    run_budget.stamp_attempt(home, at="2026-10-07T13:00:00")
    assert run_budget.spent_before(home) == 3000.0


def test_a_legacy_reset_file_is_ignored_by_the_clock_too(tmp_path):
    home = rows(tmp_path, ["2026-10-07T10:00:00"])
    (home / run_budget.CLOCK_RESET).write_text(json.dumps({"at": "2026-10-08T00:00:00"}), encoding="utf-8")
    assert run_budget.spent_before(home) == 1000.0
    assert run_budget.clock_reset_at(home) == "2026-10-08T00:00:00"     # the ladders still read it


def test_the_stamp_is_an_attempt_now_by_default(tmp_path):
    stamp = run_budget.stamp_attempt(tmp_path)
    doc = json.loads((tmp_path / run_budget.CLOCK_RESET).read_text(encoding="utf-8"))
    assert doc == {"attempt_at": stamp} and len(stamp) >= 19
    assert run_budget.clock_reset_at(tmp_path) == stamp


def test_the_autopilots_retry_stamps_and_keeps_the_clock(tmp_path):
    from tests import autopilot_cli_fixtures as fx
    cli = fx.load()
    root = fx.book(tmp_path)
    home = root / "episodes" / "ep19"
    rows(home, ["2026-10-07T10:00:00"])
    (home / "brain").mkdir()
    before = run_budget.spent_before(home)
    cli.retry(root, 19)
    assert run_budget.spent_before(home) == before == 1000.0
    assert "attempt_at" in json.loads((home / run_budget.CLOCK_RESET).read_text(encoding="utf-8"))
    assert not (home / "brain").exists() and (home / "brain_retired_01").is_dir()


def test_a_take_verdict_signed_before_the_retry_is_not_done(tmp_path, monkeypatch):
    """A55-A57 untouched: the verdict was keep_best on a spent clock; the
    retry's stamp is newer, so step 09 re-enters its ladder instead of reading
    as done (and at a spent clock that ladder is terminal at once)."""
    import time
    from types import SimpleNamespace
    from scripts.episode import step_09_shoot as step
    from studio import eye_verdict
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    take = room / "T00.mp4"
    take.write_bytes(b"take")
    eye_verdict.path(room, eye_verdict.fingerprint([take])).write_text('{"verdict": "flagged"}', encoding="utf-8")
    ctx = SimpleNamespace(home=tmp_path)
    monkeypatch.setattr(step, "judged", lambda takes: True)
    monkeypatch.setattr(step, "stale_takes", lambda ctx: [])
    assert step.done(ctx) is True
    time.sleep(1.1)
    run_budget.stamp_attempt(tmp_path)
    assert step.done(ctx) is False
