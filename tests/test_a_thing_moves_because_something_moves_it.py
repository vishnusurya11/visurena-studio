"""An object indoors moves when something moves it, and not otherwise.

OWNER, 2026-09-14, watching episode 5: "remove unnatural movement like paper
turning on its own on table ... and violin getting a red light ... keep the
movement simple".

Both are real and both are in the shipped plan:

    shot  6  "The folded paper slides across the white cloth and comes to rest
              against the edge of a plate."          -- nothing pushes it
    shot 24  "The coal settles in the grate and a red light moves once across
              the strings of the violin."            -- nothing moves the light

The chapter has the cause for the first one sitting in it -- "He threw the paper
across to me" -- and it was dropped when the shot was written as an insert.

THE RULE IS NOT "no object motion".  Plenty of things move for good reasons and
those shots are fine:

    fog rolling across lamplight, a candle flame leaning, washing lifting in the
    draught down a court, a cab wheel turning, a roadway travelling past a
    window at the horse's trot

What they share is an agent IN THE FRAME OR IMPLIED BY THE PLACE: wind outdoors,
a draught, a flame's own convection, a horse pulling. What the two faults share
is an object at rest on an indoor surface, and light falling on a still object
indoors, with nothing to move either.

So: a clause whose subject is a movable THING must name its mover -- a person, a
hand, the camera, or one of the standing natural agents -- somewhere in the same
clause. This is checkable before a frame is rendered and costs nothing.

It also serves the second half of the owner's note. The takes that score 100 are
the ones where the CAMERA carries the shot and the objects behave; the ones that
needed re-rolls are the ones where I asked objects to perform.
"""
import pytest

from studio.episode_spec import uncaused_motion


def test_a_paper_that_slides_itself_is_refused():
    said = "The folded paper slides across the white cloth and comes to rest against a plate."
    assert uncaused_motion(said) == ["paper"]


def test_a_light_that_moves_itself_is_refused():
    said = "The coal settles in the grate and a red light moves once across the strings."
    assert uncaused_motion(said) == ["light"]


def test_a_hand_may_move_the_paper():
    said = "Holmes's hand pushes the folded paper across the white cloth to the edge of a plate."
    assert uncaused_motion(said) == []


def test_the_camera_may_move_over_anything():
    said = "The camera pushes in on the violin across the whole shot, travelling a forearm."
    assert uncaused_motion(said) == []


def test_fingers_may_turn_a_ring():
    said = "The ring turns over once between the finger and thumb and settles flat on the cloth."
    assert uncaused_motion(said) == []


# ---- the standing natural agents -------------------------------------------

def test_fog_moves_on_its_own():
    assert uncaused_motion("The fog rolls a hand's breadth across the pool of lamplight.") == []


def test_a_flame_moves_on_its_own():
    assert uncaused_motion("The candle flame behind the glass leans and steadies.") == []


def test_washing_moves_in_a_draught():
    said = "The lines of washing lift and fall together in the draught down the court."
    assert uncaused_motion(said) == []


def test_a_wheel_turns_because_the_cab_is_moving():
    said = "The tall wheel turns away over the wet cobbles at a trotting pace for the whole shot."
    assert uncaused_motion(said) == []


def test_a_coal_settles_because_it_is_burning():
    assert uncaused_motion("The coal settles once in the grate.") == []


# ---- not a motion at all ----------------------------------------------------

def test_catching_the_light_is_not_movement():
    assert uncaused_motion("the gold catches the firelight and holds.") == []


def test_an_empty_motion_is_clean():
    assert uncaused_motion("") == []
    assert uncaused_motion("Static.") == []


# ---- every clause is read ---------------------------------------------------

def test_each_clause_is_judged_on_its_own():
    said = ("The camera pushes in on the table across the whole shot; the folded paper slides "
            "across the cloth.")
    assert uncaused_motion(said) == ["paper"]


def test_two_faults_are_both_named():
    said = "The paper slides across the cloth; a red light moves across the strings."
    assert uncaused_motion(said) == ["paper", "light"]
