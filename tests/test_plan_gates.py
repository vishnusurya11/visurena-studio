"""The plan gates: free checks on plan.json before anything is drawn.

Calibrated on the four fixtures the owner judged (tests/fixtures/episodes):
ep05 and ep07 looked right, ep08 and ep09 looked worse.  Every threshold in
`studio.plan_gates` quotes the numbers measured here; a gate that refuses ep05
or ep07 on these files is not the gate."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import plan_gates as pg
from studio.episode_spec import Episode

FIXTURES = Path(__file__).parent / "fixtures" / "episodes"


def load(ep: str) -> Episode:
    return Episode(**json.loads((FIXTURES / f"ep{ep}_plan.json").read_text(encoding="utf-8")))


def of(faults: list[str], gate: str) -> list[str]:
    return [f for f in faults if f.startswith(gate + " ")]


# ---- a synthetic plan that passes every gate ---------------------------------

NARRATION = ("The lamp stands on the table and the fog stands at the glass while "
             "he reads the paper.")                                     # 18 words
DIALOGUE = ("You have the ring, and the man who lost it will come for it before "
            "the clock strikes.")                                       # 18 words
DESCRIBED = (
    "The sitting room at 221B Baker Street at night, November 1881: two tall sash "
    "windows curtained in dark red on the street side, a black marble mantelpiece "
    "with a coal fire low and red in the grate, a round mahogany table under a white "
    "cloth with the remains of dinner, two armchairs turned to the fire, a violin "
    "case open on the sideboard, gas brackets either side of the mirror turned low, "
    "a Persian slipper of tobacco on the mantel shelf, the wallpaper a dark green "
    "stripe, and a thick Turkey carpet worn pale between the door and the hearth.")
GEOMETRY = (
    "The mantelpiece stands along the LEFT edge of the frame at the height of a "
    "standing man's shoulder. The curtained windows fill the RIGHT third from the "
    "table's edge to the TOP edge. The round table sits in the BOTTOM half at the "
    "CENTRE with the two armchairs between it and the fire, and the door stands "
    "at the far LEFT corner beyond the mantel, the height of a hand.")
AT_REST = (
    "Holmes stands at the LEFT third of the frame with his shoulder against the "
    "mantel edge, the fire small and red at the BOTTOM RIGHT corner, the window a "
    "dark rectangle at the TOP CENTRE, the table's near corner cutting the bottom "
    "edge, and his head half the frame's height with the gas bracket above it.")

HEAD = {"insert": "The camera pushes in on the ring across the whole shot, travelling a hand's breadth",
        "close": "The camera pushes in on his face across the whole shot, travelling a hand's breadth",
        "medium_close": "The camera tracks a hand's breadth to the left across the whole shot",
        "medium": "The camera pushes in on the table across the whole shot, travelling a long stride",
        "full": "The camera pulls back from the hearth across the whole shot, travelling two long strides",
        "wide": "The camera pushes in from the door across the whole shot, travelling two long strides"}
SIZES = ["wide", "medium", "insert", "close", "medium_close", "full", "insert", "medium", "close",
         "insert", "close", "medium", "medium", "insert", "medium_close", "wide", "medium",
         "insert", "medium", "close"]
DIALOGUE_AT = {3: "sherlock_holmes", 10: "sherlock_holmes", 19: "g_lestrade"}
SILENT = 18


def shot(i: int, size: str) -> dict:
    faces = [DIALOGUE_AT[i]] if i in DIALOGUE_AT else (["sherlock_holmes"] if size in pg.CLOSE_SIZES else [])
    section = "hook" if i == 0 else "turn" if i == 12 else "button" if i == 19 else "setup"
    motion = HEAD[size] + "; his hand comes up to his chin; his head turns toward the window."
    if i == 12:
        motion = HEAD[size] + "; Holmes catches Watson by the wrist; Watson's hand opens."
    return {"index": i, "section": section, "setup": "hearth", "size": size, "faces": faces,
            "frame": f"{size.replace('_', ' ').title()} on Holmes at the mantel, the bottle-green "
                     f"velvet jacket open over his white shirt.",
            "motion": motion, "camera": "at the height of a seated man's eye, two strides inside the door",
            "at_rest": AT_REST, "beat_s": 1.5 if i == SILENT else 0.0}


def synthetic(**over) -> dict:
    """A twenty-shot plan that clears every gate; `over` replaces top-level keys."""
    shots = [shot(i, size) for i, size in enumerate(SIZES)]
    lines, k = [], 0
    for i in range(len(shots)):
        if i == SILENT:
            continue
        if i in DIALOGUE_AT:
            lines.append({"index": k, "kind": "dialogue", "speaker": DIALOGUE_AT[i], "text": DIALOGUE, "shot": i})
        else:
            lines.append({"index": k, "kind": "narration", "speaker": "john_watson", "text": NARRATION, "shot": i})
        k += 1
    plan = {"number": 99, "title": "Synthetic", "protagonist": "sherlock_holmes",
            "setups": {"hearth": {"described": DESCRIBED, "geometry": GEOMETRY,
                                  "cast": ["sherlock_holmes", "john_watson", "g_lestrade"]}},
            "shots": shots, "lines": lines}
    plan.update(over)
    return plan


def with_shots(edit) -> Episode:
    plan = synthetic()
    for s in plan["shots"]:
        edit(s)
    return Episode(**plan)


def test_the_synthetic_plan_clears_every_gate():
    assert pg.faults(Episode(**synthetic())) == []


# ---- G-FIRSTFRAME ------------------------------------------------------------

def test_edge_tokens_count_frame_placements_and_not_a_left_hand():
    assert pg.edge_tokens("the window at the TOP CENTRE, his left hand on the table's edge, a third") == 4


def test_median_is_the_middle_value():
    assert pg.median_of([1, 50, 60]) == 50.0
    assert pg.median_of([]) == 0.0


def test_a_single_terse_insert_does_not_fail_firstframe():
    def terse(s):
        if s["index"] == 2:
            s["at_rest"] = "The ring lies on the cloth."
    assert of(pg.faults(with_shots(terse)), "G-FIRSTFRAME") == []


def test_terse_at_rest_across_the_plan_fails_on_the_median():
    def terse(s):
        s["at_rest"] = "Holmes stands at the mantel with the fire behind him at the LEFT edge."
    got = of(pg.faults(with_shots(terse)), "G-FIRSTFRAME")
    assert any("at_rest" in f and f"against {pg.AT_REST_WORDS}" in f for f in got)
    assert any("frame-edge" in f and f"against {pg.EDGE_TOKENS}" in f for f in got)


def test_a_thin_setup_fails_described_and_geometry():
    plan = synthetic()
    plan["setups"]["hearth"].update(described="A room with a fire.", geometry="The fire at the LEFT.")
    got = of(pg.faults(Episode(**plan)), "G-FIRSTFRAME")
    assert any("described" in f and "measured 5.0" in f for f in got)
    assert any("geometry" in f and "measured 5.0" in f for f in got)


def test_firstframe_regression_on_the_fixtures():
    for ep in ("05", "07", "08"):
        assert of(pg.faults(load(ep)), "G-FIRSTFRAME") == [], ep
    got = of(pg.faults(load("09")), "G-FIRSTFRAME")
    assert any("at_rest" in f and "measured 15.0 against 40" in f for f in got)
    assert any("frame-edge" in f and "measured 2.0 against 3" in f for f in got)
    assert any("described" in f and "measured 54.0 against 90" in f for f in got)
    assert any("geometry" in f and "measured 42.0 against 60" in f for f in got)


# ---- G-VARIETY ---------------------------------------------------------------

def test_inserts_needed_is_one_per_six_shots_rounded_up():
    assert pg.inserts_needed(25) == 5
    assert pg.inserts_needed(30) == 5
    assert pg.inserts_needed(24) == 4


def test_a_plan_with_no_inserts_fails():
    got = of(pg.faults(with_shots(lambda s: s.update(size="medium") if s["size"] == "insert" else None)),
             "G-VARIETY")
    assert any("insert" in f and "measured 0 against 4" in f for f in got)


def test_a_two_shot_written_at_medium_close_is_mislabelled():
    assert pg.mislabelled_two_shot("Medium two-shot at the mustang's head: ...", "medium_close")
    assert pg.mislabelled_two_shot("Two-shot of the pair", "close")
    assert not pg.mislabelled_two_shot("Medium two-shot of the pair", "medium")
    assert not pg.mislabelled_two_shot("Close on Lucy's face", "close")


def test_too_many_closes_on_one_face_fails():
    def all_lucy(s):
        if s["size"] in pg.CLOSE_SIZES and s["index"] not in DIALOGUE_AT:
            s["faces"] = ["lucy"]
    plan = synthetic()
    for s in plan["shots"]:
        all_lucy(s)
        if s["index"] in (0, 1, 5, 7):
            s.update(size="close", faces=["lucy"], motion=HEAD["close"] + "; a; b")
    got = of(pg.faults(Episode(**plan)), "G-VARIETY")
    assert any("'lucy'" in f and f"against {pg.MAX_FACE_CLOSES}" in f for f in got)


def test_wide_and_full_share_over_a_quarter_fails():
    plan = synthetic()
    for s in plan["shots"]:
        if s["size"] == "medium":
            s.update(size="wide", motion=HEAD["wide"] + "; a; b")
    got = of(pg.faults(Episode(**plan)), "G-VARIETY")
    assert any("wide+full" in f and f"against {pg.MAX_WIDE_SHARE}" in f for f in got)


def test_variety_regression_on_the_fixtures():
    for ep in ("05", "07"):
        assert of(pg.faults(load(ep)), "G-VARIETY") == [], ep
    ep08 = of(pg.faults(load("08")), "G-VARIETY")
    assert any("insert" in f and "measured 3 against 5" in f for f in ep08)
    assert any("wide+full" in f and "measured 0.37" in f for f in ep08)
    ep09 = of(pg.faults(load("09")), "G-VARIETY")
    assert any("insert" in f and "measured 0 against 5" in f for f in ep09)
    assert any("wide+full" in f and "measured 0.33" in f for f in ep09)
    assert any("'lucy_ferrier'" in f and "measured 9 against 6" in f for f in ep09)
    assert sorted(int(f.split("shot ")[1].split(":")[0]) for f in ep09 if "two-shot" in f) == [7, 17, 27]


# ---- G-MOVE ------------------------------------------------------------------

def test_amount_reads_count_times_unit_from_the_head_clause():
    assert pg.amount("The camera pushes in on his face across the whole shot, travelling a hand's breadth") == 1.0
    assert pg.amount("The camera tracks a hand's breadth to the left across the whole shot") == 1.0
    assert pg.amount("The camera pulls back off the valley across the whole shot, travelling three long strides") == 30.0
    assert pg.amount("The camera tilts down off the peaks, travelling a head's height") == pg.AMPLITUDE["head's height"]
    assert pg.amount("The camera holds level with the hub") == 0.0
    assert pg.amount("Holmes draws the far chair back and sits down") is None
    assert pg.amount("The old woman comes forward at a walking pace") is None


def test_the_fault_quotes_the_amount_in_either_shape():
    assert pg.travel_phrase("The camera tracks a long stride to the left across the whole shot") == "a long stride"
    assert pg.travel_phrase("The camera pushes in on Lucy's face across the whole shot, travelling a head's height") == "a head's height"
    assert "'a long stride' on a full over a crowd of 20" in [f for f in pg.faults(load("08")) if "shot 22" in f][0]


def test_figures_counts_people_not_waggons_or_mules():
    assert pg.figures("Forty immigrants kneel along the rock, and twelve canvas-topped waggons stand in a line") == 40
    assert pg.figures("Thirty pack mules file west with six drivers at their heads, and four Indians lead ponies") == 10
    assert pg.figures("a dozen more mounted men sit their horses") == 12
    assert pg.figures("one boy with a milk can walks the lane") == 1
    assert pg.figures("") == 0


def test_a_head_height_push_on_a_close_is_too_big():
    def big(s):
        if s["size"] == "close":
            s["motion"] = s["motion"].replace("a hand's breadth", "a head's height")
    got = of(pg.faults(with_shots(big)), "G-MOVE")
    assert len(got) == SIZES.count("close")
    assert all(f"against {pg.CAP['close']}" in f for f in got)


def test_a_forearm_on_a_close_passes_as_it_did_in_episode_seven():
    def forearm(s):
        if s["size"] == "close":
            s["motion"] = s["motion"].replace("a hand's breadth", "a forearm")
    assert of(pg.faults(with_shots(forearm)), "G-MOVE") == []


def test_a_wide_over_a_crowd_of_six_holds_or_moves_a_short_stride():
    plan = synthetic()
    plan["setups"]["hearth"]["crowd"] = "eight or nine men in top hats two deep at the counter"
    got = of(pg.faults(Episode(**plan)), "G-MOVE")
    assert len(got) == SIZES.count("wide") + SIZES.count("full")
    assert all("crowd" in f and f"against {pg.CROWD_CAP}" in f for f in got)
    plan["setups"]["hearth"]["crowd"] = "two men at the counter"
    assert of(pg.faults(Episode(**plan)), "G-MOVE") == []


def test_travel_per_second_is_capped():
    plan = synthetic()
    s = plan["shots"][0]
    s["motion"] = HEAD["wide"].replace("two long strides", "four long strides") + "; a; b"
    plan["lines"][0]["text"] = "Fog."                     # 0.83 s under four long strides
    for k in range(1, 6):                                 # keep the runtime over 120 s
        plan["shots"][k]["beat_s"] = 1.5
    got = of(pg.faults(Episode(**plan)), "G-MOVE")
    assert any("per second" in f and f"against {pg.TRAVEL_PER_SECOND}" in f for f in got)


def test_move_regression_on_the_fixtures():
    for ep in ("05", "07"):
        assert of(pg.faults(load(ep)), "G-MOVE") == [], ep
    ep09 = of(pg.faults(load("09")), "G-MOVE")
    closes = sorted(int(f.split("shot ")[1].split(":")[0]) for f in ep09 if "head's height" in f)
    assert closes == [6, 11, 18, 20, 23, 28, 29]
    two_shots = sorted(int(f.split("shot ")[1].split(":")[0]) for f in ep09 if "medium_close" in f)
    assert two_shots == [7, 17, 19, 24, 27]
    crowds = sorted(int(f.split("shot ")[1].split(":")[0]) for f in ep09 if "crowd" in f)
    assert crowds == [0, 8, 10, 13]
    assert not any("per second" in f for f in ep09)
    # ep08 fails on its own account: a long stride on medium_close 7, 16 and 26.
    ep08 = of(pg.faults(load("08")), "G-MOVE")
    assert sorted(int(f.split("shot ")[1].split(":")[0]) for f in ep08 if "medium_close" in f) == [7, 16, 26]


def test_travel_per_second_fires_on_none_of_the_four_fixtures():
    """ep07 shot 4 is a 2.0 s corridor push of four long strides (20 hands/s) and passed by
    eye, so the cap sits above it; ep09's largest is shot 17, two long strides in 2.5 s."""
    rates = {ep: max(pg.travel_rate(e, s) for s in e.shots) for ep, e in ((ep, load(ep)) for ep in ("05", "07", "08", "09"))}
    assert {ep: round(r, 1) for ep, r in rates.items()} == {"05": 3.6, "07": 20.0, "08": 5.2, "09": 8.0}
    assert all(r < pg.TRAVEL_PER_SECOND for r in rates.values())


