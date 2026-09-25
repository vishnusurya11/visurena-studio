"""The story field: the plan's turn verb among the actions the reader LISTS
on the turn shot and its neighbours.  The reader is never asked whether the
turn landed; it names what the person is doing, and code compares roots."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from studio.judges import master_eye as me

READS = json.loads((Path(__file__).parent / "fixtures" / "vlm" / "master_reads.json").read_text("utf-8"))["reads"]
TURN = {"index": 7, "section": "turn", "motion": "the camera holds on the curb; he catches the bridle"}


def reads_of(actions: dict[int, str]) -> dict[int, list[me.Read]]:
    return {shot: [me.Read(at=float(shot), shot=shot, action=action)] for shot, action in actions.items()}


def test_the_plans_verb_listed_on_the_turn_shot_is_a_y():
    ok, evidence = me.story(TURN, reads_of({7: "catching the bridle"}))
    assert ok and "catch" in evidence["matched"] and evidence["turn_shot"] == 7
    assert "hold" not in evidence["verbs"] and "camera" not in evidence["verbs"]


def test_a_neighbour_shot_counts_and_a_far_shot_does_not():
    assert me.story(TURN, reads_of({8: "he catches the horse"}))[0]
    assert me.story(TURN, reads_of({6: "catching"}))[0]
    ok, evidence = me.story(TURN, reads_of({5: "catching the bridle", 7: "walking"}))
    assert not ok and evidence["listed"] == ["walking"] and evidence["matched"] == []


def test_another_action_listed_is_an_n_with_the_listed_actions_as_evidence():
    ok, evidence = me.story(TURN, reads_of({7: "walking", 8: "standing"}))
    assert not ok and evidence["listed"] == ["walking", "standing"] and evidence["verbs"] == ["curb", "catch", "bridle"]


def test_the_reader_answers_carry_the_action_into_the_read():
    pic = np.zeros((8, 8, 3), dtype=np.uint8)
    catch = me.read_frame(lambda _p: READS["catch"], pic, 12.5, 7)
    assert catch.action == "catching the bridle" and catch.framing == "medium_close" and catch.seen is not None
    unread = me.read_frame(lambda _p: READS["unread"], pic, 12.5, 7)
    assert unread.seen is None and unread.action == ""
    assert me.story(TURN, {7: [catch]})[0] and not me.story(TURN, {7: [unread]})[0]


def test_no_turn_shot_in_the_plan_is_answered_y_with_a_note():
    ok, evidence = me.story(None, {})
    assert ok and "note" in evidence
