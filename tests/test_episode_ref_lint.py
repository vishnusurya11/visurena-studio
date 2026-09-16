"""The 18-rule prompt lint (spec §4): what makes a take prompt FAIL before it is
sent.  Every input below is real -- it is either the text on disk today, the
plan's own words, or one of the two worked prompts of spec §2, which are kept
verbatim in `tests/fixtures/ref2v_spec_t01.txt` and `..._t20.txt`.

The lint is the PRE-RENDER gate: it cannot predict a freeze caused by a pin, so
`motion_scan` stays the post-render gate."""
from pathlib import Path

import pytest

from studio import episode_ref_official as ro

FIX = Path(__file__).parent / "fixtures"
CRITERION_LIFE = ("the drinkers two deep at the near end talk, lift their glasses and shift on their "
                  "feet, and a barman reaches a bottle down from the glass shelf")
GATEWAY_LIFE = ("a hansom rolls past on the wet cobbles at the horse's trot and a porter carries a "
                "crate in through the open iron gates")
CLERKS = ("two clerks in dark coats walk the other way and a hansom is drawn up at the corner with "
          "its horse shifting in the shafts")
PORTER = "a porter with a crate on his shoulder passes the other way and a costermonger's barrow stands at the kerb"
DEUCE = "How the deuce did he know I was in Afghanistan?"

T01_FACTS = {"frames": 175, "refs": 5, "plate": 2, "strip": 5, "watson": "<Subject 1>",
             "pins": [(1, 0.0), (2, 77 / 24)], "lines": [], "life": {1: CRITERION_LIFE}}
T20_FACTS = {"frames": 294, "refs": 6, "plate": 2, "strip": 6, "watson": "<Subject 1>",
             "pins": [(1, 0.0), (2, 115 / 24), (3, 188 / 24)], "life": {1: GATEWAY_LIFE, 2: CLERKS, 3: PORTER},
             "lines": [{"block": 1, "text": DEUCE, "end": 3.83, "crosses": False}]}


def ids(text, facts=None):
    """The rule ids the lint reports, e.g. {'L2', 'L14'}."""
    return {fault.split()[0].rstrip(":") for fault in ro.lint(text, facts)}


def block(body, head="[Shot 1] From 00:00 to 00:04."):
    return f"detailed_description:\n{head} {body}"


# ---- T1-T8  the word rules, on the sentences that are on disk today ---------

def test_t1_the_static_sentence_in_all_40_blocks_fails_the_stillness_rule():
    assert "L2" in ids("Static shot; the camera position and lens remain still throughout.")


def test_t2_the_iteration_4_lips_sentence_fails_negation_and_stillness():
    text = "nobody on screen speaks while John Watson's lips remain completely closed"
    assert {"L1", "L2"} <= ids(text)


def test_t3_the_98_percent_frozen_take_fails_stillness_slow_and_action():
    text = block("Lips stay closed; the chest takes a single slow breath.")
    assert {"L2", "L3", "L4"} <= ids(text)


def test_t4_the_100_percent_frozen_insert_fails_stillness_and_action():
    assert {"L2", "L4"} <= ids(block("the finger stays over the water; the water stays clear"))


def test_t5_lie_still_and_does_not_change_fails_three_rules():
    assert {"L1", "L2", "L4"} <= ids(block("The men lie still and the light does not change."))


def test_t6_a_dialogue_block_that_freezes_on_the_last_word_fails_the_tail_rule():
    text = block("<Subject 1> (S1), on screen, a stout young man, says: <d>[English] Come along.</d> "
                 "The smile stays on him. His head does not turn away and the framing does not change.")
    facts = {"lines": [{"block": 1, "text": "Come along.", "end": 3.0, "crosses": False}]}
    assert {"L1", "L2", "L4", "L16"} <= ids(text, facts)


def test_t7_micro_motion_alone_is_not_an_action():
    assert "L4" in ids(block("his eyes narrow slightly and his brows draw together"))


