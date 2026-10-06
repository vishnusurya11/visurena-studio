"""G-FACE-KIND: a creature id in Shot.faces, SubShot.faces or Setup.cast stages
a humanoid character sheet for a thing whose drawn form is a prop card.  The
gate refuses at the plan (distinct from takes_r2v.adopt_names, which refuses a
MISSING gender at render time); the cure drops exactly the creature ids.  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_cures as pc
from studio import plan_gates as pg


def ep_of(faces, cut_faces, cast):
    cut = SimpleNamespace(faces=list(cut_faces))
    s = SimpleNamespace(index=4, faces=list(faces), cuts=[cut])
    return SimpleNamespace(shots=[s], setups={"pit": SimpleNamespace(cast=list(cast))})


def test_faces_cuts_and_cast_each_hold_a_fault():
    found = pg.creature_face_faults(ep_of(["martians", "narrator"], ["martians"],
                                          ["martians", "curate"]), {"martians"})
    assert len(found) == 3
    assert all("G-FACE-KIND" in f and "'martians'" in f and "creature row" in f for f in found)
    assert sum("shot 4" in f for f in found) == 2
    assert sum("setup pit" in f for f in found) == 1


def test_a_human_cast_is_clean():
    assert pg.creature_face_faults(ep_of(["narrator"], [], ["curate"]), {"martians"}) == []


def test_the_cure_drops_only_the_creature_and_repasses_the_gate():
    doc = {"shots": [{"index": 4, "faces": ["martians", "narrator"],
                      "cuts": [{"faces": ["martians"], "at_s": 2.0}]}],
           "setups": {"pit": {"cast": ["martians", "curate"]}}}
    out = pc.drop_creature_faces(doc, {"martians"})
    assert out["shots"][0]["faces"] == ["narrator"]
    assert out["shots"][0]["cuts"][0]["faces"] == []
    assert out["setups"]["pit"]["cast"] == ["curate"]
    cured = ep_of(out["shots"][0]["faces"], out["shots"][0]["cuts"][0]["faces"],
                  out["setups"]["pit"]["cast"])
    assert pg.creature_face_faults(cured, {"martians"}) == []
