"""A stride you measure a camera in is not a gait anybody walks at.

`GAIT` feeds L8 (a walk needs a named pace) and L9 (Watson walks with a limp).
Its own docstring says: "The nouns `step`, `stride` and `pace` are out ... the
camera's own position says `one step farther along the counter`, `a stride
behind the two men`, `at walking height`".

It implements that for the SINGULAR and not for the plural.  `strides` is in the
verb alternation, so the repo's most common camera idiom trips it:

    "level with Holmes's chest and two long STRIDES from him"

MEASURED 2026-09-13: that one phrase refused episode 4's take 15 -- a man
standing still in a parlour, talking -- for "a walk, climb or ride with no pace
named".  Nobody walks in the shot.

The distinction is grammatical and cheap: a gait verb is not followed by `from`,
`behind`, `of` or `away from`.  "He strides across the room" still reads as a
gait; "two long strides from him" and "a stride behind the two men" are
distances, which is what the docstring always said.
"""
from studio.episode_ref_official import GAIT, l8_pace, l9_limp


def block(body: str, head: str = "[Shot 1] From 00:00 to 00:04.") -> str:
    return f"detailed_description:\n{head} {body}"


# ---- the camera's distance is not a gait -----------------------------------

def test_two_long_strides_from_him_is_a_distance():
    said = "The camera is level with Holmes's chest and two long strides from him."
    assert l8_pace(block(said), {}) == []


def test_a_stride_behind_the_two_men_is_a_distance():
    """Quoted from GAIT's own docstring as a case that should already be out."""
    assert l8_pace(block("The camera is a stride behind the two men."), {}) == []


def test_one_step_farther_along_the_counter_is_a_distance():
    assert l8_pace(block("The camera is one step farther along the counter."), {}) == []


def test_a_long_stride_from_the_gate_is_a_distance():
    assert l8_pace(block("The camera stands a long stride from the gate."), {}) == []


# ---- a gait verb is still a gait -------------------------------------------

def test_a_man_who_strides_across_the_room_still_needs_a_pace():
    assert l8_pace(block("Holmes strides across the room to the window."), {})


def test_a_walk_still_needs_a_pace():
    assert l8_pace(block("Watson walks along the railings."), {})


def test_a_walk_with_its_pace_named_passes():
    said = "The camera tracks beside them at a walking pace as Watson walks along the railings."
    assert l8_pace(block(said), {}) == []


def test_watsons_limp_is_still_demanded_when_he_walks():
    said = "<Subject 1> walks the length of the platform at a walking pace."
    assert l9_limp(block(said), {"watson": "<Subject 1>"})


def test_watson_measured_in_strides_is_not_walking():
    """The same false positive, one rule over: L9 refused a take because the
    CAMERA stood two strides from a seated man."""
    said = "The camera is level with <Subject 1>'s eyes and two long strides from him."
    assert l9_limp(block(said), {"watson": "<Subject 1>"}) == []


# ---- the same distance, more prepositions -----------------------------------

def test_two_strides_inside_the_room_is_a_distance():
    """Episode 5's camera stands "two strides inside the room", which the first
    version of this fix did not cover: it listed `from`, `behind`, `of` and
    `away` and a camera's distance takes any preposition of place."""
    said = "The camera is on the carpet two strides inside the room, level with her eyes."
    assert l8_pace(block(said), {}) == []


def test_a_stride_into_the_doorway_is_a_distance():
    assert l8_pace(block("The camera stands a stride into the doorway."), {}) == []


def test_two_strides_along_the_pavement_is_a_distance():
    assert l8_pace(block("The camera is two strides along the pavement from the gate."), {}) == []


def test_a_stride_short_of_the_table_is_a_distance():
    assert l8_pace(block("The camera stands a stride short of the table."), {}) == []


def test_a_man_who_strides_into_the_room_is_still_a_gait():
    """The exemption is for a MEASURED distance -- a number or an article and a
    noun of length -- not for the preposition alone."""
    assert l8_pace(block("Holmes strides into the room and turns."), {})
