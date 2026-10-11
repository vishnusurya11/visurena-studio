"""LOOK-STATE read the caption workflow's real answer as 'not an object' and
PASSED the look (ep25 replay, 2026-10-10): the workflow wraps the JSON in a
list holding one STRING of JSON.  The parse unwraps it once, and a look whose
head markers were not read is refused, never passed (a terminal is not a pass)."""
from __future__ import annotations

import json
from pathlib import Path

from studio.continuity_spec import Markers
from studio.judges import look_state as ls

RAW = json.dumps([json.dumps({"headwear": "felt_hat", "hair_colour": "grey", "facial_hair": "none",
                              "top": "shirt", "dirt": "dusty"}, indent=2)], indent=4)
"""Dumped verbatim from the Qwen3-VL caption workflow on ragged_greyed.png."""
RAGGED = Markers(headwear="felt_hat", hair_colour="grey", facial_hair="beard", top="shirt", dirt="muddy")


def test_the_caption_lists_wrapped_json_string_is_read():
    assert ls.parse(RAW) == {"headwear": "felt_hat", "hair_colour": "grey", "facial_hair": "none",
                             "top": "shirt", "dirt": "dusty"}


def test_a_list_holding_an_object_is_read():
    assert ls.parse(json.dumps([{"hair_colour": "grey"}]))["hair_colour"] == "grey"


def test_the_real_answer_is_judged_on_its_markers():
    v = ls.judge(Path("x.png"), RAGGED, lambda p, q: RAW)
    assert not v.passed and [f.kind for f in v.faults if f.severity == "high"] == ["look_facial_hair"]


def test_an_unreadable_answer_refuses():
    v = ls.judge(Path("x.png"), RAGGED, lambda p, q: "I cannot tell")
    assert not v.passed and v.faults[0].kind == "unread" and v.faults[0].severity == "high"


def test_a_wanted_head_marker_left_unread_refuses():
    said = json.dumps({"headwear": "felt_hat", "hair_colour": "grey", "top": "shirt"})
    v = ls.judge(Path("x.png"), RAGGED, lambda p, q: said)
    assert not v.passed and [f.kind for f in v.faults] == ["unread_facial_hair"]


def test_an_unstated_marker_needs_no_read():
    said = json.dumps({"hair_colour": "grey"})
    assert ls.judge(Path("x.png"), Markers(hair_colour="grey"), lambda p, q: said).passed
