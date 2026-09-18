"""A second book brings people whose ids are not names, and women who speak.

The War of the Worlds' narrator is `unnamed_first_person_narrator` and his wife
is `narrators_wife`: title-casing the id wrote "<Subject 1> is Unnamed First
Person Narrator", and the builder called every subject "this man" and gave
every speaker "His mouth".  A book declares a display name and a gender per
character (refs.json `display`, `gender`); a book that declares neither is
built exactly as before.
"""
import pytest

from studio import episode_ref_official as ro


@pytest.fixture(autouse=True)
def wotw_names():
    ro.DISPLAY.clear()
    ro.WOMEN.clear()
    ro.DISPLAY.update({"unnamed_first_person_narrator": "the Narrator", "narrators_wife": "the Wife"})
    ro.WOMEN.add("narrators_wife")
    yield
    ro.DISPLAY.clear()
    ro.WOMEN.clear()


def test_a_declared_display_name_is_the_name():
    assert ro.name_of("unnamed_first_person_narrator") == "the Narrator"


def test_the_surname_of_a_display_name_is_its_last_word():
    assert ro.surname("narrators_wife") == "Wife"


def test_an_undeclared_id_keeps_the_old_title_case():
    assert ro.name_of("john_watson") == "John Watson"
    assert ro.surname("john_watson") == "Watson"


def test_the_frame_text_finds_a_display_named_person():
    text = "Medium of the Narrator at the eyepiece with Ogilvy behind him."
    assert ro.people_in(text, ["ogilvy", "unnamed_first_person_narrator"]) == \
        ["ogilvy", "unnamed_first_person_narrator"]


def test_a_woman_is_defined_as_a_woman():
    text, _, _ = ro.subjects(["narrators_wife"], {"narrators_wife": "Woman of 29."}, "a porch",
                             [{"frame": "Medium close of the Wife."}], has_plate=False, has_cells=False)
    assert "defines this woman alone" in text


def test_a_woman_keeps_her_own_mouth():
    assert ro.possessive("narrators_wife") == "Her"
    assert ro.possessive("ogilvy") == "His"


def test_retention_calls_a_woman_a_woman():
    text = ro.retention(["narrators_wife"], [{"frame": "Medium close of the Wife."}], {0: None}, 0, [],
                        "a porch", has_plate=False, has_cells=False)
    assert "(the woman in" in text and "shows her;" in text and "definition of the woman" in text
