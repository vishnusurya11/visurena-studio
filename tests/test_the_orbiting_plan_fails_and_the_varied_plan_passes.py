"""The fixture lock for G-MOVES: two scrubbed move lists.

`moves_orbit.json` has the shape of the plan the owner refused by eye -- 18
of 23 shots a pan whose subject keeps its third, which is an orbit request --
and `moves_varied.json` the shape of the plan written under the camera
catalog's rules (12 ids over 23 shots).  Generic nouns; the ids are what the
gate must read, so the lock is on the classifier and the three walls at once."""
import json
from pathlib import Path
from types import SimpleNamespace

from studio import plan_gates as pg

FIXTURES = Path(__file__).parent / "fixtures" / "episodes"


def plan(name: str):
    rows = json.loads((FIXTURES / f"moves_{name}.json").read_text(encoding="utf-8"))
    return SimpleNamespace(shots=[SimpleNamespace(**row) for row in rows])


def test_the_orbiting_plan_fails_every_wall():
    faults = pg.moves_faults(plan("orbit"))
    assert any("distinct catalog moves" in f for f in faults)
    assert any("'pan_to' share" in f and "0.78" in f for f in faults)
    assert sum("twice running" in f for f in faults) >= 10


def test_the_varied_plan_passes():
    assert pg.moves_faults(plan("varied")) == []


def test_the_varied_plan_reads_twelve_moves():
    ids = pg.move_ids(plan("varied").shots)
    assert len(set(ids)) == 12
    assert ids[:5] == ["pan_to", "locked", "crane_down", "follow", "high_angle"]
