r"""The picture gates: G-SIZE (hard), G-SUNSPLIT, G-LIGHT-SIDE and the motion
advisories, calibrated on episode 10 and the four judged fixtures.

MEASURED, docs/analysis/ep10_dq_synthesis.md §C and the analyst reports
(scratchpad dq10/B, C, E, J):

  * head fraction phrase in 0/34 ep10 at_rests against ep07 20/26; three
    medium_closes written "from the TOP edge to the BOTTOM third" were drawn
    as closes (face 0.51-0.59) -- shots 18, 27, 30;
  * 0/6 "LEFT half in sun, RIGHT half in shadow" splits on a sunlit face were
    drawn; 14/16 practical-light directions were -- shots 4, 5 on the path;
  * shots 16/17/18 named "sun from the right" from inside the door looking
    out, when the setup's sun is on the right only facing the porch;
  * kept-clauses held 1 of 4 (a sharp static edge object under a small move);
    "turns his head toward the door" walked the man past the lens 3/3; a walk
    toward the lens or by a 50-px figure in a wide was ignored 2/2.

Free and offline: plan JSON only.  ep05 and ep07 (judged right) take no
fault here; ep10 (the calibration) trips exactly what the reports measured.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import picture_gates as pgx
from studio.episode_spec import Episode

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "episodes"
EP10 = ROOT / "library" / "20260822113400_a-study-in-scarlet" / "episodes" / "ep10" / "plan.json"


def load(ep: str) -> Episode:
    return Episode(**json.loads((FIXTURES / f"ep{ep}_plan.json").read_text(encoding="utf-8")))


def ep10() -> Episode:
    if not EP10.exists():
        pytest.skip("the ep10 plan is not on this machine")
    return Episode(**json.loads(EP10.read_text(encoding="utf-8")))


def of(lines: list[str], gate: str) -> list[str]:
    return [f for f in lines if f.startswith(gate + " ")]


def shots_in(lines: list[str]) -> set[int]:
    import re
    return {int(m.group(1)) for f in lines for m in [re.search(r"shot (\d+)", f)] if m}


# ---- G-SIZE: the head fraction is the size, not the span ---------------------

Q18 = ("John Ferrier's head and shoulders fill the CENTRE of the frame from the TOP edge to the "
       "fawn coat at the BOTTOM third, the hat brim's black across his eyes and the RIGHT cheek "
       "in hard sun under it, the LEFT cheek in shadow. The riding whip crosses the BOTTOM edge.")
EP07_3 = ("A little lean man's head and chest fill the CENTRE of frame at half the frame height "
          "with a sallow face and wavy chestnut hair, his soft collar stands askew at his throat.")


def test_the_head_fraction_vocabulary_is_stated_as_a_constant():
    assert pgx.HEAD_FRACTION["close"] == ("half",)
    assert "third" in pgx.HEAD_FRACTION["medium_close"]
    assert "quarter" in pgx.HEAD_FRACTION["medium"]


def test_a_fraction_phrase_is_read_in_every_form_the_good_episodes_wrote():
    for said in ("his head a third of the frame's height", "at half the frame height",
                 "his head half the frame's height", "at two thirds of the frame height",
                 "at a quarter of the frame's height", "at four fifths of the frame height"):
        assert pgx.names_fraction(said), said
    assert not pgx.names_fraction("his head fills the TOP half of the frame")
    assert not pgx.names_fraction(Q18)


def test_a_face_that_fills_the_frame_states_a_closes_own_fraction():
    """ep05's closes 1 and 16 carry no fraction phrase: 'A man's face fills the
    CENTRE of frame' is the whole height, and ep05 looked right."""
    assert pgx.names_fraction("A man's face fills the CENTRE of frame lying on a cushion", "close")
    assert not pgx.names_fraction("A man's face fills the CENTRE of frame", "medium_close")


def test_medium_close_names_head_fraction():
    """Q18's at_rest fails twice -- no fraction, and the span is a close; ep07
    shot 3's passes."""
    assert not pgx.names_fraction(Q18)
    assert pgx.drawn_as_close(Q18)
    assert pgx.names_fraction(EP07_3) and not pgx.drawn_as_close(EP07_3)


def test_size_faults_name_the_shot_and_the_fraction_the_size_wants():
    ep = load("07")
    bad = ep.shots[3].model_copy(update={"at_rest": Q18})
    ep = ep.model_copy(update={"shots": [bad if s.index == 3 else s for s in ep.shots]})
    got = of(pgx.faults(ep), "G-SIZE")
    assert any("shot 3" in f and "a third" in f for f in got)
    assert any("shot 3" in f and "that sentence is a close" in f for f in got)


