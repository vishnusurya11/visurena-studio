"""A cast member called by a common noun binds only in a definite phrase.

MEASURED 2026-09-23 over the 99 rendered WotW take prompts (agent audit a2):
the display name's last word was matched bare, so
- ep06 T08 "an old man with a stick and a boy of sixteen" staged the
  13-year-old newspaper boy's sheet for a stranger ("a <Subject 1> of sixteen");
- ep09 T22 "dark rifle-green serge hussar jacket" became "serge <Subject 1> jacket".
"the dismounted hussar" must still bind: the plan names him that way.
"""
import pytest

from studio import episode_ref_official as ro


@pytest.fixture(autouse=True)
def names(monkeypatch):
    monkeypatch.setattr(ro, "DISPLAY", {"unnamed_hussar": "the hussar",
                                         "unnamed_newspaper_boy": "the newspaper boy",
                                         "ogilvy": "Ogilvy"})


def test_a_definite_phrase_binds_the_person():
    assert ro.tagged("Close on the dismounted hussar, shouting", ["unnamed_hussar"]) == \
        "Close on the dismounted <Subject 1>, shouting"


def test_the_noun_inside_a_description_does_not_bind():
    text = "dark rifle-green serge hussar jacket; the hussar turns"
    assert ro.tagged(text, ["unnamed_hussar"]) == "dark rifle-green serge hussar jacket; <Subject 1> turns"


def test_an_indefinite_stranger_is_nobody_in_the_cast():
    assert ro.people_in("an old man with a stick and a boy of sixteen", ["unnamed_newspaper_boy"]) == []
    assert ro.people_in("the newspaper boy cries the edition", ["unnamed_newspaper_boy"]) == \
        ["unnamed_newspaper_boy"]


def test_a_proper_name_still_binds_bare():
    assert ro.tagged("Ogilvy looks up", ["ogilvy"]) == "<Subject 1> looks up"
    assert ro.people_in("beside Ogilvy", ["ogilvy"]) == ["ogilvy"]


def test_a_possessive_names_what_is_owned_not_the_owner(monkeypatch):
    """ep09 T17 is the wife alone. "the narrator's wife" bound the narrator too,
    and his sheet was staged into her take (caught before any render)."""
    monkeypatch.setattr(ro, "DISPLAY", {"unnamed_first_person_narrator": "the Narrator",
                                         "narrators_wife": "the Wife"})
    cast = ["narrators_wife", "unnamed_first_person_narrator"]
    text = "a medium close shot on the narrator's wife standing on the drive"
    assert ro.people_in(text, cast) == ["narrators_wife"]
    assert ro.tagged(text, ["narrators_wife"]) == "a medium close shot on <Subject 1> standing on the drive"


def test_a_bare_article_goes_into_the_label():
    assert ro.tagged("a medium shot on the hussar", ["unnamed_hussar"]) == "a medium shot on <Subject 1>"
