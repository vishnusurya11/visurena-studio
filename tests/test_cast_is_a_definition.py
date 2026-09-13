"""A cast sheet DEFINES a man; it is not a framing any shot uses.

THE FIX WE ALREADY MADE ONCE, FOR THE PLATE, AND NEVER APPLIED TO PEOPLE.
`OWNER 5.16` records it: the plate reads `(the location behind [Shot 1] ...)`,
NOT ref-en 4.1's `(appears in ...)`, because "`appears in` is the phrasing that
measurably invited the plate in as a cutaway (0.88-0.996)".

Every cast sheet still said exactly the banned thing:
    <Subject 1> (appears in [Shot 2]): fully_preserved - face, hair, build and
    clothes exactly as in <Picture 1>.

MEASURED, episode 3 T02: the take was handed TWO whole-frame compositions of
each man -- a full-length studio portrait on a grey backdrop AND the storyboard
cell -- both marked `fully_preserved`. At 4.0 s the render shows a full-length
figure standing with a cane in the middle of the sitting-room: a composition
that matches no staged reference pixel-for-pixel (best 0.118) because the model
re-rendered the CAST CARD'S POSE AND FRAMING into the room.

A cast sheet says who a man IS. The cell says how he is FRAMED. Saying the first
is `fully_preserved` and that he `appears in` a shot conflates them.
"""
from studio.episode_ref_official import retention, subjects

FACES = ["john_watson", "sherlock_holmes"]
PHYS = {"john_watson": "A lean brown man.", "sherlock_holmes": "A tall pale man."}
SEGS = [{"frame": "Close on Watson at the hearth.", "motion": "The hands bring the note up.",
         "size": "close", "crowd": ""},
        {"frame": "Medium close on Holmes risen from the chair.", "motion": "He swings the coat up.",
         "size": "medium_close", "crowd": ""}]


def test_a_cast_sheet_never_says_appears_in():
    """The exact phrasing OWNER 5.16 banned for the plate."""
    said = retention(FACES, SEGS, {}, 0, [], "the hearth")
    assert "appears in" not in said


def test_a_cast_sheet_is_partially_preserved_like_the_plate():
    """`fully_preserved` on a whole-frame picture is an instruction to reproduce
    the PICTURE. What must survive is the man, not the studio backdrop."""
    said = retention(FACES, SEGS, {}, 0, [], "the hearth")
    for line in said.splitlines():
        if line.startswith("<Subject 1>") or line.startswith("<Subject 2>"):
            assert "partially_preserved" in line, line
            assert "fully_preserved" not in line, line


def test_the_cast_line_still_names_which_shots_show_the_man():
    """Dropping `appears in` must not drop the information."""
    said = retention(FACES, SEGS, {}, 0, [], "the hearth")
    assert "[Shot 1]" in said and "[Shot 2]" in said


def test_the_cast_line_says_the_sheet_is_not_a_framing():
    said = retention(FACES, SEGS, {}, 0, [], "the hearth")
    assert "keeps the framing of its own first-frame picture" in said


def test_the_subject_definition_says_the_sheet_defines_the_man_alone():
    said = subjects(FACES, PHYS, "the hearth", SEGS)[0]
    assert "defines this man alone" in said


def test_the_cells_are_still_fully_preserved():
    """The CELL is a framing and must be reproduced -- that part was never wrong."""
    said = retention(FACES, SEGS, {}, 0, [], "the hearth")
    assert "first frame): fully_preserved" in said


def test_the_cell_line_no_longer_demands_a_preserved_viewpoint():
    """22/22 prompts said `fully_preserved - viewpoint` while the same block
    pushed the camera through it. Holmes came back at similarity 1.000 with
    0.12 frame-to-frame change -- the still, reproduced and held."""
    said = retention(FACES, SEGS, {}, 0, [], "the hearth")
    assert "viewpoint" not in said
    assert "subject placement, wardrobe and light" in said
