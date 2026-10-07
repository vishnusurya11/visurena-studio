"""ep19, 2026-10-07 15:02Z: the signed plan staged 'broken_crockery', 'copper',
'rain_water_pump', 'green_vapour' -- scenery nouns the writer listed as setup
props -- and step 03 died opening analysis/props/broken_crockery.json.  A prop
is a card (one picture per entity); a setup may stage only pids with a card.
G-PROPCARD refuses the rest at the plan, hard, and its line routes to the
free `legal_props` cure, which drops them (the prose already carries them)."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_cures, plan_gates


def _plan(props: list[str]):
    return SimpleNamespace(setups={"scullery": SimpleNamespace(props=props), "pit": SimpleNamespace(props=[])})


def _doc(props: list[str]) -> dict:
    return {"setups": {"scullery": {"described": "x", "props": props}, "pit": {"described": "y", "props": []}}}


def test_a_staged_pid_with_a_card_passes():
    ep = _plan(["fighting_machine"])
    assert plan_gates.prop_card_faults(ep, {"fighting_machine"}) == []


def test_a_staged_pid_without_a_card_is_one_hard_line_naming_setup_and_pid():
    ep = _plan(["fighting_machine", "broken_crockery"])
    lines = plan_gates.prop_card_faults(ep, {"fighting_machine"})
    assert len(lines) == 1
    assert "G-PROPCARD" in lines[0] and "broken_crockery" in lines[0] and "no card" in lines[0] and "scullery" in lines[0]


def test_the_line_routes_to_the_legal_props_cure_which_drops_the_pid():
    ep = _plan(["fighting_machine", "broken_crockery"])
    line = plan_gates.prop_card_faults(ep, {"fighting_machine"})[0]
    assert plan_cures.cure_for(line) == "legal_props"
    cured = plan_cures.legal_props(_doc(["fighting_machine", "broken_crockery"]), {"fighting_machine"})
    assert cured["setups"]["scullery"]["props"] == ["fighting_machine"]
