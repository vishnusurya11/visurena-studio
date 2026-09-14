"""The man the words mean is the man in the frame.

OWNER 2026-09-13, watching episode 3: "sherlock was pointing ... when they
entered, white dude was saying something, it should have been lestrade not
sherlock."  He was right, and no gate in the repo could see it.

WHAT THE PLAN ACTUALLY SAID, verbatim:

    line 11  (Watson VO)  "A tall white-faced man met us and said nothing had
                           been touched."
    shot 11               frame: "a tall white-faced man in a dark coat"
                          faces: []                      <-- nobody is cast
    line 12  (Watson VO)  "Except that, HE said, pointing back at the trampled
                           path behind us."
    shot 12               motion: "HOLMES raises one hand and points back out
                           through the open door as he speaks the line."
                          faces: ['sherlock_holmes']     <-- a different man

`tobias_gregson` is in the hall's own cast list the whole time.  The plan
described him instead of casting him, and an actor who is only described cannot
be checked against anything -- so the pronoun in the next line was free to land
on whoever the picture happened to show.

TWO RULES, because there are two separate failures and either one alone would
have caught this:

  A1 AN ACTOR IS CAST, NOT DESCRIBED.  A shot whose `motion` gives an action to
     an indefinite person ("the tall man turns") while `faces` is empty.  A
     corpse is not an actor, so the test is the ACTION, not the mention -- that
     is what keeps shot 13's "a well-dressed man lying on his face" clean.

  A2 A PRONOUN KEEPS ITS MAN.  A narration line whose subject is a bare pronoun
     carrying a speech or gesture verb continues the previous line's subject, so
     the shot under it may not change actor.

Free and model-free: these read the plan's own strings.
"""
import pytest

from studio import actor_gate as ag

# ---- episode 3's real rows, verbatim ---------------------------------------

SHOT11 = {"index": 11, "setup": "hall", "faces": [], "size": "medium",
          "frame": "Medium up the bare hall from the open front door: a tall white-faced man in a "
                   "dark coat standing at the far end with a notebook open in his hand, his back "
                   "three-quarters to the camera.",
          "motion": "The tall man turns a quarter toward the open door and the camera pushes a "
                    "hand's breadth up the hall; his notebook comes down to his side."}
SHOT12 = {"index": 12, "setup": "hall", "faces": ["sherlock_holmes"], "size": "medium_close",
          "frame": "Medium close on Holmes inside the hall with the open front door at the LEFT edge.",
          "motion": "Holmes raises one hand and points back out through the open door as he speaks "
                    "the line and the camera pushes in a hand's breadth."}
SHOT13 = {"index": 13, "setup": "front_room", "faces": [], "size": "wide",
          "frame": "Wide of the bare front room from the doorway: a well-dressed man lying on his face.",
          "motion": "The flat window light shifts a little across the boards and the camera pushes in."}
FIXED11 = dict(SHOT11, faces=["tobias_gregson"])
FIXED12 = dict(SHOT12, faces=["tobias_gregson"],
               motion="Gregson raises one hand and points back out through the open door as he "
                      "speaks the line and the camera pushes in a hand's breadth.")

LINE11 = {"index": 11, "kind": "narration", "shot": 11,
          "text": "A tall white-faced man met us and said nothing had been touched."}
LINE12 = {"index": 12, "kind": "narration", "shot": 12,
          "text": "Except that, he said, pointing back at the trampled path behind us."}
CAST = {"hall": ["john_watson", "sherlock_holmes", "tobias_gregson"], "front_room": []}


def ids(faults):
    return {f.split()[0] for f in faults}


# ---- A1  an actor is cast, not described -----------------------------------

def test_a1_catches_the_uncast_man_who_acts():
    assert "A1" in ids(ag.check([SHOT11], [], CAST))


def test_a1_names_the_shot_and_the_cast_it_could_have_used():
    fault = ag.check([SHOT11], [], CAST)[0]
    assert "shot 11" in fault and "tobias_gregson" in fault


def test_a1_leaves_a_body_alone_because_a_corpse_takes_no_action():
    """The mention is not the test; the ACTION is. Shot 13's man is described in
    the framing and does nothing in the motion, so he needs no casting."""
    assert "A1" not in ids(ag.check([SHOT13], [], CAST))


def test_a1_is_silent_once_the_man_is_cast():
    assert ag.check([FIXED11], [], CAST) == []


def test_a1_says_nothing_when_the_setup_has_no_cast_to_choose_from():
    """A gate that fires where no fix exists is noise."""
    assert ag.check([dict(SHOT11, setup="front_room")], [], CAST) == []


def test_a1_ignores_a_shot_whose_motion_moves_only_the_camera_and_the_light():
    seg = {"index": 9, "setup": "hall", "faces": [], "size": "insert",
           "frame": "Insert on the clay path.",
           "motion": "The fog thickens across the pane and the camera pushes in a hand's breadth."}
    assert ag.check([seg], [], CAST) == []


# ---- A2  a pronoun keeps its man -------------------------------------------

