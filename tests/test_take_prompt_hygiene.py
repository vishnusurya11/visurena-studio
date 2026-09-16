r"""Take prompt hygiene (G-HYGIENE): the five lints L19-L23 and the builder rules
behind them, proven on the episode fixtures the owner judged.

`docs/analysis/ep08_ep09_why_worse.md` §5 measured, on the built prompts:

  * a 36-word setup crowd caption injected verbatim into 30/30 ep09 blocks
    (ep07: 2/26), with `.,` punctuation and "Behind him" over twelve shots with
    no him -- `life_sentence` wrapped `Setup.crowd` untouched and counted it as
    core, so it displaced the shot's own camera position, light and at-rest
    geometry (32 -> 4 words a block);
  * a 48-word style line ("only., 35 mm");
  * `arrival_clause` turned the drawer's `end` layout into the block's closing
    motion sentence -- "By 00:05, the log house stands twice its size..." -- and
    `noun_phrase` lowercased a proper name ("ferrier's head");
  * `mouth_of` told a man named in `frame` but absent from `faces` to keep his
    mouth shut (4 ep09 blocks);
  * `paced()` put "at a normal walking pace" on the sun, the wheat and a
    curtain, because GAIT read "three long strides as the low sun lifts";
  * `place_word` called a farm "this room" because its description says "house".

The fixtures are the BUILT prompts (the book is not in the test tree), so the
lints judge prompt TEXT and are tested on those files: ep07 passes, ep09 fails
each with a count.  Free and offline: nothing renders, nothing is spent.
"""
import json
from pathlib import Path

import pytest

from studio import episode_ref_official as ro
from studio.episode_spec import Line, Setup, Shot

FIX = Path(__file__).parent / "fixtures" / "episodes"


def takes(ep: str) -> list[dict]:
    return json.loads((FIX / f"{ep}_take_prompts.json").read_text(encoding="utf-8"))


def faults(rule, ep: str) -> list[str]:
    """Every fault one rule raises across an episode's built prompts."""
    return [f for t in takes(ep) for f in rule(t["prompt"], {})]


def prompt_ids(rule, ep: str) -> set[int]:
    return {t["index"] for t in takes(ep) if rule(t["prompt"], {})}


# ---- the lints on the fixtures: ep07 passes, ep09 fails with a count --------

def test_l19_crowd_refuses_the_dot_comma_in_every_ep09_block_and_none_of_ep07():
    assert faults(ro.l19_crowd, "ep07") == []
    bad = faults(ro.l19_crowd, "ep09")
    assert len([f for f in bad if "'.,'" in f]) == 30


def test_l19_crowd_refuses_one_long_sentence_in_two_blocks():
    crowd = ("Behind him forty immigrants in dust-grey homespun kneel along the rock shoulder with their "
             "hats off and beyond them twelve waggons stand in a line")
    text = ("detailed_description:\n[Shot 1] From 00:00 to 00:04. He walks on. "
            f"{crowd}, from 00:00 to 00:04.\n[Shot 2] From 00:04 to 00:08. He walks on. "
            f"{crowd}, from 00:04 to 00:08.")
    assert any("L19" in f and "[Shot 1] and [Shot 2]" in f for f in ro.l19_crowd(text, {}))
    one = text.split("\n[Shot 2]")[0]
    assert ro.l19_crowd(one, {}) == []


def test_l20_style_refuses_ep09s_48_word_line_and_passes_ep07s_13():
    assert faults(ro.l20_style, "ep07") == []
    bad = faults(ro.l20_style, "ep09")
    assert len(prompt_ids(ro.l20_style, "ep09")) == 28
    assert any("48 words" in f for f in bad)
    assert any("'.,'" in f for f in bad)
    assert any("Warm" in f for f in bad)


def test_l20_style_lets_a_place_name_keep_its_capital():
    line = "Photoreal cinematic live-action, the Utah valley, June 1860, 35 mm film grain, hard sun."
    assert ro.l20_style(f"detailed_description:\n{line}\n[Shot 1] From 00:00 to 00:04. He walks on.", {}) == []


def test_l20_style_refuses_a_line_of_seventeen_words():
    line = "Photoreal cinematic live-action, 1881 London, 35 mm film grain, natural weight and pace and more and more."
    assert len(line.split()) == 17
    assert any("17 words" in f for f in ro.l20_style(f"detailed_description:\n{line}", {}))


