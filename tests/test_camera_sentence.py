"""The camera sentence names the CAMERA's move, and says each clause once.

Episode 2 shipped 42 of 42 camera sentences defective and nobody noticed until
the owner read one:

    "The camera the commissionaire's broad reddened right hand comes up flat to
     his brow in a salute as he speaks the line, and the camera pushes in a
     hand's breadth as the salute arrives..., from 00:00 to 00:04."

`camera_verb` assumed the motion's head clause BEGINS with a bare camera verb.
The plan is authored for a storyboard artist, so 41 of 42 motions are
subject-first with the camera in a trailing "as/while the camera ..." subclause
-- and the one that IS camera-first writes "The camera pushes in ...", with the
article, which mangled just as badly into "The camera the camera pushes in".

So the builder finds the camera clause wherever it sits.  32 blocks also
printed the head verbatim twice, because `action` fell back to the head that
`move` had already consumed -- and the duplicate made the block LONGER, so the
L14 length gate scored it as healthier.
"""
import pytest

from studio.episode_ref_official import camera_clause, camera_sentence

SUBJECT_FIRST_AS = ("Holmes's eyes come up off the roadway as the camera pushes in a hand's breadth")
SUBJECT_FIRST_WHILE = ("The bow draws two inches along the strings while the camera pushes in a foot")
CAMERA_FIRST_ARTICLE = "The camera pushes in a hand's breadth over the wicker arm"
CAMERA_FIRST_BARE = "pushes in a hand's breadth over the wicker arm"
NO_CAMERA = "Holmes's chest rises once under the brown rug"


@pytest.mark.parametrize("head, move, subject", [
    (SUBJECT_FIRST_AS, "pushes in a hand's breadth", "Holmes's eyes come up off the roadway"),
    (SUBJECT_FIRST_WHILE, "pushes in a foot", "The bow draws two inches along the strings"),
    (CAMERA_FIRST_ARTICLE, "pushes in a hand's breadth over the wicker arm", ""),
    (CAMERA_FIRST_BARE, "pushes in a hand's breadth over the wicker arm", ""),
    (NO_CAMERA, "", "Holmes's chest rises once under the brown rug"),
])
def test_the_camera_clause_is_found_wherever_it_sits(head, move, subject):
    assert camera_clause(head) == (move, subject)


def test_the_owners_own_example_is_no_longer_mangled():
    head = ("The commissionaire's broad reddened right hand comes up flat to his brow in a salute "
            "as he speaks the line, and the camera pushes in a hand's breadth")
    said = camera_sentence(f"{head}; the salute arrives flat at his brow", 0, 8)
    # the distance is the plan's, not the model's (audit 2026-09-22, item 22)
    assert said.startswith("The camera pushes in as the commissionaire's")
    assert "The camera the commissionaire" not in said


def test_no_clause_is_printed_twice():
    """32 of 42 blocks contained the plan's whole motion clause twice."""
    said = camera_sentence(SUBJECT_FIRST_AS, 0, 8)
    assert said.count("Holmes's eyes come up off the roadway") == 1
    assert said.lower().count("the camera") == 1


def test_a_head_with_no_tail_clause_still_says_each_thing_once():
    said = camera_sentence(NO_CAMERA, 0, 8)
    assert said.count("Holmes's chest rises once under the brown rug") == 1


def test_a_camera_that_moves_is_never_called_static():
    """T00 and T19 said 'holds a static shot' in a sentence that also said the
    camera rises one tread; 'rise' was simply absent from MOVES."""
    said = camera_sentence("The hand slides up the rail as the camera rises one tread", 0, 8)
    assert "static" not in said
    assert said.startswith("The camera rises as")     # the move, without its distance


def test_a_genuinely_locked_camera_is_still_called_static():
    said = camera_sentence(NO_CAMERA, 0, 8)
    assert "holds a static shot" in said


def test_the_sentence_keeps_its_range():
    said = camera_sentence(SUBJECT_FIRST_AS, 0, 8)
    assert said.rstrip().endswith(".")
    assert "00:0" in said
