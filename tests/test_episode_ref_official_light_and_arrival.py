r"""Episode 10's prompt-text findings (dq10/J.md §6, C.md §3) on the builder:

  1. the arrival names the move ONCE and repeats no word of the camera head
     beyond the verb -- 34/34 ep10 blocks carried "across the whole shot"
     twice and 11.6 words of the camera sentence verbatim;
  2. the light sentence is capped (`LIGHT_CAP`, a direction and a black --
     ep05/07 carried 5.3/5.5 words, ep10 14.0) and is CORE: T16's was the one
     of 34 that never reached H3, cut off the end of a 45-word camera field;
  3. four advisory lints on the wording H3 measurably ignores: a kept edge
     under a travel, a target noun in a head clause, a kept-clause holding a
     scale, a blur or an absence, and a walk at the lens or in a wide.

Free and offline.
"""
import re

from studio import episode_ref_official as ro
from studio.episode_spec import Line, Setup, Shot

SEG = {"t": 0.0, "end": 4, "t_to": 4.0, "size": "close", "crowd": "", "end_frame": "", "changed": "",
       "frame": "Close on Ferrier's face.",
       "motion": "The camera pushes in on Ferrier's face across the whole shot, travelling a hand's "
                 "breadth; he brings his chin down a finger's breadth."}


def grams(text: str, n: int = 3) -> set[tuple[str, ...]]:
    w = [t.strip(",.;").lower() for t in re.sub(r"\d\d:\d\d", "", text).split()]
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


# ---- 1. the arrival ---------------------------------------------------------

def test_the_move_verb_is_the_verb_and_its_particle_alone():
    assert ro.move_verb("pushes in on <Subject 1>'s face across the whole shot, travelling a hand's breadth") == "pushing in"
    assert ro.move_verb("pulls back from the porch across the whole shot") == "pulling back"
    assert ro.move_verb("pans right along the rank") == "panning right"
    assert ro.move_verb("tracks with Holmes across the whole shot") == "tracking"
    assert ro.move_verb("") == ""


def test_the_arrival_names_the_move_once_and_repeats_no_word_of_the_camera_head():
    head = ro.camera_sentence(SEG["motion"], 0, 4)
    said = ro.arrival_clause(SEG)
    assert said.startswith("By 00:04 the camera is pushing in")
    assert "across the whole shot" not in said and "hand's breadth" not in said
    assert not grams(head) & grams(said)
    assert len(re.sub(r"\d\d:\d\d", "", said).split()) <= 16


def test_a_block_says_across_the_whole_shot_once():
    shot = Shot(index=0, section="setup", setup="s", size="close", faces=["john_ferrier"],
                frame=SEG["frame"], motion=SEG["motion"],
                camera="in the room at Ferrier's own eye, an arm's length from him, a 90mm lens. "
                       "The window light comes from the left and leaves the right of his face dark",
                at_rest="Ferrier's face fills the CENTRE of the frame from the beard at the BOTTOM edge "
                        "to the hair at the TOP edge, the LEFT half in window light.")
    text = ro.build([shot], [{"index": 0, "t_start": 0.0, "seconds": 5.0}],
                    [Line(index=0, kind="narration", speaker="john_watson", text="A word.", shot=0)],
                    {0: (0.25, 4.0)}, 120, ["john_ferrier"], {"john_ferrier": "A tall man."},
                    "A log parlour, 1860.", "john_watson", check_lint=False)
    body = ro.blocks(text)[0][3]
    assert body.count("across the whole shot") == 1
    assert "and the action continues with it" in body


# ---- 2. the light sentence ---------------------------------------------------

CAM16 = ("inside the doorway at Brigham Young's own eye, an arm's length from him with the black "
         "door jamb at each edge of the lens and the sunlit path and the pale valley between them "
         "behind his shoulders, a 50mm lens. The low sun comes from the right along the house front "
         "and lights the path behind him and his right cheek hard")


def test_the_camera_field_parts_at_its_first_sentence():
    where, light = ro.camera_parts(CAM16)
    assert where.startswith("inside the doorway") and where.endswith("a 50mm lens")
    assert light.startswith("The low sun comes from the right")
    assert ro.camera_parts("on the path, a 35mm lens") == ("on the path, a 35mm lens", "")


def test_the_light_sentence_is_a_direction_and_a_black_in_ten_words():
    assert ro.LIGHT_CAP == 10
    assert ro.light_sentence("The low sun comes from the left and leaves the right side of his face in shadow") == \
        "The low sun comes from the left."
    assert ro.light_sentence("The window light comes from the left and leaves the right of his face dark") == \
        "The window light comes from the left."
    said = ro.light_sentence(ro.camera_parts(CAM16)[1])
    assert len(said.split()) <= ro.LIGHT_CAP and "from the right" in said
    assert ro.light_sentence("") == ""


def test_the_light_sentence_reaches_every_block_whatever_the_camera_length():
    """T16: a 45-word camera field lost its light off the end of `CAMERA_CAP`."""
    seg = {"camera": CAM16, "at_rest": "His head fills the CENTRE at a third of the frame's height."}
    said = ro.detail(seg, 0)
    assert said[0].startswith("The camera is inside the doorway")
    assert said[1] == "The low sun comes from the right."
    assert said[2].startswith("At the first frame")


