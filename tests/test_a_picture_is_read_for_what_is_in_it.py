"""CONTENT DQ: is what the picture SHOWS what the shot asked for?

Every gate this pipeline had measured a statistic -- edge strength, face
count, frozen share, mux lag, tiledness. Not one looked at what was in the
frame. So every content fault of the last two episodes passed DQ and was
caught by eye, or by the owner:

  a doll in a pink dress standing in the heather      (owner)
  a horse cropped to its head in ep05 T14             (owner)
  three young men drawn as the same man three times   (owner)
  hills on a Surrey horizon, where Surrey is flat     (by eye, by luck)
  a Sherlock Holmes title card on War of the Worlds   (by eye, by luck)

OWNER 2026-09-21: "you have to do a lot of dq on these prompts and videos".

The model is never asked whether the picture is right -- a VLM says yes. It is
asked to LIST what it sees in a closed vocabulary, and the judging is done
here, against the shot's own words. That rule is `studio/describe.py`'s and it
is the only reason a read like this can be trusted.
"""
from __future__ import annotations

import pytest

from studio.panel_content import (LANDFORMS, Seen, forbidden_landform, faults,
                                  people_fault, reads_as_night, unasked_subject)


def seen(**kw) -> Seen:
    base = dict(landform="flat", people=0, lookalikes=0, text=False,
                hour="night", subjects=[])
    base.update(kw)
    return Seen(**base)


# ---- the Surrey hills -----------------------------------------------------
def test_a_hill_on_a_flat_place_is_a_fault():
    assert forbidden_landform(seen(landform="hills"), flat=True)


def test_a_hill_where_the_book_has_hills_is_not():
    assert not forbidden_landform(seen(landform="hills"), flat=False)


@pytest.mark.parametrize("land", ["flat", "gentle rise"])
def test_flat_ground_passes_a_flat_place(land):
    assert not forbidden_landform(seen(landform=land), flat=True)


def test_every_landform_the_reader_may_say_is_known():
    assert "flat" in LANDFORMS and "hills" in LANDFORMS and "mountains" in LANDFORMS


# ---- the doll, and anything else nobody asked for -------------------------
def test_a_subject_the_shot_never_named_is_a_fault():
    got = unasked_subject(seen(subjects=["heather", "pine trees", "a child's doll"]),
                          "Wide of the black common at night, knee-deep heather among the pines")
    assert got == ["a child's doll"]


def test_a_subject_the_shot_named_is_not():
    assert unasked_subject(seen(subjects=["heather", "pine trees"]),
                           "black heather and bare pine trees") == []


# ---- the clones -----------------------------------------------------------
def test_people_who_look_alike_are_a_fault():
    assert people_fault(seen(people=3, lookalikes=2), planned=0, crowd=True)


def test_a_crowd_of_different_people_is_not():
    assert not people_fault(seen(people=8, lookalikes=0), planned=0, crowd=True)


def test_more_faces_than_the_shot_casts_is_a_fault():
    assert people_fault(seen(people=2, lookalikes=0), planned=1, crowd=False)


def test_the_cast_the_shot_asked_for_passes():
    assert not people_fault(seen(people=1, lookalikes=0), planned=1, crowd=False)


# ---- the hour, which the reference decides --------------------------------
def test_a_night_shot_that_reads_as_day_is_a_fault():
    assert not reads_as_night(seen(hour="day"))


def test_a_night_shot_that_reads_as_night_passes():
    assert reads_as_night(seen(hour="night"))


# ---- the whole verdict ----------------------------------------------------
def test_a_clean_panel_has_no_faults():
    assert faults(seen(subjects=["heather", "pine trees"]),
                  frame="black heather and bare pine trees at night",
                  planned=0, crowd=False, flat=True, night=True) == []


def test_every_fault_is_named_in_the_verdict():
    got = faults(seen(landform="mountains", people=2, lookalikes=2, text=True,
                      hour="day", subjects=["a doll"]),
                 frame="empty heather at night", planned=0, crowd=True,
                 flat=True, night=True, banned=("doll",))
    assert len(got) >= 4
    assert any("landform" in f for f in got)
    assert any("doll" in f for f in got)
    assert any("text" in f or "lettering" in f for f in got)
    assert any("night" in f or "hour" in f for f in got)


def test_burned_in_lettering_is_a_fault():
    assert any("text" in f or "lettering" in f
               for f in faults(seen(text=True), frame="heather", planned=0,
                               crowd=False, flat=True, night=True))


# ---- the reader's own answer, which arrives wrapped ------------------------
def test_the_answer_is_read_out_of_a_json_array_of_a_string():
    """What the caption workflow actually returns: a JSON array whose one
    element is a STRING of JSON.

    The first version regexed for a brace and handed json.loads a string full
    of escaped quotes. It raised, the reader returned its defaults, and every
    panel of ep07 came back 'flat, 0 people, night' -- a DQ that silently
    passes everything, which is worse than no DQ.

    The fixture is BUILT, never typed: writing the escapes by hand is how the
    first version of this test failed against correct code.
    """
    import json

    from studio.panel_content import parse
    inner = json.dumps({"landform": "flat", "people": 1, "lookalikes": 0,
                        "text": False, "hour": "night",
                        "subjects": ["man", "mustache"]}, indent=2)
    got = parse(json.dumps([inner], indent=4))
    assert got.people == 1
    assert got.subjects == ["man", "mustache"]
    assert got.hour == "night"


