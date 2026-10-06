"""L21's cure: a block's last sentence is the last thing the model hears about
motion, and episode 9 closed 29 of 30 blocks on 'the log house stands twice its
size along the left edge'.  The cure deletes the layout-final sentence when an
earlier sentence already moves, else closes on the motion head's own
'continues to the last frame' clause -- the one closing form the L11 comment
names legal."""
from __future__ import annotations

from studio import episode_ref_official as ro
from studio import plan_cures as pc

LAYOUT_END = "The log house stands twice its size along the left edge."


def doc_of(end: str, motion: str = "") -> dict:
    return {"shots": [{"index": 4, "frame": "", "motion": motion, "at_rest": "", "end": end}],
            "setups": {}}


def test_a_layout_final_sentence_after_a_movement_is_deleted():
    doc = pc.arrival_ends(doc_of("The camera settles on the porch. " + LAYOUT_END), [4])
    assert doc["shots"][0]["end"] == "The camera settles on the porch."


def test_with_no_prior_movement_the_motion_head_continues_to_the_last_frame():
    motion = "The camera pushes in toward the gate across the whole shot; dust drifts"
    doc = pc.arrival_ends(doc_of(LAYOUT_END, motion), [4])
    said = doc["shots"][0]["end"]
    assert "continues to the last frame of the shot" in said
    assert "pushes in toward the gate" in said


def test_a_locked_off_motion_falls_back_to_the_cameras_move_clause():
    doc = pc.arrival_ends(doc_of(LAYOUT_END, "The camera holds a locked-off frame"), [4])
    assert "The camera's move continues to the last frame of the shot" in doc["shots"][0]["end"]


def test_the_cured_end_passes_l21_on_a_minimal_built_block():
    motion = "The camera pushes in toward the gate across the whole shot"
    doc = pc.arrival_ends(doc_of(LAYOUT_END, motion), [4])
    text = ("detailed_description:\n[Shot 1] From 00:00 to 00:05. "
            "He steps to the gate. " + doc["shots"][0]["end"])
    assert ro.l21_arrival(text, {}) == []


def test_an_end_with_no_layout_final_sentence_is_untouched():
    doc = pc.arrival_ends(doc_of("The camera settles on the porch."), [4])
    assert doc["shots"][0]["end"] == "The camera settles on the porch."


# ---- ep19 shot 5 (2026-10-05): the cure measures through the builder's arrival --

EP19_MOTION = ("The camera cranes up one whole yard above the north rubble edge across the "
               "whole shot; vapour lifts from the opened the Martian cylinder; dust runs down "
               "the terraced wall.")
EP19_END = ("The cranes up one whole yard above the north rubble edge across the whole shot "
            "continues to the last frame of the shot.")
"""ep19 shot 5's real text: an earlier round's continuation copied the motion
head, 'edge' and all, so the builder lent "...rubble edge..." as the noun now
in frame and L21 fired again; the cure rewrote the same sentence -- a fixed point."""


def built_block(end: str, motion: str) -> str:
    """The block the take builder closes: its own arrival clause, from `end`."""
    arrival = ro.arrival_clause({"end_frame": end, "motion": motion, "end": 15.0})
    return ("detailed_description:\n[Shot 1] From 00:00 to 00:15. "
            "Dust runs down the terraced wall. " + arrival)


def test_ep19_shot_5_fails_l21_as_built():
    assert ro.l21_arrival(built_block(EP19_END, EP19_MOTION), {})


def test_ep19_shot_5_is_cured_and_the_built_block_passes_l21():
    doc = pc.arrival_ends(doc_of(EP19_END, EP19_MOTION), [4])
    end = doc["shots"][0]["end"]
    assert end != EP19_END and not ro.LAYOUT.search(end)
    assert ro.l21_arrival(built_block(end, EP19_MOTION), {}) == []


def test_a_cut_end_is_cured_the_same_way():
    doc = doc_of("The camera settles on the porch.", EP19_MOTION)
    doc["shots"][0]["cuts"] = [{"end": EP19_END, "motion": EP19_MOTION}]
    cured = pc.arrival_ends(doc, [4])["shots"][0]["cuts"][0]["end"]
    assert ro.l21_arrival(built_block(cured, EP19_MOTION), {}) == []
