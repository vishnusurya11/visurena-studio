"""The ratchet: a judge with shipped constants must still catch every owner
row it caught in its committed baseline.

Over the library's casebooks (globbed; skipped on a machine without one),
every registered judge is run on the rows of its kind and compared with
`docs/calibration/bench/<judge>.json`.  A wall may move only with a new
baseline in the same commit -- so a loosened wall that drops an owner catch
fails the suite here.  The unit half runs on fixtures alone.
"""
import json
from pathlib import Path

import pytest

from studio import judge_bench as jb
from studio.judges import registry

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures" / "judge_bench"
BENCH = ROOT / "docs" / "calibration" / "bench"


def casebooks() -> list[Path]:
    library = ROOT / "library"
    return sorted(p for p in library.glob("*/casebook") if (p / "labels.jsonl").is_file()) if library.exists() else []


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


@pytest.mark.skipif(not casebooks(), reason="no library with a harvested casebook on this machine")
@pytest.mark.parametrize("name", registry.names())
def test_a_judge_may_not_lose_a_catch(name):
    target = BENCH / f"{name}.json"
    if not target.is_file():
        pytest.skip(f"{name} has no committed baseline yet: run scripts/calibration/bench.py {name}")
    baseline = json.loads(target.read_text(encoding="utf-8"))
    entry = registry.get(name)
    rows = [r for folder in casebooks() for r in jb.load_rows(folder, entry.kind)]
    outcomes = jb.run(rows, entry.judge, entry.classes)
    assert jb.lost_catches(baseline, outcomes) == []
    assert jb.recall(outcomes, by="owner").point >= baseline["recall_owner"]["point"]
