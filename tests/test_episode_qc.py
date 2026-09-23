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
    """INCLUDING THE EDIT GATE HAVING RUN.  An absent or unmeasured edit block
    used to pass -- `.get("edit", {}).get("ok", True)` -- while G5.6 provenance
    returned `measured: False` on every episode ever cut, because nothing wrote
    the manifest it needs."""
    good = {"title_card": True, "lufs_ok": True, "tp_ok": True, "missing_cuts": [], "lines": [{"passed": True}],
            "edit": {"ok": True, "measured": True}}
    assert qc.verdict(good)
    assert not qc.verdict({**good, "lines": [{"passed": False}]})
    assert not qc.verdict({**good, "missing_cuts": [5.0]})
    assert not qc.verdict({**good, "edit": {"ok": True, "measured": False}})
    assert not qc.verdict({k: v for k, v in good.items() if k != "edit"})


def test_the_longest_gap_is_measured_from_the_placed_windows():
    lines = [{"at": 0.0, "seconds": 3.0}, {"at": 3.5, "seconds": 2.0}, {"at": 12.0, "seconds": 1.0}]
    assert qc.longest_gap(lines, 20.0) == 7.0


def test_a_soft_cut_inside_a_take_run_does_not_fail_the_verdict():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("ep_qc", Path(__file__).resolve().parents[1] / "scripts" / "episode" / "qc.py")
    qc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qc)
    placed = {"shots": [{"index": 0, "t_start": 0.0}, {"index": 1, "t_start": 4.0}, {"index": 2, "t_start": 9.0}]}
    assert qc.internal_cuts(placed, [{"index": 0, "shots": [0, 1]}, {"index": 2, "shots": [2]}]) == [4.0]
    report = {"title_card": True, "lufs_ok": True, "tp_ok": True, "missing_cuts": [4.0], "internal_cuts": [4.0],
              "lines": [], "edit": {"ok": True, "measured": True}}
    assert qc.verdict(report) is True
    report["missing_cuts"] = [4.0, 9.0]
    assert qc.verdict(report) is False
