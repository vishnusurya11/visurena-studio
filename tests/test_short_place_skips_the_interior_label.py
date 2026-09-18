"""The place's NAME is not the word "Interior".

MEASURED on episode 14's prompts (2026-09-17), and true of episode 13's as
well: an interior setup is written "Interior, inside the hearth end of the
first-floor sitting-room of 221B Baker Street on a March evening in 1881, ..."
because the drawer needs to be told it is indoors with four walls. `short_place`
takes the text up to the first comma, so the model was told the take happens
"in <Subject 2>, Interior" and that "The ambience of Interior runs under the
whole take". The label is a stage direction, not a name: skip it and take the
clause that names the room.
"""
from studio.episode_ref_official import short_place

BAKER = ("Interior, inside the hearth end of the first-floor sitting-room of 221B Baker Street on a "
         "March evening in 1881, the camera within the room with walls closed on all four sides: a "
         "white marble mantelpiece over a black iron grate")
CELL = ("Interior, inside a bare stone police cell at dawn in March 1881, the camera within the cell "
        "with whitewashed stone walls closed on all four sides: a plank bed")
STREET = ("A wet London street of dark brick houses at one in the morning in March 1881, blowing hard "
          "and raining in torrents: a four-wheeled cab")


def test_an_interior_label_is_not_the_place():
    assert short_place(BAKER) == ("inside the hearth end of the first-floor sitting-room of 221B Baker "
                                  "Street on a March evening in 1881")
    assert short_place(CELL) == "inside a bare stone police cell at dawn in March 1881"


def test_an_exterior_label_is_skipped_the_same_way():
    assert short_place("Exterior, a rain-swept quay at night, the water black") == "a rain-swept quay at night"


def test_a_place_that_names_itself_first_is_unchanged():
    assert short_place(STREET) == "a wet London street of dark brick houses at one in the morning in March 1881"
    assert short_place("The chemical laboratory of Saint Bartholomew's Hospital, 1881.") == \
        "the chemical laboratory of Saint Bartholomew's Hospital"


def test_a_label_with_nothing_after_it_keeps_what_it_has():
    assert short_place("Interior") == "Interior"
