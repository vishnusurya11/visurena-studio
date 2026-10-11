"""LOOK-STATE: the reader lists, code judges.  A missing beard, grey hair or
hat refuses the look picture (HARD); top and dirt only flag; identity is a
relative margin and only advises until the bench fits it (verdict S)."""
from __future__ import annotations

import json
from pathlib import Path

from studio.continuity_spec import Markers
from studio.judges import look_state as ls

RAGGED = Markers(headwear="felt_hat", hair_colour="grey", facial_hair="beard", top="shirt", dirt="muddy")


def reader(**said):
    return lambda picture, question: json.dumps(said)


def test_a_picture_showing_every_marker_passes():
    v = ls.judge(Path("x.png"), RAGGED, reader(headwear="felt_hat", hair_colour="white", facial_hair="beard",
                                               top="shirt", dirt="muddy"))
    assert v.passed and v.faults == []


def test_dark_hair_on_a_grey_look_is_hard():
    v = ls.judge(Path("x.png"), RAGGED, reader(headwear="felt_hat", hair_colour="dark", facial_hair="beard"))
    assert not v.passed and v.faults[0].kind == "look_hair_colour"


def test_the_sheets_boater_on_a_felt_hat_look_is_hard():
    assert not ls.judge(Path("x.png"), RAGGED, reader(headwear="boater", hair_colour="grey")).passed


def test_a_wrong_top_or_dirt_only_flags():
    v = ls.judge(Path("x.png"), RAGGED, reader(hair_colour="grey", top="suit_jacket", dirt="clean"))
    assert v.passed and {f.kind for f in v.faults} == {"look_top", "look_dirt"}


def test_an_unreadable_answer_flags_and_never_passes_silently():
    v = ls.judge(Path("x.png"), RAGGED, lambda p, q: "I cannot tell")
    assert v.faults[0].kind == "unread" and v.confidence == 0.0


def test_a_look_nearer_a_stranger_than_itself_is_advised():
    vecs = {"look.png": [1.0, 0.0], "base.png": [0.6, 0.8], "other.png": [0.9, 0.1]}
    v = ls.judge(Path("look.png"), RAGGED, reader(hair_colour="grey"), face_change=True,
                 embed=lambda p: vecs[Path(p).name], base=Path("base.png"), others=[Path("other.png")])
    assert v.passed and v.faults[0].kind == "look_identity"


def test_a_clothes_only_look_skips_identity():
    v = ls.judge(Path("look.png"), RAGGED, reader(hair_colour="grey"), face_change=False,
                 embed=lambda p: 1 / 0, base=Path("base.png"))
    assert v.passed
