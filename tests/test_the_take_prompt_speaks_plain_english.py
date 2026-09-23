"""Three small grammar faults the prompt-builder audit counted in rendered prompts.

2026-09-23, over 99 rendered take prompts:
- "the camera is riseing" in 19, "the camera is keeping through the last
  frame" in 22 (calm() turns "holds" into "keeps");
- a 13-year-old boy called "this man" in 4 (ep06 T08, ep07 T09, ep08 T05, T19);
- a cast tag running on into the next verb: "long white apron to the shin
  standing at the side gate" (ep09 T01).
"""
import json

from studio import cast_refs
from studio import episode_ref_official as ro


def test_every_camera_verb_has_a_real_gerund():
    assert ro.gerund("rises from the road") == "rising from the road"
    assert ro.gerund("descends to the gate") == "descending to the gate"


def test_a_camera_that_keeps_its_frame_arrives_without_moving():
    seg = {"end": 5, "motion": "The camera keeps a static frame; he looks up", "end_frame": ""}
    assert "keeping through" not in ro.arrival_clause(seg)


def test_a_young_character_is_a_boy_not_a_man(monkeypatch):
    monkeypatch.setattr(ro, "YOUNG", {"unnamed_newspaper_boy"})
    assert ro.noun("unnamed_newspaper_boy") == "boy"
    assert ro.noun("unnamed_milkman") == "man"


def test_the_age_is_read_from_the_row():
    assert ro.age_of("Boy of 13, small and sharp-faced") == 13
    assert ro.age_of("Man of 34, 5 ft 10 in") == 34
    assert ro.age_of("A lean clean-shaven man") is None


def test_a_cast_tag_closes_itself(tmp_path, monkeypatch):
    monkeypatch.setattr(cast_refs, "row", lambda book, who: {
        "physical": "Thick chestnut walrus moustache. Wearing: long white apron to the shin"})
    got = cast_refs.tag(tmp_path, "unnamed_milkman", "the milkman",
                        ["Thick chestnut walrus moustache", "long white apron to the shin"])
    assert got == "the milkman (thick chestnut walrus moustache, long white apron to the shin)"
