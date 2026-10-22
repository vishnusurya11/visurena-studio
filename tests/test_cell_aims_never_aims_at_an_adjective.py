"""The move cure's aims are nouns, never one adjective of a list (shot framework D-f).

`move_rebalance.cell_aims` split `at_rest` on every comma, so "the lawyer's gaunt, rugged, unsmiling
face" lent "gaunt" and "rugged" as things to aim at, and ep01 shots 21 and 24 were cured to "The camera
tilts up from the gaunt to the rugged" -- the motions behind ep01's only ladder round (warp).  A one-word
piece between commas is an adjective of the list that follows it, never a clause of its own.
Fixture: tests/fixtures/shot_framework/episodes/ep01/plan.json."""
from __future__ import annotations

import pytest

import shot_framework_fixtures as sf
from studio import move_rebalance as mr


def shot(index: int) -> dict:
    return next(s for s in sf.plan()["shots"] if s["index"] == index)


def test_the_cure_wrote_gaunt_to_rugged_into_ep01():
    assert "from the gaunt to the rugged" in shot(21)["motion"] and "from the gaunt to the rugged" in shot(24)["motion"]


@pytest.mark.parametrize("index", [21, 24])
def test_shots_21_24_have_no_gaunt_or_rugged(index):
    aims = mr.cell_aims(shot(index), sf.plan()["setups"][shot(index)["setup"]])
    assert "gaunt" not in aims and "rugged" not in aims
    assert "face" in aims


def test_a_clause_without_a_list_keeps_its_noun():
    assert {"man", "cobbles"} <= set(mr.cell_aims(shot(8), sf.plan()["setups"]["night_corner"]))
