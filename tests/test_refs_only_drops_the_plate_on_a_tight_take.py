"""A tight take with a face of its own does not also stage the room.

MEASURED on episode 14's first references-only run (2026-09-17), 24 takes with
no storyboard cell:

  T20  medium close, Watson reading   frame 0 cosine to its plate 0.999, then a
                                      dissolve into an INVENTED library
  T21  insert, a fist on a newspaper  frame 0 cosine 0.999, hard cut at frame 14
                                      (the DQ's `cut` row read 55.6)

That is episode 2's fault in a new place: "a take of nothing but tight cells
cannot place a room, so the plate stops being a definition and becomes the only
whole picture the model can fall back on" -- 13 of 14 foreign frames were the
take's own plate. `places_the_plate` answers it on the normal path.

So the rule holds here too, with one exception that is not a preference: a take
with NO cast sheet has nothing else to stage, and `graph_for` reads `paths[0]`
before it counts. Such a take keeps its plate.
"""
import sys
from pathlib import Path

sys.path.insert(0, "scripts/episode")

import takes_r2v


def refs(faces, sizes, tmp_path):
    return [p.name for p in takes_r2v.refs_from_cards(tmp_path, tmp_path, faces, "sitting_room", sizes=sizes)]


def test_a_tight_take_with_a_face_stages_the_face_alone(tmp_path):
    got = refs(["john_watson"], ["medium_close"], tmp_path)
    assert got == ["char-john_watson.png"]


def test_an_insert_with_a_face_stages_the_face_alone(tmp_path):
    assert refs(["sherlock_holmes"], ["insert"], tmp_path) == ["char-sherlock_holmes.png"]


def test_a_take_with_a_wide_enough_shot_keeps_its_plate(tmp_path):
    got = refs(["sherlock_holmes"], ["medium"], tmp_path)
    assert got == ["char-sherlock_holmes.png", "plate_sitting_room.png"]


def test_a_faceless_take_keeps_its_plate_whatever_its_size(tmp_path):
    assert refs([], ["insert"], tmp_path) == ["plate_sitting_room.png"]
    assert refs([], ["close"], tmp_path) == ["plate_sitting_room.png"]
    assert refs([], ["wide"], tmp_path) == ["plate_sitting_room.png"]


def test_a_take_always_stages_at_least_one_picture(tmp_path):
    for faces, sizes in (([], ["insert"]), (["john_watson"], ["close"]), ([], ["wide"])):
        assert refs(faces, sizes, tmp_path), (faces, sizes)
