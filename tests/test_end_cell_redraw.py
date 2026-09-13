"""An END cell is redrawn FROM ITS OWN START CELL, as a picture, not from prose.

MEASURED on episode 2: 9 of 13 drawn END cells are re-staged to a different
camera setup (Q05_0 -> Q05_0E scores 0.072 against its start cell; the band
floor is 0.45).  The sheet prose already SAID the right thing -- "the same
place, the same camera position, the same lens, the same light and the same
wardrobe as panel j, one action later" -- and the drawer did it anyway, because
the same block closes with "Panel k is a DIFFERENT photograph from panel j" and
the sheet-wide no-duplicates law pushes the same way.  Told to be different and
to be the same, the drawer moved the camera.

So the END cell stops being argued for in words and is shown: its own start
cell goes in as Image 1, and the only instruction is what changed.  A picture
holds a camera position; a paragraph competing with another paragraph does not.
"""
import pytest

from studio import episode_seq_board as sq
from studio.episode_spec import Setup

SETUP = Setup(described="the sofa corner of 221B", camera="", cast=["sherlock_holmes"],
              props=[], geography=False)
SEG = {"shot": 5, "sub": 0, "frame": "Close on the wicker arm.", "motion": "The fingers close on the cane.",
       "changed": "the fingers have closed on the cane", "camera": "two feet out", "at_rest": "",
       "crowd": "", "end": True, "of": 1}


def test_the_start_cell_is_image_one():
    said = sq.end_single(SEG, SETUP, {"sherlock_holmes": "A tall man."}, "1:1")
    assert "Image 1 is this same shot ONE MOMENT EARLIER" in said


def test_the_only_change_asked_for_is_the_action():
    said = sq.end_single(SEG, SETUP, {}, "1:1")
    assert "the fingers have closed on the cane" in said


def test_it_never_asks_for_a_different_photograph():
    """The sentence that competed with the camera hold is gone."""
    said = sq.end_single(SEG, SETUP, {}, "1:1")
    assert "different photograph" not in said
    assert "what happened in between" not in said


def test_it_forbids_RE_STAGING_and_not_the_push_that_the_change_implies():
    """"The camera has not moved" contradicts half of episode 2's own END
    changes -- "the door has grown to fill the frame" IS a push in, and 4 of the
    9 cells being redrawn describe exactly that. Told both, the drawer picks one,
    which is how it ended up re-staged. What is forbidden is a NEW SETUP: a
    different part of the room, a different angle, a different subject. Straight
    in or out along the same axis is the whole point of the band."""
    said = sq.end_single(SEG, SETUP, {}, "1:1")
    for phrase in ("same lens", "SIDE", "not been re-positioned",
                   "straight in or out along its own axis"):
        assert phrase in said, phrase
    assert "camera has not moved" not in said


def test_a_start_panel_is_refused_by_the_end_writer():
    with pytest.raises(ValueError, match="END panel"):
        sq.end_single(dict(SEG, end=False), SETUP, {}, "1:1")


# ---- addressing an END cell from the command line ---------------------------

def test_a_key_ending_in_e_names_the_end_panel():
    assert sq.end_key("S05.0E") == (5, 0, True)
    assert sq.end_key("S05.0") == (5, 0, False)
    assert sq.end_key("S19.1E") == (19, 1, True)
    assert sq.end_key("S03") == (3, 0, False)


# ---- the script wires the start cell in as the first attachment -------------

def test_the_script_finds_an_end_panel_and_marks_it(tmp_path):
    import importlib.util, sys
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "redraw_panel", Path("scripts/episode/redraw_panel.py"))
    rp = importlib.util.module_from_spec(spec)
    sys.modules["redraw_panel"] = rp
    spec.loader.exec_module(rp)

    from studio import episode_home
    book = episode_home.book_dir("20260822113400_a-study-in-scarlet")
    episode = episode_home.load_plan(book, 2)
    name, panel = rp.find(episode, "S05.0E")
    assert panel.get("end") is True
    assert (panel["shot"], panel["sub"]) == (5, 0)
    name, panel = rp.find(episode, "S05.0")
    assert not panel.get("end")


# ---- the constraints must not compete with the camera hold ------------------

def test_the_be_distinct_constraint_is_dropped_for_an_end_cell():
    """"one a viewer tells from every other panel at a glance" is the SAME
    instruction as "a different photograph", and it is the pressure that moved
    the camera.  An END cell is drawn alone: there is no other panel to differ
    from, so the line has nothing to buy and a re-stage to pay for."""
    said = sq.end_single(SEG, SETUP, {}, "1:1")
    assert "tells from every other panel" not in said
    assert "wordless" in said          # the rest of the constraints survive
    assert "bare skin" in said


def test_the_change_clause_reads_as_one_sentence():
    """`in the picture you draw: The yellow shaft has risen` -- the same
    mid-sentence capital that had to be fixed in the take prompts."""
    seg = dict(SEG, changed="The yellow shaft has risen out through the TOP edge")
    said = sq.end_single(seg, SETUP, {}, "1:1")
    assert "you draw: the yellow shaft" in said
    assert "you draw: The" not in said


def test_a_name_keeps_its_capital_in_the_change_clause():
    seg = dict(SEG, changed="Holmes's hand has closed on the cane")
    assert "you draw: Holmes's hand" in sq.end_single(seg, SETUP, {}, "1:1")


# ---- attempt 2: name BOTH failures, and ask for a picture not a relation ----

def test_it_names_the_copy_failure_and_the_restage_failure_together():
    """MEASURED both ways on the same 9 cells.

    Sheet prose ("a DIFFERENT photograph") -> 9 of 13 RE-STAGED, 0.072-0.406.
    "Draw Image 1 again, with one thing changed" -> 4 of 5 COPIES, 0.984-0.997.

    The drawer obeys whichever instruction dominates, and neither prompt asked
    for a PICTURE -- both asked for a RELATION to Image 1, which is not
    something that can be drawn. So Image 1 is demoted to what it is good for
    (the place, the people, the light, the angle and the side) and the framing
    is stated as its own picture, with both failures named so neither can win
    by default."""
    said = sq.end_single(SEG, SETUP, {}, "1:1")
    assert "not a copy of Image 1" in said
    assert "not a new camera position" in said


def test_image_one_is_the_source_of_the_angle_not_of_the_framing():
    said = sq.end_single(SEG, SETUP, {}, "1:1")
    assert "ANGLE and SIDE" in said
    assert "Draw Image 1 again" not in said


def test_the_framing_change_is_stated_as_a_move_the_camera_made():
    seg = dict(SEG, changed="the door has grown to fill the frame")
    said = sq.end_single(seg, SETUP, {}, "1:1")
    assert "straight in or out along its own axis" in said
    assert "the door has grown to fill the frame" in said
