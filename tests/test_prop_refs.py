"""A prop reference: three measures, and a picture with a body in it.

MEASURED on episode 2, which drew nine props from WORDS alone across six
independent sheets: the violin came back at 0.36 of its size (a child's fiddle
under a six-foot jaw, and correct at 63 cm in panel 1 of the SAME sheet), a
shawl at 3.0, a fingerprint asked "a thumbnail wide" at about 11 times its area,
the walking-stick shaft at 1.95, and in one panel the poker was drawn AS the
walking stick.  Range across the nine: 0.36x to 3.0x.

The controlled comparison is the blue envelope, the one prop in the episode that
had a picture -- and only by accident, because the commissionaire's bust happens
to show it in his hand against his chest.  It came back at 1.25x over ten panels
and three sheets.

So the brick is: gpt-image copies APPEARANCE and never ABSOLUTE SIZE, and the
only thing in a picture that carries absolute size is a human body.  A prop
reference therefore shows the object held in a hand or standing against a
figure, never alone on a table, and the contract states three measures.
"""
import pytest
from pydantic import ValidationError

from studio.prop_refs import Prop, contract_sentence, reference_prompt, refs_row

STICK = dict(
    id="walking_stick", name="Watson's walking stick",
    overall="stands hip high on a six-foot man and reaches a little over half his own height",
    cross_section="its shaft is as thick as one finger",
    detail="a polished silver ball knob the size of a plum caps it",
    material="a black lacquered hardwood shaft with a silver knob and an iron ferrule",
    sits="on the ground beside his right boot with his hand closed on the knob",
    held_by="john_watson")


def test_a_prop_needs_all_three_measures():
    for missing in ("overall", "cross_section", "detail"):
        with pytest.raises(ValidationError):
            Prop(**{**STICK, missing: ""})


def test_the_overall_measure_must_reference_a_body():
    """A measure in inches means nothing to a model that has no ruler; a measure
    against a body is the only one that survives into a drawing."""
    with pytest.raises(ValidationError):
        Prop(**{**STICK, "overall": "it is about ninety centimetres long"})


def test_a_measure_against_a_body_passes():
    for said in ("stands hip high on a six-foot man", "as long as a man's forearm",
                 "as wide as his own spread hand", "reaches the height of his shoulder"):
        assert Prop(**{**STICK, "overall": said}).overall == said


def test_a_prop_refuses_a_negation():
    with pytest.raises(ValidationError):
        Prop(**{**STICK, "detail": "the knob has no engraving on it"})


def test_a_prop_refuses_a_pace_word():
    with pytest.raises(ValidationError):
        Prop(**{**STICK, "sits": "it leans slowly against the chair"})


def test_the_contract_sentence_carries_every_measure():
    said = contract_sentence(Prop(**STICK))
    for part in (STICK["overall"], STICK["cross_section"], STICK["detail"], STICK["material"]):
        assert part.rstrip(".") in said


def test_the_reference_picture_puts_a_body_in_frame():
    """The whole point: no body, no scale."""
    said = reference_prompt(Prop(**STICK), "Muted soot-black and gaslight amber.")
    assert "hand" in said.lower()
    assert "plain" in said.lower()
    assert STICK["overall"] in said


def test_a_prop_nobody_holds_stands_against_a_figure():
    lone = Prop(**{**STICK, "id": "poker", "name": "the iron poker", "held_by": "",
                   "sits": "upright on the tiled kerb beside the brass fender"})
    said = reference_prompt(lone, "Muted soot-black.")
    assert "figure" in said.lower() or "hand" in said.lower()


def test_the_refs_row_matches_the_character_and_location_shape():
    row = refs_row(Prop(**STICK))
    assert row["kind"] == "prop"
    assert row["ref_id"] == "prop-walking_stick"
    assert row["entity_id"] == "walking_stick"
    assert row["rel_path"] == "refs/props/prop-walking_stick.png"
    assert row["physical"] == contract_sentence(Prop(**STICK))


def test_the_id_is_a_slug():
    with pytest.raises(ValidationError):
        Prop(**{**STICK, "id": "Watson's Stick"})


def test_the_row_round_trips_without_losing_a_field():
    """`material` is the FIRST clause of the contract sentence, so a row that
    drops it produces a DIFFERENT contract on the way back in -- and silently,
    because `material` is optional. Every field the model carries must survive."""
    from studio.prop_refs import prop_from_row

    prop = Prop(**STICK)
    back = prop_from_row(refs_row(prop))
    assert back.model_dump() == prop.model_dump()
    assert contract_sentence(back) == contract_sentence(prop)
    assert STICK["material"] in contract_sentence(back)
