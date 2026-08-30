"""One beat becomes SEVERAL scenes when the place or the time changes.

The defect this fixes, measured on the only screenplay that exists: 16 of 22 scenes
changed location or time under a single slugline. Scene 12 covered six locations. Three
professional readers each called it the top finding - "this document cannot be broken
down" - and the location judges then found five scenes unanimously in the wrong place,
because a heading covering six places collapses to the vaguest thing covering them all,
which is how INT. UTAH happened.

A beat is a SEQUENCE. Coppola's notebook: 50 sections became 225 slug lines. One beat
was never meant to be one scene.
"""

from __future__ import annotations

from scripts.screenplay import step_03_draft as s03

LOCATIONS = {"221b": {"name": "221B Baker Street"},
             "lauriston": {"name": "3 Lauriston Gardens"}}


def _src(chapter, scene, location, time="DAY", int_ext="INT"):
    return {"chapter": chapter, "scene": scene, "location_id": location,
            "location_text": location, "time_of_day": time, "int_ext": int_ext}


def test_a_beat_in_one_place_at_one_time_is_one_scene():
    units = s03.split_beat([_src(1, 1, "221b"), _src(1, 2, "221b")], LOCATIONS)
    assert len(units) == 1


def test_a_location_change_starts_a_new_scene():
    units = s03.split_beat([_src(1, 1, "221b"), _src(1, 2, "lauriston")], LOCATIONS)
    assert len(units) == 2
    assert [u["slug"].location_id for u in units] == ["221b", "lauriston"]


def test_a_time_change_starts_a_new_scene():
    units = s03.split_beat([_src(1, 1, "221b", "DAY"), _src(1, 2, "221b", "NIGHT")],
                           LOCATIONS)
    assert [u["slug"].time for u in units] == ["DAY", "NIGHT"]


def test_returning_to_a_place_starts_another_scene():
    """A→B→A is three scenes, not two. Each return is a new setup on the board."""
    units = s03.split_beat(
        [_src(1, 1, "221b"), _src(1, 2, "lauriston"), _src(1, 3, "221b")], LOCATIONS)
    assert len(units) == 3


def test_each_unit_keeps_the_source_scenes_it_covers():
    units = s03.split_beat(
        [_src(1, 1, "221b"), _src(1, 2, "lauriston"), _src(1, 3, "lauriston")],
        LOCATIONS)
    assert [len(u["sources"]) for u in units] == [1, 2]


def test_the_slug_of_each_unit_describes_only_that_unit():
    """The whole point: a heading must be true of everything under it."""
    units = s03.split_beat([_src(1, 1, "221b"), _src(1, 2, "lauriston")], LOCATIONS)
    assert units[1]["slug"].location_name == "3 Lauriston Gardens"


def test_int_ext_follows_the_unit_not_the_beat():
    units = s03.split_beat(
        [_src(1, 1, "221b", int_ext="INT"), _src(1, 2, "lauriston", int_ext="EXT")],
        LOCATIONS)
    assert [u["slug"].int_ext for u in units] == ["INT", "EXT"]


def test_a_beat_with_no_source_scenes_still_yields_one_unit():
    """An invented connective cites nothing and still needs a slugline."""
    units = s03.split_beat([], LOCATIONS)
    assert len(units) == 1


def test_an_unplaced_scene_does_not_split_off_on_its_own():
    """A scene with no location continues the current one rather than starting a
    heading nobody can shoot. Splitting on None would manufacture UNKNOWN scenes."""
    units = s03.split_beat(
        [_src(1, 1, "221b"), _src(1, 2, None), _src(1, 3, "221b")], LOCATIONS)
    assert len(units) == 1 and len(units[0]["sources"]) == 3


def test_splitting_never_loses_a_source_scene():
    sources = [_src(1, n, loc) for n, loc in
               enumerate(["221b", "lauriston", "221b", None, "lauriston"], start=1)]
    units = s03.split_beat(sources, LOCATIONS)
    covered = [s for u in units for s in u["sources"]]
    assert len(covered) == len(sources)