@pytest.mark.parametrize("ep", ["05", "07"])
def test_the_judged_right_episodes_take_no_size_fault(ep):
    assert of(pgx.faults(load(ep)), "G-SIZE") == []


def test_ep09_trips_on_its_medium_closes():
    assert shots_in(of(pgx.faults(load("09")), "G-SIZE")) >= {7, 17, 19, 24, 27}


def test_ep10_medium_closes_18_27_30_are_closes_by_their_own_sentence():
    got = of(pgx.faults(ep10()), "G-SIZE")
    close = shots_in([f for f in got if "that sentence is a close" in f])
    assert {18, 27, 30} <= close
    assert shots_in(got) >= {7, 10, 13, 16, 18, 23, 27, 30}
    assert not shots_in(got) & {5, 8, 14, 22, 25, 28}     # the closes were drawn as closes


# ---- G-SUNSPLIT: under a sun, the shadow gets an object ------------------------

def test_a_face_split_is_read_in_the_plans_own_phrasings():
    assert pgx.splits_a_face("the LEFT half of the face in hard sun and the RIGHT half in shadow")
    assert pgx.splits_a_face("the low sun from the left on one cheek and the other in shadow")
    assert pgx.splits_a_face("leaves the right side of his face in shadow")
    assert pgx.splits_a_face("splits his face into a lit half and a dark half")
    assert not pgx.splits_a_face("lit hard from the RIGHT, the black coat cuff at the BOTTOM")
    assert not pgx.splits_a_face("the hat brim's black across his eyes")


def test_sun_split_on_face_is_advised_against():
    got = of(pgx.advisories(ep10()), "G-SUNSPLIT")
    assert {4, 5} <= shots_in(got)
    assert not shots_in(got) & {8, 14, 22, 27, 28}      # a window slab or a lamp: obeyed 3/4
    assert 18 not in shots_in(got)                       # the hat brim's black IS the caster
    assert all("edge" in f for f in got)


@pytest.mark.parametrize("ep", ["05", "07"])
def test_the_judged_right_episodes_take_no_sun_split_advisory(ep):
    assert of(pgx.advisories(load(ep)), "G-SUNSPLIT") == []


# ---- G-LIGHT-SIDE: the light clause names a frame side, flipped facing away ----

def test_the_light_clause_is_the_cameras_second_sentence():
    cam = "on the path at a standing man's eye, a 35mm lens. The low sun comes from the right"
    assert pgx.light_clause(cam) == "The low sun comes from the right"
    assert pgx.light_clause("on the path, a 35mm lens") == ""


def test_a_frame_side_is_not_a_body_side():
    assert pgx.frame_side("The low sun comes from the right onto his near cheek") == "right"
    assert pgx.frame_side("lights the path behind him and his right cheek hard") == ""
    assert pgx.frame_side("leaves the right side of his face in shadow") == ""
    assert pgx.frame_side("lights the right-hand log wall") == ""
    assert pgx.frame_side("The lamp lights the hands from above and the left") == "left"


def test_the_doorway_shots_that_face_out_named_the_porch_side():
    got = of(pgx.advisories(ep10()), "G-LIGHT-SIDE")
    assert shots_in(got) == {16, 17, 18}
    assert all("left" in f for f in got)


@pytest.mark.parametrize("ep", ["05", "07"])
def test_the_judged_right_episodes_take_no_light_side_advisory(ep):
    assert of(pgx.advisories(load(ep)), "G-LIGHT-SIDE") == []


# ---- the motion advisories, on the plan's own motions ---------------------------

def test_ep10_motion_advisories_land_on_the_measured_shots():
    got = of(pgx.advisories(ep10()), "G-MOTION")
    assert shots_in([f for f in got if "KEPT EDGE" in f]) == {3, 20}
    assert shots_in([f for f in got if "REPOSITION" in f]) >= {15, 28, 30, 33}
    assert shots_in([f for f in got if "KEPT SCOPE" in f]) == {5, 15, 29}
    assert shots_in([f for f in got if "WALK" in f]) >= {4, 20}


def test_ep07_takes_at_most_the_wide_walk_advisory():
    got = of(pgx.advisories(load("07")), "G-MOTION")
    assert not [f for f in got if "KEPT" in f]


def test_faults_and_advisories_are_separate_verdicts():
    ep = ep10()
    assert all(f.startswith("G-SIZE ") for f in pgx.faults(ep))
    assert not any(f.startswith("G-SIZE ") for f in pgx.advisories(ep))