def two_shot_text() -> str:
    a = Shot(index=0, section="setup", setup="s", size="medium", faces=["john_ferrier"],
             frame="Medium of Ferrier at the table.", motion=SEG["motion"],
             camera="at the table end level with a seated man's eye, two long strides from the chair, "
                    "a 50mm lens. The window at the left throws a hard slab of sun across the table",
             at_rest="Ferrier sits in the CENTRE of the frame from the bottom edge to the TOP third.")
    b = Shot(index=1, section="setup", setup="s", size="medium_close", faces=["john_ferrier"],
             frame="Medium close on Ferrier, head and shoulders.", motion=SEG["motion"], camera=CAM16,
             at_rest="His head and shoulders fill the CENTRE at a third of the frame's height.")
    return ro.build([a, b], [{"index": 0, "t_start": 0.0, "seconds": 4.0}, {"index": 1, "t_start": 4.0, "seconds": 4.0}],
                    [Line(index=0, kind="narration", speaker="john_watson", text="A word.", shot=0),
                     Line(index=1, kind="narration", speaker="john_watson", text="Another.", shot=1)],
                    {0: (0.25, 3.0), 1: (4.25, 3.0)}, 192, ["john_ferrier"], {"john_ferrier": "A tall man."},
                    "A log parlour, 1860.", "john_watson", check_lint=False)


def test_every_shots_light_sentence_is_a_substring_of_its_block():
    bodies = [b for _, _, _, b in ro.blocks(two_shot_text())]
    assert "The window at the left throws a hard slab of sun." in bodies[0]
    assert "The low sun comes from the right." in bodies[1]


# ---- 3. the advisory lints ---------------------------------------------------

def block(*sentences: str) -> str:
    return "detailed_description:\n[Shot 1] From 00:00 to 00:05. " + " ".join(sentences)


def test_a_kept_edge_under_a_travel_is_advised_against():
    said = block("The camera pushes in on the gate across the whole shot, travelling a hand's breadth "
                 "as the porch post keeps the frame edge, from 00:00 to 00:02.")
    assert any("L24 KEPT EDGE" in a and "pull-back moves it inward" in a for a in ro.advise(said))
    still = block("The camera holds a static shot as the porch post keeps the frame edge, from 00:00 to 00:02.")
    assert not [a for a in ro.advise(still) if "KEPT EDGE" in a]


def test_a_target_noun_in_a_head_clause_is_a_reposition_word():
    said = block("At 00:03 he turns his head toward the door, his shoulders following it a hand's breadth.")
    assert any("L25 REPOSITION" in a and "door" in a for a in ro.advise(said))
    fine = block("At 00:03 his chin comes round a finger's breadth, his eyes on the lens.")
    assert not [a for a in ro.advise(fine) if "REPOSITION" in a]


def test_a_kept_clause_may_hold_an_edge_object_never_a_scale_a_blur_or_an_absence():
    for clause in ("the whole face keeps inside the frame", "his dark shoulder keeps sharp at the right edge",
                   "a dark coat shoulder, the shoulder alone, comes in across the glass"):
        got = ro.advise(block(f"At 00:02 {clause}."))
        assert any("L26 KEPT SCOPE" in a for a in got), clause
    edge = block("At 00:02 the log villa keeps its one chimney at the TOP edge.")
    assert not [a for a in ro.advise(edge) if "KEPT SCOPE" in a]


def test_a_walk_toward_the_lens_is_an_advisory_and_a_walk_into_a_doorway_is_not():
    at_lens = block("The camera pushes in on him as he walks two steps up the path toward it, from 00:00 to 00:02.")
    assert any("L27 WALK" in a and "lens" in a for a in ro.advise(at_lens))
    away = block("The camera pushes in on the two men as he walks past the hand into the dark doorway "
                 "at a normal walking pace, from 00:00 to 00:02.")
    assert not [a for a in ro.advise(away) if "WALK" in a]


def test_a_walk_by_a_figure_in_a_wide_is_an_advisory():
    wide = block("The shot begins from <Picture 3>: a wide down the path to the gate. The camera pushes in "
                 "as he walks out through the open gate at a normal walking pace, from 00:00 to 00:02.")
    assert any("L27 WALK" in a and "wide" in a for a in ro.advise(wide))


def test_the_pace_mark_is_printed_not_counted():
    """L8 still asks for the pace mark (it stays a fault); the advisory does
    not read it as a brake, and a paced walk into a doorway raises nothing."""
    text = block("The camera pushes in as he walks to the door, from 00:00 to 00:02.")
    assert any("L8 NO PACE" in f for f in ro.lint(text, {}))
    assert not [a for a in ro.advise(text) if "WALK" in a]


def test_advisories_are_not_faults():
    said = block("The camera pushes in on the gate across the whole shot, travelling a hand's breadth "
                 "as the porch post keeps the frame edge, from 00:00 to 00:02.")
    assert not [f for f in ro.lint(said, {}) if "KEPT" in f]
    assert all(a.startswith("ADVISORY L2") for a in ro.advise(said))
