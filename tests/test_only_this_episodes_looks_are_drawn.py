"""Step 03_04: only the looks this episode stages are drawn, each one hop from
the base sheet by its route, judged by LOOK-STATE with a capped ladder, and
recorded on the look table with the base sheet's sha8 (star)."""
from __future__ import annotations

import json

from studio import look_timeline
from studio.continuity_spec import Layers, Look
from studio.judges.verdict import Fault, Verdict
from tests import continuity_fixtures as fx

from scripts.refs import looks


def draws(calls: list):
    def edit(prompt, source, target, seed):
        calls.append(("edit", prompt, source.name, seed))
        target.write_bytes(fx.PNG)

    def fresh(prompt, target, seed):
        calls.append(("fresh", prompt, target.name, seed))
        target.write_bytes(fx.PNG)
    return {"edit": edit, "fresh": fresh}


def verdict(passed: bool, kind: str = "look_hair_colour") -> Verdict:
    faults = [] if passed else [Fault(kind=kind, where="x", severity="high")]
    return Verdict(judge="look_state", version="1", passed=passed, faults=faults, confidence=1.0)


def test_only_the_staged_undrawn_look_is_missing(tmp_path):
    book = fx.book(tmp_path)
    assert looks.missing_looks(book, fx.episode()) == []                       # ragged is drawn
    assert looks.missing_looks(book, fx.episode({"narrator": "borrowed"})) == [("narrator", "borrowed")]
    assert looks.missing_looks(fx.book(tmp_path / "b", table=False), fx.episode({"narrator": "x"})) == []


def test_a_clothes_look_is_an_edit_of_the_front_crop_and_is_recorded(tmp_path):
    book, calls = fx.book(tmp_path), []
    done = looks.draw_missing(book, fx.episode({"narrator": "borrowed"}), draws(calls), lambda p, l: verdict(True))
    assert done == ["narrator/borrowed"] and calls[0][0] == "edit" and calls[0][2] == "sheet_front.png"
    card = look_timeline.load(book).characters["narrator"]
    assert card.looks["borrowed"].sheet == "refs/characters/narrator/looks/borrowed.png"
    assert card.looks["borrowed"].parent_sha8 == card.base_sha8 != ""
    assert json.loads((book / "refs" / "looks.verdict.json").read_text())["narrator/borrowed"]["passed"]


def test_a_hard_fault_redraws_with_the_faulted_layer_first_then_keeps_the_best(tmp_path):
    book, calls = fx.book(tmp_path), []
    done = looks.draw_missing(book, fx.episode({"narrator": "borrowed"}), draws(calls), lambda p, l: verdict(False))
    assert len(calls) == 1 + looks.MAX_REDRAWS and done == ["narrator/borrowed (flagged)"]
    assert calls[1][1].index("Ash-grey hair") < calls[1][1].index("Borrowed suit")
    assert [c[3] for c in calls] == [calls[0][3], calls[0][3] + 1, calls[0][3] + 2]


def test_a_fresh_look_writes_its_layers_first_then_the_body_then_the_form():
    card = look_timeline.CharacterLooks.model_validate(fx.CARD)
    said = looks.fresh_prompt(card, "ragged", "Narrator. Wearing: a suit. Character reference sheet on grey.")
    assert said.startswith("Ash-grey hair. Grey-brown beard.")
    assert said.index("Man of 34") < said.index("Character reference sheet on grey.")
    assert "a suit" not in said


def test_the_route_follows_the_face():
    assert looks.route_of(Look(face_change=True)) == looks.ROUTES["face"]
    assert looks.route_of(Look(layers=Layers(top="a coat"))) == looks.ROUTES["garment"]
