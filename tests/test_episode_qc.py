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
            "edit": {"ok": True, "measured": True}, "seconds": 160.0}
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
              "lines": [], "edit": {"ok": True, "measured": True}, "seconds": 160.0}
    assert qc.verdict(report) is True
    report["missing_cuts"] = [4.0, 9.0]
    assert qc.verdict(report) is False


# -- the report names the upscale and the encoder; a fallback is an advisory --------------------

def test_a_fallback_master_is_named_in_the_qc_report(tmp_path):
    import json
    (tmp_path / "upscale_used.json").write_text(json.dumps(
        {"asked": "av3", "used": "lanczos", "encoder": "cpu", "fallback": True}), encoding="utf-8")
    block = qc.upscale_block(tmp_path)
    assert block["used"] == "lanczos" and block["advisory"] == "upscale: asked av3, ran lanczos"


def test_a_master_that_ran_as_asked_has_no_advisory(tmp_path):
    import json
    (tmp_path / "upscale_used.json").write_text(json.dumps(
        {"asked": "av3", "used": "av3", "encoder": "cuda", "fallback": False}), encoding="utf-8")
    assert qc.upscale_block(tmp_path)["advisory"] == "" and qc.upscale_block(tmp_path)["encoder"] == "cuda"


def test_a_missing_record_says_it_was_not_recorded(tmp_path):
    assert qc.upscale_block(tmp_path) == {"asked": "", "used": "", "encoder": "", "fallback": False,
                                          "advisory": "", "recorded": False}


def test_qc_sets_torch_to_six_threads(monkeypatch):
    seen = []
    import types
    monkeypatch.setitem(sys.modules, "torch", types.SimpleNamespace(set_num_threads=seen.append))
    qc.limit_threads()
    assert seen == [6]


def test_qc_does_not_wait_for_comfyui(tmp_path):
    """qc.py measures on the CPU (the router claims the card when it is idle), so the step
    never parks on a busy ComfyUI queue before it."""
    import types
    import pytest
    from scripts.episode import step_11_qc
    seen = []
    ctx = types.SimpleNamespace(home=tmp_path, log=lambda *a, **k: None, budget=None,
                                run_script=lambda script, *a, **k: seen.append((script, k)) or 0)
    with pytest.raises(SystemExit):
        step_11_qc.qc_report(ctx, [])           # no report is left by the fake run: it refuses, after the call
    assert seen and seen[0][0].endswith("qc.py") and seen[0][1]["gpu"] is False