def test_l21_arrival_fails_29_of_30_ep09_blocks_and_none_of_ep07():
    assert faults(ro.l21_arrival, "ep07") == []
    assert len(faults(ro.l21_arrival, "ep09")) == 29


def test_l21_arrival_refuses_a_layout_and_accepts_the_camera_moving_through_the_last_frame():
    still = ("detailed_description:\n[Shot 1] From 00:00 to 00:05. He walks on. By 00:05, the log house "
             "stands twice its size along the left edge with the wheat reduced to a gold strip.")
    assert ro.l21_arrival(still, {})
    moving = ("detailed_description:\n[Shot 1] From 00:00 to 00:05. He walks on. By 00:05 the camera is "
              "pushing in on the log house, travelling two long strides through the last frame of the "
              "shot, with the log house now in frame, and the action continues with it.")
    assert ro.l21_arrival(moving, {}) == []


def test_l22_absent_mouth_fails_ep09_t03_t20_t21_t25_and_nothing_in_ep07():
    assert faults(ro.l22_absent_mouth, "ep07") == []
    assert prompt_ids(ro.l22_absent_mouth, "ep09") == {3, 20, 21, 25}


def test_l22_accepts_a_staged_subjects_mouth():
    text = "detailed_description:\n[Shot 1] From 00:00 to 00:04. <Subject 1>'s mouth is closed from 00:00 to 00:04 while he walks on."
    assert ro.l22_absent_mouth(text, {}) == []
    assert ro.l22_absent_mouth(text.replace("<Subject 1>", "John Ferrier"), {})


def test_l23_pace_on_a_thing_refuses_the_sun_and_the_wheat():
    bad = prompt_ids(ro.l23_pace_on_a_thing, "ep09")
    assert {0, 3} <= bad
    sun = ("detailed_description:\n[Shot 1] From 00:00 to 00:05. The camera pulls back off the valley across "
           "the whole shot, travelling three long strides as the low sun lifts along the far peaks at a "
           "normal walking pace, from 00:00 to 00:02.")
    assert any("sun" in f for f in ro.l23_pace_on_a_thing(sun, {}))


def test_l23_names_ep07s_curtain_and_gas_flame_too():
    """The report's own list is 'the sun, the wheat and a curtain'; the curtain is
    episode 7's.  A lint that spared the baseline would be the fault the report
    is about."""
    bad = faults(ro.l23_pace_on_a_thing, "ep07")
    assert len(bad) == 2 and any("curtain" in f for f in bad) and any("flame" in f for f in bad)


def test_l23_accepts_a_pace_on_a_person_or_an_animal():
    for said in ("The camera tracks beside them at a normal walking pace as <Subject 1> walks on.",
                 "Behind him one boy of about twelve carries a milk can down the lane at a normal walking pace.",
                 "The horse trots ahead at a normal trot.",
                 "Lucy walks the wheat path at a normal walking pace."):
        assert ro.l23_pace_on_a_thing(f"detailed_description:\n[Shot 1] From 00:00 to 00:04. {said}", {}) == []


def test_the_new_lints_are_in_the_rule_table_and_the_worked_prompts_still_pass():
    assert {ro.l19_crowd, ro.l20_style, ro.l21_arrival, ro.l22_absent_mouth, ro.l23_pace_on_a_thing} <= set(ro.RULES)
    fix = Path(__file__).parent / "fixtures"
    for name in ("ref2v_spec_t01.txt", "ref2v_spec_t20.txt"):
        text = (fix / name).read_text(encoding="utf-8")
        for rule in (ro.l19_crowd, ro.l20_style, ro.l21_arrival, ro.l22_absent_mouth, ro.l23_pace_on_a_thing):
            assert rule(text, {}) == [], (name, rule.__name__)


# ---- 1  the crowd: once a take, normalised, agreeing with the faces ----------

def test_a_crowd_caption_is_normalised_before_it_is_wrapped():
    names = ro.names_of(["john_ferrier", "lucy_ferrier"])
    assert ro.normal_crowd("Two farm hands pitch cut wheat onto a waggon.", names) == \
        "two farm hands pitch cut wheat onto a waggon"
    assert ro.normal_crowd("Ferrier's hands pitch wheat.", names) == "Ferrier's hands pitch wheat"
    assert ro.normal_crowd("Lucy waves from the porch", names) == "Lucy waves from the porch"
    assert ro.normal_crowd("", names) == ""


