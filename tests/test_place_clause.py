"""The place said inside a block ends on a whole clause, never mid-phrase
(WotW ep1 iter3: "...and it comes from the." in every take)."""
from studio import episode_ref_official as ro

ROOM = ("The front of the villa at night: a black door under a small porch, a fanlight glowing, "
        "clipped laurels; the fanlight is the only light and it comes from the door behind the couple")


def test_a_description_under_the_cap_is_said_whole():
    assert ro.place_clause(ROOM, 200) == f"The shot is inside this place: {ROOM}."


def test_a_cut_description_ends_at_its_last_whole_clause():
    got = ro.place_clause(ROOM, 24)
    assert got == ("The shot is inside this place: The front of the villa at night: a black door "
                   "under a small porch, a fanlight glowing, clipped laurels.")


def test_a_cut_with_no_clause_break_keeps_the_words():
    assert ro.place_clause("one two three four five", 3) == "The shot is inside this place: one two three."


def test_nothing_described_says_nothing():
    assert ro.place_clause("", 10) == ""
