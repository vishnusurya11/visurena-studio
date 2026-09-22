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
                 flat=True, night=True)
    assert len(got) >= 4
    assert any("landform" in f for f in got)
    assert any("doll" in f for f in got)
    assert any("text" in f or "lettering" in f for f in got)
    assert any("night" in f or "hour" in f for f in got)


def test_burned_in_lettering_is_a_fault():
    assert any("text" in f or "lettering" in f
               for f in faults(seen(text=True), frame="heather", planned=0,
                               crowd=False, flat=True, night=True))
