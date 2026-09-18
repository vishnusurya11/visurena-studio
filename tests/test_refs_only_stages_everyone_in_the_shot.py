"""With no storyboard, a take stages EVERY person the shot shows and the place
it happens in.

OWNER, 2026-09-17, reading episode 14's staged inputs:
  T00, a wide of the cell with Jefferson Hope's dead body -- "why only location?
      why not Jefferson image as the dead body is his?"
  T01, a close on that body's face -- "this needs location image too ...
      continuation on previous image, so you define the position relative to
      things in location, so it's accurate"
  T03, a wide of the sitting-room -- "where is the fucking Sherlock and Watson,
      they should be inputs too"

The pipeline's old rules were written for a world with drawn cells in it:
`faces` means "whose face must READ" (so a wide names nobody), and
`places_the_plate` withholds the room from a tight take (so a close gets no
room). With references alone, both starve the take of the only pictures it has.
The vendor's own guide keeps them safe: a card and a plate are cited INSIDE
`<Subject N>` and never given a `<Picture N>` line of their own, which is what
stops a reference's framing being copied.
"""
import sys

sys.path.insert(0, "scripts/episode")

import takes_r2v


class Shot:
    def __init__(self, index, size, faces, frame="", motion="", camera="", at_rest=""):
        self.index, self.size, self.faces = index, size, list(faces)
        self.frame, self.motion, self.camera, self.at_rest = frame, motion, camera, at_rest
        self.end = self.changed = ""
        self.cuts = []


CAST = ["jefferson_hope", "sherlock_holmes", "john_watson"]


def test_a_wide_stages_the_man_its_words_name_even_with_no_readable_face():
    """T00: the body on the flags is Hope's, and `faces` is empty because no face
    has to read."""
    shot = Shot(0, "wide", [], frame="Wide of the cell at dawn: the dead body of Jefferson Hope in the "
                                     "long brownish driving coat lying stretched on the flags.")
    assert takes_r2v.people_staged([shot], CAST) == ["jefferson_hope"]


def test_a_two_hander_wide_stages_both_men():
    """T03: Holmes in one armchair, Watson in the other, and `faces` names neither."""
    shot = Shot(3, "wide", [], frame="Wide of the sitting-room: Sherlock Holmes in the worn armchair at "
                                     "the right, John Watson in the armchair at the left.")
    assert takes_r2v.people_staged([shot], CAST) == ["sherlock_holmes", "john_watson"]


def test_a_face_that_must_read_is_staged_even_if_the_words_do_not_name_him():
    shot = Shot(4, "medium_close", ["sherlock_holmes"], frame="Medium close of the man in the armchair.")
    assert takes_r2v.people_staged([shot], CAST) == ["sherlock_holmes"]


def test_nobody_is_staged_twice_and_the_order_is_first_appearance():
    a = Shot(5, "medium", ["john_watson"], frame="Medium of John Watson at the hearth with Sherlock Holmes.")
    assert takes_r2v.people_staged([a], CAST) == ["john_watson", "sherlock_holmes"]


def test_the_room_is_staged_for_a_tight_take_too(tmp_path):
    """T01: a close still happens somewhere, and the place picture is what says
    where. `places_the_plate` is a cell-era rule and does not run here."""
    book, boards = tmp_path / "book", tmp_path / "boards"
    (book / "refs" / "characters").mkdir(parents=True)
    (boards / "plates").mkdir(parents=True)
    got = takes_r2v.refs_from_cards(book, boards, ["jefferson_hope"], "cell_dawn", "indoor", ["close"])
    assert [p.name for p in got] == ["char-jefferson_hope.png", "plate_cell_dawn.png"]


def test_an_insert_with_no_face_still_stages_the_room(tmp_path):
    book, boards = tmp_path / "book", tmp_path / "boards"
    (boards / "plates").mkdir(parents=True)
    assert [p.name for p in takes_r2v.refs_from_cards(book, boards, [], "cell_dawn", "", ["insert"])] == \
        ["plate_cell_dawn.png"]
