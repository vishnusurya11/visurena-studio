"""ep01 shot 2 (retro 2026-10-19, P06): the coat and shoulders melted into fog
and every gate passed, because every gate counts and none sees shape.

A canned VL read of 'fading' on two of a take's three frames is a content
fault at the shot's take -- once the kind is calibrated on the eval set
(recall >= 0.6, precision >= 0.8).  Until then, and for a single vote, it is
an advisory on the row.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

from studio import panel_content as pc

from scripts.episode import take_content_check as tcc

BASE = {"landform": "flat", "people": 1, "lookalikes": 0, "text": False, "hour": "day", "subjects": ["man"]}


def read(**kw) -> pc.Seen:
    return pc.parse(json.dumps({**BASE, **kw}))


def test_two_fading_frames_of_three_are_a_fault_when_calibrated():
    got, _ = pc.shape_read([read(body="fading"), read(body="ok"), read(body="fading")], refusing={"body"})
    assert got == ["body: reads 'fading' on 2 of 3 frames"]


def test_a_single_vote_is_advisory_even_when_calibrated():
    got, note = pc.shape_read([read(body="fading"), read(body="ok"), read(body="ok")], refusing={"body"})
    assert got == [] and note == ["body reads 'fading' on 1 of 3 frames (advisory: one vote)"]


def test_uncalibrated_is_advisory_whatever_the_votes():
    assert pc.BODY_REFUSES == frozenset()
    got, note = pc.shape_read([read(body="fading")] * 3)
    assert got == [] and note and "advisory" in note[0]


def test_cannot_tell_and_ok_never_vote():
    got, note = pc.shape_read([read(body="cannot_tell"), read(body="ok"), read()], refusing={"body"})
    assert got == [] and note == []


def test_the_take_verdict_fails_at_that_shot_when_calibrated(monkeypatch, tmp_path):
    monkeypatch.setattr(pc, "BODY_REFUSES", frozenset({"body"}))
    row = verdict(tmp_path, [read(body="fading")] * 3)
    assert row["passed"] is False and "body: reads 'fading' on 3 of 3 frames" in row["faults"]


def test_the_take_verdict_carries_the_advisory_by_default(tmp_path):
    row = verdict(tmp_path, [read(body="fading")] * 3)
    assert row["passed"] is True and row["shape_advisory"]


def verdict(book, reads):
    shot = SimpleNamespace(frame="Close on the man.", at_rest="", size="close", faces=[], extras=1, index=2,
                           model_fields_set={"frame", "faces", "extras"})
    setup = SimpleNamespace(crowd="", described="a street by day", location="")
    return tcc.verdict_for(book, shot, setup, reads, panel_people=1)

