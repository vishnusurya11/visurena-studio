"""The shorter-take rung first RESTORES a length that was just changed under
the take -- a line edited after the render moved the shot's placed seconds
(measured: two takes 88 frames short of their audio) -- by re-rendering at
the placed length with the plan untouched.  Only a take already at its placed
length has its beat and coda cut so the line fills more of it."""
from __future__ import annotations

from studio import take_ladder


def plan() -> dict:
    return {"shots": [{"index": 5, "beat_s": 0.8, "coda_s": 0.6, "frame": "a man"},
                      {"index": 6, "beat_s": 0.4, "coda_s": 0.0, "frame": "a hand"}]}


def test_a_take_whose_placed_seconds_moved_is_restored_first():
    doc, action = take_ladder.shorten(plan(), 5, placed_s=7.08, rendered_s=6.58)
    assert action == "restore"
    assert doc["shots"][0] == {"index": 5, "beat_s": 0.8, "coda_s": 0.6, "frame": "a man"}


def test_a_take_at_its_placed_length_has_its_beat_and_coda_halved():
    doc, action = take_ladder.shorten(plan(), 5, placed_s=6.58, rendered_s=6.60)
    assert action == "shorten"
    assert doc["shots"][0]["beat_s"] == 0.4 and doc["shots"][0]["coda_s"] == 0.3
    assert doc["shots"][1] == {"index": 6, "beat_s": 0.4, "coda_s": 0.0, "frame": "a hand"}


def test_a_shot_with_nothing_left_to_cut_is_not_shortened_again():
    doc = {"shots": [{"index": 5, "beat_s": 0.0, "coda_s": 0.0}]}
    doc, action = take_ladder.shorten(doc, 5, placed_s=4.0, rendered_s=4.0)
    assert action == "" and doc["shots"][0]["beat_s"] == 0.0
