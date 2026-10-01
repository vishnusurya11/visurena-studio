"""ep16 (2026-10-01): l18 ("We must go that way.", 1.75 s) was refused at
episode_voice 0.74 against the 0.75 floor -- while the sibling design gate
refuses to MEASURE similarity under SIM_MEASURABLE_S (2.0 s) at all, because
one-second slices of a TRUE voice score 0.07-0.32.  The two walls now agree:
an alternate-reference render under 2.0 s records its episode_voice and is
never gated on it; words and pace still gate it.  $0: a comparison."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sl", ROOT / "scripts" / "episode" / "say_lines.py")
sl = importlib.util.module_from_spec(spec)
sys.modules["sl"] = sl
spec.loader.exec_module(sl)


def test_a_short_clip_records_but_never_gates_episode_voice():
    assert sl.alternate_ok(0.74, seconds=1.75) is True     # unmeasurable: recorded, not gated
    assert sl.alternate_ok(0.74, seconds=4.0) is False     # measurable: the floor rules
    assert sl.alternate_ok(0.80, seconds=4.0) is True
    assert sl.alternate_ok(None, seconds=1.0) is True      # design-clip render: nothing to judge
