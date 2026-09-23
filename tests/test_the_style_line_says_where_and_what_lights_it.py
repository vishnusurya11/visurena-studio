"""The first line of every take prompt names the right place and its real light.

Audit item 17, measured 2026-09-22 on all 20 ep08 takes:
- the line read "...1894, is gaslight, black shadows" -- `source_of` took the
  word before the source as its adjective, and "is" was not a word it skipped;
  others read "that lamp" and "sash windows";
- "sash windows" was chosen over the gas lamp in the same clause, because a
  window counted as a light source like any lamp;
- it said "Horsell, Surrey" at Woking junction, in the railway carriage and in
  the village street, because the place was the episode's, not the setup's.
"""
import pytest

from studio import house_style


@pytest.mark.parametrize("clause,source", [
    ("the light is gaslight", "gaslight"),
    ("the only light is that lamp from the near end", "lamp"),
    ("the light was the moon", "moon"),
    ("which lamp burns at the far end", "lamp"),
])
def test_a_verb_or_a_pointer_is_never_the_sources_adjective(clause, source):
    assert house_style.source_of(clause) == source


def test_a_lamp_is_chosen_over_the_windows_in_the_same_clause():
    assert house_style.source_of("lit sash windows and a gas lamp burning at the kerb") == "gas lamp"


def test_a_window_is_the_source_when_nothing_else_lights_the_place():
    assert house_style.source_of("the light comes through the tall windows") == "tall windows"


def test_the_style_line_names_the_setups_own_place():
    house_style.adopt("Horsell, Surrey, 1894", "gaslight and black shadows")
    house_style.adopt_places({"woking_junction": "Woking junction"})

    class Setup:
        location, described = "woking_junction", "a station platform, the light is gaslight"
    try:
        assert "Woking junction, 1894" in house_style.live(Setup())
        assert "Horsell" not in house_style.live(Setup())
    finally:
        house_style.adopt_places({})
        house_style.adopt("", "")


def test_a_place_name_too_long_for_the_line_falls_back_to_the_episodes():
    house_style.adopt("Horsell, Surrey, 1894", "gaslight and black shadows")
    house_style.adopt_places({"street": "the main street of the old village of Horsell"})

    class Setup:
        location, described = "street", "a street, the light is gaslight"
    try:
        assert "Horsell, Surrey, 1894" in house_style.live(Setup())
    finally:
        house_style.adopt_places({})
        house_style.adopt("", "")


# ---- the two regressions the take lint caught on ep09 ------------------------

def test_a_place_name_that_breaks_the_line_wall_gives_way():
    house_style.adopt("Horsell, Surrey, 1894", "gaslight and black shadows")
    house_style.adopt_look("Angular stylised 3D animation, brush-stroke texture")
    house_style.adopt_places({"bridge": "Maybury canal bridge"})

    class Setup:
        location = "bridge"
        described = "a brick arch; the light is hard white sun from the far end of the arch"
    try:
        assert len(house_style.live(Setup()).split()) <= house_style.MAX_STYLE_WORDS
    finally:
        house_style.adopt_places({})
        house_style.adopt_look("")
        house_style.adopt("", "")


def test_a_place_name_is_not_a_stray_capital():
    from studio.episode_ref_official import stray_capitals
    house_style.adopt_places({"common": "Horsell Common"})
    try:
        line = "Angular style, Horsell Common, 1894, low sun, black shadows."
        assert stray_capitals(line, "out across the open common") == []
    finally:
        house_style.adopt_places({})
