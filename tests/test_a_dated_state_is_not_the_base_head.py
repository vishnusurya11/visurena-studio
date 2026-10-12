"""A sentence the dossier dates to a later chapter is a STATE, never the base head.

Jekyll's Lanyon (2026-10-12): the profile writer put "By chapter 6, he is
visibly deteriorated: pale, with fallen flesh, noticeably balder and older" in
`profile.physical`, so the look table read "noticeably balder" as his BASE hair
and the ch2 man with "a shock of hair prematurely white" was drawn bald.  The
dated change already lives in `physical_evolution` and the ledger; when an
authored head lands, the dated sentence leaves the body.
"""
from __future__ import annotations

from studio import head_author

BODY = ("Initially described as a rosy man. By chapter 6, he is visibly deteriorated: pale, "
        "with fallen flesh, noticeably balder and older. He later takes to his bed and dies.")
WORDS = "A red-faced gentleman. A shock of prematurely white hair; white side-whiskers; a grey silk top hat."


def test_a_dated_sentence_leaves_the_body_when_a_head_lands():
    out = head_author.with_head(BODY, WORDS, "")
    assert "balder" not in out and "By chapter 6" not in out
    assert out.startswith("Initially described as a rosy man.") and out.endswith(WORDS)


def test_every_dated_form_is_a_state():
    for said in ("In chapter 8 his hair is grey.", "From chapter 3 on he wears a beard.",
                 "After chapter 9 he is bald."):
        assert head_author.dated(said), said
    assert not head_author.dated("A man of fifty with grey hair.")


def test_a_story_state_leaves_the_body_too():
    """Jekyll's body read 'During the story he becomes pale, black-eyed, deathly
    sick' and 'as Hyde, his limbs are shrunken': his base sheet would draw both."""
    for said in ("During the story he becomes pale, black-eyed and deathly sick.",
                 "His transformations alter his stature, face, limbs and hands.",
                 "In the transformed state, Jekyll observes shrunken limbs.",
                 "His rooms are later found hurriedly ransacked.",
                 "During that action he carries a heavy kitchen poker."):
        assert head_author.dated(said), said
    assert not head_author.dated("Initially described as a rosy man.")


def test_a_silence_about_dress_leaves_the_body_when_a_head_lands():
    body = "A rosy man. No clothing, height, build, or other distinguishing features are specified."
    assert head_author.with_head(body, WORDS, "") == f"A rosy man. {WORDS}"