def test_a_bare_json_object_is_read_too():
    from studio.panel_content import parse
    got = parse('{"landform": "hills", "people": 2, "lookalikes": 1, '
                '"text": true, "hour": "day", "subjects": ["a doll"]}')
    assert got.landform == "hills" and got.people == 2 and got.text is True


def test_an_answer_that_cannot_be_read_raises_rather_than_passing():
    """A read that fails must not look like a clean panel."""
    from studio.panel_content import Unreadable, parse
    import pytest as _pytest
    with _pytest.raises(Unreadable):
        parse("the picture shows a man standing in heather")


# ---- what the first design got wrong --------------------------------------
def test_an_unlisted_detail_is_not_a_fault():
    """MEASURED: the first `faults` flagged every panel of ep07, 27 of 27.

    Shot prose describes a COMPOSITION, not an inventory, so "tie", "trees",
    "wallpaper" and "tablecloth" are all legitimately in frame and none of
    them is named. A gate that fails everything says nothing."""
    from studio.panel_content import faults
    got = faults(seen(subjects=["heather", "a tie", "wallpaper", "trees"]),
                 frame="black heather at night", planned=0, crowd=False,
                 flat=True, night=True)
    assert got == []


def test_a_banned_subject_is_still_a_fault():
    """The doll, and anything else an episode says must never appear."""
    from studio.panel_content import faults
    got = faults(seen(subjects=["heather", "a child's doll"]),
                 frame="black heather at night", planned=0, crowd=False,
                 flat=True, night=True, banned=("doll", "mountain"))
    assert any("doll" in f for f in got)


def test_facial_hair_the_cast_row_forbids_is_a_fault():
    """The narrator is clean-shaven and the reader saw a moustache on him in
    six panels. Nothing in this pipeline was comparing the two."""
    from studio.panel_content import contradictions
    assert contradictions(seen(subjects=["man", "mustache", "suit"]),
                          "a lean clean-shaven man of thirty-five")


def test_a_beard_the_cast_row_asks_for_is_not():
    from studio.panel_content import contradictions
    assert not contradictions(seen(subjects=["man", "short sandy beard"]),
                              "a spare quick man with a short sandy beard")


def test_a_hill_where_the_location_is_a_hill_is_not_a_fault():
    """Maybury HILL is a hill. Flatness is a property of the LOCATION, not of
    the book."""
    from studio.panel_content import forbidden_landform
    assert not forbidden_landform(seen(landform="hills"), flat=False)


# ---- three false positives the first real run produced --------------------
def test_a_banned_word_matches_a_whole_word_only():
    """MEASURED: the reader said "carafe" on three panels of a dining room and
    the gate reported a CAR, because "car" is a substring of it."""
    from studio.panel_content import banned_subject
    assert banned_subject(seen(subjects=["a carafe of wine"]), ("car",)) == []
    assert banned_subject(seen(subjects=["a car in the road"]), ("car",)) == ["car"]


def test_an_indoor_picture_is_not_judged_on_the_hour():
    """A lamplit dining room read as 'day' and was called a night fault. The
    hour of an interior is the lamp's, and the reader cannot see the sky."""
    from studio.panel_content import faults
    got = faults(seen(landform="indoors", hour="day"), frame="the dining room at night",
                 planned=0, crowd=False, flat=False, night=True)
    assert not any("hour" in f for f in got)


def test_an_insert_on_a_body_part_may_hold_a_figure():
    """ep07's shot 20 is an INSERT on a burst collar stud at a man's throat,
    cast for nobody, and the reader counted one figure -- correctly. A collar
    is worn. It is the same rule `whole_subject` states for the other
    direction: a horse's head cannot exist on its own."""
    from studio.panel_content import worn_by_someone
    assert worn_by_someone("Insert on a burst collar stud at his throat")
    assert worn_by_someone("Insert on the hand resting on the gate")
    assert not worn_by_someone("Insert on the cold joint and the loaf on the cloth")


def test_printed_matter_may_carry_print():
    """ep08 shot 6 is an INSERT ON A NEWSPAPER and the gate called its type a
    fault. A shot whose subject is printed carries print by definition."""
    from studio.panel_content import faults, prints_words
    assert prints_words("Insert on the front page of an evening paper")
    assert prints_words("the shuttered bookstall with its board")
    assert not prints_words("Insert on the cold joint and the loaf")
    # the SIZE decides it now (audit 2026-09-22): type is expected only where a
    # printed thing is the subject of an insert or close
    got = faults(seen(text=True), frame="Insert on the front page of an evening paper",
                 planned=0, crowd=False, flat=True, night=True, size="insert")
    assert not any("text" in f or "lettering" in f for f in got)


def test_two_identical_machines_are_not_copied_people():
    """ep10 shot 13: two tripods over a cylinder, no one in the field. The
    reader said 0 people and 2 lookalikes; lookalikes are 'of those figures',
    so with nobody there, the copies are machines the book asks for."""
    from studio.panel_content import Seen, people_fault
    assert not people_fault(Seen(people=0, lookalikes=2), planned=0, crowd=False)
    assert people_fault(Seen(people=3, lookalikes=2), planned=3, crowd=True)
