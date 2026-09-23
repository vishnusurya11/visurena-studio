"""The DQ gate on the one irreversible step could not fire.

`youtube_upload.failed_takes` globbed `home/"shots_r2v"/T*.dq.json`.  That room
was retired in the layout change; the reports are in `takes/r2v/`.  So the glob
returned nothing, `dq_failed` was ALWAYS empty, `yp.refusals` never emitted its
DQ refusal, and `yp.waived` wrote `dq_failed: []` into the override ledger --
the audit trail repeating the same false thing.

Episode 4 went out under this.  Its 24 takes did all pass, so nothing false was
published; the gate simply had no part in knowing that.

The guard that should have caught it globbed only `scripts/episode/*.py` and
`studio/*.py`, and this lives in `scripts/publish/`.  It now walks every script
under both trees, and also sees a room hidden in a conditional expression --
`home / ("shots_r2v" if engine == "r2v" else "shots")` -- which is the shape
that hid this one.
"""
import json
from pathlib import Path

from scripts.publish.youtube_upload import failed_takes


def episode(tmp_path: Path, **verdicts) -> Path:
    room = tmp_path / "takes" / "r2v"
    room.mkdir(parents=True)
    # A REAL TAKES ROOM: the render records its takes in shots.json, and
    # failed_takes now reads that as the universe (audit 2026-09-22, item 6).
    (room / "shots.json").write_text(json.dumps([{"index": int(n[1:])} for n in verdicts]),
                                     encoding="utf-8")
    for name, passed in verdicts.items():
        (room / f"{name}.mp4").write_bytes(b"mp4")
        (room / f"{name}.dq.json").write_text(json.dumps({"passed": passed}), encoding="utf-8")
    return tmp_path


def test_a_failed_take_is_found(tmp_path):
    assert failed_takes(episode(tmp_path, T00=True, T07=False)) == ["T07"]


def test_an_episode_where_every_take_passed_is_clean(tmp_path):
    assert failed_takes(episode(tmp_path, T00=True, T01=True)) == []


def test_several_failures_come_back_in_order(tmp_path):
    assert failed_takes(episode(tmp_path, T00=False, T12=False, T05=True)) == ["T00", "T12"]


def test_it_does_not_look_in_the_retired_room(tmp_path):
    """A stale report left in the old place must not decide a publish."""
    home = episode(tmp_path, T00=True)
    old = tmp_path / "shots_r2v"
    old.mkdir()
    (old / "T99.dq.json").write_text(json.dumps({"passed": False}), encoding="utf-8")
    assert failed_takes(home) == []


def test_a_missing_takes_room_is_not_silently_clean(tmp_path):
    """The exact failure: no room, no reports, and `[]` read as "nothing failed".
    An episode with no takes at all has not passed its DQ -- it has not had one."""
    with_nothing = tmp_path / "empty"
    with_nothing.mkdir()
    # It used to return [] here and leave the caller to know better, which is
    # the flaw this file is about. Now the refusal is inside: no record of which
    # takes exist is itself a reason not to publish.
    assert failed_takes(with_nothing) != []
    assert not (with_nothing / "takes" / "r2v").exists()