def test_the_life_sentence_agrees_with_the_blocks_faces():
    assert ro.life_sentence("the drinkers lift their glasses", 0, 3, "them") == \
        "Behind them the drinkers lift their glasses, from 00:00 to 00:03."
    assert ro.life_sentence("the drinkers lift their glasses", 0, 3, "<Subject 1>").startswith("Behind <Subject 1> ")
    assert ro.life_sentence("the drinkers lift their glasses", 0, 3, "").startswith("Beyond the foreground ")
    assert ro.life_sentence("", 0, 3, "them") == ""


def test_who_the_crowd_is_behind_is_the_staged_faces_never_a_pronoun_for_nobody():
    assert ro.behind([]) == ""
    assert ro.behind(["lucy_ferrier"]) == "<Subject 1>"
    assert ro.behind(["lucy_ferrier", "jefferson_hope"]) == "them"


def test_the_crowd_goes_in_the_first_wide_enough_block_only():
    setup = Setup(described="A farm.", crowd="two farm hands pitch wheat", outdoors=True)
    segs = [{"size": "close", "crowd": "", "setup": setup}, {"size": "medium", "crowd": "", "setup": setup},
            {"size": "wide", "crowd": "", "setup": setup}]
    assert ro.crowd_block(segs) == 1
    # a take of closes still stands in a public place: the first block that is not an insert
    assert ro.crowd_block([{"size": "insert", "crowd": "", "setup": setup},
                           {"size": "close", "crowd": "", "setup": setup}]) == 1
    assert ro.crowd_block([{"size": "insert", "crowd": "", "setup": setup}]) is None
    assert ro.crowd_block([{"size": "wide", "crowd": "", "setup": Setup(described="A parlour.")}]) is None


# ---- 3  the arrival is the camera, and a name keeps its capital --------------

SEG = {"t": 0.0, "end": 5, "t_to": 5.0, "size": "wide", "crowd": "", "faces": [],
       "frame": "Wide of Ferrier's farm on the valley floor.",
       "motion": "The camera pushes in on the log house across the whole shot, travelling two long strides; "
                 "the wheat runs in a long wave where the wind crosses it.",
       "end_frame": "The log house stands twice its size along the left edge with the porch posts at the "
                    "bottom corner and the wheat reduced to a gold strip.", "changed": ""}


def test_a_layout_end_becomes_the_camera_arriving_with_one_noun_in_frame():
    said = ro.arrival_clause(SEG)
    assert said == ("By 00:05 the camera is pushing in on the log house across the whole shot, travelling "
                    "two long strides through the last frame of the shot, with the log house now in frame, "
                    "and the action continues with it.")
    assert "stands" not in said and "twice" not in said and ".," not in said
    assert ro.l21_arrival(f"detailed_description:\n[Shot 1] From 00:00 to 00:05. He walks on. {said}", {}) == []


def test_a_layout_is_known_by_its_verbs_and_its_frame_edge_nouns():
    for end in ("The log house stands twice its size along the left edge.",
                "Lucy has crossed to the left half of the frame.",
                "The head of the mule train has arrived at the left edge.",
                "The waggon line fills it from edge to edge."):
        assert ro.is_layout(end), end
    assert not ro.is_layout("The door stands open.")
    assert not ro.is_layout("Holmes has turned to the window.")


def test_the_one_noun_carried_from_a_layout_is_what_has_come_into_frame():
    names = ro.names_of(["lucy_ferrier", "john_ferrier"])
    assert ro.end_noun("The log house stands twice its size along the left edge.", names) == "the log house"
    assert ro.end_noun("The snow peaks have left the top of the frame and the waggon line fills it.", names) == \
        "the waggon line"
    assert ro.end_noun("Lucy has crossed to the left half of the frame.", names) == "Lucy"
    assert ro.end_noun("Ferrier's head and shoulders fill the left half of the frame.", names) == \
        "Ferrier's head and shoulders"
    assert ro.end_noun("The far end of the kneeling rank has arrived at the right edge.", names) == "the far end"


def test_a_proper_name_keeps_its_capital_through_noun_phrase():
    names = ro.names_of(["john_ferrier", "lucy_ferrier"])
    assert ro.noun_phrase("Ferrier's head and shoulders fill the frame.", names) == \
        "Ferrier's head and shoulders fill the frame"
    assert ro.noun_phrase("Lucy has crossed to the left half.", names) == "Lucy has crossed to the left half"
    assert ro.noun_phrase("The door stands open.", names) == "the door stands open"
    assert ro.noun_phrase("Close on Ferrier at the fence.", names) == "a close shot of Ferrier at the fence"


