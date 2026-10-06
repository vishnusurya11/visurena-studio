"""The mechanical cure for a dangling bed span: keep only spans that point
into the cut, in story order; an emptied list is legal (one plain span end to
end).  The dispatcher routes the contract's refusal text to it."""
from __future__ import annotations

from studio import plan_cures as pc
from studio.episode_spec import Episode
from tests.test_episode_spec import episode


def test_the_dangling_span_is_dropped_and_survivors_sorted():
    doc = {"shots": [{"index": i} for i in range(6)], "omit": [5],
           "beds": [{"from_shot": 5, "tone": "tense"},        # no cut shot at or after it
                    {"from_shot": 4, "tone": "dark"},
                    {"from_shot": 0, "tone": "plain"},
                    {"from_shot": 9, "tone": "plain"},        # past the last shot
                    {"from_shot": "two", "tone": "plain"}]}   # not an int
    cured = pc.clamp_beds(doc)
    assert cured["beds"] == [{"from_shot": 0, "tone": "plain"}, {"from_shot": 4, "tone": "dark"}]


def test_empty_beds_and_no_beds_both_survive():
    assert pc.clamp_beds({"shots": [{"index": 0}], "beds": []})["beds"] == []
    assert pc.clamp_beds({"shots": [{"index": 0}]})["beds"] == []


def test_the_cured_doc_validates_as_an_episode():
    data = episode().model_dump()
    data["beds"] = [{"from_shot": len(data["shots"]) + 3, "tone": "plain"},
                    {"from_shot": 3, "tone": "plain"}, {"from_shot": 1, "tone": "tense"}]
    Episode(**pc.clamp_beds(data))


def test_the_dispatcher_routes_the_refusal_to_clamp_beds():
    assert pc.cure_for("CONTRACT: beds :: bed span from_shot 22 has no cut shot at or after it") == "clamp_beds"
    assert pc.cure_for("bed span from_shot 9 names a shot outside the plan") == "clamp_beds"
