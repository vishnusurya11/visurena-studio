"""Step 05's bounded measured-hole cure: trim_measured_holes shaves the holds
of the shots a MEASURED hole crosses down to MAX_GAP_S - HOLE_MARGIN_S, never
below a floor, never a shot outside the hole, and inserts nothing.  0 shaved
(every slot at its floor) leaves the doc byte-equal and the step refuses."""
from __future__ import annotations

import json

from studio import plan_cures as pc


def placed_with_8s_hole() -> dict:
    return {"duration_s": 13.0,
            "lines": [{"index": 0, "at": 0.25, "seconds": 2.0, "shot": 0},
                      {"index": 1, "at": 10.25, "seconds": 2.0, "shot": 3}],
            "shots": [{"index": 0, "t_start": 0.0, "t_end": 3.0},
                      {"index": 1, "t_start": 3.0, "t_end": 6.0},
                      {"index": 2, "t_start": 6.0, "t_end": 10.0},
                      {"index": 3, "t_start": 10.0, "t_end": 12.5},
                      {"index": 4, "t_start": 12.5, "t_end": 13.0}]}


def doc_of() -> dict:
    return {"shots": [{"index": 0, "beat_s": 0.5, "coda_s": 1.5},
                      {"index": 1, "beat_s": 0.0, "coda_s": 2.0},   # wordless
                      {"index": 2, "beat_s": 0.4, "coda_s": 0.5},   # wordless, pre-button
                      {"index": 3, "beat_s": 0.0, "coda_s": 1.0},   # the button shot
                      {"index": 4, "beat_s": 0.0, "coda_s": 3.0}],  # OUTSIDE the hole
            "lines": [{"index": 0, "shot": 0, "text": "just four words here"},
                      {"index": 1, "shot": 3, "text": "the button line lands"}]}


def test_the_trim_cuts_exactly_to_the_margin_wall_and_only_inside_the_hole():
    doc = doc_of()
    before = {(s["index"], k): s[k] for s in doc["shots"] for k in ("beat_s", "coda_s")}
    shaved = pc.trim_measured_holes(doc, placed_with_8s_hole())
    assert shaved > 0
    cut = sum(before[(s["index"], k)] - s[k]
              for s in doc["shots"] for k in ("beat_s", "coda_s"))
    assert abs(cut - 2.5) < 0.02                                 # 8.0 s hole -> 5.5 s
    assert doc["shots"][4]["coda_s"] == 3.0                      # outside the hole: untouched
    assert len(doc["lines"]) == 2                                # trims only, never inserts


def test_no_hold_falls_below_its_floor():
    doc = doc_of()
    pc.trim_measured_holes(doc, placed_with_8s_hole())
    by = {s["index"]: s for s in doc["shots"]}
    assert by[1]["coda_s"] >= 0.5                                # wordless floor
    assert by[2]["coda_s"] >= 0.5
    assert by[2]["beat_s"] == 0.4                                # under the 1.0 floor: untouched
    assert by[3]["coda_s"] >= 0.6                                # button rest


def test_everything_at_its_floor_shaves_nothing_and_changes_nothing():
    doc = {"shots": [{"index": 0, "beat_s": 0.0, "coda_s": 0.0},
                     {"index": 1, "beat_s": 0.0, "coda_s": 0.5},
                     {"index": 2, "beat_s": 0.4, "coda_s": 0.5},
                     {"index": 3, "beat_s": 0.0, "coda_s": 0.6},
                     {"index": 4, "beat_s": 0.0, "coda_s": 3.0}],
           "lines": doc_of()["lines"]}
    before = json.dumps(doc, sort_keys=True)
    assert pc.trim_measured_holes(doc, placed_with_8s_hole()) == 0
    assert json.dumps(doc, sort_keys=True) == before