def test_a_static_shot_with_a_layout_end_still_arrives_with_the_noun():
    seg = dict(SEG, motion="The wheat runs in a long wave where the wind crosses it.")
    said = ro.arrival_clause(seg)
    assert said.startswith("By 00:05 the action of that shot continues through the last frame")
    assert "with the log house now in frame" in said and "twice" not in said


# ---- 4  the mouth belongs to a staged face -----------------------------------

def test_a_man_named_in_the_frame_but_absent_from_faces_gets_no_mouth_sentence():
    cast = ["john_ferrier", "lucy_ferrier"]
    seg = {"size": "wide", "frame": "Wide of Ferrier's farm on the valley floor."}
    assert ro.mouth_of(seg, [], cast) == ""
    assert ro.mouth_of(seg, ["john_ferrier"], cast) == "<Subject 1>"
    assert ro.mouth_of({"size": "close", "frame": "Close on Lucy's face."}, ["lucy_ferrier"], cast) == "<Subject 1>"
    # the take's sheet is staged for every shot; the BLOCK's own faces say who is in this picture
    assert ro.mouth_of(dict(seg, faces=[]), ["john_ferrier"], cast) == ""
    assert ro.mouth_of(dict(seg, faces=["john_ferrier"]), ["lucy_ferrier", "john_ferrier"], cast) == "<Subject 2>"


def test_the_block_shows_only_its_own_faces_among_the_staged_sheets():
    assert ro.staged({"faces": ["lucy_ferrier"]}, ["john_ferrier", "lucy_ferrier"]) == ["lucy_ferrier"]
    assert ro.staged({"faces": ["jefferson_hope"]}, ["john_ferrier"]) == []
    assert ro.staged({}, ["john_ferrier"]) == ["john_ferrier"]
    assert ro.behind(["lucy_ferrier"], ["john_ferrier", "lucy_ferrier"]) == "<Subject 2>"


def test_subject_of_never_falls_back_to_a_bare_name():
    assert ro.subject_of("john_ferrier", ["john_ferrier"]) == "<Subject 1>"
    assert ro.subject_of("john_ferrier", []) == ""
    assert ro.lead_tag([]) == "John Watson"          # the limp rule still watches an unstaged Watson
    assert ro.speaker_intro("john_ferrier", "S1", "An old man.", set(), []).startswith("John Ferrier (S1)")


# ---- 5  the pace lands on a person, never on a thing -------------------------

def test_a_measured_stride_is_blanked_in_place_so_positions_hold():
    said = "travelling three long strides as the low sun lifts"
    assert len(ro.blank_measures(said)) == len(said)
    assert "strides" not in ro.blank_measures(said)


def test_the_pace_never_lands_on_the_sun_the_wheat_or_a_curtain():
    for said in ("The camera pulls back off the valley across the whole shot, travelling three long strides "
                 "as the low sun lifts along the far peaks",
                 "The camera pushes in on the log house, travelling two long strides as the wheat runs in a "
                 "long wave where the wind crosses it",
                 "The camera pushes in from the doorway, travelling two long strides as the curtain at the "
                 "open window lifts and falls once in the draught"):
        assert ro.paced(said) == said, said


def test_the_pace_still_lands_on_a_person_and_an_animal():
    assert ro.paced("The camera tracks beside Lucy, travelling four long strides as she walks the path") == \
        "The camera tracks beside Lucy, travelling four long strides as she walks the path at a normal walking pace"
    assert ro.paced("Behind him a boy with a milk can walks the lane, and a cat sits on a crate") == \
        "Behind him a boy with a milk can walks the lane at a normal walking pace, and a cat sits on a crate"
    assert ro.paced("The horse trots ahead.") == "The horse trots ahead at a normal trot."


def test_the_limp_lands_on_watsons_gait_never_on_a_measured_stride():
    said = "The camera pulls back from the chair, travelling two long strides as <Subject 1> sits down"
    assert ro.limp(said) == said
    assert ro.limp("<Subject 1> walks to the door") == "<Subject 1> walks limping on his stick to the door"


def test_a_clause_is_a_persons_when_its_subject_is_one():
    assert ro.is_person("<Subject 1> sits down and his shoulders come down")
    assert ro.is_person("a boy with a milk can")
    assert ro.is_person("Lucy on the lower step")
    assert not ro.is_person("the low sun lifts along the far peaks")
    assert not ro.is_person("the curtain at the open window lifts and falls once in the draught")
    assert not ro.is_person("The camera pushes in on the log house")


