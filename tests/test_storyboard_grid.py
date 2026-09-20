"""The grid prompt: every block carries its own framing, its own people, one place.

MEASURED 2026-09-20, WotW ep05 shots 5-8 on Qwen-Image-2.1 (poc_qwen_grid_fast):
identity and location held across four panels -- the same face, the same striped
blazer, one sunset -- and panel 4 drew the two men correctly dressed, which is
the exact shot H3 returned with the neighbour in the narrator's suit at DQ
100/100.  Two things did NOT hold, and they are what this module exists to fix:

  * FRAMING WAS IGNORED.  "His head is a quarter of the panel's height" bought
    nothing: panel 1 came back a full-length wide, panel 2 a big close-up.  A
    head fraction is a measurement, and the drawer does not measure.  What it
    obeys is WHERE THE FRAME CUTS THE BODY -- "the frame cuts him at the
    waist" -- so every panel states the cut, and states the shot size twice,
    once as a lead and once as the last clause.
  * TWO HATS BECAME ONE HAT.  The neighbour's soft cream panama came back as a
    flat straw boater with a band, which is the narrator's hat: the one thing
    still blurring two men the prompt worked hard to keep apart.  A wardrobe
    item has to be said by its SHAPE and against the other man's, not named and
    left ("a soft wide flexible brim, NOT a flat stiff boater").
"""
import pytest


NEIGHBOUR = {"ref": 3, "name": "THE NEIGHBOUR",
             "wear": "a soft cream panama with a wide flexible brim",
             "against": "not a flat stiff straw boater"}
NARRATOR = {"ref": 4, "name": "THE NARRATOR",
            "wear": "a flat straw boater with a stiff flat crown and a black band",
            "against": "not a soft floppy panama"}


def test_a_panel_states_where_the_frame_cuts_the_body():
    from studio.storyboard_grid import panel_block
    said = panel_block(1, "top-left", "MEDIUM", "he stands among the furze",
                       cut="the frame cuts him at the waist")
    assert "the frame cuts him at the waist" in said


def test_a_panel_says_its_shot_size_twice():
    """Once leading, once last: a lead alone was overridden by the prose."""
    from studio.storyboard_grid import panel_block
    said = panel_block(1, "top-left", "MEDIUM", "he stands among the furze",
                       cut="the frame cuts him at the waist")
    assert said.count("MEDIUM") == 2
    assert said.rstrip().endswith("MEDIUM.")


def test_a_panel_is_led_by_its_own_cell():
    from studio.storyboard_grid import panel_block
    assert panel_block(3, "bottom-left", "WIDE", "the common", cut="full figure").startswith(
        "PANEL 3, bottom-left")


def test_cells_are_named_row_by_row():
    from studio.storyboard_grid import cell_names
    assert cell_names(2, 2) == ["top-left", "top-right", "bottom-left", "bottom-right"]


def test_a_taller_grid_names_its_rows_by_number():
    """2 by 6 has no word for the fourth row down."""
    from studio.storyboard_grid import cell_names
    names = cell_names(2, 6)
    assert len(names) == 12
    assert names[0] == "row 1 left" and names[1] == "row 1 right"
    assert names[6] == "row 4 left" and names[11] == "row 6 right"


def test_the_geometry_states_the_grid_and_the_numbering():
    from studio.storyboard_grid import geometry
    said = geometry(2, 6, "a painted style")
    assert "2 columns" in said and "6 rows" in said and "twelve panels" in said
    assert "number" in said.lower()


def test_each_person_is_bound_to_an_image_slot():
    from studio.storyboard_grid import cast_clause
    said = cast_clause([NEIGHBOUR, NARRATOR])
    assert "<image3>" in said and "<image4>" in said


def test_a_wardrobe_item_is_said_against_the_other_mans():
    """The panama/boater collapse: shape, and what it is NOT."""
    from studio.storyboard_grid import cast_clause
    said = cast_clause([NEIGHBOUR, NARRATOR])
    assert "not a flat stiff straw boater" in said
    assert "not a soft floppy panama" in said


def test_the_place_names_every_location_slot_it_was_given():
    from studio.storyboard_grid import place_clause
    said = place_clause([1, 2], "Horsell Common at sunset, knee-deep heather")
    assert "<image1>" in said and "<image2>" in said
    assert "never changes" in said


def test_the_whole_prompt_has_one_block_per_panel():
    from studio.storyboard_grid import grid_prompt
    shots = [{"size": "MEDIUM", "body": f"shot {i}", "cut": "at the waist"} for i in range(4)]
    said = grid_prompt(shots, 2, 2, place=place_clause_args(), cast=[NEIGHBOUR, NARRATOR],
                       style="a painted style")
    for n in (1, 2, 3, 4):
        assert f"PANEL {n}," in said


def place_clause_args():
    return ([1, 2], "Horsell Common at sunset, knee-deep heather")


def test_the_prompt_refuses_a_shot_count_that_does_not_fill_the_grid():
    """A short list leaves blank cells the drawer fills with invention."""
    from studio.storyboard_grid import grid_prompt
    shots = [{"size": "MEDIUM", "body": "one", "cut": "at the waist"}]
    with pytest.raises(ValueError, match="4 cells"):
        grid_prompt(shots, 2, 2, place=place_clause_args(), cast=[NEIGHBOUR], style="s")
