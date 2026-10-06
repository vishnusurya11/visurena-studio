"""A bed span must point into the cut AT THE PLAN, never first at assemble:
ep18's signed plan carried a bed on a shot the cut dropped, and
episode_bed.in_cut raised hours later, mid-assemble ('shot 22 cut, and its
music bed removed' by hand)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from studio.episode_spec import Episode
from tests.test_episode_spec import episode


def doc_with(beds, omit=None):
    data = episode().model_dump()
    data["beds"] = beds
    if omit is not None:
        data["omit"] = omit
    return data


def test_a_span_past_the_last_shot_is_refused():
    data = doc_with([{"from_shot": len(episode().shots), "tone": "plain"}])
    with pytest.raises(ValidationError, match="bed span from_shot"):
        Episode(**data)


def test_a_span_on_an_omitted_shot_with_a_later_cut_shot_passes():
    data = doc_with([{"from_shot": 2, "tone": "plain"}], omit=[2])
    assert Episode(**data).beds[0]["from_shot"] == 2


def test_a_span_with_no_cut_shot_at_or_after_it_is_refused():
    last = len(episode().shots) - 1
    data = doc_with([{"from_shot": last, "tone": "plain"}], omit=[last])
    with pytest.raises(ValidationError, match="bed span from_shot"):
        Episode(**data)


def test_spans_out_of_story_order_are_refused():
    data = doc_with([{"from_shot": 5, "tone": "tense"}, {"from_shot": 2, "tone": "plain"}])
    with pytest.raises(ValidationError, match="bed span from_shot"):
        Episode(**data)


def test_a_span_without_an_int_from_shot_is_refused():
    with pytest.raises(ValidationError, match="bed span from_shot"):
        Episode(**doc_with([{"tone": "plain"}]))