def test_porch_steps_are_a_noun_not_a_gait():
    assert ro.gaits("a medium two-shot on the porch steps: Lucy on the lower step") == []
    assert ro.gaits("Lucy steps down off the porch")


# ---- 6  an outdoor setup is a place -------------------------------------------

def test_an_outdoor_setup_is_a_place_whatever_its_description_says():
    farm = "John Ferrier's farm: a long low log house grown room by room into a villa with a deep porch."
    assert ro.place_word(farm) == "room"
    assert ro.place_word(farm, outdoors=True) == "place"
    assert ro.place_word("The Criterion Bar.", outdoors=False) == "room"


# ---- 7  the camera position and the at-rest geometry are required -------------

def test_the_camera_position_and_the_at_rest_geometry_are_never_displaced():
    seg = {"camera": "on the beaten cart road in front of the farm at a standing man's eye, four long strides "
                     "out from the rail fence, a 35mm lens",
           "at_rest": "The log house stands along the LEFT edge and the gold wheat fills the middle band"}
    out = ro.detail(seg, 0)
    assert out[0].startswith("The camera is on the beaten cart road")
    assert out[1] == "At the first frame the log house stands along the LEFT edge and the gold wheat fills the middle band."
    assert ro.detail(seg, 400) == out
    assert ro.detail({"camera": "", "at_rest": ""}, 40) == []


# ---- the rebuilt ep09-shaped block carries everything the fixtures lost --------

FARM = Setup(described="John Ferrier's farm on the valley floor, June 1860: a long low log house grown room by "
                       "room into a rambling villa with a shingled roof and a deep porch, a rail fence running "
                       "out from it, a hundred acres of ripe gold wheat beyond the fence, red pine hills "
                       "behind, hard morning sunlight", cast=["john_ferrier", "lucy_ferrier"], outdoors=True,
             crowd="Two farm hands in shirtsleeves pitch cut wheat onto a waggon at the fence line, and a yoke "
                   "of oxen stands in the shafts with a boy at their heads.")
T03 = Shot(index=3, section="setup", setup="ferrier_land", size="wide", faces=[],
           frame="Wide of Ferrier's farm on the valley floor: the long log house with its deep porch and "
                 "shingled roof on the left, a rail fence running out from it, a hundred acres of ripe gold "
                 "wheat beyond, red pine hills behind under a bleached sky.",
           motion="The camera pushes in on the log house across the whole shot, travelling two long strides; "
                  "the wheat runs in a long wave where the wind crosses it; a farm hand pitches a forkful up "
                  "onto the waggon at the fence.",
           camera="on the beaten cart road in front of the farm at a standing man's eye, four long strides "
                  "out from the rail fence, a 35mm lens. The hard morning sun stands high behind the camera",
           at_rest="The log house stands along the LEFT edge and the gold wheat fills the middle band.",
           end="The log house stands twice its size along the left edge with the porch posts at the bottom "
               "corner and the wheat reduced to a gold strip.")
T04 = Shot(index=4, section="setup", setup="ferrier_land", size="medium", faces=["john_ferrier"],
           frame="Medium of John Ferrier at the rail fence, the wide-brimmed brown felt hat level over his "
                 "brows, one bare heavy-knuckled hand closed on the top rail, the gold wheat behind him.",
           motion="The camera pushes in on John Ferrier across the whole shot, travelling one long stride; he "
                  "runs his bare hand along the top rail toward the post; he turns his beard toward the wheat.",
           camera="on the road side of the rail fence, level with Ferrier's eye, two long strides from him, "
                  "a 50mm lens. The high sun comes over his right shoulder",
           at_rest="Ferrier stands in the LEFT half with his hand on the top rail and the wheat behind him.",
           end="Ferrier's head and shoulders fill the left half of the frame with the fence rail cut off at "
               "the bottom edge.")
LINES = [Line(index=3, kind="narration", speaker="john_watson", shot=3,
              text="Among them was John Ferrier, who had walked out of the desert carrying a child."),
         Line(index=4, kind="narration", speaker="john_watson", shot=4,
              text="In three years he was comfortable, in nine he was rich, in twelve he had no equal.")]
