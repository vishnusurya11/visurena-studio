"""The episode gate compares the file to the plan, with a tolerance it states."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_qc", ROOT / "scripts" / "episode" / "qc.py")
qc = importlib.util.module_from_spec(spec)
sys.modules["ep_qc"] = qc
spec.loader.exec_module(qc)


def test_a_cut_within_tolerance_is_found():
    assert qc.missing_cuts([5.0, 9.0], [5.08, 9.2]) == [9.0]


def test_the_verdict_needs_every_gate():
    good = {"lufs_ok": True, "tp_ok": True, "missing_cuts": [], "lines": [{"passed": True}]}
    assert qc.verdict(good)
    assert not qc.verdict({**good, "lines": [{"passed": False}]})
    assert not qc.verdict({**good, "missing_cuts": [5.0]})


def test_the_longest_gap_is_measured_from_the_placed_windows():
    lines = [{"at": 0.0, "seconds": 3.0}, {"at": 3.5, "seconds": 2.0}, {"at": 12.0, "seconds": 1.0}]
    assert qc.longest_gap(lines, 20.0) == 7.0
