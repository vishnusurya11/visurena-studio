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


def test_an_unnumbered_grid_forbids_lettering_outright():
    """MEASURED 2026-09-20: asked for 'the panel number small in the corner',
    Qwen drew the SHOT SIZE there instead -- WIDE, MEDIUM, INSERT burned into
    the picture.  Harmless on a review page, and not harmless at all here: a
    panel is going on to be an H3 ref2va reference, and lettering in a
    reference is lettering in the video."""
    from studio.storyboard_grid import geometry
    said = geometry(2, 2, "a painted style", numbered=False)
    assert "top-left corner" not in said, "it must not ASK for a corner label"
    assert "no text" in said.lower() and "no lettering" in said.lower()
    assert "no numbers" in said.lower()


def test_a_numbered_grid_still_asks_for_the_number():
    from studio.storyboard_grid import geometry
    assert "number" in geometry(2, 2, "a painted style", numbered=True).lower()


def test_the_prompt_is_unnumbered_by_default():
    """The default use is an H3 reference, not a page for a person."""
    from studio.storyboard_grid import grid_prompt
    shots = [{"size": "MEDIUM", "body": f"shot {i}", "cut": "at the waist"} for i in range(4)]
    said = grid_prompt(shots, 2, 2, place=([1], "a heath"), cast=[], style="s")
    assert "no lettering" in said.lower()


def test_a_person_with_no_sheet_is_still_described():
    """MEASURED 2026-09-20, ep05 `dusk` as 2x3: shot 13 names the newspaper boy,
    a hand-written cast dict had no entry for him, the binding dropped him
    silently -- and the panel came back a grinning man selling apples.  A person
    the panels name must reach the prompt whether or not a sheet was drawn."""
    from studio.storyboard_grid import cast_clause
    said = cast_clause([{"ref": None, "name": "THE NEWSPAPER BOY",
                         "wear": "a boy of thirteen in a cloth cap",
                         "against": "he is no one else"}])
    assert "THE NEWSPAPER BOY" in said
    assert "<image" not in said, "no slot was staged for him, so none may be cited"


def test_an_unstaged_person_is_not_promised_a_reference():
    from studio.storyboard_grid import cast_clause
    said = cast_clause([{"ref": 3, "name": "A", "wear": "w", "against": "x"},
                        {"ref": None, "name": "B", "wear": "w", "against": "x"}])
    assert "<image3>" in said and "<imageNone>" not in said


def test_a_panel_names_who_stands_in_it():
    """MEASURED 2026-09-20, ep05 `dusk` 2x3 iteration 2: the binding was right
    at last -- one boy, one face, one corduroy jacket across the grid -- and he
    turned up in FOUR panels when only shot 13 names him.  The clause said
    "every panel THE NEWSPAPER BOY appears in gives him this face" and nothing
    anywhere said WHICH panels those were, so he appeared in all of them.

    Binding a person to a slot says who he is. It does not say where he is."""
    from studio.storyboard_grid import panel_block
    said = panel_block(2, "top-right", "MEDIUM", "the heather", cut="at the waist",
                       who=["THE NEWSPAPER BOY"])
    assert "In this panel: THE NEWSPAPER BOY" in said


def test_a_panel_with_nobody_in_it_says_so():
    """Shot 9 is a wide of empty common; leaving it silent let the boy walk in."""
    from studio.storyboard_grid import panel_block
    said = panel_block(1, "top-left", "WIDE", "the common", cut="full figure", who=[])
    assert "no named character" in said.lower()


def test_a_panel_forbids_the_others_by_name():
    from studio.storyboard_grid import panel_block
    said = panel_block(1, "top-left", "WIDE", "x", cut="y", who=["A"], absent=["B", "C"])
    assert "B" in said and "C" in said and "does not appear" in said.lower()


def test_the_cast_says_a_person_keeps_to_his_own_panels():
    from studio.storyboard_grid import cast_clause
    said = cast_clause([NEIGHBOUR, NARRATOR])
    assert "only in the panels that name" in said.lower()


