"""A kept-best take that shipped over failed gates carries its settled state (flagged, the fault
rows), never a default pass.  Replayed on ep01 T07/T10/T16/T20/T21/T24 (C5, P07 known gap)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.calibration import harvest_labels as hl  # noqa: E402
from scripts.episode import warp_labels as wl  # noqa: E402
from studio import casebook  # noqa: E402

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "P09"
SHIPPED = ("T07", "T10", "T16", "T20", "T21", "T24")


def kept(take):
    dq = json.loads((FIX / f"{take}.dq.json").read_text(encoding="utf-8"))
    return hl.take_rows("c", "ep01", dq, {}, "src", "v1")[0]


def test_each_shipped_flagged_take_is_a_fault_row_not_a_pass():
    for take in SHIPPED:
        row = kept(take)
        assert row.verdict == "fault" and row.machine["flagged"] is True, take
        assert row.machine["label_source"] == "shipped-flagged" and "warp" in row.machine["faults"]


def test_the_warp_gate_names_blur_warp_and_the_hard_fault_comes_first():
    assert kept("T07").fault_class == "blur_warp"
    assert kept("T10").fault_class == "blur_warp"       # warp is hard, frozen-whole advisory


def test_a_take_whose_gates_passed_stays_a_shipped_default_pass():
    row = kept("T08")
    assert row.verdict == "pass" and row.machine["label_source"] == "shipped-default"


def test_a_shipped_flagged_row_is_nobodys_label_and_no_metric_counts_it(tmp_path):
    row = kept("T07")
    assert not casebook.counted(row) and casebook.is_shipped(row)
    assert wl.labels([row.model_dump()]) == {}
    casebook.write_rows(tmp_path / casebook.LABELS, [row, kept("T08")])
    assert [r.path[-7:-4] for r in casebook.load(tmp_path)] == ["T08"]
