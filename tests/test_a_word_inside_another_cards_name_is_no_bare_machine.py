"""G-STAGE and its cure measure identically (ep19, 2026-10-05).

ep19 shots 8, 9 and 11 say "the opened the Martian cylinder" -- the CYLINDER's
card name.  The gate read the 'martian' inside it as a bare word for the
fighting-machine (term 'martian') and fired three rows; the cure masks every
card name first, found nothing, and returned the doc unchanged -- three rows no
round could ever clear.  A word inside ANOTHER card's name is that card, not a
bare alias: both sides now mask the other cards' names before the term test.
Real ep19 text and the chapter's real vocab, no disk, $0."""
from __future__ import annotations

import copy
from types import SimpleNamespace

from studio import pack_refs
from studio import plan_cures as pc
from studio import plan_gates as pg

VOCAB = {"machines": {
    "digging_machine": {"name": "the Martian digging mechanism", "terms": ["mechanism"],
                        "physical": "A small busy machine."},
    "fighting_machine": {"name": "the Martian fighting-machine",
                         "terms": ["giant", "hood", "martian", "stilts", "titan", "tripod"],
                         "physical": "A walking engine of glittering metal."},
    "handling_machine": {"name": "the Martian handling-machine",
                         "terms": ["handling-machine", "spider", "tentacle"],
                         "physical": "A crablike engine of jointed levers."},
    "martian_cylinder": {"name": "the Martian cylinder", "terms": ["cylinder", "projectile"],
                         "physical": "A huge pitted metal cylinder."}},
    "creatures": {"martians": ["martian"]}}

SHOT_9 = {
    "index": 9, "setup": "slit_interior",
    "frame": "Medium-close view of the curate at the triangular slit, his face turned toward "
             "the pit while the narrator listens behind him, with the opened the Martian "
             "cylinder far beyond.",
    "motion": "The camera tracks laterally to the RIGHT past the narrator's shoulder, with the "
              "curate behind it, across the whole shot; the curate presses his eye toward the "
              "opening; green vapour lifts beyond the beam.",
    "at_rest": "THE FOCUS OF THE PICTURE IS the curate (pale blue eyes, black clerical "
               "waistcoat), his head a quarter of the frame's height at CENTER; the opened the "
               "Martian cylinder lies far beyond at the CENTER, and the beam crosses the upper edge.",
    "end": "The curate occupies the aperture; the opened the Martian cylinder glows through "
           "the slit at CENTER, green vapour crosses the opening, and dust hangs at the beam."}

PROPS = ["martian_cylinder", "handling_machine", "fighting_machine", "green_vapour", "martian"]


def doc_of(**over) -> dict:
    return {"shots": [{**SHOT_9, **over}],
            "setups": {"slit_interior": {"described": "A ruined kitchen.", "props": list(PROPS)}}}


def as_ep(doc: dict):
    shots = [SimpleNamespace(cuts=[], faces=[], **s) for s in doc["shots"]]
    setups = {k: SimpleNamespace(described=v.get("described", ""), crowd=v.get("crowd", ""),
                                 geometry=v.get("geometry", ""), props=v.get("props") or [],
                                 cast=[]) for k, v in doc["setups"].items()}
    return SimpleNamespace(shots=shots, setups=setups)


def test_mask_other_cards_blanks_every_name_but_the_pids_own():
    text = "the Martian cylinder beside the Martian fighting-machine"
    out = pack_refs.mask_other_cards(text, VOCAB["machines"], "fighting_machine")
    assert "cylinder" not in out and "fighting-machine" in out and len(out) == len(text)


def test_a_martian_inside_the_cylinders_name_is_no_bare_fighting_machine():
    assert pg.stage_faults(as_ep(doc_of()), VOCAB) == []


def test_the_cure_leaves_the_same_text_alone():
    doc = doc_of()
    cured, unresolved = pc.stage_machines(copy.deepcopy(doc), VOCAB)
    assert cured == doc and unresolved == []


def test_a_real_bare_alias_beside_it_is_flagged_and_then_cured():
    doc = doc_of(end=SHOT_9["end"] + " A tripod stands on the far rim.")
    assert any("bare word 'tripod'" in f for f in pg.stage_faults(as_ep(doc), VOCAB))
    cured, _ = pc.stage_machines(doc, VOCAB)
    assert pg.stage_faults(as_ep(cured), VOCAB) == []
    assert "the Martian fighting-machine" in cured["shots"][0]["end"]
