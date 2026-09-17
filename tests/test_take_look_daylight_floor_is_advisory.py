"""A sunlit exterior's missing black floor is an ADVISORY, not a wall.

MEASURED: ep11 T00 (a day wide, p5 19) moved P5_FLOOR from 15 to 20; ep12 T16
and T27 (the Eagle Canyon in hard sun, p5 22 and 30, near-black 0.07 and 0.03)
failed it again, and their retakes scored lower.  Both pictures are correct
daylight: haze over a valley has no black to find.  The floor was measured on
lamp, fire and candle episodes (ep05-09), so it stays a wall for them and
becomes a scored advisory for an outdoor setup lit by the sky.
"""
from studio import take_look


NO_FLOOR = {"n": 5, "p5": 30.0, "near_black": 0.03, "share": 0.5, "mean": 120.0,
            "near_black_first": 0.03, "near_black_last": 0.03, "share_first": 0.5, "share_last": 0.5}


def test_a_night_take_with_no_floor_is_hard():
    g = take_look.verdict(NO_FLOOR)
    assert g.hard and not g.ok


def test_a_daylight_take_with_no_floor_is_an_advisory():
    g = take_look.verdict(NO_FLOOR, daylight=True)
    assert not g.hard and not g.ok and "daylight" in g.note


def test_daylight_is_an_outdoor_setup_lit_by_the_sky():
    sun = "A rock shelf in the canyon; the sun comes from the left, hard, and throws shadows black"
    grey = "A cab rank on a raw grey afternoon; the low grey sky is the only light"
    assert take_look.is_daylight(sun, outdoors=True)
    assert take_look.is_daylight(grey, outdoors=True)


def test_lamp_fire_candle_and_interiors_are_not_daylight():
    assert not take_look.is_daylight("A wet street at one in the morning; the gas lamp is the only light",
                                     outdoors=True)
    assert not take_look.is_daylight("A nook at dusk; the fire is the only light", outdoors=True)
    assert not take_look.is_daylight("Interior, a cell; the grey dawn through the barred window", outdoors=False)
