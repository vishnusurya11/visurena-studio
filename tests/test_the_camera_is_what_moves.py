r"""The head clause of a motion names a camera move, or the take freezes.

MEASURED 2026-09-14 over the 92 judged takes of episodes 2 to 5, using the
builder's own `camera_clause(clauses_of(motion)[0])`:

    episode   shots   head names a camera move   stillness points lost
    ep02      25      25 (100 %)                  12.2 over 19 takes
    ep03      25      25 (100 %)                  10.8 over 24 takes
    ep04      24      12  (50 %)                  59.1
    ep05      25       7  (28 %)                 106.8

Episodes 2 and 3 scored badly -- means of 59.6 and 76.6 -- but lost it to
landing, drift, foreign frames and lip-sync. Their stillness loss is ~zero. The
moment the plan-writing convention stopped naming a camera move, ALL the loss
moved to stillness. Mean frozen penalty per take, pooled:

    head names a camera move : 0.20 (n=27, >=3 clauses) / 0.50 (n=35, <3)
    head names none          : 4.22 (n=14)             / 6.68 (n=16)

A 13-21x effect against ~1.6x for clause count. Fisher one-sided on "penalised
at all": 4/62 vs 9/30, p = 0.0041. All ten of the stillest takes in ep04+ep05
are in the no-camera set; not one of the nineteen camera-move takes was ever
penalised.

WHY THE CAMERA AND NOT THE SUBJECT. The camera move is the only element of the
prompt that is not a property of the reference picture. Everything else H3 reads
-- the pose, the wardrobe, the room -- it can satisfy by rendering the pinned
cell and holding. A move is the one instruction it cannot satisfy by standing
still, which is why it is the one that grips from frame zero.

THIS IS ALSO THE OWNER'S NOTE, from the other side. 2026-09-14: "remove
unnatural movement like paper turning on its own on table ... and violin getting
a red light ... keep the movement simple". Those shots are un-caused BECAUSE
their heads named no camera move: with nothing else moving, the motion got
handed to the props. One rule answers both -- the camera moves, and the objects
behave. See [[test_a_thing_moves_because_something_moves_it]].

A QUERY, NOT A VALIDATOR. `long_shots` records what happens when a rule like
this is made a `model_validator`: it refused episode 1's already-published plan
and broke every tool that merely READS a plan. Episodes 4 and 5 are published
with 30 shots that fail this; reading them is not endorsing them. The refusal
belongs at the step that is about to SPEND -- `seq_boards`, which draws the
sheets, and `takes_r2v`, which renders.
"""
import pytest

from studio.episode_spec import motion_faults


def faults(motion: str) -> list[str]:
    return [code for code, _ in motion_faults(motion)]


GOOD = ("The camera pushes in on the sofa across the whole shot, travelling two long "
        "strides; his hand comes down off his chin; his shoulders come down.")


def test_a_well_formed_motion_has_no_faults():
    assert motion_faults(GOOD) == []


# ---- M2, the one that matters ----------------------------------------------

def test_a_head_with_no_camera_move_is_refused():
    said = ("The folded paper slides across the white cloth; his eyes go to it; "
            "his chin lifts.")
    assert "M2" in faults(said)


def test_a_camera_move_in_the_head_satisfies_it():
    assert "M2" not in faults(GOOD)


def test_the_subject_may_come_first_if_the_camera_is_still_in_the_head():
    """41 of episode 2's 42 motions are this shape and all 25 heads passed."""
    said = ("his hand comes up to the pipe as the camera pushes in a hand's breadth "
            "across the whole shot; his chin lifts; his shoulders come down.")
    assert "M2" not in faults(said)


def test_a_camera_move_after_the_first_semicolon_does_not_count():
    """ep04 T21 wrote it in clause position and the builder DELETED it -- the
    move never reached the model. Position, not presence."""
    said = ("Rance stands in the doorway; the camera pushes in on Rance across the "
            "whole shot, travelling two long strides; his chin lifts.")
    assert "M2" in faults(said)


