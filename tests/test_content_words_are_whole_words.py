"""The content gate reads words, not letters, and never fills in an answer.

Audit items 2 and 36, measured 2026-09-22 on panel_content:
- WORN and PRINTED matched inside other words: "surface" was a face, "chair"
  was hair, "footpath" a foot; "papered wall" was paper, "boot print" print,
  "cupboard" a board. A WORN match makes the shot a crowd and stands the
  people check down; a PRINTED match switched the lettering check off -- on
  five ep07 dining-room shots that say "papered wall", the room that already
  had a lettered engraving.
- A printed thing anywhere in the prose excused lettering anywhere in the
  picture. Type is expected only where the printed thing IS the subject: an
  insert or close on it.
- `parse` filled a missing field with a default -- no "people" read as 0
  people, no "hour" as night, no "text" as no text -- so a malformed answer
  passed as a clean one. A missing field is an unreadable answer.
"""
import json

import pytest

from studio.panel_content import Unreadable, lettering_expected, parse, worn_by_someone


@pytest.mark.parametrize("prose", [
    "a collar stud at his throat", "her hands folded", "a boot on the fender",
    "the cuff of his sleeve", "his face lit from the left"])
def test_parts_of_a_person_are_found(prose):
    assert worn_by_someone(prose)


@pytest.mark.parametrize("prose", [
    "the surface of the canal", "a chair by the window", "a footpath across the heath",
    "the handle of the door", "a bootscraper by the step"])
def test_words_that_merely_contain_them_are_not(prose):
    assert not worn_by_someone(prose)


@pytest.mark.parametrize("prose,size", [
    ("Insert on the front page of an evening newspaper", "insert"),
    ("Close on a telegram in his hand", "close"),
    ("Insert on a timetable pinned by the bookstall", "insert")])
def test_lettering_is_expected_on_a_printed_subject_up_close(prose, size):
    assert lettering_expected(prose, size)


@pytest.mark.parametrize("prose,size", [
    ("Wide on a papered dining room with a table laid for two", "wide"),
    ("Medium on him beside a cupboard", "medium"),
    ("A boot print in the sand", "insert"),
    ("Wide on the platform, a poster on the far wall", "wide")])
def test_lettering_is_not_excused_elsewhere(prose, size):
    assert not lettering_expected(prose, size)


def answer(**fields):
    base = {"landform": "flat", "people": 1, "lookalikes": 0, "text": False,
            "hour": "day", "subjects": ["a man"]}
    base.update(fields)
    return json.dumps(base)


def test_a_complete_answer_parses():
    assert parse(answer()).people == 1


@pytest.mark.parametrize("missing", ["people", "hour", "text", "lookalikes", "landform"])
def test_a_missing_field_is_unreadable_not_a_default(missing):
    got = json.loads(answer())
    got.pop(missing)
    with pytest.raises(Unreadable, match=missing):
        parse(json.dumps(got))
