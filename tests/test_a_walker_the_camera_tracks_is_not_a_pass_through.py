"""A walker the camera tracks WITH reads exactly like a pass-through -- the
person holds his screen place and the set slides -- and is correct.  The plan
decides: the held row's eligibility rule is kept, unchanged, for the dense
measure.  A better flow field does not get to overrule the plan's words.
"""
from studio import take_lock as tl
from synth_frames import fixed_face, pan, pin_person

TRACKS_WITH = ("The camera tracks with him along the platform at his own pace, a truck with small amplitude, "
               "keeping him in the middle of the picture; he calls out the paper")
PANS_WITH = "The camera pans to the right with him as he moves off; he goes on shouting"
STRIDING = "The camera tracks sideways along the road; he goes on striding toward the gate"
TRUCK = ("The camera tracks sideways to the right along the fence, a truck with small amplitude, "
         "travelling one short stride; he goes on holding the basket out")


def test_the_number_reads_the_same_and_the_plan_excuses_it():
    got = tl.pass_through(pin_person(pan()), track=fixed_face)
    assert got["pass_through"] > 0.75 and got["lock"] > 0.75            # the measure fires
    for walker in (TRACKS_WITH, PANS_WITH, STRIDING):
        row = tl.pass_through_row(got, walker)
        assert row.ok and row.value is None and row.note == "n/a by the plan"
    assert not tl.pass_through_row(got, TRUCK).ok


def test_the_eligibility_rule_is_the_held_rows_own():
    assert tl.eligible(TRUCK)
    assert not tl.eligible(TRACKS_WITH) and not tl.eligible(PANS_WITH) and not tl.eligible(STRIDING)
    assert tl.pass_through_row.__module__ == tl.row.__module__


def test_a_small_set_travel_cannot_fire_the_row():
    got = {"pass_through": 0.95, "lock": 1.0, "scen": tl.TRAVEL - 1, "subj": 0.0, "fitted_on": tl.FITTED_ON}
    assert tl.pass_through_row(got, TRUCK).ok
    got["scen"] = tl.TRAVEL
    assert not tl.pass_through_row(got, TRUCK).ok