# ---- G-STORY -----------------------------------------------------------------

def test_first_dialogue_late_fails():
    plan = synthetic()
    for line in plan["lines"]:
        if line["shot"] == 3:
            line.update(kind="narration", speaker="john_watson", text=NARRATION)
    plan["shots"][3]["faces"] = []
    got = of(pg.faults(Episode(**plan)), "G-STORY")
    assert any("first dialogue" in f and f"against {pg.FIRST_DIALOGUE_SHARE}" in f for f in got)


def test_a_long_narration_only_run_fails():
    plan = synthetic()
    for line in plan["lines"]:
        if line["shot"] == 10:
            line.update(kind="narration", speaker="john_watson", text=NARRATION)
    got = of(pg.faults(Episode(**plan)), "G-STORY")
    assert any("narration-only run" in f and f"against {pg.NARRATION_RUN_S}" in f for f in got)


def test_no_silent_shot_fails():
    plan = synthetic()
    plan["lines"].insert(SILENT, {"index": SILENT, "kind": "narration", "speaker": "john_watson",
                                  "text": NARRATION, "shot": SILENT})
    for k, line in enumerate(plan["lines"]):
        line["index"] = k
    got = of(pg.faults(Episode(**plan)), "G-STORY")
    assert any("silent" in f and f"measured 0 against {pg.MIN_SILENT_SHOTS}" in f for f in got)


