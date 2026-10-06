"""ghost_limbs, the $0 clause surgeon: the exact surgery the ep17/18 hand
fixes ran.  'over the X's shoulder' keeps the camera position and loses the
body ('from behind'); any other ghost clause is dropped whole; a strip past
30% of the field is refused and handed to the injected rewrite callable."""
from __future__ import annotations

import json

from studio import plan_cures as pc

NAMES = {"brother": "brother", "curate": "curate", "captain": "captain"}

BASE_AT_REST = ("The captain sits square at the kitchen table, the loaf under his left hand, "
                "the lamp burning at the RIGHT of the frame, steam rising off the bowl beside it")


def doc_of(**shot_over):
    shot = {"index": 11, "faces": ["captain"], "cuts": [],
            "frame": "Close over the brother's shoulder on the captain braced at the rail.",
            "at_rest": BASE_AT_REST + "; the curate's shoulder rises at the lower LEFT.",
            "end": "", "motion": "", "camera": ""}
    shot.update(shot_over)
    return {"shots": [shot]}


def test_over_the_brothers_shoulder_becomes_from_behind():
    out = pc.ghost_limbs(doc_of(), NAMES)
    assert out["shots"][0]["frame"] == "Close from behind on the captain braced at the rail."


def test_the_trailing_ghost_clause_is_deleted_whole():
    out = pc.ghost_limbs(doc_of(), NAMES)
    at = out["shots"][0]["at_rest"]
    assert "curate" not in at and "shoulder" not in at
    assert at.startswith("The captain sits square") and at.rstrip().endswith("beside it;")


def test_the_surgery_is_idempotent_on_its_own_output():
    once = pc.ghost_limbs(doc_of(), NAMES)
    frozen = json.dumps(once, sort_keys=True)
    assert json.dumps(pc.ghost_limbs(once, NAMES), sort_keys=True) == frozen


def test_a_field_that_is_mostly_ghost_clause_is_refused_and_handed_on():
    handed = []
    doc = doc_of(frame="The rail.",
                 at_rest="The rail; the curate's shoulder and the curate's arm cross the whole "
                         "lower LEFT of the frame toward the rail's near end.")
    out = pc.ghost_limbs(doc, NAMES, rewrite=lambda index, field: handed.append((index, field)))
    assert out["shots"][0]["at_rest"].endswith("near end.")   # left untouched
    assert handed == [(11, "at_rest")]


def test_without_a_names_table_the_cure_is_a_byte_level_no_op():
    doc = doc_of(frame="Close over the brother’s shoulder on the captain.")
    frozen = json.dumps(doc, sort_keys=True)
    assert json.dumps(pc.ghost_limbs(doc, {}), sort_keys=True) == frozen


def test_a_cuts_ghost_clause_is_cured_against_the_joined_faces():
    cut = {"at_s": 2.0, "faces": ["curate"],
           "at_rest": "The curate's hand lifts the latch a finger's breadth, the lamplight "
                      "catching the worn brass plate and the grain of the oak door around it; "
                      "the brother's shoulder leans into the RIGHT edge.",
           "frame": "", "end": "", "motion": "", "camera": ""}
    doc = {"shots": [{"index": 3, "faces": ["captain"], "cuts": [cut], "frame": "A door.",
                      "at_rest": "", "end": "", "motion": "", "camera": ""}]}
    out = pc.ghost_limbs(doc, NAMES)
    at = out["shots"][0]["cuts"][0]["at_rest"]
    assert at.startswith("The curate's hand") and "brother" not in at
