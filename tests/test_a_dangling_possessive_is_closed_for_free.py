"""P11's dangling possessive is cured for free: "to the safe's," -> "to the safe,".

Jekyll ep05 (2026-10-28): shot 27's camera read "The camera tilts up from the door to the safe's,
across the whole shot"; the plan's climbs spent, PLAN kept best and step 06's take lint refused T27,
parking the episode on a word.  The noun is gone; the possessive alone is the fault.
"""
from studio import plan_cures as pc

SHOT = {"index": 27, "motion": "The camera tilts up from the door to the safe's, across the whole shot; "
                              "the lawyer swings the safe door shut onto the papers"}


def test_the_lint_row_routes_to_the_free_cure():
    assert pc.cure_for("G-TAKELINT card T27: P11 dangling aim: safe's,") == "close_possessives"
    assert pc.cure_for("P11 dangling aim: shot 27 safe's,") == "close_possessives"


def test_the_possessive_closes_and_the_rest_stays():
    doc = pc.close_possessives({"shots": [dict(SHOT)]})
    assert doc["shots"][0]["motion"] == ("The camera tilts up from the door to the safe, across the whole shot; "
                                         "the lawyer swings the safe door shut onto the papers")


def test_a_possessive_with_its_noun_and_a_contraction_are_left_alone():
    kept = "The camera pans to the lawyer's face; he says it's late, and turns"
    assert pc.close_possessives({"shots": [{"index": 1, "motion": kept}]})["shots"][0]["motion"] == kept
