"""Retro 2026-10-20 item 7 / V7 (ops #5, #8): the retro pause set at 23:10 PDT on
10-18 (events.jsonl 2026-10-19T06:10:15Z `pause`) had no end condition, and nothing
looked at it again until the next work at 11:19.  A pause is now a lease
{by, why, since, expires, sha}: a retro pause expires at 2 h and says so once; an
owner pause never expires unless he gives hours, and is never resumed by code;
the autopilot resumes only a pause it set itself (the two-parks brake), and only
once its lease ran out AND a commit landed since."""
from __future__ import annotations

import json

from studio import autopilot as ap
from tests import autopilot_cli_fixtures as fx

T0 = 1_000_000.0
HOUR = 3600.0
LEGACY = {"book": fx.CODEX, "first": 1, "last": 3, "paused": True,
          "last_why": "2026-10-14 HEL ep01 remake: stop after ep01, ep02 must not start"}
"""The shape of the Jekyll series.json today: a pause from before leases."""


def _series(book) -> dict:
    return json.loads((book / "autopilot" / "series.json").read_text(encoding="utf-8"))


def _events(cli, book, name) -> list[dict]:
    return [r for r in cli.rows_of(book / "autopilot" / "events.jsonl") if r["event"] == name]


def test_a_retro_lease_expires_at_two_hours_and_an_owner_lease_never():
    retro = ap.lease("retro", "deadline retro", T0, sha="abc")
    assert retro["by"] == "retro" and retro["expires"] == T0 + 2 * HOUR and retro["why"] == "deadline retro"
    assert ap.lease("owner", "", T0)["expires"] is None
    assert ap.lease("owner", "", T0, hours=3)["expires"] == T0 + 3 * HOUR


def test_expiry_is_read_against_now():
    retro = ap.lease("retro", "x", T0)
    assert not ap.lease_expired(retro, T0 + HOUR) and ap.lease_expired(retro, T0 + 2 * HOUR)
    assert not ap.lease_expired(ap.lease("owner", "x", T0), T0 + 1000 * HOUR)
    assert not ap.lease_expired(None, T0 + 1000 * HOUR), "a pause from before leases never expires"


def test_only_an_autopilot_pause_resumes_and_only_after_a_commit_landed():
    late = T0 + 3 * HOUR
    assert ap.may_resume(ap.lease("autopilot", "brake", T0, sha="aaa"), late, "bbb")
    assert not ap.may_resume(ap.lease("autopilot", "brake", T0, sha="aaa"), late, "aaa"), "no fix landed"
    assert not ap.may_resume(ap.lease("autopilot", "brake", T0, sha="aaa"), T0 + HOUR, "bbb"), "lease still held"
    assert not ap.may_resume(ap.lease("owner", "x", T0, hours=1, sha="aaa"), late, "bbb")
    assert not ap.may_resume(ap.lease("retro", "x", T0, sha="aaa"), late, "bbb")
    assert not ap.may_resume(None, late, "bbb")


def test_pause_writes_the_lease_and_resume_clears_it(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    cli.set_paused(book, fx.CODEX, True, by="retro", why="deadline retro", now=T0, sha="abc")
    doc = _series(book)
    assert doc["paused"] is True and doc["pause"]["by"] == "retro" and doc["pause"]["expires"] == T0 + 2 * HOUR
    assert doc["paused_why"] == "deadline retro", "the board reads paused_why"
    cli.set_paused(book, fx.CODEX, False)
    assert "pause" not in _series(book) and _series(book)["paused"] is False


def test_an_expired_retro_lease_says_so_once_and_stays_paused(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    cli.set_paused(book, fx.CODEX, True, by="retro", why="deadline retro", now=T0, sha="abc123def")
    d = fx.deps(tmp_path, "IDLE", now=lambda: T0 + 2 * HOUR + 60)
    cli.tick(book, fx.CODEX, d, 1)
    cli.tick(book, fx.CODEX, d, 2)
    assert len(_events(cli, book, "pause_expired")) == 1
    assert len(d.calls["notify"]) == 1 and "retro" in d.calls["notify"][0] and "resume" in d.calls["notify"][0]
    assert _series(book)["paused"] is True and not d.calls["popen"]


def test_an_owner_pause_is_never_resumed_by_the_autopilot(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    cli.set_paused(book, fx.CODEX, True, by="owner", why="hold", hours=1, now=T0, sha="aaa")
    d = fx.deps(tmp_path, "IDLE", now=lambda: T0 + 5 * HOUR)        # HEAD is abc123def: code moved
    cli.tick(book, fx.CODEX, d, 1)
    assert _series(book)["paused"] is True and not d.calls["popen"] and not _events(cli, book, "resume")


def test_the_brake_pause_resumes_after_its_lease_once_a_fix_landed(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    cli.set_paused(book, fx.CODEX, True, by="autopilot", why="two parked in a row", now=T0, sha="0ld5ha")
    d = fx.deps(tmp_path, "IDLE", now=lambda: T0 + 3 * HOUR)
    cli.tick(book, fx.CODEX, d, 1)
    assert _series(book)["paused"] is False and _events(cli, book, "resume")[-1]["by"] == "autopilot"
    assert d.calls["popen"], "the same tick launches on the resumed series"


def test_a_pause_from_before_leases_is_left_alone(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    (book / "autopilot").mkdir(parents=True, exist_ok=True)
    (book / "autopilot" / "series.json").write_text(json.dumps(LEGACY), encoding="utf-8")
    d = fx.deps(tmp_path, "IDLE", now=lambda: T0 + 1000 * HOUR)
    cli.tick(book, fx.CODEX, d, 1)
    assert _series(book)["paused"] is True and not d.calls["notify"] and not d.calls["popen"]


def test_the_two_parks_brake_takes_an_autopilot_lease(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = fx.deps(tmp_path)
    assert cli.brake_two_parks(book, [{"episode": 1}, {"episode": 2}], d)
    lease = _series(book)["pause"]
    assert lease["by"] == "autopilot" and lease["expires"] == 1_000_000.0 + 2 * HOUR and lease["sha"] == "abc123def"


def test_the_cli_pause_takes_by_why_and_hours():
    args = fx.load().parser().parse_args(["pause", "--by", "retro", "--why", "retro build", "--hours", "1.5"])
    assert (args.by, args.why, args.hours) == ("retro", "retro build", 1.5)
    assert fx.load().parser().parse_args(["pause"]).by == "owner"