def test_a_head_that_only_says_static_is_refused():
    said = "Static shot; he lifts the glass; his shoulders come down."
    assert "M2" in faults(said)


def test_a_clause_that_merely_contains_the_word_camera_is_not_a_move():
    """ep04 T23: `lifts one finger between himself and the camera as he speaks
    the line` split at `and the camera` and shipped `The camera as he speaks the
    line as ...`. A non-empty camera clause is not yet a camera MOVE."""
    said = ("<Subject 1> lifts one finger between himself and the camera as he speaks "
            "the line; his chin lifts; his shoulders come down.")
    assert "M2" in faults(said)


# ---- M1, no timed beats at all ---------------------------------------------

def test_a_two_clause_motion_is_refused():
    """`beat_sentences` reads `parts[2:]`, so two clauses yield zero beats and no
    "continues to the last frame" sentence. Verified 49/49 on the shipped
    prompts: `parts >= 3` if and only if that sentence exists."""
    said = "The camera pushes in across the whole shot; his chin lifts."
    assert "M1" in faults(said)


def test_a_three_clause_motion_is_enough():
    assert "M1" not in faults(GOOD)


# ---- M4/M5, how the last clause ends ---------------------------------------

def test_a_terminal_last_clause_is_refused():
    """The builder then writes `and the drop continues to the last frame`, a
    sentence that contradicts itself; the model obeys the terminal half."""
    said = ("The camera pushes in across the whole shot; his arm comes out; the ring "
            "settles flat on the cloth.")
    assert "M5" in faults(said)


def test_coming_to_rest_is_terminal():
    said = ("The camera tracks left across the whole shot; his hand crosses; the paper "
            "comes to rest against the edge of a plate.")
    assert "M5" in faults(said)


def test_a_continuing_last_clause_passes():
    said = ("The camera pushes in across the whole shot; his arm comes out; his thumb "
            "runs along the barrel.")
    assert motion_faults(said) == []


def test_a_stillness_word_in_the_last_clause_is_refused():
    """`clauses_of` calls `calm()` first, which rewrites `stays -> is`, so the
    take lint can never see this. Judged on the RAW clause."""
    said = ("The camera pushes in across the whole shot; the fog travels across the "
            "lamplight; his muffled face stays turned down.")
    assert "M4" in faults(said)


def test_a_stillness_word_that_is_not_last_is_allowed():
    """11 of the 13 shipped motions with one scored 100. Only last is fatal."""
    said = ("The camera pushes in across the whole shot; his face stays turned down; "
            "his shoulders come down.")
    assert "M4" not in faults(said)


# ---- M6, the last clause has to be big enough to measure -------------------

def test_an_eye_movement_cannot_carry_the_tail():
    """`motion_gate` bins a 24x24 block of a 192x336 grey frame -- about a
    mouth's size at 768x1344. ep04 T11 put `his eyes go to the coin` last and
    the final 1.25 s is a still portrait."""
    said = ("The camera pushes in across the whole shot; his arm comes out; his eyes "
            "go to the coin in Holmes's hand.")
    assert "M6" in faults(said)


def test_a_limb_can_carry_the_tail():
    assert "M6" not in faults(GOOD)


def test_a_walking_stick_is_not_a_gait():
    """`motion_noun` matched `walk` inside `walking stick` and shipped `the walk
    limping continues ... at a normal walking pace` for a man sitting in a cab."""
    said = ("The camera pushes in across the whole shot; his arm comes out; his hand "
            "closes on the knob of the black walking stick.")
    assert "M6" not in faults(said)


# ---- the faults carry their own reason -------------------------------------

def test_each_fault_says_what_to_do():
    code, why = motion_faults("The paper slides across the cloth; his chin lifts.")[0]
    assert code and len(why) > 20


def test_an_empty_motion_is_not_judged():
    assert motion_faults("") == []
