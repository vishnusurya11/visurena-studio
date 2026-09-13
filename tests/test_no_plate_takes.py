"""A take with no wide cell stages no plate, and numbers its pictures without one.

MEASURED on episode 2: 13 of the episode's 14 foreign frames are the take's OWN
attached plate, matched at 0.988-0.998 -- T03 opens on Holmes's face and by 1.5 s
the frame IS `plate_sofa.png`, chairs and violin and all. Every one came from a
close or insert segment with no wider cell in the take (Fisher p = 0.0072; 0 of
64 wider frame samples).

Dropping the plate from the reference LIST alone is not enough and fails loudly:
`picture_numbers` fixed the plate at slot `n_faces + 1` and both emitters wrote
a `<Subject>`/`<Picture>` line for it, so the prompt cited a picture the graph
never staged -- "L11 PICTURES: 5 pictures defined against 4 staged references".
The numbering has to close the gap too.
"""
from studio.episode_ref_official import picture_numbers, retention, subjects, summary

FACES = ["john_watson", "sherlock_holmes"]
SEGS = [{"frame": "Close on Watson's hand on the knob.", "motion": "The hand turns."},
        {"frame": "Insert on the silver knob.", "motion": "The knob turns."}]
PHYS = {"john_watson": "A lean man.", "sherlock_holmes": "A tall man."}


def test_with_a_plate_the_slots_are_unchanged():
    plate, cells, last, after = picture_numbers(2, 2, [])
    assert plate == 3 and cells == {0: 4, 1: 5} and after == 6


def test_without_a_plate_the_cells_close_the_gap():
    """No slot is skipped, or the prompt cites a picture nobody staged."""
    plate, cells, last, after = picture_numbers(2, 2, [], has_plate=False)
    assert plate is None
    assert cells == {0: 3, 1: 4}
    assert after == 5


def test_end_cells_follow_the_cells_either_way():
    _p, _c, last, _a = picture_numbers(1, 2, [1], has_plate=False)
    assert last == {1: 4}
    _p, _c, last, _a = picture_numbers(1, 2, [1], has_plate=True)
    assert last == {1: 5}


def test_the_subject_block_omits_the_plate_when_there_is_none():
    said = subjects(FACES, PHYS, "a dim sofa corner", SEGS, [], None, False)[0]
    assert "is the location in" not in said
    assert "<Picture 3> is the first frame of [Shot 1]" in said


def test_the_subject_block_still_defines_the_plate_when_there_is_one():
    said = subjects(FACES, PHYS, "a dim sofa corner", SEGS)[0]
    assert "<Subject 3> is the location in <Picture 3>" in said


def test_the_reference_block_omits_the_plate_when_there_is_none():
    said = retention(FACES, SEGS, {}, 0, [], "a dim sofa corner", has_plate=False)
    # the CAST lines are partially_preserved now too (fix A), so the plate is
    # identified by its own words rather than by that one token
    assert "is the location in" not in said
    assert "(the location behind" not in said
    assert "<Picture 3> ([Shot 1] first frame)" in said


def test_the_reference_block_keeps_the_plate_when_there_is_one():
    said = retention(FACES, SEGS, {}, 0, [], "a dim sofa corner")
    assert "partially_preserved" in said


def test_every_picture_defined_is_a_picture_that_would_be_staged():
    """The invariant L11 checks: defined pictures == staged references."""
    said = subjects(FACES, PHYS, "a corner", SEGS, [], None, False)[0]
    import re
    defined = {int(n) for n in re.findall(r"<Picture (\d+)> is ", said)}
    assert defined == {3, 4}          # two faces at 1-2, then the two cells


# ---- the other two emitters, and the whole prompt ---------------------------

CELLS = {0: 3, 1: 4}


def test_the_summary_names_the_place_in_words_when_no_plate_is_staged():
    """`<Subject 3>` there would cite a subject subject_definitions never defined."""
    said = summary(96, [{"t": 0.0, "end": 2.0}, {"t": 2.0, "end": 4.0}], CELLS,
                   "a dim sofa corner", FACES, [], has_plate=False)
    assert "<Subject 3>" not in said
    assert "sofa corner" in said


def test_the_summary_still_names_the_plate_subject_when_one_is_staged():
    said = summary(96, [{"t": 0.0, "end": 2.0}, {"t": 2.0, "end": 4.0}], {0: 4, 1: 5},
                   "a dim sofa corner", FACES, [])
    assert "<Subject 3>" in said


def test_a_faceless_take_with_no_plate_still_names_what_it_carries():
    """`who` fell back to the plate subject; with no plate it falls to the first cell."""
    said = summary(96, [{"t": 0.0, "end": 2.0}], {0: 1}, "a dim corner", [], [], has_plate=False)
    assert "<Subject" not in said
    assert "<Picture 1>" in said


def test_the_plate_lints_go_quiet_when_no_plate_is_staged():
    """L11's two plate rules key off facts['plate']; a staged-nothing slot must be None."""
    from studio.episode_ref_official import prompt_facts
    segs = [{"t": 0.0, "t_to": 4.0, "size": "close", "crowd": ""}]
    assert prompt_facts(96, segs, FACES, [], {}, 0.0, None, 0, 4, has_plate=False)["plate"] is None
    assert prompt_facts(96, segs, FACES, [], {}, 0.0, None, 0, 5)["plate"] == 3
