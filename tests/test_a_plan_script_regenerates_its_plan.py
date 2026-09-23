"""Every plan script regenerates the plan.json it stands for, byte for byte.

Audit item 14, measured 2026-09-22: ep01, ep03 and ep04 had fixes patched
straight into plan.json by session scripts, so their plan .py files no longer
produce what shipped -- re-running one silently reverts fixes already
published (ep01 differs on every shot from 0 to 9, ep03 on shots 3 and 8,
ep04 on 4, 9, 18, 19 and 21). ep02 and ep05-ep09 regenerate identically.

A fix goes into the plan .py, and the .py is run. The three published
divergences are recorded as STRICT expected failures: the debt stays visible,
and the day someone ports their patches back the test flips to a failure and
the marker comes off.
"""
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "library" / "20260827135508_the-war-of-the-worlds" / "episodes"
PLANS = sorted((ROOT / "scripts" / "episode" / "plans").glob("wotw_ep*.py"))
PATCHED_BY_HAND = {"01", "03", "04"}


def episode_of(py: Path) -> str:
    return re.search(r"ep(\d\d)", py.name).group(1)


def cases():
    for py in PLANS:
        n = episode_of(py)
        mark = pytest.mark.xfail(strict=True, reason=f"ep{n}'s plan.json was patched by hand; "
                                 f"port those patches into {py.name}") if n in PATCHED_BY_HAND else ()
        yield pytest.param(py, marks=mark, id=f"ep{n}")


@pytest.mark.skipif(not BOOK.exists(), reason="no library on this machine")
@pytest.mark.parametrize("py", list(cases()))
def test_the_plan_script_regenerates_its_plan(py):
    spec = importlib.util.spec_from_file_location(py.stem, py)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    on_disk = json.loads((BOOK / f"ep{episode_of(py)}" / "plan.json").read_text(encoding="utf-8"))
    assert json.dumps(module.build(), sort_keys=True) == json.dumps(on_disk, sort_keys=True)
