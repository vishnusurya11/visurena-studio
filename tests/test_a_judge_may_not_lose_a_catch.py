"""The ratchet: a judge with shipped constants must still catch every owner
row it caught in its committed baseline.

Over the library's casebooks (globbed; a book with only an owner.jsonl counts)
and the committed exhibits under tests/fixtures/casebook/ (owner rows with
their machine snapshot, so the ratchet runs on a clean clone), every
registered judge is run on the rows of its kind and compared with
`docs/calibration/bench/<judge>.json` and the append-only catch ledger
`docs/calibration/bench/caught.jsonl`.  A wall may move only with a new
baseline in the same commit -- so a loosened wall that drops an owner catch
fails the suite here.

Fleet H ruling A9-A12:
- a vacuity alarm: a baseline benched on no owner rows fails once the judge
  measures owner rows, so an empty baseline cannot pass forever;
- the ledger's catches are kept even when a baseline is rewritten;
- the other side: a new refusal of an owner PASS row, and a class whose owner
  recall fell while the pooled number rose, are named -- report-only until
  the class has the convention's 30 owner rows, then they fail.
"""
import json
from pathlib import Path

import pytest

from studio import judge_bench as jb
from studio.casebook import Row
from studio.judges import registry

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures" / "judge_bench"
EXHIBITS = Path(__file__).parent / "fixtures" / "casebook"
BENCH = ROOT / "docs" / "calibration" / "bench"


def casebooks() -> list[Path]:
    library = ROOT / "library"
    found = sorted(p for p in library.glob("*/casebook") if jb.is_casebook(p)) if library.exists() else []
    return jb.with_exhibits(found, EXHIBITS)


def test_a_judge_that_forgets_a_catch_is_named_by_path():
    baseline = json.loads((FIXTURES / "baseline.json").read_text(encoding="utf-8"))
    forgetful = jb.run(jb.load_rows(FIXTURES, "take"), lambda r: {"refused": False, "classes": [], "values": {}})
    assert jb.lost_catches(baseline, forgetful) == ["episodes/ep01/takes/r2v/T04.mp4",
                                                     "episodes/ep01/takes/r2v/T05.mp4"]
    strict = jb.run(jb.load_rows(FIXTURES, "take"), lambda r: {"refused": True, "classes": [], "values": {}})
    assert jb.lost_catches(baseline, strict) == []


def test_every_registered_judge_has_a_kind_and_classes_from_the_closed_list():
    from studio import casebook
    for name in registry.names():
        entry = registry.get(name)
        assert entry.kind in casebook.KINDS
        assert entry.classes and all(c in casebook.CLASSES for c in entry.classes)
        assert len(entry.version) == 8


# ---- A9: the vacuity alarm ------------------------------------------------------------

EMPTY = {"recall_owner": {"point": 0.0, "low": 0.0, "high": 1.0, "n": 0, "k": 0}, "caught": []}


def test_an_empty_baseline_against_an_owner_catch_fails():
    outcomes = jb.run(jb.load_rows(FIXTURES, "take"), lambda r: {"refused": True, "classes": [], "values": {}})
    assert "rebuild" in jb.vacuous(EMPTY, outcomes)
    assert jb.vacuous(EMPTY, []) == ""
    full = json.loads((FIXTURES / "baseline.json").read_text(encoding="utf-8"))
    assert jb.vacuous(full, outcomes) == ""


# ---- A10: the catch ledger -------------------------------------------------------------

def test_a_ledger_catch_is_kept_when_the_baseline_forgets_it():
    ledger = [{"judge": "fixture", "codex": "00000000000000", "sha8": "aaaa0004",
               "path": "episodes/ep01/takes/r2v/T04.mp4"}]
    merged = jb.with_ledger(EMPTY, ledger, "fixture")
    forgetful = jb.run(jb.load_rows(FIXTURES, "take"), lambda r: {"refused": False, "classes": [], "values": {}})
    assert jb.lost_catches(merged, forgetful) == ["episodes/ep01/takes/r2v/T04.mp4"]
    assert jb.with_ledger(EMPTY, ledger, "other")["caught"] == []


# ---- A12: the other side, report-only below 30 -----------------------------------------

def owner(path, verdict="pass", cls=None):
    return Row(codex="c", unit="ep01", kind="take", path=path, verdict=verdict, fault_class=cls, verdict_by="owner")


def test_a_loosened_judge_that_refuses_an_owner_pass_is_named():
    rows = [owner("a.mp4"), owner("b.mp4")]
    before = jb.baseline(jb.run(rows, lambda r: {"refused": False, "classes": [], "values": {}}), "f", "v")
    after = jb.run(rows, lambda r: {"refused": r.path == "b.mp4", "classes": [], "values": {}})
    assert jb.new_refusals(before, after) == ["b.mp4"]
    assert jb.new_refusals(jb.baseline(after, "f", "v"), after) == []


def test_a_class_that_falls_while_the_pool_rises_is_named():
    rows = [owner(f"s{i}.mp4", "fault", "over_push") for i in range(4)] + [owner("f.mp4", "fault", "face_out")]
    before = jb.baseline(jb.run(rows, lambda r: {"refused": r.path in ("s0.mp4", "f.mp4"), "classes": [], "values": {}}), "f", "v")
    after = jb.run(rows, lambda r: {"refused": r.fault_class == "over_push", "classes": [], "values": {}})
    assert jb.recall(after, "owner").point > before["recall_owner"]["point"]
    assert jb.class_drops(before, after) == ["face_out: 1/1 -> 0/1"]


def test_the_other_side_fails_only_on_a_class_with_thirty_owner_rows():
    assert jb.armed({"face_out": {"n": 29}}) == [] and jb.armed({"face_out": {"n": 30}}) == ["face_out"]


# ---- the library and the exhibits -------------------------------------------------------

def ledger_rows() -> list[dict]:
    path = BENCH / "caught.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    return [json.loads(line) for line in lines if line.strip()]


def outcomes_for(name: str) -> list[jb.Outcome]:
    entry = registry.get(name)
    rows = [r for folder in casebooks() for r in jb.load_rows(folder, entry.kind)]
    return jb.run(rows, entry.judge, entry.classes)


@pytest.mark.skipif(not casebooks(), reason="no library casebook and no committed exhibit on this machine")
@pytest.mark.parametrize("name", registry.names())
def test_a_judge_may_not_lose_a_catch(name):
    target = BENCH / f"{name}.json"
    if not target.is_file():
        pytest.skip(f"{name} has no committed baseline yet: run scripts/calibration/bench.py {name}")
    baseline = jb.with_ledger(json.loads(target.read_text(encoding="utf-8")), ledger_rows(), name)
    outcomes = outcomes_for(name)
    assert jb.lost_catches(baseline, outcomes) == []
    assert jb.recall(outcomes, by="owner").point >= baseline["recall_owner"]["point"]
    assert jb.vacuous(baseline, outcomes) == ""


@pytest.mark.skipif(not casebooks(), reason="no library casebook and no committed exhibit on this machine")
@pytest.mark.parametrize("name", registry.names())
def test_a_judge_may_not_refuse_an_armed_owner_pass(name, capsys):
    target = BENCH / f"{name}.json"
    if not target.is_file():
        pytest.skip(f"{name} has no committed baseline yet")
    baseline, outcomes = json.loads(target.read_text(encoding="utf-8")), outcomes_for(name)
    report = jb.other_side(baseline, outcomes)
    print(f"{name} other side (report-only below {jb.ARMABLE_N} owner rows per class): {report}")
    assert report["failing"] == []
