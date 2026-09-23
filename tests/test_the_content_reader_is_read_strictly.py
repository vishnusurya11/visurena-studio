"""The content reader's answer is read strictly, salvaged when cut off, and a
missing named person fails.

VLM-gate audit, 2026-09-23 (7 single-image reads, verdicts of ep08/ep09):
- "unread: no JSON" was a reply cut off inside `subjects` -- the five judged
  fields were already complete -- and it failed ep09 T21 at seed 6;
- `bool("false")` is True, and a subjects STRING was iterated into letters,
  silently disabling the beard, banned and hair checks;
- a two-person tea panel read 0 people and passed: only too MANY failed;
- "mountains", "cliffs" and "dolls" passed a list that bans the singulars;
- the message said "7 figure(s) for 0 cast" when 6 extras were declared.
"""
import pytest

from studio.panel_content import Seen, Unreadable, faults, parse

WHOLE = '{"landform": "gentle rise", "people": 2, "lookalikes": 0, "text": false, "hour": "dusk", '


def seen(**kw) -> Seen:
    return Seen(**{**dict(landform="flat", people=0, lookalikes=0, text=False, hour="day", subjects=[]), **kw})


def test_a_reply_cut_off_inside_subjects_is_salvaged():
    got = parse(WHOLE + '"subjects": ["horse", "cart", "people", "chur')
    assert got.people == 2 and got.subjects == ["horse", "cart", "people"]


def test_a_reply_cut_off_before_a_judged_field_still_refuses():
    with pytest.raises(Unreadable):
        parse('{"landform": "gentle rise", "people": 2, "looka')


def test_false_as_a_string_is_false():
    assert parse(WHOLE.replace("false", '"false"') + '"subjects": []}').text is False


def test_subjects_as_a_string_are_words_not_letters():
    assert parse(WHOLE + '"subjects": "man, beard"}').subjects == ["man", "beard"]


def test_a_named_person_missing_from_the_picture_fails():
    got = faults(seen(people=0), frame="Medium on the two of them at tea", planned=2,
                 crowd=False, flat=True, night=False, size="medium")
    assert any("missing" in f for f in got)


def test_an_insert_or_a_back_view_may_hold_fewer_faces():
    assert not faults(seen(people=0), frame="Insert on his hand", planned=1, crowd=False,
                      flat=True, night=False, size="insert")
    assert not faults(seen(people=0), frame="Medium on him with his back to the camera", planned=1,
                      crowd=False, flat=True, night=False, size="medium")


def test_a_banned_singular_bans_its_plural():
    got = faults(seen(subjects=["mountains", "sky"]), frame="Wide", planned=0, crowd=False,
                 flat=True, night=False, banned=["mountain"], size="wide")
    assert any("banned" in f for f in got)


def test_the_count_message_names_the_declared_total():
    got = faults(seen(people=7), frame="Wide on a bevy of hussars", planned=0, crowd=False,
                 flat=True, night=False, size="wide", extras=6)
    assert got and "6 declared" in got[0]
