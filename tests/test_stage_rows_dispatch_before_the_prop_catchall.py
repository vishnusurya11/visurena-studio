"""The new stage families dispatch to THEIR cures, never to the legal_props
catch-all (whose bare 'prop ' alternative would have swallowed them as a no-op)
and never to the writer: machine rows to stage_machines, setup creature rows to
strip_creatures, shot creature rows to stage_machines (one-candidate rename or
the llm pick), face rows to drop_creature_faces, span rows to prop_spans."""
from __future__ import annotations

from studio import plan_cures as pc


def test_a_machine_row_dispatches_to_stage_machines():
    row = ("G-STAGE shot 14: names fighting_machine by 'tripod' and the setup stages "
           "no sheet, measured tripod against card name + setup props entry")
    assert pc.cure_for(row) == "stage_machines"


def test_a_bare_word_row_dispatches_to_stage_machines():
    row = ("G-STAGE shot 2: names fighting_machine by the bare word 'tripod', not its "
           "card name, measured tripod against card name + setup props entry")
    assert pc.cure_for(row) == "stage_machines"


def test_a_setup_creature_row_dispatches_to_strip_creatures():
    row = ("G-STAGE setup lane: bare creature word 'martian'; a drawn creature is its "
           "machine card, measured martian against its machine card's name")
    assert pc.cure_for(row) == "strip_creatures"


def test_a_shot_creature_row_dispatches_to_stage_machines():
    row = ("G-STAGE shot 9: bare creature word 'martian'; a drawn creature is its "
           "machine card, measured martian against its machine card's name")
    assert pc.cure_for(row) == "stage_machines"


def test_a_face_row_dispatches_to_drop_creature_faces():
    row = ("G-FACE-KIND shot 14: 'martians' is a creature row staged as a face; its "
           "drawn form is a prop card, measured martians against no creature-kind faces")
    assert pc.cure_for(row) == "drop_creature_faces"


def test_a_prop_span_row_dispatches_to_prop_spans_not_legal_props():
    row = "G-SOURCE shot 4: prop 'fighting_machine' has no chapter span, measured 0 against 1"
    assert pc.cure_for(row) == "prop_spans"


def test_the_other_spanless_claims_stay_the_writers():
    assert pc.cure_for("G-SOURCE shot 3: posture 'astride' has no chapter span, "
                       "measured 0 against 1") is None
    assert pc.cure_for("G-SOURCE shot 3: extras 2 has no chapter span, "
                       "measured 0 against 1") is None
