"""The voice register is read off the dossier, and it read a wife as a man.

MEASURED 2026-09-20, casting WotW ep06: `unnamed_neighbours_wife` was assigned
125 Hz and "male". The detector looks for " she ", " her ", "woman", "girl",
"daughter" in the dossier text, and for a short list of names -- and none of
them is the word WIFE. A character whose entity id says what she is came out a
baritone.

It is the same shape as every other fault this week: a list that was right for
the characters it was written against, used on a character it had never seen.
Scarlet's women were Lucy, Madame, Mrs, Miss and a servant, so those are the
words in it.
"""
import pytest

from scripts.cast.cast_voices import gender_of


def card(name: str, physical: str = "") -> dict:
    return {"name": name, "profile": {"physical": physical}}


def test_a_wife_is_a_woman():
    assert gender_of(card("the narrator's neighbour's wife")) == "female"


def test_the_words_scarlet_taught_it_still_work():
    assert gender_of(card("Mrs Hudson")) == "female"
    assert gender_of(card("Miss Elphinstone")) == "female"


def test_the_other_words_a_book_uses_for_a_woman():
    for said in ("his wife", "the widow", "her mother", "the sister",
                 "a lady of forty", "the landlady", "the barmaid", "the nurse",
                 "the governess", "the washerwoman", "the schoolmistress"):
        assert gender_of(card(said)) == "female", said


def test_a_man_is_still_a_man():
    for said in ("Stent", "Ogilvy the astronomer", "the carter", "the artilleryman"):
        assert gender_of(card(said)) == "male", said


def test_the_dossier_outranks_the_name():
    """A physical description that says 'she' decides it whatever the id says."""
    assert gender_of(card("snippy", "She is a tall woman of fifty.")) == "female"
