"""Retro 2026-10-20 item 7 (ops #4): with no publish/standing.json, step 13 stops
every finished master at G-STANDING by design (memory: no upload unless asked).
The autopilot recorded that hold as a failure: ep01 PARKED at 10-19 21:33 PDT and
again at 10-20 04:51Z ("escalated: G-STANDING"), and each needed retry + resume.
In a series two holds in a row would trip the two-parks brake.

Now the hold is the state HELD_PUBLISH: no parked row, one message naming the
file to sign, the series moves to the next chapter, and the held episode runs
step 13 again once the owner signs.  The tail below is a copy of the last lines
of ep01's drive_launch18.log."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from studio import autopilot as ap
from studio.autopilot import State
from tests import autopilot_cli_fixtures as fx
from tests.test_autopilot_derives_state_from_disk import rows, signals

TAIL = (Path(__file__).parent / "fixtures" / "autopilot_ops" / "ep01_drive_launch18_tail.log").read_text(encoding="utf-8")
ENDED = rows(("start",), ("run", "escalated"), ("end", 1))


def test_the_ep01_tail_classifies_as_a_hold_not_a_park():
    assert ap.classify(TAIL, set()) == ("held", "held_publish", None)


def test_another_owner_gate_still_parks():
    kind, reason, _ = ap.classify("OWNER G-LOOK | book episode/ep02 | look | sign: x\n", set())
    assert (kind, reason) == ("park", "escalated: G-LOOK")


def test_derive_names_held_publish_and_the_file_to_sign():
    got = ap.derive(signals(drive_rows=ENDED, log_tail=TAIL), 1)
    assert got.state is State.HELD_PUBLISH and "publish/standing.json" in got.reason


def test_a_signed_standing_file_relaunches_the_held_episode():
    got = ap.derive(replace(signals(drive_rows=ENDED, log_tail=TAIL), standing=True), 1)
    assert got.state is State.IDLE and got.reason == "standing_signed"


def _held_deps(tmp_path, held=(1,)):
    d = fx.deps(tmp_path)
    d.derive = lambda s, n: fx.derived("HELD_PUBLISH" if n in held else "IDLE", "held_publish: sign publish/standing.json")
    return d


def test_a_hold_writes_no_parked_row_and_tells_once(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = _held_deps(tmp_path)
    doc = cli.tick(book, fx.CODEX, d, 1)
    assert doc["episode"]["state"] == "HELD_PUBLISH"
    assert not (book / "autopilot" / "parked.jsonl").exists()
    assert len(d.calls["notify"]) == 1 and "publish/standing.json" in d.calls["notify"][0]
    cli.tick(book, fx.CODEX, d, 2)
    assert len(d.calls["notify"]) == 1


def test_the_series_moves_past_a_held_episode(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = _held_deps(tmp_path)
    cli.tick(book, fx.CODEX, d, 1)
    assert cli.tick(book, fx.CODEX, d, 2)["episode"]["n"] == 2


def test_two_holds_in_a_row_never_pause_the_series(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = _held_deps(tmp_path, held=(1, 2, 3))
    for i in range(4):
        doc = cli.tick(book, fx.CODEX, d, i)
    assert doc["series"]["paused"] is False and doc["episode"]["state"] == "HELD_PUBLISH"
    assert doc["episode"]["n"] == 1, "all held: the series sits on the lowest hold, never COMPLETE"


def test_a_retry_lifts_the_hold(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = _held_deps(tmp_path)
    cli.tick(book, fx.CODEX, d, 1)
    cli.retry(book, 1)
    assert cli.held_units(book) == []


def test_a_signed_standing_file_brings_the_held_episode_back(tmp_path):
    cli, book = fx.load(), fx.book(tmp_path)
    d = _held_deps(tmp_path)
    cli.tick(book, fx.CODEX, d, 1)
    signed = {"kind": "publish", "decision": "2026-10-01-no-human-input-at-publish", "by": "owner", "at": "2026-10-20"}
    (book / "publish").mkdir(parents=True)
    (book / "publish" / "standing.json").write_text(json.dumps(signed), encoding="utf-8")
    assert cli.tick(book, fx.CODEX, d, 2)["episode"]["n"] == 1
