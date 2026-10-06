"""The calibration lock: G-GHOST and G-TWICE return [] on the owner-judged
fixture plans (ep05, ep07, ep08) under a names table built from their own
cast ids.  A gate that refuses the judged episodes is one somebody switches
off."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import plan_gates as pg
from studio.episode_spec import Episode

FIXTURES = Path(__file__).parent / "fixtures" / "episodes"


def names_of(ep: Episode) -> dict[str, str]:
    cast = sorted({who for setup in ep.setups.values() for who in setup.cast})
    return pg.names_from_refs([{"entity_id": who} for who in cast])


@pytest.mark.parametrize("name", ["ep05_plan.json", "ep07_plan.json", "ep08_plan.json"])
def test_the_judged_plans_stage_no_ghost_limbs(name):
    ep = Episode(**json.loads((FIXTURES / name).read_text(encoding="utf-8")))
    assert pg.ghost_limb_faults(ep, names_of(ep)) == []


@pytest.mark.parametrize("name", ["ep05_plan.json", "ep07_plan.json", "ep08_plan.json"])
def test_the_judged_plans_place_each_person_once(name):
    ep = Episode(**json.loads((FIXTURES / name).read_text(encoding="utf-8")))
    assert pg.double_position_faults(ep, names_of(ep)) == []