def test_shots_with_nobody_in_them_form_their_own_grid():
    """MEASURED 2026-09-20 on ep05 `dusk`, the finding of this POC.

    A STAGED CHARACTER REFERENCE IS CAST INTO ANY PANEL WHOSE PROSE CALLS FOR
    UNNAMED PEOPLE, however plainly the panel says he is not in it.  Three
    escalating wordings failed: binding him to a slot, naming who stands in
    each panel, and forbidding him by name panel by panel.  He stood in four
    of six.

    Dropping his sheet from the staging -- changing nothing in the words --
    emptied him out of all of them, and the crowd came back individuated: an
    old bearded man, a woman in a shawl, a younger man, no two alike.  With
    this model the references are stronger than the prose, so presence is
    decided by WHAT IS PASSED, not by what is written.
    """
    from studio.storyboard_grid import grid_groups
    shots = [{"index": 9, "faces": []}, {"index": 10, "faces": []},
             {"index": 11, "faces": []}, {"index": 12, "faces": []},
             {"index": 13, "faces": ["boy"]}, {"index": 14, "faces": []}]
    groups = grid_groups(shots)
    empty = [g for g in groups if not g["faces"]]
    assert len(empty) == 1
    assert [s["index"] for s in empty[0]["shots"]] == [9, 10, 11, 12, 14]
    assert [g["faces"] for g in groups if g["faces"]] == [("boy",)]


def test_one_cast_one_grid():
    from studio.storyboard_grid import grid_groups
    shots = [{"index": 0, "faces": ["a"]}, {"index": 1, "faces": ["a", "b"]},
             {"index": 2, "faces": ["a"]}]
    groups = grid_groups(shots)
    assert {g["faces"] for g in groups} == {("a",), ("a", "b")}


def test_a_grid_shape_is_as_square_as_the_count_allows():
    from studio.storyboard_grid import grid_shape
    assert grid_shape(4) == (2, 2)
    assert grid_shape(6) == (2, 3)
    assert grid_shape(2) == (2, 1)
    assert grid_shape(1) == (1, 1)
    assert grid_shape(9) == (3, 3)


def test_an_odd_count_never_leaves_a_hole():
    """A blank cell is a cell the drawer fills with its own invention."""
    from studio.storyboard_grid import grid_shape
    for n in range(1, 13):
        cols, rows = grid_shape(n)
        assert cols * rows == n, f"{n} -> {cols}x{rows} leaves a hole"


def test_the_style_points_at_a_reference_rather_than_describing_itself():
    """MEASURED 2026-09-20. The owner saw it first: the panels were not in the
    book's style at all.

    The Krea2 house anchor was passed as <image1> the whole time, and Qwen took
    the HEATH from it -- the pines, the sand ring, the purple-brown heather --
    and rendered all of it in its own default look: photographic depth of
    field, soft cinematic light, photoreal skin and cloth. A reference is used
    for CONTENT unless the prompt says to use it for STYLE.

    Describing the look in words ("a heavily angular 3d art style with brush
    stroke colour texture") bought nothing across four renders. Naming the slot
    -- DRAWN IN EXACTLY THE ART STYLE OF <image1> -- flipped it on the first
    try, same seed, same 60 s: flat painted shapes, visible brush texture, no
    photographic blur.

    This matters beyond the storyboard. H3 ref2va conditions on its references
    and takes style from them, which is why the delivered episodes look like
    Krea2. A panel in the wrong style drags the video with it."""
    from studio.storyboard_grid import style_clause
    said = style_clause(1, "flat angular shapes, brush-stroke colour texture")
    assert "<image1>" in said
    assert "no photographic depth of field" in said.lower()


def test_the_style_clause_can_cite_several_anchors():
    from studio.storyboard_grid import style_clause
    said = style_clause([1, 2], "flat angular shapes")
    assert "<image1>" in said and "<image2>" in said


def test_an_insert_on_part_of_a_creature_keeps_the_creature_whole():
    """OWNER 2026-09-20: "just horse head can't exist, it should be whole horse,
    we need to focus on the horse head".

    ep05 shot 14 asks for "the black shape of a cab horse's head down in a
    nosebag", and INSERT was carried straight through as "the panel holds the
    object alone, close and filling the frame". A nosebag is an object and a
    horse is not: the panel came back a head with no body, floating over the
    gravel with the hansom shafts barely reading behind it.

    A living thing is never cropped to a part. The part is what the framing
    ATTENDS to; the creature is what the panel CONTAINS."""
    from studio.storyboard_grid import whole_subject
    said = whole_subject("the cab horse in the shafts of its hansom", "its head down in the nosebag")
    assert "whole" in said.lower()
    assert "its head down in the nosebag" in said
    assert "never" in said.lower()


def test_the_attention_is_the_part_and_the_frame_is_the_creature():
    from studio.storyboard_grid import whole_subject
    said = whole_subject("the cab horse", "its head")
    assert said.index("the cab horse") < said.index("its head"), (
        "the creature is stated as what the panel holds before the part it attends to")
