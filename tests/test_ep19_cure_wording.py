"""ep19 (2026-10-06): three cures wrote heads and phrases no reader would.
(1) `cell_aims` harvested the parenthetical tag a plan puts on a person -- "the
narrator (grey eyes, cream flannel shirt)" -- so the move cure wrote "tilts up
from the eyes to the flags" and "pushes in toward the eyes" (shots 0, 1), and
offered `follow` on scenery: "tracks behind the terrace" (shot 10).
(2) `_rename_first` matched a bare noun whose article stood one word earlier,
and wrote "the opened the Martian cylinder" (shots 8, 9, 11).
(3) `_continuation` stripped "The camera" and kept "The", so an end read
"The cranes up one whole yard above ..." (shot 5).  $0, no model."""
from __future__ import annotations

from collections import Counter

from studio import move_rebalance as mr
from studio import plan_cures as pc

SCULLERY = {"props": ["rain_water_pump", "copper", "meat_chopper", "broken_crockery"]}
PIT = {"props": ["martian_cylinder", "handling_machine", "digging_mechanism", "green_vapour",
                 "fighting_machine", "martian"]}

SHOT_0 = {
    "index": 0, "size": "wide", "setup": "scullery_wake", "faces": ["unnamed_first_person_narrator"],
    "at_rest": "THE FOCUS OF THE PICTURE IS the narrator (grey eyes, cream flannel shirt) lying on the "
               "stone flags at CENTER; the pump stands at the LEFT edge, the copper fills the far LEFT "
               "corner, broken crockery surrounds him from the lower LEFT edge to the lower RIGHT edge, "
               "and the kitchen doorway occupies the RIGHT edge.",
    "frame": "Wide scullery view: the narrator lifts from the stone flags while the kitchen doorway glows "
             "at the RIGHT edge, the pump stands at the LEFT edge, and broken crockery marks the CENTER "
             "foreground between both lower edges.",
    "motion": "The camera tracks laterally one whole yard from the kitchen doorway past the copper across "
              "the whole shot; the narrator lifts his shoulders from the flags; plaster dust falls from "
              "the ceiling."}

SHOT_1 = {
    "index": 1, "size": "medium_close", "setup": "scullery_wake",
    "faces": ["unnamed_first_person_narrator", "curate"],
    "at_rest": "THE FOCUS OF THE PICTURE IS the narrator (grey eyes, cream flannel shirt), his head a "
               "quarter of the frame's height at CENTER; the pump sits behind his LEFT shoulder, the "
               "kitchen doorway fills the RIGHT edge, the triangular opening glows within it, the curate "
               "lies beyond it, and broken crockery marks the lower frame from the LEFT edge to the "
               "RIGHT edge.",
    "frame": "Medium-close view of the narrator crossing toward the curate at the kitchen doorway, with "
             "the pump at the LEFT edge, the triangular opening at the RIGHT edge, and broken crockery "
             "across the lower frame.",
    "motion": "The camera pans from the pump across to the triangular opening one whole frame across the "
              "whole shot; the narrator turns his head toward the opening; grey light trembles over the "
              "flags."}

SHOT_10 = {
    "index": 10, "size": "medium", "setup": "pit_work", "faces": [],
    "at_rest": "THE FOCUS OF THE PICTURE IS the digging-machine on the eastern terrace at the CENTER "
               "RIGHT; the Martian handling-machine stands beside the opened the Martian cylinder at the "
               "LEFT edge, laid rods form a shelf at the RIGHT edge, the fighting-machine marks the far "
               "rim at the TOP edge, and green vapour hangs above the clay.",
    "frame": "Medium view of the digging-machine circling the eastern terrace, with the Martian "
             "handling-machine beside the opened the Martian cylinder at the LEFT edge, rods along the "
             "RIGHT shelf, and the fighting-machine on the far rim.",
    "motion": "The camera pans from the Martian handling-machine across to the digging-machine one whole "
              "frame across the whole shot; the digging-machine excavates the eastern terrace; green "
              "vapour jets pulse from its sides."}


