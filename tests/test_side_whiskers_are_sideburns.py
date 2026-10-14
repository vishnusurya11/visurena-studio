"""Side-whiskers are not a moustache (Jekyll ep01 Hellsing remake, 2026-10-14).

Hyde's base face reads "thick, bushy black mutton-chop side-whiskers down both
cheeks to the jaw"; the closed FACIAL table matched `whisker` as a moustache, so
refs/looks.json stamped `facial_hair: moustache` and LOOK-STATE would have
refused every drawn Hyde that shows his mutton chops and a bare upper lip.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import look_table as lt
from studio.continuity_spec import Markers
from studio.judges import look_state as ls

HYDE = ("thick, bushy black mutton-chop side-whiskers down both cheeks to the jaw; "
        "thin upper lip curled in a cold sneer")


@pytest.mark.parametrize("face", [HYDE, "grey side-whiskers", "mutton chops", "long sideburns",
                                  "whiskered cheeks, sidewhiskers to the jaw"])
def test_side_whiskers_mark_sideburns(face):
    assert lt.first_of(lt.FACIAL, face) == "sideburns"


@pytest.mark.parametrize("face, want", [("a heavy walrus moustache", "moustache"),
                                        ("side-whiskers and a waxed moustache", "moustache"),
                                        ("grey whiskers", "moustache"),
                                        ("a full beard and mutton chops", "beard"),
                                        ("clean-shaven", "none")])
def test_the_other_faces_keep_their_marker(face, want):
    assert lt.first_of(lt.FACIAL, face) == want


def test_sideburns_is_a_contract_marker():
    assert Markers(facial_hair="sideburns").facial_hair == "sideburns"
    assert "sideburns" in ls.VOCAB["facial_hair"]


def reader(**said):
    return lambda picture, question: json.dumps(said)


@pytest.mark.parametrize("seen", ["sideburns", "beard"])
def test_mutton_chops_read_as_sideburns_or_a_beard_pass(seen):
    want = Markers(headwear="felt_hat", hair_colour="dark", facial_hair="sideburns")
    v = ls.judge(Path("x.png"), want, reader(headwear="felt_hat", hair_colour="dark", facial_hair=seen))
    assert v.passed, v.faults


def test_a_bare_face_on_a_sideburns_look_is_hard():
    want = Markers(headwear="felt_hat", hair_colour="dark", facial_hair="sideburns")
    v = ls.judge(Path("x.png"), want, reader(headwear="felt_hat", hair_colour="dark", facial_hair="none"))
    assert not v.passed and v.faults[0].kind == "look_facial_hair"
