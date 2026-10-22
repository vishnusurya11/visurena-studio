"""An owner row carries the machine values of the file he judged (fleet H ruling A6, A8).

`owner_row()` left `machine={}`, and every registered judge reads `row.machine`,
so every owner row came back "not measured" and the bench counted none of
them.  Now:

- note_owner snapshots the artefact's machine json (the take's dq record and
  content read, the panel's dq and content rows) through the harvest's own
  readers, minus the harvest's shipped-flagged stamp: the owner's word is the
  label, not the gate's state.
- a dq record whose `take_sha8` is of other bytes is stale, and a file with
  no json is no snapshot: the row goes on the casebook's needs-rejudge list.
- an older owner row with no machine borrows the harvested row's machine on
  the same artefact, but only when the sha8s match.
- the Row carries the label session's sampling fields; an old row still parses.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.audit import note  # noqa: E402
from scripts.calibration import harvest_labels as hl  # noqa: E402
from studio import casebook, episode_home, judge_bench as jb  # noqa: E402
from studio.judges import registry  # noqa: E402

CODEX = "20260901000001"
GATES = [{"name": "frozen-at-start", "value": 2.0, "ok": False, "hard": True, "note": "2.0s", "penalty": 0.0},
         {"name": "warp", "value": 0.4, "ok": False, "hard": True, "note": "warp", "penalty": 0.0}]


@pytest.fixture()
def book(tmp_path, monkeypatch):
    home = tmp_path / "book"
    room = home / "episodes" / "ep01" / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "T03.mp4").write_bytes(b"take three")
    (room / "T04.mp4").write_bytes(b"take four")
    sha = casebook.sha8_of(room / "T03.mp4")
    (room / "T03.dq.json").write_text(json.dumps({"take": 3, "file": "T03.mp4", "passed": False, "score": 40.0,
                                                  "take_sha8": sha, "gates": GATES}), encoding="utf-8")
    (room / "T04.dq.json").write_text(json.dumps({"take": 4, "file": "T04.mp4", "passed": True, "score": 90.0,
                                                  "take_sha8": "00000000", "gates": []}), encoding="utf-8")
    monkeypatch.setattr(episode_home, "book_dir", lambda _id: home)
    return home


def owner_rows(book):
    return casebook.read_rows(book / "casebook" / casebook.OWNER)


def test_a_noted_take_is_measured_by_the_take_verdict(book):
    note.main(["note.py", CODEX, "ep01", "episodes/ep01/takes/r2v/T03.mp4", "frozen_start", "it never moved"])
    row = owner_rows(book)[0]
    assert row.machine["take_dq"]["gates"][0]["name"] == "frozen-at-start"
    assert "label_source" not in row.machine and casebook.counted(row)
    said = registry.get("take_verdict").judge(row)
    assert said["refused"] is True and said["values"].get("note") != "not measured"
    outcomes = jb.run([row], registry.get("take_verdict").judge)
    assert jb.recall(outcomes, "owner").n == 1


def test_a_stale_or_missing_record_goes_on_the_needs_rejudge_list(book):
    note.main(["note.py", CODEX, "ep01", "episodes/ep01/takes/r2v/T04.mp4", "pass", "fine"])
    note.main(["note.py", CODEX, "ep01", "episodes/ep01/takes/r2v/T09.mp4", "pass", "fine"])
    assert [r.machine for r in owner_rows(book)] == [{}, {}]
    waiting = (book / "casebook" / casebook.NEEDS_REJUDGE).read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["path"] for line in waiting] == ["episodes/ep01/takes/r2v/T04.mp4",
                                                              "episodes/ep01/takes/r2v/T09.mp4"]


def test_the_snapshot_reads_through_the_harvests_own_rows(book):
    machine = hl.machine_for(CODEX, book, "episodes/ep01/takes/r2v/T03.mp4")
    assert set(machine) == {"take_dq", "content"}
    assert hl.machine_for(CODEX, book, "episodes/ep01/takes/r2v/T04.mp4") is None


def harvested(path, sha8, machine):
    return casebook.Row(codex="c", unit="ep01", kind="take", path=path, sha8=sha8, verdict="pass",
                        verdict_by="default", machine=machine)


def test_an_old_owner_row_borrows_the_harvested_machine_of_the_same_bytes(tmp_path):
    take_dq = {"take_dq": {"gates": GATES}}
    casebook.write_rows(tmp_path / casebook.LABELS, [harvested("a.mp4", "11111111", take_dq),
                                                     harvested("b.mp4", "22222222", take_dq)])
    old = [casebook.Row(codex="c", unit="ep01", kind="take", path=p, sha8=s, verdict="fault",
                        fault_class="frozen_start", verdict_by="owner") for p, s in (("a.mp4", "11111111"),
                                                                                     ("b.mp4", "99999999"))]
    for row in old:
        casebook.append_owner(tmp_path, row)
    loaded = {r.path: r for r in casebook.load(tmp_path) if r.verdict_by == "owner"}
    assert loaded["a.mp4"].machine == take_dq and loaded["b.mp4"].machine == {}


def test_the_row_carries_the_sampling_fields_and_old_rows_still_parse():
    old = casebook.Row.model_validate({"codex": "c", "unit": "ep01", "kind": "take", "path": "a.mp4",
                                       "verdict": "pass", "verdict_by": "owner"})
    assert old.p_select is None and old.stratum == "" and old.seen_by_owner is False
    new = old.model_copy(update={"stratum": "P", "p_select": 0.25, "seen_by_owner": True, "session_id": "s1",
                                 "rubric_version": "r1", "repeat_of": "x", "latency_ms": 4200})
    assert casebook.Row.model_validate(json.loads(json.dumps(new.model_dump()))) == new
    with pytest.raises(ValueError):
        casebook.Row.model_validate(new.model_dump() | {"p_select": 0.0})
