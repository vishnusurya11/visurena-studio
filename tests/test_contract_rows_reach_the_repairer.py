"""The HARD_LISTS 'CONTRACT :' entry never matched plan_check's printed
'CONTRACT:' (no space before the colon), so NO contract refusal ever reached
plan_repair -- the bed-span cure included.  Regression for the one-character
fix."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("pr_contract", ROOT / "scripts" / "episode" / "plan_repair.py")
pr = importlib.util.module_from_spec(_spec)
sys.modules["pr_contract"] = pr
_spec.loader.exec_module(pr)

OUT = ("CONTRACT: beds :: bed span from_shot 22 has no cut shot at or after it\n"
       "VERDICT      : REFUSED\n")


def test_a_contract_row_is_collected_by_fault_rows():
    rows = pr.fault_rows(OUT)
    assert rows == ["CONTRACT: beds :: bed span from_shot 22 has no cut shot at or after it"]


def test_the_collected_row_routes_to_the_bed_cure():
    from studio import plan_cures as pc
    assert pc.cure_for(pr.fault_rows(OUT)[0]) == "clamp_beds"


def test_the_contract_ok_banner_is_not_a_fault_row():
    assert pr.fault_rows("CONTRACT OK: x | 26 shots | 147s projected\nVERDICT      : clean\n") == []
