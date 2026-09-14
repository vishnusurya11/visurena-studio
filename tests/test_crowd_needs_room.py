"""Background life goes only in a panel wide enough to hold a place.

OWNER 2026-09-13, watching episode 3: "does any of them shot where watson was
talking there is a blur human on the side??"  There is -- shot 10, a
MEDIUM_CLOSE on Watson's face, with a constable in a tall helmet and four men in
caps sitting out of focus against the left edge.

The crowd itself is right.  `garden_path.crowd` reads "one stalwart police
constable in a tall helmet leaning against the brick wall, and five or six
loafers in caps craning over the rails behind him", which is Conan Doyle's own
description of Lauriston Gardens, and it belongs in the wides.

What was wrong is WHERE it was drawn.  `crowd_clause` excluded exactly one size,
`insert`, so every other size got the full crowd -- including a medium close on
one man's head.  At that size the people cannot be people; they are smears at
the frame edge.

THE LADDER ALREADY EXISTS.  `WIDE_ENOUGH = {medium, full, wide}` is used by
`places_the_plate` for the identical reason, stated there: "below it you are
looking at a person, not at a place."  A crowd is part of the place.  So this
is not a new rule -- it is the existing rule applied to the other thing that
only a place can hold.
"""
from studio.episode_seq_board import WIDE_ENOUGH, crowd_clause
from studio.episode_spec import Setup

GARDEN = Setup(
    name="garden_path", described="The front garden of Number 3 Lauriston Gardens.",
    cast=["john_watson", "sherlock_holmes"], props=[], state="day",
    crowd="one stalwart police constable in a tall helmet leaning against the brick wall, and "
          "five or six loafers in caps craning over the rails behind him")
BARE = Setup(name="hall", described="The bare front hall.", cast=[], props=[], state="day")


def seg(size: str, crowd: str = "") -> dict:
    return {"size": size, "crowd": crowd}


def test_the_wide_that_establishes_the_street_keeps_its_crowd():
    assert "constable" in crowd_clause(seg("wide"), GARDEN)


def test_a_medium_still_shows_enough_room_for_people():
    assert "constable" in crowd_clause(seg("medium"), GARDEN)


def test_the_medium_close_on_watson_is_left_alone():
    """The exact panel the owner caught: shot 10, `medium_close`."""
    assert crowd_clause(seg("medium_close"), GARDEN) == ""


def test_a_close_is_left_alone():
    assert crowd_clause(seg("close"), GARDEN) == ""


def test_an_insert_is_still_left_alone():
    """The one size the rule already excluded; it stays excluded."""
    assert crowd_clause(seg("insert"), GARDEN) == ""


def test_every_size_that_keeps_a_crowd_is_exactly_the_plate_ladder():
    """One ladder, not two. If `WIDE_ENOUGH` ever changes, this moves with it."""
    kept = {s for s in ("wide", "full", "medium", "medium_close", "close", "insert")
            if crowd_clause(seg(s), GARDEN)}
    assert kept == WIDE_ENOUGH


def test_a_setup_with_no_crowd_says_nothing_at_any_size():
    assert all(crowd_clause(seg(s), BARE) == "" for s in ("wide", "medium", "close"))


def test_a_panels_own_crowd_still_overrides_the_setups_when_there_is_room():
    said = crowd_clause(seg("wide", "two clerks in dark coats walk the other way"), GARDEN)
    assert "clerks" in said and "constable" not in said


def test_a_panels_own_crowd_still_needs_the_room():
    """A per-panel crowd is not a licence to put people in a close-up."""
    assert crowd_clause(seg("close", "two clerks in dark coats walk the other way"), GARDEN) == ""


# ---- the same law when ONE panel is redrawn alone ---------------------------

def test_a_single_panel_redraw_keeps_the_crowd_out_of_a_close_up():
    """`redraw_panel.py` builds its prompt with `single()`, not with the sheet's,
    so the rule has to hold in both places or a $0.08 repair puts the crowd
    straight back into the panel it was just taken out of."""
    from studio.episode_seq_board import single
    said = single({"size": "medium_close", "frame": "Medium close on Watson.", "camera": "",
                   "at_rest": "", "crowd": ""}, GARDEN, {})
    assert "people fill it" not in said and "constable" not in said


def test_a_single_panel_redraw_of_a_wide_still_carries_the_crowd():
    from studio.episode_seq_board import single
    said = single({"size": "wide", "frame": "Wide of the garden path.", "camera": "",
                   "at_rest": "", "crowd": ""}, GARDEN, {})
    assert "people fill it" in said
