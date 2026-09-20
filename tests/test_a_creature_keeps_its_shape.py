"""A non-human cast member's SHAPE reaches the prompt.

`visual_description` keeps a sentence only when it carries an appearance word,
and the whole vocabulary was faces and clothes.  The Martian's two load-bearing
sentences -- the body plan and the tentacles -- carried none, so they were
dropped silently from every take prompt of the episode built on them, and the
prompt described skin, a face and an ear disc with no shape at all.
"""
from studio.trailer_refs import contract_description, is_photographable

MARTIAN = (
    "A rounded grey-brown bulk the size of a bear and four feet across, whose whole body is one "
    "huge head. "
    "Oily grey-brown skin, fungoid, glistening like wet leather and pulsing with laboured breath. "
    "Sixteen slender grey whiplike tentacles as thick as a walking stick, hanging in two drooping "
    "bunches of eight on either side of the mouth and taking the bulk's weight on the ground."
)


def test_the_body_plan_and_the_tentacles_survive():
    kept = contract_description(MARTIAN)
    assert "four feet across" in kept
    assert "Sixteen slender grey whiplike tentacles" in kept


def test_the_creature_nouns_are_appearance_words():
    assert is_photographable("A rounded bulk the size of a bear and four feet across")
    assert is_photographable("Sixteen whiplike tentacles in two bunches of eight")
    assert is_photographable("A grey-brown hide glistening like wet leather")


def test_narration_is_still_refused():
    assert not is_photographable("He walked to the window and looked out")
    assert not is_photographable("The dossier gives no physical description")
