"""A night setup lit by the cure's daylight (Jekyll Kawajiri ep01, 2026-10-18).

The night corner said "Cast-iron gas lamps stand at intervals along each kerb, their flames
burning yellow; the nearest lamp ... throwing hard yellow light down from the upper right".
G-LIGHT split it on commas (the lamp in one clause, the burning in the next) and read
"from the upper right" as no direction; `light_directions` then took the first source word,
"every WINDOW shuttered and dark", and appended "Grey daylight through the window at the
LEFT" to a street at three in the morning.  The master was drawn with a lit window from it."""
from __future__ import annotations

from studio import house_style, plan_cures as pc

NIGHT = ("A crossroads of two narrow London streets at three o'clock of a black winter morning. "
         "Tall soot-dark brick terraces line both streets, every window shuttered and dark. "
         "Cast-iron gas lamps stand at intervals along each kerb, their flames burning yellow; "
         "the nearest lamp stands on the corner itself, throwing hard yellow light down from the "
         "upper right onto the wet cobbles.")
CURED = NIGHT + " Grey daylight through the window at the LEFT, deep shadow."


def doc_of(described: str) -> dict:
    return {"shots": [], "setups": {"night_corner": {"described": described, "outdoors": True}}}


def test_a_lamp_whose_flames_burn_after_a_comma_lights_the_setup():
    assert not house_style.setup_faults(NIGHT, True)


def test_from_the_upper_right_is_a_direction():
    assert house_style.DIRECTIONS.search("throwing light down from the upper right onto the cobbles")


def test_daylight_in_a_night_setup_is_a_g_light_fault():
    faults = house_style.setup_faults(CURED, True)
    assert any("daylight" in f and "night" in f for f in faults)


def test_the_cure_swaps_its_own_daylight_for_lamplight_at_night():
    said = pc.light_directions(doc_of(CURED))["setups"]["night_corner"]["described"]
    assert "daylight" not in said and "Lamplight glows through the window at the LEFT" in said
    assert not house_style.setup_faults(said, True)
    assert pc.light_directions(doc_of(said))["setups"]["night_corner"]["described"] == said


def test_a_new_clause_at_night_is_lamplight():
    bare = "A narrow street at night, every window shuttered, wet cobbles between the terraces."
    said = pc.light_directions(doc_of(bare))["setups"]["night_corner"]["described"]
    assert "daylight" not in said and "amplight" in said
    assert not house_style.setup_faults(said, True)


def test_a_day_setup_keeps_the_daylight_clause():
    day = "A broad street on a Sunday afternoon, a single shop window bright."
    said = pc.light_directions(doc_of(day))["setups"]["night_corner"]["described"]
    assert "Grey daylight through the window at the LEFT" in said
