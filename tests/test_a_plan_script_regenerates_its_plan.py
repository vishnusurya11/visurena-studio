"""Every plan script regenerates the plan.json it stands for, byte for byte.

A plan is book content and lives beside its plan.json under the library
(`library/<book>/episodes/epNN/plan.py`); the code tree names no book.  A fix
goes into the plan .py and the .py is run; a plan.json patched in place by hand
would silently revert the next time its script ran.

A script that declares `PATCHED_BY_HAND = True` records exactly that debt: its
plan.json carries patches the script does not.  It is a STRICT expected
failure, so the day someone ports the patches back the test flips and the
marker comes off.  The library is gitignored, so on a machine without it the
test skips.
"""
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "library"


def plan_scripts() -> list[Path]:
    return sorted(LIBRARY.glob("*/episodes/ep*/plan.py")) if LIBRARY.exists() else []


def load(py: Path):
    spec = importlib.util.spec_from_file_location(f"plan_{py.parent.name}_{py.parents[2].name[:14]}", py)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def patched_by_hand(py: Path) -> bool:
    return re.search(r"^PATCHED_BY_HAND = True", py.read_text(encoding="utf-8"), re.M) is not None


def cases():
    for py in plan_scripts():
        label = f"{py.parents[2].name[:14]}-{py.parent.name}"
        mark = pytest.mark.xfail(strict=True, reason=f"{label}'s plan.json was patched by hand; "
                                 f"port those patches into {py}") if patched_by_hand(py) else ()
        yield pytest.param(py, marks=mark, id=label)


@pytest.mark.skipif(not plan_scripts(), reason="no library with plan scripts on this machine")
@pytest.mark.parametrize("py", list(cases()))
def test_the_plan_script_regenerates_its_plan(py):
    on_disk_path = py.with_name("plan.json")
    if not on_disk_path.exists():
        pytest.skip(f"{py.parent.name} has a plan script but no plan.json yet")
    module = load(py)
    on_disk = json.loads(on_disk_path.read_text(encoding="utf-8"))
    assert json.dumps(module.build(), sort_keys=True) == json.dumps(on_disk, sort_keys=True)