def test_a2_catches_the_actor_changing_under_a_continuing_pronoun():
    """Once shot 11 casts its man, the change to Holmes in shot 12 is visible.

    NOTE the gate reports an AMBIGUITY, not a verdict: for this very pair the
    source (ch3 P34) makes HOLMES right and the picture innocent, and the fix
    was to name Holmes in the line. See `a2_pronoun_keeps_its_man`."""
    assert "A2" in ids(ag.check([FIXED11, SHOT12], [LINE11, LINE12], CAST))


def test_a2_names_the_line_and_offers_BOTH_remedies():
    fault = next(f for f in ag.check([FIXED11, SHOT12], [LINE11, LINE12], CAST) if f.startswith("A2"))
    assert "he said" in fault and "shot 12" in fault and "CHECK THE SOURCE" in fault


def test_a2_stays_quiet_when_the_cut_goes_to_an_insert_on_a_thing():
    """MEASURED on episode 3: "then he threw me a note" cuts to an insert of the
    note. A thing contradicts no pronoun, and firing there would have made the
    gate noise on 2 of its 3 real hits. A1 is what keeps a shot with an ACTOR in
    it from being faceless, so nothing is missed by staying quiet here."""
    insert = {"index": 2, "setup": "hall", "faces": [], "size": "insert",
              "frame": "Insert square on the blue-grey note held open in two bare sunburnt hands.",
              "motion": "The sheet turns a few degrees flat toward the camera as the hands bring it up."}
    lines = [{"index": 1, "kind": "narration", "shot": 11, "text": "A blue anchor, he said."},
             {"index": 2, "kind": "narration", "shot": 2,
              "text": "Then he threw me a note, and said he had been wrong about crime."}]
    assert "A2" not in ids(ag.check([FIXED11, insert], lines, CAST))


def test_a2_is_satisfied_when_both_shots_show_the_same_man():
    assert "A2" not in ids(ag.check([FIXED11, FIXED12], [LINE11, LINE12], CAST))


def test_a2_ignores_a_line_that_names_its_own_subject():
    """"Holmes said" carries its antecedent with it and binds nothing backwards."""
    named = {"index": 12, "kind": "narration", "shot": 12,
             "text": "Holmes said it, pointing back at the trampled path behind us."}
    assert "A2" not in ids(ag.check([SHOT11, SHOT12], [LINE11, named], CAST))


def test_a2_ignores_a_pronoun_with_no_speech_or_gesture_verb():
    """"He walked the pavement" attributes no utterance; the cut is free to move."""
    quiet = {"index": 12, "kind": "narration", "shot": 12,
             "text": "He walked the pavement and stared at the mud."}
    assert "A2" not in ids(ag.check([SHOT11, SHOT12], [LINE11, quiet], CAST))


def test_a2_needs_the_two_lines_to_be_consecutive():
    far = dict(LINE12, index=15)
    assert "A2" not in ids(ag.check([SHOT11, SHOT12], [LINE11, far], CAST))


def test_a2_says_nothing_about_dialogue_which_already_carries_a_speaker():
    spoken = {"index": 12, "kind": "dialogue", "shot": 12, "speaker": "sherlock_holmes",
              "text": "He said so, pointing back at the path."}
    assert "A2" not in ids(ag.check([SHOT11, SHOT12], [LINE11, spoken], CAST))


# ---- the fix clears the whole gate -----------------------------------------

def test_the_corrected_plan_passes_both_rules():
    assert ag.check([FIXED11, FIXED12], [LINE11, LINE12], CAST) == []


# ---- A3  a close-up carries no background person ---------------------------

def test_a3_catches_a_background_person_written_into_a_close_ups_own_prose():
    """The setup-level crowd block is not the only way people get into a tight
    frame. Episode 3's shot 10 says it in the panel's OWN at_rest: "the constable
    stands small and BLURRED at the LEFT" -- the author wrote the defect in.
    Taking `BACKGROUND LIFE` off the prompt left that sentence untouched, and the
    redrawn panel came back with the constable still there."""
    seg = {"index": 10, "setup": "garden_path", "faces": ["john_watson"], "size": "medium_close",
           "frame": "Medium close on Watson halted on the clay path.",
           "motion": "Watson halts on the path and the camera pushes in a hand's breadth.",
           "at_rest": "Watson stands halted on the narrow clay path, the brick front of Number 3 "
                      "rising behind him, the constable stands small and blurred at the LEFT"}
    assert "A3" in ids(ag.check([seg], [], CAST))


def test_a3_leaves_the_same_sentence_alone_in_a_wide():
    seg = {"index": 7, "setup": "garden_path", "faces": [], "size": "wide",
           "frame": "Wide from the street side of Number 3.", "motion": "The fog thickens.",
           "at_rest": "The constable stands small and blurred at the LEFT of the rails"}
    assert "A3" not in ids(ag.check([seg], [], CAST))


def test_a3_leaves_the_subject_of_a_close_up_alone():
    """"the dead man's face" IS the picture, not somebody loitering in it."""
    seg = {"index": 14, "setup": "front_room", "faces": [], "size": "close",
           "frame": "Close on the dead man's face turned up from the boards.",
           "motion": "The flat window light shifts a little across the still face.",
           "at_rest": "The dead man's face is turned up from the boards, well fed and clean shaven"}
    assert "A3" not in ids(ag.check([seg], [], CAST))