def heads_of(shot: dict, setup: dict) -> list[str]:
    return mr.candidates(shot, Counter(), "", "", setup, 5.0)


# ---- (1) aim nouns ------------------------------------------------------------------

def test_a_parenthetical_tag_is_never_an_aim():
    for shot in (SHOT_0, SHOT_1):
        aims = mr.cell_aims(shot, SCULLERY)
        assert not {"eyes", "shirt"} & set(aims), aims


def test_ep19_shots_0_and_1_never_aim_at_the_eyes():
    for shot in (SHOT_0, SHOT_1):
        assert not [h for h in heads_of(shot, SCULLERY) if "eyes" in h or "shirt" in h]


def test_a_layout_word_is_never_an_aim():
    for shot, setup in ((SHOT_0, SCULLERY), (SHOT_1, SCULLERY), (SHOT_10, PIT)):
        aims = set(mr.cell_aims(shot, setup))
        assert not aims & {"edge", "corner", "height", "it", "beyond", "foreground"}, aims


def test_a_possessed_body_part_is_never_an_aim():
    """ep19 shot 1's diagnosis: "tilts up from the narrator to the shoulder",
    harvested from "the pump sits behind his LEFT shoulder"."""
    assert "shoulder" not in mr.cell_aims(SHOT_1, SCULLERY)


def test_follow_is_never_offered_on_scenery():
    assert not [h for h in heads_of(SHOT_10, PIT) if "tracks behind" in h]


def test_follow_tracks_a_figure_from_the_shots_faces():
    follows = [h for h in heads_of(SHOT_0, SCULLERY) if "tracks behind" in h]
    assert follows and all("tracks behind the narrator" in h for h in follows)


def test_figure_aims_are_the_faces_named_at_rest():
    assert mr.figure_aims(SHOT_1) == ["narrator", "curate"]
    assert mr.figure_aims(SHOT_10) == []


# ---- (2) a renamed noun under an earlier article -------------------------------------

EP19_SOURCE = "the curate pulls the narrator back from the slit while the opened cylinder remains beyond"


def test_the_inserted_name_never_doubles_an_earlier_article():
    out, hit = pc._rename_first(EP19_SOURCE, "cylinder", "the Martian cylinder", [])
    assert hit and "the opened Martian cylinder remains" in out
    assert "the opened the" not in out


def test_a_quantified_noun_drops_the_names_article():
    out, _ = pc._rename_first("three long arms lift a plate", "arms", "the Martian arms", [])
    assert out == "three long Martian arms lift a plate"


def test_an_adjacent_article_is_still_replaced_whole():
    out, _ = pc._rename_first("vapour crosses the cylinder", "cylinder", "the Martian cylinder", [])
    assert out == "vapour crosses the Martian cylinder"


def test_a_bare_noun_after_a_preposition_keeps_the_names_article():
    out, _ = pc._rename_first("vapour lifts from cylinder", "cylinder", "the Martian cylinder", [])
    assert out == "vapour lifts from the Martian cylinder"


# ---- (3) the continuation keeps its subject ------------------------------------------

EP19_MOTION = ("The camera cranes up one whole yard above the north rubble edge across the whole "
               "shot; vapour lifts from the opened the Martian cylinder; dust runs down the terraced wall.")


def test_the_continuation_keeps_the_camera():
    said = pc._continuation(EP19_MOTION)
    assert said.startswith("The camera cranes up one whole yard above the north rubble edge")
    assert not said.startswith("The cranes")
    assert "continues to the last frame of the shot" in said


def test_the_continuation_drops_the_heads_own_duration():
    said = pc._continuation("The camera pushes in toward the gate across the whole shot; dust drifts")
    assert said == "The camera pushes in toward the gate and continues to the last frame of the shot."


def test_a_head_without_the_camera_falls_back_to_the_cameras_move():
    assert pc._continuation("Dust drifts over the gate") == pc.CAMERA_CONTINUES
