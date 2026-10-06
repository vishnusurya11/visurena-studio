"""L8's two-handed cure: a THING's gait is swapped for its own motion verb
(fire spreads, never 'climbs at a normal walking pace'), a PERSON's gait keeps
its verb and gains a pace -- and L23's inverse strips the pace an earlier blind
injection glued to a thing.  The swap trusts only the strict PERSON regex plus
a noun allowlist: ro.is_person's capitalised fallback is the known mis-router
(ep09: the sun lifted at a normal walking pace)."""
from __future__ import annotations

from studio import episode_ref_official as ro
from studio import plan_cures as pc


def doc_of(**fields) -> dict:
    shot = {"index": 0, "frame": "", "motion": "", "at_rest": "", "end": ""}
    shot.update(fields)
    return {"shots": [shot], "setups": {}}


def test_a_fires_climb_becomes_a_spread_with_no_pace_appended():
    doc = pc.pace_words(pc.figurative_gaits(doc_of(motion="the fire climbs the stair rail")))
    said = doc["shots"][0]["motion"]
    assert said == "the fire spreads the stair rail"
    assert not any(p in said.lower() for p in ro.PACE)


def test_a_persons_climb_is_untouched_by_the_swap_then_paced():
    doc = pc.figurative_gaits(doc_of(motion="Watson climbs the stair"))
    assert doc["shots"][0]["motion"] == "Watson climbs the stair"
    doc = pc.pace_words(doc)
    assert "at a walking pace" in doc["shots"][0]["motion"]


def test_a_non_person_subject_outside_the_allowlist_is_left_for_the_llm():
    doc = pc.figurative_gaits(doc_of(motion="the piston walks along its track"))
    assert doc["shots"][0]["motion"] == "the piston walks along its track"


def test_drop_thing_pace_removes_a_pace_glued_to_the_curtain():
    doc = pc.drop_thing_pace(doc_of(motion="the curtain lifts at a normal walking pace"))
    assert doc["shots"][0]["motion"].strip() == "the curtain lifts"


def test_drop_thing_pace_keeps_a_persons_pace():
    doc = pc.drop_thing_pace(doc_of(motion="he walks to the door at a normal walking pace"))
    assert "at a normal walking pace" in doc["shots"][0]["motion"]


def test_swap_and_strip_are_both_idempotent():
    doc = doc_of(motion="the fire climbs the lane at a normal walking pace")
    once = pc.drop_thing_pace(pc.figurative_gaits(doc))
    said = once["shots"][0]["motion"]
    twice = pc.drop_thing_pace(pc.figurative_gaits(once))
    assert twice["shots"][0]["motion"] == said
    assert "spreads" in said and "pace" not in said
