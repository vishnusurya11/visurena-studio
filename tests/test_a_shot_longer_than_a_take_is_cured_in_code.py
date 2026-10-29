"""Jekyll ep06 (2026-10-28): the plan deferred after three writer rounds (26 min) on one row,
'TAKE BUILDER : shot 7 projects 8.17 s; ... longer than a take (8.0 s)'.  `holds` -- seat a line on
a neighbour, else split the shot -- cures it in code (26 shots -> 27, none over), but the router
knew only the 'TAKE LENGTH' row, so the builder's row went to the writer as creative."""
from studio import plan_cures

BUILDER = ("battery at plan: TAKE BUILDER : shot 7 projects 8.17 s; shot 13 projects 8.56 s -- "
           "longer than a take (8.0 s). Split each into two shots with two lines;")


def test_the_take_builders_row_is_cured_by_holds():
    assert plan_cures.cure_for(BUILDER) == "holds"


def test_the_take_length_row_still_is():
    assert plan_cures.cure_for("battery at plan: TAKE LENGTH  : [(7, 8.17)]") == "holds"