def test_story_regression_on_the_fixtures():
    for ep in ("05", "07", "08"):
        assert of(pg.faults(load(ep)), "G-STORY") == [], ep
    ep09 = of(pg.faults(load("09")), "G-STORY")
    assert any("first dialogue" in f and "measured 0.6 against 0.25" in f for f in ep09)
    assert any("narration-only run" in f and "measured 92.2 against 75.0" in f for f in ep09)
    assert any("silent" in f and "measured 0 against 1" in f for f in ep09)


def test_narration_run_wall_sits_above_the_good_episodes():
    """The report's 45 s was measured on rendered audio; PROJECTED, ep05 runs 70.3 s and
    ep07 46.0 s of narration only, so a 45 s wall would refuse both good episodes."""
    runs = {ep: round(pg.longest_narration_run(load(ep)), 1) for ep in ("05", "07", "08", "09")}
    assert runs == {"05": 70.3, "07": 46.0, "08": 47.7, "09": 92.2}
    assert max(runs["05"], runs["07"], runs["08"]) < pg.NARRATION_RUN_S < runs["09"]


# ---- what could not be a refusal --------------------------------------------

def test_shot_length_stdev_cannot_separate_ep09_from_ep05():
    """By projection ep05 is the metronome (0.82 s) and ep09 sits at 1.00; the report's
    0.85 was measured on the cut.  So the stdev is an ADVISORY, never a fault."""
    got = {ep: round(pg.shot_length_stdev(load(ep)), 2) for ep in ("05", "07", "08", "09")}
    assert got == {"05": 0.82, "07": 1.70, "08": 1.31, "09": 1.00}
    assert any("stdev" in a for a in pg.advisories(load("05")))
    assert not any("stdev" in f for f in pg.faults(load("05")))


def test_turn_acting_on_a_cast_member_is_true_of_no_delivered_plan():
    """ep05's turn is a curtsey, ep07's a knife splitting a pill, ep08's a dust column:
    none acts on another cast member, so the rule cannot refuse ep09 alone."""
    assert pg.turn_acts_on(Episode(**synthetic())) == "Holmes catches Watson by the wrist"
    assert all(pg.turn_acts_on(load(ep)) == "" for ep in ("05", "07", "08", "09"))
    assert any("turn" in a for a in pg.advisories(load("09")))
    assert not any("G-STORY turn" in f for f in pg.faults(load("07")))


def test_every_fault_names_its_gate_and_its_numbers():
    for f in pg.faults(load("09")):
        assert f.split(" ")[0] in ("G-FIRSTFRAME", "G-VARIETY", "G-MOVE", "G-STORY"), f
        assert ", measured " in f and " against " in f, f
