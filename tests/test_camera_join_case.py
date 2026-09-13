"""The half after `as` is a subordinate clause, so it does not start with a capital.

MEASURED on episode 2: 21 of the 19 rebuilt take prompts carry a mid-sentence
capital -- "The camera pushes in a hand's breadth as The right forefinger with
the white plaster on it lifts...".  `camera_sentence` joins the camera half to
the motion half, and the motion half arrives from the plan as its own sentence,
capital and all.  A capital mid-sentence reads to the model as a new sentence,
which is the same class of fault as the malformed camera clause that had to be
fixed before this render: the prompt says two things where it means one.

A proper noun keeps its capital, because lowercasing `Watson` would be worse
than the fault being fixed.
"""
from studio.episode_ref_official import camera_sentence, lower_lead


def test_a_leading_article_is_lowercased():
    assert lower_lead("The right forefinger lifts") == "the right forefinger lifts"
    assert lower_lead("A hand closes") == "a hand closes"
    assert lower_lead("His chin comes down") == "his chin comes down"


def test_a_proper_noun_keeps_its_capital():
    assert lower_lead("Watson's hand turns") == "Watson's hand turns"
    assert lower_lead("Holmes leans in") == "Holmes leans in"
    assert lower_lead("Mrs Hudson sets it down") == "Mrs Hudson sets it down"


def test_a_subject_tag_is_left_alone():
    assert lower_lead("<Subject 2>'s mouth lifts") == "<Subject 2>'s mouth lifts"


def test_an_empty_clause_survives():
    assert lower_lead("") == ""


MOTION = ("The right forefinger with the white plaster on it lifts a finger's width off the "
          "cushion and settles back while the camera pushes in a hand's breadth.")
"""Episode 2, shot 3 cut 1, verbatim: `<action> while the camera <move>.`"""


def test_the_camera_sentence_joins_in_lower_case():
    said = camera_sentence(MOTION, 0, 4)
    assert "as the right forefinger" in said
    assert "as The" not in said


def test_the_camera_sentence_still_capitalises_its_own_head():
    assert camera_sentence(MOTION, 0, 4).startswith("The camera pushes in")
