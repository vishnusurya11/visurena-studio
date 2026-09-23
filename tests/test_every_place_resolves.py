"""Every place every plan names resolves to a picture on disk.

Guard for audit items 8 and 13. ep09's garden row once named
`wide_establishing.png` while its folder held only `wide_morning.png`; that
would have refused the episode's first take, after the audio, the grids and
the panels were already made. This finds it from the plans alone, in a second.
It reads the live library, so it is skipped where the library is absent.
"""
import json
from pathlib import Path

import pytest

from studio import pack_refs

BOOK = Path(__file__).resolve().parents[1] / "library" / "20260827135508_the-war-of-the-worlds"
PLANS = sorted(BOOK.glob("episodes/ep*/plan.json")) if BOOK.exists() else []


@pytest.mark.skipif(not PLANS, reason="no library on this machine")
@pytest.mark.parametrize("plan", PLANS, ids=lambda p: p.parent.name)
def test_every_setup_place_resolves_to_a_drawn_picture(plan):
    setups = json.loads(plan.read_text(encoding="utf-8")).get("setups", {})
    missing = []
    for name, setup in setups.items():
        if not setup.get("location"):
            continue
        try:
            pack_refs.location_view(BOOK, setup["location"], view=setup.get("view", ""))
        except SystemExit as why:
            missing.append(f"{name}: {why}")
    assert not missing, "\n".join(missing)
