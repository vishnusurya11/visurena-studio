"""ep01 shot 27 (retro 2026-10-19, P06): a green sleeve and a hand holding a
match ended in a hard cut mid-wall with no body, and the panel passed.

`limb_attached` 'floating' is a content fault on two frames of a take once
calibrated, an advisory on the panel's single read (the K9 contract P05 reads).
"""
from __future__ import annotations

import json

from studio import panel_content as pc

BASE = {"landform": "flat", "people": 1, "lookalikes": 0, "text": False, "hour": "day", "subjects": ["hand"]}


def read(**kw) -> pc.Seen:
    return pc.parse(json.dumps({**BASE, **kw}))


def test_two_floating_frames_are_a_limb_fault_when_calibrated():
    got, _ = pc.shape_read([read(limb_attached="floating"), read(limb_attached="floating"), read()],
                           refusing={"limb_attached"})
    assert got == ["limb_attached: reads 'floating' on 2 of 3 frames"]


def test_the_panels_single_read_is_an_advisory_naming_the_key():
    got, note = pc.shape_read([read(limb_attached="floating")], refusing={"limb_attached"})
    assert got == [] and note == ["limb_attached reads 'floating' on 1 of 1 frames (advisory: one vote)"]


def test_a_fading_fog_cover_is_logged_never_refused():
    got, note = pc.shape_read([read(fog_cover="fading")] * 3, refusing={"body", "limb_attached", "fog_cover"})
    assert got == [] and note and note[0].startswith("fog_cover")


def test_the_panel_row_lists_the_advisory_and_the_raw_keys():
    row = pc.shape_fields(read(body="fading", limb_attached="floating"))
    assert row["body"] == "fading" and row["limb_attached"] == "floating"
    assert row["shape_advisory"] == ["body reads 'fading' on 1 of 1 frames (advisory: one vote)",
                                     "limb_attached reads 'floating' on 1 of 1 frames (advisory: one vote)"]


def test_a_clean_read_adds_nothing_to_the_row():
    assert pc.shape_fields(read(body="ok", limb_attached="ok")) == {"body": "ok", "limb_attached": "ok", "shape_advisory": []}
