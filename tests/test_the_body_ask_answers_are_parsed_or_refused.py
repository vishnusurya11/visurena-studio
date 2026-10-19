"""K9 (retro 2026-10-19, P06): the optional shape keys on the existing VL ask.

`body`, `limb_attached` and `fog_cover` are read with .get -- an answer
without them is still a whole answer -- and a value outside ok / fading /
floating / cannot_tell reads as cannot_tell, never as Unreadable (the old
reads in the vlm cache stay valid).
"""
from __future__ import annotations

import json

from studio import panel_content as pc, take_content as tc

BASE = {"landform": "flat", "people": 1, "lookalikes": 0, "text": False, "hour": "day", "subjects": ["man"]}


def said(**extra) -> str:
    return json.dumps({**BASE, **extra})


def test_an_old_answer_without_the_keys_still_parses():
    got = pc.parse(said())
    assert (got.body, got.limb_attached, got.fog_cover) == ("", "", "")


def test_the_three_keys_are_read():
    got = pc.parse(said(body="Fading", limb_attached="floating", fog_cover="ok"))
    assert (got.body, got.limb_attached, got.fog_cover) == ("fading", "floating", "ok")


def test_a_foreign_value_becomes_cannot_tell_not_unreadable():
    got = pc.parse(said(body="dissolving", limb_attached=True, fog_cover=3))
    assert (got.body, got.limb_attached, got.fog_cover) == ("cannot_tell",) * 3


def test_the_keys_are_not_required():
    assert not {"body", "limb_attached", "fog_cover"} & set(pc.REQUIRED)


def test_the_ask_names_the_keys_and_the_take_ask_carries_them():
    for key in ("body", "limb_attached", "fog_cover"):
        assert f'"{key}"' in pc.ASK and f'"{key}"' in tc.ASK
    assert "cannot_tell" in pc.ASK


def test_the_ask_has_one_version_marker():
    assert pc.ASK_VERSION == "2" and f"ask v{pc.ASK_VERSION}" in pc.ASK


def test_a_refusal_needs_recall_and_precision_from_the_eval():
    assert pc.calibrated(recall=0.6, precision=0.8) is True
    assert pc.calibrated(recall=0.59, precision=0.9) is False
    assert pc.calibrated(recall=0.9, precision=0.79) is False


def test_the_scores_count_hits_and_false_alarms():
    got = pc.eval_scores([True, True, False, False], [True, False, True, False])
    assert got == {"recall": 0.5, "precision": 0.5, "tp": 1, "fp": 1, "fn": 1, "n": 4}