PHYS = {"john_ferrier": "A gaunt weather-beaten man of sixty with a black beard.",
        "lucy_ferrier": "A girl of eighteen with fair hair."}


def rebuilt(shots, placed, at, frames, faces):
    lines = [l for l in LINES if l.shot in {s.index for s in shots}]
    return ro.build(shots, placed, lines, at, frames, faces, PHYS, FARM.described, "john_watson",
                    setup=FARM, check_lint=False)


def test_a_rebuilt_ep09_wide_carries_its_camera_its_geometry_and_one_clean_crowd():
    text = rebuilt([T03], [{"index": 3, "t_start": 10.0, "seconds": 5.88}], {3: (10.2, 5.0)}, 141, [])
    body = ro.blocks(text)[0][3]
    assert "The camera is on the beaten cart road in front of the farm" in body
    assert "At the first frame the log house stands along the LEFT edge" in body
    assert body.count("Beyond the foreground two farm hands in shirtsleeves") == 1
    assert ".," not in body and "Behind him" not in body
    assert "mouth is closed" not in body                       # nobody's face is staged
    assert "at a normal walking pace" not in body              # the wheat has no gait
    assert "with the log house now in frame" in body and "twice its size" not in body
    assert "defines this place alone" in text and "this room" not in text
    for rule in (ro.l19_crowd, ro.l21_arrival, ro.l22_absent_mouth, ro.l23_pace_on_a_thing):
        assert rule(text, {}) == [], rule.__name__


def test_a_rebuilt_two_shot_take_carries_the_crowd_once_in_its_first_wide_enough_block():
    text = rebuilt([T03, T04], [{"index": 3, "t_start": 10.0, "seconds": 5.88},
                                {"index": 4, "t_start": 15.88, "seconds": 7.29}],
                   {3: (10.2, 5.0), 4: (16.0, 6.5)}, 316, ["john_ferrier"])
    one, two = [b[3] for b in ro.blocks(text)]
    assert "two farm hands" in one and "two farm hands" not in two
    assert "<Subject 1>'s mouth is closed" in two and "John Ferrier's mouth" not in text
    assert "with <Subject 1>'s head and shoulders now in frame" in two
    assert "The camera is on the road side of the rail fence" in two
    assert "At the first frame Ferrier stands in the LEFT half" in two or \
        "At the first frame <Subject 1> stands in the LEFT half" in two
    assert ro.l19_crowd(text, {}) == [] and ro.l21_arrival(text, {}) == []


def test_the_crowd_is_the_first_thing_dropped_when_a_block_would_overflow():
    ctx = {"crowd_at": 0, "names": (), "faces": [], "cast": [], "life": {}}
    seg = {"t": 0.0, "end": 5, "size": "wide", "crowd": "", "setup": FARM}
    assert ro.life_for(1, seg, ctx, ro.HIGH_BLOCK - 5) == ""
    assert ctx["life"] == {}
    # short of room for the whole caption, its first clause goes in; L10 asks for exactly that
    part = ro.life_for(1, seg, ctx, ro.HIGH_BLOCK - 24)
    assert part == ("Beyond the foreground two farm hands in shirtsleeves pitch cut wheat onto a waggon at "
                    "the fence line, from 00:00 to 00:05.")
    assert ctx["life"][1] == "two farm hands in shirtsleeves pitch cut wheat onto a waggon at the fence line"
    said = ro.life_for(1, seg, ctx, 100)
    assert said.startswith("Beyond the foreground two farm hands") and ctx["life"][1] == \
        "two farm hands in shirtsleeves pitch cut wheat onto a waggon at the fence line, and a yoke of oxen " \
        "stands in the shafts with a boy at their heads"


def test_the_lint_facts_ask_for_the_crowd_only_where_the_builder_put_it():
    text = rebuilt([T03, T04], [{"index": 3, "t_start": 10.0, "seconds": 5.88},
                                {"index": 4, "t_start": 15.88, "seconds": 7.29}],
                   {3: (10.2, 5.0), 4: (16.0, 6.5)}, 316, ["john_ferrier"])
    # the wide's block is full (a 45-word frame), so the crowd went in as its first clause
    life = {1: "two farm hands in shirtsleeves pitch cut wheat onto a waggon at the fence line"}
    assert ro.l10_life(text, {"life": life}) == []
    assert ro.l10_life(text, {"life": {2: life[1]}})
    assert ro.l10_life(text, {"life": {1: life[1] + ", and a yoke of oxen stands in the shafts"}})
