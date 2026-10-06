"""The plan cure table (2026-10-01): 97% of ep14-15's plan hours were paid
whole-plan rewrites refused by rules whose cures are TEMPLATE ARITHMETIC --
every repair of the ep15 session, codified.  A mechanical fault never costs a
writer call again; `plan_repair` loops plan_check -> cures until only creative
faults remain.  Verdict: docs/audit/2026-10-01_plan_hours_debate.md."""
from __future__ import annotations

from studio import plan_cures as pc


def doc_of(**over):
    base = {
        "shots": [
            {"index": 0, "setup": "yard", "size": "wide", "frame": "The yard.",
             "at_rest": "The pump stands at the left edge.", "motion": "The camera holds a locked-off frame",
             "beat_s": 0.3, "coda_s": 0.2, "faces": [], "extras": 0},
            {"index": 1, "setup": "yard", "size": "medium_close", "frame": "A man.",
             "at_rest": "The man stands at the centre by the gate.", "motion": "The camera holds a locked-off frame",
             "beat_s": 0.3, "coda_s": 0.2, "faces": ["the_man"], "extras": 0},
        ],
        "lines": [{"index": 0, "kind": "narration", "speaker": "narrator", "text": "Words.", "shot": 0}],
        "setups": {"yard": {"described": "A stone yard in hard morning sunlight, forty words of room.",
                            "crowd": "", "props": []}},
    }
    base.update(over)
    return base


def test_renumber_remaps_lines_and_beds():
    doc = doc_of()
    doc["shots"][0]["index"], doc["shots"][1]["index"] = 3, 7
    doc["lines"][0]["shot"] = 7
    doc["beds"] = [{"from_shot": 3, "tone": "plain"}]
    out = pc.renumber(doc)
    assert [s["index"] for s in out["shots"]] == [0, 1]
    assert out["lines"][0]["shot"] == 1
    assert out["beds"][0]["from_shot"] == 0


def test_light_direction_is_templated_from_the_setups_own_words():
    doc = doc_of()
    out = pc.light_directions(doc)
    said = out["setups"]["yard"]["described"]
    assert pc.has_light_direction(said), said
    # idempotent: a second pass adds nothing
    assert pc.light_directions(out)["setups"]["yard"]["described"] == said


def test_head_fraction_lands_on_every_close_size():
    out = pc.head_fractions(doc_of())
    assert "a third of the frame's height" in out["shots"][1]["at_rest"]
    assert "frame's height" not in out["shots"][0]["at_rest"]      # a wide needs none


def test_a_gait_without_a_pace_gets_one():
    doc = doc_of()
    doc["setups"]["yard"]["crowd"] = "One man climbs the lane; another walks the wall."
    out = pc.pace_words(doc)
    crowd = out["setups"]["yard"]["crowd"]
    assert crowd.count("at a walking pace") == 2
    assert pc.pace_words(out)["setups"]["yard"]["crowd"] == crowd  # idempotent


def test_the_button_breath_is_restored():
    doc = doc_of()
    doc["shots"][0]["beat_s"] = 0.3                                # penultimate
    out = pc.button_beat(doc)
    assert out["shots"][0]["beat_s"] >= 1.0


def test_repeated_heads_are_swapped_to_a_catalog_move_that_aims_at_the_cell():
    doc = doc_of()
    doc["shots"][0]["motion"] = "The camera tracks sideways to the right, past the pump"
    doc["shots"][1]["motion"] = "The camera tracks sideways to the right, past the gate"
    out = pc.vary_heads(doc, [1])
    head = out["shots"][1]["motion"].split(";")[0]
    assert "tracks sideways" not in head
    assert any(w in out["shots"][1]["at_rest"].lower() for w in pc.aim_of_head(head))


def test_ghost_props_are_dropped_against_the_registry():
    doc = doc_of()
    doc["setups"]["yard"]["props"] = ["pump_handle", "bay_window"]
    out = pc.legal_props(doc, legal={"pump_handle"})
    assert out["setups"]["yard"]["props"] == ["pump_handle"]


def test_the_series_fields_are_pinned():
    doc = doc_of()
    doc["look"], doc["style"], doc["aspect"] = "An invented fourteen word look that the writer made up on its own today", "x", "9:16"
    out = pc.pin_series(doc, look="Angular stylised 3D animation, brush-stroke texture",
                        aspect="1:1")
    assert out["look"] == "Angular stylised 3D animation, brush-stroke texture"
    assert out["aspect"] == "1:1" and out["style"] == ""


def test_the_dispatcher_names_a_cure_for_every_mechanical_family():
    rows = [
        "CONTRACT : shots are numbered 0..n-1 in cut order",
        "G-LIGHT: setup 'yard': `described` names no light source with a direction",
        "G-SIZE shot 1: a medium_close whose at_rest names no head fraction",
        "L8 NO PACE [Shot 1]: a walk, climb or ride with no pace named",
        "CONTRACT : the shot before the button names a beat of >= 1.0 s of silence",
        "G-MOVES shot 1: 'track_lateral' follows the same move on shot 0 (twice running)",
        "G-STILL shot 1: 'low_angle' held with no move renders still",
        "G-AIM shot 1: the camera aims at 'Martian', which the cell (at_rest) does not hold",
        "CONTRACT : projects to 119 s; an episode is 120-174 s",
        "G-SETUP setup yard: projected seconds of picture in one setup, measured 50.2 against 50.0",
        "ONE PER TAKE : [(4, 5)]",
        "G-FIRSTFRAME plan: median frame-edge per shot is under the floor, measured 2.0 against 3",
    ]
    for row in rows:
        assert pc.cure_for(row) is not None, row
    assert pc.cure_for("G-STORY plan: narration-only run in projected seconds") is None  # creative: the writer's


def test_camera_rows_dispatch_to_rebalance_and_subject_rows_stay_the_writers():
    """AREA 2 (2026-10-05): every camera-head family routes to the catalog-wide
    rebalance -- including G-ANCHOR and M2, which matched nothing on ep18 and
    bounced to the writer as hand edits.  M9/M10 accuse the SUBJECT clauses
    and remain the writer's."""
    rows = [
        "G-MOVES plan: distinct catalog moves over 23 shots, measured 6 against 8",
        "G-STILL shot 7: 'tilt_down' is a move H3 ignores; use 'pull_reveal'",
        "G-AIM shot 14: the camera aims at 'ruin', which the cell (at_rest) does not hold",
        "G-ANCHOR shot 3: a sideways truck or pan on a medium_close of a person 'leans on'",
        "M2 shot 12: the head names no camera move. Open with one, before the first semicolon",
    ]
    for row in rows:
        assert pc.cure_for(row) == "rebalance_heads", row
    assert pc.cure_for("M9 shot 4: the tail clause names no moving thing") is None
    assert pc.cure_for("M10 shot 2: the motion brings in what at_rest already holds") is None
