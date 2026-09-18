"""THE ROOM IS STAGED ON EVERY REFERENCES-ONLY TAKE, tight ones included.

This file recorded the opposite rule for one afternoon, and the reversal is
worth keeping because both halves were measured on the same episode.

WHY IT WAS WITHHELD (ep02, and ep14's first references-only reel): beside a
close-up CELL the room becomes the only whole picture the model can fall back
on -- 13 of episode 2's 14 foreign frames were the take's own plate, and ep14's
T20 (medium close) opened on the room at cosine 0.999 before dissolving into an
invented library, T21 (insert) opened on it and hard-cut into the shot at frame
14. So `places_the_plate` was consulted here too, and tight takes staged the
face alone.

WHY IT IS STAGED AGAIN: with the room withheld, the four takes that had only a
face invented a building -- ep14's T04, T05, T06 and T22 put Holmes and Watson
in a Gothic panelled hall with a carved stone chimneypiece, and T22's prompt
asked for a curtained window that the shot does not contain. A room that opens
at the wrong size is a fixable framing fault; a room that is the wrong room is a
continuity break across the cut. OWNER 2026-09-17: "this needs location image
too ... so you define the position relative to things in location, so it's
accurate."

The opening-on-the-room fault is answered where the vendor's guide puts it
instead: a plate is cited INSIDE `<Subject N>` and never given a `<Picture N>`
line of its own, which is the documented switch between "identity source" and
"frame anchor" (ref-en 2.2).
"""
import sys

sys.path.insert(0, "scripts/episode")

import takes_r2v


def refs(faces, sizes, tmp_path):
    return [p.name for p in takes_r2v.refs_from_cards(tmp_path, tmp_path, faces, "sitting_room",
                                                      sizes=sizes)]


def test_a_tight_take_stages_its_face_and_its_room(tmp_path):
    assert refs(["john_watson"], ["medium_close"], tmp_path) == ["char-john_watson.png",
                                                                 "plate_sitting_room.png"]


def test_an_insert_with_a_face_stages_both_too(tmp_path):
    assert refs(["sherlock_holmes"], ["insert"], tmp_path) == ["char-sherlock_holmes.png",
                                                               "plate_sitting_room.png"]


def test_a_wide_stages_both(tmp_path):
    assert refs(["sherlock_holmes"], ["medium"], tmp_path) == ["char-sherlock_holmes.png",
                                                               "plate_sitting_room.png"]


def test_a_faceless_take_stages_the_room_alone(tmp_path):
    for size in ("insert", "close", "wide"):
        assert refs([], [size], tmp_path) == ["plate_sitting_room.png"], size


def test_a_take_always_stages_at_least_one_picture(tmp_path):
    for faces, sizes in (([], ["insert"]), (["john_watson"], ["close"]), ([], ["wide"])):
        assert refs(faces, sizes, tmp_path), (faces, sizes)
