"""ep17 (2026-10-04): with the good-era brief the writer produced proper shots
(size first, lens, light, one focus) but still put a `crowd` on 5 close shots.
A crowd behind a close face is where H3 minted cast copies in ep16.  A close or
medium-close shot carries no crowd: a gate names it, a mechanical cure blanks
it, and wides keep theirs.  $0: pure data."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_cures, plan_gates


def ep(*shots):
    return SimpleNamespace(shots=[SimpleNamespace(index=i, size=size, crowd=crowd)
                                  for i, (size, crowd) in enumerate(shots)])


def test_a_crowd_on_a_close_shot_is_a_fault():
    faults = plan_gates.close_crowd_faults(ep(("wide", "many refugees"),
                                              ("medium_close", "fugitives behind her"),
                                              ("close", ""),
                                              ("close", "a throng")))
    assert len(faults) == 2
    assert all(f.startswith("G-CROWD-CLOSE") for f in faults)


def test_the_cure_blanks_close_crowds_and_keeps_wides():
    doc = {"shots": [{"index": 0, "size": "wide", "crowd": "many refugees"},
                     {"index": 1, "size": "medium_close", "crowd": "fugitives behind her"},
                     {"index": 2, "size": "close", "crowd": "a throng"}]}
    cured = plan_cures.close_crowds(doc)
    assert [s["crowd"] for s in cured["shots"]] == ["many refugees", "", ""]


def test_the_dispatcher_routes_the_fault_to_the_cure():
    assert plan_cures.cure_for("    G-CROWD-CLOSE shot 4: a close shot carries a crowd") == "close_crowds"
