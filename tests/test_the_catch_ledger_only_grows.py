"""The ratchet's memory may only grow (fleet H ruling A10, A11).

- bench.py appends every owner catch to docs/calibration/bench/caught.jsonl
  and never rewrites a line, so a rebuilt baseline cannot quietly forget one;
- the fixer's ratchet refuses any commit that touches the bench folder, except
  lines ADDED to the ledger: a shortened ledger is refused;
- bench.py --exhibits copies every measured owner row (one with its machine
  snapshot) into tests/fixtures/casebook/<codex>/owner.jsonl, so the ratchet
  still runs on a clone with no library.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.calibration import bench  # noqa: E402
from studio import casebook, judge_bench as jb, ratchet  # noqa: E402
from studio.casebook import Row  # noqa: E402

LEDGER = "docs/calibration/bench/caught.jsonl"
CATCH = {"codex": "c", "sha8": "aaaa0004", "path": "episodes/ep01/takes/r2v/T04.mp4"}


def diff(path: str, *lines: str) -> str:
    return f"--- a/{path}\n+++ b/{path}\n" + "".join(f"{line}\n" for line in lines)


def test_a_shortened_ledger_is_refused_and_a_grown_one_is_not():
    cut = diff(LEDGER, '-{"judge": "take_verdict", "path": "T04.mp4"}')
    grown = diff(LEDGER, '+{"judge": "take_verdict", "path": "T05.mp4"}')
    assert ratchet.ledger_cut(cut) == ['-{"judge": "take_verdict", "path": "T04.mp4"}']
    assert ratchet.ledger_cut(grown) == [] and ratchet.ledger_cut(diff("studio/x.py", "-a = 1")) == []
    refusals = ratchet.check([LEDGER], cut, lambda ref, files: 0, "old", "new", {}, {}, set())
    assert any("ledger" in r for r in refusals)


def test_the_bench_folder_is_denied_but_the_ledger_may_be_appended():
    assert ratchet.outside_allow_set(["docs/calibration/bench/take_zoom.json"]) == ["docs/calibration/bench/take_zoom.json"]
    assert ratchet.outside_allow_set([LEDGER]) == []


def test_the_ledger_appends_new_catches_and_never_rewrites(tmp_path):
    ledger = tmp_path / "caught.jsonl"
    assert bench.append_ledger(ledger, "take_verdict", [CATCH]) == 1
    first = ledger.read_text(encoding="utf-8")
    assert bench.append_ledger(ledger, "take_verdict", [CATCH, CATCH | {"path": "T05.mp4"}]) == 1
    assert bench.append_ledger(ledger, "face_end", [CATCH]) == 1
    text = ledger.read_text(encoding="utf-8")
    assert text.startswith(first) and len(text.splitlines()) == 3
    assert json.loads(text.splitlines()[0]) == {"judge": "take_verdict"} | CATCH


def test_measured_owner_rows_become_clean_clone_exhibits(tmp_path):
    folder = tmp_path / "library" / "book" / "casebook"
    snap = {"take_dq": {"gates": [{"name": "frozen-at-start", "ok": False, "hard": True}]}}
    for path, machine in (("a.mp4", snap), ("b.mp4", {})):
        casebook.append_owner(folder, Row(codex="20260901000001", unit="ep01", kind="take", path=path,
                                          verdict="fault", fault_class="frozen_start", verdict_by="owner",
                                          machine=machine))
    written = bench.export_exhibits([folder], tmp_path / "exhibits")
    assert written == [tmp_path / "exhibits" / "20260901000001" / casebook.OWNER]
    rows = casebook.read_rows(written[0])
    assert [r.path for r in rows] == ["a.mp4"] and jb.is_casebook(written[0].parent)
    assert bench.export_exhibits([folder], tmp_path / "exhibits") == written
    assert len(casebook.read_rows(written[0])) == 1
