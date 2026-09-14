"""An END panel must BE a picture, not a pointer to one.

`end_panel` built the END panel's `frame` as "the same place, the same camera and
the same light as panel N, drawn afresh with this carried through to its finish
-- <verb> -- and every person and object standing where that leaves them".  That
fallback fired on 24 of 24 shots in episode 4, because `Shot.end` is empty on
every one.

So the START panel names nouns at frame fractions and frame edges, and its END
panel names NO FRAMING NOUN AT ALL.  It is a delta with no base, and the only
copy of the base the drawer can see is the panel six inches away on the same
canvas.  Counted on one sheet: each END panel says "same" EIGHT times and carries
a six-noun "Unchanged since panel J" list against ONE change clause, stated last.
Every start panel on that sheet says "same" zero times.

MEASURED over all eleven of episode 4's END pairs -- what separates the three
copies from the four keepers is not the wording, it is whether the change names
a PLACE:

    Q08_0E 0.982  0 blocks  "rubs one hand over his sandy side-whiskers"
    Q11_0E 0.945  0         "knits his brows and sets both hands flat on his knees"
    Q00_0E 0.935  0         "the brick fronts travel past the open window"
    Q15_0E 0.938  4         "lifts one hand OFF HIS KNEE and turns it over"
    Q20_0E 0.856  3         "straightens OFF THE TABLE and turns his face TO THE SASH WINDOW"
    Q21_0E 0.856  3         "lays the half-sovereign down ON THE CHECKED CLOTH and follows
                             Watson OUT THROUGH THE PARLOUR DOOR"
    Q09_0E 0.807  3         "holds it up BETWEEN FINGER AND THUMB"

Every keeper names a body or object at a NEW PLACE in the frame.  Every copy
names a verb with no destination.  The drawer draws nouns at places; it was being
handed a pointer and a verb.

And the stay-clauses were passed straight through -- "his hands stay folded on
the head of his stick", "the gold catches the firelight and holds".  A drawer
told to draw a still in which hands STAY FOLDED draws the same hands.
"""
from studio.episode_seq_board import end_panel, end_text, moved_clause


SEG = {"shot": 21, "sub": 0, "size": "full", "faces": [], "crowd": "",
       "frame": ("Full of the low parlour from the window side: Holmes at the parlour door in the "
                 "LEFT half, Watson beyond him in the doorway, and Rance still seated on the "
                 "horsehair sofa at the BOTTOM RIGHT."),
       "motion": ("Holmes lays the half-sovereign down on the checked cloth and follows Watson out "
                  "through the parlour door; Rance's head comes round after them."),
       "camera": "at the sash window", "at_rest": "", "end_frame": "", "changed": ""}


def test_the_end_panel_inherits_the_start_panels_own_nouns():
    """Not a pointer: the frame text carries the picture."""
    got = end_panel(SEG, 3)["frame"]
    assert "Holmes at the parlour door" in got
    assert "the same place, the same camera" not in got


def test_the_end_panel_states_where_the_change_arrives():
    got = end_panel(SEG, 3)["frame"]
    assert "checked cloth" in got or "parlour door" in got


def test_a_stay_clause_is_not_asked_for_as_a_change():
    """"his hands stay folded" is the drawer being told to redraw the same hands.

    The splitter works on the plan's OWN clause separators, `;` and `,` -- which
    is what episode 4's motion lines use.  It deliberately does NOT split on
    " and ", because that would rescue the first half of "the gold catches the
    firelight and holds", which is a clause about nothing moving."""
    seg = dict(SEG, motion="Holmes's hands stay folded on the head of his stick; he "
                           "lays the coin down on the checked cloth.")
    assert "stay folded" not in end_panel(seg, 3)["changed"]
    assert "coin" in end_panel(seg, 3)["changed"]


def test_a_change_that_is_only_a_stay_clause_is_empty():
    seg = dict(SEG, motion="His eyes hold steady on Rance; his hands remain on his knees.")
    assert end_panel(seg, 3)["changed"] == ""


def test_the_plans_own_end_frame_still_wins():
    seg = dict(SEG, end_frame="A written picture.", changed="a written change")
    got = end_panel(seg, 3)
    assert got["frame"] == "A written picture." and got["changed"] == "a written change"


# ---- the prompt ------------------------------------------------------------

def test_the_end_prompt_does_not_repeat_sameness_eight_times():
    said = end_text(4, end_panel(SEG, 3), "")
    assert said.lower().count("same") <= 1


def test_the_change_comes_first_in_the_end_prompt():
    said = end_text(4, end_panel(SEG, 3), "")
    assert said.index("checked cloth") < said.index("In frame")


def test_the_unchanged_inventory_is_gone():
    assert "Unchanged since panel" not in end_text(4, end_panel(SEG, 3), "")


def test_the_end_prompt_still_names_the_panel_it_closes():
    assert "panel 3" in end_text(4, end_panel(SEG, 3), "").lower()


# ---- the clause helper -----------------------------------------------------

def test_moved_clause_keeps_a_destination():
    assert "off his knee" in moved_clause("Rance lifts one hand off his knee and turns it over")


def test_moved_clause_drops_a_stay():
    assert moved_clause("his hands stay folded on the stick") == ""


def test_moved_clause_drops_hold_remain_and_steady():
    for verb in ("the gold catches the firelight and holds",
                 "his hands remain on his knees",
                 "his eyes hold steady on Rance"):
        assert moved_clause(verb) == "", verb


def test_moved_clause_keeps_the_first_real_move_of_several():
    said = moved_clause("His hands stay folded; he straightens off the table and turns to the window")
    assert "straightens off the table" in said