def test_t8_the_slow_small_amplitude_boilerplate_fails_slow_but_keeps_its_pace():
    text = block("Tracking beside at walking pace, slowly, with small amplitude, in one continuous "
                 "motion in one direction. He walks on.")
    found = ids(text)
    assert "L3" in found and "L8" not in found


# ---- T9-T18  the structure rules, on today's emitted prompts ----------------

def test_t9_a_voice_range_may_not_leave_the_shot_it_plays_under():
    text = block("From 00:00 to 00:05 John Watson keeps the lips closed and the action moving. "
                 "He lifts the glass.", head="[Shot 1] From 00:00 to 00:03.")
    assert "L6" in ids(text)


def test_t10_the_ranges_must_cover_every_second_of_the_latent():
    """The last range ends on the second the latent ACTUALLY REACHES.

    It used to end on the CEILING, and this test asserted that: 294 frames is
    12.25 s, so the prompt said 00:13. MEASURED 2026-09-13 -- 16 of episode 3's
    22 prompts named up to 0.75 s of time the video does not contain, and the
    model laid its shots across the longer timeline, every one arriving early
    (T02's second cell by 1.50 s). `stated_end` floors instead, so 00:12 is now
    right and stopping SHORT of it is the fault."""
    def ranges(last):
        return ("detailed_description:\n[Shot 1] From 00:00 to 00:05. He walks on.\n"
                "[Shot 2] From 00:05 to 00:08. He walks on.\n"
                f"[Shot 3] From 00:08 to {last}. He walks on.")

    assert "L5" not in ids(ranges("00:12"), {"frames": 294})   # 294f = 12.25 s
    assert "L5" in ids(ranges("00:11"), {"frames": 294})       # stops short
    assert "L5" in ids(ranges("00:13"), {"frames": 294})       # names time that does not exist


def test_t11_the_summary_states_the_rendered_length_never_the_placed_one():
    text = "summary:\n[reference generation] One 6.79-second take of 2 shots in <Subject 2>."
    assert "L15" in ids(text, {"frames": 175})      # 175 frames is 7.29 s


def test_t12_every_relationship_in_play_is_named_as_a_task_type():
    text = ("summary:\n[reference generation] One 7.29-second take.\n\nretention_analysis:\n"
            "<Picture 3> ([Shot 1] first frame): fully_preserved - viewpoint.\n"
            "<Audio 1>: fully_copy - <Audio 1> is reused 1:1.")
    assert "L13" in ids(text)


def test_t13_one_picture_may_not_be_the_first_frame_of_every_shot():
    text = ("retention_analysis:\n<Picture 3> ([Shot 1] first frame, [Shot 2] first frame): "
            "fully_preserved - viewpoint, subject placement, wardrobe and light.")
    assert "L11" in ids(text, {"strip": 3})


def test_no_picture_may_be_declared_a_shot_s_LAST_FRAME():
    """THE OWNER'S RULE, and the lint is where it has to live.

    `takes_r2v.NO_ENDS` stops END cells being STAGED; this stops the prompt
    DECLARING one, which is the same pin by another route and is exactly how 15
    of them reached episode 8 while the skill already said "no end pins". The
    model races to the last-frame picture and then holds it: near, the segment
    freezes; far, the background dissolves into the other picture.

    The gate is on the ARTEFACT -- the built prompt -- because a flag can be
    honoured on one code path and bypassed on another, and was."""
    text = ("subject_definitions:\n<Picture 2> is the first frame of [Shot 1], a wide.\n"
            "<Picture 3> is the last frame of [Shot 1], with the action of that shot completed.")
    assert "L11" in ids(text)
    assert any("last frame" in fault for fault in ro.lint(text))


def test_the_retention_line_may_not_retain_one_either():
    text = ("retention_analysis:\n<Picture 3> ([Shot 1] last frame): fully_preserved - viewpoint.")
    assert any("last frame" in fault for fault in ro.lint(text))


def test_a_prompt_that_only_names_its_first_frames_passes_that_rule():
    text = "subject_definitions:\n<Picture 2> is the first frame of [Shot 1], a wide."
    assert not [f for f in ro.lint(text) if "last frame" in f]


