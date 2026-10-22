"""A7: clean the screenplay input (craft ruling 2026-10-21, wave 1).

The Jekyll feature screenplay tells chapter 1 three times: scenes 1, 2 and 3 are all beat B01 at the
Black Mail House door (DAY / NIGHT / DAY), and scene 1 invents a visible "JEKYLL" signature the book
withholds ("a name that I can't mention").  The brief passed all three, unranked, with no note that
the book wins.  Now a RUN of scenes in one beat, one chapter and one room is one scene, kept by its
verbatim dialogue; B02's six scenes are not a run (five rooms, and the two in Utterson's house are not
adjacent), so all six survive.  An invented element says so, and the section says the chapter wins.
Fixture: tests/fixtures/craft/screenplay/feature/screenplay.json (the Jekyll file's scenes holding a
chapter 1 or 2 element, copied by name).  No render, no network, no spend."""
from __future__ import annotations

from pathlib import Path

from studio import plan_brief

BOOK = Path(__file__).parent / "fixtures" / "craft"


def test_the_ch1_brief_holds_one_b01_scene_not_three():
    scenes = plan_brief.screenplay(BOOK, 1)
    assert [s["number"] for s in scenes] == [3]          # the most verbatim dialogue of the three (18)


def test_the_ch2_brief_keeps_b02s_six_scenes():
    assert [s["number"] for s in plan_brief.screenplay(BOOK, 2)] == [4, 5, 6, 7, 8, 9]


def test_invented_staging_is_marked():
    scene = plan_brief._read(BOOK / "screenplay" / "feature" / "screenplay.json")["scenes"][0]
    marked = {e["text"]: e.get("invented", False) for e in plan_brief._scene_elements(scene, 1)}
    assert marked["Utterson takes the cheque. The signature is visible before Hyde can fold it away: JEKYLL."]
    assert marked["Did you ever remark that door?"] is False


def test_the_section_says_the_chapter_wins():
    text = plan_brief.render({"screenplay": [{"target": "feature"}]})
    assert "where the screenplay and the chapter disagree, the chapter wins" in text


def test_a_run_is_one_beat_one_chapter_one_room_adjacent():
    a = {"beat_id": "B1", "slug": {"location_id": "door"}, "elements": []}
    b = {"beat_id": "B1", "slug": {"location_id": "door"}, "elements": [
        {"kind": "dialogue", "provenance": "verbatim", "text": "x"}]}
    c = {"beat_id": "B1", "slug": {"location_id": "hall"}, "elements": []}
    assert plan_brief.one_per_run([a, b, c, dict(a)]) == [b, c, a]
