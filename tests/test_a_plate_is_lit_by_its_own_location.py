"""A plate's light is the LOCATION'S light, not a photographic default.

`PLATE_FRAME` ended with "Deep focus, even natural light." -- a camera
instruction, sitting after the style and before the location's own description,
and it fights the scene.  "Even natural light" is daylight, so every plate in the
book has been drawn in daylight whatever hour the scene happens at.

MEASURED on episode 5, 2026-09-14, before a penny of sheet money was spent: four
of its six setups are after dark and say so at length -- "after dark", "the
curtains pulled across the two windows behind", "one gas bracket burning amber on
the wall above", "the gas turned down to a bead", "close upon midnight" -- and
all four plates came back with bright grey daylight in the windows.

That matters because the plate is the room DEFINITION handed to the sheet drawer
and then to the take as a `<Subject>`; a plate that says noon binds noon into
every picture restaged from it.  Episodes 1 to 4 were mostly morning scenes, so
the default agreed with them by luck.

The fix is to say nothing about light here.  `described` always names its own
light sources -- the palette line already carries "gaslight amber" and "practical
period light sources" -- so the only thing the frame clause needs to assert is
the framing and the depth.
"""
from studio.trailer_refs import PLATE_FRAME, location_prompt

PALETTE = "Muted desaturated palette of soot-black, gaslight amber and cold grey."
NIGHT = ("The hearth of a first-floor sitting-room after dark: a coal fire burning red in the "
         "grate, the curtains pulled across the windows, and one gas jet burning low amber.")
DAY = ("The sofa corner of a first-floor sitting-room: the grey light of a March afternoon "
       "coming flat through two sash windows.")


def test_the_frame_clause_asserts_no_light():
    said = PLATE_FRAME.lower()
    assert "natural light" not in said
    assert "even" not in said or "even natural" not in said


def test_it_still_asks_for_an_empty_location():
    assert "empty" in PLATE_FRAME.lower() and "unoccupied" in PLATE_FRAME.lower()


def test_it_still_asks_for_deep_focus():
    assert "deep focus" in PLATE_FRAME.lower()


def test_a_night_locations_own_light_is_the_only_light_named():
    said = location_prompt(NIGHT, PALETTE)
    assert "burning low amber" in said and "curtains pulled across" in said
    assert "even natural light" not in said


def test_a_day_location_still_says_daylight_because_it_says_so_itself():
    said = location_prompt(DAY, PALETTE)
    assert "grey light of a March afternoon" in said


def test_the_palette_still_carries_the_period_light_sources():
    assert "gaslight amber" in location_prompt(NIGHT, PALETTE)
