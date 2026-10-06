"""The G-TAKELINT and ROW TEXT rows print at the 4-space indent
plan_repair.fault_rows already collects, advisory lines stay excluded, and
the check() ValueError format is a PINNED PARSE CONTRACT: parse_faults reads
the structured list check() now attaches and falls back to splitting the
exact message -- both halves land together or the gate breaks silently."""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import episode_ref_official as ro  # noqa: E402

pr_spec = importlib.util.spec_from_file_location("plan_repair", ROOT / "scripts" / "episode" / "plan_repair.py")
pr = importlib.util.module_from_spec(pr_spec)
pr_spec.loader.exec_module(pr)

tr_spec = importlib.util.spec_from_file_location("takes_r2v", ROOT / "scripts" / "episode" / "takes_r2v.py")
tr = importlib.util.module_from_spec(tr_spec)
tr_spec.loader.exec_module(tr)

STDOUT = """CONTRACT OK: t | 20 shots | 150s projected
G-LIGHT      : clean
G-TAKELINT   : 2
    G-TAKELINT shot 14: L8 NO PACE [shot 14]: a walk, climb or ride with no pace named [plan]
    G-TAKELINT shot 3: L2 STILLNESS: ['held'] [row mrs_hall]
ROW TEXT     : 1
    G-ROWTEXT L2 STILLNESS: ['holds'] [card revolver]
  advisory: M6 shot 2: a repeated head
    this row says not applicable here
VERDICT      : REFUSED
"""


def test_fault_rows_collects_the_new_rows_and_still_excludes_advisories():
    rows = pr.fault_rows(STDOUT)
    assert rows == [
        "G-TAKELINT shot 14: L8 NO PACE [shot 14]: a walk, climb or ride with no pace named [plan]",
        "G-TAKELINT shot 3: L2 STILLNESS: ['held'] [row mrs_hall]",
        "G-ROWTEXT L2 STILLNESS: ['holds'] [card revolver]",
    ]


def test_the_check_message_format_is_pinned():
    """The exact prefix and '; '-join parse_faults splits on; a reword that
    drops the structured list AND the format breaks this test first."""
    with pytest.raises(ValueError) as refused:
        ro.check("No man moves without a sound.", {})
    said = str(refused.value)
    assert re.match(r"^the prompt fails the lint \(\d+ faults\): L\d+ ", said)
    assert refused.value.faults == ro.lint("No man moves without a sound.", {})
    assert tr.parse_faults(refused.value) == refused.value.faults


def test_parse_faults_splits_the_bare_message_identically():
    with pytest.raises(ValueError) as refused:
        ro.check("No man moves without a sound.", {})
    bare = ValueError(str(refused.value))
    assert tr.parse_faults(bare) == refused.value.faults