def test_the_PROSE_clause_the_spec_requires_is_not_a_pin():
    """"...and the lean continues to the last frame of the shot" is the spec's own
    continuation clause and appears in both worked prompts. It binds no picture to
    anything; a rule that cannot tell it from a declaration would refuse every take."""
    text = ("detailed_description:\n[Shot 1] From 00:00 to 00:03. The shot begins from "
            "<Picture 3>: a close shot. At 00:02 he leans his weight onto the stick, "
            "and the lean continues to the last frame of the shot.")
    assert not [f for f in ro.lint(text) if "last frame" in f]


def test_t14_the_location_may_not_appear_in_a_shot_nor_be_fully_preserved():
    text = ("retention_analysis:\n<Subject 2> (appears in [Shot 1], [Shot 2]): fully_preserved - "
            "the room, its furniture, walls, windows and light.")
    assert "L11" in ids(text, {"plate": 2})


def test_t15_a_speakers_first_line_carries_his_identity():
    text = block(f"<Subject 1> (S1) says: <d>[English] {DEUCE}</d> He walks on.")
    facts = {"lines": [{"block": 1, "text": DEUCE, "end": 3.0, "crosses": False}]}
    assert "L12" in ids(text, facts)


def test_t16_watson_walking_without_a_limp_fails():
    text = block("The camera tracks beside them at a normal walking pace as <Subject 1> walks along "
                 "the railings.")
    assert "L9" in ids(text, {"watson": "<Subject 1>"})


def test_t17_a_public_setup_must_put_its_people_to_work():
    text = block("The camera holds a static shot as <Subject 1> lifts the glass, from 00:00 to 00:02.")
    assert "L10" in ids(text, {"life": {1: GATEWAY_LIFE}})


def test_t18_a_shot_block_of_114_words_is_under_the_official_band():
    text = block(" ".join(["He lifts the glass and drinks."] * 12))   # 72 words
    found = ids(text)
    assert "L14" in found


def test_t19_the_plans_own_negations_are_the_blocker_section_0_1_names():
    described = ("a long mahogany counter, thinning to nobody at the far end; not a window on that "
                 "wall, and no street is visible through the doors")
    assert "L1" in ids(described)


def test_t18b_a_block_over_240_words_is_padded_and_also_fails():
    assert "L14" in ids(block(" ".join(["He lifts the glass and sets it down again."] * 40)))


# ---- L18 -------------------------------------------------------------------

def test_a_banned_prop_never_reaches_the_prompt():
    """Already BANNED_PROPS in episode_spec; the lint repeats it at prompt level."""
    assert "L18" in ids("his gloved hand on the silver knob")


# ---- T20-T22  the two worked prompts pass every rule ------------------------

def test_t20_the_worked_narration_prompt_passes_every_rule():
    assert ro.lint((FIX / "ref2v_spec_t01.txt").read_text(encoding="utf-8"), T01_FACTS) == []


def test_t21_the_worked_dialogue_prompt_passes_every_rule():
    assert ro.lint((FIX / "ref2v_spec_t20.txt").read_text(encoding="utf-8"), T20_FACTS) == []


def test_t22_a_negation_inside_the_spoken_line_is_never_a_fault():
    """ref-en §5.4 wants the line byte for byte, so `<d>...</d>` is cut out first."""
    line = "I do not know."
    text = (FIX / "ref2v_spec_t20.txt").read_text(encoding="utf-8").replace(DEUCE, line)
    facts = dict(T20_FACTS, lines=[{"block": 1, "text": line, "end": 3.83, "crosses": False}])
    assert "L1" not in ids(text, facts)


def test_check_raises_on_the_first_fault_and_says_nothing_when_clean():
    with pytest.raises(ValueError, match="L2"):
        ro.check("Static shot; the camera and lens remain still throughout.")
    assert ro.check((FIX / "ref2v_spec_t01.txt").read_text(encoding="utf-8"), T01_FACTS) is None
