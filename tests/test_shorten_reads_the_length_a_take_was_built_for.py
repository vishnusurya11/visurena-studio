"""The shorter-take rung compares the timeline against the length the take was
BUILT FOR (its record's `placed_seconds`), never its measured file length.

A ref2v take renders frames_for(placed + HANDLE), so its file is always longer
than its placed seconds (Jekyll ep01 v2 T14: placed 5.04 s, file 5.88 s).  The
ladder passed `measured_seconds`, every shorten read "restore", and T14's
mux-lag cure became four same-length reseeds (2026-10-14)."""
from __future__ import annotations

from studio import take_ladder


def test_a_take_built_for_its_placed_length_is_measured_by_that_length():
    record = {"index": 14, "placed_seconds": 5.041667, "measured_seconds": 5.88}
    assert take_ladder.built_for(record) == 5.041667


def test_an_older_record_without_placed_seconds_falls_back_to_its_file():
    assert take_ladder.built_for({"index": 3, "measured_seconds": 6.58}) == 6.58


def test_a_missing_record_reads_zero():
    assert take_ladder.built_for({}) == 0.0


def test_a_take_at_its_placed_length_is_shortened_not_restored():
    doc = {"shots": [{"index": 14, "beat_s": 0.0, "coda_s": 1.5}]}
    record = {"index": 14, "placed_seconds": 5.041667, "measured_seconds": 5.88}
    doc, action = take_ladder.shorten(doc, 14, 5.041667, take_ladder.built_for(record))
    assert action == "shorten" and doc["shots"][0]["coda_s"] == 0.75
