"""The move cures never write a push (shot framework B-1, ruling 1).

A push un-froze a held shot 8 of 8 times across the prompt bench and bench B1, and overran to cut a head or
hat on 4 of the 8 (end/first face 1.77, 1.86, 2.23 against the 1.6 cap; H3 ignores "stop before the crop").
So R1 is retired: a push is no freeze cure.  `move_rebalance.candidates` offered `push_slow` first on a
medium, medium close, close and insert, and `move_llm.head_prompt` listed it to the model.  A push stays
LEGAL for a size (`face_floor.blocker` reads `LEGAL`), and the writer may still write one on a realisation
beat inside G-PUSH's two; only the cures stop writing it.  Fixture: tests/fixtures/shot_framework/."""
from __future__ import annotations

from collections import Counter

import pytest

import shot_framework_fixtures as sf
from studio import move_llm, move_rebalance as mr


def shot(index: int) -> dict:
    return next(s for s in sf.plan()["shots"] if s["index"] == index)


def setup_of(index: int) -> dict:
    return sf.plan()["setups"][shot(index)["setup"]]


@pytest.mark.parametrize("index", [9, 10, 21])           # medium close, medium, medium close
def test_candidates_hold_no_push_on_a_medium_close(index):
    heads = mr.candidates(shot(index), Counter(), "", "", setup_of(index), 5.0)
    assert heads and not [h for h in heads if "pushes" in h]


def test_head_prompt_lists_no_push():
    said = move_llm.head_prompt(shot(21), setup_of(21), {}, "", "")
    assert mr.HEADS["push_slow"] not in said and "push_slow:" not in said


def test_a_push_stays_legal_for_the_size():
    assert "push_slow" in mr.LEGAL["medium_close"] and "push_slow" in mr.NOT_A_CURE
